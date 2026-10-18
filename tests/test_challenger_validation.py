"""Contract of the challenger's decision-id validation (grilling-contracts,
ишью 09): the validator is extracted verbatim from the shipped workflow
between markers and run under node — a missing, empty or non-string id, a
duplicate id and a non-object decision are each named with their position, a
valid draft passes empty, an empty array passes empty (nothing to break).
The call site is pinned by anchor: validation must run after the parse abort
and before the first agent() name is built — removing the call or reordering
it reds this probe here, not in a live grill (the failure being pinned:
dwfrun-62a83e74 died on a host name collision, with no field validation in
the file at all)."""
import json
import re
import subprocess
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
WORKFLOW = REPO / "skills" / "grilling" / "challenger.workflow.ts"

CASES = [
    # (decisions, expected broken list)
    ([{"id": "d1", "question": "q", "choice": "c",
       "rationale": "r", "evidence": "e"}], []),
    ([{"id": "d1"}, {"id": "d2"}], []),
    ([], []),
    ([{"question": "q"}], ["#1: id отсутствует или пуст"]),
    ([{"id": "", "question": "q"}], ["#1: id отсутствует или пуст"]),
    ([{"id": 7, "question": "q"}], ["#1: id отсутствует или пуст"]),
    ([{"id": "d1"}, {"question": "q"}], ["#2: id отсутствует или пуст"]),
    ([{"id": "d1"}, {"id": "d1"}], ['#2: id "d1" дублирует #1']),
    ([{"id": "d1"}, {"id": "d2"}, {"id": "d1"}], ['#3: id "d1" дублирует #1']),
    (["d1"], ["#1: решение — не объект"]),
    ([{"id": "d1"}, None], ["#2: решение — не объект"]),
    ([{"id": "d1"}, ["x"]], ["#2: решение — не объект"]),
]


def validator_source() -> str:
    """The validator function from the shipped workflow, markers and TS
    annotations stripped — ready to paste into a node driver. Любой дрейф
    формата внутри маркерного блока роняет тест здесь с внятной причиной,
    а не невнятным node-крэшем (прецедент lens_literal, test_lens_routing)."""
    text = WORKFLOW.read_text(encoding="utf-8")
    m = re.search(
        r"// BEGIN DECISION VALIDATION.*?\n(.*?)// END DECISION VALIDATION",
        text, re.S)
    assert m, "DECISION VALIDATION block lost its markers in challenger.workflow.ts"
    return (m.group(1)
            .replace(": Decision[]", "")
            .replace(": string[] = []", " = []")
            .replace("new Map<string, number>()", "new Map()"))


def broken_of(decisions) -> list:
    driver = (
        validator_source()
        + f"\nconst decisions = {json.dumps(decisions, ensure_ascii=False)};\n"
        + "console.log(JSON.stringify(validateDecisions(decisions)));\n"
    )
    with tempfile.NamedTemporaryFile("w", suffix=".mjs", delete=False) as fh:
        fh.write(driver)
    r = subprocess.run(["node", fh.name], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


def test_matrix():
    for decisions, expected in CASES:
        assert broken_of(decisions) == expected, f"case: {decisions!r}"


def test_valid_ids_are_reported_verbatim():
    """A passing draft is not enough: the broken positions must be named so
    the caller can fix the args without a second run (the live failure named
    nothing — «challenger-undefined is used twice» in a foreign layer)."""
    out = broken_of([{"id": "d9", "question": "q"}])
    assert out == []


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
