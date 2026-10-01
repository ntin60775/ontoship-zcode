"""Tests for the roles resolver: layer priority, merge by name, broken files, set/unset."""
import importlib.util
import sys
from pathlib import Path

import pytest

_SPEC = importlib.util.spec_from_file_location(
    "roles", Path(__file__).resolve().parent.parent / "skills" / "roles" / "roles.py")
roles = importlib.util.module_from_spec(_SPEC)
sys.modules["roles"] = roles
_SPEC.loader.exec_module(roles)


def wf(path: Path, roles_block: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\n{roles_block}\n---\n\n# note\n", encoding="utf-8")
    return path


def test_priority_project_over_user_over_default(tmp_path: Path):
    d = wf(tmp_path / "d.md", "roles:\n  reviewer:\n    model: default/m\n    level: low\n")
    u = wf(tmp_path / "u.md", "roles:\n  reviewer:\n    model: user/m\n    level: high\n")
    p = wf(tmp_path / "p.md", "roles:\n  reviewer:\n    model: proj/m\n")
    got = roles.resolve(tmp_path, default_path=d, user_path=u, project_path=p)
    assert got["reviewer"]["model"] == "proj/m"
    assert got["reviewer"]["_source"] == "project"
    assert "level" not in got["reviewer"]


def test_merge_by_name_not_by_file(tmp_path: Path):
    """Проектный reviewer не прячет пользовательский challenger."""
    d = wf(tmp_path / "d.md",
           "roles:\n  reviewer:\n    model: default/r\n  challenger:\n    model: default/c\n")
    u = wf(tmp_path / "u.md", "roles:\n  challenger:\n    model: user/c\n    level: max\n")
    p = wf(tmp_path / "p.md", "roles:\n  reviewer:\n    model: proj/r\n")
    got = roles.resolve(tmp_path, default_path=d, user_path=u, project_path=p)
    assert got["reviewer"]["model"] == "proj/r"
    assert got["challenger"]["model"] == "user/c"
    assert got["challenger"]["_source"] == "user"


def test_missing_layers_are_not_errors(tmp_path: Path, monkeypatch):
    # изолируем user-слой: тест не должен зависеть от реального ~/.zcode/ontoship
    monkeypatch.setenv("ONTOSHIP_HOME", str(tmp_path / "home"))
    d = wf(tmp_path / "d.md", "roles:\n  reviewer:\n    model: default/r\n")
    got = roles.resolve(tmp_path, default_path=d)
    assert got["reviewer"]["_source"] == "plugin-default"


def test_broken_layer_fails_closed(tmp_path: Path):
    d = wf(tmp_path / "d.md", "roles:\n  reviewer:\n    model: default/r\n")
    u = tmp_path / "u.md"
    u.parent.mkdir(parents=True, exist_ok=True)
    u.write_text("---\nroles:\n  reviewer:\n      bad indent: :\n---\n", encoding="utf-8")
    with pytest.raises(roles.RolesError):
        roles.resolve(tmp_path, default_path=d, user_path=u)


def test_unknown_key_and_missing_model_fail(tmp_path: Path):
    d = wf(tmp_path / "d.md", "roles:\n  reviewer:\n    modle: typo/m\n")
    with pytest.raises(roles.RolesError):
        roles.parse_roles(d.read_text("utf-8"), str(d))
    d2 = wf(tmp_path / "d2.md", "roles:\n  reviewer:\n    level: max\n")
    with pytest.raises(roles.RolesError):
        roles.parse_roles(d2.read_text("utf-8"), str(d2))


def test_set_writes_user_layer_and_preserves_siblings(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("ONTOSHIP_HOME", str(tmp_path / "home"))
    msg = roles.cmd_set("reviewer", "new/m$max", project=False, root=tmp_path)
    assert "user-слой" in msg
    f = tmp_path / "home" / ".zcode" / "ontoship" / "roles.md"
    got = roles.parse_roles(f.read_text("utf-8"), str(f))
    assert got["reviewer"] == {"model": "new/m", "level": "max"}
    roles.cmd_set("challenger", "new/c", project=False, root=tmp_path)
    got = roles.parse_roles(f.read_text("utf-8"), str(f))
    assert got["challenger"]["model"] == "new/c" and "level" not in got["challenger"]
    assert got["reviewer"]["model"] == "new/m"


def test_set_project_writes_project_layer(tmp_path: Path):
    roles.cmd_set("reviewer", "proj/m$high", project=True, root=tmp_path)
    f = tmp_path / ".zcode" / "ontoship" / "roles.md"
    got = roles.parse_roles(f.read_text("utf-8"), str(f))
    assert got["reviewer"] == {"model": "proj/m", "level": "high"}


def test_unset_removes_project_role_only(tmp_path: Path, monkeypatch):
    # изолируем user-слой: сняли project-роль — из реального home ничего не подтекает
    monkeypatch.setenv("ONTOSHIP_HOME", str(tmp_path / "home"))
    roles.cmd_set("reviewer", "proj/m", project=True, root=tmp_path)
    roles.cmd_set("challenger", "proj/c", project=True, root=tmp_path)
    print(roles.cmd_unset("reviewer", user_layer=False, root=tmp_path))
    got = roles.resolve(tmp_path, default_path=tmp_path / "nope.md")
    assert "reviewer" not in got
    assert got["challenger"]["model"] == "proj/c"
    msg = roles.cmd_unset("reviewer", user_layer=False, root=tmp_path)
    assert "нечего" in msg


def test_split_model_level():
    assert roles._split_model("a/b$c") == ("a/b", "c")
    assert roles._split_model("a/b") == ("a/b", None)
    with pytest.raises(roles.RolesError):
        roles._split_model("a/b$")
    with pytest.raises(roles.RolesError):
        roles._split_model("a/b$UPPER")
