#!/usr/bin/env python3
"""Verification steps for the benefit-feature workflow. Each command prints one JSON object on stdout.

Exit codes: 0 = pass, 1 = the check failed (the workflow run stops there), 2 = usage error.

  spec-check     <feature_dir>               spec structure; counts open [NEEDS CLARIFICATION] markers
  scope-check    <feature_dir>               validates scope.json (lanes and repos the feature touches)
  decisions-check <feature_dir>              ADR structure and status counts (open = needs a person)
  plan-check     <feature_dir>               plan names target repos and follows every Accepted ADR
  tasks-split    <feature_dir>               every task tagged with a lane; lists the lanes that have tasks
  ownership      <feature_dir>               every changed file belongs to a lane in scope (or contracts)
  lane-tests     <feature_dir> <lane>        runs the lane's unit tests; never fails (the lane review reads it)
  status         <json_file> [--require-clean]   prints a review status; --require-clean fails if blocking > 0
  mark-tasks     <feature_dir>               marks tasks the lanes reported done as [X] in tasks.md
  trace          <feature_dir> [strict|warn] every FR in the spec has a test named after it (FR-009-04 naming)
  inputs-check   <pr_mode> <trace_mode>      pr_mode is draft|ask|none, trace_mode is strict|warn
  use-spec       <feature>                   selects an existing spec (NNN or specs/NNN-name); prints its paths
  test-plan-check <feature_dir>              every FR has a test case; levels and test names follow testing.md
  verify-init    <feature_dir>               clears earlier verification results before the verify loop
  jobs           <feature_dir>               lists the test and build jobs for the changed repos
  job            <feature_dir> <job>         runs one job (e.g. benefit-fe:build); never fails, writes review/jobs/
  review-list    <feature_dir>               lists the reviews to run: compliance + one code review per repo
  verify-status  <feature_dir>               merges jobs and reviews into review/verify.json and verify.md
  snapshot       <feature_dir>               records each repo's working tree so re-reviews only read the change
  ci-wait        <feature_dir>               waits for the GitHub Actions checks on the PRs in review/prs.json

Paths are relative to the metarepo root. The lane ownership map mirrors project-rules/backend-architecture.md.
"""
import json, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
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
CONTRACTS = {"benefit-be": ["packages/domain/", "pyproject.toml", "uv.lock", ".env.example", "README.md",
                            "CLAUDE.md", ".gitignore"]}
# Cross-lane tests written in the sequential [qa] step after the lanes join.
QA = {"benefit-be": ["tests/integration/", "tests/contract/", "tests/e2e/"]}
SHORT = {"workflows": "workflows-lane", "agents": "agents-lane", "data": "data-lane",
         "platform-ui": "platform-ui-lane", "platform": "platform-ui-lane"}
LEVELS = {"unit", "integration", "workflow", "contract", "e2e", "eval"}
FR_RE = re.compile(r"\bFR-(\d{3})-(\d{2})\b")


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


def changed_files(repo: str):
    d = ROOT / "repos" / repo
    if not (d / ".git").exists():
        return []
    def git(*a):
        r = subprocess.run(["git", "-C", str(d), *a], capture_output=True, text=True)
        return r.stdout.splitlines() if r.returncode == 0 else []
    files = set(git("diff", "--name-only", "origin/main...HEAD"))
    for line in git("status", "--porcelain", "-uall"):
        files.add(line[3:].split(" -> ")[-1])
    return sorted(f for f in files if f)


def spec_frs(d: Path):
    """The feature's own requirements (FR-<NNN>-xx for specs/<NNN>-name). IDs of other specs that
    spec.md only refers to belong to those specs, so tasks, test plan and trace don't need them."""
    own = re.match(r"(\d{3})-", d.name)
    return sorted({f"FR-{a}-{b}" for a, b in FR_RE.findall(read(d / "spec.md"))
                   if own is None or a == own.group(1)})


