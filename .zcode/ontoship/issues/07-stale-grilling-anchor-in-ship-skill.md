# Битый построчный якорь grilling:36-38 в ship SKILL.md (правило переехало на :151)

**Наблюдаемое поведение.** skills/ship/SKILL.md:49–50 (секция
провенанс-проверки) ссылается на «grilling:36-38 — evidence or
escalate, no third option», но правило «Evidence or escalate» лежит на
строке 151 skills/grilling/SKILL.md (раздел Invariants), а на 36–38 —
хвост свипа открытых ишью. Сдвиг от правок flow-semantics/03; бит уже
в main (fdf73dc) и синхронно в вендоре .zcode/skills/grilling/SKILL.md
— структурный lint битые прозаические якоря не ловит.

**Источник.** Гейт-ран /ship gate-loop-cap r4 (review dwfrun-69a5b1c1,
confirm dwfrun-42d99679, 2026-10-18), находка low, verified
конфирмером (репродукция sed + grep в worktree и в main). Вне границ
плана gate-loop-cap: его мораторий держит правки ship SKILL в шаге 6
и секции стоп-поинтов, якорь живёт в другой секции.

**Почему отложено.** Косметика ссылки, поведение не задето; тот же
класс, что ишью 06 (устаревшие якоря вне хунков) — чинить одним
рейсом с ним или при ближайшей правке grilling SKILL, отдельным
срезом не разворачивать.
