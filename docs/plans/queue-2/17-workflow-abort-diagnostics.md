---
node_type: ticket
title: Abort-сообщения workflow несут причину парсинга args
service: _platform
status: draft
updated: 2026-10-03
links:
  part_of: [README.md]
---

# 17: Abort-сообщения workflow несут причину парсинга args

**What to build:** `challenger.workflow.ts:61` и `onto-doc.workflow.ts:56`
глотают причину неудачного `JSON.parse` аргументов — abort показывает только
голову строки (`slice(0, 80)`); диагноз 09 показал, что это стоило недели
ложных гипотез («хост обрезает» вместо «битый JSON у вызывающего»). В
abort-сообщение включать: `e.message` парсера, полученную длину строки и её
хвост (~80 символов) — по хвосту «обрезано» (нет закрывающих `]}`) и «битый
синтаксис» (ошибка с позицией) различаются сразу.

**Blocked by:** None (can start immediately).

- [ ] оба workflow при битом JSON-аргументе дают abort с e.message + длиной +
      хвостом строки — живой прогон с битым аргументом (репро в
      `.scratch/diagnose-wf-args/REPORT.md`)
- [ ] `gitmark lint` + `pytest` зелёные
