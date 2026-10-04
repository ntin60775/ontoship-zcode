#!/usr/bin/env bash
#
# hygiene.sh — nightly KB maintenance: lint --strict + index + map, quiet.
#
# The nightly counterpart of the maintain commands in AGENTS.md. Runs the
# engine's lint gate, rebuilds the search index and regenerates the HTML map;
# nothing on stdout when lint passes (cron/off-peak friendly). The point of
# the run is that nightly failures do not vanish: the outcome lands in
# .gitmark/hygiene.log whose last line is machine-readable —
#
#   HYGIENE <iso-date> lint=<rc> index=<rc> map=<rc>
#
# — and the SessionStart hook (.zcode/hooks/session-start.sh) announces a
# lint=<nonzero> at the next session start. The log is rewritten every run:
# the hook reports the LAST nightly run; the fix loop (repair, re-run) closes
# it naturally. Derived data lives in .gitmark/ — gitignored, like the index.
# Exit code is nonzero when any step failed, so plain cron mail sees it too.
#
# Usage:
#   bash .zcode/scripts/hygiene.sh          # vendored, from a consumer repo
#   bash scripts/hygiene.sh                 # dev checkout of the plugin itself
#   cron:   0 3 * * * cd <repo> && bash .zcode/scripts/hygiene.sh
#
# init is deliberately untouched: one-pass stays one-pass (queue-2 constraint).
# No pipelines in this script — pipefail would be dead weight (gate 10).
set -u

root="${ZCODE_PROJECT_DIR:-${CLAUDE_PROJECT_DIR:-$PWD}}"
cd "$root" 2>/dev/null || exit 0

# Same KB-project contract as the hook: md+git, docs/, an engine. Prefer the
# vendored engine (consumers); fall back to the source tree (this dev repo).
git rev-parse --git-dir >/dev/null 2>&1 || exit 0
[[ -d docs ]] || exit 0
engine=""
for cand in .zcode/skills/kb-search/gitmark.py skills/kb-search/gitmark.py; do
  [[ -f "$cand" ]] && engine="$cand" && break
done
[[ -n "$engine" ]] || exit 0

logdir=.gitmark
log="$logdir/hygiene.log"
# A KB project is confirmed by now — failing to make its log dir is a real
# failure and must reach cron as nonzero, not as a silent exit 0 (gate 10).
mkdir -p "$logdir" 2>/dev/null || exit 1

lint_rc=0; index_rc=0; map_rc=0
lint_out="$(python3 "$engine" lint --strict 2>&1)" || lint_rc=$?
python3 "$engine" index >/dev/null 2>&1 || index_rc=$?
python3 "$engine" map -o docs-map.html >/dev/null 2>&1 || map_rc=$?

# Rewrite the log (last run only). On lint failure the ERRs ride along — the
# log is the sink the hook points at, so the agent reads the findings there,
# not a bare exit code. An unwritable sink is itself a failure: exit 1, never
# mask the run behind it (gate 10 — the chmod-555 repro).
if ! {
  echo "hygiene run $(date '+%Y-%m-%dT%H:%M:%S%z') in $root (engine: $engine)"
  if (( lint_rc != 0 )); then
    echo "--- lint --strict output ---"
    printf '%s\n' "$lint_out"
    echo "----------------------------"
  fi
  echo "HYGIENE $(date '+%Y-%m-%dT%H:%M:%S%z') lint=$lint_rc index=$index_rc map=$map_rc"
} > "$log" 2>/dev/null; then
  exit 1
fi

(( lint_rc == 0 && index_rc == 0 && map_rc == 0 )) && exit 0
exit 1
