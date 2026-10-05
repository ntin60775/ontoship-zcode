---
node_type: runbook
title: Миграция проекта с omp на zcode (payload ontoship)
service: _platform
status: active
updated: 2026-10-05
tags: [runbook, migration, omp, zcode, ontoship]
links:
  relates_to: [install.md, deploy-check.md, session-start-hook.md, ../../skills/init/SKILL.md]
---

# Миграция проекта с omp на zcode

Принцип (решение оператора, 2026-09-30): **полный переезд, без split-brain** —
проект целиком на zcode; omp остаётся терминалом-фоллбэком для общих задач;
1c/unica omp-плагины остаются omp'у до собственных портов (вне этого runbook).
Аудит старых правил — обязательная фаза: каждый rule/skill/command omp-payload
получает вердикт keep/drop/replace, значительная часть ожидаемо выпадает.
Замена payload — по явному подтверждению оператора на каждый проект.

## Два канала omp-установки — что именно снимаем

| Канал | Признаки в проекте | Где живёт payload |
|---|---|---|
| плагин (каталог `sot-omp-marketplace`) | запись в `.omp/plugins/installed_plugins.json`, симлинк `.omp/plugins/node_modules/ontoship`, команды с префиксом `/ontoship:*` | машинный кэш `~/.omp/plugins/cache/plugins/`; чистка кэша оставляет висячий симлинк и «мёртвую» регистрацию — снятие обязано работать и с этим состоянием (2026-10-05: все рабочие проекты машины в нём и находятся) |
| локальная копия (dev, air-gapped) | плоские `.omp/skills/…`, `.omp/rules/…`, `.omp/commands/…`, `.omp/scripts/` в самом проекте, команды без префикса | в репо проекта; установка zcode-плагина поверх копии запрещена — копия снимается первой (одна поставка: native-провайдер затеняет плагин, две копии дрейфуют) |

Payload omp-ontoship, подлежащий аудиту: 4 always-on правила (`kb-first`,
`kb-source-of-truth`, `ship-gate`, `acceptance-rounds`), скиллы (kb-search,
kb-curate, grilling, dev-flow, domain-modeling, mp-*), команды (`kb`, `doc`,
`onto-doc`, `kb-map`, `to-tickets`, `ship`, `handoff`, `prototype`, `init`).
Если кэш вычищен и сверить не с чем — исходник payload: репо `ontoship-omp`
(состав тот же).

`AGENTS.md` и `docs/` — данные проекта: omp-плагин их не трогает при апгрейде,
zcode тоже. KB (markdown в `docs/` + индекс `.gitmark/`) не «переносится» —
она продолжает жить под тем же движком, теперь из `.zcode/skills/kb-search/`.

## Фазы

### 0. Предусловия

- Проект — git-репо; несвязанные грязные файлы не мешают, коммиты миграции —
  отдельные и свои.
- zcode-плагин в pin-релизе потребителя (установка — [install.md](install.md)).
- Оператор назвал проект и подтвердил переезд.

### 1. Аудит omp-payload — вердикты keep/drop/replace

Инвентаризация по признакам каналов из таблицы выше плюс omp-следы в данных
проекта: секция KB в `AGENTS.md` (у omp-инициализации — без маркеров, с путями
`.omp/plugins/...`), omp-блок в `.gitignore`, секции `⟦⟦…⟧⟧` в `.omp/RULES.md`.

Результат — один документ `docs/decisions/<slug>-omp-migration.md` в
потребителе: таблица «артефакт → вердикт → замена»; отдельный ADR — только для
спорных правил. Типовые вердикты (пилот ut-10, 2026-10-05):

