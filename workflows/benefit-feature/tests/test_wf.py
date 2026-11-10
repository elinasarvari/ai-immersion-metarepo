"""Tests for workflows/benefit-feature/scripts/wf.py.

Run from the metarepo root:  python3 -m unittest discover -s workflows/benefit-feature/tests -v

Each test builds a throwaway metarepo (specs/ + two git clones under repos/) in a temp folder and points wf.py at
it with WF_ROOT, so nothing in the real workspace is read or changed.
"""
import json, os, socket, subprocess, sys, tempfile, textwrap, unittest
from pathlib import Path
from unittest import mock

WF = Path(__file__).resolve().parents[1] / "scripts" / "wf.py"
FD = "specs/010-demo"

SPEC = """# Feature: demo
## User Scenarios
### Acceptance Scenarios
1. Given a household, when it extends, then ten days are added.
## Requirements
- **FR-010-01** The system adds ten days on extension.
- **FR-010-02** The UI shows the new deadline.
## Success Criteria
- Works.
"""
PLAN = """# Plan
Targets repos/benefit-be and repos/benefit-fe.
## Architecture decisions
- ADR-010-01 (Accepted)
"""
ADR = """# ADR-010-01: Store deadlines
**Status:** {status}
## Context
x
## Options
### Option A
a
### Option B
b
## Decision
A
## Consequences
c
## How we verify it
tests
"""
TASKS = """# Tasks
- [ ] T001 [contracts][benefit-be] Add Deadline model (FR-010-01)
- [ ] T002 [workflows][benefit-be] Extend deadline activity (FR-010-01)
- [ ] T003 [platform-ui][benefit-fe] Show deadline (FR-010-02)
- [ ] T004 [qa][benefit-be] Contract test
"""
TEST_PLAN = """# Test plan
## Cases
| ID | Proves | Level | Lane / repo | Test name | Data |
|---|---|---|---|---|---|
| TC-01 | FR-010-01 | unit | workflows-lane / benefit-be | test_FR_010_01_extension_adds_ten_days | seed |
| TC-02 | FR-010-02 | unit | platform-ui-lane / benefit-fe | FR-010-02: shows the new deadline | seed |
"""


def sh(*cmd, cwd):
    subprocess.run(cmd, cwd=cwd, check=True, capture_output=True)


class WfCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.fd = self.root / FD
        self.write("spec.md", SPEC)
        self.write("plan.md", PLAN)
        self.write("decisions/README.md", "# Decisions\n")
        self.write("decisions/ADR-010-01-store.md", ADR.format(status="Accepted"))
        self.write("scope.json", json.dumps({"lanes": ["workflows-lane", "platform-ui-lane"],
                                             "repos": ["benefit-be", "benefit-fe"]}))
        self.write("tasks.md", TASKS)
        self.write("test-plan.md", TEST_PLAN)
        for repo in ("benefit-be", "benefit-fe"):
            rd = self.root / "repos" / repo
            rd.mkdir(parents=True)
            sh("git", "init", "-q", "-b", "main", cwd=rd)
            sh("git", "config", "user.email", "t@example.com", cwd=rd)
            sh("git", "config", "user.name", "t", cwd=rd)
            (rd / "README.md").write_text("x\n")
            sh("git", "add", "-A", cwd=rd)
            sh("git", "commit", "-qm", "init", cwd=rd)
            sh("git", "update-ref", "refs/remotes/origin/main", "HEAD", cwd=rd)
            sh("git", "switch", "-qc", "feature/010-demo", cwd=rd)

    def tearDown(self):
        self.tmp.cleanup()

    # helpers
    def write(self, rel, text, base=None):
        p = (base or self.fd) / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(textwrap.dedent(text))
        return p

    def repo_file(self, repo, rel, text):
        return self.write(rel, text, base=self.root / "repos" / repo)

    def wf(self, *args, path_prefix=None):
        env = {**os.environ, "WF_ROOT": str(self.root)}
        if path_prefix:
            env["PATH"] = f"{path_prefix}{os.pathsep}{env['PATH']}"
        r = subprocess.run([sys.executable, str(WF), *args], capture_output=True, text=True, env=env)
        try:
            data = json.loads(r.stdout.splitlines()[0]) if r.stdout.strip() else {}
        except ValueError:
            data = {"raw": r.stdout}
        return r.returncode, data, r.stdout

    def job(self, name):
        code, data, _ = self.wf("job", FD, name)
        self.assertEqual(code, 0, "a job never fails the step itself")
        return data

    def add_passing_tests(self):
        self.repo_file("benefit-be", "tests/apps/worker/test_deadline.py",
                       "def test_FR_010_01_extension_adds_ten_days():\n    assert True\n")
        self.repo_file("benefit-fe", "src/deadline.test.tsx",
                       "test('FR-010-02: shows the new deadline', () => {})\n")


