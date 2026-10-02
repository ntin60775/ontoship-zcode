"""Tests for hooks/session-start.sh: stale-index notice at session start over
the engine's whole markdown corpus (git ls-files, like gitmark indexes it),
silence when fresh or outside a KB project, quiet --rebuild; plus the session
continuity half (ticket 08): the .session-id marker written from the hook's
own environment, the fresh-handoff announcement with the ReadSessionContext
hint, and the one-emit contract (exactly one JSON on stdout, however much
there is to say). The hook is exercised end-to-end (subprocess, bash) against
the real engine in a fake KB project; mtimes are pinned with os.utime, so no
sleeps."""
import json
import os
import shutil
import subprocess
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
HOOK = REPO / "hooks" / "session-start.sh"
ENGINE = REPO / "skills" / "kb-search" / "gitmark.py"


def make_kb_project(tmp_path: Path, with_engine: bool = True,
                    with_docs: bool = True, with_git: bool = True) -> Path:
    proj = tmp_path / "proj"
    proj.mkdir(parents=True)
    if with_git:
        subprocess.run(["git", "init", "-q"], cwd=proj, check=True)
    # The deployed contract (init skill) ignores .scratch/ — mirror it, so
    # handoff files never count into the freshness corpus.
    (proj / ".gitignore").write_text(".scratch/\n", encoding="utf-8")
    if with_engine:
        d = proj / ".zcode" / "skills" / "kb-search"
        d.mkdir(parents=True)
        shutil.copy(ENGINE, d / "gitmark.py")
    if with_docs:
        (proj / "docs").mkdir()
        (proj / "docs" / "a.md").write_text(
            "---\ntitle: a\n---\n\nOntoShip smoke word.\n", encoding="utf-8")
    return proj


def build_index(proj: Path) -> None:
    subprocess.run(["python3", str(proj / ".zcode" / "skills" / "kb-search" / "gitmark.py"),
                    "index"], cwd=proj, capture_output=True, text=True, check=True)


def run_hook(proj: Path, args: tuple = (),
             session_id: str | None = None) -> subprocess.CompletedProcess:
    """session_id=None runs the hook with no ZCODE_SESSION_ID at all."""
    env = {k: v for k, v in os.environ.items() if k != "ZCODE_SESSION_ID"}
    env["ZCODE_PROJECT_DIR"] = str(proj)
    if session_id is not None:
        env["ZCODE_SESSION_ID"] = session_id
    return subprocess.run(["bash", str(HOOK), *args], cwd=proj,
                          capture_output=True, text=True, timeout=120, env=env)


def ctx_of(p: subprocess.CompletedProcess) -> str | None:
    """None when the hook stayed silent; else the additionalContext string."""
    if not p.stdout.strip():
        return None
    out = json.loads(p.stdout)
    assert out["hookSpecificOutput"]["hookEventName"] == "SessionStart"
    return out["hookSpecificOutput"]["additionalContext"]


def test_not_a_kb_project_is_silent(tmp_path: Path):
    proj = tmp_path / "empty"
    proj.mkdir()
    p = run_hook(proj)
    assert p.returncode == 0
    assert p.stdout == ""


def test_non_git_project_is_silent(tmp_path: Path):
    """md+git is the KB contract: without a git repo the hook stays quiet."""
    proj = make_kb_project(tmp_path, with_git=False)
    p = run_hook(proj)
    assert p.returncode == 0
    assert p.stdout == ""


def test_docs_without_engine_is_silent(tmp_path: Path):
    proj = make_kb_project(tmp_path, with_engine=False)
    p = run_hook(proj)
    assert p.returncode == 0
    assert p.stdout == ""


def test_missing_index_suggests_building(tmp_path: Path):
    proj = make_kb_project(tmp_path)
    p = run_hook(proj)
    assert p.returncode == 0
    ctx = ctx_of(p)
    assert ctx is not None and "gitmark.py index" in ctx


