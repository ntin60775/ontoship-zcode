---
node_type: ticket
title: hygiene runbook — ночной lint+index+map
service: _platform
status: archived
updated: 2026-10-04
links:
  part_of: [README.md]
  depends_on: [03-session-start-hook.md]
  implemented_by: [../../scripts/hygiene.sh, ../../hooks/session-start.sh]
---

# 10: hygiene runbook — ночной lint+index+map

**What to build:** ночное обслуживание KB по расписанию (cron/off-peak):
lint+index+map; ночные ошибки не пропадают — sink через `lint --strict`
exit-код в лог, который SessionStart-хук читает и сообщает на старте сессии.
init не меняется (one-pass остаётся).

**Blocked by:** 03 — sink ночных ERR читает SessionStart-хук.

- [x] runbook: команда ночной автоматизации (cron/off-peak), тихий запуск,
      лог ночных ERR — `docs/ops/hygiene.md` + `scripts/hygiene.sh`
- [x] `lint --strict` при проблемах даёт ненулевой exit в лог; хук находит лог
      и сообщает о несвежести (анонс lint≠0 и index≠0; чужой/рукописный лог молчит)
- [x] `gitmark lint` + `pytest` зелёные (93 passed)
