#!/usr/bin/env python3
"""Checks for the benefit-feature workflow. Each command prints one JSON object on stdout.

Exit codes: 0 = pass, 1 = the check failed (the workflow run stops there), 2 = usage error.

Gates (one after each planning stage; the skills also run them as their self-check):
  prepare     <feature> <pr_mode> <trace_mode> [decision_mode]  validates the inputs, selects the spec, checks spec.md
  clarify-gate <feature_dir>                    after the spec clarifier: answers recorded; how many questions are still open
  plan-gate   <feature_dir>                     plan.md, ADRs (decisions/) and scope.json (incl. the feature map's target repos); lists the open ADRs
  decisions-gate <feature_dir>                  after the decision-maker: none open, each recorded; does the plan need updating?
  tasks-gate  <feature_dir>                     every task tagged with a lane; test-plan.md covers every FR; the build items
  qa-remaining <feature_dir>                    after the parallel build: the [qa] and late [contracts] tasks left for the QA step

Verify loop (every check runs here, so the fix step can repair any failure):
  verify-init <feature_dir>                     clears earlier results before the loop
  needs-fix   <feature_dir> [coding judgement]  start of a round: what blocks, which fixers (one per repo, or `all`), which model
  behind      <feature_dir>                     the repos whose feature branch is behind origin/main (the integrator merges them)
  jobs        <feature_dir> [strict|warn]       lists this round's jobs (tests, builds, evals, script checks)
  jobs-start  <feature_dir> [strict|warn]       starts this round's jobs in the background (the reviews run meanwhile)
  jobs-wait   <feature_dir>                     waits for them; a job that didn't finish counts as failed
  job         <feature_dir> <job>               runs one job, writes review/jobs/<job>.json and .log; never fails
  review-list <feature_dir> [parallel|on_green] the reviews to run; records the trees reviewed. on_green: waits for the
                                                jobs, and none while a job fails
  changes     <feature_dir> <repo>              the branch's whole change in <repo> against origin/main, uncommitted and
                                                new files included, independent of the git index (what a full review reads)
  delta       <feature_dir> <repo>              diff of <repo> since its last review (what a re-review reads)
  verify-status <feature_dir> [parallel|on_green]  merges jobs and reviews into review/verify.json and verify.md
  final-gate  <feature_dir>                     fails unless the last round left nothing blocking

Ship (CI loop: a failing check goes to a fix step, which pushes to the feature branch, then CI runs again):
  ci-needs-fix <feature_dir>                    start of a CI round: did the last CI run fail?
  ci-wait     <feature_dir> [pr_mode]           waits for GitHub Actions on the PRs in review/prs.json; writes
                                                review/ci.md (failing checks with their log tails); never fails.
                                                With pr_mode draft, marks the PRs ready for review once all green
  ci-gate     <feature_dir>                     fails unless the last CI run passed

Script jobs (run by `job`, also usable by hand): ownership, tasks, trace:strict, trace:warn, e2e, main.
  ports                                         the stack ports something already listens on (never fails)
Paths are relative to the metarepo root. The lane ownership map mirrors project-rules/backend-architecture.md.
"""
import fcntl, json, os, re, shutil, signal, socket, subprocess, sys, tempfile, time
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(os.environ.get("WF_ROOT") or Path(__file__).parents[3]).resolve()
REPOS = ("benefit-be", "benefit-fe")

# Lane -> {repo: [path prefixes it owns]}. Tests mirror the source tree (tests/<prefix>), so they belong to
# the same lane. Keep in step with the Ownership table in project-rules/backend-architecture.md.
LANES = {
    "workflows-lane": {"benefit-be": ["apps/worker/"]},
    "agents-lane": {"benefit-be": ["packages/agents/", "evals/"]},
    "data-lane": {"benefit-be": ["packages/rag/", "packages/rules/", "db/", "analytics/", "data/policy/", "evals/"]},
    "platform-ui-lane": {
        "benefit-be": ["apps/api/", "packages/mcp_servers/", "packages/platform/", "Makefile", "Procfile",
                       "Brewfile", "scripts/", ".github/"],
        "benefit-fe": [""],  # the whole frontend repo
    },
}
# Shared files changed only in the sequential contracts step (BA-8, PR-4), never by a parallel lane.
CONTRACTS = {"benefit-be": ["packages/domain/", "openapi/", "pyproject.toml", "uv.lock", ".env.example", "README.md",
                            "CLAUDE.md", ".gitignore"]}
# Cross-lane tests, written by the qa item of the parallel build (beside the lanes) and finished in the QA step.
QA = {"benefit-be": ["tests/integration/", "tests/contract/", "tests/e2e/"]}
SHORT = {"workflows": "workflows-lane", "agents": "agents-lane", "data": "data-lane",
         "platform-ui": "platform-ui-lane", "platform": "platform-ui-lane"}
LEVELS = {"unit", "integration", "workflow", "contract", "e2e", "eval"}
FR_RE = re.compile(r"\bFR-(\d{3})-(\d{2})\b")
TASK_RE = re.compile(r"^\s*-\s*\[([ xX])\]\s*(T\d{3,})\b(.*)$")
RESULT_FILES = {"verify", "snapshot", "reviewed", "prs", "history", "ci"}  # review/*.json that aren't review results


def out(obj, ok=True):
    print(json.dumps(obj))
    sys.exit(0 if ok else 1)


def fdir(arg):
    d = (ROOT / arg).resolve()
    if not d.is_dir():
        out({"problems": [f"feature folder {arg} not found"]}, ok=False)
    return d


def read(p: Path) -> str:
    return p.read_text() if p.exists() else ""


def load_json(p: Path, default=None):
    try:
        return json.loads(p.read_text())
    except (OSError, ValueError):
        return default


def rel(p: Path) -> str:
    return str(p.relative_to(ROOT))


def lane_of(token: str):
    t = token.strip().lower()
    return t if t in ("contracts", "qa") else SHORT.get(t) or (t if t in LANES else None)


def owner(repo: str, path: str):
    """The lane, 'contracts' or 'qa' that owns a repo-relative path, else None."""
    if any(path.startswith(q) for q in QA.get(repo, [])):
        return "qa"
    p = path[len("tests/"):] if path.startswith("tests/") else path
    for prefix in CONTRACTS.get(repo, []):
        if p == prefix or (prefix.endswith("/") and p.startswith(prefix)):
            return "contracts"
    for lane, owned in LANES.items():
        for prefix in owned.get(repo, []):
            if prefix == "" or p == prefix or (prefix.endswith("/") and p.startswith(prefix)):
                return lane
    return None


def repo_dir(repo: str) -> Path:
    return ROOT / "repos" / repo


def git(repo, *a, env=None):
    r = subprocess.run(["git", "-C", str(repo_dir(repo)), *a], capture_output=True, text=True,
                       env={**os.environ, **(env or {})})
    return r.stdout if r.returncode == 0 else None


def changed_files(repo: str):
    if not (repo_dir(repo) / ".git").exists():
        return []
    files = set((git(repo, "diff", "--name-only", "origin/main...HEAD") or "").splitlines())
    for line in (git(repo, "status", "--porcelain", "-uall") or "").splitlines():
        files.add(line[3:].split(" -> ")[-1].strip('"'))
    return sorted(f for f in files if f)


def tree_id(repo: str):
    """A tree object for the whole working tree, untracked files included, without touching the real index."""
    if not (repo_dir(repo) / ".git").exists():
        return None
    with tempfile.TemporaryDirectory() as t:
        env = {"GIT_INDEX_FILE": str(Path(t) / "index")}
        git(repo, "read-tree", "HEAD", env=env)
        git(repo, "add", "-A", env=env)
        tid = git(repo, "write-tree", env=env)
    return tid.strip() if tid else None


