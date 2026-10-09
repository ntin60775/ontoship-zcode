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
| [gate-risk-scaling.md](gate-risk-scaling.md) | draft | — |
| [handoff-snapshot/](handoff-snapshot/README.md) | archived | 3/3 |
| [kb-service-doc.md](kb-service-doc.md) | archived | — |
| [lens-substrate-flash.md](lens-substrate-flash.md) | draft | — |
| [onto-doc-parity.md](onto-doc-parity.md) | archived | — |
| [ontology-i7-zcode-paths.md](ontology-i7-zcode-paths.md) | archived | — |
| [queue-2/](queue-2/README.md) | archived | 17/17 |
| [run-args-discipline.md](run-args-discipline.md) | draft | — |
<!-- END inventory:plans -->

## Порядок выполнения

Статусы планов и тикетов живёт только в таблице-реестре выше; проза здесь —
исключительно решения оператора о порядке. Решение оператора 2026-10-09:
сначала доделать планы разработки (все три прогрилены 2026-10-09 —
субагент-грилл + challenger dwfrun-c3a6d4a4, substantial-возражения
пере-решены), затем — реальная эксплуатация (ADR
[invariant-moratorium](../decisions/invariant-moratorium.md)).

1. **lens-substrate-flash** — субстрат линз на дефолтных субагентах Flash
   (убирает класс finish=length и обслуживание LENS_PROFILES; приёмка A/B —
   гибрид с посевом, решение оператора 2026-10-09).
2. **gate-risk-scaling** — лёгкий контур гейта для доковых диффов (движок уже
   даёт docs-only ростер; добавляются условный confirm и доковая ветка
   шагов 6/7/9 скилла ship).
3. **run-args-discipline** — префлайт args перед сабмитом рана (уроки 10–11
   contour).
4. **Реальная эксплуатация** — миграция шести оставшихся проектов с omp по
   runbook queue-2/19 (ждёт перечень или «все шесть» от оператора) и
   повседневное использование KB/гейтов в рабочих проектах.

Расширение инвариантов/реестров сверх моратория — только от записанного
инцидента гнили.
