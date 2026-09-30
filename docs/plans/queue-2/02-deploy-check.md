---
node_type: ticket
title: Порт deploy-check под zcode-раскладку
service: _platform
status: draft
updated: 2026-09-30
links:
  part_of: [README.md]
  depends_on: [01-install-visibility.md]
---

# 02: Порт deploy-check под zcode-раскладку

**What to build:** проверка развёртывания плагина одной командой: `deploy-check.sh`
резолвит корень пакета от своего расположения, проверяет ключевые файлы zcode-плагина
(движок, скиллы, роли-дефолт, манифест), FTS5/trigram, смоук индекса и поиска —
зелёный на живой установке, `[FAIL]` на сломанной.

**Blocked by:** 01 (проверяется установленная раскладка).

- [ ] `scripts/deploy-check.sh`: пакетные файлы от корня пакета (skills/, defaults/,
      .zcode-plugin/), entry point AGENTS.md — от корня проекта; без omp-путей
- [ ] Страж: payload не ссылается на мёртвые пути движка (в zcode путь относительный
      через SKILL.md — страж ищет именно их отсутствие/наличие по-новому)
- [ ] SQLite FTS5 обязателен, trigram опционален (WARN); смоук index+search в cwd
- [ ] Роли: `roles.py resolve` находит дефолт (fail в обратном случае — WARN)
- [ ] Прогон: зелёный на живой установке из тикета 01; ручная порча одного файла
      даёт `[FAIL]` и exit 1
