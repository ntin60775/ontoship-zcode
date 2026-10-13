"""The run-model column of the gate tells the truth (roles-fallback-substrate/
02): the review run launches on the reviewer role's model, the confirm run on
the confirmer's, grilling stays on the challenger; a model-death relaunch goes
exactly once on the fallback role with the loud note; assembled gate args are
preflighted before every submit; the fail-closed rule (a model missing from
ListModels stops before launch — the fallback never masks a configuration
error) is pinned too. С roles-per-agent/02 сюда входит и мост №2: онто-док —
шаблон с плейсхолдерами {{ROLE_MODEL:<role>}} и запуском только через свежую
инстанциацию с дифф-префлайтом (никогда модель чата/рана). These are text
pins over the skill prose — the
discipline lives at the calling-skill level, not in the workflow scripts.
Literals are asserted on whitespace-normalized text, so line wrapping in the
prose cannot flip a pin; template pins are bounded by their own backtick pair,
so a reflow cannot make the lazy span swallow the neighbouring template; the
confirmer-ban is scoped to the subagent_model assignment, not to any mention.
Pins that claim a location hold inside it: the ship discipline pins live in
step 6 (ship_step6()), the contour pin inside lesson 10 (contour_lesson10()).
Mutation probes (each must turn its test red, confirmed live):
  - revert `reviewer` to `confirmer` in the review-run template of
    skills/ship/SKILL.md (the old lying column);
  - restore the old substrate claim «the confirmer role model»;
  - drop the loud-note literal, the exactly-once limit, the args-preflight
    sentence or a fail-closed sentence;
  - move the fallback block or the preflight sentence out of ship step 6;
  - drop or reorder the stub bullet out of skills/contour/SKILL.md lesson 10."""
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

NOTE = r"ран #1 на <модель> не тянет\s*—\s*перезапущено на <фолбэк>"


def norm(path: Path) -> str:
    return " ".join(path.read_text("utf-8").split())


def ship() -> str:
    return norm(REPO / "skills" / "ship" / "SKILL.md")


def ship_step6() -> str:
    """Step 6 of the ship skill, whitespace-normalized: the ticket places the
    gate disciplines in step 6, so the pins must hold there."""
    text = ship()
    return text[text.index("6. **Independent review**"):text.index("7. **Dev checks**")]


def contour_lesson10() -> str:
    """Lesson 10 of the contour skill, whitespace-normalized, bounded by the
    next lesson header — the stub bullet must stay in the args-preflight
    lesson, not anywhere in the file."""
    text = norm(REPO / "skills" / "contour" / "SKILL.md")
    return text[text.index("## 10. "):text.index("## 11. ")]


def run_template(workflow: str, text: str) -> str:
    """The CreateWorkflow template of `workflow` (reviewer/confirm): from its
    unique path anchor to its own subagent_model close. The first
    role$level>…)`-close after the anchor is always the anchor's own — each
    template carries exactly one such clause — and the `\\s*` before `\\)` keeps a
    reflowed `role$level>\\n)` matched, so the span cannot leak into the
    neighbouring template even when the prose reflows."""
    m = re.search(
        rf"CreateWorkflow\(path={workflow}\.workflow\.ts.*?role\$level>\s*\)`", text, re.S)
    assert m, f"шаблон {workflow}-рана потерян из шага 6 ship-скилла"
    return m.group(0)


def test_review_run_runs_on_reviewer_role():
    template = run_template("reviewer", ship_step6())
    assert re.search(r"subagent_model=<reviewer\s+role\$level>", template), (
        "review-ран не на роли reviewer — колонка модели врёт")
    assert not re.search(r"subagent_model=<confirmer", template), (
        "review-ран назначен на confirmer — старая ложная колонка")
    step6 = ship_step6()
    assert "confirm on `confirmer`" in step6, (
        "указание «confirm на confirmer» потеряно")
    confirm = run_template("confirm", step6)
    assert re.search(r"subagent_model=<confirmer\s+role\$level>", confirm), (
        "confirm-ран не на роли confirmer")


def test_no_lingering_confirmer_is_the_lense_model_claim():
    step6 = ship_step6()
    assert "the confirmer role model" not in step6, (
        "старое утверждение «модель линз = confirmer» осталось в шаге 6")
    assert "each run's own role model" in step6, (
        "формулировка «модель = модель своей роли рана» потеряна")