def scope(d: Path):
    sc = load_json(d / "scope.json", {}) or {}
    return sc if isinstance(sc, dict) else {}


DEFINED_FR_RE = re.compile(r"^\s*-\s*\*\*(FR-\d{3}-\d{2})\*\*", re.M)


def spec_frs(d: Path):
    """The requirements this spec defines (its `- **FR-…**` list items). IDs it only mentions, such as
    requirements moved to another feature or cross-references, belong to that other spec."""
    s = read(d / "spec.md")
    defined = sorted(set(DEFINED_FR_RE.findall(s)))
    return defined or sorted({f"FR-{a}-{b}" for a, b in FR_RE.findall(s)})


# ── Gates ─────────────────────────────────────────────────────────────────────────────────────────
def check_spec(d):
    s = read(d / "spec.md")
    if not s:
        return {"fr_count": 0, "open": 0, "open_items": [], "problems": ["spec.md missing"]}
    problems = [f"missing section '{h}'" for h in ("## User Scenarios", "## Requirements", "## Success Criteria")
                if h not in s]
    defined = re.findall(r"^\s*-\s*\*\*(FR-\d{3}-\d{2})\*\*", s, re.M)
    if not defined:
        problems.append("no functional requirements in the FR-<NNN>-<nn> form")
    dupes = sorted({x for x in defined if defined.count(x) > 1})
    if dupes:
        problems.append(f"duplicate requirement IDs: {', '.join(dupes)}")
    if "Acceptance Scenarios" not in s:
        problems.append("no acceptance scenarios")
    open_items = [o.strip() for o in re.findall(r"\[NEEDS CLARIFICATION:?([^\]]*)\]", s)]
    return {"fr_count": len(defined), "open": len(open_items), "open_items": open_items, "problems": problems}


def prepare(feature, pr_mode, trace_mode, decision_mode="auto"):
    problems = []
    if decision_mode not in ("auto", "ask"):
        problems.append(f"decision_mode must be auto or ask, got '{decision_mode}'")
    if pr_mode not in ("draft", "ask", "none"):
        problems.append(f"pr_mode must be draft, ask or none, got '{pr_mode}'")
    if trace_mode not in ("strict", "warn"):
        problems.append(f"trace_mode must be strict or warn, got '{trace_mode}'")
    if "/" in feature:  # specs/001-case-lifecycle
        cands = [ROOT / feature]
    elif (ROOT / "specs" / feature).is_dir():  # 001-case-lifecycle
        cands = [ROOT / "specs" / feature]
    else:  # 001
        cands = sorted((ROOT / "specs").glob(f"{feature}-*"))
    cands = [c for c in cands if (c / "spec.md").exists()]
    if len(cands) != 1:
        out({"problems": problems + [f"expected one spec folder for '{feature}' with spec.md, found {len(cands)}"]},
            ok=False)
    d = cands[0].resolve()
    r = rel(d)
    (ROOT / ".specify").mkdir(exist_ok=True)
    (ROOT / ".specify" / "feature.json").write_text(json.dumps({"feature_directory": str(d)}) + "\n")
    # An earlier run's lane reports name its task IDs; left in place, the verify `tasks` job would tick off
    # this run's tasks that happen to reuse them. Each run starts without them.
    cleared = []
    for f in sorted((d / "lanes").glob("*/*")):
        if f.is_file() and f.name in ("done.json", "blocked.md"):
            f.unlink()
            cleared.append(rel(f))
    existing = (d / "tasks.md").exists()
    spec = check_spec(d)
    out({"feature_dir": r, "feature": d.name, "branch": f"feature/{d.name}", "spec_file": f"{r}/spec.md",
         "update": existing, "cleared_lane_reports": cleared,
         "review_dir": f"{r}/review", "pr_mode": pr_mode, "trace_mode": trace_mode, "decision_mode": decision_mode, **spec,
         "problems": problems + spec["problems"]}, ok=not (problems or spec["problems"]))


def adr_status(text):
    m = re.search(r"\*\*Status:\*\*\s*(.+)", text)
    s = (m.group(1) if m else "").lower()
    for key, word in (("needs_decision", "needs decision"), ("needs_amendment", "needs amendment"),
                      ("superseded", "superseded"), ("auto_decided", "auto-decided"), ("accepted", "accepted")):
        if word in s:
            return key
    return None


def feature_map_repos(d):
    """Target repos for feature folder `d` in the specs/README.md feature map ([] if it isn't listed).

    The map is the documented source of which repos a feature touches, so a plan can't quietly drop
    one (for example the screens in benefit-fe).
    """
    for line in read(ROOT / "specs" / "README.md").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 3 and f"({d.name}/spec.md)" in cells[0]:
            return [r for r in REPOS if r in cells[2]]
    return []


def plan_gate(d):
    problems, accepted, open_adrs = [], [], []
    counts = {"accepted": 0, "auto_decided": 0, "needs_decision": 0, "needs_amendment": 0, "superseded": 0}
    # plan.md
    p = read(d / "plan.md")
    if not p:
        problems.append("plan.md missing")
    repos = sorted(set(re.findall(r"repos/(benefit-(?:be|fe))", p)))
    if p and not repos:
        problems.append("plan names no target repo (repos/benefit-be or repos/benefit-fe)")
    # decisions/
    dd = d / "decisions"
    if not (dd / "README.md").exists():
        problems.append("decisions/README.md missing (the architecture step didn't finish)")
    required = ("## Context", "## Options", "## Decision", "## Consequences", "## How we verify it")
    for f in sorted(dd.glob("ADR-*.md")):
        s = f.read_text()
        st = adr_status(s)
        if st is None:
            problems.append(f"{f.name}: no valid Status line")
        else:
            counts[st] += 1
            m = re.match(r"(ADR-\d{3}-\d{2})", f.name)
            if st in ("accepted", "auto_decided") and m:
                accepted.append(m.group(1))
            if st in ("needs_decision", "needs_amendment"):
                open_adrs.append(f.name)
        problems += [f"{f.name}: missing '{h}'" for h in required if h not in s]
        if s.count("### Option") < 2:
            problems.append(f"{f.name}: fewer than two options")
    if p:
        problems += [f"plan doesn't reference Accepted {a}" for a in accepted if a not in p]
        if accepted and "Architecture decisions" not in p:
            problems.append("plan has no 'Architecture decisions' section")
    # scope.json
    sc = load_json(d / "scope.json")
    lanes, sc_repos = [], []
    if not isinstance(sc, dict):
        problems.append("scope.json missing or invalid")
    else:
        raw = sc.get("lanes", [])
        lanes = sorted({lane_of(x) for x in raw if lane_of(x) in LANES})
        problems += [f"scope.json: unknown lane '{x}'" for x in raw if lane_of(x) not in LANES]
        sc_repos = sc.get("repos", [])
        problems += [f"scope.json: unknown repo '{r}'" for r in sc_repos if r not in REPOS]
        problems += [f"scope.json: no {k} in scope" for k, v in (("lanes", raw), ("repos", sc_repos)) if not v]
        problems += [f"repos/{r} is not cloned (clone-repo skill)" for r in sc_repos
                     if r in REPOS and not (repo_dir(r) / ".git").exists()]
        if p:
            problems += [f"scope.json targets {r}, but plan.md never names repos/{r}" for r in sc_repos
                         if r in REPOS and r not in repos]
        mapped = feature_map_repos(d)
        problems += [f"the feature map (specs/README.md) lists {r} for this feature, but scope.json doesn't"
                     for r in mapped if r not in sc_repos]
        if "benefit-fe" in mapped and "platform-ui-lane" not in lanes:
            problems.append("the feature map lists benefit-fe for this feature (its screens), "
                            "so scope.json needs platform-ui-lane, which owns benefit-fe")
    out({**counts, "open": len(open_adrs), "open_adrs": open_adrs, "accepted_adrs": accepted,
         "lanes": lanes, "repos": sc_repos, "problems": problems}, ok=not problems)


