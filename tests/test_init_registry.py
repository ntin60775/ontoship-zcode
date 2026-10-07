"""Contract of the /init registry seeding (gate-followups-2/05): a fresh KB
project gets docs/reference/commands.md with both inventory marker pairs, and
`gitmark inventory` fills the tables — `gitmark lint --strict` comes out green,
so I7 «реестр не найден» no longer outlives the install. The init skill is
prose, so its "code" is the text itself: the skeleton is extracted from the
shipped SKILL.md (any fenced block carrying both marker pairs) and applied to
a scratch project, the same way test_hygiene_script consumes it. The case
logic (file exists -> untouched) lives in the prose and is pinned by anchors
here; the create-if-missing dry-run on a live project belongs to the ship run
report, as in test_init_block."""
import re
import subprocess
from pathlib import Path

from test_session_start_hook import make_kb_project

REPO = Path(__file__).resolve().parent.parent
SKILL = REPO / "skills" / "init" / "SKILL.md"
DATE = "2026-10-06"


def skeleton_text(date: str = DATE) -> str:
    """The verbatim registry skeleton shipped in SKILL.md: the fenced block
    carrying both inventory marker pairs, date placeholder substituted."""
    text = SKILL.read_text(encoding="utf-8")
    fences = re.findall(r"```[^\n]*\n(.*?)```", text, re.S)
    for fence in fences:
        if ("<!-- BEGIN inventory:commands -->" in fence
                and "<!-- BEGIN inventory:skills -->" in fence):
            return fence.replace("<today, YYYY-MM-DD>", date)
    raise AssertionError(
        f"no fenced inventory skeleton in skills/init/SKILL.md: fenced blocks "
        f"seen {len(fences)}, ни один не несёт обе пары маркеров "
        "inventory:commands/inventory:skills")


def seed_registry(proj: Path, date: str = DATE) -> None:
    """What the init skill's registry step prescribes: write the skeleton when
    missing, then let the engine fill the tables. An inventory failure is a
    named assertion with the engine's stderr (verified-находка приёмки:
    check=True прятал причину за CalledProcessError до lint-assert)."""
    reg = proj / "docs" / "reference" / "commands.md"
    if reg.exists():
        return
    reg.parent.mkdir(parents=True, exist_ok=True)
    reg.write_text(skeleton_text(date), encoding="utf-8")
    r = subprocess.run(
        ["python3", str(proj / ".zcode" / "skills" / "kb-search" / "gitmark.py"),
         "inventory"], cwd=proj, capture_output=True, text=True)
    assert r.returncode == 0, (
        "gitmark inventory (шаг 4 /init) упал до lint — причина в движке, не в I7: "
        f"exit {r.returncode}, stderr: {r.stderr.strip()[:300]}")


def lint_strict(proj: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["python3", str(proj / ".zcode" / "skills" / "kb-search" / "gitmark.py"),
         "lint", "--strict"], cwd=proj, capture_output=True, text=True)


def test_skeleton_carries_valid_reference_frontmatter():
    sk = skeleton_text()
    for fragment in ("node_type: reference", "title: ", "service: _platform",
                     "status: active", f"updated: {DATE}"):
        assert fragment in sk, f"skeleton lost required frontmatter: {fragment}"


def test_skeleton_marks_created_tables():
    sk = skeleton_text()
    assert re.search(
        r"<!-- BEGIN inventory:commands -->\n<!-- END inventory:commands -->", sk), \
        "commands table markers must wrap an empty body — gitmark inventory fills it"
    assert re.search(
        r"<!-- BEGIN inventory:skills -->\n<!-- END inventory:skills -->", sk), \
        "skills table markers must wrap an empty body — gitmark inventory fills it"


def test_skill_pins_create_if_missing_and_fill():
    text = SKILL.read_text(encoding="utf-8")
    assert "docs/reference/commands.md" in text
    # create-if-missing: an existing registry is never rewritten
    assert "never rewrite it" in text
    # the tables are filled by the engine run, not typed by hand
    assert "gitmark.py inventory" in text


def test_fresh_project_lint_strict_green_after_seed(tmp_path):
    proj = make_kb_project(tmp_path)
    # a payload skill the tables must pick up: without any SKILL.md the
    # filled table would be indistinguishable from an empty one
    skill = proj / ".zcode" / "skills" / "echo"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        "---\nname: echo\ndescription: Echo the arguments back.\n---\n\nSay hi.\n",
        encoding="utf-8")
    seed_registry(proj)
    p = lint_strict(proj)
    assert p.returncode == 0, f"I7 пережил установку:\n{p.stdout}\n{p.stderr}"
    reg = (proj / "docs" / "reference" / "commands.md").read_text(encoding="utf-8")
    assert "| `echo` | Echo the arguments back. |" in reg, \
        "строка скилла не доехала до таблицы — inventory-прогон шага не отработал"


def test_inventory_is_a_fixed_point(tmp_path):
    proj = make_kb_project(tmp_path)
    seed_registry(proj)
    reg = proj / "docs" / "reference" / "commands.md"
    before = reg.read_text(encoding="utf-8")
    # check=True прятал причину за CalledProcessError (verified гейта 05) —
    # тот же именованный ассерт, что в seed_registry
    r = subprocess.run(
        ["python3", str(proj / ".zcode" / "skills" / "kb-search" / "gitmark.py"),
         "inventory"], cwd=proj, capture_output=True, text=True)
    assert r.returncode == 0, (
        f"повторный inventory упал: exit {r.returncode}, stderr: {r.stderr.strip()[:300]}")
    assert reg.read_text(encoding="utf-8") == before, \
        "повторный inventory переписал таблицы — зафиксированная точка потеряна"


def test_seed_registry_skips_existing_file_and_lint_stays_green(tmp_path):
    """Ветка «файл уже есть — ранний выход» (verified-находка приёмки: не
    была покрыта ни разу): повторный вызов ничего не меняет в файле, а
    lint --strict остаётся зелёным — существующий реестр не трогается."""
    proj = make_kb_project(tmp_path)
    seed_registry(proj)
    reg = proj / "docs" / "reference" / "commands.md"
    before = reg.read_text(encoding="utf-8")
    seed_registry(proj)
    assert reg.read_text(encoding="utf-8") == before, \
        "повторный seed_registry переписал существующий реестр — create-if-missing сломан"
    p = lint_strict(proj)
    assert p.returncode == 0, f"I7 покраснел после повторного seed:\n{p.stdout}\n{p.stderr}"
