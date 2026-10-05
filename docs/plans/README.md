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
  EvilFreelancer/crossreview 2026-10-04; тикеты 01–02 отгружены — 2026-10-05
  релиз v0.5.21 и 2026-10-06 релиз v0.5.22).
- [gate-followups/](gate-followups/README.md) — фоллоу-апы ship-гейта из прогона
  queue-2/16 (папка, 2 тикета: паритет код-ревью по untracked-файлам,
  гигиена контекста гейта против qwen-400; отгружена целиком 2026-10-05,
  релизы v0.5.19–v0.5.20).
- [ontology-i7-zcode-paths.md](ontology-i7-zcode-paths.md) — формулировка I7
  называет пути движка zcode, а не omp (file plan; дрейф omp-порта из прогона
  queue-2/18; отгружен 2026-10-05).
- [gate-followups-2/](gate-followups-2/README.md) — хвосты ship-прогонов:
  честность review-ранов и шаблон поставки (папка, 4 тикета: init-блок
  короткими именами, контракт цитаты, лог нормализации severity, кэш
  extractParts; собран из verified-находок прогонов 2026-10-05 и ADR ut-10).

## Порядок выполнения

1. ~~gate-followups~~ — отгружен целиком 2026-10-05 (релизы v0.5.19–v0.5.20);
   правки тех же файлов легли до crossreview-adoption, как и планировалось.
2. **crossreview-adoption** — в работе: 01 отгружен 2026-10-05 (релиз
   v0.5.21), 02 отгружен 2026-10-06 (релиз v0.5.22, три исхода confirm-рана);
   остался 03 — инварианты слепого ревью в KB, фиксирует конечное состояние
   обеих дельт.
3. **gate-followups-2** — четыре хвоста ship-прогонов (init-блок короткими
   именами, контракт цитаты, лог severity-нормализации, кэш extractParts);
   тикеты независимы, идут после crossreview-adoption: файлы не пересекаются
   (тот правит confirm-ран и KB-док, этот — review-воркфлоу, init, тесты),
   порядок держит заявленную очередь релизных циклов.
4. ~~ontology-i7-zcode-paths~~ — отгружен 2026-10-05 (merge `368c9a3`,
   вендорится релизом v0.5.21).
