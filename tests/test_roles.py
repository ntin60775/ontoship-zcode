"""Tests for the roles resolver: layer priority, merge by name, broken files, set/unset."""
import importlib.util
import re
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


REPO = Path(__file__).resolve().parent.parent


def test_defaults_layer_defines_fallback_constant(tmp_path: Path, monkeypatch):
    """roles-fallback-substrate/01: the restart slot resolves from the defaults
    layer with model$level and plugin-default provenance — an assigned run that
    died must be restartable on fallback. Mutations that break the defaults
    wiring (e.g. a bad DEFAULTS_REL) or drop the provenance must turn this test
    red (mutation probes confirmed by the gate's confirmer)."""
    monkeypatch.setenv("ONTOSHIP_HOME", str(tmp_path / "home"))  # isolate user layer
    got = roles.resolve(tmp_path)  # project layer missing in tmp_path as well
    cfg = got.get("fallback")
    assert cfg, "роль fallback не резолвится из defaults-слоя"
    assert cfg["_source"] == "plugin-default", "у fallback нет provenance defaults-слоя"
    assert cfg["_file"].endswith("defaults/roles.md"), "fallback резолвится не из defaults/roles.md"
    assert cfg.get("level"), "у fallback нет уровня"
    text = (REPO / "defaults" / "roles.md").read_text("utf-8")
    assert "not a step assignment" in text, "абзац-описание fallback повреждён"
    assert "No workflow script reads it as its model" in text, "маркер честного статуса механики повреждён"


def test_roles_skill_marks_fallback_as_service_constant():
    """The /roles dashboard instruction must couple the fallback role with the
    service-constant note in one block — without the block fallback renders as
    a regular assignable step model. Dropping the note block from
    skills/roles/SKILL.md must turn this test red (mutation probe); the intro
    mention of `fallback` alone must not satisfy it."""
    skill = (REPO / "skills" / "roles" / "SKILL.md").read_text("utf-8")
    assert re.search(
        r"The `fallback` role.*константа фолбэка, потребителям не назначается",
        skill, re.S), "пункт дашборда с пометкой константы фолбэка повреждён"


def test_defaults_define_curator_and_surveyor(tmp_path: Path, monkeypatch):
    """roles-per-agent/01: записи онто-дока — curator $high (кураторы fan-out и
    healer) и surveyor $max (surveyor), обе из defaults-слоя с провенансом и
    файлом; имя surveyor не коллизирует с гейт-агентом synthesizer (грилл
    d5/d11); описания потребителей и пометка целевого подключения запинены
    якорями — «synthesizer» живёт и в абзаце Record rule, голое слово не
    ловит повреждение заметки. Dropping a record, its level, its description
    or the collision note must each turn this red."""
    monkeypatch.setenv("ONTOSHIP_HOME", str(tmp_path / "home"))  # isolate user layer
    got = roles.resolve(tmp_path)  # project layer missing in tmp_path as well
    cur = got.get("curator")
    assert cur, "роль curator не резолвится из defaults-слоя"
    assert cur["_source"] == "plugin-default", "у curator нет provenance defaults-слоя"
    assert cur["_file"].endswith("defaults/roles.md"), "curator резолвится не из defaults/roles.md"
    assert "GLM-5.3-Flash" in cur["model"], "curator ушёл с GLM-5.3-Flash без тикета"
    assert cur.get("level") == "high", "у curator не уровень high (решение 2026-10-13)"
    sur = got.get("surveyor")
    assert sur, "роль surveyor не резолвится из defaults-слоя"
    assert sur["_source"] == "plugin-default", "у surveyor нет provenance defaults-слоя"
    assert sur["_file"].endswith("defaults/roles.md"), "surveyor резолвится не из defaults/roles.md"
    assert "GLM-5.3-Flash" in sur["model"], "surveyor ушёл с GLM-5.3-Flash без тикета"
    assert sur.get("level") == "max", "у surveyor не уровень max"
    text = (REPO / "defaults" / "roles.md").read_text("utf-8")
    assert "Named `surveyor`, not `synthesizer`" in text, "заметка о неколлизии surveyor/synthesizer повреждена"
    assert "one curator per plan piece" in text, "описание потребителя curator повреждено"
    assert "surveys the repo into" in text, "описание потребителя surveyor повреждено"
    assert "roles-per-agent/02" in text, "пометка целевого подключения онто-дока потеряна"


def test_defaults_every_record_carries_explicit_level(tmp_path: Path, monkeypatch):
    """roles-per-agent/01: пин полноты — каждая запись defaults/roles.md несёт
    явный level (правило записи: новая роль — GLM-5.3-Flash с level: max,
    исключения поимённо). Live probes at ticket and gate time: removing the
    level line of exactly the confirmer record → only this test red (1
    failed); the blunter `sed '/^    level: high$/d'` strips both confirmer
    and curator (both are `level: high`) and reddens both new tests (2
    failed, confirmer's gate run dwfrun-572c1bde). This pin only sees parse
    survivors — a record silently dropped by the parser (tab indent) is
    caught by the strict-format pin below."""
    monkeypatch.setenv("ONTOSHIP_HOME", str(tmp_path / "home"))  # isolate user layer
    got = roles.resolve(tmp_path)  # effective = defaults only
    assert got, "defaults-слой пуст — resolve ничего не вернул"
    missing = sorted(n for n, cfg in got.items() if not cfg.get("level"))
    assert not missing, f"записи defaults/roles.md без явного level: {missing}"


def test_defaults_frontmatter_strict_format():
    """roles-per-agent/01 (gate, dwfrun-572c1bde): каждая непустая
    не-комментарная строка frontmatter defaults/roles.md обязана совпадать с
    одной из трёх форм — `roles:`, `  <имя-роли>:`, `    model:|level:
    <значение>`. Парсер молча выбрасывает нераспознанную строку нулевого
    отступа (таб даёт indent 0 — отступ считается только по пробелам,
    parse_roles в skills/roles/roles.py), запись пропадает без RolesError, и
    пины над resolve её не видят; этот пин читает сырой текст. Мутационная
    проба живьём (конфирмер гейта): `s/^  confirmer:/\\tconfirmer:/` → RED."""
    fm = roles._frontmatter((REPO / "defaults" / "roles.md").read_text("utf-8"))
    bad = [
        f"строка {i + 2}: {raw!r}"
        for i, raw in enumerate(fm.splitlines())
        if raw.strip()
        and not raw.strip().startswith("#")
        and not re.fullmatch(r"roles:|  [a-z][a-z0-9-]*:|    (model|level): \S.*", raw)
    ]
    assert not bad, f"строки frontmatter вне строгого формата: {bad}"
