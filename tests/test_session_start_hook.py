"""Tests for hooks/session-start.sh: stale-index notice at session start over
the engine's whole markdown corpus (git ls-files, like gitmark indexes it),
silence when fresh or outside a KB project, quiet --rebuild. The hook is
exercised end-to-end (subprocess, bash) against the real engine in a fake KB
project; mtimes are pinned with os.utime, so no sleeps."""
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


def run_hook(proj: Path, args: tuple = ()) -> subprocess.CompletedProcess:
    return subprocess.run(["bash", str(HOOK), *args], cwd=proj,
                          capture_output=True, text=True, timeout=120,
                          env={**os.environ, "ZCODE_PROJECT_DIR": str(proj)})


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
