---
node_type: service
title: deploy — канал доставки плагина (marketplace runner)
service: deploy
status: active
updated: 2026-10-01
tags: [service, deploy, marketplace, vendor, release, self-hosting]
links:
  documents: [../../../deploy.json, ../../../.zcode/deployed.json]
  depends_on: [../../ops/install.md]
  relates_to: [../kb-search/README.md, ../../ops/deploy-check.md, ../../reference/roles.md]
---

# deploy — канал доставки плагина (marketplace runner)

OntoShip — **проектный плагин**: глобальной установки нет. Раннер
`sot-zcode-marketplace` вендорит запиненный релиз в `.zcode/`
проекта-потребителя по контракту [deploy.json](../../../deploy.json); данные
проекта (KB, managed-блок, роли, регистрация хука) раннер не трогает — их
создаёт сам плагин после деплоя. Процедуры установки/обновления — в runbook
[install.md](../../ops/install.md); здесь — сам канал: контракт, раннер, журнал.

## Контракт deploy.json (v1)

| поле | значение | смысл |
|---|---|---|
| `strategy` | `replace` | вендор перезаписывается содержимым пина — вендоренная копия всегда равна релизу, не патч и не рабочее дерево |
| `on_drift` | `fail` | локально правленный вендоренный файл блокирует `update`: список, поправить или убрать, повторить |
| `mappings` | 12 | 8 скиллов → `.zcode/skills/<name>` (kb-search, kb-curate, grilling, ship, init, doc, roles, to-tickets); `defaults` → `.zcode/defaults`; `package.json` → `.zcode/package.json`; `scripts` → `.zcode/scripts`; `hooks` → `.zcode/hooks` |
| `post_update` | 1 `run` + 3 `say` | пересборка KB-индекса (когда есть `docs/`); напоминания агенту: init-скилл (managed-блок в `AGENTS.md` + `.gitignore`), проектный оверрайд ролей, регистрация SessionStart-хука |

## Раннер sot-zcode-marketplace

Внешний репозиторий — кода раннера в плагине нет. Команды запускаются из
чекаута маркетплейса (`deploy/deploy-plugin.py`): `install` (вендорить пин),
`update` (перейти на новый пин), `check` (дрейф вендора против пина),
`remove` (снять по журналу), `validate` (каталог + манифесты, для CI).
Пин релиза живёт в `marketplace.json` маркетплейса; откат = откат пина —
сами рефы раннер не откатывает. Раннер пишет **только под `.zcode/`**.

## Журнал deployed.json

`.zcode/deployed.json` — машинный журнал деплоя: `url`, `ref`, `deployed_at`,
`manifest` и фактические маппинги. **Коммитится** вместе с проектом — по нему
раннер (`remove`) и [deploy-check](../../ops/deploy-check.md) восстанавливают,
что и откуда вендорено. Вендоренный код тоже коммитится (self-hosting
переживает clone); локальные бэкапы раннера `.zcode/.backup/` гитом не
хранятся (строка в `.gitignore`; в этом репо каталога нет).

## Самодеплой

Репозиторий плагина сам вендорит свой последний релиз: запись журнала —
`ref: v0.5.5`, деплой 2026-10-01 из `git@github.com:ntin60775/ontoship-zcode.git`.
Dev-цикл — релизного темпа (дев-пина нет): изменения доказываются pytest и
прогонами, встают тегом — и только после этого попадают в вендор; вендоренная
копия всегда равна последнему релизу, не рабочему дереву.

## Границы

- **Дрейф байтов** вендора против пина — не здесь: `deploy-plugin.py check`
  раннера (runbook [install.md](../../ops/install.md)); раскладку и смоуки
  без сети проверяет [deploy-check](../../ops/deploy-check.md).
- **Данные проекта** — KB, managed-блок, `.gitignore`, регистрация хука в
  `.zcode/config.json` — каналом доставки не доставляются: за них отвечает
  init-скилл (напоминания в `post_update`).
- Роли subagent-моделей канал доставки передаёт только как **дефолт**
  (маппинг `defaults` → `.zcode/defaults/roles.md`); проектный оверрайд
  `<repo>/.zcode/ontoship/roles.md` — данные проекта: напоминалка в
  `post_update`, заводится через `/roles set <role> <model>$<level> --project`,
  не руками (слои, fail-closed — в reference
  [ролей](../../reference/roles.md)).
