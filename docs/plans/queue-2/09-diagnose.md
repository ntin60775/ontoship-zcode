---
node_type: ticket
title: diagnose — репро-цикл на вопросах
service: _platform
status: archived
updated: 2026-10-03
links:
  part_of: [README.md]
---

# 09: diagnose — репро-цикл на вопросах

**What to build:** diagnose-скилл сводит баг или странный вопрос к минимальному
воспроизведению через цикл гипотез и проверок: воспроизвести до фикса,
зафиксировать репро, сформулировать диагноз с доказательством.

**Blocked by:** None (can start immediately).

- [x] скилл существует; прогон на реальном вопросе даёт воспроизводимый репро
      и диагноз с доказательством
- [x] репро не теряется: зафиксировано там, где его найдёт продолжение работы
- [x] `gitmark lint` + `pytest` зелёные

## Прогон (shipping note, 2026-10-03)

- worktree `../ontoship-zcode-ship-09`, ветка `ship/queue-2-09`; скилл — порт
  метода mp-diagnose (ontoship-omp) под zcode: оператор-запуск, артефакты в
  `.scratch/diagnose-<slug>/`, диагноз эфемерен (kb-curate), фикс — только
  через grilling → to-tickets → ship.
- Гейт: reviewer `qwen3.6-35b-a3b$high` → 8 сырых; confirmer
  `GLM-5.3-Flash$high` → 7 verified закрыто в диффе, 1 unconfirmed отчитан:
  «SKILL.md:48 относительный путь hitl-шаблона» — опровергнут с
  доказательствами (якорь «next to this SKILL.md» в той же строке; конвенция
  ещё 8 скиллов), не чинился.
- Закрытое verified: резолюция repo-root + деривация/санитизация slug +
  mkdir; исполнимый рецепт фазы 0 redact (env-значения не в argv, re-grep);
  Redaction-запись в REPORT (фаза 0 проверяема, skip-оправдание пишется);
  EOF-защита read в HITL-шаблоне (set -e доедал скрипт до Captured);
  валидация bash-идентификатора в capture.
- Приёмочный прогон на реальном вопросе: аномалия args CreateWorkflow —
  **капа нет** (транспорт байт-в-байт, проверено до ~24.8 КБ/аргумент и
  ~33 КБ суммарно; пробы `dwfrun-41e7c846`, `dwfrun-eb1e4a99`), оригинальный
  отказ 2026-09-30 (`dwfrun-59c259bb`) — невалидный JSON в строке на
  отправке, а не обрезка хостом. Отчёт с репро:
  `.scratch/diagnose-wf-args/REPORT.md` (основной чекаут; путь — это и есть
  фиксация репро для продолжения работы). Память
  `challenger-workflow-arg-length` исправлена.
- Фоллоу-апы из прогона: (1) abort-сообщения `challenger.workflow.ts` /
  `onto-doc.workflow.ts` должны нести e.message + хвост строки (сейчас
  причина парсинга глотается); (2) `reviewer.workflow.ts` не видит
  untracked-файлы диффа (`git.changedFiles` — tracked only; первый ран гейта
  отревьюил 2 из 4 файлов, спас перезапуск после `git add -A`).
- Честная деградация: headless-проба скилла невозможна как у соседей;
  живой прогон выше — и есть приёмка. suite 80 passed, `lint --strict` чист.
