---
node_type: index
title: Plans
service: _platform
status: active
updated: 2026-10-15
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
| [behavior-reel/](behavior-reel/README.md) | archived | 4/4 |
| [checks-profile.md](checks-profile.md) | draft | — |
| [crossreview-adoption/](crossreview-adoption/README.md) | archived | 3/3 |
| [evidence-discipline/](evidence-discipline/README.md) | archived | 3/3 |
| [external-dependencies/](external-dependencies/README.md) | archived | 4/4 |
| [flow-continuity.md](flow-continuity.md) | archived | — |
| [flow-semantics/](flow-semantics/README.md) | draft | 2/3 |
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
| [queue-3/](queue-3/README.md) | archived | 3/3 |
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
10. ✅ **behavior-reel → flow-continuity** — оба отгружены: behavior-reel
   v0.5.53–v0.5.56 (4/4, разбивка тогда — ручным `/to-tickets`, автоцепочки
   ещё не было); flow-continuity v0.5.57 (файл-план одним слайсом: автоцепочка
   грилл→тике́ты той же сессией с определённым предикатом многослайсности,
   шаг 0 tracked/untracked, one-piece коммит разбивки, drift mini-grill в
   /ship шаг 1 с соседним каскадом; гейт 3 раунда 15 verified/0/0, финал
   чист; план отгружен одним срезом — ручная разбивка не понадобилась).
   Порядок «behavior-reel первым» держался: якоря ленты легли на тексты до
   флоу-правки; хвост гейта (kb-curate:96 «I1–I9» при движке I1–I10) —
   тикетом queue-3/03.

11. ✅ **queue-3 — упразднена** (2026-10-16, flow-semantics/03): парковка
   хвостов и продуктов шипов заменена ишью-контуром — находка вне границ
   плана живёт ишью-файлом `.zcode/ontoship/issues/` и возвращается
   планированию триажом на входе грилла (решение оператора 2026-10-16,
   план flow-semantics). Тикеты 04–06 мигрированы в ишью-файлы 02–04
   (содержание, критерии и статус сохранены), тикеты 01–03 — архив плана;
   queue-3 archived — административная архивация, причина в Context плана.

12. **checks-profile — профиль проверок проекта** (решение оператора
   2026-10-15, разговор о подъёме онтошипа в «ЕРП мини»): бутстрапп спрашивает и
   записывает, что в проекте значат «проверки»; файл-план варианта 3
   (профиль-файл + вопрос init) собран без грилла по прецеденту
   external-dependencies. Порядок относительно queue-3 не назначен.

13. **flow-semantics — семантика планирования** (решение оператора
   2026-10-16): план ⇒ грилл (гарантию несёт артефакт, провенанс в Context),
   ишью-контур (тикеты только из плана, находки вне границ — файлы в
   `.zcode/ontoship/issues/`, триаж на входе грилла), план = один юнит
   (якорь — план-критерии приёмки), план-приёмка — пост-фактум аккорд;
   queue-3 упразднена 2026-10-16 (04–06 → ишью 02–04). Прогрилен 2026-10-16 (challenger
   dwfrun-6d3a363a: 8 решений, 7 substantial пере-решены, эскалации —
   носитель ишью и роль приёмки — закрыты оператором; контрслой
   dwfrun-eb97eb2e: 12 враждебных случаев приняты в ленты тикетов);
   тикеты линейны 01→02→03 — один класс файлов на тикет (01: grilling/
   to-tickets/kb-curate; 02: ship; 03: KB и миграция), тикет 03
   финализирует пункт 11 этой секции; checks-profile прогрилливается перед
   своим шипом как первый ретро-клиент.

Расширение инвариантов/реестров сверх моратория — только от записанного
инцидента гнили.
