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
  (file plan, архив; внутренний смоук девфлоу).
- [queue-2/](queue-2/README.md) — очередь 2: доставка (install, deploy-check, хук),
  порт to-tickets, размеченный хвост срезов и подготовленный переезд с omp
  (папка, 18 тикетов 01–19; отгружена целиком 2026-10-05, пилот миграции — ut-10).
- [crossreview-adoption/](crossreview-adoption/README.md) — контрактные дельты из
  методологии кросс-ревью в гейты ревью (папка, 3 тикета: intent осей /code-review,
  unverified-статус confirm-рана, инварианты слепого ревью в KB; из сверки с
  EvilFreelancer/crossreview 2026-10-04).
- [gate-followups/](gate-followups/README.md) — фоллоу-апы ship-гейта из прогона
  queue-2/16 (папка, 2 тикета: паритет код-ревью по untracked-файлам,
  гигиена контекста гейта против qwen-400; отгружена целиком 2026-10-05,
  релизы v0.5.19–v0.5.20).
- [ontology-i7-zcode-paths.md](ontology-i7-zcode-paths.md) — формулировка I7
  называет пути движка zcode, а не omp (file plan; дрейф omp-порта из прогона
  queue-2/18).

## Порядок выполнения

1. ~~gate-followups~~ — отгружен целиком 2026-10-05 (релизы v0.5.19–v0.5.20);
   правки тех же файлов легли до crossreview-adoption, как и планировалось.
2. **crossreview-adoption** — следующий по порядку: правки тех же файлов
   ложатся на починенную базу (untracked-карта, гигиена asks); внутри плана
   01 и 02 независимы, 03 — после обоих.
3. **ontology-i7-zcode-paths** — в любой момент: одна формулировка в двух
   синхронных копиях онтологии, файлов с соседними планами не разделяет;
   вендорится — обычный релизный цикл.
