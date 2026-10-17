---
node_type: ticket
title: 'kb-curate: комментарий к lint занижает покрытие — I1–I9 вместо I1–I10'
service: _platform
status: archived
updated: 2026-10-16
links:
  part_of: [README.md]
---

# 03: kb-curate — комментарий «invariants I1–I9» при движке I1–I10

**What to build:** строка `# invariants I1–I9` у команды lint в
skills/kb-curate/SKILL.md («Always at the end») называет реальное покрытие
движка — I1–I10, а не I1–I9; перечень флагов в соседней строке сверяется с
фактическим составом инвариантов движка.

**Blocked by:** —.

Источник: гейт шипа flow-continuity, раунд 2 (review dwfrun-fea04320,
confirm dwfrun-8b0eb476 — verified; pre-existing, вне хунков диффа, потому
маршрутизирован сюда правилом оператора «проблема шипа — тикет в день
находки», 2026-10-15). Факты конфирмера: gitmark.py:699 докстринг
«Проверка инвариантов онтологии I1–I10», :16 help, I10 (индексная цепочка
README) определена :653–695, вызовы I6–I10 (:788–801) безусловны — флага не
требуют; строка :99 kb-curate перечисляет флаги без I6/I7/I8/I9/I10.

## Живая сверка (2026-10-16, до правки; строки сдвинуты после v0.5.59)

```
$ grep -n 'I1–' skills/kb-curate/SKILL.md
96:python3 <kb-search-skill-dir>/gitmark.py lint     # invariants I1–I9
```

```
gitmark.py:789  def cmd_lint(root: Path, paths: list | None = None) -> dict:
gitmark.py:790      """Проверка инвариантов онтологии I1–I10. Возвращает {errors, warnings, checked}."""
gitmark.py:1336     lp = sub.add_parser("lint", help="проверить онтологию (I1–I10)")
```

Фактический состав по коду (`cmd_lint`, :789–922): I1 фронтмиссинг
несущего (ERR), I2 словари node_type/service/status (ERR/WARN), I3 сироты
(WARN), I4 битые ссылки тела и frontmatter (ERR), I5 docs/-папка без README
(WARN), I6 supersedes-цель не deprecated/archived (WARN), I7 рассинхрон
реестра команд с payload (ERR), I8 дрейф модели онтологии проект↔пакет,
I9 схемы карточек (required/values), I10 индексная цепочка README. Текущий
перечень флагов в SKILL.md (:99–100) называет только I1–I5.

## Живая E2E-проба заявленного покрытия (2026-10-16, worktree v фичи 8b2ce66)

Фикстурный KB (tmp: docs/README.md без ссылок на подразделы, d1.md с
`supersedes` на активный документ, без реестра команд), настоящий CLI:

```
ERR I10 docs/README.md — в теле индекса нет ссылки на подраздел docs/reference/
ERR I10 docs/README.md — в теле индекса нет ссылки на подраздел docs/sub/
ERR I7  docs/reference/commands.md — реестр не найден
WARN I6 docs/reference/d1.md — supersedes ../README.md, но он не deprecated/archived
3 ERR · 1 WARN  (4 файла · I10×2 · I6×1 · I7×1)
```

Новоназванные в перечне флаги (I6/I7/I10) срабатывают живьём; I8 —
безусловный вызов cmd_lint:911, негативно закрыт чистым прогоном репо
(123 файла); I9 — тесты test_gitmark.py:512–603, I6 :498–509, I7
:295–305, I10 test_onto_doc_parity.py:59–281.

## Гейт (раунд 1, 2026-10-16)

Review dwfrun-980540e8 (reviewer GLM-5.3-Flash$max, docs-линза, покрытие
1/1): 1 сырая находка. Confirm dwfrun-bbd3df9b (confirmer
GLM-5.3-Flash$high): **1 verified / 0 unconfirmed / 0 unverified** —
словарь `node_type` в SKILL.md:108 не называл `schema` при валидации
типа движком (NODE_TYPES gitmark.py:574–575, SCHEMA_TYPE :587,
LOAD_BEARING :580), строках `schema` в обеих таблицах ontology.md
(docs/ontology.md:45, skills/kb-curate/ontology.md:31) и новом перечне
флагов (:102 → I9, носитель node_type: schema). Пробел предсуществующий
(строка вне хунков), класс тот же «чек-лист SKILL.md ↔ движок» — закрыт
в этом тикете фикс-коммитом 5b8d82e (одно слово `|schema`). По итогам
фикса: сьют 322 passed, lint --strict чист (123 файла).

## Гейт (раунд 2, 2026-10-16)

