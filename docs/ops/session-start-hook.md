---
node_type: runbook
title: SessionStart-хук свежести индекса
service: _platform
status: active
updated: 2026-09-30
tags: [runbook, hooks, session-start, kb, index]
links:
  implemented_by: [../../hooks/session-start.sh]
  relates_to: [install.md, deploy-check.md, ../plans/queue-2/03-session-start-hook.md]
---

# SessionStart-хук свежести индекса

Хук запускается при старте сессии и не даёт KB отвечать устаревшим: если
какой-нибудь markdown из корпуса движка новее `.gitmark/index.db`, агент
получает напоминание перестроить индекс. Корпус — весь md репозитория по
`git ls-files -c -o --exclude-standard -- '*.md'` (как у самого движка), а
не только `docs/`; gitignored-файлы исключены так же, как в индексе. Вне
KB-проектов (не git-репозиторий, нет `docs/` или нет вендоренного движка
`.zcode/skills/kb-search/gitmark.py`) — тихий выход 0. Хук никогда не
блокирует сессию: все пути — exit 0, говорит только через SessionStart
`additionalContext`.

## Регистрация — данные проекта

Раннер вендорит **код** (`deploy.json`: `hooks → .zcode/hooks`), но хук
должен быть зарегистрирован в конфиге самого проекта —
`<repo>/.zcode/config.json`. Регистрируйте **после** `install`/`update`,
когда `.zcode/hooks/session-start.sh` уже вендорен (иначе каждая сессия
ловит recoverable-ошибку «файл не найден»):

```json
{
  "hooks": {
    "enabled": true,
    "events": {
      "SessionStart": [
        {
          "hooks": [
            {
              "type": "command",
              "command": "bash \"${ZCODE_PROJECT_DIR}/.zcode/hooks/session-start.sh\"",
              "timeoutMs": 60000,
              "statusMessage": "свежесть индекса KB"
            }
          ]
        }
      ]
    }
  }
}
```

Без `"enabled": true` конфигурационные хуки не запускаются (плагинных хуков
у ontoship нет — манифест плагина не используется раннером маркетплейса).
Матчер опущен. В проверенном рантайме (zcode 0.16.9) SessionStart
срабатывает на `startup` и `resume`; после `/clear` приходит новая сессия
(снова `startup`), а вот после `/compact` — нет: до рестарта сессии
напоминания о свежести не будет. Это известное ограничение, а не поломка.

## Поведение

| Ситуация | Действие |
|---|---|
| не git-репозиторий, нет `docs/` или нет вендоренного движка | тишина, exit 0 |
| `.gitmark/index.db` отсутствует | напоминание собрать индекс |
| есть md корпуса новее индекса | напоминание перестроить |
| индекс свежее всего markdown | тишина, exit 0 |
| mtime из будущего (рассинхрон часов, распаковка архивов) | такой файл пропускается — перестройка не может его «догнать», вечный сигнал был бы ложным |
| `--rebuild` (флаг регистрации) | тихий `gitmark index`; при неудаче — напоминание, сессия не блокируется |

По умолчанию хук **напоминает**, а не перестраивает: побочный эффект на
старте сессии — решение оператора, а не плагина. Перестройку выбирают флагом
в команде регистрации: `bash "${ZCODE_PROJECT_DIR}/.zcode/hooks/session-start.sh" --rebuild`.
На большой KB (сотни–тысячи md) тихая перестройка может не укладываться в
таймаут хука — убийство по таймауту для хука бессловесно (индекс при этом не
портится: движок коммитит одной транзакцией); держите режим напоминания и
запускайте rebuild руками.

## Проверка руками

```bash
bash .zcode/hooks/session-start.sh; echo "rc=$?"    # пусто и rc=0 — индекс свеж / не KB-проект
touch docs/что-нибудь.md && bash .zcode/hooks/session-start.sh   # JSON-напоминание
bash .zcode/hooks/session-start.sh --rebuild        # тихо перестроил
```

Факт срабатывания и исход пишутся в лог zcode (`~/.zcode/logs`): запись хука
несёт источник, матчер, исход (fired/timeout/failed) и превью stderr.
Напоминание видно агенту в начале сессии как additionalContext.
