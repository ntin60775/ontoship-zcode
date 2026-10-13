---
node_type: ticket
title: Роли — реестр LLM + два моста роль→модель
service: _platform
status: draft
updated: 2026-10-13
links:
  part_of: [README.md]
  implemented_by: [../../../defaults/roles.md, ../../../skills/roles/roles.py]
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

- [ ] В `defaults/roles.md` есть записи `curator` (GLM-5.3-Flash$high —
  кураторы fan-out и healer онто-дока) и `surveyor` (GLM-5.3-Flash$max —
  surveyor онто-дока; имя без коллизии с гейт-агентом `synthesizer`),
  обе с явным `level` и описанием потребителей; prose несёт правило записи
  «новая роль без специфики — запись GLM-5.3-Flash$max с явным level» и
  поимённые исключения: confirmer $high (тикет 14), curator $high
  (2026-10-13), гейт-сводчик на confirmer (к ролям не относится).
- [ ] Мутационная проба в `tests/test_roles.py`: удаление строки `level` у
  любой записи defaults (например confirmer) краснит сьют; пин полноты —
  каждая запись несёт явный `level`.
- [ ] Fail-closed правило в `skills/roles/SKILL.md` и
  `docs/reference/roles.md` содержит явный пункт: роль отсутствует в
  `resolve --json` — тот же стоп с диагностикой роли и слоя, что и
  mismatch (grep «роли нет/отсутствует» до правки — 0 совпадений).
- [ ] `skills/roles/SKILL.md` несёт секцию «два моста»: №1 — одноролевой
  ран (`subagent_model` после resolve+ListModels, паттерн гейтов), №2 —
  конвенция `{{ROLE_MODEL:<role>}}`: режим-зависимый резолв → инстанциация
  строковыми литералами в уникально именованный черновик
  `.zcode/workflow-drafts/` → дифф-префлайт (diff(инстанс, шаблон) ≡ ровно
  замены плейсхолдеров на model$level из resolve, ≥1 плейсхолдер, все
  заменены) → CreateWorkflow(path=инстанс); переиспользование старых
  инстансов запрещено. Захардкоженные перечни ролей (description :3,
  интро :8-13) синхронизированы с defaults.
- [ ] `docs/reference/roles.md`: таблица дополнена curator/surveyor,
  заголовок без «четыре роли», секция мостов с дословной цитатой
  компиляторской диагностики (persona.model — только литералы).
- [ ] `docs/reference/dependencies.md`: контур замены модели роли дополнен
  пер-агентными моделями (фасад октября 2026, зонд dwfrun-e8132143) и
  мостом №2.
- [ ] `roles.py` не изменён; `resolve --json` отдаёт curator/surveyor с
  провенансом; `pytest` зелёный; `gitmark lint --strict` зелёный после
  inventory-синка.
