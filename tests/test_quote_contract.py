"""Contract of the code-review axis quote prompt (gate-followups-2/02): the
prompt must not promise mechanics the code lacks. The operator's decision
(2026-10-06, recorded in the ticket): honest fallback wording — a finding
without a quote still travels to the confirm run with the fallback evidence
"цитаты ось не дала — проверяй проблему по месту where"; enforcement (dropping
quote-less findings) was rejected. The workflow file is the shipped artifact
(prompt and collecting code in one), so the test pins the text itself: the
false "no quote = no finding" promise is gone, the prompt names the where
fallback, and the code's fallback behavior is still in place — prompt and
code stay in sync."""
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
WF = REPO / "skills" / "code-review" / "code-review.workflow.ts"

FALLBACK_CODE = "цитаты ось не дала — проверяй проблему по месту where"


def _text() -> str:
    return WF.read_text(encoding="utf-8")


def _file_prompt_body() -> str:
    """The filePrompt function body — the window the quote contract lives in.
    The function closes with a `}` at column 0 (the repo's extraction idiom),
    so the window survives reformatting of the prompt inside."""
    m = re.search(r"function filePrompt\(.*?^}", _text(), re.S | re.M)
    assert m, "filePrompt() not found in code-review.workflow.ts"
    return m.group(0)


def _raw_findings_block() -> str:
    """The collecting code that builds the gate findings — the rawFindings
    flatMap closing with `);` on its own line after the mapping."""
    m = re.search(r"const rawFindings: Finding\[\] = reviews\.flatMap\(.*?^\);", _text(), re.S | re.M)
    assert m, "rawFindings block not found in code-review.workflow.ts"
    return m.group(0)


def test_no_false_drop_promise():
    assert "несостоявшаяся находка" not in _text()
    assert "Цитата обязательна" not in _text()


def test_prompt_names_where_fallback():
    # The filePrompt quote contract asks for a quote always and states what
    # actually happens without one: the confirmer checks the finding by its
    # where. Both ends of the match must sit inside the filePrompt body, so a
    # stray mention elsewhere in the file cannot fake the contract.
    m = re.search(r"Цитату давай всегда.*?по месту where", _file_prompt_body(), re.S)
    assert m, "honest quote contract wording with the where fallback not found in the axis prompt"


def test_code_fallback_unchanged():
    # The no-quote fallback evidence is the code's actual behavior — pin the
    # ternary expression inside the rawFindings collecting block, not the
    # whole file: the phrase in a comment (or anywhere outside the ternary)
    # must not stand in for the behavior.
    block = _raw_findings_block()
    m = re.search(
        r'evidence: f\.quote \? redact\(f\.quote\) : "' + re.escape(FALLBACK_CODE) + '"',
        block)
    assert m, "no-quote fallback ternary (evidence when the axis gave no quote) not found in the rawFindings block"