# ---------------------------------------------------------------------------------------------------
def spec_check(d):
    s = read(d / "spec.md")
    problems = []
    if not s:
        out({"problems": ["spec.md missing"]}, ok=False)
    for h in ("## User Scenarios", "## Requirements", "## Success Criteria"):
        if h not in s:
            problems.append(f"missing section '{h}'")
    defined = re.findall(r"^\s*-\s*\*\*(FR-\d{3}-\d{2})\*\*", s, re.M)
    if not defined:
        problems.append("no functional requirements in the FR-<NNN>-<nn> form")
    dupes = sorted({x for x in defined if defined.count(x) > 1})
    if dupes:
        problems.append(f"duplicate requirement IDs: {', '.join(dupes)}")
    if "Acceptance Scenarios" not in s:
        problems.append("no acceptance scenarios")
    open_items = re.findall(r"\[NEEDS CLARIFICATION:?([^\]]*)\]", s)
    out({"fr_count": len(defined), "open": len(open_items),
         "open_items": [o.strip() for o in open_items], "problems": problems}, ok=not problems)


def scope_check(d):
    try:
        sc = json.loads(read(d / "scope.json"))
    except ValueError as e:
        out({"problems": [f"scope.json missing or invalid: {e}"]}, ok=False)
    lanes = [lane_of(x) for x in sc.get("lanes", [])]
    repos = sc.get("repos", [])
    problems = [f"unknown lane '{x}'" for x, l in zip(sc.get("lanes", []), lanes) if l in (None, "contracts")]
    problems += [f"unknown repo '{r}'" for r in repos if r not in REPOS]
    if not lanes:
        problems.append("no lanes in scope")
    if not repos:
        problems.append("no repos in scope")
    missing = [r for r in repos if not (ROOT / "repos" / r / ".git").exists()]
    problems += [f"repos/{r} is not cloned (clone-repo skill)" for r in missing]
    out({"lanes": sorted({l for l in lanes if l in LANES}), "repos": repos, "problems": problems}, ok=not problems)


def decisions_check(d):
    dd = d / "decisions"
    problems, counts = [], {"accepted": 0, "needs_decision": 0, "needs_amendment": 0, "superseded": 0}
    if not (dd / "README.md").exists():
        out({"problems": ["decisions/README.md missing (architecture step didn't finish)"], **counts, "open": 0}, ok=False)
    required = ("## Context", "## Options", "## Decision", "## Consequences", "## How we verify it")
    for f in sorted(dd.glob("ADR-*.md")):
        s = f.read_text()
        m = re.search(r"\*\*Status:\*\*\s*(.+)", s)
        status = (m.group(1) if m else "").lower()
        if "needs decision" in status:
            counts["needs_decision"] += 1
        elif "amendment" in status:
            counts["needs_amendment"] += 1
        elif "superseded" in status:
            counts["superseded"] += 1
        elif "accepted" in status:
            counts["accepted"] += 1
        else:
            problems.append(f"{f.name}: no valid Status line")
        problems += [f"{f.name}: missing '{h}'" for h in required if h not in s]
        if s.count("### Option") < 2:
            problems.append(f"{f.name}: fewer than two options")
    out({**counts, "open": counts["needs_decision"] + counts["needs_amendment"], "problems": problems},
        ok=not problems)


def plan_check(d):
    p = read(d / "plan.md")
    problems = []
    if not p:
        out({"problems": ["plan.md missing"]}, ok=False)
    repos = sorted(set(re.findall(r"repos/(benefit-(?:be|fe))", p)))
    if not repos:
        problems.append("plan names no target repo (repos/benefit-be or repos/benefit-fe)")
    accepted = []
    for f in sorted((d / "decisions").glob("ADR-*.md")):
        m = re.search(r"\*\*Status:\*\*\s*(.+)", f.read_text())
        if m and "accepted" in m.group(1).lower():
            adr_id = re.match(r"(ADR-\d{3}-\d{2})", f.name)
            if adr_id:
                accepted.append(adr_id.group(1))
    problems += [f"plan doesn't reference Accepted {a}" for a in accepted if a not in p]
    if accepted and "Architecture decisions" not in p:
        problems.append("plan has no 'Architecture decisions' section")
    out({"repos": repos, "accepted_adrs": accepted, "problems": problems}, ok=not problems)