class Gates(WfCase):
    def test_prepare_selects_spec_and_counts_open_questions(self):
        self.write("spec.md", SPEC + "\n[NEEDS CLARIFICATION: which timezone?]\n")
        code, data, _ = self.wf("prepare", "010", "draft", "strict")
        self.assertEqual(code, 0)
        self.assertEqual((data["feature_dir"], data["branch"], data["open"]), (FD, "feature/010-demo", 1))
        self.assertTrue((self.root / ".specify" / "feature.json").exists())

    def test_prepare_accepts_number_folder_name_or_path(self):
        for arg in ("010", "010-demo", "specs/010-demo"):
            with self.subTest(arg):
                code, data, _ = self.wf("prepare", arg, "ask", "strict")
                self.assertEqual((code, data.get("feature_dir")), (0, FD), data)

    def test_prepare_accepts_every_pr_mode(self):
        for mode in ("draft", "ask", "none"):
            with self.subTest(mode):
                self.assertEqual(self.wf("prepare", "010", mode, "strict")[0], 0)
        self.assertEqual(self.wf("prepare", "010", "ready", "strict")[0], 1)

    def test_a_new_run_clears_an_earlier_runs_lane_reports_and_knows_it_is_an_update(self):
        self.write("lanes/workflows-lane/done.json", json.dumps({"tasks": ["T002"]}))
        self.write("lanes/workflows-lane/blocked.md", "old note\n")
        code, data, _ = self.wf("prepare", "010", "draft", "strict")
        self.assertEqual(code, 0)
        self.assertTrue(data["update"], "tasks.md exists, so this run updates an earlier one")
        self.assertEqual(len(data["cleared_lane_reports"]), 2)
        self.assertFalse((self.fd / "lanes/workflows-lane/done.json").exists())
        self.assertFalse((self.fd / "lanes/workflows-lane/blocked.md").exists())

    def test_prepare_rejects_bad_inputs_and_bad_spec(self):
        self.assertEqual(self.wf("prepare", "010", "yolo", "strict")[0], 1)
        self.assertEqual(self.wf("prepare", "999", "draft", "strict")[0], 1)
        self.write("spec.md", "# no sections\n")
        code, data, _ = self.wf("prepare", "010", "draft", "strict")
        self.assertEqual(code, 1)
        self.assertTrue(any("User Scenarios" in p for p in data["problems"]))

    def test_plan_gate_passes_a_complete_plan(self):
        code, data, _ = self.wf("plan-gate", FD)
        self.assertEqual(code, 0, data)
        self.assertEqual((data["accepted"], data["open"]), (1, 0))
        self.assertEqual(data["lanes"], ["platform-ui-lane", "workflows-lane"])

    def test_plan_gate_counts_decisions_that_need_a_person(self):
        self.write("decisions/ADR-010-01-store.md", ADR.format(status="Needs decision"))
        code, data, _ = self.wf("plan-gate", FD)
        self.assertEqual((code, data["open"]), (0, 1))

    def test_plan_gate_catches_each_kind_of_problem(self):
        cases = {
            "ADR section": ("decisions/ADR-010-01-store.md", ADR.format(status="Accepted").replace("## Consequences", "")),
            "Accepted ADR not in plan": ("plan.md", "Targets repos/benefit-be and repos/benefit-fe.\n"),
            "scope repo not in plan": ("plan.md", PLAN.replace(" and repos/benefit-fe", "")),
            "unknown lane": ("scope.json", json.dumps({"lanes": ["magic"], "repos": ["benefit-be"]})),
        }
        for label, (rel, text) in cases.items():
            with self.subTest(label):
                self.tearDown()
                self.setUp()
                self.write(rel, text)
                code, data, _ = self.wf("plan-gate", FD)
                self.assertEqual(code, 1, f"{label}: {data}")

    def test_tasks_gate_passes_and_splits_lanes(self):
        code, data, _ = self.wf("tasks-gate", FD)
        self.assertEqual(code, 0, data)
        self.assertEqual(data["lanes"], ["platform-ui-lane", "workflows-lane"])
        self.assertEqual((data["contracts_tasks"], data["qa_tasks"], data["cases"]), (1, 1, 2))

    def test_ids_the_spec_only_mentions_are_not_its_requirements(self):
        self.write("spec.md", SPEC + "\n## Moved\n| Old | New |\n|---|---|\n| FR-010-03 | FR-011-01 |\n"
                   "Review reasons are in FR-012-01.\n")
        code, data, _ = self.wf("tasks-gate", FD)
        self.assertEqual(code, 0, data)

    def test_a_contracts_task_that_waits_for_lane_work_moves_to_the_qa_step(self):
        self.write("tasks.md", TASKS + "- [ ] T005 [contracts][benefit-be] Regenerate openapi.json after T002 and T003\n"
                   "- [ ] T006 [contracts][benefit-be] Write the model tests before T001\n")
        code, data, _ = self.wf("tasks-gate", FD)
        self.assertEqual(code, 0, data)
        self.assertEqual(data["late_contracts"], ["T005"], "T006 only refers to another contracts task")
        self.assertEqual((data["contracts_tasks"], data["qa_tasks"]), (2, 2))

    def test_tasks_gate_catches_each_kind_of_problem(self):
        cases = {
            "untagged task": ("tasks.md", TASKS + "- [ ] T005 Do something\n"),
            "lane outside scope": ("tasks.md", TASKS + "- [ ] T005 [agents][benefit-be] Prompt\n"),
            "FR without a test case": ("test-plan.md", TEST_PLAN.split("| TC-02")[0]),
            "test name not starting with FR": ("test-plan.md", TEST_PLAN.replace("test_FR_010_01_", "test_")),
            "unknown level": ("test-plan.md", TEST_PLAN.replace("| unit | workflows", "| smoke | workflows")),
            "no test plan": ("test-plan.md", ""),
        }
        for label, (rel, text) in cases.items():
            with self.subTest(label):
                self.tearDown()
                self.setUp()
                self.write(rel, text)
                code, data, _ = self.wf("tasks-gate", FD)
                self.assertEqual(code, 1, f"{label}: {data}")


