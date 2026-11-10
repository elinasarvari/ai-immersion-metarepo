"""Open (or find) a GitHub pull request using the token git already uses for this remote.

Called by create-pr.sh when `gh` is not logged in. The token comes from `git credential fill`
(the macOS keychain, Git Credential Manager, ...) and is only sent to api.github.com; it is never
printed or written to disk.

    github_api.py check <owner/repo>
    github_api.py create <owner/repo> <base> <branch> <title> <body-file-or-empty> <draft:0|1>
    github_api.py edit-body <owner/repo> <pr-number> <body-file>
"""

from __future__ import annotations

import json
import subprocess
import sys
import urllib.error
import urllib.request

API = "https://api.github.com"


def token() -> str:
    done = subprocess.run(
        ["git", "credential", "fill"],
        input="protocol=https\nhost=github.com\n\n",
        capture_output=True,
        text=True,
        env={"GIT_TERMINAL_PROMPT": "0", "PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin"},
        check=False,
    )
    fields = dict(line.split("=", 1) for line in done.stdout.splitlines() if "=" in line)
    value = fields.get("password", "")
    if not value:
        sys.exit("no GitHub credential found for git; push once with git, or run 'gh auth login'")
    return value


def call(method: str, path: str, payload: dict[str, object] | None = None) -> object:
    request = urllib.request.Request(
        f"{API}{path}",
        method=method,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={
            "Authorization": f"Bearer {token()}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        detail = json.loads(error.read() or b"{}")
        errors = "; ".join(str(e.get("message", e)) for e in detail.get("errors", []))
        sys.exit(f"GitHub API {error.code}: {detail.get('message', '')} {errors}".strip())


def check(slug: str) -> None:
    repo = call("GET", f"/repos/{slug}")
    if not isinstance(repo, dict) or not repo.get("permissions", {}).get("push"):
        sys.exit(f"the git credential cannot push to {slug}, so it cannot open PRs there")


def commit_text() -> tuple[str, str]:
    message = subprocess.run(
        ["git", "log", "-1", "--format=%B"], capture_output=True, text=True, check=True
    ).stdout.strip()
    subject, _, body = message.partition("\n")
    return subject, body.strip()


def create(slug: str, base: str, branch: str, title: str, body_file: str, draft: str) -> None:
    owner = slug.split("/", 1)[0]
    existing = call("GET", f"/repos/{slug}/pulls?state=open&head={owner}:{branch}&base={base}")
    if isinstance(existing, list) and existing:
        print(f"PR already open (updated with the new commits): {existing[0]['html_url']}")
        return
    subject, commit_body = commit_text()
    body = open(body_file).read() if body_file else commit_body
    pull = call(
        "POST",
        f"/repos/{slug}/pulls",
        {"title": title or subject, "head": branch, "base": base, "body": body, "draft": draft == "1"},
    )
    assert isinstance(pull, dict)
    print(pull["html_url"])


def edit_body(slug: str, number: str, body_file: str) -> None:
    pull = call("PATCH", f"/repos/{slug}/pulls/{number}", {"body": open(body_file).read()})
    assert isinstance(pull, dict)
    print(f"updated {pull['html_url']}")


if __name__ == "__main__":
    action, *args = sys.argv[1:]
    if action == "check":
        check(*args)
    elif action == "create":
        create(*args)
    elif action == "edit-body":
        edit_body(*args)
    else:
        sys.exit(f"unknown action {action}")
