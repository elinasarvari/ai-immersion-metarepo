#!/usr/bin/env python3
"""Prints the allow rules the unattended agent steps need that a Claude Code settings file lacks (nothing = ok).

  python3 workflows/benefit-feature/scripts/check_permissions.py .claude/settings.json

The agent steps run as `claude -p` with no one to approve a prompt, so a command that isn't allowed is
refused and a coding step stalls on it. run.sh calls this before starting or resuming a run.
"""
import json, sys

NEEDED = [
    "Read", "Edit", "Write", "Glob", "Grep",
    "Bash(git *)", "Bash(gh *)", "Bash(make *)", "Bash(uv *)", "Bash(pnpm *)", "Bash(python3 *)", "Bash(bash *)",
    "Bash(.specify/scripts/*)", "Bash(skills/*)", "Bash(workflows/*)",
    "Bash(cd *)", "Bash(mkdir *)", "Bash(sed *)", "Bash(mv *)", "Bash(cp *)", "Bash(rm *)",
    "Bash(node *)", "Bash(npx *)",
]


def main(path):
    try:
        allow = set(json.load(open(path)).get("permissions", {}).get("allow", []))
    except (OSError, ValueError) as e:
        print(f"unreadable: {e}")
        return 1
    missing = [r for r in NEEDED if r not in allow]
    print(" ".join(missing))
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else ".claude/settings.json"))