Review dwfrun-30b60bc6 (docs-линза, 1/1): 2 сырых. Confirm
dwfrun-daa4a896: **2 verified / 0 / 0** — (1) «Pick a node_type» :23
остался на 10 типах при 11 в словаре :108 — фикс r1 дошёл только до
Vocabularies; (2) service :110 «define it in docs/ontology.md» — lint
читает словарь сервисов не оттуда: services_vocab = `_platform` (SERVICES
:578) + имена всех каталогов под docs/ (gitmark.py:830–832), node_types()
(:656–677) берёт из ontology.md только таблицу node_type, перечня
service-значений в ontology.md нет (:4/:59 — примеры). Обе закрыты
фикс-коммитом a8c336e: schema в перечне CREATE с ролью (card schema, I9);
строка service называет фактический источник (имена папок docs/,
`_platform` для кросс-срезового). Конфирмер ранжировал (2) как «кандидат
в тикет, не блокер» — закрыта в прогоне по правилу «fix every verified»
(прецедент r1, тот же класс «чек-лист ↔ движок»: перечень флагов заявляет
vocabulary violations node_type/service/status), решение оператора на
стоп-поинте. По итогам фикса: сьют 322 passed, lint --strict чист
(123 файла).

## Гейт (раунд 3 — кап, 2026-10-16)

Review dwfrun-e32b7c5d (docs-линза, 1/1): 1 сырая. Confirm
dwfrun-6723d4bc: **1 verified / 0 / 0** — строка I7 перечня флагов
(:102) называет только реестр команд, а движковый I7 шире: таблицы
commands **и** skills в docs/reference/commands.md
(inventory_issues :1138–1147), плюс план-реестр inventory:plans в
docs/plans/README.md (_plans_issues :1104–1120, вызов :1158); канон
docs/ontology.md:176–185 называет оба. Находка в строке самого тикета
(недозвучение), не pre-existing. Кап 3 раунда (решение оператора
2026-10-15, тикет queue-3/06 — после миграции 2026-10-16 носит
.zcode/ontoship/issues/04-gate-loop-cap.md) исчерпан: следующий раунд не
открывается
сам — стоп-поинт с историей r1–r3 и решением оператора (continue = ровно
один дополнительный раунд / принять / тикетами).

## Гейт (раунд 4 — финальный по continue, 2026-10-16)

Кап 3 раунда исчерпан на r3 — стоп-поинт принесён, оператор дал
**continue** (+1 раунд). Review dwfrun-7110b802 (docs-линза, 1/1): 1
сырая. Confirm dwfrun-ea740df3: **1 verified / 0 / 0** — зачин файла
(:8–9) обещал приоритет «service vocabulary» из проектной онтологии,
которого в движке нет (services_vocab :829–832 = `_platform` + имена
папок docs/; онтология читается только node_types() :656–677 ради
таблицы node_type и ontology_twin_issues() :1086–1101 ради сравнения
копий); после фикса r2 файл противоречил сам себе (:8–9 ↔ :112–113).
Вред воспроизведён живой пробой: `service: billing` из примера
docs/ontology.md:59 без папки docs/billing → WARN I2 «вне словаря»
(:887–888). Фикс 7d1c493: зачин называет реальный приоритет — `node_type`
vocabulary. Раунд 4 финальный (прецедент queue-3/02 r4): находки
чинятся, раунда 5 нет. Сьют 322 passed, lint --strict чист (123 файла).

**Итог гейта: 4 раунда, 1+2+1+1 = 5 verified / 0 unconfirmed / 0
unverified, все закрыты** (5b8d82e, a8c336e, db25372, 7d1c493). Все
находки — класс «чек-лист SKILL.md ↔ движок»: одна недозвученная строка
(I7) и четыре фантомных/усечённых обещания (schema в словаре, schema в
Pick-перечне, источник service-словаря, приоритет service-словаря) —
движок и онтология всегда были правы, документация отставала.

- [x] Живая сверка: `grep -n 'I1–' skills/kb-curate/SKILL.md` и докстринг
  `cmd_lint` процитированы в тикете до правки.
- [x] Комментарий называет I1–I10; перечень `lint flags` синхронен с
  фактическим составом (что именно флагуется — по коду, не по памяти).
  По итогам гейта скоуп расширен в том же классе «чек-лист ↔ движок»:
  schema в словаре и Pick-перечне, источник service-словаря, приоритет
  онтологии (только node_type), полный состав I7 — 5 verified, все
  закрыты.
- [x] pytest и lint --strict зелёные, лог прочитан (322 passed, 123
  файла; живая E2E-проба I6/I7/I10 в тикете).

Отгружено v0.5.60: фича 8b2ce66 + гейт-фиксы 5b8d82e/a8c336e/db25372/
7d1c493, dev c894fd1, main 00caaaf, релиз dcc8871+тег v0.5.60,
self-update вендора (kb-curate+package байт-в-байт, deploy-check 0), пин
маркетплейса 1b305b5 (validate --fetch пройден; в сообщении пина
кириллическая «о» в «ontоship» — запушено, не переписано).
