"""Tests for the feature worktrees in workflows/benefit-feature/run.sh (prepare, worktrees, cleanup) and for
skills/sync-repos/sync-repos.sh accepting them.

Run from the metarepo root:  python3 -m unittest discover -s workflows/benefit-feature/tests -v

Each test builds a throwaway metarepo (a git repo with run.sh, a spec and two clones of local bare "origins") in a
temp folder, with WF_WORKTREES pointing at another temp folder, so nothing in the real workspace is touched. Only
the git side runs: `prepare` never starts the engine, and the fake clones have no pyproject.toml or package.json,
so no dependencies are installed.
"""
import os, shutil, subprocess, tempfile, unittest
from pathlib import Path

META = Path(__file__).resolve().parents[3]
BRANCH = "feature/010-demo"
ENV = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.com", "GIT_COMMITTER_NAME": "t",
       "GIT_COMMITTER_EMAIL": "t@example.com", "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}


def git(*a, cwd):
    return subprocess.run(["git", *a], cwd=cwd, env=ENV, check=True, capture_output=True, text=True).stdout.strip()


class RunWorktreesTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.root, self.wts = self.tmp / "meta", self.tmp / "wts"
        for f in ("workflows/benefit-feature/run.sh", "skills/sync-repos/sync-repos.sh"):
            (self.root / f).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(META / f, self.root / f)
        (self.root / "specs/010-demo").mkdir(parents=True)
        (self.root / "specs/010-demo/spec.md").write_text("# demo\n")
        (self.root / "repos").mkdir()
        (self.root / "repos/.gitkeep").write_text("")
        (self.root / ".gitignore").write_text("repos/*\n!repos/.gitkeep\n.specify/workflows/runs/\n")
        git("init", "-q", "-b", "main", cwd=self.root)
        git("add", "-A", cwd=self.root)
        git("commit", "-q", "-m", "init", cwd=self.root)
        for r in ("benefit-be", "benefit-fe"):
            seed = self.tmp / f"seed-{r}"
            seed.mkdir()
            (seed / "README.md").write_text(r)
            git("init", "-q", "-b", "main", cwd=seed)
            git("add", "-A", cwd=seed)
            git("commit", "-q", "-m", "init", cwd=seed)
            git("clone", "-q", "--bare", str(seed), str(self.tmp / f"{r}.git"), cwd=self.tmp)
            git("clone", "-q", str(self.tmp / f"{r}.git"), str(self.root / "repos" / r), cwd=self.tmp)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_sh(self, *args, ok=True):
        r = subprocess.run(["bash", str(self.root / "workflows/benefit-feature/run.sh"), *args], cwd=self.root,
                           env={**ENV, "WF_WORKTREES": str(self.wts)}, capture_output=True, text=True,
                           stdin=subprocess.DEVNULL)
        out = r.stdout + r.stderr
        self.assertEqual(r.returncode == 0, ok, out)
        return out

    def test_prepare_creates_metarepo_and_clone_worktrees_on_the_feature_branch(self):
        (self.root / "specs/010-demo/spec.md").write_text("# demo, edited and not committed\n")
        self.run_sh("prepare", "010")
        wt = self.wts / "010-demo"
        self.assertEqual(git("symbolic-ref", "--short", "HEAD", cwd=wt), BRANCH)
        self.assertIn("not committed", (wt / "specs/010-demo/spec.md").read_text())  # the spec came along
        for r in ("benefit-be", "benefit-fe"):
            d = wt / "repos" / r
            self.assertTrue((d / ".git").is_file(), "a worktree, not a second clone")
            self.assertEqual(git("symbolic-ref", "--short", "HEAD", cwd=d), BRANCH)
            self.assertEqual(git("rev-parse", "HEAD", cwd=d), git("rev-parse", "origin/main", cwd=d))
            main_clone = self.root / "repos" / r
            self.assertEqual(git("symbolic-ref", "--short", "HEAD", cwd=main_clone), "main")  # left free

    def test_prepare_twice_reuses_the_worktree_and_keeps_its_changes(self):
        self.run_sh("prepare", "010")
        plan = self.wts / "010-demo/specs/010-demo/plan.md"
        plan.write_text("written by the run\n")
        out = self.run_sh("prepare", "010")
        self.assertIn("reusing worktree", out)
        self.assertTrue(plan.exists())

    def test_prepare_frees_the_branch_from_a_clean_main_clone(self):
        be = self.root / "repos/benefit-be"
        git("switch", "-q", "-c", BRANCH, cwd=be)
        self.run_sh("prepare", "010")
        self.assertEqual(git("symbolic-ref", "--short", "HEAD", cwd=be), "main")
        self.assertEqual(git("symbolic-ref", "--short", "HEAD", cwd=self.wts / "010-demo/repos/benefit-be"), BRANCH)

    def test_prepare_stops_when_the_main_clone_has_the_branch_with_uncommitted_changes(self):
        be = self.root / "repos/benefit-be"
        git("switch", "-q", "-c", BRANCH, cwd=be)
        (be / "README.md").write_text("work in progress")
        out = self.run_sh("prepare", "010", ok=False)
        self.assertIn("uncommitted changes", out)
        self.assertEqual((be / "README.md").read_text(), "work in progress")

    def test_sync_repos_accepts_clone_worktrees(self):
        self.run_sh("prepare", "010")
        wt = self.wts / "010-demo"
        r = subprocess.run(["bash", str(wt / "skills/sync-repos/sync-repos.sh"), "--check"], cwd=wt, env=ENV,
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn("submodule", r.stdout)
        self.assertIn("left alone", r.stdout)

    def test_worktrees_lists_branches_and_latest_run(self):
        self.run_sh("prepare", "010")
        run = self.wts / "010-demo/.specify/workflows/runs/ab12cd34"
        run.mkdir(parents=True)
        out = self.run_sh("worktrees")
        self.assertIn("010-demo  (latest run: ab12cd34)", out)
        self.assertIn(BRANCH, out)

    def test_cleanup_refuses_uncommitted_changes_then_removes_and_keeps_branches(self):
        self.run_sh("prepare", "010")
        wt = self.wts / "010-demo"
        (wt / "repos/benefit-be/new.py").write_text("x = 1\n")
        out = self.run_sh("cleanup", "010", "--yes", ok=False)
        self.assertIn("nothing removed", out)
        self.assertTrue(wt.exists())
        (wt / "repos/benefit-be/new.py").unlink()
        self.run_sh("cleanup", "010", ok=False)  # no terminal and no --yes: asks for confirmation, removes nothing
        self.assertTrue(wt.exists())
        self.run_sh("cleanup", "010", "--yes")
        self.assertFalse(wt.exists())
        self.assertTrue(git("branch", "--list", BRANCH, cwd=self.root))
        self.assertTrue(git("branch", "--list", BRANCH, cwd=self.root / "repos/benefit-be"))


if __name__ == "__main__":
    unittest.main()
