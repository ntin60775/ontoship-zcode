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
  честность review-ранов и шаблон поставки (папка, 7 тикетов: init-блок
  короткими именами, контракт цитаты, лог нормализации severity, кэш
  extractParts, init создаёт реестр, шаг 7 синхронен git-флоу, узкие линзы
  гейт-ревьюера; собран из verified-находок прогонов 2026-10-05–06 и решений
  оператора).
- [handoff-snapshot/](handoff-snapshot/README.md) — единый катящийся слепок
  состояния: один хэндофф-файл с полным регенератом при закрытии тикета и при
  /handoff, анонс хука без TTL, зачистка legacy (папка, 3 тикета; решение
  оператора 2026-10-06 после коллизии неуникальных sess-id).
- [external-dependencies/](external-dependencies/README.md) — внешние
  зависимости: контур моделей/кредов замкнут на zcode, гейт fail-closed по
  субстрату, инвентаризация всех внешних зависимостей с контурами замены
  провайдера и обновления апстрима ontoship-omp, поставляемые уроки контура,
  автоподстройка субстрата под модель роли (папка, 4 тикета; решения
  оператора 2026-10-06–07 после тарифной стены гейта).

## Порядок выполнения

1. ~~gate-followups~~ — отгружен целиком 2026-10-05 (релизы v0.5.19–v0.5.20);
   правки тех же файлов легли до crossreview-adoption, как и планировалось.
2. ~~handoff-snapshot~~ — отгружен целиком 2026-10-06 (v0.5.23–v0.5.25).
3. ~~gate-followups-2~~ — отгружен целиком 2026-10-06–07 (релизы
   v0.5.26–v0.5.30): 01–04 штатно; 05+07 — на новом субстрате гейта
   (узкие линзы на прямом API neuraldeep, контур кредов на zcode — решение
   оператора после тарифной стены; цикл гейта 7 итераций, 35 сырых →
   20 verified закрыты / 14 опровергнуты / 0 unverified, ни одного
   provider-stop; details в shipping-notes тикетов).
4. **external-dependencies** — внешние зависимости на посадке субстрата
   «прямой API» (решения оператора 2026-10-07): 01 контур кредов на zcode
   fail-closed + args.provider (замена провайдера — конфигурационная), 02
   инвентаризация зависимостей + контуры замены провайдера и обновления
   апстрима ontoship-omp, 03 поставляемые уроки контура (skills/contour),
   04 автоподстройка субстрата под модель роли (обсуждение; blocked by 01).
   Следующий план к отгрузке.
5. **crossreview-adoption** — остался 03 (инварианты слепого ревью в KB),
   ПОСЛЕДНИМ: док фиксирует конечное состояние гейтов, включая контракт
   цитаты из gate-followups-2/02 и субстрат прямого API, — писать его до
   кодовых планов значило бы устареть к публикации. 01–02 отгружены
   (v0.5.21, v0.5.22).
6. ~~ontology-i7-zcode-paths~~ — отгружен 2026-10-05 (merge `368c9a3`,
   вендорится релизом v0.5.21).
7. **06 «Шаг 7 /ship ↔ git-flow»** (из gate-followups-2, остался draft) —
   доковый тикет, вендорится; отдельный запуск /ship в любой момент,
   очередь выше не блокирует.