def test_fresh_index_is_silent(tmp_path: Path):
    proj = make_kb_project(tmp_path)
    build_index(proj)
    os.utime(proj / "docs" / "a.md", (0, 0))
    p = run_hook(proj)
    assert p.returncode == 0
    assert p.stdout == ""


def test_stale_docs_get_a_notice(tmp_path: Path):
    proj = make_kb_project(tmp_path)
    build_index(proj)
    os.utime(proj / ".gitmark" / "index.db", (0, 0))
    p = run_hook(proj)
    assert p.returncode == 0
    ctx = ctx_of(p)
    assert ctx is not None and "gitmark.py index" in ctx


def test_stale_markdown_outside_docs_is_noticed(tmp_path: Path):
    """The engine indexes the whole repo corpus; so does the freshness check."""
    proj = make_kb_project(tmp_path)
    build_index(proj)
    os.utime(proj / ".gitmark" / "index.db", (0, 0))
    agents = proj / "AGENTS.md"
    agents.write_text("# x\n", encoding="utf-8")
    assert agents.stat().st_mtime > 0
    p = run_hook(proj)
    assert p.returncode == 0
    ctx = ctx_of(p)
    assert ctx is not None and "gitmark.py index" in ctx


def test_gitignored_markdown_does_not_nag(tmp_path: Path):
    """Ignored files are not in the engine's corpus: editing one must not
    produce a notice the rebuild could never satisfy."""
    proj = make_kb_project(tmp_path)
    (proj / ".gitignore").write_text("docs/private/\n", encoding="utf-8")
    private = proj / "docs" / "private"
    private.mkdir()
    (private / "notes.md").write_text("secret\n", encoding="utf-8")
    build_index(proj)
    os.utime(proj / ".gitmark" / "index.db", (0, 0))
    os.utime(proj / "docs" / "a.md", (0, 0))
    (private / "notes.md").write_text("secret v2\n", encoding="utf-8")
    p = run_hook(proj)
    assert p.returncode == 0
    assert p.stdout == ""


def test_future_mtime_does_not_nag(tmp_path: Path):
    """A rebuild can never get ahead of a future mtime — skip, don't nag."""
    proj = make_kb_project(tmp_path)
    build_index(proj)
    future = time.time() + 86_400
    os.utime(proj / "docs" / "a.md", (future, future))
    p = run_hook(proj)
    assert p.returncode == 0
    assert p.stdout == ""


def test_rebuild_flag_rebuilds_quietly(tmp_path: Path):
    proj = make_kb_project(tmp_path)
    build_index(proj)
    db = proj / ".gitmark" / "index.db"
    md = proj / "docs" / "a.md"
    os.utime(db, (0, 0))
    p = run_hook(proj, args=("--rebuild",))
    assert p.returncode == 0
    assert p.stdout == ""
    assert db.stat().st_mtime >= md.stat().st_mtime


def test_rebuild_flag_on_missing_index_creates_it(tmp_path: Path):
    proj = make_kb_project(tmp_path)
    p = run_hook(proj, args=("--rebuild",))
    assert p.returncode == 0
    assert p.stdout == ""
    assert (proj / ".gitmark" / "index.db").is_file()


def test_rebuild_failure_does_not_block(tmp_path: Path):
    proj = make_kb_project(tmp_path)
    (proj / ".zcode" / "skills" / "kb-search" / "gitmark.py").write_text(
        "import sys; sys.exit(3)\n", encoding="utf-8")
    p = run_hook(proj, args=("--rebuild",))
    assert p.returncode == 0
    ctx = ctx_of(p)
    assert ctx is not None and "не удалась" in ctx


def test_extra_positional_arg_ignored(tmp_path: Path):
    proj = make_kb_project(tmp_path)
    p = run_hook(proj, args=("whatever",))
    assert p.returncode == 0
    assert ctx_of(p) is not None


def write_handoff(proj: Path, name: str, body: str) -> Path:
    scratch = proj / ".scratch"
    scratch.mkdir(exist_ok=True)
    f = scratch / name
    f.write_text(body, encoding="utf-8")
    return f


