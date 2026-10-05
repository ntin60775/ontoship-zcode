---
node_type: ticket
title: Abort-сообщения workflow несут причину парсинга args
service: _platform
status: archived
updated: 2026-10-05
links:
  part_of: [README.md]
  relates_to: [../../reference/workflow-args.md]
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

- [x] оба workflow при битом JSON-аргументе дают abort с e.message + длиной +
      хвостом строки — живой прогон с битым аргументом (репро в
      `.scratch/diagnose-wf-args/REPORT.md`)
- [x] `gitmark lint` + `pytest` зелёные

**Shipping-note (2026-10-05).** Фича `797d1a0`, релиз v0.5.17 (релиз-коммит
`a2ae540`, тег v0.5.17, пин в marketplace.json `50ae9ff`, self-update
`4223961`). Оба workflow при непарсящемся JSON-аргументе несут abort с
`e.message`, длиной и хвостом (~80 симв.; при >80 — ещё и головой). Гейт:
reviewer qwen3.6-35b-a3b$high — 6 сырых находок, 5/5 файлов диффа; confirmer
GLM-5.3-Flash$high — 5 verified + 1 unconfirmed. Verified закрыты: не-массивный
JSON после успешного `JSON.parse` (null/объект/число) в challenger ронял код
голым TypeError (high) — теперь диагностический abort со значением; в onto-doc
не-массивный план молча превращался в `[]` и abort обвинял `args.task`, а
не-строковый `planRaw` обходил catch-ветку (medium) — теперь abort называет
`args.plan` и реальную причину; `decisions=null` молча становился пустым
черновиком (low) — теперь громкий отказ (benign no-op остался только за
явным `[]`). Без правки: `String(e)`-fallback в catch — мёртвая защитная
ветка (JSON.parse всегда бросает SyntaxError), подтверждена конфирмером как
наблюдение без практической опасности. Unconfirmed отчитан оператору:
«shell injection в `onto-doc.workflow.ts:104`» опровергнут с доказательствами —
строка 104 — фрагмент system-промпта куратора, не shell-команда; `world.run`
передаёт `root` отдельным элементом argv-массива. Приёмка: 4 живых прогона
(по 2 на workflow; финальные `dwfrun-68b30b8a`/`dwfrun-7182edf0` — на
финальном коде, abort-сообщения с полной диагностикой) + локальные пробы
закрытых находок исполнением срезов реальных файлов через node strip-types
(8/8 кейсов challenger, 9/9 onto-doc). pytest 95, `gitmark lint --strict`
rc=0, dev-чекауты зелёные. Отклонений от лупа нет; prod-чек: деплой-контура
как такового нет (прецедент 08/15/16) — живые прогоны финального кода в
хостовом рантайме и есть сильнейшая prod-проверка, вендор доехал
self-update'ом v0.5.17 (deploy-check зелёный; вместе с вендором ожив
to-tickets SKILL.md из `2b7cf96`). KB-готча из Prevention диагноза 09
записана: `docs/reference/workflow-args.md`.
