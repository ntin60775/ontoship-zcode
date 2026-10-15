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
  conclusion/notCovered по файлу (surveyor :369 — подтверждён; :439/:517 —
  кандидаты) — каждая либо редактируется, либо обосновывается как
  доверенная.
- [ ] Правки с кейсами в tests/onto_doc_matrix.mjs (мост уже извлекает
  функции; для abort-веток — поведенческие пробы срезами, как в
  test_onto_doc_matrix.py).
- [ ] pytest и lint --strict зелёные.

**Источник:** гейт шипа queue-3/01, раунды 2–3 — review dwfrun-f9e6847f,
confirm dwfrun-7f851f1e и dwfrun-3abc44d2/a6a3d904 (verified). Pre-existing
вне хунков диффа: строка введена 597e412f (2026-10-08, тогда
skills/doc/onto-doc.workflow.ts:230; на текущем пути — :369 в дереве шипа,
якоря писались против 31721ab и сдвинуты фиксами r2/r3 — подтверждено
конфирмером r3 с трассировкой по всем ревизиям). Разрыв обострён самим
шипом: комментарий у точки humanZones (:387–389) декларирует «мин-редакция,
как у всякой диагностики» — сырые ветки рядом противоречат заявленному.
