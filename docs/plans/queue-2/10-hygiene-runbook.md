---
node_type: ticket
title: hygiene runbook — ночной lint+index+map
service: _platform
status: draft
updated: 2026-10-01
links:
  part_of: [README.md]
  depends_on: [03-session-start-hook.md]
---

# 10: hygiene runbook — ночной lint+index+map

**What to build:** ночное обслуживание KB по расписанию (cron/off-peak):
lint+index+map; ночные ошибки не пропадают — sink через `lint --strict`
exit-код в лог, который SessionStart-хук читает и сообщает на старте сессии.
init не меняется (one-pass остаётся).

**Blocked by:** 03 — sink ночных ERR читает SessionStart-хук.

- [ ] runbook: команда ночной автоматизации (cron/off-peak), тихий запуск,
      лог ночных ERR
- [ ] `lint --strict` при проблемах даёт ненулевой exit в лог; хук находит лог
      и сообщает о несвежести (03 отгружен)
- [ ] `gitmark lint` + `pytest` зелёные
