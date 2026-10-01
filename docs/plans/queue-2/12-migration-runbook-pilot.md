---
node_type: ticket
title: migration runbook + пилотный переезд
service: _platform
status: draft
updated: 2026-10-01
links:
  part_of: [README.md]
  depends_on: [03-session-start-hook.md, 04-to-tickets-port.md]
---

# 12: migration runbook + пилотный переезд

**What to build:** полный переезд одного проекта с omp на zcode — runbook и
его первая проверка пилотом, как одна единица: runbook проверяем только
пилотом, разбивка дала бы непроверяемый тикет. Аудит omp-payload
(rule/skill/command → keep/drop/replace; один документ аудита в
`docs/decisions/` проекта-потребителя, ADR — только для спорных правил),
снятие ontoship-payload обоих каналов (plugin remove / локальная копия), init
обновляет общий managed-блок, эквиваленты правил — AGENTS.md/хуки,
deploy-check + lint; omp остаётся терминалом-фоллбэком.

**Blocked by:** 03, 04 — precondition паритета (Constraints плана).

- [ ] runbook в `docs/ops/`: обе категории omp-установки, полный контроль при
      первой миграции, замена payload — по явному подтверждению оператора
- [ ] пилот: полный переезд одного проекта по runbook (аудит с вердиктами,
      снятие, init, верификация deploy-check+lint); 1c/unica-плагины остаются
      omp-фоллбэку
- [ ] у потребителя: скиллы видны по слэшу, deploy-check зелёный, omp-fallback
      проверен
- [ ] `gitmark lint` + `pytest` зелёные
