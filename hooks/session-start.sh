#!/usr/bin/env bash
# SessionStart hook: KB index freshness + session continuity.
# At session start in a KB project (md+git, plugin vendored), notice markdown
# newer than .gitmark/index.db and tell the agent. The corpus is the engine's
# own: `git ls-files -c -o --exclude-standard -- '*.md'` from the repo root —
# not just docs/; gitignored files are excluded exactly like the engine does.
# Not a KB project (no git, no docs/, no vendored engine) — silent exit 0.
# Never blocks a session: every path exits 0, speaks only through
# SessionStart additionalContext.
#   default — remind (the agent sees the command and decides);
#   --rebuild — rebuild the index quietly; no output on success.
# Session continuity: write .scratch/.session-id from the hook's own
# ZCODE_SESSION_ID (no variable — write nothing, say nothing), and announce
# the newest fresh (≤7 days) handoff file so the next session reads it and
# continues; deep detail — ReadSessionContext on the previous session id
# taken from the file's From line.
# One-emit contract: index freshness, handoff announcement, or both — glued
# into exactly one JSON on stdout (two JSONs broke the runner parser).
set -uo pipefail

root="${ZCODE_PROJECT_DIR:-${CLAUDE_PROJECT_DIR:-$PWD}}"
cd "$root" 2>/dev/null || exit 0

rebuild=0
[[ "${1:-}" == "--rebuild" ]] && rebuild=1

engine=.zcode/skills/kb-search/gitmark.py
index=.gitmark/index.db
scratch=.scratch
handoff_ttl=604800   # 7 days in seconds; beyond this the skill cleans up

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

# Message parts accumulate; the single emit happens once, at the end.
msg=""
add_part() { msg="${msg:+${msg}
}$1"; }

# Session-id marker for /handoff, from the hook's own env (bundle-confirmed).
# No variable — nothing written, nothing said. A value that does not look like
# a session id is not written either: the marker feeds a filename downstream
# (handoff-<id>.md), so junk in would be path injection out.
if [[ "${ZCODE_SESSION_ID:-}" =~ ^sess_[A-Za-z0-9._-]{1,128}$ ]]; then
  if mkdir -p "$scratch" 2>/dev/null; then
    printf '%s\n' "$ZCODE_SESSION_ID" > "$scratch/.session-id" 2>/dev/null || true
  fi
fi

msg_stale='KB: markdown менялся после последней сборки индекса — поиск может отвечать устаревшим. Перестрой индекс: python3 .zcode/skills/kb-search/gitmark.py index'
msg_noindex='KB: поисковый индекс .gitmark/index.db ещё не собран — поиск не работает. Собери: python3 .zcode/skills/kb-search/gitmark.py index'
msg_fail='KB: тихая перестройка индекса не удалась — запусти вручную и разберись: python3 .zcode/skills/kb-search/gitmark.py index'

rebuild_quietly() {
  python3 "$engine" index >/dev/null 2>&1
}

if [[ ! -f "$index" ]]; then
  if (( rebuild )); then
    rebuild_quietly || add_part "$msg_fail"
  else
    add_part "$msg_noindex"
  fi
else
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
      rebuild_quietly || add_part "$msg_fail"
    else
      add_part "$msg_stale"
    fi
  fi
fi

# Handoff announcement: newest handoff file by mtime, only while fresh (≤7
# days). The hook never deletes stale handoffs — cleanup is the skill's job.
newest=""
for f in "$scratch"/handoff-*.md; do
  [[ -f "$f" ]] || continue
  [[ -z "$newest" || "$f" -nt "$newest" ]] && newest="$f"
done
if [[ -n "$newest" ]]; then
  now="$(date +%s)"
  mt="$(stat -c %Y "$newest" 2>/dev/null)" || mt=0
  # < ttl, not <=: at exactly 7 days the file belongs to the skill's cleanup,
  # not to the announcement.
  if (( now - mt < handoff_ttl )); then
    from="$(sed -n 's/^From:[[:space:]]*//p' "$newest" | head -1 | tr -d '\r' | cut -d' ' -f1)"
    if [[ "$from" =~ ^sess_[A-Za-z0-9._-]+$ ]]; then
      add_part "Handoff: свежий handoff прошлой сессии — $newest. Прочти его и продолжи работу; детали, которых в файле нет, — ReadSessionContext(sessionId=$from, strategy=handoff)."
    else
      add_part "Handoff: свежий handoff прошлой сессии — $newest. Прочти его и продолжи работу; id прошлой сессии из файла не распознан — для ReadSessionContext возьми id у оператора (#sess_*)."
    fi
  fi
fi

[[ -n "$msg" ]] && emit "$msg"
exit 0
