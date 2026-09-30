#!/usr/bin/env bash
# Deployed-layout check for the OntoShip zcode plugin (run from a consumer
# project root; the runner-vendored copy lives in .zcode/ per deploy.json).
#   exit 0 — vendored code is in place and works;
#   exit 1 — critical problems (fix required);
#   exit 2 — warnings only (works, but with caveats).
#
# Unlike the omp original, the package is NOT resolved from the script
# location: here the package is the project's own .zcode/, so every path is
# resolved from the project root (git toplevel), never from $0.
set -uo pipefail

root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"; cd "$root"
rc=0
warn() { rc=$(( rc == 0 ? 2 : rc )); }

# 1. Vendored layout: key files per the deploy mappings
for p in .zcode/skills/kb-search/gitmark.py .zcode/skills/roles/roles.py \
         .zcode/defaults/roles.md .zcode/deployed.json; do
  [[ -f "$p" ]] || { echo "[FAIL] отсутствует: $p"; rc=1; }
done

#    Journal: parseable, plugin entry present, every mapping target on disk
if [[ -f .zcode/deployed.json ]]; then
  journal="$(python3 - <<'PY' 2>&1
import json, os, sys
try:
    j = json.load(open(".zcode/deployed.json", encoding="utf-8"))
except (OSError, ValueError) as e:
    print(f"[FAIL] журнал .zcode/deployed.json не читается: {e}"); sys.exit(1)
p = j.get("plugins", {}).get("ontoship")
if p is None:
    print("[FAIL] в журнале нет записи плагина ontoship"); sys.exit(1)
print(f"deployed: ontoship@{p.get('ref', '?')}")
ms = p.get("mappings", [])
if not isinstance(ms, list):
    print("[FAIL] mappings в журнале не список"); sys.exit(1)
missing = []
for m in ms:
    to = m.get("to", "") if isinstance(m, dict) else ""
    if not to:
        missing.append("маппинг без 'to'")
    elif not os.path.exists(to):
        missing.append(f"отсутствует: {to}")
    elif os.path.isdir(to) and to.startswith(".zcode/skills/") \
            and not os.path.isfile(os.path.join(to, "SKILL.md")):
        missing.append(f"в скилле нет SKILL.md: {to}")
for what in missing:
    print(f"[FAIL] по журналу {what}")
sys.exit(1 if missing else 0)
PY
)"
  jst=$?
  echo "$journal"
  (( jst != 0 )) && rc=1
fi

# 2. Roles: the vendored default itself is valid and carries the roles
#    (checked by importing the vendored resolver), and resolve from the
#    vendored path finds reviewer — via the default or a project override
roles_py=.zcode/skills/roles/roles.py
roles_md=.zcode/defaults/roles.md
if [[ -f "$roles_py" && -f "$roles_md" ]]; then
  def_out="$(python3 - "$roles_py" "$roles_md" <<'PY' 2>&1
import importlib.util, sys
try:
    spec = importlib.util.spec_from_file_location("roles_check", sys.argv[1])
    roles = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(roles)
    parsed = roles.parse_roles(open(sys.argv[2], encoding="utf-8").read(), sys.argv[2])
except Exception as e:
    print(f"[FAIL] дефолт ролей: {type(e).__name__}: {e}"); sys.exit(1)
if not parsed:
    print("[FAIL] дефолт ролей пуст — ролям в .zcode неоткуда взяться"); sys.exit(1)
if "reviewer" not in parsed:
    print("[FAIL] в дефолте ролей нет reviewer"); sys.exit(1)
print("roles: default OK")
PY
)"
  dst=$?
  echo "$def_out"
  (( dst != 0 )) && rc=1
  roles_out="$(python3 "$roles_py" resolve --json 2>&1)"; rst=$?
  if (( rst != 0 )); then
    echo "[FAIL] roles resolve: ${roles_out//$'\n'/ }"; rc=1
  elif ! python3 -c 'import json,sys; r=json.load(sys.stdin).get("reviewer") or {}; sys.exit(0 if r.get("model") else 1)' <<<"$roles_out"; then
    echo "[FAIL] роли: reviewer не резолвится из .zcode (дефолт не найден?)"; rc=1
  else
    echo "roles: reviewer OK"
  fi
fi

# 3. SQLite: FTS5 is required, trigram is optional (documented degradation)
sql_out="$(python3 - <<'PY'
import sqlite3, sys
c = sqlite3.connect(":memory:")
try:
    c.execute("CREATE VIRTUAL TABLE t USING fts5(x)")
except sqlite3.OperationalError as e:
    print(f"[FAIL] SQLite без FTS5: {e}"); sys.exit(1)
print("FTS5 OK")
try:
    c.execute("CREATE VIRTUAL TABLE t2 USING fts5(x, tokenize='trigram')")
    print("trigram OK")
except sqlite3.OperationalError:
    print("[WARN] trigram-токенайзер недоступен (опционально, нужен SQLite >= 3.34)")
PY
)"
(( $? != 0 )) && rc=1
echo "$sql_out"
if grep -q '^\[WARN\] trigram' <<<"$sql_out"; then
  echo "[WARN] fuzzy/substring-поиск будет ограничен"; warn
fi

# 4. Engine smoke from the vendored path: index + search work in project cwd.
#    --json smoke: text mode prints "nothing found" to stdout, so an
#    "output is non-empty" check would be vacuous. Engine error — FAIL;
#    empty result — WARN (the project KB may lack the word entirely).
engine=.zcode/skills/kb-search/gitmark.py
python3 "$engine" index || { echo "[FAIL] gitmark index"; rc=1; }
smoke="$(python3 "$engine" search "OntoShip" -k 1 --json 2>/dev/null)"; smoke_rc=$?
smoke_compact="${smoke//[[:space:]]/}"
if (( smoke_rc != 0 )); then
  err="$(python3 "$engine" search "OntoShip" -k 1 2>&1 >/dev/null)"
  echo "[FAIL] смоук-поиск: ${err:-движок завершился с ошибкой}"; rc=1
elif [[ -z "$smoke_compact" || "$smoke_compact" == "[]" ]]; then
  echo "[WARN] смоук-поиск без хитов — слова \"OntoShip\" в KB проекта нет; индекс собран"
  warn
fi

echo "deploy-check: exit=$rc"
exit "$rc"
