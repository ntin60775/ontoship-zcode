---
node_type: ticket
title: ship-гейт — confirmer-ран
service: _platform
status: archived
updated: 2026-10-02
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

- [x] роль `confirmer` в `defaults/roles.md` (дефолт автора
      `GLM-5.3-Flash$high`); `/roles` показывает её с провенансом;
      смоук-прогон на новой роли
- [x] `confirm.workflow.ts`: args `{root, findings, ticket?}`; конфирмеры
      (ограда `<finding>` + neutralize) + сводчик; вход — находки
      `{where, claim, evidence, severity, quote?}`; выход — прежний контракт
      (findings verified/unconfirmed + conclusion + notCovered)
- [x] `reviewer.workflow.ts` заканчивается сырыми находками (confirm-фаза
      вынесена); SKILL.md шаг 6 описывает два CreateWorkflow с резолвом обеих
      ролей и передачей `root`
- [x] приёмка: прогон гейта на реальном диффе — оба рана на своих ролях,
      вердикты verified/unconfirmed различимы
- [x] `gitmark lint` + `pytest` зелёные

**Отгружено (2026-10-02).** Коммиты `bcd920b` (feat) + `b558bb0` (фикс
кросс-чтений) + `053ab3d` (правки по вердиктам приёмки) в worktree
`ship/14-confirmer-synth-roles-01`, ff-мерж в main, релиз `v0.5.9`
(`881eee2`), self-update (`672f230`), deploy-check exit=0, push. Роль
`confirmer` резолвится из plugin-default (`GLM-5.3-Flash$high`; user-слой её
не перекрывает — reviewer/challenger остались на qwen35b); смоук-микроворкфлоу
на роли вернул OK.

Шаг-6 гейт (вендорный монолит v0.5.8) на диффе тикета: 12 находок (8 verified:
2 зафиксированы — явное поле `findings` в SKILL.md и контекст в именах
конфирмеров; 6 опровергнуты с evidence — среди них «сломанный контракт
возврата» = сам тикет и отсутствие таймаута на ask, которого нет в фасаде;
4 unconfirmed: 2 зафиксированы по сути — neutralize(ticket) и allowlist вместо
spread в выводе, 2 опровергнуты конфирмером).

Приёмка: первый запуск review-рана дважды остановлен провайдером —
qwen3.6-35b рвал контекстное окно на reviewer-f4 (агент кросс-читал соседние
файлы диффа, ask этого не запрещал, хотя дизайн гейта декларирует «only its
file's diff»); 4/5 файл-ревью прошли (f2 сжёг 852K токенов на confirm.workflow.ts
— 35b работает у кромки окна). Оператор выбрал «ограничить чтения»: строка в
ask ревьюера, свежий CreateWorkflow (AmendWorkflow на этом хосте не переносит
args — кэш 4/5 потерян). v2 прошёл: 16 сырых находок. Confirm-ран на
GLM-Flash$high: 16 → 10 verified / 6 unconfirmed + дедуп-свод; args с 16
находками (~6.5 КБ) прошли наблюдённый на challenger лимит ~4.6 КБ. Вердиктам
различимы: подтверждены реальные дефекты, оба громких «high» (shell-инъекция
через q(), root без neutralize) опровергнуты конфирмерами с разбором кода.

По вердиктам приёмки (`053ab3d`): SKILL.md — стоп при сбое review-рана,
якорь stop-before-commit (оба рана), пустой findings — валидный вход;
roles.md — формулировка без «mechanical» (ран синтезирует и свод), уровень
high с fail-closed-оговоркой; confirm.workflow.ts — комментарий о трейд-оффе
«конфирмеры видят уже отредактированные находки» (находка с секретом в
evidence подтвердится хуже — сознательная защита от расползания секретов по
ранам; альтернатива «передавать конфирмерам сырые» отклонена).

**Отложено в follow-up** (кандидат-тикет «полнота redact»): PEM-регекс не
маскирует `-----BEGIN PGP PRIVATE KEY BLOCK-----` (node-проба), `eyJ`-альтернатива
ловит любой base64url-литерал (state=eyJ… → [REDACTED]), общая полнота redact
(V9/V11 шага-6 гейта: raw hex/base64, query-креды) и ложные срабатывания на
`auth`/`token`-именах. Всё — унаследовано от baseline 13, не регресс 14/01;
изменение поведения redact после приёмочного прогона сознательно не делалось.

Отклонения: dev-ветки нет — сьют на ветке (72 passed) и main; деплой — ручной
вендор изменённых маппингов в `.zcode/` по deploy.json (раннер не вызывался),
post_update (index) выполнен, deploy-check зелёный; подтверждения мержа и
деплоя одним сообщением «continue и деплой»; из self-update-коммита убран
случайно затянутый незатреканный план-файл сессии (amend).
