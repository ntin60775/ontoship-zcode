---
node_type: ticket
title: code-review — переход на confirm-ран
service: _platform
status: archived
updated: 2026-10-02
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

- [x] code-review workflow/SKILL переходят на `../ship/confirm.workflow.ts`
      (inline-конфирмеры и сводчик вынесены); quote в находках доезжает до
      конфирмеров
- [x] приёмка: прогон code-review на реальном диффе — конфирмеры на
      confirmer-роли, свод сохраняет two-axis дедуп и цитаты в отчёте
- [x] `gitmark lint` + `pytest` зелёные

**Shipping note (2026-10-02, ран 14/02):** реализовано в `39e8a83`
(ветка ship/queue-2-14-02 → main, fast-forward). `code-review.workflow.ts`
заканчивается сырыми находками общей формы (axis едет с находкой, цитата оси —
evidence и quote; пустые оболочки отбрасываются со счётчиком), SKILL.md
оркестрирует два CreateWorkflow на резолвнутых ролях reviewer
(`neuraldeep-sub/qwen3.6-35b-a3b$high`, user-слой) и confirmer
(`GLM-5.3-Flash$high`, дефолт плагина), второй ран —
`../ship/confirm.workflow.ts` с `report:"markdown"`. `confirm.workflow.ts`
получил опц. `axis` и report-режим (полный отчёт с цитатами, артефакт
review, скриптовый fallback с redact+экранированием markdown и оградой длиннее
серий backtick), two-axis дедуп и пометки осей — по подтверждённым находкам;
ship-путь (без осей и report) не изменён.

**Гейт и приёмка:** гейт — reviewer-ран 12 сырых → confirmer-ран 10 verified /
2 unconfirmed (обе опровергнуты разбором: перепутанное old/new у
redact-находки; контент-условная секция отчёта). Приёмка — 4 прогона
code-review на собственном диффе (v1–v4); критерии (confirmer-роль, two-axis
дедуп, цитаты в отчёте) подтверждены на каждом прогоне. По verified-находкам
между прогонами — точечные правки: хардкод осей в description → из
подтверждённых данных; критерий останова и формулировка findings-аргумента в
SKILL.md; redact-щели fallback и allowlist (axis); экранирование markdown в
fallback; счётчик droppedEmpty в conclusion; мёртвое поле key; формулировка
«открой файл». v4: 11 сырых → 7 verified / 4 опровергнуты (цитаты против
собственных claim'ов, no-op-коэрция catch-нормализации, ES-семантика
регекс-класса и тернарника).

**Отложено (решение оператора 2026-10-02):** high-находка «модельный свод без
пост-redact» и redact на прозе claim (унаследовано от queue-2/06) → follow-up
в тикет 15 (внесены туда же: PEM-цифры в префиксе, сертификаты/публичные
ключи, короткие значения). Косметика fallback (оставшиеся markdown-символы
мимо md(), where без экранирования, пометка отказа сводчика в conclusion
markdown-режима) и осознанный дубликат evidence==quote (решение грилла 14/Q4)
— в отчётах ранов, не чинились. Отклонения от полного лупа: dev-ветки нет —
сьют на ветке и main (lint --strict чисто, pytest 72 passed, deploy-check 0);
прод-контура нет — сьют и есть проверка; `commands.md` синхронизирован
inventory на деплой-шаге (таблица генерируется из `.zcode/`, ручная правка в
исходнике откатывается генератором — наблюдение зафиксировано).
