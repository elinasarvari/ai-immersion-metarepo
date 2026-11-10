#!/usr/bin/env python3
"""Live progress view of a benefit-feature run.

  python3 workflows/benefit-feature/scripts/watch.py [run-id] [--once] [--every N]

Shows every stage in order (done, running, failed, waiting for you, skipped, not started) with how long it
took, the agent sessions running right now, what each agent has produced so far, and, when the run stops,
why and the exact command to continue. Defaults to the latest run; refreshes every 5 seconds until the run
finishes. Reads only the engine's run files and the feature folder; changes nothing.
"""
import json, os, re, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(os.environ.get("WF_ROOT") or Path(__file__).parents[3]).resolve()
RUNS = ROOT / ".specify" / "workflows" / "runs"

# Top-level steps of workflow.yml in order: (id, label, who, child step ids). Keep in step with workflow.yml;
# tests/test_wf.py fails if a top-level step is missing here.
STAGES = [
    ("sync", "Sync the repos", "script", []),
    ("feature", "Prepare: inputs and spec check", "script", []),
    ("spec_questions", "Open spec questions", "you", ["approve_spec"]),
    ("architect", "Architect: plan, ADRs, scope", "agent", []),
    ("plan_gate", "plan-gate", "script", []),
    ("decide", "Decision-maker settles open ADRs", "agent",
     ["decision_maker", "decisions_gate", "plan_update", "architect_update", "plan_recheck"]),
    ("decision_questions", "Your decisions (decision_mode=ask)", "you", ["approve_decisions"]),
    ("tasks", "Tasks, tagged by lane", "agent", []),
    ("quality_engineer", "Quality engineer: test plan, QA tasks", "agent", []),
    ("tasks_gate", "tasks-gate", "script", []),
    ("branches", "Feature branches", "script", []),
    ("contracts", "Contracts (shared changes, alone)", "agent", ["implement_contracts"]),
    ("lanes", "Lanes, in parallel", "agent", ["lane"]),
    ("qa", "QA tests (cross-lane)", "agent", ["implement_qa"]),
    ("verify_init", "Clear earlier results", "script", []),
    ("verify_loop", "Verify loop (≤3 rounds)", "agent",
     ["needs_fix", "maybe_fix", "fix", "job_list", "run_jobs", "run_job", "review_list", "reviews", "review",
      "verify_status"]),
    ("final_gate", "final-gate", "script", []),
    ("pr_approval", "Approve the push (pr_mode=ask)", "you", ["approve_pr"]),
    ("ship", "PRs, then GitHub Actions", "agent", ["create_pr", "ci"]),
]
# What a failure at each step usually means (mirrors skills/feature-workflow/SKILL.md).
HINTS = {
    "sync": "a repo isn't cloned, isn't clean, or isn't on main",
    "branches": "a repo isn't clean or is on another branch",
    "feature": "a bad input or spec problem; see the problems above",
    "plan_gate": "the architect's output is incomplete; fix the file it names",
    "plan_recheck": "the architect's plan update is incomplete",
    "decisions_gate": "the decision-maker found no compliant option, or didn't record a decision fully",
    "tasks_gate": "tasks.md or test-plan.md is incomplete; fix what it names",
    "final_gate": "still blocking after 3 rounds; see review/verify.md",
    "ci": "GitHub Actions failed on a PR",
}
TOKEN = re.compile(r"[:./\[\]#]+")
C = {"g": "32", "r": "31", "y": "33", "c": "36", "d": "2", "b": "1"}


def paint(s, c, on):
    return f"\033[{C[c]}m{s}\033[0m" if on else s


def parse_ts(s):
    try:
        return datetime.fromisoformat(s)
    except (TypeError, ValueError):
        return None


def dur(sec):
    if sec is None:
        return ""
    sec = int(sec)
    h, m, s = sec // 3600, sec % 3600 // 60, sec % 60
    return f"{h}h{m:02d}m" if h else (f"{m}m{s:02d}s" if m else f"{s}s")


def load(p, default=None):
    try:
        return json.loads(p.read_text())
    except (OSError, ValueError):
        return default


def events(run_dir):
    out = []
    try:
        for line in (run_dir / "log.jsonl").read_text().splitlines():
            try:
                out.append(json.loads(line))
            except ValueError:
                pass
    except OSError:
        pass
    return out


def stage_of(step_id):
    toks = set(t for t in TOKEN.split(str(step_id)) if t)
    for sid, _label, _who, kids in STAGES:
        if sid in toks or toks & set(kids):
            return sid
    return None


