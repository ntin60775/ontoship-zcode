---
node_type: ticket
title: ship-гейт — confirmer-ран
service: _platform
status: draft
updated: 2026-10-01
links:
  part_of: [../README.md]
  depends_on: [../13-reviewer-gate-split.md]
---

# 01: ship-гейт — confirmer-ран

**What to build:** шаг 6 лупа /ship подтверждает находки на отдельной роли
`confirmer`: фаза confirm выносится из ревью-рана в собственный
`skills/ship/confirm.workflow.ts`, запускаемый SKILL.md вторым CreateWorkflow
на резолвнутой роли `confirmer` (fail-closed, как reviewer). Оператор видит
те же вердикты verified/unconfirmed, но модель подтверждающего настраивается
отдельно от модели ревьюера.

**Blocked by:** 13 (архивирован; сплит-ревьюер поставляет сырые находки).

- [ ] роль `confirmer` в `defaults/roles.md` (дефолт автора
      `GLM-5.3-Flash$high`); `/roles` показывает её с провенансом;
      смоук-прогон на новой роли
- [ ] `confirm.workflow.ts`: args `{root, findings, ticket?}`; конфирмеры
      (ограда `<finding>` + neutralize) + сводчик; вход — находки
      `{where, claim, evidence, severity, quote?}`; выход — прежний контракт
      (findings verified/unconfirmed + conclusion + notCovered)
- [ ] `reviewer.workflow.ts` заканчивается сырыми находками (confirm-фаза
      вынесена); SKILL.md шаг 6 описывает два CreateWorkflow с резолвом обеих
      ролей и передачей `root`
- [ ] приёмка: прогон гейта на реальном диффе — оба рана на своих ролях,
      вердикты verified/unconfirmed различимы
- [ ] `gitmark lint` + `pytest` зелёные