def option_key(text):
    m = re.search(r"option\s+([a-z0-9]+)", str(text), re.I)
    return m.group(1).lower() if m else str(text).strip().lower()


def decisions_gate(d):
    """After the decision-maker: nothing open, every automatic decision recorded in its ADR and in
    auto-decisions.json, and which decisions differ from the architect's recommendation (the plan assumed it)."""
    dd, problems, auto = d / "decisions", [], []
    for f in sorted(dd.glob("ADR-*.md")):
        s = f.read_text()
        st = adr_status(s)
        if st in ("needs_decision", "needs_amendment"):
            problems.append(f"{f.name} is still open: the decision-maker found no compliant option (see decisions/README.md)")
        elif st == "auto_decided":
            m = re.match(r"(ADR-\d{3}-\d{2})", f.name)
            auto.append(m.group(1) if m else f.stem)
            problems += [f"{f.name}: no '{k}' line" for k in ("**Decided by:**", "**Revisit if:**") if k not in s]
    log = load_json(dd / "auto-decisions.json")
    entries = {}
    if auto and not isinstance(log, list):
        problems.append("decisions/auto-decisions.json missing or not a list")
    for e in log if isinstance(log, list) else []:
        if not isinstance(e, dict) or not e.get("adr") or not e.get("chosen"):
            problems.append(f"auto-decisions.json: entry without adr and chosen: {e}")
            continue
        entries[e["adr"]] = e
    problems += [f"{a} is auto-decided but not in auto-decisions.json" for a in auto if a not in entries]
    problems += [f"auto-decisions.json lists {a}, which isn't an auto-decided ADR" for a in entries if a not in auto]
    differs = sorted(a for a, e in entries.items() if a in auto and e.get("recommended")
                     and option_key(e["chosen"]) != option_key(e["recommended"]))
    if "Decided automatically" not in read(dd / "README.md") and auto:
        problems.append("decisions/README.md has no 'Decided automatically' section")
    out({"auto_decided": auto, "plan_update_needed": differs, "problems": problems}, ok=not problems)


def test_cases(d):
    """Rows of the test-plan.md cases table: id, frs, level, repo, name."""
    cases = []
    for line in read(d / "test-plan.md").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 6 or not re.fullmatch(r"TC-\d+", cells[0]):
            continue
        repo = next((r for r in REPOS if r in cells[3]), None)
        cases.append({"id": cells[0], "frs": [f"FR-{a}-{b}" for a, b in FR_RE.findall(cells[1])],
                      "level": cells[2].lower(), "repo": repo, "name": cells[4].strip("`").strip()})
    return cases


def tasks_gate(d):
    problems, warnings = [], []
    t = read(d / "tasks.md")
    if not t:
        problems.append("tasks.md missing")
    by_lane, untagged, text, lane_by_id = {}, [], {}, {}
    for line in t.splitlines():
        m = TASK_RE.match(line)
        if not m:
            continue
        text[m.group(2)] = m.group(3)
        lanes = [x for x in (lane_of(x) for x in re.findall(r"\[([A-Za-z-]+)\]", m.group(3))) if x]
        if lanes:
            lane_by_id[m.group(2)] = lanes[0]
        if lanes:
            by_lane.setdefault(lanes[0], []).append(m.group(2))
        else:
            untagged.append(m.group(2))
    if untagged:
        problems.append(f"tasks without a lane tag: {', '.join(untagged)}")
    in_scope = {lane_of(x) for x in scope(d).get("lanes", [])}
    stray = sorted(l for l in by_lane if l in LANES and l not in in_scope)
    if stray:
        problems.append(f"tasks for lanes outside scope.json: {', '.join(stray)}")
    mentioned = {f"FR-{a}-{b}" for a, b in FR_RE.findall(t)}
    frs = spec_frs(d)
    unmentioned = [f for f in frs if f not in mentioned]
    if unmentioned:
        warnings.append(f"no task mentions {', '.join(unmentioned)}")
    # test-plan.md
    cases = test_cases(d)
    if not read(d / "test-plan.md"):
        problems.append("test-plan.md missing")
    elif not cases:
        problems.append("test-plan.md has no TC-<n> rows in its cases table")
    names = {}
    for c in cases:
        if c["level"] not in LEVELS:
            problems.append(f"{c['id']}: unknown level '{c['level']}'")
        if not c["repo"]:
            problems.append(f"{c['id']}: no repo in its 'Lane / repo' column")
        if not c["name"]:
            problems.append(f"{c['id']}: no test name")
        elif c["frs"] and c["level"] != "eval":
            a, b = c["frs"][0][3:].split("-")
            if not (c["name"].startswith(f"test_FR_{a}_{b}") or c["name"].startswith(f"FR-{a}-{b}:")):
                problems.append(f"{c['id']}: test name '{c['name']}' doesn't start with {c['frs'][0]} (testing.md)")
        if c["name"] and c["name"] in names:
            problems.append(f"{c['id']}: same test name as {names[c['name']]}")
        names.setdefault(c["name"], c["id"])
    covered = {f for c in cases for f in c["frs"]}
    missing = [f for f in frs if f not in covered]
    if cases and missing:
        problems.append(f"requirements without a test case: {', '.join(missing)}")
    # A [contracts] task that has to wait for lane work ("after T020") can't run in the contracts step, which
    # comes before the lanes. The QA step, after the lanes, does it instead, so no fix round is spent on it.
    late = []
    for tid in by_lane.get("contracts", []):
        refs = []
        for grp in re.findall(r"\bafter\s+(T\d{3,}(?:\s*(?:,|and|&)\s*T\d{3,})*)", text.get(tid, ""), re.I):
            refs += re.findall(r"T\d{3,}", grp)
        if any(lane_by_id.get(r) not in (None, "contracts") for r in refs):
            late.append(tid)
    if late:
        warnings.append(f"[contracts] tasks that need lane work first, done in the QA step instead: {', '.join(late)}")
    lanes = sorted(l for l in by_lane if l in LANES)
    # The parallel build: every lane, plus the qa item, which writes the planned cross-lane tests beside them.
    build_items = lanes + (["qa"] if by_lane.get("qa") else [])
    out({"lanes": lanes, "build_items": build_items,
         "contracts_tasks": len(by_lane.get("contracts", [])) - len(late), "late_contracts": late,
         "qa_tasks": len(by_lane.get("qa", [])) + len(late),
         "tasks_by_lane": {k: len(v) for k, v in sorted(by_lane.items())},
         "cases": len(cases), "warnings": warnings, "problems": problems}, ok=not problems)


