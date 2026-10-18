# Битый построчный якорь grilling:36-38 (правило переехало на grilling:151)

**Наблюдаемое поведение.** Мёртвая ссылка «grilling:36-38 — evidence
or escalate, no third option» живёт в трёх носителях:
skills/ship/SKILL.md:50–51 (секция провенанс-проверки),
.zcode/skills/ship/SKILL.md:50 (вендор — доедет self-update) и
docs/plans/flow-continuity.md:46 (в пятёрке ишью 06 не назван).
Правило «Evidence or escalate» лежит на строке 151
skills/grilling/SKILL.md (раздел Invariants), на 36–38 — хвост свипа
открытых ишью. Сдвиг от правок flow-semantics/03; бит уже в main
(fdf73dc); структурный lint битые прозаические якоря не ловит.

**Источник.** Гейт-ран /ship gate-loop-cap r4 (review dwfrun-69a5b1c1,
confirm dwfrun-42d99679, 2026-10-18), находка low, verified
конфирмером (репродукция sed + grep в worktree и в main); третий
носитель и повод фикса уточнены гейтом r5 (review dwfrun-549dbb7f,
confirm dwfrun-8533eca0). Вне границ плана gate-loop-cap: его
мораторий держит правки ship SKILL в шаге 6 и секции стоп-поинтов,
ссылки живут в других секциях и файлах.

**Почему отложено.** Косметика ссылок, поведение не задето; чинить
правкой носителей — skills/ship/SKILL.md:50–51 и
docs/plans/flow-continuity.md:46 (правка grilling SKILL якорь не
чинит, а сдвигает цель), одним рейсом с ишью 06, отдельным срезом не
разворачивать. Вендорная копия правится только self-update.
