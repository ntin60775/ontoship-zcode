---
node_type: ticket
title: Init создаёт реестр команд
service: _platform
status: draft
updated: 2026-10-06
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

- [ ] после `/init` на проекте без реестра `docs/reference/commands.md`
      существует: валидная шапка, оба инвентарных маркера; таблицы заполнены
      (скилл прогоняет `gitmark inventory` сам или текст предписывает прогон)
- [ ] повторный `/init` существующий реестр не перезаписывает (idempotent)
- [ ] `lint --strict` на свежем scratch-проекте после `/init` зелёный — I7
      закрыт без ручных шагов
- [ ] тест механики init в духе test_hygiene_script (scratch-проект) +
      комментарий в test_hygiene_script.py приведён в соответствие с фактом
- [ ] `gitmark lint` + `pytest` зелёные