AUTO_DECISION = """
**Decided by:** decision-maker (automated), 2026-11-10; architect recommended Option A
**Revisit if:** volumes exceed 10k cases
"""


class Decisions(WfCase):
    def open_adr(self, status="Needs decision"):
        self.write("decisions/ADR-010-02-retention.md", ADR.format(status=status).replace("ADR-010-01", "ADR-010-02"))

    def auto_decide(self, chosen="Option A", recommended="Option A", record=True):
        self.write("decisions/ADR-010-02-retention.md", ADR.format(status="Accepted – auto-decided")
                   .replace("ADR-010-01", "ADR-010-02").replace("## Decision\nA", "## Decision\n" + chosen + AUTO_DECISION))
        self.write("decisions/README.md", "# Decisions\n## Decided automatically (review in the PR)\n- ADR-010-02\n")
        if record:
            self.write("decisions/auto-decisions.json", json.dumps(
                [{"adr": "ADR-010-02", "kind": "product", "chosen": chosen, "recommended": recommended,
                  "revisit_if": "volumes exceed 10k cases"}]))

    def test_plan_gate_requires_the_target_repos_from_the_feature_map(self):
        feature_map = (
            "| Feature | Lane | Target repo(s) | Depends on | Day 1? |\n|---|---|---|---|---|\n"
            "| [010 Demo](010-demo/spec.md) | Workflows | benefit-be, benefit-fe | 000 | No |\n"
        )
        self.write("specs/README.md", feature_map, base=self.root)
        self.write("plan.md", PLAN.replace(" and repos/benefit-fe", ""))
        self.write("scope.json", json.dumps({"lanes": ["workflows-lane"], "repos": ["benefit-be"]}))

        code, data, _ = self.wf("plan-gate", FD)

        self.assertEqual(code, 1, data)
        self.assertTrue(any("feature map" in p and "benefit-fe" in p for p in data["problems"]), data)
        self.assertTrue(any("platform-ui-lane" in p for p in data["problems"]), data)

    def test_plan_gate_passes_when_scope_covers_the_feature_map(self):
        feature_map = "| [010 Demo](010-demo/spec.md) | Workflows | benefit-be, benefit-fe | 000 | No |\n"
        self.write("specs/README.md", feature_map, base=self.root)

        code, data, _ = self.wf("plan-gate", FD)

        self.assertEqual(code, 0, data)

    def test_plan_gate_lists_open_adrs_of_both_kinds(self):
        self.open_adr("Proposed – needs amendment")
        code, data, _ = self.wf("plan-gate", FD)
        self.assertEqual((code, data["open"], data["needs_amendment"]), (0, 1, 1), data)
        self.assertEqual(data["open_adrs"], ["ADR-010-02-retention.md"])

    def test_auto_decided_counts_as_accepted_and_the_plan_must_reference_it(self):
        self.auto_decide()
        code, data, _ = self.wf("plan-gate", FD)
        self.assertEqual(code, 1, "plan.md doesn't mention ADR-010-02 yet")
        self.assertEqual((data["open"], data["auto_decided"]), (0, 1))
        self.write("plan.md", PLAN + "- ADR-010-02 (Accepted – auto-decided)\n")
        self.assertEqual(self.wf("plan-gate", FD)[0], 0)

    def test_decisions_gate_passes_and_reports_no_plan_update_when_the_recommendation_was_chosen(self):
        self.auto_decide("Option A", "Option A")
        code, data, _ = self.wf("decisions-gate", FD)
        self.assertEqual((code, data["auto_decided"], data["plan_update_needed"]), (0, ["ADR-010-02"], []), data)

    def test_decisions_gate_asks_for_a_plan_update_when_another_option_was_chosen(self):
        self.auto_decide("Option B: archive monthly", "Option A")
        code, data, _ = self.wf("decisions-gate", FD)
        self.assertEqual((code, data["plan_update_needed"]), (0, ["ADR-010-02"]), data)

    def test_decisions_gate_fails_while_anything_is_open_or_unrecorded(self):
        cases = {
            "still open": lambda: self.open_adr(),
            "no auto-decisions.json": lambda: self.auto_decide(record=False),
            "no Revisit-if line": lambda: (self.auto_decide(), self.write(
                "decisions/ADR-010-02-retention.md",
                (self.fd / "decisions/ADR-010-02-retention.md").read_text().replace("**Revisit if:**", "Later:"))),
            "json lists an ADR that wasn't auto-decided": lambda: (self.auto_decide(), self.write(
                "decisions/auto-decisions.json", json.dumps([{"adr": "ADR-010-02", "chosen": "Option A"},
                                                             {"adr": "ADR-010-01", "chosen": "Option A"}]))),
        }
        for label, setup in cases.items():
            with self.subTest(label):
                self.tearDown()
                self.setUp()
                setup()
                code, data, _ = self.wf("decisions-gate", FD)
                self.assertEqual(code, 1, f"{label}: {data}")

    def test_prepare_checks_decision_mode(self):
        self.assertEqual(self.wf("prepare", "010", "draft", "strict", "auto")[1]["decision_mode"], "auto")
        self.assertEqual(self.wf("prepare", "010", "draft", "strict")[1]["decision_mode"], "auto")
        self.assertEqual(self.wf("prepare", "010", "draft", "strict", "maybe")[0], 1)


