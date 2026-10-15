---
node_type: ticket
title: 'onto-doc: сырые String(e) исключений в abort-ветках — мимо redactLite'
service: _platform
status: draft
updated: 2026-10-15
links:
  part_of: [README.md]
---

# 05: onto-doc: сырые String(e) исключений в abort-ветках

**What to build:** сообщения исключений субагентов, уезжающие в conclusion
abort'ов onto-doc.workflow.ts, проходят мин-редакцию redactLite — сейчас
abort-ветка surveyor'а кладёт сырое `String(e)` в conclusion вопреки
собственному контракту файла (докстринг redactLite: «маскируются до
попадания в conclusion abort'а»). Тот же класс на ветках note куратора
и healer'а (подтверждено конфирмером как контекст).

**Blocked by:** —.

- [ ] Инвентарь сырых вставок исключений/недоверенного текста в
  conclusion/notCovered по файлу (surveyor :367 — подтверждён; :437/:515 —
  кандидаты) — каждая либо редактируется, либо обосновывается как
  доверенная.
- [ ] Правки с кейсами в tests/onto_doc_matrix.mjs (мост уже извлекает
  функции; для abort-веток — поведенческие пробы срезами, как в
  test_onto_doc_matrix.py).
- [ ] pytest и lint --strict зелёные.

**Источник:** гейт шипа queue-3/01, раунд 2 — review dwfrun-f9e6847f,
confirm dwfrun-7f851f1e (verified). Pre-existing вне хунков диффа (строка
:367 из 597e412f, 2026-10-08) — потому тикетом по правилу пополнения.
Разрыв обострён самим шипом: комментарий у точки humanZones (:385–387)
декларирует «мин-редакция, как у всякой диагностики» — сырые ветки
рядом противоречат заявленному.
