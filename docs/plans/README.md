---
node_type: index
title: Plans
service: _platform
status: active
updated: 2026-10-09
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
| [evidence-discipline/](evidence-discipline/README.md) | draft | 0/3 |
| [external-dependencies/](external-dependencies/README.md) | archived | 4/4 |
| [gate-followups/](gate-followups/README.md) | archived | 2/2 |
| [gate-followups-2/](gate-followups-2/README.md) | archived | 7/7 |
| [gate-risk-scaling.md](gate-risk-scaling.md) | archived | — |
| [handoff-snapshot/](handoff-snapshot/README.md) | archived | 3/3 |
| [kb-service-doc.md](kb-service-doc.md) | archived | — |
| [lens-substrate-flash.md](lens-substrate-flash.md) | archived | — |
| [onto-doc-parity.md](onto-doc-parity.md) | archived | — |
| [ontology-i7-zcode-paths.md](ontology-i7-zcode-paths.md) | archived | — |
| [queue-2/](queue-2/README.md) | archived | 17/17 |
| [roles-fallback-substrate/](roles-fallback-substrate/README.md) | draft | 0/4 |
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
4. **evidence-discipline** — дисциплина доказательств: телеметрия прогона
   (лог прочитан, иначе активность, не факт), обязательность негативной/
   мутационной пробы для новой тест-матрицы, справка «Иерархия доказательств»
   (03 blocked by 01+02; 01–02 правят один шаг ship-скилла — едут подряд;
   03 доковый — лёгкий контур v0.5.40). План собран 2026-10-09 из разбора
   заметки о TDD и агентах (DeepSWE, arXiv 2603.07084) по явному запросу
   оператора, без грилла — прецедент external-dependencies.
5. **roles-fallback-substrate** — честные роли с фолбэком и демонтаж прямого
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

Расширение инвариантов/реестров сверх моратория — только от записанного
инцидента гнили.