class Trace(WfCase):
    def test_passes_when_every_planned_test_is_defined(self):
        self.add_passing_tests()
        res = self.job("trace:strict")
        self.assertEqual(res["status"], "pass", res)
        self.assertIn("Defined in", (self.fd / "review" / "trace.md").read_text())

    def test_a_mention_in_a_comment_is_not_a_test(self):
        self.add_passing_tests()
        self.repo_file("benefit-be", "tests/apps/worker/test_deadline.py",
                       "# TODO test_FR_010_01_extension_adds_ten_days\ndef test_other():\n    pass\n")
        res = self.job("trace:strict")
        self.assertEqual(res["status"], "fail")
        self.assertIn("FR-010-01", res["unproven"])

    def test_a_skipped_test_does_not_count(self):
        self.add_passing_tests()
        self.repo_file("benefit-be", "tests/apps/worker/test_deadline.py",
                       "import pytest\n\n@pytest.mark.skip(reason='later')\n"
                       "def test_FR_010_01_extension_adds_ten_days():\n    pass\n")
        self.repo_file("benefit-fe", "src/deadline.test.tsx", "test.skip('FR-010-02: shows the new deadline', () => {})\n")
        res = self.job("trace:strict")
        self.assertEqual(res["status"], "fail")
        self.assertEqual(sum(p.startswith("TC-") and "skipped" in p for p in res["problems"]), 2, res["problems"])

    def test_a_test_in_the_wrong_repo_or_a_non_test_file_does_not_count(self):
        self.add_passing_tests()
        self.repo_file("benefit-be", "tests/apps/worker/test_deadline.py", "def test_x():\n    pass\n")
        self.repo_file("benefit-fe", "src/test_deadline.py", "def test_FR_010_01_extension_adds_ten_days():\n    pass\n")
        self.repo_file("benefit-be", "apps/worker/deadline.py", "def test_FR_010_01_extension_adds_ten_days():\n    pass\n")
        self.assertEqual(self.job("trace:strict")["status"], "fail")

    def test_a_unit_test_in_a_folder_that_needs_services_is_flagged(self):
        """Feature 001's CI failure: a unit test under tests/db/, whose conftest connects to MongoDB."""
        self.add_passing_tests()
        self.repo_file("benefit-be", "tests/apps/worker/test_deadline.py", "def test_other():\n    pass\n")
        self.repo_file("benefit-be", "tests/db/seeds/test_deadline.py",
                       "def test_FR_010_01_extension_adds_ten_days():\n    assert True\n")
        res = self.job("trace:strict")
        self.assertEqual(res["status"], "fail")
        self.assertTrue(any("need MongoDB" in p for p in res["problems"]), res["problems"])

    def test_warn_mode_reports_without_blocking(self):
        self.assertEqual(self.job("trace:warn")["status"], "warn")