| Артефакт | Вердикт | Замена |
|---|---|---|
| плагин `ontoship@sot-omp-marketplace` (регистрация + симлинк) | replace | zcode-плагин `ontoship` из `sot-zcode-marketplace` |
| omp-секция KB в `AGENTS.md` (пути `.omp/plugins/...`) | replace | управляемый блок `<!-- BEGIN ontoship -->` (init, фаза 3) |
| правила payload: `kb-first`, `kb-source-of-truth`, `ship-gate`, `acceptance-rounds` | replace | контракты скиллов zcode (`kb-search`, `ship`) и строки managed-блока; проза-дубликаты не создаются |
| omp-команды (`/kb`, `/doc`, `/ship`, …) | replace | zcode-слэши (`/kb-search`, `/doc`, `/ship`, …) — перечислены в блоке |
| omp-блок в `.gitignore` (`.omp/plugins/`, …) | keep | omp остаётся фоллбэком-терминалом; существующие строки не удалять — init только дописывает, но чистка файла руками cmp-строки не защитит |
| секции `.omp/RULES.md` (1c/unica) | keep | вне переезда |
| локальные omp-скиллы проекта (не из payload) | keep | проектное, omp-фоллбэку |
| KB: `docs/` + `.gitmark/` + `*-map.html` | keep | данные; индекс пересобирается zcode-движком |

### 2. Снятие ontoship-payload

- Канал-плагин, из корня проекта: перед снятием — резерв для отката:
  скопировать `.omp/plugins/installed_plugins.json` в `.scratch/` и записать
  pin-версию плагина из его записи. Затем
  `omp plugin uninstall ontoship@sot-omp-marketplace --scope project`
  (работает и по висячему симлинку). Проверка снятия: записи нет в
  `.omp/plugins/installed_plugins.json`, симлинка нет в
  `.omp/plugins/node_modules/`.
- Канал-копия: tar-снимок `.omp/` в `.scratch/`, затем удалить ровно
  payload-пути из аудита (правила/скиллы/команды/скрипты ontoship); проектные
  omp-артефакты не трогать. Состав версионируемого задаёт `.gitignore`
  потребителя (пример ut-10: версионируются `.omp/rules/` проектных имён и
  `.omp/extensions/`; машинный слой `.omp/plugins|skills|commands|scripts/` и
  `.omp/RULES.md` — в игноре).
- При обоих каналах: перед снятием убедиться, что в KB нет незакоммиченных
  правок, которые вы хотели бы сохранить.

**Откат, если фаза 3 не удалась.** omp-payload восстанавливается целиком:
канал-плагин — `omp plugin install ontoship@sot-omp-marketplace --scope project`
(той же pin-версии, что в резервной копии `installed_plugins.json`);
канал-копия — `tar -xzf .scratch/<снимок>.tar.gz` в корне проекта. Частично
написанный `.zcode/` при откате удалить целиком — установка повторяется с нуля.

### 3. Установка zcode

- Из клона `sot-zcode-marketplace`:
  `python3 deploy/deploy-plugin.py install ontoship <проект>` — раннер пишет
  только `.zcode/` (журнал `.zcode/deployed.json` коммитится).
- Точка входа — по [SKILL.md init-скилла](../../skills/init/SKILL.md):
  управляемый блок `<!-- BEGIN ontoship -->` в `AGENTS.md` + строки `.gitignore`
  (`.gitmark/`, `*-map.html`, `.scratch/`); идемпотентно, вне маркеров не пишет.
  Старую omp-секцию KB в `AGENTS.md` удаляет мигрирующий агент — init чужое не
  трогает, а дублировать точку входа нельзя.
- Опционально — хук свежести индекса: [session-start-hook.md](session-start-hook.md)
  (регистрация в `.zcode/config.json` — данные проекта, не раннер).

### 4. Верификация

- `bash .zcode/scripts/deploy-check.sh` из корня проекта — зелёный;
- `python3 .zcode/skills/kb-search/gitmark.py index`, затем
  `python3 .zcode/skills/kb-search/gitmark.py lint --strict` — зелёные;
  `python3 .zcode/skills/kb-search/gitmark.py search "<запрос>"` находит
  документы KB проекта;
- слэш-видимость: zcode-сессия в проекте видит `/kb-search`, `/ship`, … —
  вендор проверяет deploy-check, слэш — хост-факт, фиксируется в отчёте
  миграции;
- omp-фоллбэк: omp-терминал в проекте работает; unica/1c-плагины на месте или
  восстанавливаются самим omp (их состояние — вне переезда, факт фиксируется).

### 5. Записи

- В потребителе коммитятся: аудит-док, `AGENTS.md`, `.gitignore`, `.zcode/`.
- В KB источника (репо плагина) — ship-заметка пилота: что проверено, что нет,
  какие отклонения от runbook потребовались.
