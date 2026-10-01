---
node_type: ticket
title: code-review workflow — две оси параллельно
service: _platform
status: draft
updated: 2026-10-01
links:
  part_of: [README.md]
---

# 06: code-review workflow — две оси параллельно

**What to build:** ревью диффа запускается workflow с двумя независимыми осями
параллельно (корректность и качество/опасные места), на явно назначенных моделях
ролей; свод вердиктов приходит оператору одним читаемым списком с вердиктами
verified/unconfirmed по каждой находке.

**Blocked by:** None (can start immediately).

- [ ] workflow-файл существует; обе оси отрабатывают параллельно на реальном
      диффе и сводятся в один отчёт
- [ ] вердикты находок различимы (verified / unconfirmed), находки опираются на
      цитаты кода
- [ ] `gitmark lint` + `pytest` зелёные
