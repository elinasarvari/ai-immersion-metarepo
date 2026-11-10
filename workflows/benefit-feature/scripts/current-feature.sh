#!/usr/bin/env bash
# Print the current Spec Kit feature as JSON (read from .specify/feature.json, written by /speckit-specify).
# {"feature_dir": "specs/003-x", "feature": "003-x", "branch": "feature/003-x", "spec_file": ..., "plan_file": ..., "tasks_file": ..., "review_dir": ...}
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd -P)"
fj="$root/.specify/feature.json"
[ -f "$fj" ] || { echo "No current feature: $fj not found. Run /speckit-specify first." >&2; exit 1; }
dir="$(python3 -I -c 'import json,sys; print(json.load(open(sys.argv[1]))["feature_directory"])' "$fj")"
dir="${dir#"$root"/}"; dir="${dir%/}"
[ -d "$root/$dir" ] || { echo "Feature folder $dir does not exist" >&2; exit 1; }
name="${dir##*/}"
python3 -I -c 'import json,sys; d,n=sys.argv[1],sys.argv[2]; print(json.dumps({"feature_dir":d,"feature":n,"branch":"feature/"+n,"spec_file":d+"/spec.md","plan_file":d+"/plan.md","tasks_file":d+"/tasks.md","review_dir":d+"/review"}))' "$dir" "$name"