def clarify_gate(d):
    """After the spec clarifier (or with none): every automatic answer recorded fully, the spec still valid, and
    how many [NEEDS CLARIFICATION] questions are left for a person. Fails only on a broken record or spec."""
    spec = check_spec(d)
    problems = list(spec["problems"])
    log_path = d / "clarifications.json"
    log = load_json(log_path) if log_path.exists() else []
    answered, left = [], []
    if not isinstance(log, list):
        problems.append("clarifications.json is not a list")
        log = []
    for e in log:
        if not isinstance(e, dict) or not e.get("question"):
            problems.append(f"clarifications.json: entry without a question: {e}")
        elif e.get("left_open"):
            left.append(e["question"])
        else:
            problems += [f"clarifications.json: '{e['question'][:60]}' has no {k}"
                         for k in ("answer", "kind", "revisit_if") if not e.get(k)]
            answered.append(e["question"])
    if answered and "(automated)" not in read(d / "spec.md"):
        problems.append("spec.md has no automated Clarifications session listing the answers")
    out({"open": spec["open"], "open_items": spec["open_items"], "answered": len(answered), "left_open": left,
         "problems": problems}, ok=not problems)


def qa_remaining(d):
    """After the parallel build: the [qa] tasks the qa item left (they needed the lanes' code) and the late
    [contracts] tasks. The QA step runs only if there are any."""
    done = set()
    for f in (d / "lanes").glob("*/done.json"):
        done |= set((load_json(f, {}) or {}).get("tasks", []))
    open_qa, late = [], []
    t = read(d / "tasks.md")
    by_id = {}
    for line in t.splitlines():
        m = TASK_RE.match(line)
        if m:
            lanes = [x for x in (lane_of(x) for x in re.findall(r"\[([A-Za-z-]+)\]", m.group(3))) if x]
            by_id[m.group(2)] = (m.group(1), lanes[0] if lanes else None, m.group(3))
    for tid, (mark, lane, _) in by_id.items():
        if lane == "qa" and mark == " " and tid not in done:
            open_qa.append(tid)
    for tid, (mark, lane, text) in by_id.items():
        if lane != "contracts" or mark != " " or tid in done:
            continue
        refs = []
        for grp in re.findall(r"\bafter\s+(T\d{3,}(?:\s*(?:,|and|&)\s*T\d{3,})*)", text, re.I):
            refs += re.findall(r"T\d{3,}", grp)
        if any(by_id.get(r, (None, None))[1] not in (None, "contracts") for r in refs):
            late.append(tid)
    out({"open_qa": open_qa, "late_contracts": late, "count": len(open_qa) + len(late)})


# ── Script jobs (run inside the verify loop) ─────────────────────────────────────────────────────
def job_ownership(d):
    in_scope = {lane_of(x) for x in scope(d).get("lanes", [])} | {"contracts", "qa"}
    problems = []
    for repo in REPOS:
        for f in changed_files(repo):
            o = owner(repo, f)
            if o is None:
                problems.append(f"{repo}:{f} is outside every lane's folders (BA-1)")
            elif o not in in_scope:
                problems.append(f"{repo}:{f} belongs to {o}, which isn't in this feature's scope.json")
    return {"status": "fail" if problems else "pass", "problems": problems}


def job_tasks(d):
    """Marks the tasks the lanes reported done, then fails while any task is still open."""
    done = set()
    for f in (d / "lanes").glob("*/done.json"):
        done |= set((load_json(f, {}) or {}).get("tasks", []))
    tp = d / "tasks.md"
    lines, marked, still_open = read(tp).splitlines(keepends=True), [], []
    for i, line in enumerate(lines):
        m = TASK_RE.match(line)
        if not m or m.group(1) != " ":
            continue
        if m.group(2) in done:
            lines[i] = line.replace("[ ]", "[X]", 1)
            marked.append(m.group(2))
        else:
            still_open.append(m.group(2))
    if marked:
        tp.write_text("".join(lines))
    problems = [f"{t} is not done" for t in still_open]
    for b in sorted((d / "lanes").glob("*/blocked.md")) if still_open else []:
        if b.read_text().strip():
            problems.append(f"{rel(b)} lists work a lane couldn't do in its own folders: do it, then mark the task [X]")
    return {"status": "fail" if still_open else "pass", "marked": marked, "problems": problems}


def is_test_file(p: Path) -> bool:
    return (p.suffix == ".py" and (p.name.startswith("test_") or p.name.endswith("_test.py"))) \
        or bool(re.search(r"\.(test|spec)\.[cm]?[jt]sx?$", p.name))


def source_files(rd: Path):
    for p in rd.rglob("*"):
        if p.is_file() and not ({"node_modules", ".git", ".venv", "dist", "build"} & set(p.parts)):
            yield p


def find_test(case, files):
    """Where a planned test is defined: (found, skipped) lists of 'repo:path'."""
    name, found, skipped = case["name"], [], []
    q = re.escape(name)
    if name.startswith("test_"):  # Python: a real def, not a mention in a comment or string
        pat = re.compile(rf"^(?P<deco>(?:[ \t]*@.*\n)*)[ \t]*(?:async[ \t]+)?def[ \t]+{q}\b", re.M)
        kinds = (".py",)
    elif case["level"] == "eval":  # an eval case id in the eval suite or its dataset
        pat, kinds = re.compile(rf"(?<![\w-]){q}(?![\w-])"), None
    else:  # TypeScript/Playwright: test('<name> …') or it("<name> …")
        pat = re.compile(rf"\b(?:test|it)(?P<mod>\.(?:only|skip|todo|fixme))?\(\s*['\"`]{q}")
        kinds = (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".mts", ".cts")
    for where, p, text in files:
        if kinds and p.suffix not in kinds:
            continue
        if case["level"] != "eval" and not is_test_file(p):
            continue
        if case["level"] == "eval" and not ("evals" in p.parts or is_test_file(p)):
            continue
        for m in pat.finditer(text):
            gd = m.groupdict()
            skip = bool(re.search(r"\bmark\.(skip|skipif|xfail)\b|\bskip\(", gd.get("deco") or "")) \
                or (gd.get("mod") or "") in (".skip", ".todo", ".fixme")
            (skipped if skip else found).append(where)
    return sorted(set(found)), sorted(set(skipped) - set(found))


# Folders whose conftest starts real services (benefit-be tests/conftest.py level_for: db, integration).
SERVICE_TEST_DIRS = r"benefit-be:tests/(db|integration)/"


def job_trace(d, mode):
    cases = test_cases(d)
    if not cases:
        return {"status": "fail", "problems": ["test-plan.md has no test cases to trace"]}
    files = {}
    for repo in REPOS:
        rd = repo_dir(repo)
        if rd.is_dir():
            files[repo] = [(f"{repo}:{p.relative_to(rd)}", p, p.read_text(errors="ignore"))
                           for p in source_files(rd) if p.suffix in (".py", ".ts", ".tsx", ".js", ".jsx", ".mjs",
                                                                     ".cjs", ".mts", ".cts", ".json", ".jsonl",
                                                                     ".yaml", ".yml")]
    rows, problems, proven = [], [], set()
    for c in cases:
        pool = files.get(c["repo"], []) if c["repo"] else [f for v in files.values() for f in v]
        found, skipped = find_test(c, pool)
        wrong_level = [w for w in found if c["level"] == "unit" and re.match(SERVICE_TEST_DIRS, w)]
        if wrong_level:
            problems.append(f"{c['id']}: unit test `{c['name']}` is in {', '.join(wrong_level)}, a folder whose "
                            "tests need MongoDB/Temporal (CI's unit job has neither): move it out, or plan it "
                            "as integration")
        if found:
            proven |= set(c["frs"])
            where = ", ".join(found)
        elif skipped:
            where = f"**skipped** ({', '.join(skipped)})"
            problems.append(f"{c['id']}: `{c['name']}` is skipped in {', '.join(skipped)}")
        else:
            where = "**missing**"
            problems.append(f"{c['id']}: no {c['level']} test named `{c['name']}` in {c['repo'] or 'any repo'}")
        rows.append(f"| {c['id']} | {', '.join(c['frs']) or '-'} | {c['level']} | `{c['name']}` | {where} |")
    unproven = [f for f in spec_frs(d) if f not in proven]
    problems += [f"{f} has no test defined (every case for it is missing or skipped)" for f in unproven]
    report = ["# Requirement traceability", "", f"Mode: {mode}. A test counts only where it is defined (a Python "
              "`def`, a `test(`/`it(` title, or an eval case id) and not skipped.", "",
              "| Case | Proves | Level | Test | Defined in |", "|---|---|---|---|---|", *rows]
    if unproven:
        report += ["", "**Requirements with no test:** " + ", ".join(unproven)]
    rp = d / "review" / "trace.md"
    rp.parent.mkdir(parents=True, exist_ok=True)
    rp.write_text("\n".join(report) + "\n")
    status = "pass" if not problems else ("warn" if mode == "warn" else "fail")
    return {"status": status, "cases": len(cases), "unproven": unproven, "problems": problems, "report": rel(rp)}


