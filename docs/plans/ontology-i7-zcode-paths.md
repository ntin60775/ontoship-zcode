---
node_type: plan
title: I7 онтологии называет пути движка zcode, а не omp
service: _platform
status: archived
updated: 2026-10-05
tags: [plan, ontology, docs, omp-port]
links:
  relates_to: [../ontology.md, README.md]
---

# Контракт: I7 онтологии называет пути движка zcode

## Goal

Инвариант I7 — контракт для онтология-линтера, и его текст до сих пор описывает
omp-эру: «the project's `.omp/commands/*.md`». В zcode-раскладке такого каталога
нет — движок сканирует проектный `.zcode/commands` и пакетный `commands/`.
Потребитель, сверяющийся с онтологией, ищет не тот путь. Дрейф остался от
omp→zcode порта; замечен попутно в прогоне queue-2/18 (2026-10-05).

## Done

- Формулировка I7 в `docs/ontology.md` называет реальные пути: проектный
  `.zcode/commands/*.md` и пакетный `commands/*.md`.
- Та же правка в пакетной копии `skills/kb-curate/ontology.md` — тела моделей
  от первого `## ` совпадают (I8 чист); вендорная копия доедет очередным
  self-update без отдельных действий (зафиксировать в ship-заметке).
- `grep -rn "\.omp/" docs/` пуст; `gitmark lint --strict` и `inventory --check`
  зелёные.

## Scope

- По одной строке формулировки I7 в двух синхронных копиях онтологии.
  Вне scope: изменения движка, инвентарных таблиц (SKILL.md навыков не
  трогается), прочих инвариантов.

## Constraints

- План независим («в любой момент»): файлов с соседними планами не разделяет,
  migration-пилот queue-2/19 не блокирует. Вендорится (`skills/` → `.zcode/`)
  — доезжает обычным релизным циклом.

## Context

Решение оператора (2026-10-05, квиз /to-tickets): форма — файл-план (одно
неделимое обещание, папка с одним тикетом — церемония), слот — «в любой
момент», как kb-service-doc.

**Отгружено (2026-10-05).** Единственный срез (файл-план) через полный луп:
worktree `ship/ontology-i7-zcode-paths`, фича `0c57040` — по одной строке I7
в `docs/ontology.md:177` и `skills/kb-curate/ontology.md:163`
(`.omp/commands` → `.zcode/commands`); I8 держится. Гейт: ревью
(qwen3.6-35b-a3b$high) — 0 находок, оба файла покрыты; confirmer
(GLM-5.3-Flash$high) — подтверждать нечего, пустой случай отчитан честно.
Люк: pytest 99 passed, `lint --strict` и `inventory --check` rc=0,
`deploy-check` exit=0 (self-hosted контур, ontoship@v0.5.20).
Отклонения: (1) критерий «`grep -rn "\.omp/" docs/` пуст» сужен до двух копий
онтологии — полный grep по `docs/` остаётся непустым: легитимные `.omp/` в
рунбуке миграции `docs/ops/migration-omp-to-zcode.md` (появил после публикации
плана) и в цитате omp-эры в самом этом плане; (2) релиз/self-update не
делается — доковый тикет (прецедент 11/19), вендорная копия
`.zcode/skills/kb-curate/ontology.md` доедет очередным self-update без
отдельных действий.
