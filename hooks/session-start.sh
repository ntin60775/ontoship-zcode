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
# the rolling snapshot .scratch/handoff-current.md by its explicit name
# whenever it exists, regardless of age — an old snapshot means no work
# happened, so announcing it is even more important; without the snapshot —
# the newest fresh (≤7 days) legacy handoff-*.md, until the old files are
# cleaned (handoff-snapshot/03). Deep detail — ReadSessionContext on the
# session id taken from the file's From line.
# Nightly hygiene: scripts/hygiene.sh (cron/off-peak) writes
# .gitmark/hygiene.log whose last line is
#   HYGIENE <iso-date> lint=<rc> index=<rc> map=<rc>
# a lint=<nonzero> or index=<nonzero> is announced here so nightly KB errors
# do not vanish (a transient index-rebuild failure on unchanged md is NOT
# caught by the freshness check — nothing is newer than the index; gate 10);
# the map is cosmetic — the log and the script's exit code carry it.
# Unparseable or missing log — silence. One-emit contract: index freshness,
# hygiene, handoff announcement, or any mix — glued into exactly one JSON.
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

# Nightly hygiene (ticket 10): the last log line is machine-written by
# scripts/hygiene.sh. The date token is an ISO stamp with at most a timezone
# tail — the bare non-whitespace tail the first version allowed leaked
# arbitrary log text into the announcement (gate 10, reproduced end-to-end),
# and a hand-edited or foreign log must say nothing.
hygiene_log=.gitmark/hygiene.log
if [[ -f "$hygiene_log" ]]; then
  last="$(tail -n 1 "$hygiene_log" 2>/dev/null)"
  if [[ "$last" =~ ^HYGIENE\ ([0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}([+-][0-9]{2}:?[0-9]{2}|Z)?)\ lint=([0-9]+)\ index=([0-9]+)\ map=([0-9]+)$ ]]; then
    if (( 10#${BASH_REMATCH[3]} != 0 )); then
      add_part "KB: ночной гигиенический прогон от ${BASH_REMATCH[1]} нашёл ошибки lint --strict — разбери лог $hygiene_log и почини; после починки прогон перезапишет лог: bash .zcode/scripts/hygiene.sh (runbook: docs/ops/hygiene.md)"
    elif (( 10#${BASH_REMATCH[4]} != 0 )); then
      add_part "KB: ночной гигиенический прогон от ${BASH_REMATCH[1]} не смог перестроить индекс (index=${BASH_REMATCH[4]}) — запусти python3 .zcode/skills/kb-search/gitmark.py index и разберись; детали в логе $hygiene_log"
    fi
  fi
fi

# Handoff announcement. The rolling snapshot .scratch/handoff-current.md —
# the one file /handoff and /ship rewrite in full on every write — is
# announced by its explicit name whenever it exists, regardless of age: an
# old snapshot means no work happened, and it is announced all the more. The
# legacy glob handoff-*.md also matches that name (it announced the snapshot
# live, with this TTL ticking), so the explicit check comes first — the
# snapshot is never stale by design. Without the snapshot — migration
# fallback (ticket 03 cleans the old files): newest legacy handoff-*.md by
# mtime, only while fresh (≤7 days). The hook never deletes handoffs —
# cleanup is the skill's job.
handoff=""
label=""
if [[ -f "$scratch/handoff-current.md" ]]; then
  handoff="$scratch/handoff-current.md"
  label="слепок состояния проекта"
else
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
      handoff="$newest"
      label="свежий handoff прошлой сессии"
    fi
  fi
fi
if [[ -n "$handoff" ]]; then
  from="$(sed -n 's/^From:[[:space:]]*//p' "$handoff" | head -1 | tr -d '\r' | cut -d' ' -f1)"
  if [[ "$from" =~ ^sess_[A-Za-z0-9._-]+$ ]]; then
    add_part "Handoff: $label — $handoff. Прочти его и продолжи работу; детали, которых в файле нет, — ReadSessionContext(sessionId=$from, strategy=handoff)."
  else
    add_part "Handoff: $label — $handoff. Прочти его и продолжи работу; id прошлой сессии из файла не распознан — для ReadSessionContext возьми id у оператора (#sess_*)."
  fi
fi

[[ -n "$msg" ]] && emit "$msg"
exit 0
