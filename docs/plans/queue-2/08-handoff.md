---
node_type: ticket
title: handoff — ReadSessionContext + .scratch/
service: _platform
status: draft
updated: 2026-10-02
links:
  part_of: [README.md]
---

# 08: handoff — ReadSessionContext + `.scratch/`

**What to build:** сессия передаёт контекст следующей. Handoff-скилл
`skills/handoff/` (запуск только оператором: /handoff, «передай смену») пишет
`.scratch/handoff-<id>.md` (id — session id маркера или timestamp; предыдущие
handoff-файлы не затираются) по фиксированному шаблону: From (session id,
дата), Task (ссылка на тикет/план), Done, Decisions (каждая с evidence в
формате `path:line`, commit или `#sess_*`), Open, Next, Artifacts. Правило:
репо-изменённые решения живут в репо — файл ссылается, не дублирует;
переживающие задачу факты (конвенции, предпочтения) при handoff уходят в
memory одной строкой, не в файл. Session id берётся из маркера
`.scratch/.session-id`, который SessionStart-хук пишет из своего env
(`ZCODE_SESSION_ID`); нет маркера — честная деградация: оператор передаёт
`#sess_*` вручную. Новую сессию приводит тот же хук: свежий (≤7 дней) новейший
handoff — анонс «прочти и продолжи; глубже — ReadSessionContext(sessionId=
<old>, strategy=handoff)», склеенный с напоминанием о свежести индекса в один
emit (ровно один JSON на stdout). Аварийный конец сессии без /handoff — known
limitation: транскрипт сессии остаётся, fallback — `#sess_*`/ReadSessionContext.

**Blocked by:** None (can start immediately).

- [ ] скилл `skills/handoff/SKILL.md` существует: пишет handoff-файл по
      шаблону, не затирая предыдущие; при записи удаляет протухшие (>7 дней)
      handoff-файлы; граница handoff / memory / report зафиксирована в
      SKILL.md
- [ ] SessionStart-хук: пишет `.scratch/.session-id` из `ZCODE_SESSION_ID`
      (нет переменной — не пишет, тишина); анонсирует новейший свежий handoff
      с ReadSessionContext-подсказкой; stdout-контракт — всегда ровно один
      JSON одним emit'ом; тесты test_session_start_hook.py расширены (маркер
      с переменной и без; анонс свежий/протухший/отсутствующий; один JSON)
- [ ] передача проверена на живой паре сессий: A пишет handoff, B продолжает
      без потерянных решений, `ReadSessionContext(A, strategy=handoff)`
      достаёт деталь, которой в файле нет (headless-проба невозможна —
      прецедент 03: `Model creation failed`; честная деградация)
- [ ] deploy.json: + mapping `skills/handoff`; inventory-строка commands.md
      перегенерирована `gitmark inventory` (сканирует и skills/ —
      gitmark.py:804-811); вендор-копия — релизным циклом
- [ ] `gitmark lint` + `pytest` зелёные

**Решения грилла (2026-10-02; challenger на neuraldeep-sub/qwen3.6-35b-a3b$high:
6 substantial + 4 minor, все substantial пере-решены; 2 факт-претензии
проверены: env-переменные хука подтверждены по бандлу, inventory-претензия
опровергнута по gitmark.py:804-811):**

- **Q1. Форма механики?** Скилл, исполняется сессией по вызову оператора; не
  workflow (fan-out не нужен) и не авто-запись (Stop стреляет после каждого
  ответа). Evidence: docs/ontology.md:156-160, skills/ship/SKILL.md:8-9.
  Отклонено: workflow, Stop-хук.
- **Q2. Артефакт?** Per-session файлы `.scratch/handoff-<id>.md`, discovery —
  новейший по mtime (возражение принято: single-file перезапись теряла
  Decisions предыдущих сессий цепочки A→B→C; механическое сохранение лучше
  мягкого правила переноса). Отклонено: single-file с carry-forward-правилом,
  symlink (mtime решает), KB-док (онтология: ephemeral).
- **Q3. Содержание?** Шаблон From/Task/Done/Decisions/Open/Next/Artifacts;
  Task ссылается на тикет/план, evidence-ссылки в формате `path:line`,
  commit, `#sess_*` (поправка принята). Отклонено: дублирование репо.
