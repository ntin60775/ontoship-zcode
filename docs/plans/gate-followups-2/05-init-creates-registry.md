---
node_type: ticket
title: Init создаёт реестр команд
service: _platform
status: archived
updated: 2026-10-07
links:
  part_of: [README.md]
---

# 05: Init создаёт реестр команд

**What to build:** `/init` (плагинная форма `/ontoship:init`) сегодня управляет
только managed-блоком в AGENTS.md и строками `.gitignore`; скелет реестра
команд `docs/reference/commands.md` (frontmatter-шапка + маркеры
`BEGIN/END inventory:commands` и `inventory:skills`) не создаёт никто — свежий
KB-проект получает вечный красный I7 «реестр не найден» в `lint --strict`.
Живой кейс: KB репозитория sot-zcode-marketplace — I7 красный с рождения KB
(вендоренный онтошип стоит, реестра нет, инвентарь запускать некуда). Init
создаёт скелет при отсутствии файла и обеспечивает заполнение таблиц
(`gitmark inventory`); существующий реестр не трогает. Комментарий в
`tests/test_hygiene_script.py` («the same thing the init skill does») перестаёт
врать.

**Blocked by:** None (can start immediately).

- [x] после `/init` на проекте без реестра `docs/reference/commands.md`
      существует: валидная шапка, оба инвентарных маркера; таблицы заполнены
      (скилл прогоняет `gitmark inventory` сам или текст предписывает прогон)
- [x] повторный `/init` существующий реестр не перезаписывает (idempotent)
- [x] `lint --strict` на свежем scratch-проекте после `/init` зелёный — I7
      закрыт без ручных шагов
- [x] тест механики init в духе test_hygiene_script (scratch-проект) +
      комментарий в test_hygiene_script.py приведён в соответствие с фактом
- [x] `gitmark lint` + `pytest` зелёные


**Shipping-note (2026-10-07).** Фича `b22135f`, гейт-фикс `dc02048` (мерж
`5fadb51` dev / `75edfe4` main), релиз v0.5.30 `3a3fe84`+тег, пин `b6e8f29`
(маркетплейс, каталог 0.5.61), self-update `5722a20` (этот репо) + `cc3db7f`
(маркетплейс-репо), inventory-синк `4b3fdaf`. Особенность цикла: дифф тикета
послужил материалом живой приёмки линз (см. 07) и прошёл собственный
формальный гейт уже на финальном субстрате — вендор v0.5.30. Гейт: reviewer
qwen3.6-unlim-xl$high — 9 сырых (3/3 файла; logic-линза — именованный
finish=length на одном файле, файл покрыт tests-линзой); confirmer
GLM-5.3-Flash$high — 1 verified / 8 опровергнуты / 0 unverified. Verified
закрыта гейт-фиксом `dc02048`: фикс-поинт тест прятал причину сбоя за
check=True (CalledProcessError без stderr движка) — заменён на именованный
ассерт, как в seed_registry. Опровергнуты прогонами: «нет test_* в диффе»
(test_init_registry.py — новый файл целиком в диффе), «протекание check=True»
(именованный ассерт уже стоял), «CLI-путь ломает inventory» (post_update зовёт
его же; репро exit 0 с заполненными таблицами), «I7-сообщение вводит в
заблуждение» (I7 — код дефекта, сообщение описывает провал). Сьют после фикса
133 passed. Отступления-константы: MR нет — локальный мерж в dev; прод-контур
— suite + deploy-check + вендор self-update'ом.