# API, worker health, Vite, Temporal (gRPC, UI), MongoDB: what `make verify` starts for the e2e job.
STACK_PORTS = [int(p) for p in os.environ.get("WF_STACK_PORTS", "8000,8001,5173,7233,8233,27017").split(",") if p]


def behind_main(repo):
    """(commits the feature branch is behind origin/main, files a merge would conflict in). Fetches main only, so
    other features' branches never land in the clone (gitleaks scans every ref it knows)."""
    if not (repo_dir(repo) / ".git").exists() or not changed_files(repo):
        return 0, []
    git(repo, "fetch", "-q", "origin", "main")
    n = int((git(repo, "rev-list", "--count", "HEAD..origin/main") or "0").strip() or 0)
    files = []
    if n:
        r = subprocess.run(["git", "-C", str(repo_dir(repo)), "merge-tree", "--write-tree", "--name-only",
                            "--no-messages", "origin/main", "HEAD"], capture_output=True, text=True)
        files = [ln for ln in r.stdout.splitlines()[1:] if ln] if r.returncode == 1 else []
    return n, files


def behind_repos():
    return [{"repo": r, "behind": n, "conflicts": f} for r in REPOS for n, f in [behind_main(r)] if n]


def behind(d):
    out({"repos": behind_repos()})


def project_dirs():
    """This checkout and the main checkout it belongs to (a feature worktree's metarepo), as path prefixes."""
    dirs = {str(ROOT)}
    common = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--path-format=absolute", "--git-common-dir"],
                            capture_output=True, text=True).stdout.strip()
    if common:
        dirs.add(str(Path(common).parent.resolve()))
    return [d.rstrip("/") + "/" for d in dirs]


def busy_ports():
    """[(port, holder)] for each stack port another project's process listens on, IPv4 or IPv6 (Vite binds ::1).
    This project's own services (started from the metarepo or one of its worktrees, such as the shared local
    MongoDB) don't count: the e2e job may use them."""
    busy, ours = [], project_dirs()
    for port in STACK_PORTS:
        used = False
        for fam, host in ((socket.AF_INET, "127.0.0.1"), (socket.AF_INET6, "::1")):
            try:
                with socket.socket(fam, socket.SOCK_STREAM) as sk:
                    sk.settimeout(0.5)
                    used = used or sk.connect_ex((host, port)) == 0
            except OSError:
                pass
        if used:
            r = subprocess.run(["lsof", "-nP", f"-iTCP:{port}", "-sTCP:LISTEN", "-Fpc"], capture_output=True, text=True)
            fields = dict((ln[0], ln[1:]) for ln in r.stdout.splitlines() if ln[:1] in ("p", "c"))
            pid = fields.get("p", "")
            where = ""
            if pid:
                where = subprocess.run(["ps", "-o", "command=", "-p", pid], capture_output=True, text=True).stdout
                cwd = subprocess.run(["lsof", "-a", "-p", pid, "-d", "cwd", "-Fn"], capture_output=True, text=True)
                where += "".join(ln[1:] + "/" for ln in cwd.stdout.splitlines() if ln[:1] == "n")
            if any(d in where for d in ours):
                continue
            busy.append((port, f"{fields.get('c', '?')} pid {pid or '?'}"))
    return busy


def ports():
    out({"busy": [{"port": p, "holder": h} for p, h in busy_ports()]})


def make_has(rd, target):
    mf = rd / "Makefile"
    return mf.exists() and re.search(rf"^{re.escape(target)}:", mf.read_text(), re.M)


def repo_job_cmd(repo, kind):
    rd = repo_dir(repo)
    if make_has(rd, kind):
        return f"make {kind}"
    if repo == "benefit-fe" and kind == "check":
        return "pnpm lint && pnpm format:check && pnpm typecheck && pnpm test"
    if repo == "benefit-fe" and kind == "build":
        return "pnpm build"
    return None


def job_names(d, trace_mode):
    js, e2e = [], False
    for repo in REPOS:
        files = changed_files(repo)
        if not files:
            continue
        e2e = e2e or repo == "benefit-fe" or any(re.match(r"(apps|packages|db)/", f) for f in files)
        js.append(f"{repo}:check")
        if repo == "benefit-fe":
            js.append(f"{repo}:build")
        if repo == "benefit-be" and any(re.match(r"(packages/agents|packages/rag|evals)/", f) for f in files):
            js.append(f"{repo}:eval")
    # e2e first: it is the longest, so it starts first
    return (["e2e"] if e2e else []) + js + (["main"] if js else []) + ["ownership", "tasks", f"trace:{trace_mode}"]


def clear_jobs(d):
    # Each round's results come only from this round's jobs: a job file an agent left behind (by running
    # `wf.py job` itself) would otherwise count as a failing job.
    jd = d / "review" / "jobs"
    for f in (jd.glob("*") if jd.is_dir() else []):
        if f.is_file() and f.name != "runner.state":
            f.unlink()


def jobs(d, trace_mode):
    clear_jobs(d)
    out({"jobs": job_names(d, trace_mode)})


JOB_WORKERS = 6       # heavy jobs (check, build, eval, e2e) are at most 5; the script checks take seconds
JOBS_TIMEOUT = 3700   # seconds jobs-wait waits for the runner (each job's command stops itself at 3600)


def runner_alive(pid):
    if not pid:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    cmd = subprocess.run(["ps", "-o", "command=", "-p", str(pid)], capture_output=True, text=True).stdout
    return "jobs-run" in cmd


def stop_runner(d):
    """Stops an earlier round's runner (an interrupted or resumed run) and puts any index it staged back."""
    info = load_json(d / "review" / "jobs" / "runner.state", {}) or {}
    pid = info.get("pid")
    if runner_alive(pid):
        try:
            os.killpg(pid, signal.SIGTERM)
        except OSError:
            pass
        for _ in range(30):
            if not runner_alive(pid):
                break
            time.sleep(1)
    for repo in REPOS:
        if (repo_dir(repo) / ".git").exists() and git_path(repo, "wf-stage.json").exists():
            stage_exit(repo, force=True)


def jobs_start(d, trace_mode):
    """Starts this round's jobs in a background runner and returns at once, so the reviews run meanwhile."""
    jd = d / "review" / "jobs"
    jd.mkdir(parents=True, exist_ok=True)
    stop_runner(d)
    clear_jobs(d)
    js = job_names(d, trace_mode)
    log = open(jd / "runner.log", "w")
    # Its own session and no inherited pipes: the engine's shell step returns now, not when the jobs finish.
    proc = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "jobs-run", rel(d), *js],
                            stdin=subprocess.DEVNULL, stdout=log, stderr=log, start_new_session=True,
                            env={**os.environ, "WF_ROOT": str(ROOT)})
    (jd / "runner.state").write_text(json.dumps({"pid": proc.pid, "jobs": js, "started": time.time()}))
    out({"jobs": js, "pid": proc.pid})


