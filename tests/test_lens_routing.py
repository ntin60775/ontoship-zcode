"""Contract of the gate-reviewer lens routing (gate-followups-2/07): the
roster of narrow lenses is extracted verbatim from the shipped workflow and
pinned against representative paths of this repository — every changed file
must land under at least one relevant lens (executable → logic, .md → docs,
.sh → shell+concurrency), no lens may cover everything, and routing must
depend only on the path (the map is built from numstat/status, the script
never sees file content). The predicates are plain JS on purpose: the slice
runs under node, no TS stripping. The per-file reviewer topology is gone —
the source must not carry it back."""
import json
import re
import subprocess
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
WORKFLOW = REPO / "skills" / "ship" / "reviewer.workflow.ts"

CASES = [
    "skills/init/SKILL.md",
    "README.md",
    "docs/plans/gate-followups-2/07-lens-reviewer-topology.md",
    "tests/test_diff_map.py",
    "tests/diff_map.mjs",
    "scripts/hygiene.sh",
    "hooks/session-start.sh",
    "skills/ship/reviewer.workflow.ts",
    "skills/kb-search/gitmark.py",
    "package.json",
]


def lens_literal() -> str:
    """The LENSES array literal from the shipped workflow, markers and TS
    annotation stripped — ready to paste into a node driver."""
    text = WORKFLOW.read_text(encoding="utf-8")
    m = re.search(r"// BEGIN LENSES.*?\n(.*?)// END LENSES", text, re.S)
    assert m, "LENSES block lost its markers in skills/ship/reviewer.workflow.ts"
    lit = re.search(r"=\s*(\[.*\]);", m.group(1), re.S)
    assert lit, "LENSES array literal not found inside the marked block"
    return lit.group(1)


def routing_for(paths: list[str]) -> dict:
    driver = (
        f"const LENSES = {lens_literal()};\n"
        f"const CASES = {json.dumps(paths)};\n"
        "const out = {};\n"
        "for (const p of CASES) out[p] = LENSES.filter((l) => l.appliesTo(p)).map((l) => l.id);\n"
        "console.log(JSON.stringify(out));\n"
    )
    with tempfile.NamedTemporaryFile("w", suffix=".mjs", delete=False) as fh:
        fh.write(driver)
        name = fh.name
    r = subprocess.run(["node", name], capture_output=True, text=True, timeout=60)
    Path(name).unlink()
    assert r.returncode == 0, f"node упал на срезе LENSES:\n{r.stderr}"
    return json.loads(r.stdout)


def test_no_per_file_reviewer_mapping_left():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "reviewer-f$" not in text, "per-file reviewer naming came back (file→personal reviewer axis)"
    assert "по одному ревьюеру на файл" not in text
    assert "Узкие линзы ревьюют свой материал параллельно" in text
    assert "BEGIN LENSES" in text


def test_roster_is_narrow_and_documented():
    literal = lens_literal()
    ids = re.findall(r'id: "([\w-]+)"', literal)
    assert ids == ["logic", "security", "shell", "concurrency", "tests", "docs"], (
        f"ростер линз дрейфует без переназначения матрицы: {ids}"
    )
    assert literal.count("focus:") == len(ids)
    # каждый вопрос — конкретный, не «найди баги»
    for focus in re.findall(r'focus: "([^"]+)"', literal):
        assert len(focus) > 60, f"вопрос линзы слишком общий: {focus[:40]}…"


def test_routing_covers_every_file_and_is_narrow():
    out = routing_for(CASES)
    for p, lenses in out.items():
        assert lenses, f"файл вне любой линзы — молчаливая дыра покрытия: {p}"
    assert out["skills/init/SKILL.md"] == ["docs"]
    assert out["README.md"] == ["docs"]
    assert out["tests/test_diff_map.py"] == ["logic", "tests"]
    assert out["scripts/hygiene.sh"] == ["logic", "security", "shell", "concurrency"]
    assert out["hooks/session-start.sh"] == out["scripts/hygiene.sh"]
    assert out["skills/ship/reviewer.workflow.ts"] == ["logic", "security"]
    # docs-линза не расползается на код, security — на тесты с фейковыми секретами
    assert "docs" not in out["skills/kb-search/gitmark.py"]
    assert "security" not in out["tests/diff_map.mjs"]


def test_routing_depends_only_on_path():
    # два прогона — один результат: маршрутизация не читает содержимое
    assert routing_for(CASES) == routing_for(CASES)
    # расширение решает, не каталог: .md в tests/ — docs и tests, не logic
    out = routing_for(["tests/README.md"])
    assert out["tests/README.md"] == ["tests", "docs"]
