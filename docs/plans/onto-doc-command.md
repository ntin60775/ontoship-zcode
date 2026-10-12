---
node_type: plan
title: onto-doc — восстановление команды-входа
service: _platform
status: draft
updated: 2026-10-12
links:
  documents: [../../skills/onto-doc/onto-doc.workflow.ts]
  relates_to: [onto-doc-parity.md, ../ops/migration-omp-to-zcode.md, ../reference/workflow-args.md]
---

# onto-doc — восстановление команды-входа

## Goal

Онто-док снова полнокровный член лестницы метода `/kb-search → /doc → /onto-doc → /ship`:
отдельный вызываемый вход `/onto-doc` с бутстрапом по умолчанию — как в оригинале
Ковальского (`.omp/commands/onto-doc.md`, рядом с `doc`), а не воркфлоу без
поверхности входа внутри чужого скилла.

## Done

- Скилл `skills/onto-doc/SKILL.md` существует: `name: onto-doc`, триггеры
  «онто-док», «погони онто-док», «бутстрап KB», «пересбор KB», `/onto-doc`;
  тело инструктирует запуск CreateWorkflow на `onto-doc.workflow.ts`, лежащий
  **рядом со SKILL.md** (паттерн grilling), с args `{task, root}` — без `plan`
  это бутстрап (surveyor сам обследует и декомпозирует), с готовым планом —
  прежний контракт кусков.
- Воркфлоу переехал к своему скиллу: `skills/doc/onto-doc.workflow.ts` →
  `skills/onto-doc/onto-doc.workflow.ts` через `git mv`, дифф тела пуст —
  переезд семантический, доказывается `git diff -M` (R100), не рассуждением.
- Живой прогон воркфлоу **с нового пути** завершается: бутстрап на tmp-фикстуре
  (как в Done плана onto-doc-parity: `git init` + копия
  `skills/{kb-search,kb-curate,doc}` + `docs/ontology.md`) поднимает KB с
  зелёным `gitmark lint`, отчёт прежней формы
  `{conclusion, green, rounds, pieces, verified, notCovered}`.
- Слэш-видимость: zcode-сессия в этом репо видит `/onto-doc` — host-факт,
  фиксируется в ship-заметке (прецедент — фаза 4 миграции).
- Ссылки за переездом: typed links на новый путь в
  `docs/reference/workflow-args.md` (implemented_by),
  `docs/plans/onto-doc-parity.md` (documents, архивный), в этом файл-плане;
  `lint --strict` зелёный — битых typed links нет. Prose-упоминания в
  архивных тикетах queue-2 не правятся (история).
- `deploy.json` несёт маппинг `skills/onto-doc → .zcode/skills/onto-doc`;
  `bash scripts/deploy-check.sh` зелёный.
- Runbook миграции: в таблице аудита замена `/onto-doc` названа явно среди
  zcode-слэшей — мигрирующий проект больше не теряет команду.
- `skills/doc/SKILL.md` содержит строку-указатель: тяжёлые прогоны
  (бутстрап/веер правок) — `/onto-doc`, лёгкий путь одного дока — здесь.
- На репо `lint --strict` и `pytest` зелёные; I8-twin онтологии не тронут;
  вендор `.zcode/` доезжает self-update на шаге деплоя (руками не правится).

## Scope

- `skills/onto-doc/SKILL.md` — новый скилл-обёртка.
- `skills/doc/onto-doc.workflow.ts` → `skills/onto-doc/onto-doc.workflow.ts` —
  `git mv`, тело не менять.
- `deploy.json` — маппинг нового скилла.
- `skills/doc/SKILL.md` — строка-указатель на `/onto-doc`.
- `docs/reference/workflow-args.md`, `docs/plans/onto-doc-parity.md`,
  этот файл-план — пути typed links за переездом.
- `docs/ops/migration-omp-to-zcode.md` — `/onto-doc` в таблице замены команд.
- Инвентарь скиллов потребителя (`docs/reference/commands.md`) — derived,
  перегенерируется `gitmark inventory`, в скоуп не входит.

## Constraints

- `stop-before-commit` (дефолт).
- Тело воркфлоу семантически не меняется — чинится поверхность входа, не
  механика прогона; приёмка механики — живым прогоном по Done.
- Один шип: файл-план исполняется одним тикетом-слайсом.
- Мораторий инвариантов: новых инвариантов и реестров не заводить.

## Context

- Разговор 2026-10-12: оператор — «onto-doc всегда был отдельной командой как
  и doc»; сверка с оригиналом подтвердила (форк omp-раскладки:
  `.omp/commands/onto-doc.md` рядом с `doc`; актуальный апстрим — `commands/`
  в корне claude-plugin). Сверять — с оригиналом Ковальского, не с omp-payload.
- История регресса: queue-2/05 сузил онто-док до исполнения готового плана,
  отступление нигде не записано; план onto-doc-parity (2026-10-08, v0.5.38)
  вернул функцию — бутстрап surveyor'ом, map, coverage, I10 — но поверхность
  входа не восстанавливал: воркфлоу остался внутри `skills/doc/`, SKILL.md
  скилла `doc` его по имени не называет, запуск — только прозаическая просьба
  агенту собрать CreateWorkflow вручную.
- Runbook миграции обещает «omp-команды → replace zcode-слэшами», замены для
  `/onto-doc` в списке нет — мигрирующий проект молча теряет команду.
- Паттерн внутри плагина уже есть: grilling — скилл-вход, явно называющий
  `challenger.workflow.ts` «next to this SKILL.md» (`skills/grilling/SKILL.md:41`).
- Понимание цели оператора (проверено 2026-10-08): онто-док — покрытие кода
  документацией; лестница `/kb-search → /doc → /onto-doc → /ship`.