def jobs_run(d, names):
    """The background runner: every job in parallel, each as its own `wf.py job`."""
    me = [sys.executable, str(Path(__file__).resolve()), "job", rel(d)]
    with ThreadPoolExecutor(max_workers=JOB_WORKERS) as pool:
        list(pool.map(lambda n: subprocess.run([*me, n], capture_output=True, text=True), names))
    (d / "review" / "jobs" / "runner.done").write_text("\n".join(names) + "\n")


def job_file(d, name):
    return d / "review" / "jobs" / f"{name.replace(':', '-')}.json"


def wait_for_jobs(d, timeout=JOBS_TIMEOUT):
    """Waits for the runner; any job without a result (killed, timed out, crashed) is written as failed."""
    jd = d / "review" / "jobs"
    info = load_json(jd / "runner.state", {}) or {}
    names, pid = info.get("jobs", []), info.get("pid")
    deadline = time.time() + timeout
    while runner_alive(pid) and not (jd / "runner.done").exists() and time.time() < deadline:
        time.sleep(2)
    if runner_alive(pid) and not (jd / "runner.done").exists():
        stop_runner(d)
    missing = []
    for n in names:
        if not job_file(d, n).exists():
            missing.append(n)
            job_file(d, n).write_text(json.dumps({"job": n, "status": "fail", "problems": [
                f"the job didn't finish (no result after {timeout}s, or the runner stopped); see {rel(jd)}/runner.log"]}))
    return names, missing


def jobs_wait(d):
    names, missing = wait_for_jobs(d)
    out({"jobs": names, "missing": missing, "failing": failing_jobs(d)})


def git_path(repo, name):
    p = (git(repo, "rev-parse", "--path-format=absolute", "--git-path", name) or "").strip()
    return Path(p) if p else None


@contextmanager
def stage_lock(repo):
    lock = git_path(repo, "wf-stage.lock")
    with open(lock, "a+") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(fh, fcntl.LOCK_UN)


def stage_enter(repo):
    """Stage the working tree for a job. Jobs overlap (and share a repo), so it is counted: the first job in saves
    the real index, the last one out puts it back."""
    state, idx = git_path(repo, "wf-stage.json"), git_path(repo, "index")
    with stage_lock(repo):
        st = load_json(state, {}) or {}
        if not st.get("count"):
            backup = git_path(repo, "wf-stage.index")
            if idx.exists():
                shutil.copyfile(idx, backup)
            st = {"count": 0, "had_index": idx.exists()}
        st["count"] += 1
        state.write_text(json.dumps(st))
        for _ in range(10):  # a reviewer's `git status` may hold index.lock for a moment
            if git(repo, "add", "-A") is not None:
                break
            time.sleep(0.5)


def stage_exit(repo, force=False):
    state, idx, backup = git_path(repo, "wf-stage.json"), git_path(repo, "index"), git_path(repo, "wf-stage.index")
    with stage_lock(repo):
        st = load_json(state, {}) or {}
        if not st:
            return
        st["count"] = 0 if force else st.get("count", 1) - 1
        if st["count"] > 0:
            state.write_text(json.dumps(st))
            return
        if st.get("had_index") and backup.exists():
            shutil.copyfile(backup, idx)
        elif not st.get("had_index") and idx.exists():
            idx.unlink()
        backup.unlink(missing_ok=True)
        state.unlink(missing_ok=True)


def run_in_repo(repo, cmd, res, log_file, stage=None):
    """Runs cmd in the repo; sets res status/tail and writes the log. `stage`: the repos whose working tree the
    command checks against git (default: just this one; e2e's `make verify` checks both).

    The loop commits nothing, so a check that diffs a generated file against git (openapi-check's
    `git diff --exit-code`) would fail every round. Stage the working tree for the command, then put the index back
    exactly as it was: the diff then means "regenerating changed something". No GIT_INDEX_FILE is exported,
    because tests that make their own git repos would inherit it. Reviewers, which run meanwhile, read the change
    with `changes`/`delta`, which don't depend on the index."""
    staged = [rp for rp in sorted(stage or [repo]) if (repo_dir(rp) / ".git").exists()]
    for rp in staged:
        stage_enter(rp)
    try:
        r = subprocess.run(cmd, shell=True, cwd=repo_dir(repo), capture_output=True, text=True, timeout=3600)
        res["status"] = "pass" if r.returncode == 0 else "fail"
        log = r.stdout + r.stderr
    except subprocess.TimeoutExpired:
        res["status"], log = "fail", "timed out after 3600s"
    finally:
        for rp in staged:
            stage_exit(rp)
    log_file.write_text(log)
    res["tail"] = log[-2000:]


def job(d, name):
    jd = d / "review" / "jobs"
    jd.mkdir(parents=True, exist_ok=True)
    head, _, arg = name.partition(":")
    res = {"job": name}
    if name == "ownership":
        res.update(job_ownership(d))
    elif name == "tasks":
        res.update(job_tasks(d))
    elif head == "trace" and arg in ("strict", "warn"):
        res.update(job_trace(d, arg))
    elif head in REPOS and arg in ("check", "build", "eval") and (repo_dir(head) / ".git").exists():
        cmd = repo_job_cmd(head, arg)
        res["cmd"] = cmd
        if not cmd:  # never a silent pass: a skipped job is a warning in verify.md and the PR
            res.update(status="warn", problems=[f"repos/{head} has no '{arg}' target, so this job didn't run"])
        else:
            run_in_repo(head, cmd, res, jd / f"{name.replace(':', '-')}.log")
    elif name == "main":  # the branch must contain main: what ships is tested against what is already there
        rs = behind_repos()
        res.update(status="fail" if rs else "pass", problems=[
            f"repos/{r['repo']}: {r['behind']} commit(s) behind origin/main"
            + (f", would conflict in {', '.join(r['conflicts'])}" if r["conflicts"] else "")
            + "; the integrator merges it at the start of the next round" for r in rs])
    elif name == "e2e":  # the stack and e2e, the way CI's e2e job runs them
        busy = busy_ports()
        if busy:  # never borrow or wipe another stack (make verify runs make reset); CI still runs e2e on the PR
            res.update(status="warn", problems=[f"e2e didn't run here: port {p} is in use ({h}). Stop that stack to "
                                                "run it locally; CI's e2e job runs it on the PR" for p, h in busy])
        elif not make_has(repo_dir("benefit-be"), "verify"):
            res.update(status="warn", problems=["repos/benefit-be has no 'verify' target, so e2e didn't run"])
        else:
            # verify-stack: only the stages no other job runs (integration, client in sync, stack, e2e); plain
            # `make verify` repeats the check and build jobs' stages too
            res["cmd"] = "make verify-stack" if make_has(repo_dir("benefit-be"), "verify-stack") else "make verify"
            run_in_repo("benefit-be", res["cmd"], res, jd / "e2e.log", stage=REPOS)
    else:
        res.update(status="fail", problems=[f"unknown job '{name}'"])
    (jd / f"{name.replace(':', '-')}.json").write_text(json.dumps(res, indent=2))
    out({k: v for k, v in res.items() if k != "tail"})


