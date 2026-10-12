---
node_type: ticket
title: Роли — реестр LLM + два моста роль→модель
service: _platform
status: draft
updated: 2026-10-13
links:
  part_of: [README.md]
  implemented_by: [../../../defaults/roles.md, ../../../skills/roles/roles.py]
---

# 01: Роли — реестр LLM + два моста роль→модель

**What to build:** роли становятся единственным реестром LLM субагентов:
новые записи `curator` (GLM-5.3-Flash$high) и `synthesizer`
(GLM-5.3-Flash$max) с описаниями потребителей, prose-правило общего дефолта
(любая роль без специфики — GLM-5.3-Flash$max), и документированные два
моста роли в воркфлоу: одноролевой (subagent_model после resolve+ListModels)
и многоролевой (инстанциация движка-шаблона литералами ролей запускающим
агентом). Неявный дефолт неизвестной роли в резолвер не заводится — опечатка
падает fail-closed.

**Blocked by:** None (can start immediately).

- [ ] В `defaults/roles.md` есть записи `curator` (GLM-5.3-Flash$high —
  воркеры онто-дока: кураторы fan-out и healer) и `synthesizer`
  (GLM-5.3-Flash$max — «сводящий»/сильнейший агент прогона; конкретный
  потребитель онто-дока — по гриллу тикета 02) с описаниями; prose несёт
  правило «общий дефолт роли — GLM-5.3-Flash$max» и исключение confirmer
  $high (тикет 14).
- [ ] `docs/reference/roles.md`: таблица ролей дополнена curator/synthesizer;
  секция «мосты роль→модель» описывает оба паттерна с точными шагами
  запуска (resolve → ListModels → стоп при несовпадении → запуск) и
  компиляторский предел (persona.model известен до старта; args-строки
  запрещены — диагностика хоста процитирована).
- [ ] `skills/roles/SKILL.md` несёт секцию про два моста: как одноролевой
  ран получает `subagent_model`, как многоролевой инстанцирует шаблон
  литералами; help-список ролей читается из defaults (новые роли видны без
  правки текста).
- [ ] `docs/reference/dependencies.md`: контур замены модели роли дополнен
  пер-агентными моделями (фасад октября 2026, зонд dwfrun-e8132143).
- [ ] `roles.py` не изменён (или изменён только текстами — механика готова:
  свободные имена, слои, провенанс); `resolve --json` отдаёт новые роли с
  провенансом; битые слои по-прежнему fail-closed.
- [ ] `pytest` зелёный (включая `tests/test_roles.py` — при необходимости
  добавлены пины записей curator/synthesizer в defaults); `gitmark lint
  --strict` зелёный после inventory-синка реестра планов.
