#!/usr/bin/env bash
# SessionStart hook: keep the KB index no older than the markdown.
# At session start in a KB project (md+git, plugin vendored), notice markdown
# newer than .gitmark/index.db and tell the agent. The corpus is the engine's
# own: `git ls-files -c -o --exclude-standard -- '*.md'` from the repo root —
# not just docs/; gitignored files are excluded exactly like the engine does.
# Not a KB project (no git, no docs/, no vendored engine) — silent exit 0.
# Never blocks a session: every path exits 0, speaks only through
# SessionStart additionalContext.
#   default — remind (the agent sees the command and decides);
#   --rebuild — rebuild the index quietly; no output on success.
set -uo pipefail

root="${ZCODE_PROJECT_DIR:-${CLAUDE_PROJECT_DIR:-$PWD}}"
cd "$root" 2>/dev/null || exit 0

rebuild=0
[[ "${1:-}" == "--rebuild" ]] && rebuild=1

engine=.zcode/skills/kb-search/gitmark.py
index=.gitmark/index.db

# Not a KB project: md+git is the contract, so no git repo — silence;
# same for no knowledge base and no vendored engine.
git rev-parse --git-dir >/dev/null 2>&1 || exit 0
[[ -d docs && -f "$engine" ]] || exit 0

emit() {
  MSG="$1" python3 -c 'import json, os, sys
sys.stdout.write(json.dumps(
    {"hookSpecificOutput": {"hookEventName": "SessionStart",
                            "additionalContext": os.environ["MSG"]}},
    ensure_ascii=False) + "\n")'
}

msg_stale='KB: markdown менялся после последней сборки индекса — поиск может отвечать устаревшим. Перестрой индекс: python3 .zcode/skills/kb-search/gitmark.py index'
msg_noindex='KB: поисковый индекс .gitmark/index.db ещё не собран — поиск не работает. Собери: python3 .zcode/skills/kb-search/gitmark.py index'
msg_fail='KB: тихая перестройка индекса не удалась — запусти вручную и разберись: python3 .zcode/skills/kb-search/gitmark.py index'

rebuild_quietly() {
  python3 "$engine" index >/dev/null 2>&1
}

if [[ ! -f "$index" ]]; then
  if (( rebuild )); then
    rebuild_quietly || emit "$msg_fail"
  else
    emit "$msg_noindex"
  fi
  exit 0
fi

# Stale = any md of the engine corpus with mtime between the index build and
# now. Future mtimes (clock skew, extracted archives) are skipped: a rebuild
# cannot get ahead of them, so they must not nag forever.
now="$(date +%s)"
stale=0
while IFS= read -r -d '' f; do
  [[ -f "$f" ]] || continue
  mt="$(stat -c %Y "$f" 2>/dev/null)" || continue
  (( mt > now )) && continue
  if [[ "$f" -nt "$index" ]]; then stale=1; break; fi
done < <(git ls-files -z -c -o --exclude-standard -- '*.md' 2>/dev/null)

if (( stale )); then
  if (( rebuild )); then
    rebuild_quietly || emit "$msg_fail"
  else
    emit "$msg_stale"
  fi
fi

exit 0
