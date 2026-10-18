# Шаг 3 grilling описывает запись решения без id — контракт challenger.workflow.ts требует

**Наблюдаемое поведение.** Скилл grilling, шаг 3 («Resolve autonomously»),
предписывает записывать решение как
`{question, choice, rationale, evidence, reversible}` — поля `id` в
перечне нет. challenger.workflow.ts принимает decisions в формате
Decision с обязательным `id` (короткий идентификатор, из него строится
имя субагента `challenger-${d.id}`); вызов по перечню шага 3 падает на
раздаче имён: «Subagent name "challenger-undefined" is used twice»
(живой кейс: dwfrun-62a83e74, 2026-10-18 — семь решений без id, ран
умер до первого субагента). Падение дешёвое (модели не тратятся), но
каждый следующий грилл по тексту скилла наступает на те же грабли.

**Источник.** Первый запуск грилла плана onto-doc-abort-redact,
2026-10-18; args собирались дословно по шагу 3 SKILL.md.

**Почему отложено.** Правка шага 3 skills/grilling/SKILL.md — проза
скилла, вне скоупа плана onto-doc-abort-redact (его мораторий держит
только onto-doc.workflow.ts, матрицу и ишью 03/05). Кандидат на триаж:
добавить `id` в перечень шага 3 (одна строка: «каждому решению —
короткий id, d1…dN — контракт challenger.workflow.ts») — вендорная
копия доедет self-update'ом.

**Статус.** Закрыт — отгружен v0.5.66 (2026-10-19): дев 56414ae, main
273792b, релиз 370902a + тег, self-update (вендор=исходник, deploy-check
exit=0). Шаг 3 skills/grilling/SKILL.md несёт id (короткий уникальный
d1…dN), challenger.workflow.ts громко валидирует до раздачи имён — канон
(/^d\d+$/), undefined/null args громкий abort, перечень всех битых
позиций, Array.from-плотнение дыр; матрица 12 кейсов + behavioral-проба
args-контракта (строковая ветка, перечень в abort-тексте, sparse) в
tests/test_challenger_validation.py. Гейт шипа 3 раунда: r1 17v/2 опр.
(dwfrun-c31a3629/5338e42d), r2 17v/3 опр. (dwfrun-945a6d97/66d28c1d),
r3 12v/4 опр. (dwfrun-9dbfc247/70a2e2a0) — все verified адресованы
(7cac7c7, 1f94c61+ddf2758, 30ad250), чистого нет, кап-стоп: оператор
«хвосты в ишью» (ишью 12–13). Проба контракта (Done 7) dwfrun-50eeca6d ok.