# ── Verify loop ───────────────────────────────────────────────────────────────────────────────────
def verify_init(d):
    rd = d / "review"
    rd.mkdir(parents=True, exist_ok=True)
    stop_runner(d)
    for f in [*rd.glob("*.json"), *rd.glob("*.md"), *(rd / "jobs").glob("*")]:
        if f.is_file() and f.name not in ("prs.json", "integrate.md"):  # integrate.md: the merge before the lanes
            f.unlink()
    out({"cleared": rel(rd)})


MAX_ROUNDS = 6  # verify rounds at most; the loop stops earlier once it stops making progress


def history(d):
    h = load_json(d / "review" / "history.json", [])
    return h if isinstance(h, list) else []


REVIEW_REPO = {f"code-{r}": r for r in REPOS}


def fix_items(d, st):
    """Who fixes this round: one fixer per repo when every blocker belongs to one repo (they run in parallel, each
    in its own clone), else one fixer for everything. `main` is the integrator's, and a review with no valid
    result (99) reruns by itself, so neither needs a fixer."""
    repos, cross = set(), []
    for j in st.get("jobs_failing", []):
        head = j.partition(":")[0]
        if head in REPOS:
            repos.add(head)
        elif j != "main":
            cross.append(j)
    for name, n in (st.get("reviews") or {}).items():
        if not n or n == 99:
            continue
        if name in REVIEW_REPO:
            repos.add(REVIEW_REPO[name])
            continue
        r = load_json(d / "review" / f"{name}.json", {}) or {}
        found = [f for f in r.get("findings", []) if isinstance(f, dict)
                 and str(f.get("severity", "")).lower() in ("critical", "major")]
        for f in found or [{}]:
            head = str(f.get("file", "")).partition(":")[0]
            if head in REPOS:
                repos.add(head)
            else:
                cross.append(name)
    if cross:
        return ["all"]
    return sorted(repos)


def needs_fix(d, coding_model="sonnet", judgement_model="opus"):
    """Start of a round. The first fix uses the coding model; once a fix has already been tried, what is left
    is the hard part, so later fixes use the judgement model."""
    st = load_json(d / "review" / "verify.json")
    blocking = int(st.get("blocking", 99)) if isinstance(st, dict) else 0  # no result yet = first round
    items = fix_items(d, st) if isinstance(st, dict) and blocking > 0 else []
    rounds = len(history(d))
    model = coding_model if rounds <= 1 else judgement_model
    out({"fix": bool(items), "blocking": blocking, "fix_items": items, "round": rounds + 1, "fix_model": model})


def keep_going(h):
    """(continue?, why). Continue while something blocks, unless the cap is reached or the last two rounds
    didn't beat the best result before them (stuck: more rounds would only spend tokens)."""
    if not h or h[-1] == 0:
        return False, "nothing blocking"
    if len(h) >= MAX_ROUNDS:
        return False, f"{MAX_ROUNDS} rounds done"
    if len(h) >= 3 and min(h[-2:]) >= min(h[:-2]):
        return False, f"no progress in the last 2 rounds (blocking per round: {h})"
    return True, f"still {h[-1]} blocking, round {len(h) + 1} next"


def failing_jobs(d):
    res = [load_json(f, {}) or {} for f in sorted((d / "review" / "jobs").glob("*.json"))]
    return [j.get("job", "?") for j in res if j.get("status") not in ("pass", "warn")]


def review_names(d):
    repos = [r for r in REPOS if r in scope(d).get("repos", [])]
    return {"compliance": repos, **{f"code-{r}": [r] for r in repos}}


REVIEW_MODES = ("parallel", "on_green")


def review_list(d, mode="parallel"):
    """Round 1 runs every review. Later rounds rerun a review only if it has no result, still blocks, or its
    repos changed since it last looked. snapshot.json = the trees the previous reviews saw (a re-review reads
    only the change since then); reviewed.json = the trees this round's reviews see.

    parallel: the reviews run while the jobs do (nothing edits the code meanwhile), so one fix gets both.
    on_green: waits for the jobs first and runs no review while one fails (fewer review tokens, more rounds)."""
    rd = d / "review"
    if mode == "on_green":
        wait_for_jobs(d)
        if failing_jobs(d):
            out({"reviews": [], "reason": "a test, build or script check fails; reviews wait until it passes"})
    before = load_json(rd / "reviewed.json", {}) or {}
    now = {r: tree_id(r) for r in REPOS}
    todo = []
    for name, repos in review_names(d).items():
        prev = load_json(rd / f"{name}.json")
        try:
            blocking = int(prev.get("blocking", 99)) if isinstance(prev, dict) else None
        except (TypeError, ValueError):
            blocking = 99
        if blocking is None or blocking > 0 or any(before.get(r) != now[r] for r in repos):
            todo.append(name)
    if before:
        (rd / "snapshot.json").write_text(json.dumps(before) + "\n")
    (rd / "reviewed.json").write_text(json.dumps(now) + "\n")
    out({"reviews": todo, "skipped": sorted(set(review_names(d)) - set(todo))})


def changes(d, repo):
    if not (repo_dir(repo) / ".git").exists():
        out({"problems": [f"repos/{repo} is not cloned"]}, ok=False)
    base = (git(repo, "merge-base", "origin/main", "HEAD") or "").strip()
    now = tree_id(repo)
    diff = git(repo, "diff", base, now) if base and now else None
    if diff is None:
        out({"problems": [f"couldn't diff {repo} against origin/main"]}, ok=False)
    print(diff or f"(no changes in {repo} against origin/main)")


def delta(d, repo):
    snap = (load_json(d / "review" / "snapshot.json", {}) or {}).get(repo)
    if not snap:
        out({"problems": [f"no snapshot for {repo}: do a full review"]}, ok=False)
    now = tree_id(repo)
    diff = git(repo, "diff", snap, now) if now else None
    if diff is None:
        out({"problems": [f"couldn't diff {repo} against {snap}: do a full review"]}, ok=False)
    print(diff or f"(no changes in {repo} since the last review)")


def verify_status(d, mode="parallel"):
    rd = d / "review"
    job_res = [load_json(f, {}) or {} for f in sorted((rd / "jobs").glob("*.json"))]
    failing = [j for j in job_res if j.get("status") not in ("pass", "warn")]
    warns = [j for j in job_res if j.get("status") == "warn"]
    lines = ["# Verification", "", "## Tests, builds and checks"]
    for j in job_res:
        name = j.get("job", "?")
        log = rd / "jobs" / f"{name.replace(':', '-')}.log"
        lines.append(f"- `{name}`: **{j.get('status', 'missing')}**" +
                     (f" (log: {rel(log)})" if j.get("status") == "fail" and log.exists() else ""))
        lines += [f"  - {p}" for p in j.get("problems", [])[:20]]
    if not job_res:
        lines.append("- no job results found")
    blocking = len(failing) + (0 if job_res else 99)
    reviews = {}
    # parallel: every review saw this round's code, so it counts even while a job fails (the fix gets both).
    # on_green: reviews ran only if the jobs passed; otherwise they are still valid from an earlier round.
    if job_res and (mode == "parallel" or not failing):
        lines += ["", "## Reviews"]
        for name in review_names(d):
            r = load_json(rd / f"{name}.json")
            try:
                n = int(r.get("blocking", 99)) if isinstance(r, dict) else 99
            except (TypeError, ValueError):
                n = 99
            reviews[name] = n
            blocking += n
            lines.append(f"- `{name}`: {n} blocking" + (" (no valid result)" if n == 99 else f" (see review/{name}.md)"))
    if warns:
        lines += ["", "## Warnings (not blocking; say so in the PR)"]
        lines += [f"- `{j['job']}`: {p}" for j in warns for p in j.get("problems", [])]
    h = history(d) + [blocking]
    (rd / "history.json").write_text(json.dumps(h) + "\n")
    go, why = keep_going(h)
    lines += ["", f"Round {len(h)}: {why}."]
    st = {"blocking": blocking, "jobs_failing": [j.get("job", "?") for j in failing], "reviews": reviews,
          "warnings": [j["job"] for j in warns], "round": len(h), "history": h, "continue": go, "why": why}
    (rd / "verify.json").write_text(json.dumps(st, indent=2))
    (rd / "verify.md").write_text("\n".join(lines) + "\n")
    out(st)