TASK_RE = re.compile(r"^\s*-\s*\[([ xX])\]\s*(T\d{3,})\b(.*)$")


def tasks_split(d):
    t = read(d / "tasks.md")
    if not t:
        out({"problems": ["tasks.md missing"]}, ok=False)
    by_lane, problems, untagged = {}, [], []
    for line in t.splitlines():
        m = TASK_RE.match(line)
        if not m:
            continue
        tid, rest = m.group(2), m.group(3)
        tags = [lane_of(x) for x in re.findall(r"\[([A-Za-z-]+)\]", rest)]
        lanes = [x for x in tags if x]
        if not lanes:
            untagged.append(tid)
            continue
        by_lane.setdefault(lanes[0], []).append(tid)
    if untagged:
        problems.append(f"tasks without a lane tag: {', '.join(untagged)}")
    covered = set(FR_RE.findall(t))
    uncovered = [f for f in spec_frs(d) if tuple(f[3:].split("-")) not in covered]
    out({"lanes": sorted(l for l in by_lane if l not in ("contracts", "qa")),
         "contracts_tasks": len(by_lane.get("contracts", [])), "qa_tasks": len(by_lane.get("qa", [])),
         "tasks_by_lane": {k: len(v) for k, v in sorted(by_lane.items())},
         "frs_not_mentioned_in_tasks": uncovered, "problems": problems}, ok=not problems)


def ownership(d):
    try:
        in_scope = set(json.loads(read(d / "scope.json")).get("lanes", []))
    except ValueError:
        in_scope = set()
    in_scope = {lane_of(x) for x in in_scope} | {"contracts", "qa"}
    violations, files = [], {}
    for repo in REPOS:
        for f in changed_files(repo):
            o = owner(repo, f)
            files[f"{repo}:{f}"] = o
            if o is None:
                violations.append(f"{repo}:{f} is outside every lane's folders (BA-1)")
            elif o not in in_scope:
                violations.append(f"{repo}:{f} belongs to {o}, which isn't in this feature's scope")
    out({"files": files, "violations": violations}, ok=not violations)


def lane_tests(d, lane):
    res = {"lane": lane, "runs": []}
    for repo, prefixes in LANES.get(lane, {}).items():
        rd = ROOT / "repos" / repo
        if not (rd / ".git").exists():
            continue
        if repo == "benefit-fe":
            cmd = ["pnpm", "vitest", "run"] if (rd / "package.json").exists() else None
        else:
            dirs = [f"tests/{p}" for p in prefixes if p.endswith("/") and (rd / "tests" / p).is_dir()]
            cmd = ["uv", "run", "pytest", "-q", *dirs] if dirs else None
        if not cmd:
            res["runs"].append({"repo": repo, "status": "skipped", "reason": "no tests for this lane yet"})
            continue
        try:
            r = subprocess.run(cmd, cwd=rd, capture_output=True, text=True, timeout=900)
            res["runs"].append({"repo": repo, "cmd": " ".join(cmd), "status": "pass" if r.returncode == 0 else "fail",
                                "tail": (r.stdout + r.stderr)[-3000:]})
        except (OSError, subprocess.TimeoutExpired) as e:
            res["runs"].append({"repo": repo, "cmd": " ".join(cmd), "status": "error", "tail": str(e)})
    res["failing"] = sum(1 for r in res["runs"] if r["status"] in ("fail", "error"))
    res["blocking"] = res["failing"]
    p = d / "lanes" / lane / "tests.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(res, indent=2))
    out({k: v for k, v in res.items() if k != "runs"} | {"report": str(p.relative_to(ROOT))})


def status(path, require_clean):
    try:
        st = json.loads(Path(ROOT / path).read_text())
        st["blocking"] = int(st.get("blocking", 99))
    except Exception as e:  # a missing or broken status never lets the run through
        st = {"blocking": 99, "error": f"no valid status at {path}: {e}"}
    if require_clean and st["blocking"] > 0:
        print(json.dumps(st))
        print(f"Still {st['blocking']} blocking finding(s) after the last round; see the report next to {path}. "
              "Fix them, then: specify workflow resume <run-id>", file=sys.stderr)
        sys.exit(1)
    out(st)


