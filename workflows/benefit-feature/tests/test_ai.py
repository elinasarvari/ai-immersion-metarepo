"""Tests for workflows/benefit-feature/scripts/ai.py (which AI CLI runs the agents, its models, the Copilot guard).

Run from the metarepo root:  python3 -m unittest discover -s workflows/benefit-feature/tests -v
"""
import json, os, sys, tempfile, unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import ai  # noqa: E402


class ResolveTest(unittest.TestCase):
    def test_claude_keeps_the_aliases_and_adds_nothing(self):
        self.assertEqual(ai.resolve("", ["-i", "integration=claude"]), ("claude", ["-i", "integration=claude"]))

    def test_copilot_turns_every_default_alias_into_a_copilot_model(self):
        name, args = ai.resolve("", ["-i", "integration=copilot", "-i", "trace_mode=warn"])
        self.assertEqual(name, "copilot")
        self.assertIn("judgement_model=claude-opus-5.5", args)
        self.assertIn("coding_model=claude-sonnet-5.5", args)
        self.assertIn("test_plan_model=claude-sonnet-5.5", args)
        self.assertIn("trace_mode=warn", args)

    def test_copilot_maps_a_given_alias_in_place_and_keeps_a_full_id(self):
        _, args = ai.resolve("", ["-i", "integration=copilot", "-i", "coding_model=opus", "-i", "test_plan_model=gpt-6"])
        self.assertIn("coding_model=claude-opus-5.5", args)
        self.assertNotIn("coding_model=opus", args)
        self.assertIn("test_plan_model=gpt-6", args)

    def test_copilot_model_override_from_the_environment(self):
        with mock.patch.dict(os.environ, {"WF_COPILOT_OPUS": "claude-opus-6"}):
            _, args = ai.resolve("", ["-i", "integration=copilot"])
        self.assertIn("judgement_model=claude-opus-6", args)

    def test_resume_takes_the_saved_integration_and_switching_back_to_claude_restores_the_aliases(self):
        with tempfile.TemporaryDirectory() as tmp:
            saved = Path(tmp) / "inputs.json"
            saved.write_text(json.dumps({"inputs": {"integration": "copilot", "judgement_model": "claude-opus-5.5",
                                                    "coding_model": "claude-sonnet-5.5"}}))
            self.assertEqual(ai.resolve(str(saved), []), ("copilot", ["-i", "test_plan_model=claude-sonnet-5.5"]))
            name, args = ai.resolve(str(saved), ["-i", "integration=claude"])
        self.assertEqual(name, "claude")
        self.assertIn("judgement_model=opus", args)
        self.assertIn("coding_model=sonnet", args)

    def test_auto_is_the_projects_integration(self):
        with mock.patch.object(ai, "project_integration", return_value="claude"):
            self.assertEqual(ai.resolve("", [])[0], "claude")

    def test_the_model_inputs_are_read_from_the_workflow(self):
        self.assertEqual(set(ai.workflow_models()), {"judgement_model", "coding_model", "test_plan_model"})


class GuardTest(unittest.TestCase):
    def run_guard(self, command, fmt="claude"):
        payload = ({"tool_name": "Bash", "tool_input": {"command": command}} if fmt == "claude"
                   else {"toolName": "bash", "toolArgs": json.dumps({"command": command})})
        with mock.patch("sys.stdout"), mock.patch("sys.stderr"):
            return ai.guard(json.dumps(payload))

    def test_the_settings_deny_list_is_enforced(self):
        for cmd in ("git push --force origin feature/x", "git push origin main", "git reset --hard HEAD~1",
                    "git clean -fdx", "rm -rf specs/010-demo", "git push -f"):
            self.assertEqual(self.run_guard(cmd), 2, cmd)

    def test_compound_commands_global_git_options_and_env_prefixes_are_seen_through(self):
        for cmd in ('cd repos/benefit-be && git push --force-with-lease',
                    'git -C "/Users/x/AE Immersion Workshop/repos/benefit-be" push origin main',
                    "GIT_TRACE=1 git push -f origin feature/x", "make check; git clean -n"):
            self.assertEqual(self.run_guard(cmd), 2, cmd)
        self.assertEqual(self.run_guard("git reset --hard", fmt="copilot"), 2)

    def test_the_agents_everyday_commands_pass(self):
        for cmd in ("git push origin feature/011-applicant-waits", "git commit -m 'fix: x'", "make check",
                    "rm -f review/verify.json", "git -C repos/benefit-fe status", "pnpm lint && pnpm typecheck"):
            self.assertEqual(self.run_guard(cmd), 0, cmd)

    def test_other_tools_and_bad_input_never_block(self):
        self.assertEqual(ai.guard(json.dumps({"tool_name": "Edit", "tool_input": {"file_path": "x"}})), 0)
        self.assertEqual(ai.guard("not json"), 0)


if __name__ == "__main__":
    unittest.main()