- **Q4. Session id?** Хук пишет маркер из env `ZCODE_SESSION_ID` (бандл
  подтверждает CLAUDE_SESSION_ID/ZCODE_SESSION_ID в окружении хуков —
  поправка принята, stdin-парсинг не нужен); скилл читает маркер. Отклонено:
  чтение db.sqlite (268М, схема недокументирована), stdin-парсинг.
- **Q5. Подача новой сессии?** Анонс в SessionStart-хук, но одним emit'ом
  (возражение принято: два JSON на stdout ломали бы парсер раннера и
  ctx_of-тест); части сообщения склеиваются.
- **Q6. Чистка?** Агент, исполняющий /handoff, удаляет протухшие (>7 дней)
  handoff-файлы при записи нового; хук по протухшим молчит, ничего не удаляет
  (возражение о «скилл не исполняемый» закрыто: инструкции скилла исполняет
  агент с shell-доступом). Отклонено: cleanup-скрипт (YAGNI, .scratch
  disposable), авто-чистка хуком (сюрприз в shipped-коде).
- **Q7. Поставка?** Feature-коммит: скилл + deploy.json mapping + хук/тесты +
  inventory-строка (`gitmark inventory` сканирует и skills/ — утверждённое
  challenger'ом «только .zcode/» опровергнуто, gitmark.py:804-811); хук
  доезжает существующим mapping hooks → .zcode/hooks; вендор — релизным
  циклом (тег → пин → self-update).
- **Q8. Граница с memory/report?** Трёхсторонняя: репо-факты → репо; состояние
  задачи → handoff; переживающие задачу факты → memory в момент handoff
  (серая зона закрыта — поправка принята). Promote handoff в docs/ как report
  — только вручную через kb-curate (вне тикета); оговорка онтологии (таблица
  называет handoff среди report-примеров) — словесная, kinetic-слой
  (ontology.md:156-160) авторитетен, правки онтологии нет.
- **Q9. Приёмка передачи?** Живая пара сессий (headless `zcode.cjs -p` падает
  в `Model creation failed` — прецедент 03); хук-часть покрывается pytest;
  honest degradation зафиксирована в тикете.
- **Q10. Кто запускает?** Только оператор; забытый/аварийный handoff — known
  limitation, fallback: транскрипт сессии через `#sess_*`/ReadSessionContext
  (канал не единственный). Отклонено: auto-handoff (события конца сессии в
  zcode нет).

**Constraints:** `stop-before-commit` (дефолт); поверхность хука — только
маркер + анонс, один emit; авто-записи handoff нет; тикет 10 (hygiene) не
расширяется чисткой .scratch; онтология не правится.

**Решения прогона (2026-10-03).** Скилл — 7 шагов: привязка к корню репо
(`git rev-parse --show-toplevel`, как у init), session id из маркера хука
(timestamp-фолбэк = честная деградация Q4), санитизация id для имени файла
(только `[A-Za-z0-9._-]`), шаблон From/Task/Done/Decisions/Open/Next/Artifacts,
evidence-правило (ссылка, не дублирование), memory-правило (адресат назван —
zcode auto-memory; нет memory — сказать в отчёте), чистка >7 дней при записи
(`-mmin +10080`). Хук: маркер из `ZCODE_SESSION_ID` с формат-гейтом
`^sess_[A-Za-z0-9._-]{1,128}$` (грязное значение не пишется вовсе — маркер
питает имя файла, инъекция `../` закрыта и у источника, и в скилле); анонс
новейшего свежего (<7 дней по mtime) handoff с ReadSessionContext-подсказкой
(id из From-строки, `\r` срезается; не распознан — деградация без подсказки);
части (индекс + handoff) склеиваются в ровно один JSON; хук никогда не
удаляет и не блокирует. TTL хука `<` (не `<=`): ровно на 7-м дне файл
принадлежит чистке скилла, не анонсу. Гейт шага 6: reviewer
qwen3.6-35b-a3b$high → confirmer GLM-5.3-Flash$high; 15 сырых находок →
9 verified закрыто / 6 unconfirmed отчитано оператору (опровергнуты с
evidence: «find -delete GNU-only», «printf падает при неудачном mkdir»,
«--rebuild extra игнорирует rebuild», «mtime-гонка», «strategy-поле в From»,
«нужен `--` в find»).

