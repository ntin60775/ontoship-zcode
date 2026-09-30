---
node_type: plan
title: Очередь 2 — доставка, паритет, переезд
service: _platform
status: draft
updated: 2026-09-30
tags: [plan, queue-2, delivery, migration, parity]
links:
  relates_to: [../README.md, ../reference/commands.md, ../../README.md]
  depends_on: [../ontology.md]
---

# Контракт: очередь 2 — доставка, паритет, переезд

## Goal

Превратить ontoship-zcode из «работает у автора в сессии» в плагин, которым можно
пользоваться и переезжать: работающая установка и видимость в воркспейсе, порт
deploy-check, SessionStart-хук свежести, порт to-tickets — и только затем
подготовленный переезд потребителей с omp.

## Done

- Плагин ставится в воркспейс из локальной директории, скиллы доступны по слэшу;
  runbook установки воспроизведён (`docs/ops/install.md`).
- `deploy-check.sh` портирован под zcode-раскладку: зелёный на установке, честный
  FAIL на сломанной.
- SessionStart-хук замечает docs новее индекса и говорит об этом.
- `/to-tickets` работает в zcode и первым же прогоном разбивает хвост этой очереди.
- Хвост очереди (onto-doc, code-review/architecture, handoff/diagnose, hygiene+memory)
  размечен в тикеты нативным to-tickets.
- Migration runbook написан; пилотный переезд одного ontoship-only проекта проведён.

## Scope

- Репозиторий ontoship-zcode: hooks/, scripts/deploy-check.sh, skills/to-tickets/,
  docs/ops/, правка README (guard-обещание).
- Пилотный потребительский проект (ontoship-only) — по runbook, с подтверждением
  оператора перед заменой payload.

Вне scope: порты 1c/unica плагинов omp→zcode; мультиплагинные 1С-проекты (см.
Open question); маркетплейс-каталог; MCP из gitmark; workflow-ификация интерактива.

## Constraints

- Переезд потребителей — только после срезов 03+04 (паритет: хук + to-tickets),
  по явному подтверждению оператора на каждый проект (нативный permission-гейт).
- Runbook покрывает оба канала omp-установки (plugin remove + локальная копия).
- Гигиена не меняет init (one-pass остаётся); sink ночных ERR — `lint --strict`
  exit-код → лог, читаемый SessionStart-хуком.

## Context

Дизайн-гриллинг 2026-09-30 (этим же репо, скилл grilling + challenger на
GLM-5.3-Flash$max; 4 существенных возражения приняты, 1 отклонена частично):

- **Порядок.** Установка/видимость + deploy-check — голова; миграция — после
  паритета, не в голове: у оператора 8 рабочих 1С-проектов с тремя omp-плагинами
  (1c + unica + ontoship), их ship-луп опирается на 1C/unica-контур; замена
  payload до паритета отрезает им правила/команды/guard (проверено challenger по
  реестрам omp).
- **Замена, не coexist.** omp native provider (priority 100) затеняет плагин (90),
  две копии дрейфуют (ontoship-omp/README.md:176–179); управляемый блок общий,
  но шаблоны у omp/zcode init разные — coexist мерцал бы блоком.
- **Guard — слой хоста.** На хостах оператора уже работает глобальный
  `~/.zcode/hooks/safety-guard.py` (PreToolUse Bash, SAFE>50/NORMAL>7,
  ZCODE_SAFETY_CONFIRM); destructive-guard из vakovalskii/destructive-guard —
  Claude Code-плагин с другим протоколом, вендор = вторая копия с несовместимым
  подтверждением. Срез вырезан; README-обещание поправлено; для guardless-хостов —
  отложено (вне очереди).
- **Тикеты: голова руками, хвост — нативным to-tickets.** MVP-папку создавал
  работавший omp-to-tickets («ручная разметка = как в MVP» — было неверно);
  хвост очереди не размечается руками — он первый приёмочный прогон порта
  to-tickets. Отступление для головы: папка создана вручную, потому что порт
  to-tickets сам является тикетом головы (в omp папку создаёт только to-tickets).
- **Гигиена/мемори в очереди, в хвосте, без init-оффера** (init — one-pass);
  зависимость от SessionStart-хука (sink ночных ERR) объявлена.

### Open question (оператору, не блокирует голову очереди)

Режим для 8 мультиплагинных 1С-проектов: приемлем ли split-brain (KB/ship в zcode,
1C-разработка остаётся в omp) на переходный период — или ждать портов 1c/unica
(их нет ни в этой очереди, ни в бэклоге)? Решение определяет судьбу их миграции.

## Head tickets (размечены этим гриллингом; хвост — после порта to-tickets)

| # | Title | Status | Blocked by |
|---|---|---|---|
| [01](01-install-visibility.md) | Установка из локальной директории + видимость в воркспейсе | draft | — |
| [02](02-deploy-check.md) | Порт deploy-check под zcode-раскладку | draft | 01 |
| [03](03-session-start-hook.md) | SessionStart-хук свежести индекса | draft | 01 |
| [04](04-to-tickets-port.md) | Порт to-tickets + критерии неделимости Q1–Q7 | draft | 01 |

## Tail (список срезов — разобьёт нативный to-tickets, тикет 04)

1. onto-doc workflow: fan-out кураторов + lint-гейт + цикл долечивания.
2. code-review (две оси параллельно) + architecture (скан в фоне) workflows.
3. handoff (ReadSessionContext + `.scratch/`) + diagnose (репро-цикл на вопросах).
4. Hygiene + memory: runbook ночного lint+index+map (cron/off-peak, sink ERR —
   `--strict` → лог → SessionStart), шаблон тонкого MEMORY.md-указателя в KB.
5. Migration runbook + пилот: снять ontoship-payload (оба канала omp-установки),
   init обновит общий managed-блок, deploy-check + lint; пилот на одном
   ontoship-only проекте; precondition — срезы 03+04 зашиплены.
