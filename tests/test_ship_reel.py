"""Contract of the ship-side behavior reel (behavior-reel/04): the
stop-before-commit payload carries, per Reel example, the pair
«обещано → фактически» — «обещано» is the example's «Наблюдаемый выход»
verbatim, «фактически» is the output a live E2E run of the example's «Вход»
actually printed; the executor's self-report «совпало» is forbidden in any
form; a discrepancy between the sides is closed only by the operator; a
ticket without a `## Reel` section carries «Reel: отсутствует». The
reviewer's tests lens owes the same axis from the other end: tests are
checked against the ticket's Reel — every example needs a live case
reproducing the Вход and asserting the promised «Наблюдаемый выход».
These are text pins over the skill prose and the lens roster — the
discipline lives at those levels, not in code. Pins that claim a location
hold inside it (convention of test_run_model_column): the stop-point pins
live in the stop-before-commit bullet, the E2E anchor in step 8, the lens
duty inside the tests-lens object — a stray mention elsewhere in the file
must not fake the duty. Mutation probes (each must turn its test red):
  - drop «обещано → фактически» or «Reel: отсутствует» from the
    stop-before-commit bullet;
  - drop the «совпало» ban or the operator-only closure;
  - move the Reel rule out of the stop-before-commit bullet (e.g. into
    step 6 or the section intro);
  - drop the Reel duty from the tests-lens focus;
  - drop the step 8 anchor (prod E2E no longer runs the Reel inputs)."""
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
WORKFLOW = REPO / "skills" / "ship" / "reviewer.workflow.ts"


def norm(path: Path) -> str:
    return " ".join(path.read_text("utf-8").split())


def skill() -> str:
    return norm(REPO / "skills" / "ship" / "SKILL.md")


def stop_point() -> str:
    """The stop-before-commit bullet, whitespace-normalized, bounded by the
    next stop-point header: the Reel rule lives in this bullet, so a pin
    must hold there — not anywhere in the skill. The window anchors on the
    section header first: «`stop-after-mr`» occurs earlier in the prose
    (step 7), so a bare first-index slice would come out empty."""
    text = skill()
    head = text.index("## Stop-points and confirmations")
    start = text.index("`stop-before-commit`", head)
    end = text.index("`stop-after-mr`", start)
    return text[start:end]


def step8() -> str:
    """Step 8 of the ship skill, whitespace-normalized, bounded by the next
    step header: the prod-E2E anchor for Reel inputs lives in step 8."""
    text = skill()
    return text[text.index("8. **Prod checks**"):text.index("9. **Ship**")]


def lens_object() -> str:
    """The tests-lens object of the reviewer roster, verbatim from its id to
    the object's closing brace — a Reel mention in another lens, in a
    comment, or in the header prose cannot stand in for the duty."""
    text = WORKFLOW.read_text("utf-8")
    m = re.search(r'\{\s*id: "tests",.*?\n  \},', text, re.S)
    assert m, "объект тестов-линзы не найден в ростере reviewer.workflow.ts"
    return m.group(0)


def test_stop_point_carries_promised_vs_actual_pairs():
    bullet = stop_point()
    assert "«обещано → фактически»" in bullet, (
        "форма пары «обещано → фактически» потеряна из стоп-поинта")
    assert "«Наблюдаемый выход» verbatim" in bullet, (
        "сторона «обещано» не определена как дословный Наблюдаемый выход примера")
    assert "live E2E run of the example's «Вход»" in bullet, (
        "сторона «фактически» не привязана к живому прогону Входа примера")


def test_self_report_is_banned_and_operator_closes():
    bullet = stop_point()
    assert re.search(r"«совпало».{0,140}?is forbidden", bullet), (
        "запрет самоотчёта «совпало» потерян из стоп-поинта")
    assert "closed only by the operator" in bullet, (
        "закрытие расхождения только оператором не закреплено")
    assert "fix the code, fix the Reel, or accept" in bullet, (
        "три исхода расхождения (чинить код/ленту/принять) не названы")


def test_no_reel_branch_is_named():
    bullet = stop_point()
    assert "«Reel: отсутствует»" in bullet, (
        "ветка «Reel: отсутствует» для тикета без ленты потеряна")


def test_step8_runs_reel_inputs_against_prod_contour():
    step = step8()
    assert "«Вход»" in step, (
        "шаг 8 не прогоняет Входы примеров ленты в прод-контуре")
    assert "«обещано → фактически»" in step, (
        "шаг 8 не сводит наблюдённое обратно в форму пары стоп-поинта")


def test_tests_lens_owes_the_reel_crosscheck():
    lens = lens_object()
    assert "сверка с Reel" in lens, (
        "тесты-линза не сверяет тесты с Reel тикета")
    assert "«Цель → Вход → Наблюдаемый выход»" in lens, (
        "линза не называет тройку примера ленты")
    assert "пример ленты без кейса — дыра покрытия" in lens, (
        "пример ленты без живого кейса не назван дырой покрытия")