class ScriptJobs(WfCase):
    def test_ownership(self):
        self.repo_file("benefit-be", "apps/worker/deadline.py", "x = 1\n")
        self.repo_file("benefit-be", "packages/domain/deadline.py", "x = 1\n")
        self.repo_file("benefit-be", "tests/integration/test_x.py", "x = 1\n")
        self.repo_file("benefit-be", "openapi/openapi.json", "{}\n")  # generated contract, contracts step
        self.repo_file("benefit-fe", "src/App.tsx", "x\n")
        self.assertEqual(self.job("ownership")["status"], "pass")
        self.repo_file("benefit-be", "packages/agents/prompt.py", "x = 1\n")  # agents lane isn't in scope
        self.repo_file("benefit-be", "random/thing.py", "x = 1\n")           # nobody owns it
        res = self.job("ownership")
        self.assertEqual(res["status"], "fail")
        self.assertEqual(len(res["problems"]), 2, res["problems"])

    def test_tasks_marks_lane_reports_and_fails_while_any_is_open(self):
        self.write("lanes/workflows-lane/done.json", json.dumps({"tasks": ["T002"]}))
        self.write("lanes/platform-ui-lane/blocked.md", "T003 needs a change in packages/domain\n")
        res = self.job("tasks")
        self.assertEqual((res["status"], res["marked"]), ("fail", ["T002"]))
        self.assertTrue(any("blocked.md" in p for p in res["problems"]))
        self.assertIn("- [X] T002", (self.fd / "tasks.md").read_text())
        self.write("tasks.md", TASKS.replace("[ ]", "[X]"))
        res = self.job("tasks")
        self.assertEqual((res["status"], res["problems"]), ("pass", []))

    def test_jobs_lists_script_checks_and_only_changed_repos(self):
        code, data, _ = self.wf("jobs", FD, "warn")
        self.assertEqual(data["jobs"], ["ownership", "tasks", "trace:warn"])
        self.repo_file("benefit-be", "packages/agents/prompt.py", "x = 1\n")
        code, data, _ = self.wf("jobs", FD)
        self.assertEqual(data["jobs"], ["benefit-be:check", "benefit-be:eval", "e2e", "ownership", "tasks",
                                        "trace:strict"])

    def test_a_repo_job_with_no_target_warns_instead_of_passing_silently(self):
        res = self.job("benefit-be:eval")
        self.assertEqual(res["status"], "warn")
        self.repo_file("benefit-be", "Makefile", "check:\n\t@exit 3\n")
        self.assertEqual(self.job("benefit-be:check")["status"], "fail")
        self.assertTrue((self.fd / "review" / "jobs" / "benefit-be-check.log").exists())

    def test_a_check_diffing_a_generated_file_sees_uncommitted_work_but_still_catches_drift(self):
        rd = self.root / "repos" / "benefit-be"
        self.repo_file("benefit-be", "spec.json", "v1\n")
        sh("git", "add", "spec.json", cwd=rd)
        sh("git", "commit", "-qm", "spec", cwd=rd)
        # The feature changed the generated file and the loop committed nothing: still a pass.
        self.repo_file("benefit-be", "spec.json", "v2\n")
        self.repo_file("benefit-be", "Makefile", "check:\n\tgit diff --exit-code spec.json\n")
        self.assertEqual(self.job("benefit-be:check")["status"], "pass")
        # Regenerating changes the file: drift, so a fail.
        self.repo_file("benefit-be", "Makefile", "check:\n\techo v3 > spec.json\n\tgit diff --exit-code spec.json\n")
        self.assertEqual(self.job("benefit-be:check")["status"], "fail")
        # The real index was never touched.
        self.assertEqual(subprocess.run(["git", "diff", "--cached", "--name-only"], cwd=rd, capture_output=True,
                                        text=True).stdout, "")
        # A check whose tests make and commit to their own git repo still works (no GIT_INDEX_FILE leaks in).
        own = self.root / "own-repo"
        self.repo_file("benefit-be", "Makefile",
                       f"check:\n\tgit init -q {own} && git -C {own} -c user.name=t -c user.email=t@example.com"
                       " commit -q --allow-empty -m x\n")
        self.assertEqual(self.job("benefit-be:check")["status"], "pass")

    def test_e2e_only_for_code_changes_and_never_on_a_busy_stack_port(self):
        self.repo_file("benefit-be", "docs/notes.md", "x\n")
        self.assertNotIn("e2e", self.wf("jobs", FD)[1]["jobs"])
        with socket.socket() as busy:
            busy.bind(("127.0.0.1", 0))
            busy.listen()
            with mock.patch.dict(os.environ, {"WF_STACK_PORTS": str(busy.getsockname()[1])}):
                self.repo_file("benefit-be", "Makefile", "verify:\n\t@touch ran\n")
                res = self.job("e2e")
        self.assertEqual(res["status"], "warn")
        self.assertIn("in use", res["problems"][0])
        self.assertFalse((self.root / "repos/benefit-be/ran").exists())

    def test_e2e_checks_both_repos_working_trees_and_restores_both_indexes(self):
        fe = self.root / "repos" / "benefit-fe"
        self.repo_file("benefit-fe", "client.ts", "v1\n")
        sh("git", "add", "client.ts", cwd=fe)
        sh("git", "commit", "-qm", "client", cwd=fe)
        self.repo_file("benefit-fe", "client.ts", "v2\n")  # regenerated by the feature, not committed
        self.repo_file("benefit-be", "Makefile", "verify:\n\tgit -C ../benefit-fe diff --exit-code client.ts\n")
        with mock.patch.dict(os.environ, {"WF_STACK_PORTS": ""}):
            self.assertEqual(self.job("e2e")["status"], "pass")
        for repo in ("benefit-be", "benefit-fe"):
            self.assertEqual(subprocess.run(["git", "diff", "--cached", "--name-only"], cwd=self.root / "repos" / repo,
                                            capture_output=True, text=True).stdout, "")

    def test_a_stack_port_held_by_this_project_does_not_count_as_busy(self):
        script = self.root / "repos" / "benefit-be" / "hold_port.py"
        script.write_text("import socket, sys, time\ns = socket.socket()\ns.bind(('127.0.0.1', 0))\ns.listen()\n"
                          "print(s.getsockname()[1], flush=True)\ntime.sleep(30)\n")
        proc = subprocess.Popen([sys.executable, str(script)], stdout=subprocess.PIPE, text=True,
                                cwd=script.parent)
        try:
            port = proc.stdout.readline().strip()
            with mock.patch.dict(os.environ, {"WF_STACK_PORTS": port}):
                self.assertEqual(self.wf("ports")[1]["busy"], [])
        finally:
            proc.kill()
            proc.wait()

    def test_each_round_counts_only_its_own_jobs(self):
        self.write("review/jobs/trace.json", json.dumps({"job": "trace", "status": "fail"}))
        self.wf("jobs", FD)
        self.assertFalse((self.fd / "review" / "jobs" / "trace.json").exists())

    def test_unknown_job_is_recorded_as_failing(self):
        self.assertEqual(self.job("nope")["status"], "fail")