def test_session_id_marker_written_from_env(tmp_path: Path):
    proj = make_kb_project(tmp_path)
    p = run_hook(proj, session_id="sess_abc-123")
    assert p.returncode == 0
    marker = proj / ".scratch" / ".session-id"
    assert marker.read_text(encoding="utf-8") == "sess_abc-123\n"


def test_session_id_marker_not_written_without_env(tmp_path: Path):
    proj = make_kb_project(tmp_path)
    build_index(proj)
    os.utime(proj / "docs" / "a.md", (0, 0))
    p = run_hook(proj)
    assert p.returncode == 0
    assert p.stdout == ""
    assert not (proj / ".scratch").exists()


def test_session_id_marker_not_written_for_dirty_value(tmp_path: Path):
    """The marker feeds a filename downstream (handoff-<id>.md): a value that
    does not look like a session id is not written at all."""
    proj = make_kb_project(tmp_path)
    p = run_hook(proj, session_id="../evil\nwith newline")
    assert p.returncode == 0
    assert not (proj / ".scratch").exists()


def test_fresh_handoff_is_announced(tmp_path: Path):
    proj = make_kb_project(tmp_path)
    build_index(proj)
    os.utime(proj / "docs" / "a.md", (0, 0))
    write_handoff(proj, "handoff-sess_old.md",
                  "# Handoff\n\nFrom: sess_old (2026-10-03)\n\n## Done\n- x\n")
    p = run_hook(proj)
    assert p.returncode == 0
    ctx = ctx_of(p)
    assert ctx is not None
    assert "handoff-sess_old.md" in ctx
    assert "ReadSessionContext(sessionId=sess_old, strategy=handoff)" in ctx


def test_stale_handoff_is_silent(tmp_path: Path):
    proj = make_kb_project(tmp_path)
    build_index(proj)
    os.utime(proj / "docs" / "a.md", (0, 0))
    f = write_handoff(proj, "handoff-sess_old.md", "From: sess_old\n")
    old = time.time() - 8 * 86_400
    os.utime(f, (old, old))
    p = run_hook(proj)
    assert p.returncode == 0
    assert p.stdout == ""


def test_handoff_from_line_crlf_still_recognized(tmp_path: Path):
    """A handoff file edited on Windows (CRLF) must not lose the hint: \r is
    stripped before the session id is matched."""
    proj = make_kb_project(tmp_path)
    build_index(proj)
    os.utime(proj / "docs" / "a.md", (0, 0))
    write_handoff(proj, "handoff-sess_crlf.md", "From: sess_crlf\r\n")
    p = run_hook(proj)
    assert p.returncode == 0
    ctx = ctx_of(p)
    assert ctx is not None
    assert "ReadSessionContext(sessionId=sess_crlf, strategy=handoff)" in ctx


def test_handoff_without_session_id_degrades(tmp_path: Path):
    proj = make_kb_project(tmp_path)
    build_index(proj)
    os.utime(proj / "docs" / "a.md", (0, 0))
    write_handoff(proj, "handoff-20261003T000000Z.md",
                  "From: unknown (2026-10-03)\n")
    p = run_hook(proj)
    assert p.returncode == 0
    ctx = ctx_of(p)
    assert ctx is not None and "handoff-20261003T000000Z.md" in ctx
    assert "ReadSessionContext(sessionId=" not in ctx


def test_handoff_and_stale_index_glue_into_one_json(tmp_path: Path):
    proj = make_kb_project(tmp_path)
    build_index(proj)
    os.utime(proj / ".gitmark" / "index.db", (0, 0))
    write_handoff(proj, "handoff-sess_old.md", "From: sess_old\n")
    p = run_hook(proj)
    assert p.returncode == 0
    ctx = ctx_of(p)
    assert ctx is not None
    assert "gitmark.py index" in ctx
    assert "ReadSessionContext(sessionId=sess_old" in ctx
    assert p.stdout.count("\n") == 1
