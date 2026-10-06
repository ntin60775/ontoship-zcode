"""Contract of the /init verbatim block (gate-followups-2/01): the block
names commands the way zcode actually resolves them — the skills deploy into
the consumer's .zcode/skills/ and are invoked without a prefix. The omp form
`/ontoship:*` is port drift and must not come back (ut-10 ADR: the short form
is the correct one). The init skill is prose, so its "code" is the text
itself; this pins the shipped artifact. The migration dry-runs (old prefix
block between markers -> replaced, lines outside markers untouched; missing
AGENTS.md -> created with the short form) are exercised in the ship run
report, since the case logic lives in the prose, not in repo code."""
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILL = REPO / "skills" / "init" / "SKILL.md"


def _skill_text() -> str:
    return SKILL.read_text(encoding="utf-8")


def _block() -> str:
    # The skill shows an empty marker pair in its "Scope of the write" prose
    # before the verbatim block, and the fence info string is formatting the
    # skill may change — so the block is any fenced block whose markers wrap
    # non-empty content.
    for fence in re.findall(r"```[^\n]*\n(.*?)```", _skill_text(), re.S):
        m = re.search(
            r"<!-- BEGIN ontoship -->\n(.*?)<!-- END ontoship -->",
            fence, re.S)
        if m and m.group(1).strip():
            return fence
    raise AssertionError(
        "no fenced ontoship block with content in skills/init/SKILL.md")


def test_no_plugin_prefix_anywhere_in_skill():
    assert "/ontoship:" not in _skill_text()


def test_block_names_short_commands():
    block = _block()
    for cmd in ("/kb-search", "/doc", "/ship"):
        assert cmd in block, f"missing short command {cmd}"


def test_block_carries_no_prefix_caveat():
    # The caveat promising plugin-prefixed names is gone: no install form
    # resolves these commands prefixed, so any prefix caveat would promise
    # mechanics that do not exist. The block states the commands plain.
    assert "prefix" not in _block()