def mark_tasks(d):
    done = set()
    for f in (d / "lanes").glob("*/done.json"):
        try:
            done |= set(json.loads(f.read_text()).get("tasks", []))
        except ValueError:
            pass
    tp = d / "tasks.md"
    lines, marked = read(tp).splitlines(keepends=True), []
    for i, line in enumerate(lines):
        m = TASK_RE.match(line)
        if m and m.group(1) == " " and m.group(2) in done:
            lines[i] = line.replace("[ ]", "[X]", 1)
            marked.append(m.group(2))
    if marked:
        tp.write_text("".join(lines))
    out({"marked": marked, "reported_done": sorted(done)})


def trace(d, warn):
    frs = spec_frs(d)
    found = {f: [] for f in frs}
    pats = {f: (f"test_FR_{f[3:6]}_{f[7:9]}", f"{f}:") for f in frs}
    for repo in REPOS:
        rd = ROOT / "repos" / repo
        if not rd.exists():
            continue
        for p in rd.rglob("*"):
            if not p.is_file() or "node_modules" in p.parts or ".git" in p.parts:
                continue
            if not (p.suffix == ".py" and "test" in p.name) and not re.search(r"\.(test|spec)\.tsx?$", p.name):
                continue
            text = p.read_text(errors="ignore")
            for f, (py, ts) in pats.items():
                if py in text or ts in text:
                    found[f].append(f"{repo}:{p.relative_to(rd)}")
    untested = [f for f, where in found.items() if not where]
    report = ["# Requirement traceability", "", "| Requirement | Tests |", "|---|---|"]
    report += [f"| {f} | {', '.join(w) if w else '**none**'} |" for f, w in found.items()]
    rp = d / "review" / "trace.md"
    rp.parent.mkdir(parents=True, exist_ok=True)
    rp.write_text("\n".join(report) + "\n")
    out({"requirements": len(frs), "untested": untested, "report": str(rp.relative_to(ROOT))},
        ok=warn or not untested)


def use_spec(arg):
    """Select an existing spec by number (003) or folder (specs/003-name) and make it current for Spec Kit."""
    cands = [ROOT / arg] if "/" in arg else sorted((ROOT / "specs").glob(f"{arg}-*"))
    cands = [c for c in cands if (c / "spec.md").exists()]
    if len(cands) != 1:
        out({"problems": [f"expected one spec folder for '{arg}' with spec.md, found {len(cands)}"]}, ok=False)
    d = cands[0].resolve()
    rel = str(d.relative_to(ROOT))
    (ROOT / ".specify").mkdir(exist_ok=True)
    (ROOT / ".specify" / "feature.json").write_text(json.dumps({"feature_directory": str(d)}) + "\n")
    out({"feature_dir": rel, "feature": d.name, "branch": f"feature/{d.name}", "spec_file": f"{rel}/spec.md",
         "plan_file": f"{rel}/plan.md", "tasks_file": f"{rel}/tasks.md", "review_dir": f"{rel}/review"})


def test_plan_check(d):
    t = read(d / "test-plan.md")
    if not t:
        out({"problems": ["test-plan.md missing"]}, ok=False)
    problems, cases = [], 0
    covered = set()
    for line in t.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 6 or not re.match(r"TC-\d+", cells[0]):
            continue
        cases += 1
        covered |= {f"FR-{a}-{b}" for a, b in FR_RE.findall(cells[1])}
        level, name = cells[2].lower(), cells[4].strip("`")
        if level not in LEVELS:
            problems.append(f"{cells[0]}: unknown level '{cells[2]}'")
        frs = FR_RE.findall(cells[1])
        if frs and level != "eval":
            a, b = frs[0]
            if f"test_FR_{a}_{b}" not in name and f"FR-{a}-{b}:" not in name:
                problems.append(f"{cells[0]}: test name '{name}' doesn't start with its requirement (testing.md)")
    missing = [f for f in spec_frs(d) if f not in covered]
    if missing:
        problems.append(f"requirements without a test case: {', '.join(missing)}")
    out({"cases": cases, "problems": problems}, ok=not problems and cases > 0)


