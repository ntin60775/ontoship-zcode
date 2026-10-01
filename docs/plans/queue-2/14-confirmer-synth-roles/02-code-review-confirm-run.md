---
node_type: ticket
title: code-review — переход на confirm-ран
service: _platform
status: draft
updated: 2026-10-01
links:
  part_of: [../README.md]
  depends_on: [01-ship-gate-confirm-run.md]
---

# 02: code-review — переход на confirm-ран

**What to build:** code-review workflow подтверждает находки тем же
confirm-раном, что и ship-гейт: SKILL.md ссылается на
`../ship/confirm.workflow.ts`, находки осей сериализуются в общую форму
(quote сохраняется — основа конфирмации по цитате и дедупа сводчика), сводчик
в confirm-ране сохраняет two-axis дедуп и пометки осей. Оператору
code-review не меняется: один запуск, те же отчёты.

**Blocked by:** 01 (создаёт confirm.workflow.ts).

- [ ] code-review workflow/SKILL переходят на `../ship/confirm.workflow.ts`
      (inline-конфирмеры и сводчик вынесены); quote в находках доезжает до
      конфирмеров
- [ ] приёмка: прогон code-review на реальном диффе — конфирмеры на
      confirmer-роли, свод сохраняет two-axis дедуп и цитаты в отчёте
- [ ] `gitmark lint` + `pytest` зелёные
