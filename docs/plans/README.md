---
node_type: index
title: Plans
service: _platform
status: active
updated: 2026-10-04
links:
  part_of: [../README.md]
  relates_to: [../ontology.md]
---

# Plans

Plan contracts (`node_type: plan`). A plan starts as a **file** `docs/plans/<slug>.md`,
written by `grilling`; `/to-tickets` promotes it to a folder with tickets.
`/ship` executes one ticket — or one file plan as a single slice — per hand-launched run.

- [kb-service-doc.md](kb-service-doc.md) — задокументировать сервис kb-search в KB
  (file plan; внутренний смоук девфлоу).
- [queue-2/](queue-2/README.md) — очередь 2: доставка (install, deploy-check, хук),
  порт to-tickets, размеченный хвост срезов и подготовленный переезд с omp
  (папка, 16 тикетов: голова 01–04, хвост 05–14; 14 разбит на 14/01–02).
- [crossreview-adoption/](crossreview-adoption/README.md) — контрактные дельты из
  методологии кросс-ревью в гейты ревью (папка, 3 тикета: intent осей /code-review,
  unverified-статус confirm-рана, инварианты слепого ревью в KB; из сверки с
  EvilFreelancer/crossreview 2026-10-04).

## Порядок выполнения

1. **queue-2** (остаток): 10 → 12; 11, 14, 15–18 — в любом месте после своих блокеров.
2. **crossreview-adoption** — после закрытия queue-2: тикеты 15–17 правят те же
   воркфлоу ревью (redact, untracked, abort-диагностика), один churn на релизный
   цикл; внутри плана 01 и 02 независимы, 03 — после обоих.
3. **kb-service-doc** — внутренний смоук, в любой момент.
