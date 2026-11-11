#!/usr/bin/env python3
"""The AI tool a run's agent steps use: Claude Code (`claude -p`) or GitHub Copilot CLI (`copilot -p`).

  ai.py args <saved-inputs.json|""> [run.sh args ...]   integration on line 1, then the run.sh args to use
  ai.py check <claude|copilot>                           exit 1 with the reason if the CLI can't run unattended
  ai.py guard                                            Copilot PreToolUse hook (.github/hooks/benefit-guard.json)

`args`: the integration comes from `-i integration=...`, else the run's saved inputs (resume), else the project's
(.specify/integration.json). The model inputs default to Claude Code aliases (opus, sonnet), which Copilot CLI
doesn't know, so for Copilot each alias becomes a Copilot model ID (override with WF_COPILOT_OPUS,
WF_COPILOT_SONNET, WF_COPILOT_HAIKU), and back to the alias when a run switches to Claude.

`guard`: Copilot CLI runs with every tool allowed (Spec Kit passes --yolo), and its own deny rules can't match
flags (`git push --force`). This hook denies the same commands as the "deny" list in .claude/settings.json, which
Claude Code applies, so both tools refuse the same things.
"""
import fnmatch, json, os, re, shlex, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
WORKFLOW = ROOT / "workflows/benefit-feature/workflow.yml"
SUPPORTED = ("claude", "copilot")
COPILOT_MODELS = {"opus": "claude-opus-5.5", "sonnet": "claude-sonnet-5.5", "haiku": "claude-haiku-5.5"}
INSTALL = {"claude": "npm install -g @anthropic-ai/claude-code",
           "copilot": "npm install -g @github/copilot (or brew install copilot-cli), then copilot login"}


def workflow_models():
    """The *_model inputs and their defaults, from workflow.yml."""
    text = WORKFLOW.read_text() if WORKFLOW.exists() else ""
    return dict(re.findall(r'^\s+(\w+_model):\s*\{[^}]*default:\s*"([^"]+)"', text, re.M))


def to_copilot(model):
    return os.environ.get(f"WF_COPILOT_{model.upper()}", COPILOT_MODELS[model]) if model in COPILOT_MODELS else model


def to_claude(model):
    m = re.fullmatch(r"claude-(opus|sonnet|haiku)-[\d.]+", model)
    return m.group(1) if m and "." in model else model


def split_inputs(argv):
    """[(index of the value, key, value)] for every `-i key=value` / `--input key=value`."""
    found = []
    for i, a in enumerate(argv[1:], 1):
        if argv[i - 1] in ("-i", "--input") and "=" in a:
            k, v = a.split("=", 1)
            found.append((i, k, v))
    return found


def project_integration():
    try:
        return json.loads((ROOT / ".specify/integration.json").read_text()).get("integration") or "claude"
    except (OSError, ValueError):
        return "claude"


def resolve(saved, argv):
    """(integration, argv with the model inputs that integration needs)."""
    given = {k: v for _, k, v in split_inputs(argv)}
    try:
        saved_inputs = json.loads(Path(saved).read_text()).get("inputs", {}) if saved else {}
    except (OSError, ValueError):
        saved_inputs = {}
    ai = given.get("integration") or saved_inputs.get("integration") or "auto"
    if ai == "auto":
        ai = project_integration()
    convert = to_copilot if ai == "copilot" else to_claude
    argv = list(argv)
    for key, default in workflow_models().items():
        current = given.get(key) or saved_inputs.get(key) or default
        new = convert(current)
        if key in given:
            for i, k, _ in split_inputs(argv):
                if k == key:
                    argv[i] = f"{key}={new}"
        elif new != current:
            argv += ["-i", f"{key}={new}"]
    return ai, argv


def check(ai):
    """Problem with the CLI for `ai`, or "" when it runs."""
    if ai not in SUPPORTED:
        return f"integration '{ai}' isn't supported; use {' or '.join(SUPPORTED)}"
    try:
        r = subprocess.run([ai, "--version"], stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=60)
    except FileNotFoundError:
        return f"{ai} isn't installed: {INSTALL[ai]}"
    except subprocess.TimeoutExpired:
        return f"`{ai} --version` didn't answer within 60s"
    out = (r.stdout + r.stderr).strip()
    if r.returncode or not re.search(r"\d+\.\d+", out):  # e.g. VS Code's `copilot` shim, which offers to install
        last = out.splitlines()[-1] if out else f"exit {r.returncode}"
        return f"{ai} doesn't run unattended (`{ai} --version`: {last}); {INSTALL[ai]}"
    return ""


def deny_patterns(settings=ROOT / ".claude/settings.json"):
    rules = json.loads(Path(settings).read_text()).get("permissions", {}).get("deny", [])
    return [r[5:-1] for r in rules if r.startswith("Bash(") and r.endswith(")")]


def commands(line):
    """Each simple command in a shell line, normalised the way the deny patterns are written."""
    for part in re.split(r"&&|\|\||[;|&\n()`]|\$\(", line):
        try:
            words = shlex.split(part)
        except ValueError:
            words = part.split()
        while words and (re.match(r"^\w+=", words[0]) or words[0] in ("env", "command", "exec", "sudo", "nohup")):
            words.pop(0)
        if words and words[0] == "git":  # git's global options come before the subcommand the patterns name
            rest, words = words[1:], ["git"]
            while rest and rest[0].startswith("-"):
                opt = rest.pop(0)
                if opt in ("-C", "-c") and rest:
                    rest.pop(0)
            words += rest
        if words:
            yield " ".join(words)


def denied(line, patterns):
    """The deny pattern `line` hits, or None."""
    for cmd in commands(line):
        for p in patterns:
            if fnmatch.fnmatchcase(cmd, p):
                return p
    return None


def guard(stdin):
    """Exit status for the hook: 2 (with the reason) denies, 0 lets Copilot's own permissions decide."""
    try:
        payload = json.loads(stdin or "{}")
        args = payload.get("tool_input", payload.get("toolArgs"))
        if isinstance(args, str):
            args = json.loads(args)
        line = args.get("command") if isinstance(args, dict) else None
        hit = denied(line, deny_patterns()) if isinstance(line, str) else None
    except Exception:  # a broken hook must not block every command; Copilot fails a crashed PreToolUse closed
        return 0
    if not hit:
        return 0
    reason = f"denied by .claude/settings.json (Bash({hit})), the same rule Claude Code applies to the agents"
    print(json.dumps({"permissionDecision": "deny", "permissionDecisionReason": reason}))
    print(reason, file=sys.stderr)
    return 2


def main(argv):
    cmd = argv[1] if len(argv) > 1 else ""
    if cmd == "args" and len(argv) > 2:
        ai, args = resolve(argv[2], argv[3:])
        print("\n".join([ai, *args]))
        return 0
    if cmd == "check" and len(argv) == 3:
        problem = check(argv[2])
        print(problem)
        return 1 if problem else 0
    if cmd == "guard":
        return guard(sys.stdin.read())
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
