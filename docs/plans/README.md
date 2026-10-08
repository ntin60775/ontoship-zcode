---
node_type: index
title: Plans
service: _platform
status: active
updated: 2026-10-08
links:
  part_of: [../README.md]
  relates_to: [../ontology.md]
---

# Plans

Plan contracts (`node_type: plan`). A plan starts as a **file** `docs/plans/<slug>.md`,
written by `grilling`; `/to-tickets` promotes it to a folder with tickets.
`/ship` executes one ticket — or one file plan as a single slice — per hand-launched run.

The table below is generated (`gitmark inventory`, target `plans`) and is the **single
carrier** of plan statuses and ticket counters: change the carriers' frontmatter, then
regenerate — never edit the table by hand.

<!-- BEGIN inventory:plans -->
| Plan | Status | Tickets |
|---|---|---|
| [crossreview-adoption/](crossreview-adoption/README.md) | archived | 3/3 |
| [external-dependencies/](external-dependencies/README.md) | archived | 4/4 |
| [gate-followups/](gate-followups/README.md) | archived | 2/2 |
| [gate-followups-2/](gate-followups-2/README.md) | archived | 7/7 |
| [handoff-snapshot/](handoff-snapshot/README.md) | archived | 3/3 |
| [kb-service-doc.md](kb-service-doc.md) | archived | — |
| [onto-doc-parity.md](onto-doc-parity.md) | active | — |
| [ontology-i7-zcode-paths.md](ontology-i7-zcode-paths.md) | archived | — |
| [queue-2/](queue-2/README.md) | archived | 17/17 |
<!-- END inventory:plans -->

## Порядок выполнения

Статусы планов и тикетов живёт только в таблице-реестре выше; проза здесь —
исключительно решения оператора о порядке:

- миграция шести оставшихся проектов с omp — по runbook queue-2/19, когда
  оператор даст перечень или скажет «все шесть»; в своей очереди идёт
  последней;
- новая работа открывается гриллом или to-tickets: план с резом на тикеты
  сначала раскладывается, затем шипится по одному тикету за прогон.
