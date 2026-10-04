---
node_type: ticket
title: Confirm-ран — отказ проверки ≠ опровержение
service: _platform
status: draft
updated: 2026-10-04
links:
  part_of: [README.md]
---

# 02: Confirm-ран — отказ проверки ≠ опровержение

**What to build:** confirm-ран различает три исхода находки: `verified`
(воспроизведено независимо), `unconfirmed` (проверено — не воспроизводится) и
`unverified` (проверка не состоялась: конфирмер не отработал). Сегодня исключение
конфирмера (сеть, лимит, отказ) даёт `holds: false` → находка помечается
unconfirmed и уходит оператору как «нужны глаза человека» — один сбой API
конвертируется в ложный шум. Отказ конфирмера ретраится один раз без разбора
причины (снифинг причин приходит с queue-2/17), второй отказ → `unverified` с
причиной в confirmationNote. Сводчик и markdown-отчёт показывают unverified
отдельной секцией — не «не подтверждено», а «не проверено».

**Blocked by:** None (can start immediately).

- [ ] отказ agent()-вызова конфирмера → один retry; повторный отказ → статус
      `unverified`, причина сохранена в confirmationNote
- [ ] контракт выхода confirm-рана: status ∈ {verified, unconfirmed, unverified};
      шапка workflow описывает все три исхода
- [ ] gate-digest и markdown-отчёт различают три секции/счётчика; unverified
      сформулирован как отказ проверки, не как опровержение
- [ ] `skills/ship/SKILL.md` шаг 6 и `skills/code-review/SKILL.md` шаг 4 описывают
      три исхода (unverified докладывается оператору наравне с unconfirmed,
      но называется тем, чем является — проверка не состоялась)
- [ ] контракт входа не меняется: findings от обоих review-ранов принимаются
      как раньше (общая форма находки гейта нетронута)
- [ ] `gitmark lint` + `pytest` зелёные
