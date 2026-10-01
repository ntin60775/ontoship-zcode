---
node_type: ticket
title: onto-doc workflow — fan-out кураторов + lint-гейт
service: _platform
status: draft
updated: 2026-10-01
links:
  part_of: [README.md]
---

# 05: onto-doc workflow — fan-out кураторов + lint-гейт

**What to build:** док-задача исполняется workflow: план правок расходится
fan-out по кураторам (каждый ведёт свой кусок KB), собранный результат проходит
`gitmark lint` как гейт, провалившееся лечится циклом долечивания до зелёного.
Оператор получает долеченную, линт-чистую правку KB, а не черновик.

**Blocked by:** None (can start immediately).

- [ ] workflow-файл существует и запускается на реальной док-задаче в этом репо:
      fan-out кураторов, сборка, lint-гейт после сборки
- [ ] цикл долечивания доводит прогон до зелёного `gitmark lint` или честно
      репортит потолок попыток
- [ ] `gitmark lint` + `pytest` зелёные