class VerifyLoop(WfCase):
    def result(self, name, blocking):
        self.write(f"review/{name}.json", json.dumps({"blocking": blocking, "verdict": "FAIL" if blocking else "PASS",
                                                     "findings": []}))

    def green_jobs(self):
        self.write("review/jobs/ownership.json", json.dumps({"job": "ownership", "status": "pass"}))

    def reviews(self):
        return self.wf("review-list", FD)[1]["reviews"]

    def status_with(self, blocking_reviews):
        """One verify round: green jobs, one review with this many blocking findings."""
        self.green_jobs()
        for n in ("compliance", "code-benefit-be", "code-benefit-fe"):
            self.result(n, 0)
        self.result("compliance", blocking_reviews)
        return self.wf("verify-status", FD)[1]

    def test_the_loop_keeps_going_while_it_makes_progress(self):
        rounds = [self.status_with(n) for n in (5, 3, 2, 1)]
        self.assertEqual([r["continue"] for r in rounds], [True, True, True, True])
        self.assertEqual(rounds[-1]["history"], [5, 3, 2, 1])
        self.assertFalse(self.status_with(0)["continue"], "nothing blocking")

    def test_the_loop_stops_when_two_rounds_make_no_progress(self):
        rounds = [self.status_with(n) for n in (3, 4, 4)]  # this run's shape: fixes surfaced new findings
        self.assertEqual([r["continue"] for r in rounds], [True, True, False])
        self.assertIn("no progress", rounds[-1]["why"])
        self.assertEqual(self.wf("final-gate", FD)[0], 1)

    def test_the_loop_stops_at_the_round_cap(self):
        rounds = [self.status_with(n) for n in (9, 8, 7, 6, 5, 4)]
        self.assertEqual(rounds[-1]["continue"], False)
        self.assertIn("6 rounds", rounds[-1]["why"])

    def test_later_fixes_use_the_judgement_model(self):
        models = []
        for n in (4, 3, 2):
            self.status_with(n)
            models.append(self.wf("needs-fix", FD, "sonnet", "opus")[1]["fix_model"])
        self.assertEqual(models, ["sonnet", "opus", "opus"])

    def test_first_round_needs_no_fix(self):
        self.wf("verify-init", FD)
        self.assertEqual(self.wf("needs-fix", FD)[1], {"fix": False, "blocking": 0, "round": 1, "fix_model": "sonnet"})

    def test_no_reviews_while_a_job_fails(self):
        self.write("review/jobs/ownership.json", json.dumps({"job": "ownership", "status": "fail"}))
        self.assertEqual(self.reviews(), [])
        st = self.wf("verify-status", FD)[1]
        self.assertEqual((st["blocking"], st["reviews"]), (1, {}))
        self.assertTrue(self.wf("needs-fix", FD)[1]["fix"])

    def test_reviews_rerun_only_where_needed(self):
        self.green_jobs()
        self.assertEqual(self.reviews(), ["compliance", "code-benefit-be", "code-benefit-fe"])
        self.assertFalse((self.fd / "review" / "snapshot.json").exists(), "round 1 is a full review")
        for n in ("compliance", "code-benefit-be", "code-benefit-fe"):
            self.result(n, 0)
        self.assertEqual(self.reviews(), [], "nothing changed and nothing blocks")
        self.repo_file("benefit-fe", "src/App.tsx", "changed\n")
        self.assertEqual(self.reviews(), ["compliance", "code-benefit-fe"])
        self.assertTrue((self.fd / "review" / "snapshot.json").exists())
        for n in ("compliance", "code-benefit-fe"):
            self.result(n, 0)
        self.result("code-benefit-be", 2)
        self.assertEqual(self.reviews(), ["code-benefit-be"], "a blocking review reruns even with no change")
        (self.fd / "review" / "code-benefit-fe.json").unlink()
        self.assertIn("code-benefit-fe", self.reviews(), "a missing result reruns")

    def test_delta_shows_only_the_change_since_the_last_review_including_new_files(self):
        self.green_jobs()
        self.repo_file("benefit-be", "apps/worker/old.py", "before = 1\n")
        self.reviews()                                  # round 1 records the trees reviewed
        self.repo_file("benefit-be", "apps/worker/new.py", "after = 2\n")
        self.reviews()                                  # round 2 writes snapshot.json = round 1 trees
        code, _, text = self.wf("delta", FD, "benefit-be")
        self.assertEqual(code, 0)
        self.assertIn("after = 2", text)
        self.assertNotIn("before = 1", text)
        self.assertEqual(subprocess.run(["git", "status", "--porcelain", "-uall"], cwd=self.root / "repos/benefit-be",
                                        capture_output=True, text=True).stdout.count("??"), 2,
                         "the real index is untouched (new files stay untracked)")

    def test_status_blocks_on_missing_or_broken_results_and_not_on_warnings(self):
        self.green_jobs()
        self.write("review/jobs/benefit-be-eval.json", json.dumps({"job": "benefit-be:eval", "status": "warn",
                                                                  "problems": ["no eval target"]}))
        self.result("compliance", 0)
        self.result("code-benefit-be", 0)
        self.write("review/code-benefit-fe.json", "not json")
        st = self.wf("verify-status", FD)[1]
        self.assertEqual(st["blocking"], 99)
        self.assertEqual(st["warnings"], ["benefit-be:eval"])
        self.assertIn("Warnings", (self.fd / "review" / "verify.md").read_text())
        self.assertEqual(self.wf("final-gate", FD)[0], 1)
        self.result("code-benefit-fe", 0)
        self.assertEqual(self.wf("verify-status", FD)[1]["blocking"], 0)
        self.assertEqual(self.wf("final-gate", FD)[0], 0)

    def test_no_job_results_is_blocking_and_init_clears_everything_but_prs(self):
        self.write("review/prs.json", "{}")
        self.result("compliance", 0)
        self.assertEqual(self.wf("verify-status", FD)[1]["blocking"], 99)
        self.wf("verify-init", FD)
        self.assertEqual(sorted(p.name for p in (self.fd / "review").iterdir() if p.is_file()), ["prs.json"])
        self.assertEqual(self.wf("final-gate", FD)[0], 1)


