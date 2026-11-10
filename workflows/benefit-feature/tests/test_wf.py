"""Tests for workflows/benefit-feature/scripts/wf.py.

Run from the metarepo root:  python3 -m unittest discover -s workflows/benefit-feature/tests -v

Each test builds a throwaway metarepo (specs/ + two git clones under repos/) in a temp folder and points wf.py at
it with WF_ROOT, so nothing in the real workspace is read or changed.
"""
import json, os, subprocess, sys, tempfile, textwrap, unittest
from pathlib import Path

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

    def wf(self, *args):
        r = subprocess.run([sys.executable, str(WF), *args], capture_output=True, text=True,
                           env={**os.environ, "WF_ROOT": str(self.root)})
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

    def test_warn_mode_reports_without_blocking(self):
        self.assertEqual(self.job("trace:warn")["status"], "warn")


class ScriptJobs(WfCase):
    def test_ownership(self):
        self.repo_file("benefit-be", "apps/worker/deadline.py", "x = 1\n")
        self.repo_file("benefit-be", "packages/domain/deadline.py", "x = 1\n")
        self.repo_file("benefit-be", "tests/integration/test_x.py", "x = 1\n")
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
        self.assertEqual(data["jobs"], ["benefit-be:check", "benefit-be:eval", "ownership", "tasks", "trace:strict"])

    def test_a_repo_job_with_no_target_warns_instead_of_passing_silently(self):
        res = self.job("benefit-be:eval")
        self.assertEqual(res["status"], "warn")
        self.repo_file("benefit-be", "Makefile", "check:\n\t@exit 3\n")
        self.assertEqual(self.job("benefit-be:check")["status"], "fail")
        self.assertTrue((self.fd / "review" / "jobs" / "benefit-be-check.log").exists())

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

    def test_first_round_needs_no_fix(self):
        self.wf("verify-init", FD)
        self.assertEqual(self.wf("needs-fix", FD)[1], {"fix": False, "blocking": 0})

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


if __name__ == "__main__":
    unittest.main()