def verify_init(d):
    rd = d / "review"
    rd.mkdir(parents=True, exist_ok=True)
    for f in [rd / "snapshot.json", rd / "verify.json", rd / "verify.md", *rd.glob("*.json"), *(rd / "jobs").glob("*")]:
        if f.is_file() and f.name != "prs.json":
            f.unlink()
    out({"cleared": str(rd.relative_to(ROOT))})


def jobs(d):
    js = []
    for repo in REPOS:
        files = changed_files(repo)
        if not files:
            continue
        js.append(f"{repo}:check")
        if repo == "benefit-fe":
            js.append(f"{repo}:build")
        if repo == "benefit-be" and any(re.match(r"(packages/agents|packages/rag|evals)/", f) for f in files):
            js.append(f"{repo}:eval")
    out({"jobs": js}, ok=True)


def make_has(rd, target):
    mf = rd / "Makefile"
    return mf.exists() and re.search(rf"^{target}:", mf.read_text(), re.M)


def job(d, name):
    repo, _, kind = name.partition(":")
    rd = ROOT / "repos" / repo
    if repo not in REPOS or kind not in ("check", "build", "eval") or not (rd / ".git").exists():
        out({"problems": [f"unknown job '{name}'"]}, ok=False)
    if make_has(rd, kind):
        cmd = f"make {kind}"
    elif repo == "benefit-fe" and kind == "check":
        cmd = "pnpm lint && pnpm tsc --noEmit && pnpm vitest run"
    elif repo == "benefit-fe" and kind == "build":
        cmd = "pnpm build"
    else:
        cmd = None
    jd = d / "review" / "jobs"
    jd.mkdir(parents=True, exist_ok=True)
    res = {"job": name, "cmd": cmd}
    if not cmd:
        res.update(status="skipped", reason=f"no '{kind}' target in repos/{repo}")
    else:
        try:
            r = subprocess.run(cmd, shell=True, cwd=rd, capture_output=True, text=True, timeout=3600)
            res["status"] = "pass" if r.returncode == 0 else "fail"
            (jd / f"{name.replace(':', '-')}.log").write_text(r.stdout + r.stderr)
            res["tail"] = (r.stdout + r.stderr)[-2000:]
        except subprocess.TimeoutExpired:
            res["status"] = "fail"
            res["tail"] = "timed out after 3600s"
    (jd / f"{name.replace(':', '-')}.json").write_text(json.dumps(res, indent=2))
    out({k: v for k, v in res.items() if k != "tail"})


def review_list(d):
    try:
        repos = json.loads(read(d / "scope.json")).get("repos", [])
    except ValueError:
        repos = []
    out({"reviews": ["compliance"] + [f"code-{r}" for r in REPOS if r in repos]})


def verify_status(d):
    rd = d / "review"
    job_res = [json.loads(f.read_text()) for f in sorted((rd / "jobs").glob("*.json"))]
    failing = [j for j in job_res if j.get("status") == "fail"]
    lines = ["# Verification", "", "## Tests and builds"]
    lines += [f"- `{j['job']}`: **{j['status']}**" + (f" (log: review/jobs/{j['job'].replace(':', '-')}.log)"
              if j["status"] == "fail" else "") for j in job_res]
    reviews, blocking = {}, len(failing)
    if not failing:  # reviews run only when tests and builds pass, so their results are from this round
        lines += ["", "## Reviews"]
        for f in sorted(rd.glob("*.json")):
            if f.stem in ("verify", "snapshot", "prs", "status"):
                continue
            try:
                r = json.loads(f.read_text())
                n = int(r.get("blocking", 99))
            except (ValueError, TypeError):
                n = 99
            reviews[f.stem] = n
            blocking += n
            lines.append(f"- `{f.stem}`: {n} blocking (see review/{f.stem}.md)")
        if not reviews:
            blocking += 99
            lines.append("- no review results found")
    st = {"blocking": blocking, "jobs_failing": [j["job"] for j in failing], "reviews": reviews}
    (rd / "verify.json").write_text(json.dumps(st, indent=2))
    (rd / "verify.md").write_text("\n".join(lines) + "\n")
    out(st)


