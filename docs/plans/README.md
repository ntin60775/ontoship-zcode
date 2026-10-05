---
node_type: index
title: Plans
service: _platform
status: active
updated: 2026-10-05
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
  (папка, 18 тикетов 01–19; 14 разбит на 14/01–02; 01–18 отгружены).
- [crossreview-adoption/](crossreview-adoption/README.md) — контрактные дельты из
  методологии кросс-ревью в гейты ревью (папка, 3 тикета: intent осей /code-review,
  unverified-статус confirm-рана, инварианты слепого ревью в KB; из сверки с
  EvilFreelancer/crossreview 2026-10-04).
- [gate-followups/](gate-followups/README.md) — фоллоу-апы ship-гейта из прогона
  queue-2/16 (папка, 2 тикета: паритет код-ревью по untracked-файлам,
  гигиена контекста гейта против qwen-400 на тяжёлых файлах).
- [ontology-i7-zcode-paths.md](ontology-i7-zcode-paths.md) — формулировка I7
  называет пути движка zcode, а не omp (file plan; дрейф omp-порта из прогона
  queue-2/18).

## Порядок выполнения

1. **queue-2** (остаток): 19-миграция последняя.
2. **gate-followups** — после queue-2, до crossreview-adoption: оба тикета
   правят те же воркфлоу ревью, что crossreview (01–02), — один churn на
   релизный цикл; внутри плана тикеты независимы.
3. **crossreview-adoption** — после gate-followups: правки тех же файлов
   ложатся на починенную базу (untracked-карта, гигиена asks); внутри плана
   01 и 02 независимы, 03 — после обоих.
4. **kb-service-doc** — внутренний смоук, в любой момент.
5. **ontology-i7-zcode-paths** — в любой момент: одна формулировка в двух
   синхронных копиях онтологии, файлов с соседними планами не разделяет,
   migration-пилот 19 не блокирует; вендорится — обычный релизный цикл.
