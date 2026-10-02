---
node_type: ticket
title: Роль confirmer — подтверждающий ран и свод
service: _platform
status: archived
updated: 2026-10-02
links:
  part_of: [README.md]
  depends_on: [../13-reviewer-gate-split.md]
---

# 14: Роль confirmer — подтверждающий ран и свод

**What to build:** шаг «подтверждение находок» получает собственную роль
`confirmer`: фаза confirm выносится из `skills/ship/reviewer.workflow.ts` в
отдельный `skills/ship/confirm.workflow.ts` (args: `{root, findings, ticket?}`,
вход — находки `{where, claim, evidence, severity, quote?}`), запускаемый
оркестратором скилла вторым CreateWorkflow на роли `confirmer` (fail-closed,
как reviewer). В confirm-ране живут конфирмеры (ограда `<finding>` +
neutralize) и сводчик; выход — прежний контракт: findings с
verified/unconfirmed + conclusion + notCovered. code-review workflow переходит
на тот же confirm-ран (нет split-brain). Роль `synth` не заводится — сводчик
потребляет только вывод конфирмаций (code-review.workflow.ts:277-301).

**Blocked by:** 13 (ревью-машинерия стабилизируется; 14 меняет её конфигурацию).

**Решение оператора (2026-10-01):** «квен почти бесплатный» — ролевое
разделение даёт конфирмерам дешёвую модель, а ревьюеру сильную; мотивация
наблюдена на qwen-эксперименте (fp8 ронял ревьюера, конфирмеры работали).

- [ ] роль `confirmer` в `defaults/roles.md` (дефолт автора
      `GLM-5.3-Flash$high`); разрешение тремя слоями, fail-closed без
      исключений; `/roles` показывает её с провенансом; смоук-прогон
- [ ] `skills/ship/confirm.workflow.ts` существует: конфирмеры + сводчик,
      вход `{root, findings, ticket?}`, форма находок
      `{where, claim, evidence, severity, quote?}` (quote обязателен там,
      где был: основа конфирмации по цитате и дедупа сводчика), выход —
      прежний контракт
- [ ] `reviewer.workflow.ts` отдаёт confirm-фазу (review-ран заканчивается
      сырыми находками), SKILL.md ship шаг 6 описывает два CreateWorkflow
      с резолвом обеих ролей
- [ ] code-review workflow переходит на общий confirm-ран (SKILL.md —
      ссылка на `../ship/confirm.workflow.ts`)
- [ ] onto-doc и challenger вне скоупа (конфирмаций нет)
- [ ] приёмка: прогон гейта ship на реальном диффе — оба рана на своих
      ролях, вердикты verified/unconfirmed различимы; `gitmark lint` +
      `pytest` зелёные

**Решения грилла (2026-10-01; challenger на qwen3.6-35b-a3b$high: 5 substantial
возражений, все переопределены с evidence):**

- **Q1. Как дать конфирмерам свою модель при фасаде «одна subagent_model на
  ран»?** Двухрановый гейт: review-ран → confirm-ран. Отклонено: per-agent
  override (не существует), третий ран для сводчика (YAGNI).
- **Q2. Семантика незаданной роли?** Полноценная роль, применяемая
  оркестратором скилла (резолв + subagent_model confirm-рана) — роль без
  механизма применения no-op (возражение челленджера принято). Отклонено:
  тихое наследование модели вызова.
- **Q3. Scope?** ship-гейт + code-review; onto-doc/challenger вне
  (конфирмаций нет, челленджер: severity none).
- **Q4. Форма находок?** `{where, claim, evidence, severity, quote?}` —
  quote сохранён (стирание ломало конфирмацию по цитате и дедуп сводчика —
  возражение принято); один confirm-файл, code-review ссылается на него.
- **Q5. Дефолт confirmer?** `GLM-5.3-Flash$high` (конфирмация — механическая
  проверка; сигнал false-negative на цитатах — повод перенастроить через
  `/roles`, не менять дефолт).
- **Q6. Объём?** Рефакторинг: фаза confirm выносится, создаётся
  confirm.workflow.ts, правятся оба SKILL.md; downstream (шаги 7+, оператор
  code-review) не меняется.

**Constraints:** `stop-before-commit` (дефолт); роль `synth` не заводится —
потребность (отчёты упираются в лимит ответа, свод сложнее дедупа) — сигнал
будущего тикета.

## Tickets (разбит to-tickets, 2026-10-01)

| # | Title | Status | Blocked by |
|---|---|---|---|
| [01](01-ship-gate-confirm-run.md) | ship-гейт — confirmer-ран | archived | 13 (archived) |
| [02](02-code-review-confirm-run.md) | code-review — переход на confirm-ран | archived | 01 (archived) |