def stage_rows(state, evs, now):
    """One row per stage: (id, label, who, status, seconds, note)."""
    run_status = state.get("status", "")
    info = {sid: {"start": None, "end": None, "status": None, "kids": 0, "last_kid_start": None}
            for sid, *_ in STAGES}
    for e in evs:
        sid = stage_of(e.get("step_id", ""))
        if not sid:
            continue
        top = e.get("step_id") == sid
        i, t, ev = info[sid], parse_ts(e.get("timestamp")), e.get("event")
        if not top:
            i["kids"] += 1
            if ev == "step_started":
                i["last_kid_start"] = e.get("step_id")
        if ev == "step_started" and top:
            i.update(start=t, end=None, status="running")
        elif ev == "step_completed" and top:
            i.update(end=t, status=e.get("status", "completed"))
        elif ev == "step_failed":
            i.update(end=t, status="failed")
    rows, cur = [], state.get("current_step_id")
    for sid, label, who, kids in STAGES:
        i = info[sid]
        st, note = i["status"], ""
        if st == "running" and sid == cur and run_status == "paused":
            st, note = "paused", "waiting for you"
        elif st == "running" and run_status not in ("running", "paused", "created"):
            st = "stopped"
        elif st == "completed" and kids and i["kids"] == 0:
            st, note = "skipped", "not needed"
        elif st == "running" and i["last_kid_start"]:
            note = "now: " + i["last_kid_start"].split(":")[-1]
        secs = None
        if i["start"]:
            secs = ((i["end"] or now) - i["start"]).total_seconds()
        rows.append((sid, label, who, st or "pending", secs, note))
    return rows


def sessions():
    """The agent sessions (claude -p) running now: (name, elapsed)."""
    try:
        out = subprocess.run(["ps", "-o", "etime=,args=", "-ax"], capture_output=True, text=True).stdout
    except OSError:
        return []
    found = []
    for line in out.splitlines():
        m = re.match(r"\s*(\S+)\s+(.*)", line)
        if not m or "claude -p" not in m.group(2):
            continue
        a = m.group(2)
        name = (re.search(r"You are the ([\w-]+) agent", a) or re.search(r"tasks tagged \[([\w-]+)\]", a)
                or re.search(r'Review "([\w-]+)"', a) or re.search(r"ONLY the \[(\w+)\] tasks", a))
        label = name.group(1) if name else ("fix" if a.split("-p", 1)[-1].strip().startswith("Fix") else "agent")
        if "tasks tagged" in a:
            label = f"lane {label}"
        elif a.lstrip().startswith(("For ", "claude -p For")) or "speckit-tasks" in a[:400]:
            label = "tasks"
        found.append((label, m.group(1)))
    return found


def artifacts(fd):
    """What the agents have produced so far, in pipeline order."""
    rows = []

    def has(rel):
        return (fd / rel).exists()

    adrs = sorted((fd / "decisions").glob("ADR-*.md")) if has("decisions") else []
    if adrs:
        texts = [a.read_text(errors="ignore") for a in adrs]
        open_ = sum(bool(re.search(r"\*\*Status:\*\*.*(needs decision|needs amendment)", t, re.I)) for t in texts)
        auto = sum("auto-decided" in t for t in texts)
        adr_note = f"{len(adrs)} ADRs, {open_} open, {auto} auto-decided"
    else:
        adr_note = ""
    tasks = (fd / "tasks.md").read_text(errors="ignore") if has("tasks.md") else ""
    total = len(re.findall(r"^\s*-\s*\[[ xX]\]\s*T\d+", tasks, re.M))
    done = len(re.findall(r"^\s*-\s*\[[xX]\]\s*T\d+", tasks, re.M))
    cases = len(re.findall(r"^\|\s*TC-\d+", (fd / "test-plan.md").read_text(errors="ignore"), re.M)) \
        if has("test-plan.md") else 0
    lanes = sorted(p.parent.name for p in (fd / "lanes").glob("*/done.json")) if has("lanes") else []
    verify = load(fd / "review" / "verify.json", {}) or {}
    prs = load(fd / "review" / "prs.json", {}) or {}
    rows += [
        ("plan.md", has("plan.md"), ""),
        ("decisions/", bool(adrs), adr_note),
        ("scope.json", has("scope.json"), ", ".join((load(fd / "scope.json", {}) or {}).get("lanes", []))),
        ("tasks.md", has("tasks.md"), f"{done}/{total} tasks done" if total else ""),
        ("test-plan.md", has("test-plan.md"), f"{cases} test cases" if cases else ""),
        ("lanes/*/done.json", bool(lanes), ", ".join(lanes)),
        ("review/verify.md", has("review/verify.md"),
         (f"{verify.get('blocking')} blocking" + (f"; failing: {', '.join(verify['jobs_failing'])}"
                                                  if verify.get("jobs_failing") else "")) if verify else ""),
        ("review/trace.md", has("review/trace.md"), ""),
        ("review/prs.json", bool(prs), "  ".join(prs.values())),
    ]
    return rows


def failure(state):
    """(step id, error, output tail) of the failed step, if any."""
    for sid, r in reversed(list((state.get("step_results") or {}).items())):
        if isinstance(r, dict) and r.get("status") == "failed":
            o = r.get("output") or {}
            tail = (str(o.get("stderr") or "") + "\n" + str(o.get("stdout") or "")).strip()
            return sid, r.get("error") or state.get("error") or "", tail[-1800:]
    return None


