"""Tests for scripts/deploy-check.sh: green on a fresh consumer layout,
honest FAIL on corruption, WARN-only degradation. The script is exercised
end-to-end (subprocess, bash) in a fake consumer project built in tmp_path:
the package is the project's own .zcode/, resolved from cwd — not from the
script location."""
import json
import os
import shutil
import sqlite3
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "scripts" / "deploy-check.sh"

MAPPINGS = [
    {"from": "skills/kb-search", "to": ".zcode/skills/kb-search"},
    {"from": "skills/roles", "to": ".zcode/skills/roles"},
    {"from": "defaults", "to": ".zcode/defaults"},
    {"from": "package.json", "to": ".zcode/package.json"},
]


def make_consumer(tmp_path: Path, with_docs: bool = True) -> Path:
    """Minimal vendored layout: engine + roles resolver + role defaults +
    package manifest + journal, per the deploy mappings."""
    proj = tmp_path / "proj"
    z = proj / ".zcode"
    (z / "skills" / "kb-search").mkdir(parents=True)
    (z / "skills" / "roles").mkdir(parents=True)
    (z / "defaults").mkdir(parents=True)
    shutil.copy(REPO / "skills" / "kb-search" / "gitmark.py",
                z / "skills" / "kb-search" / "gitmark.py")
    shutil.copy(REPO / "skills" / "roles" / "roles.py",
                z / "skills" / "roles" / "roles.py")
    (z / "skills" / "kb-search" / "SKILL.md").write_text(
        "---\nnode_type: skill\ntitle: kb-search\n---\n", encoding="utf-8")
    (z / "skills" / "roles" / "SKILL.md").write_text(
        "---\nnode_type: skill\ntitle: roles\n---\n", encoding="utf-8")
    shutil.copy(REPO / "defaults" / "roles.md", z / "defaults" / "roles.md")
    shutil.copy(REPO / "package.json", z / "package.json")
    (z / "deployed.json").write_text(json.dumps(
        {"plugins": {"ontoship": {"ref": "vTEST", "mappings": MAPPINGS}}}),
        encoding="utf-8")
    if with_docs:
        docs = proj / "docs"
        docs.mkdir()
        (docs / "note.md").write_text(
            "---\nnode_type: note\ntitle: note\nupdated: 2026-09-30\n"
            "---\n\nOntoShip smoke word lives here.\n", encoding="utf-8")
    return proj


