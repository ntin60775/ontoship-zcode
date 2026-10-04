"""Tests for scripts/hygiene.sh (ticket 10): the nightly KB maintenance
launcher — lint --strict + index + map, quiet on success, outcome sunk into
.gitmark/hygiene.log whose last line is machine-readable
(HYGIENE <iso-date> lint=<rc> index=<rc> map=<rc>), lint failure carries the
lint output. Exercised end-to-end (subprocess, bash) against the real engine
in a fake KB project, the same way the hook tests drive the hook."""
import os
import subprocess
from pathlib import Path

from test_session_start_hook import build_index, make_kb_project

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "scripts" / "hygiene.sh"


def make_strict_clean_kb(tmp_path: Path) -> Path:
    """A fixture KB that passes `lint --strict`: the vendored engine makes I7
    expect the command registry — create the marker skeleton and let
    `gitmark inventory` fill it (the same thing the init skill does)."""
    proj = make_kb_project(tmp_path)
    build_index(proj)
    ref = proj / "docs" / "reference"
    ref.mkdir()
    (ref / "commands.md").write_text(
        "---\nnode_type: reference\ntitle: Command registry\n"
        "service: _platform\nstatus: active\nupdated: 2026-10-04\n---\n\n"
        "# Commands\n\n"
        "<!-- BEGIN inventory:commands -->\n<!-- END inventory:commands -->\n\n"
        "<!-- BEGIN inventory:skills -->\n<!-- END inventory:skills -->\n",
        encoding="utf-8")
    subprocess.run(
        ["python3", str(proj / ".zcode" / "skills" / "kb-search" / "gitmark.py"),
         "inventory"], cwd=proj, capture_output=True, text=True, check=True)
    return proj


def run_script(proj: Path) -> subprocess.CompletedProcess:
    """env built explicitly, like run_hook does: a foreign ZCODE_PROJECT_DIR
    or CLAUDE_PROJECT_DIR from the pytest environment would silently redirect
    the script to another project (gate 10 — reproduced with a side-effect
    write into a foreign KB)."""
    env = {k: v for k, v in os.environ.items()
           if k not in ("ZCODE_PROJECT_DIR", "CLAUDE_PROJECT_DIR")}
    env["ZCODE_PROJECT_DIR"] = str(proj)
    return subprocess.run(["bash", str(SCRIPT)], cwd=proj,
                          capture_output=True, text=True, timeout=120, env=env)


def last_line(proj: Path) -> str:
    log = proj / ".gitmark" / "hygiene.log"
    lines = log.read_text(encoding="utf-8").strip().splitlines()
    # A regression that leaves the log empty must fail with the reason named,
    # not with IndexError (gate 10).
    assert lines, f"hygiene.log пуст или не записан: {log}"
    return lines[-1]


def hygiene_lines(proj: Path) -> list[str]:
    """Machine-readable records only — the log also carries a header and,
    on lint failure, the lint output (gate 10: substring checks over the
    whole log are fragile)."""
    log = proj / ".gitmark" / "hygiene.log"
    text = log.read_text(encoding="utf-8")
    return [line for line in text.splitlines() if line.startswith("HYGIENE ")]


def test_clean_project_green_and_log_machine_shaped(tmp_path: Path):
    proj = make_strict_clean_kb(tmp_path)
    p = run_script(proj)
    assert p.returncode == 0
    assert p.stdout == ""  # quiet: nothing on stdout on success
    assert last_line(proj).split(" ", 2)[0] == "HYGIENE"
    assert " lint=0 index=0 map=0" in last_line(proj)


def write_bad_md(proj: Path) -> None:
    """A doc that makes `lint --strict` fail for its own sake (I4 broken
    link — an ERR), not by fixture accident."""
    (proj / "docs" / "bad.md").write_text(
        "---\nnode_type: gotcha\ntitle: bad\nservice: _platform\n"
        "status: active\nupdated: 2026-10-04\nlinks:\n"
        "  relates_to: [nonexistent.md]\n---\n\npoint nowhere.\n",
        encoding="utf-8")


def test_broken_md_fails_lint_and_sinks_output(tmp_path: Path):
    proj = make_strict_clean_kb(tmp_path)
    write_bad_md(proj)
    p = run_script(proj)
    assert p.returncode == 1
    text = (proj / ".gitmark" / "hygiene.log").read_text(encoding="utf-8")
    assert " lint=1 " in last_line(proj)
    assert "--- lint --strict output ---" in text  # the ERRs ride along
    assert "ERR" in text


def test_not_a_kb_project_is_silent_and_writes_no_log(tmp_path: Path):
    proj = tmp_path / "empty"
    proj.mkdir()
    p = run_script(proj)
    assert p.returncode == 0
    assert p.stdout == ""
    assert not (proj / ".gitmark" / "hygiene.log").exists()


def test_log_rewrite_leaves_only_the_last_run(tmp_path: Path):
    """The hook reports the LAST nightly run; the fix loop (repair, re-run)
    closes the complaint naturally, so the log is rewritten, not appended."""
    proj = make_strict_clean_kb(tmp_path)
    write_bad_md(proj)
    assert run_script(proj).returncode == 1
    (proj / "docs" / "bad.md").unlink()
    assert run_script(proj).returncode == 0
    records = hygiene_lines(proj)
    assert len(records) == 1, f"должна остаться одна запись прогона, а не: {records}"
    assert " lint=0 " in records[0]
