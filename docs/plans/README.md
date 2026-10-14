---
node_type: index
title: Plans
service: _platform
status: active
updated: 2026-10-12
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
| [behavior-reel/](behavior-reel/README.md) | draft | 0/4 |
| [crossreview-adoption/](crossreview-adoption/README.md) | archived | 3/3 |
| [evidence-discipline/](evidence-discipline/README.md) | archived | 3/3 |
| [external-dependencies/](external-dependencies/README.md) | archived | 4/4 |
| [flow-continuity.md](flow-continuity.md) | draft | — |
| [gate-followups/](gate-followups/README.md) | archived | 2/2 |
| [gate-followups-2/](gate-followups-2/README.md) | archived | 7/7 |
| [gate-risk-scaling.md](gate-risk-scaling.md) | archived | — |
| [handoff-snapshot/](handoff-snapshot/README.md) | archived | 3/3 |
| [kb-service-doc.md](kb-service-doc.md) | archived | — |
| [lens-substrate-flash.md](lens-substrate-flash.md) | archived | — |
| [onto-doc-canon/](onto-doc-canon/README.md) | archived | 2/2 |
| [onto-doc-command.md](onto-doc-command.md) | archived | — |
| [onto-doc-hygiene.md](onto-doc-hygiene.md) | archived | — |
| [onto-doc-parity.md](onto-doc-parity.md) | archived | — |
| [ontology-i7-zcode-paths.md](ontology-i7-zcode-paths.md) | archived | — |
| [queue-2/](queue-2/README.md) | archived | 17/17 |
| [roles-fallback-substrate/](roles-fallback-substrate/README.md) | archived | 4/4 |
| [roles-per-agent/](roles-per-agent/README.md) | archived | 2/2 |
| [run-args-discipline.md](run-args-discipline.md) | archived | — |
<!-- END inventory:plans -->

## Порядок выполнения

Статусы планов и тикетов живёт только в таблице-реестре выше; проза здесь —
исключительно решения оператора о порядке. Решение оператора 2026-10-09:
сначала доделать планы разработки (все три прогрилены 2026-10-09 —
субагент-грилл + challenger dwfrun-c3a6d4a4, substantial-возражения
пере-решены), затем — реальная эксплуатация (ADR
[invariant-moratorium](../decisions/invariant-moratorium.md)).

1. ✅ **lens-substrate-flash** — отгружен v0.5.39: субстрат линз на дефолтных
   субагентах Flash (убирает класс finish=length и обслуживание LENS_PROFILES;
   приёмка A/B с посевом: новый субстрат 4/4 + полный coverage, старый 3/4).
2. ✅ **gate-risk-scaling** — отгружен v0.5.40: лёгкий контур гейта для
   доковых диффов (классификация по карте диффа + условный confirm и доковая
   ветка шагов 6/7/9 скилла ship; приёмка — две живые пробы лёгкого контура).
3. ✅ **run-args-discipline** — отгружен v0.5.41: префлайт args перед сабмитом
   рана — уроки 10–11 contour (декларация — нижняя граница; node -e съедает
   `--`); триггер в description; verified-находка гейта закрыта фикс-ом
   (гарда конфирма не отклоняет декодируемую строку).
4. ✅ **evidence-discipline** — отгружен целиком: телеметрия прогона v0.5.43,
   обязательность пробы v0.5.44, справка
   [evidence-hierarchy.md](../reference/evidence-hierarchy.md) (03 доковый —
   лёгкий контур, без релиза). План собран 2026-10-09 из разбора
   заметки о TDD и агентах (DeepSWE, arXiv 2603.07084) по явному запросу
   оператора, без грилла — прецедент external-dependencies.
5. ✅ **roles-fallback-substrate** — отгружен целиком 2026-10-11 (релиз v0.5.46, 4/4): честные роли с фолбэком и демонтаж прямого
   API-субстрата: роль-константа `fallback`, шаг 6 ведёт линзы на модель роли
   reviewer, снос direct-ветки с тарифной картой, чистка модельных якорей
   комментариев (решения оператора 2026-10-09; тикеты линейны 01→02→03→04).
   Едет после evidence-discipline: тикет 02 правит тот же шаг 6 ship-скилла
   (один файл — один чурн), 03 — тот же пин-тест субстрата; пререквизит 02 —
   оператор перепризначает reviewer/challenger на GLM-5.3-Flash$high.
6. **Реальная эксплуатация** — миграция шести оставшихся проектов с omp по
   runbook queue-2/19 (ждёт перечень или «все шесть» от оператора) и
   повседневное использование KB/гейтов в рабочих проектах; первая реальная
   док-only правка любого проекта — через лёгкий контур (v0.5.40).
7. ✅ **onto-doc-command** — отгружен v0.5.47 (2026-10-12): восстановление команды-входа онто-дока: тонкий
   скилл-обёртка над воркфлоу (бутстрап по умолчанию, паттерн grilling),
   замена `/onto-doc` в runbook миграции (решение оператора 2026-10-12 —
   «onto-doc всегда был отдельной командой как и doc», сверка с оригиналом
   Ковальского). Слот «в любой момент»: один файл-план — один слайс,
   с разработочными планами по файлам не пересекается.
8. ✅ **onto-doc-hygiene** — отгружен v0.5.48 (гейт 23/23 verified): 10 verified
   дефектов тела онто-дока с гейта шипа onto-doc-command (маскировка секретов в
   abort-ветках, инъекционные обрамления, exitCode хвоста, нормализация выходов):
   в том шипе отклонены по констрейнту «тело не меняется» (R100-критерий переезда),
   здесь констрейнт снят явным перечнем.

9. ✅ **onto-doc-canon** — отгружен v0.5.49–v0.5.50 целиком (2/2): возврат семантики
   апстрима команде /onto-doc: пустой вызов = весь репозиторий молча, аргумент =
   опциональная scope-подсказка; модель прогона = модель чата (решение оператора
   2026-10-12, роль curator отвергнута после подготовки). Прогрилен 2026-10-12
   (challenger dwfrun-8e44670e: 5 substantial пере-решены находкой
   required-хедера, 2 minor — поправки формулировок). Тикеты линейны 01→02;
   шипался после onto-doc-hygiene: общий файл onto-doc.workflow.ts, якоря canon
   легли выше hygiene-правок.
10. **behavior-reel → flow-continuity** — behavior-reel (контракт 2026-10-13;
   4 линейных тикета: носитель цитат → формат ленты → контрслой+пробы → ship)
   шипуется первым, разбивка — ручным `/to-tickets` (автоцепочки ещё нет);
   flow-continuity (контракт 2026-10-14; файл-план одним слайсом: автоцепочка
   грилл→тике́ты той же сессией + перегрилль тикета по дрейфу в /ship шаг 1)
   встаёт после behavior-reel 04 включительно — задержка тикетов 03–04
   решением оператора порядок не меняет. Основание — общие файлы: якоря
   behavior-reel написаны против текущих текстов, флоу-правка ложится чистым
   диффом поверх; обратный порядок сдвигал бы зафиксированный контракт
   behavior-reel.

Расширение инвариантов/реестров сверх моратория — только от записанного
инцидента гнили.
