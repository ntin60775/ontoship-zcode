---
node_type: ticket
title: deploy-check — валидация вендоренной раскладки
service: _platform
status: draft
updated: 2026-09-30
links:
  part_of: [README.md]
  depends_on: [01-install-visibility.md]
---

# 02: deploy-check — валидация вендоренной раскладки

**What to build:** проверка развёртывания одной командой: `deploy-check.sh` в
проекте с задеплоенным плагином подтверждает, что вендоренный код на месте и
работает — зелёный на живом деплое, `[FAIL]` на сломанной.

**Blocked by:** 01 (проверяется вендоренная раскладка из самодеплоя).

- [ ] `scripts/deploy-check.sh` (в репо плагина, запуск — из проекта-потребителя):
      пакетные пути по журналу/маппингам — `.zcode/skills/kb-search/gitmark.py`,
      `.zcode/defaults/roles.md`, `.zcode/deployed.json`; без omp-путей
- [ ] Движок работает из вендоренного пути: index/search смоук в cwd проекта
- [ ] Роли: `roles.py resolve` из `.zcode` находит дефолт
- [ ] SQLite FTS5 обязателен, trigram опционален (WARN)
- [ ] Прогон: зелёный на самодеплое из тикета 01; ручная порча вендоренного файла
      даёт `[FAIL]` и exit 1