def final_gate(d):
    st = load_json(d / "review" / "verify.json")
    if not isinstance(st, dict):
        st = {"blocking": 99, "error": "review/verify.json missing or invalid"}
    st["blocking"] = int(st.get("blocking", 99))
    if st["blocking"] > 0:
        print(json.dumps(st))
        print(f"Still {st['blocking']} blocking ({st.get('why', 'last round')}); see {rel(d)}/review/verify.md. Fix them, "
              "rerun the failing jobs (`wf.py job`) and reviews (review-changes skill), then `wf.py verify-status` "
              "and `specify workflow resume <run-id>`.", file=sys.stderr)
        sys.exit(1)
    out(st)


def gh(*args, timeout=120):
    try:
        r = subprocess.run(["gh", *args], capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stdout + r.stderr).strip()
    except (OSError, subprocess.TimeoutExpired) as e:
        return 1, str(e)


def failing_checks(url):
    """[(check name, link, log tail)] for the failed checks of a PR."""
    code, text = gh("pr", "checks", url, "--json", "name,state,link")
    try:
        checks = json.loads(text) if code in (0, 1, 8) else []
    except ValueError:
        checks = []
    repo = re.search(r"github\.com/([^/]+/[^/]+)/pull/", url)
    found, seen = [], set()
    for c in checks:
        if str(c.get("state", "")).upper() not in ("FAILURE", "ERROR", "CANCELLED", "TIMED_OUT", "STARTUP_FAILURE"):
            continue
        m = re.search(r"/runs/(\d+)/job/(\d+)", c.get("link", ""))
        if not m or (c.get("name"), m.group(1)) in seen:
            continue
        seen.add((c.get("name"), m.group(1)))
        args = ["run", "view", m.group(1), "--job", m.group(2), "--log-failed"]
        if repo:
            args += ["-R", repo.group(1)]
        _, log = gh(*args)
        found.append((c.get("name", "?"), c.get("link", ""), "\n".join(log.splitlines()[-80:])))
    return found


def ci_wait(d, pr_mode="draft"):
    """Wait for GitHub Actions on every PR. A red check is reported (review/ci.md), not raised, so the CI fix
    step can repair it; ci-gate decides after the loop. When everything is green and the PRs were opened as
    drafts, they are marked ready for review."""
    rd = d / "review"
    prs = load_json(rd / "prs.json")
    if not isinstance(prs, dict) or not prs:
        out({"problems": ["review/prs.json missing or invalid (the PR step writes it)"]}, ok=False)
    results, report, failing = {}, ["# GitHub Actions", ""], 0
    for repo, url in prs.items():
        code, text = gh("pr", "checks", url, "--watch", "--interval", "30", timeout=5400)
        if "no checks reported" in text:
            results[repo] = "no checks configured"
        elif code == 0:
            results[repo] = "pass"
        else:
            results[repo] = "fail"
            fails = failing_checks(url)
            failing += max(1, len(fails))
            report += [f"## {repo}: failed ({url})", ""]
            for name, link, log in fails:
                report += [f"### `{name}` ({link})", "", "```", log, "```", ""]
            if not fails:
                report += ["(couldn't read the failing jobs; open the PR's Checks tab)", ""]
        if results[repo] != "fail":
            report.append(f"- {repo}: {results[repo]} ({url})")
    ready = []
    if failing == 0 and pr_mode == "draft":
        for repo, url in prs.items():
            code, text = gh("pr", "view", url, "--json", "isDraft", "-q", ".isDraft")
            if text.strip() == "true" and gh("pr", "ready", url)[0] == 0:
                ready.append(url)
        if ready:
            report += ["", "All green: marked ready for review: " + ", ".join(ready)]
    st = {"ci": results, "failing": failing, "ready": ready}
    (rd / "ci.json").write_text(json.dumps(st, indent=2))
    (rd / "ci.md").write_text("\n".join(report) + "\n")
    out(st)


def ci_needs_fix(d):
    st = load_json(d / "review" / "ci.json")
    failing = int(st.get("failing", 0)) if isinstance(st, dict) else 0  # no CI result yet = first round
    out({"fix": failing > 0, "failing": failing})


def ci_gate(d):
    st = load_json(d / "review" / "ci.json")
    if not isinstance(st, dict):
        out({"problems": ["review/ci.json missing: CI didn't run"]}, ok=False)
    failing = int(st.get("failing", 0))
    if failing:
        print(json.dumps(st))
        print(f"GitHub Actions still failing after the CI fix rounds; see {rel(d)}/review/ci.md. Fix it on the "
              "feature branch and push; then `run.sh resume`.", file=sys.stderr)
        sys.exit(1)
    out(st)


def main(argv):
    cmd, pos = (argv[1], argv[2:]) if len(argv) > 1 else ("", [])
    one = {"clarify-gate": clarify_gate, "qa-remaining": qa_remaining, "jobs-wait": jobs_wait, "plan-gate": plan_gate, "decisions-gate": decisions_gate, "tasks-gate": tasks_gate, "verify-init": verify_init, "needs-fix": needs_fix,
           "review-list": review_list, "behind": behind, "verify-status": verify_status, "final-gate": final_gate, "ci-wait": ci_wait,
           "ci-needs-fix": ci_needs_fix, "ci-gate": ci_gate}
    if cmd in one and len(pos) == 1:
        return one[cmd](fdir(pos[0]))
    if cmd == "ci-wait" and len(pos) == 2:
        return ci_wait(fdir(pos[0]), pos[1])
    if cmd in ("review-list", "verify-status") and len(pos) == 2:
        if pos[1] not in REVIEW_MODES:
            out({"problems": [f"review mode must be parallel or on_green, got '{pos[1]}'"]}, ok=False)
        return (review_list if cmd == "review-list" else verify_status)(fdir(pos[0]), pos[1])
    if cmd == "needs-fix" and len(pos) == 3:
        return needs_fix(fdir(pos[0]), pos[1], pos[2])
    if cmd == "prepare" and len(pos) in (3, 4):
        return prepare(*pos)
    if cmd in ("jobs", "jobs-start") and len(pos) in (1, 2):
        mode = pos[1] if len(pos) == 2 else "strict"
        if mode not in ("strict", "warn"):
            out({"problems": [f"trace mode must be strict or warn, got '{mode}'"]}, ok=False)
        return (jobs if cmd == "jobs" else jobs_start)(fdir(pos[0]), mode)
    if cmd == "jobs-run" and pos:
        return jobs_run(fdir(pos[0]), pos[1:])
    if cmd == "ports" and not pos:
        return ports()
    if cmd == "job" and len(pos) == 2:
        return job(fdir(pos[0]), pos[1])
    if cmd in ("delta", "changes") and len(pos) == 2 and pos[1] in REPOS:
        return (delta if cmd == "delta" else changes)(fdir(pos[0]), pos[1])
    print(__doc__, file=sys.stderr)
    sys.exit(2)


if __name__ == "__main__":
    main(sys.argv)
