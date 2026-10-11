"""The run-model column of the gate tells the truth (roles-fallback-substrate/
02): the review run launches on the reviewer role's model, the confirm run on
the confirmer's, grilling stays on the challenger; a model-death relaunch goes
exactly once on the fallback role with the loud note; assembled gate args are
preflighted before every submit. These are text pins over the skill prose —
the discipline lives at the calling-skill level, not in the workflow scripts.
Literals are asserted on whitespace-normalized text so line wrapping in the
prose cannot flip a pin. Mutation probes (each must turn its test red,
confirmed live):
  - revert `reviewer` to `confirmer` in the review-run template of
    skills/ship/SKILL.md (the old lying column);
  - restore the old substrate claim «the confirmer role model»;
  - drop the loud-note literal, the exactly-once limit or the args-preflight
    sentence;
  - drop the stub bullet from skills/contour/SKILL.md lesson 10."""
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

NOTE = r"ран #1 на <модель> не тянет\s*—\s*перезапущено на <фолбэк>"


def norm(path: Path) -> str:
    return " ".join(path.read_text("utf-8").split())


def ship() -> str:
    return norm(REPO / "skills" / "ship" / "SKILL.md")


def review_template() -> str:
    """The review-run CreateWorkflow template of ship step 6, extracted by its
    anchor (the workflow path next to the SKILL.md) up to the end of its
    subagent_model clause."""
    m = re.search(
        r"CreateWorkflow\(path=reviewer\.workflow\.ts.*?subagent_model=<\w+\s+role\$level>\)",
        ship(), re.S)
    assert m, "шаблон review-рана потерян из шага 6 ship-скилла"
    return m.group(0)


def test_review_run_runs_on_reviewer_role():
    template = review_template()
    assert re.search(r"subagent_model=<reviewer\s+role\$level>", template), (
        "review-ран не на роли reviewer — колонка модели врёт")
    assert "confirmer" not in template, (
        "в шаблоне review-рана упоминается confirmer — старая ложная колонка")
    text = ship()
    assert re.search(r"confirm on `confirmer`", text), (
        "указание «confirm на confirmer» потеряно")
    confirm = re.search(
        r"CreateWorkflow\(path=confirm\.workflow\.ts.*?subagent_model=<\w+\s+role\$level>\)",
        text, re.S)
    assert confirm, "шаблон confirm-рана потерян из шага 6"
    assert re.search(r"subagent_model=<confirmer\s+role\$level>", confirm.group(0)), (
        "confirm-ран не на роли confirmer")


def test_no_lingering_confirmer_is_the_lense_model_claim():
    text = ship()
    assert "the confirmer role model" not in text, (
        "старое утверждение «модель линз = confirmer» осталось в шаге 6")
    assert "each run's own role model" in text, (
        "формулировка «модель = модель своей роли рана» потеряна")


def test_fallback_relaunch_discipline_pinned_in_ship_and_grilling():
    for skill in ("ship", "grilling"):
        text = norm(REPO / "skills" / skill / "SKILL.md")
        assert "subagent_model=<fallback role$level>" in text, (
            f"{skill}: перезапуск не назначен на роль fallback")
        assert re.search(
            r"relaunched clean exactly once on `subagent_model=<fallback role\$level>`", text), (
            f"{skill}: одиночность перезапуска на fallback не закреплена")
        assert re.search(NOTE, text), (
            f"{skill}: громкая пометка деградации потеряна")
        assert re.search(r"a second\s+model-death", text), (
            f"{skill}: стоп на втором провале не закреплён")
        assert "not a fallback signal" in text, (
            f"{skill}: транзиентные ошибки не отделены от сигнала фолбэка")


def test_grilling_stays_on_challenger():
    text = norm(REPO / "skills" / "grilling" / "SKILL.md")
    assert "subagent_model=<challenger role>" in text, (
        "grilling-ран потерял роль challenger")


def test_args_preflight_pinned_in_ship_and_contour():
    text = ship()
    assert "Preflight the assembled args before every submit" in text, (
        "префлайт собранных args не закреплён в шаге 6")
    assert "dwfrun-5d20732c" in text, "прецедент заглушки не назван в шаге 6"
    assert "stopped immediately and relaunched clean" in text, (
        "правило «мусорный ран остановить и перезапустить» потеряно")
    contour = norm(REPO / "skills" / "contour" / "SKILL.md")
    assert re.search(r"semantically unvalidated.*dwfrun-5d20732c", contour, re.S), (
        "урок о семантической невалидированности ручных args потерян в уроке 10")