class WorkflowFile(unittest.TestCase):
    """workflow.yml passes Spec Kit's own validator (step types, ids, expressions, gates, fan-out templates)."""

    def test_workflow_yml_is_valid(self):
        try:
            tools = subprocess.run(["uv", "tool", "dir"], capture_output=True, text=True, check=True).stdout.strip()
        except (OSError, subprocess.CalledProcessError):
            self.skipTest("uv isn't installed, so Spec Kit's validator can't be found")
        py = Path(tools) / "specify-cli" / "bin" / "python"
        if not py.exists():
            self.skipTest("specify-cli isn't installed as a uv tool")
        code = ("import sys, pathlib; from specify_cli.workflows.engine import WorkflowDefinition, validate_workflow; "
                "errs = validate_workflow(WorkflowDefinition.from_yaml(pathlib.Path(sys.argv[1]))); "
                "print(chr(10).join(errs)); sys.exit(1 if errs else 0)")
        r = subprocess.run([str(py), "-c", code, str(WF.parents[1] / "workflow.yml")], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


WATCH = WF.parent / "watch.py"
RUN_SH = WF.parents[1] / "run.sh"


class Monitor(unittest.TestCase):
    """scripts/watch.py (the live view) and run.sh (the entry point)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "specs" / "010-demo").mkdir(parents=True)

    def tearDown(self):
        self.tmp.cleanup()

    def run_dir(self, status, events, current, results=None):
        d = self.root / ".specify" / "workflows" / "runs" / "abc12345"
        d.mkdir(parents=True, exist_ok=True)
        t = "2026-11-10T18:00:0{}+00:00"
        (d / "log.jsonl").write_text("\n".join(json.dumps(dict(e, timestamp=t.format(i % 10)))
                                               for i, e in enumerate(events)))
        (d / "state.json").write_text(json.dumps({"status": status, "current_step_id": current,
                                                  "created_at": t.format(0), "step_results": results or {}}))
        (d / "inputs.json").write_text(json.dumps({"inputs": {"feature": "010-demo", "pr_mode": "ask"}}))
        return d

    def watch(self):
        r = subprocess.run([sys.executable, str(WATCH), "abc12345", "--once"], capture_output=True, text=True,
                           env={**os.environ, "WF_ROOT": str(self.root)})
        self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout

    def test_every_top_level_step_of_the_workflow_has_a_stage(self):
        import re
        ids = re.findall(r"^  - id: (\w+)", (WF.parents[1] / "workflow.yml").read_text(), re.M)
        sys.path.insert(0, str(WATCH.parent))
        import watch
        self.assertEqual(ids, [s[0] for s in watch.STAGES], "watch.STAGES is out of step with workflow.yml")

    def test_a_failed_run_shows_where_why_and_how_to_continue(self):
        ev = lambda e, sid, **k: {"event": e, "step_id": sid, **k}
        self.run_dir("failed", [ev("step_started", "sync"), ev("step_completed", "sync", status="completed"),
                                ev("step_started", "architect"), ev("step_failed", "architect", error="Prompt exited with code 1")],
                     "architect", {"architect": {"status": "failed", "error": "Prompt exited with code 1",
                                                 "output": {"stderr": "Permission denied for Write"}}})
        out = self.watch()
        self.assertRegex(out, r"✓ .*Sync the repos")
        self.assertRegex(out, r"✗ .*Architect")
        self.assertIn("Stopped at 'architect'", out)
        self.assertIn("Permission denied for Write", out)
        self.assertIn("run.sh resume abc12345", out)

    def test_a_paused_run_shows_the_gate_and_its_verdict_input(self):
        self.run_dir("paused", [{"event": "step_started", "step_id": "pr_approval"},
                                {"event": "step_started", "step_id": "pr_approval:approve_pr"}], "approve_pr")
        out = self.watch()
        self.assertIn("Waiting for you at 'approve_pr'", out)
        self.assertIn("-i pr_verdict=approve", out)

    def test_an_if_stage_counts_as_running_while_its_inner_step_runs(self):
        ev = lambda e, sid, **k: {"event": e, "step_id": sid, **k}
        self.run_dir("running", [ev("step_started", "decide"), ev("step_completed", "decide", status="completed"),
                                 ev("step_started", "decision_maker")], "decision_maker")
        self.assertRegex(self.watch(), r"▶ .*Decision-maker.*now: decision_maker")

    def test_parallel_inner_steps_show_as_one_running_stage(self):
        ev = lambda e, sid, **k: {"event": e, "step_id": sid, **k}
        self.run_dir("running", [ev("step_started", "lanes"), ev("step_completed", "lanes", status="completed"),
                                 ev("step_started", "lanes:lane:0"), ev("step_started", "lanes:lane:1"),
                                 ev("step_started", "lanes:lane:2"), ev("step_completed", "lanes:lane:1")], "lanes")
        self.assertRegex(self.watch(), r"▶ .*Lanes, in parallel.*2 in parallel")

    def test_permission_check_names_what_the_agents_lack(self):
        check = WF.parent / "check_permissions.py"
        full = self.root / "full.json"
        sys.path.insert(0, str(check.parent))
        import check_permissions
        full.write_text(json.dumps({"permissions": {"allow": check_permissions.NEEDED}}))
        self.assertEqual(subprocess.run([sys.executable, str(check), str(full)]).returncode, 0)
        thin = self.root / "thin.json"
        thin.write_text(json.dumps({"permissions": {"allow": ["Read", "Bash(git *)"]}}))
        r = subprocess.run([sys.executable, str(check), str(thin)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 1)
        self.assertIn("Bash(rm *)", r.stdout)

    def test_run_sh_parses_and_shows_usage(self):
        self.assertEqual(subprocess.run(["bash", "-n", str(RUN_SH)]).returncode, 0)
        r = subprocess.run(["bash", str(RUN_SH)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)
        self.assertIn("run.sh start", r.stdout)


FAKE_GH = """#!/usr/bin/env python3
import json, os, sys
a = sys.argv[1:]
log = os.path.join(os.path.dirname(__file__), "calls.log")
open(log, "a").write(" ".join(a) + "\\n")
green = os.path.exists(os.path.join(os.path.dirname(__file__), "GREEN"))
if a[:2] == ["pr", "checks"] and "--watch" in a:
    print("all checks done"); sys.exit(0 if green else 1)
if a[:2] == ["pr", "checks"] and "--json" in a:
    print(json.dumps([{"name": "unit", "state": "FAILURE",
                       "link": "https://github.com/o/benefit-be/actions/runs/11/job/22"},
                      {"name": "static", "state": "SUCCESS", "link": "https://github.com/o/benefit-be/actions/runs/11/job/23"}]))
    sys.exit(1)
if a[:2] == ["run", "view"]:
    print("E   setting MONGO_URL_APP: missing; required"); sys.exit(0)
if a[:2] == ["pr", "view"]:
    print("true"); sys.exit(0)
if a[:2] == ["pr", "ready"]:
    sys.exit(0)
sys.exit(0)
"""


class GitHubActions(WfCase):
    """The CI loop: ci-wait reports instead of failing, marks green drafts ready; ci-gate decides."""

    def fake_gh(self, green):
        bin_dir = self.root / "bin"
        bin_dir.mkdir(exist_ok=True)
        gh = bin_dir / "gh"
        gh.write_text(FAKE_GH)
        gh.chmod(0o755)
        marker = bin_dir / "GREEN"
        marker.write_text("") if green else (marker.unlink() if marker.exists() else None)
        self.write("review/prs.json", json.dumps({"benefit-be": "https://github.com/o/benefit-be/pull/2"}))
        return bin_dir

    def calls(self):
        return (self.root / "bin" / "calls.log").read_text()

    def test_no_ci_result_yet_needs_no_fix(self):
        self.assertEqual(self.wf("ci-needs-fix", FD)[1], {"fix": False, "failing": 0})

    def test_a_red_check_is_reported_with_its_log_and_goes_to_the_fix_step(self):
        bin_dir = self.fake_gh(green=False)
        code, data, _ = self.wf("ci-wait", FD, "draft", path_prefix=bin_dir)
        self.assertEqual(code, 0, "ci-wait never fails; ci-gate decides after the fix rounds")
        self.assertEqual((data["ci"], data["failing"], data["ready"]), ({"benefit-be": "fail"}, 1, []))
        report = (self.fd / "review" / "ci.md").read_text()
        self.assertIn("`unit`", report)
        self.assertIn("MONGO_URL_APP: missing", report)
        self.assertNotIn("`static`", report, "only failing checks are reported")
        self.assertNotIn("pr ready", self.calls(), "a red PR is never marked ready")
        self.assertTrue(self.wf("ci-needs-fix", FD)[1]["fix"])
        self.assertEqual(self.wf("ci-gate", FD)[0], 1)

    def test_all_green_marks_a_draft_ready_for_review(self):
        bin_dir = self.fake_gh(green=True)
        code, data, _ = self.wf("ci-wait", FD, "draft", path_prefix=bin_dir)
        self.assertEqual((code, data["failing"]), (0, 0))
        self.assertEqual(data["ready"], ["https://github.com/o/benefit-be/pull/2"])
        self.assertIn("pr ready https://github.com/o/benefit-be/pull/2", self.calls())
        self.assertEqual(self.wf("ci-gate", FD)[0], 0)

    def test_ask_mode_leaves_the_pr_as_it_is(self):
        bin_dir = self.fake_gh(green=True)
        self.assertEqual(self.wf("ci-wait", FD, "ask", path_prefix=bin_dir)[1]["ready"], [])
        self.assertNotIn("pr ready", self.calls())


if __name__ == "__main__":
    unittest.main()
