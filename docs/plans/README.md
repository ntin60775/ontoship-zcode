---
node_type: index
title: Plans
service: _platform
status: active
updated: 2026-09-30
links:
  part_of: [../README.md]
  relates_to: [../ontology.md]
---

# Plans

Plan contracts (`node_type: plan`). A plan starts as a **file** `docs/plans/<slug>.md`,
written by `grilling`; `/to-tickets` (backlog) promotes it to a folder with tickets.
`/ship` executes one ticket — or one file plan as a single slice — per hand-launched run.

- [kb-service-doc.md](kb-service-doc.md) — задокументировать сервис kb-search в KB
  (file plan; внутренний смоук девфлоу).
- [queue-2/](queue-2/README.md) — очередь 2: доставка (install, deploy-check, хук),
  порт to-tickets, хвост срезов и подготовленный переезд с omp (папка, 4 тикета головы).
