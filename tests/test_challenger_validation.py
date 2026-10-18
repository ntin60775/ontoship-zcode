"""Contract of the challenger's decision validation (grilling-contracts,
ишью 09): the validator is extracted verbatim from the shipped workflow
between markers and run under node — a missing, empty, non-canonical or
duplicate id and a non-object decision are each named with their position
(every broken position, not just the first), a valid draft passes empty,
an empty array passes empty (nothing to break). The id must be canonical
d1…dN (/^d\\d+$/, the step-3 contract): spaces, case drift and control
characters would otherwise flow into subagent names and abort text as-is.
The call site is pinned by anchor: validation must run after the parse
abort and before the first agent() name is built — removing the call or
reordering it reds this probe here, not in a live grill (the failure being
pinned: dwfrun-62a83e74 died on a host name collision, with no field
validation in the file at all)."""
import json
import re
import subprocess
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
WORKFLOW = REPO / "skills" / "grilling" / "challenger.workflow.ts"

# The three TS annotations the marker block legitimately carries — replaced
# by name below (literal → JS replacement); a renamed one fails with its
# name, a new one fails the annotation-sweep probe.
STRIP = [
    (": Decision[]", ""),
    (": string[] = []", " = []"),
    ("new Map<string, number>()", "new Map()"),
]

CANON = "#1: id не каноничен — ожидается d1…dN (буква d и цифры)"

CASES = [
    # (decisions, expected broken list — every broken position, in order)
    ([{"id": "d1", "question": "q", "choice": "c",
       "rationale": "r", "evidence": "e"}], []),
    ([{"id": "d1"}, {"id": "d2"}], []),
    ([], []),
    ([{"question": "q"}], ["#1: id отсутствует или пуст"]),
    ([{"id": ""}, {"id": 7}],
     ["#1: id отсутствует или пуст", "#2: id отсутствует или пуст"]),
    (["d1", None, ["x"]],
     ["#1: решение — не объект", "#2: решение — не объект",
      "#3: решение — не объект"]),
    ([{"id": "d1 "}], [CANON]),
    ([{"id": "D1"}], [CANON]),
    ([{"id": "   "}], [CANON]),
    ([{"id": "d1\nERR: гриллинг пройден"}], [CANON]),
    # ≥2 broken positions of different kinds: pins the accumulation contract
    # (an early-exit mutant that names only the first one reds here).
    ([{"question": "q"}, {"id": "d1"}, {"id": "d1"}, {"id": "d2"}],
     ["#1: id отсутствует или пуст", '#3: id "d1" дублирует #2']),
]


def validator_source() -> str:
    """The validator function from the shipped workflow, markers stripped and
    the known TS annotations removed by name: a renamed annotation fails
    here with its name, and any annotation outside STRIP fails the sweep at
    the end — внятная причина вместо сырого node-крэша (прецедент
    lens_literal, test_lens_routing)."""
    text = WORKFLOW.read_text(encoding="utf-8")
    m = re.search(
        r"// BEGIN DECISION VALIDATION.*?\n(.*?)// END DECISION VALIDATION",
        text, re.S)
    assert m, "DECISION VALIDATION block lost its markers in challenger.workflow.ts"
    src = m.group(1)
    for literal, replacement in STRIP:
        assert literal in src, (
            f"аннотация {literal!r} не найдена в маркерном блоке — дрейф формата; "
            "обнови STRIP явно")
        src = src.replace(literal, replacement)
    leftovers = re.search(r":\s*(Decision|string|number|boolean)\b|new Map<", src)
    assert not leftovers, (
        f"в маркерном блоке новая TS-аннотация ({leftovers.group(0)!r}) — "
        "драйвер упал бы сырым SyntaxError; добавь литерал в STRIP")
    return src


def broken_of(decisions) -> list:
    driver = (
        validator_source()
        + f"\nconst decisions = {json.dumps(decisions, ensure_ascii=False)};\n"
        + "console.log(JSON.stringify(validateDecisions(decisions)));\n"
    )
    with tempfile.TemporaryDirectory() as td:
        driver_path = Path(td) / "driver.mjs"
        driver_path.write_text(driver, encoding="utf-8")
        r = subprocess.run(["node", str(driver_path)],
                           capture_output=True, text=True)
    assert r.returncode == 0, f"node упал на срезе валидатора:\n{r.stderr}"
    return json.loads(r.stdout)


def test_matrix():
    for decisions, expected in CASES:
        assert broken_of(decisions) == expected, f"case: {decisions!r}"


def test_broken_positions_named_verbatim():
    """The abort list names every broken position verbatim, so the caller
    fixes the args in one pass — the live failure named nothing
    («challenger-undefined is used twice» in a foreign layer)."""
    out = broken_of([{"question": "q"}, {"id": "d1"}, {"id": "d1"}])
    assert out == ["#1: id отсутствует или пуст", '#3: id "d1" дублирует #2']


def test_call_site_is_wired():
    """Mutation probe: the validator must be called after the parse abort and
    before the first subagent name is built, and the abort must name the
    contract. Removing the call, reordering it after naming, or deleting the
    marker block reds this file — not a live grill."""
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "// BEGIN DECISION VALIDATION" in text
    assert "// END DECISION VALIDATION" in text
    call = text.index("validateDecisions(decisions)")
    assert text.index("if (unparsable)") < call, \
        "validation must follow the parse abort"
    assert call < text.index("challenger-${d.id}"), \
        "validation must precede subagent naming"
    assert "не прошли валидацию id" in text
