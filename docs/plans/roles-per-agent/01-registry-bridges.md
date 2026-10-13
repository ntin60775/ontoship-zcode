---
node_type: ticket
title: Роли — реестр LLM + два моста роль→модель
service: _platform
status: archived
updated: 2026-10-13
links:
  part_of: [README.md]
  implemented_by: [../../../defaults/roles.md, ../../../skills/roles/SKILL.md, ../../../skills/roles/roles.py, ../../reference/roles.md, ../../reference/dependencies.md, ../../../tests/test_roles.py]
---

# 01: Роли — реестр LLM + два моста роль→модель

**What to build:** роли — единственный реестр LLM субагентов: записи
`curator` (GLM-5.3-Flash$high) и `surveyor` (GLM-5.3-Flash$max) с
описаниями потребителей, правило записи вместо мёртвого prose-дефолта,
машинный пин явных level, absence-стоп в fail-closed правиле и секция
«два моста» в скилле roles: №1 — одноролевой `subagent_model`, №2 —
конвенция `{{ROLE_MODEL:<role>}}` с режим-зависимым префлайтом,
инстанциацией строковыми литералами, дифф-префлайтом и запретом
переиспользования инстансов.

**Blocked by:** None (can start immediately).

- [x] В `defaults/roles.md` есть записи `curator` (GLM-5.3-Flash$high —
  кураторы fan-out и healer онто-дока) и `surveyor` (GLM-5.3-Flash$max —
  surveyor онто-дока; имя без коллизии с гейт-агентом `synthesizer`),
  обе с явным `level` и описанием потребителей; prose несёт правило записи
  «новая роль без специфики — запись GLM-5.3-Flash$max с явным level» и
  поимённые исключения: confirmer $high (тикет 14), curator $high
  (2026-10-13), гейт-сводчик на confirmer (к ролям не относится). Плюс
  гейт-фикс: заметка «целевые назначения, проводка уезжает тикетом 02» —
  до него ран онто-дока на модели чата.
- [x] Мутационная проба в `tests/test_roles.py`: удаление строки `level` у
  любой записи defaults (например confirmer) краснит сьют; пин полноты —
  каждая запись несёт явный `level`. Пробы живьём: точечная (confirmer) →
  1 failed; sed-форма → 2 failed (гейт-ран конфирмера воспроизвёл).
  Гейт-дополнение: пин строгого формата frontmatter ловит молча
  выброшенные парсером записи (таб-каскад — живая проба).
- [x] Fail-closed правило в `skills/roles/SKILL.md` и
  `docs/reference/roles.md` содержит явный пункт: роль отсутствует в
  `resolve --json` — тот же стоп с диагностикой роли и слоя, что и
  mismatch (grep «роли нет/отсутствует» до правки — 0 совпадений,
  проверено).
- [x] `skills/roles/SKILL.md` несёт секцию «два моста»: №1 — одноролевой
  ран (`subagent_model` после resolve+ListModels, паттерн гейтов), №2 —
  конвенция `{{ROLE_MODEL:<role>}}`: режим-зависимый резолв → инстанциация
  строковыми литералами в уникально именованный черновик
  `.zcode/workflow-drafts/` → дифф-префлайт (diff(инстанс, шаблон) ≡ ровно
  замены плейсхолдеров на model$level из resolve, ≥1 плейсхолдер, все
  заменены) → CreateWorkflow(path=инстанс); переиспользование старых
  инстансов запрещено. Захардкоженные перечни ролей (description, интро)
  синхронизированы с defaults (6 ролей; commands.md поднялся self-update).
- [x] `docs/reference/roles.md`: таблица дополнена curator/surveyor,
  заголовок без «четыре роли», секция мостов с дословной цитатой
  компиляторской диагностики (persona.model — только литералы).
  Гейт-фиксы: строка fallback с пометкой константы возвращена, приоритет
  `$ONTOSHIP_HOME` сформулирован честно.
- [x] `docs/reference/dependencies.md`: контур замены модели роли дополнен
  пер-агентными моделями (фасад октября 2026, зонд dwfrun-e8132143) и
  мостом №2 (без приписывания несуществующих пинов — они появляются
  тикетом 02).
- [x] `roles.py` не изменён; `resolve --json` отдаёт curator/surveyor с
  провенансом plugin-default; `pytest` зелёный (188 passed);
  `gitmark lint --strict` зелёный после inventory-синка.

## Ship facts (2026-10-13)

- Фича `724967a` + гейт-фиксы `cd90f48` (ветка `ship/roles-per-agent-01`);
  dev-мерж `8e47008`; main-мерж `2d71474`; релиз `38be1cf` + тег `v0.5.51`;
  self-update `69de1ae` (вендор `.zcode/` = v0.5.51, inventory поднял
  строку roles в commands.md — вендор-лаг закрыт штатно).
- Гейт: review `dwfrun-59de1901` (reviewer GLM-5.3-Flash$max) — 13 сырых
  находок, покрытие полное (5/5 файлов, 0 failed); confirm
  `dwfrun-572c1bde` (confirmer GLM-5.3-Flash$high) — 11 verified / 2
  опровергнуты живыми мутациями / 0 unverified. Все verified закрыты в
  `cd90f48`; commands.md — без правки (машинно-генерируемый вендор-лаг,
  вердикт конфирмера).
- Сьют 185 → 188 passed (2 пина фичи + пин строгого формата из гейта);
  мутационные пробы: точечная, sed-форма, таб-каскад, снятие якоря
  неколлизии — все живьём.
- Пин маркетплейса `4011d09` (каталог, ref v0.5.51), validate --fetch rc=0.