def run_check(proj: Path, env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(["bash", str(SCRIPT)], cwd=proj,
                          capture_output=True, text=True, timeout=120,
                          env={**os.environ, **(env or {})})


def _has_trigram() -> bool:
    """The script degrades trigram to a WARN (exit 2); the green test must
    expect the exit the host SQLite actually produces, not assume 3.34+."""
    c = sqlite3.connect(":memory:")
    try:
        c.execute("CREATE VIRTUAL TABLE t USING fts5(x, tokenize='trigram')")
        return True
    except sqlite3.OperationalError:
        return False


def test_green_on_fresh_consumer(tmp_path: Path):
    p = run_check(make_consumer(tmp_path))
    expected = 0 if _has_trigram() else 2
    assert p.returncode == expected, p.stdout + p.stderr
    assert f"deploy-check: exit={expected}" in p.stdout
    assert "deployed: ontoship@vTEST" in p.stdout
    assert "roles: default OK" in p.stdout
    assert "roles: reviewer OK" in p.stdout
    assert "[FAIL]" not in p.stdout


def test_missing_engine_file_fails(tmp_path: Path):
    proj = make_consumer(tmp_path)
    (proj / ".zcode" / "skills" / "kb-search" / "gitmark.py").unlink()
    p = run_check(proj)
    assert p.returncode == 1
    assert "[FAIL] отсутствует: .zcode/skills/kb-search/gitmark.py" in p.stdout


def test_corrupted_engine_fails(tmp_path: Path):
    proj = make_consumer(tmp_path)
    (proj / ".zcode" / "skills" / "kb-search" / "gitmark.py").write_text(
        "import sys; sys.exit(3)\n", encoding="utf-8")
    p = run_check(proj)
    assert p.returncode == 1
    assert "[FAIL] gitmark index" in p.stdout
    assert "[FAIL] смоук-поиск" in p.stdout


def test_missing_journal_fails(tmp_path: Path):
    proj = make_consumer(tmp_path)
    (proj / ".zcode" / "deployed.json").unlink()
    p = run_check(proj)
    assert p.returncode == 1
    assert "[FAIL] отсутствует: .zcode/deployed.json" in p.stdout


def test_broken_journal_fails(tmp_path: Path):
    proj = make_consumer(tmp_path)
    (proj / ".zcode" / "deployed.json").write_text("{not json", encoding="utf-8")
    p = run_check(proj)
    assert p.returncode == 1
    assert "[FAIL] журнал .zcode/deployed.json не читается" in p.stdout


def test_missing_mapped_target_fails(tmp_path: Path):
    """A whole mapping target gone (file mapping here) is caught via the journal;
    a file inside a mapped dir is the key-files loop's job."""
    proj = make_consumer(tmp_path)
    (proj / ".zcode" / "package.json").unlink()
    p = run_check(proj)
    assert p.returncode == 1
    assert "[FAIL] по журналу отсутствует: .zcode/package.json" in p.stdout


def test_journal_without_plugin_fails(tmp_path: Path):
    proj = make_consumer(tmp_path)
    (proj / ".zcode" / "deployed.json").write_text(
        json.dumps({"plugins": {}}), encoding="utf-8")
    p = run_check(proj)
    assert p.returncode == 1
    assert "[FAIL] в журнале нет записи плагина ontoship" in p.stdout


def test_journal_mapping_without_to_fails_cleanly(tmp_path: Path):
    """A malformed mapping is a clean [FAIL], not a KeyError traceback."""
    proj = make_consumer(tmp_path)
    (proj / ".zcode" / "deployed.json").write_text(json.dumps(
        {"plugins": {"ontoship": {"ref": "vTEST",
                                  "mappings": [{"from": "skills/x"}]}}}),
        encoding="utf-8")
    p = run_check(proj)
    assert p.returncode == 1
    assert "[FAIL] по журналу маппинг без 'to'" in p.stdout
    assert "Traceback" not in p.stdout


def test_emptied_skill_dir_fails(tmp_path: Path):
    """A vendored skill dir without its SKILL.md is broken, target exists or not."""
    proj = make_consumer(tmp_path)
    (proj / ".zcode" / "skills" / "roles" / "SKILL.md").unlink()
    p = run_check(proj)
    assert p.returncode == 1
    assert "[FAIL] по журналу в скилле нет SKILL.md: .zcode/skills/roles" in p.stdout


def test_empty_default_roles_with_user_override_fails(tmp_path: Path):
    """Roles resolving through a user override do not mask an empty vendored
    default: the ticket criterion is that .zcode finds the default."""
    proj = make_consumer(tmp_path)
    (proj / ".zcode" / "defaults" / "roles.md").write_text(
        "---\n---\n", encoding="utf-8")
    home = tmp_path / "home"
    layer = home / ".zcode" / "ontoship"
    layer.mkdir(parents=True)
    (layer / "roles.md").write_text(
        "---\nroles:\n  reviewer:\n    model: user/m\n    level: max\n---\n",
        encoding="utf-8")
    p = run_check(proj, env={"ONTOSHIP_HOME": str(home)})
    assert p.returncode == 1
    assert "[FAIL] дефолт ролей пуст" in p.stdout


def test_empty_kb_is_warn_only(tmp_path: Path):
    """No docs/ in the project: engine works, smoke has no hits — WARN, exit 2."""
    p = run_check(make_consumer(tmp_path, with_docs=False))
    assert p.returncode == 2, p.stdout + p.stderr
    assert "[WARN] смоук-поиск без хитов" in p.stdout
    assert "[FAIL]" not in p.stdout


def test_not_a_plugin_project_fails(tmp_path: Path):
    proj = tmp_path / "empty"
    proj.mkdir()
    p = run_check(proj)
    assert p.returncode == 1
    assert "[FAIL] отсутствует: .zcode/skills/kb-search/gitmark.py" in p.stdout