def test_fallback_relaunch_discipline_pinned_in_ship_and_grilling():
    for where, text in (("ship step 6", ship_step6()),
                        ("grilling", norm(REPO / "skills" / "grilling" / "SKILL.md"))):
        assert "subagent_model=<fallback role$level>" in text, (
            f"{where}: перезапуск не назначен на роль fallback")
        assert re.search(
            r"relaunched clean exactly once on `subagent_model=<fallback role\$level>`", text), (
            f"{where}: одиночность перезапуска на fallback не закреплена")
        assert re.search(NOTE, text), (
            f"{where}: громкая пометка деградации потеряна")
        assert re.search(r"a second\s+model-death", text), (
            f"{where}: стоп на втором провале не закреплён")
        assert "not a fallback signal" in text, (
            f"{where}: транзиентные ошибки не отделены от сигнала фолбэка")
        assert "fail-closed" in text, (
            f"{where}: fail-closed-правило для нерезолвящейся модели потеряно")
        assert "never a configuration error" in text, (
            f"{where}: «фолбэк не маскирует ошибку конфигурации» потеряно")


def test_grilling_stays_on_challenger():
    text = norm(REPO / "skills" / "grilling" / "SKILL.md")
    assert re.search(r"subagent_model=<challenger role(\$level)?>", text), (
        "grilling-ран потерял роль challenger")


def test_onto_doc_rides_the_role_bridge_not_the_chat_model():
    """roles-per-agent/02: онто-док — первый потребитель моста №2. Движок —
    шаблон: плейсхолдеры {{ROLE_MODEL:<role>}} строковыми литералами (форма
    model() запрещена — ломает мок-обёрточные тесты, грилл d6), движок не
    принимает модель рана; скилл запускает ран только через свежую
    инстанциацию с дифф-префлайтом. Уровни ролей — факты реестра, их дом —
    tests/test_roles.py (записи defaults с явными level); здесь контракт —
    назначение ролей и дисциплина запуска. Мутационные пробы (подтверждены
    живьём при отгрузке): смена плейсхолдера surveyor → curator и снятие
    «never rides the chat model» обязаны краснить этот пин."""
    skill = norm(REPO / "skills" / "onto-doc" / "SKILL.md")
    assert "runs on the `surveyor` role" in skill, (
        "surveyor не на своей роли")
    assert "the fan-out curators and the healer on the `curator` role" in skill, (
        "кураторы/healer не на роли curator")
    assert "never rides the chat model" in skill, (
        "полярный якорь «никогда модель чата» потерян")
    assert "uniquely named" in skill and "0 placeholders left in the instance" in skill, (
        "дисциплина свежей инстанциации с дифф-префлайтом не запинена")
    engine = (REPO / "skills" / "onto-doc" / "onto-doc.workflow.ts").read_text(
        encoding="utf-8")
    assert engine.count('model: "{{ROLE_MODEL:curator}}"') == 2, (
        "плейсхолдер curator должен стоять ровно на кураторе fan-out и healer")
    assert engine.count('model: "{{ROLE_MODEL:surveyor}}"') == 1, (
        "плейсхолдер surveyor должен стоять ровно на surveyor")
    assert 'model("' not in engine, "форма model() в движке запрещена"
    assert "subagent_model" not in engine, (
        "движок не принимает модель рана — только плейсхолдеры ролей")


def test_args_preflight_pinned_in_ship_and_contour():
    step6 = ship_step6()
    assert "Preflight the assembled args before every submit" in step6, (
        "префлайт собранных args не закреплён в шаге 6")
    assert "dwfrun-5d20732c" in step6, "прецедент заглушки не назван в шаге 6"
    assert "stopped immediately and relaunched clean" in step6, (
        "правило «мусорный ран остановить и перезапустить» потеряно")
    lesson = contour_lesson10()
    assert "semantically unvalidated" in lesson, (
        "урок о семантической невалидированности ручных args потерян в уроке 10")
    assert "dwfrun-5d20732c" in lesson, (
        "прецедент заглушки потерян в уроке 10 contour")
