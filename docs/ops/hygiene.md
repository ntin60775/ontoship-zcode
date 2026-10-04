---
node_type: runbook
title: Ночная гигиена KB (lint+index+map)
service: _platform
status: active
updated: 2026-10-04
tags: [runbook, hygiene, cron, kb, lint]
links:
  implemented_by: [../../scripts/hygiene.sh]
  relates_to: [session-start-hook.md, ../plans/queue-2/10-hygiene-runbook.md]
---

# Ночная гигиена KB (lint+index+map)

Ночное обслуживание KB по расписанию: гейт `lint --strict`, перестройка
индекса, регенерация HTML-графа. Ночные ошибки не пропадают: исход пишется в
`.gitmark/hygiene.log` — машинно-читаемая последняя строка
`HYGIENE <дата> lint=<rc> index=<rc> map=<rc>`, при провале lint — рядом и сам
вывод `lint --strict`. SessionStart-хук читает лог и сообщает на старте
следующей сессии о `lint≠0` (ошибки онтологии — починить и перегнать) и об
`index≠0` — транзиентный провал перестройки, который проверка свежести ловит
не всегда (при неизменном md ничего не новее индекса); карта — косметика,
её провал виден в логе и в exit-коде скрипта. init не меняется — one-pass
остаётся one-pass (ограничение queue-2).

## Что делает скрипт

`scripts/hygiene.sh` (вендорится в `.zcode/scripts/` раннером):

1. Гард того же контракта, что у хука: не git-репозиторий / нет `docs/` /
   нет движка — тихий выход 0. Движок: вендоренный
   `.zcode/skills/kb-search/gitmark.py`, в dev-чекауте — исходный `skills/…`.
2. `lint --strict` — вывод и rc фиксируются (это sink ночных ERR).
3. `index` тихо; `map -o docs-map.html` тихо (`*-map.html` gitignored).
4. Перезаписывает `.gitmark/hygiene.log` (только последний прогон: хук
   сообщает именно последний, цикл «починил → перегонял» закрывает жалобу
   естественно) и выходит 1, если хоть один шаг упал — обычный cron-мейл это
   увидит. Успех — stdout пуст.

## Расписание

Классический cron (ночь, тихо):

```cron
0 3 * * * cd /path/to/repo && ZCODE_PROJECT_DIR=/path/to/repo bash .zcode/scripts/hygiene.sh
```

В zcode-сессии то же самое делается off-peak задачей (Idle-time task):
«еженощно запускай `bash .zcode/scripts/hygiene.sh` в корне проекта и
молчи при успехе; при exit≠0 покажи хвост `.gitmark/hygiene.log`» —
расписание не задаётся вручную, сервер сам ставит задачу в паузы.

## Проверка руками

```bash
bash .zcode/scripts/hygiene.sh; echo "rc=$?"   # успех: пусто, rc=0
cat .gitmark/hygiene.log                       # строка HYGIENE … lint=0 index=0 map=0
# md без фронтматтера в несущем подкаталоге (docs/ops/) — гарантированный
# ERR I1 «нет frontmatter с node_type»: mini-парсер движка молча пропускает
# строки без «:», а I1 проверяет только несущие пути, поэтому файл в корне
# docs/ lint не уронит.
printf 'текст без фронтматтера\n' > docs/ops/_broken.md
bash .zcode/scripts/hygiene.sh; echo "rc=$?"   # rc=1
cat .gitmark/hygiene.log                       # lint=1 и вывод ERR
rm docs/ops/_broken.md && bash .zcode/scripts/hygiene.sh   # цикл закрыт: lint=0
```

Хук подхватывает провал без пересбора: положите в лог последней строкой
`HYGIENE 2026-10-04T03:00:00+0300 lint=1 index=0 map=0` и запустите
`bash .zcode/hooks/session-start.sh` — получите JSON-упоминание гигиены
(проверка хука: `docs/ops/session-start-hook.md`).

## Контракт лога (для хука)

Последняя строка — строго `HYGIENE <ISO-дата> lint=<число> index=<число>
map=<число>`; anything else хук молча игнорирует (чужой/рукописный лог не
говорит). Дата пинается к ISO-форме — та же защитная манера, что у From-строки
handoff. Лог — derived-данные в `.gitmark/` (gitignored), в KB не коммитится.