def render(run_dir, color=False):
    state = load(run_dir / "state.json", {}) or {}
    evs = events(run_dir)
    now = datetime.now(timezone.utc)
    inputs = (load(run_dir / "inputs.json", {}) or {}).get("inputs") or state.get("inputs") or {}
    feature = inputs.get("feature", "?")
    fd = next((p for p in [ROOT / "specs" / feature, *sorted((ROOT / "specs").glob(f"{feature}-*"))]
               if p.is_dir()), ROOT / "specs" / feature)
    created = parse_ts(state.get("created_at"))
    status = state.get("status", "unknown")
    scol = {"completed": "g", "failed": "r", "paused": "y", "running": "c"}.get(status, "d")
    L = [paint(f"benefit-feature run {run_dir.name}", "b", color) + f"   {feature}   " +
         paint(status.upper(), scol, color) + (f"   {dur((now - created).total_seconds())} so far" if created else ""),
         paint(f"pr_mode={inputs.get('pr_mode', '?')}  decision_mode={inputs.get('decision_mode', 'auto')}  "
               f"trace_mode={inputs.get('trace_mode', '?')}", "d", color), ""]
    icon = {"completed": ("✓", "g"), "running": ("▶", "c"), "failed": ("✗", "r"), "paused": ("⏸", "y"),
            "skipped": ("–", "d"), "stopped": ("■", "y"), "pending": ("·", "d")}
    for sid, label, who, st, secs, note in stage_rows(state, evs, now):
        ic, col = icon.get(st, ("?", "d"))
        tag = {"agent": "AI ", "script": "   ", "you": "YOU"}[who]
        L.append(f" {paint(ic, col, color)} {paint(tag, 'd', color)} {label:<40} {dur(secs):>7}  "
                 + paint(note, "y" if st == "paused" else "d", color))
    live = sessions()
    L += ["", paint("Agents running now", "b", color)]
    L += [f"   {name:<28} {el}" for name, el in live] or [paint("   none", "d", color)]
    L += ["", paint(f"Produced so far ({fd.relative_to(ROOT) if fd.is_relative_to(ROOT) else fd})", "b", color)]
    for name, ok, note in artifacts(fd):
        L.append(f"   {paint('✓', 'g', color) if ok else paint('·', 'd', color)} {name:<20} {paint(note, 'd', color)}")
    here = "workflows/benefit-feature/run.sh"
    if status == "failed":
        f = failure(state)
        if f:
            sid, err, tail = f
            L += ["", paint(f"Stopped at '{sid}': {err}", "r", color)]
            if HINTS.get(sid):
                L.append(f"   usually: {HINTS[sid]}")
            if tail:
                L += ["   last output:"] + ["     " + x for x in tail.splitlines()[-12:]]
            elif "exited with code" in err:
                L.append("   (no output: the session ended without a reply; usually a permission refused or "
                         "an interrupted session. Start runs with run.sh, which passes the agents' permissions.)")
        L += ["", f"   fix it, then continue:  {here} resume {run_dir.name}"]
    elif status == "paused":
        gate = {"approve_spec": "spec_verdict", "approve_decisions": "decision_verdict", "approve_pr": "pr_verdict"}
        cur = state.get("current_step_id", "")
        verdict = next((v for k, v in gate.items() if k in cur), None)
        L += ["", paint(f"Waiting for you at '{cur}'", "y", color)]
        if verdict:
            L.append(f"   decide, then:  {here} resume {run_dir.name} -i {verdict}=approve   (or =reject)")
    elif status == "completed":
        L += ["", paint("Finished.", "g", color)]
    return "\n".join(L)


def main(argv):
    once = "--once" in argv
    every = 5
    if "--every" in argv:
        every = max(1, int(argv[argv.index("--every") + 1]))
    ids = [a for a in argv[1:] if not a.startswith("--") and not a.isdigit()]
    runs = sorted(RUNS.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True) if RUNS.is_dir() else []
    run_dir = (RUNS / ids[0]) if ids else (runs[0] if runs else None)
    if not run_dir or not run_dir.is_dir():
        print("no workflow run found; start one with: workflows/benefit-feature/run.sh start <feature>")
        return 1
    color = sys.stdout.isatty()
    while True:
        text = render(run_dir, color)
        if once:
            print(text)
            return 0
        sys.stdout.write("\033[H\033[2J" + text + "\n\n" + paint(f"refreshing every {every}s · Ctrl+C to stop "
                                                                 "watching (the run keeps going)", "d", color) + "\n")
        sys.stdout.flush()
        if (load(run_dir / "state.json", {}) or {}).get("status") in ("completed", "failed", "aborted"):
            return 0
        try:
            time.sleep(every)
        except KeyboardInterrupt:
            return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