def snapshot(d):
    snap = {}
    for repo in REPOS:
        rd = ROOT / "repos" / repo
        if not (rd / ".git").exists():
            continue
        subprocess.run(["git", "-C", str(rd), "add", "-N", "."], capture_output=True)  # include new files
        r = subprocess.run(["git", "-C", str(rd), "stash", "create"], capture_output=True, text=True)
        head = subprocess.run(["git", "-C", str(rd), "rev-parse", "HEAD"], capture_output=True, text=True)
        snap[repo] = r.stdout.strip() or head.stdout.strip()
    (d / "review" / "snapshot.json").write_text(json.dumps(snap) + "\n")
    out(snap)


def ci_wait(d):
    try:
        prs = json.loads(read(d / "review" / "prs.json"))
    except ValueError:
        out({"problems": ["review/prs.json missing or invalid (the PR step writes it)"]}, ok=False)
    results, problems = {}, []
    for repo, url in prs.items():
        r = subprocess.run(["gh", "pr", "checks", url, "--watch", "--interval", "30"], capture_output=True,
                           text=True, timeout=5400)
        text = (r.stdout + r.stderr).strip()
        if "no checks reported" in text:
            results[repo] = "no checks configured"
        elif r.returncode == 0:
            results[repo] = "pass"
        else:
            results[repo] = "fail"
            problems.append(f"{repo}: GitHub Actions failed on {url}")
    out({"ci": results, "problems": problems}, ok=not problems)


def main(argv):
    if len(argv) < 2:
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    cmd, args = argv[1], argv[2:]
    flags = {a for a in args if a.startswith("--")}
    pos = [a for a in args if not a.startswith("--")]
    single = {"spec-check": spec_check, "scope-check": scope_check, "decisions-check": decisions_check,
              "plan-check": plan_check, "tasks-split": tasks_split, "ownership": ownership, "mark-tasks": mark_tasks}
    if cmd in single and len(pos) == 1:
        return single[cmd](fdir(pos[0]))
    multi = {"test-plan-check": test_plan_check, "verify-init": verify_init, "jobs": jobs,
             "review-list": review_list, "verify-status": verify_status, "snapshot": snapshot, "ci-wait": ci_wait}
    if cmd in multi and len(pos) == 1:
        return multi[cmd](fdir(pos[0]))
    if cmd == "use-spec" and len(pos) == 1:
        return use_spec(pos[0])
    if cmd == "job" and len(pos) == 2:
        return job(fdir(pos[0]), pos[1])
    if cmd == "lane-tests" and len(pos) == 2:
        return lane_tests(fdir(pos[0]), pos[1])
    if cmd == "status" and len(pos) == 1:
        return status(pos[0], "--require-clean" in flags)
    if cmd == "trace" and len(pos) in (1, 2):
        mode = pos[1] if len(pos) == 2 else "strict"
        if mode not in ("strict", "warn"):
            out({"problems": [f"trace mode must be strict or warn, got '{mode}'"]}, ok=False)
        return trace(fdir(pos[0]), mode == "warn" or "--warn" in flags)
    if cmd == "inputs-check" and len(pos) == 2:
        problems = []
        if pos[0] not in ("draft", "ask", "none"):
            problems.append(f"pr_mode must be draft, ask or none, got '{pos[0]}'")
        if pos[1] not in ("strict", "warn"):
            problems.append(f"trace_mode must be strict or warn, got '{pos[1]}'")
        out({"pr_mode": pos[0], "trace_mode": pos[1], "problems": problems}, ok=not problems)
    print(__doc__, file=sys.stderr)
    sys.exit(2)


if __name__ == "__main__":
    main(sys.argv)
