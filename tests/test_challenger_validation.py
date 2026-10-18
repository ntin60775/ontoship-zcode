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
    # a chain of duplicates: every extra occurrence named, not just the first
    ([{"id": "d1"}, {"id": "d1"}, {"id": "d1"}],
     ['#2: id "d1" дублирует #1', '#3: id "d1" дублирует #1']),
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
        r = subprocess.run(["node", str(driver_path)], capture_output=True,
                           text=True, encoding="utf-8")
    assert r.returncode == 0, f"node упал на срезе валидатора:\n{r.stderr}"
    return json.loads(r.stdout)


# The TS annotations the ARGS CONTRACT section legitimately carries — same
# named-stripping convention as STRIP above.
ARGS_STRIP = [
    (": Decision[]", ""),
    (" as Decision[]", ""),
    (": unknown", ""),
]


def args_contract_source() -> str:
    """The parse+validation section of the shipped workflow between the ARGS
    CONTRACT markers — the wiring probe runs it as-is under node with only
    the TS annotations stripped by name (same named-failure convention as
    validator_source)."""
    text = WORKFLOW.read_text(encoding="utf-8")
    m = re.search(r"// BEGIN ARGS CONTRACT.*?\n(.*?)// END ARGS CONTRACT",
                  text, re.S)
    assert m, "ARGS CONTRACT block lost its markers in challenger.workflow.ts"
    src = m.group(1)
    for literal, replacement in ARGS_STRIP:
        assert literal in src, (
            f"аннотация {literal!r} не найдена в секции args-контракта — "
            "дрейф формата; обнови ARGS_STRIP явно")
        src = src.replace(literal, replacement)
    leftovers = re.search(
        r":\s*(Decision|string|number|boolean|unknown)\b|\bas\s+[A-Z]", src)
    assert not leftovers, (
        f"новая TS-аннотация ({leftovers.group(0)!r}) в секции "
        "args-контракта — драйвер упал бы сырым SyntaxError; "
        "добавь литерал в ARGS_STRIP")
    return src


def run_args_contract(decisions_literal: str) -> tuple:
    driver = (
        "const args = { decisions: " + decisions_literal + " };\n"
        + validator_source() + "\n"
        + args_contract_source()
        + '\nconsole.log("PASSED");\n'
    )
    with tempfile.TemporaryDirectory() as td:
        driver_path = Path(td) / "driver.mjs"
        driver_path.write_text(driver, encoding="utf-8")
        r = subprocess.run(["node", str(driver_path)], capture_output=True,
                           text=True, encoding="utf-8")
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def test_args_contract_wiring():
    """Behavioral probe of the call site: the validation result is bound to
    the abort, so a dead-condition mutant reds here instead of letting the
    dwfrun-62a83e74 regression (a broken draft reaches subagent naming)
    survive. Also pins the loud missing/null class — the undefined case
    slipped through as a benign no-op before gate r1, and gate r2 found no
    test covering it."""
    rc, out = run_args_contract('[{"id": "d1"}, {"id": "d1"}]')
    assert rc != 0 and "не прошли валидацию id" in out, out
    rc, out = run_args_contract("null")
    assert rc != 0 and "не строка и не массив" in out, out
    rc, out = run_args_contract("undefined")
    assert rc != 0 and "не строка и не массив" in out, out
    rc, out = run_args_contract("[]")
    assert rc == 0 and "PASSED" in out, out
    rc, out = run_args_contract('[{"id": "d1"}]')
    assert rc == 0 and "PASSED" in out, out


def pin_index(text: str, literal: str, what: str) -> int:
    """str.index with a named failure: a renamed pin reports which anchor
    was lost instead of a bare ValueError (the file's own convention)."""
    try:
        return text.index(literal)
    except ValueError:
        raise AssertionError(
            f"потерян якорь {what} ({literal!r}) в challenger.workflow.ts")


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
    """Structural pins of the call site: the marker blocks exist, validation
    is called between the parse abort and the first subagent name, and the
    abort names the contract. The behavioral binding (a broken draft actually
    aborts) is test_args_contract_wiring's probe — this test only pins the
    anchors by name, so a rename reports the lost anchor."""
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "// BEGIN DECISION VALIDATION" in text
    assert "// END DECISION VALIDATION" in text
    assert "// BEGIN ARGS CONTRACT" in text
    assert "// END ARGS CONTRACT" in text
    call = pin_index(text, "validateDecisions(decisions)", "вызов валидатора")
    parse_abort = pin_index(text, "if (unparsable)", "parse abort")
    naming = pin_index(text, "challenger-${d.id}", "раздача имён субагентов")
    assert parse_abort < call, "validation must follow the parse abort"
    assert call < naming, "validation must precede subagent naming"
    assert "не прошли валидацию id" in text
