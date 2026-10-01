---
node_type: ticket
title: architecture workflow — скан в фоне
service: _platform
status: draft
updated: 2026-10-01
links:
  part_of: [README.md]
---

# 07: architecture workflow — скан в фоне

**What to build:** архитектурный скан репо исполняется как фоновый workflow:
карта модулей и связей, точки дрейфа от задокументированной архитектуры,
отчёт оператору; сессия не блокируется на время скана.

**Blocked by:** None (can start immediately).

- [ ] workflow-файл существует; скан уходит в фон и не блокирует сессию
- [ ] отчёт по реальному репо: модули, связи, расхождения с KB-документацией
- [ ] `gitmark lint` + `pytest` зелёные
