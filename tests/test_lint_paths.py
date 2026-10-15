"""Тикет queue-3/02: lint валидирует path-аргументы.

Несуществующий путь — именованный отказ с путём в сообщении и exit 2
(класс usage-ошибки argparse), а не молчаливый полный прогон KB с «чисто».
Семантика фильтра по существующим путям запинена матрицей: sel сужает только
per-file проверки I1/I2/I3/I6, сквозные I4/I5/I7–I10 и счётчик checked
всегда идут по всему KB (cmd_lint: sel-фильтр во втором цикле по файлам).
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

_GITMARK = Path(__file__).resolve().parent.parent / "skills" / "kb-search" / "gitmark.py"
_spec = importlib.util.spec_from_file_location("gitmark", _GITMARK)
gm = importlib.util.module_from_spec(_spec)
sys.modules["gitmark"] = gm
_spec.loader.exec_module(gm)


@pytest.fixture()
def kb(tmp_path: Path) -> Path:
    docs = tmp_path / "docs"
    (docs / "reference").mkdir(parents=True)
    (docs / "README.md").write_text(
        "---\nnode_type: index\ntitle: KB\n---\n\n# KB\n", encoding="utf-8")
    (docs / "reference" / "README.md").write_text(
        "---\nnode_type: index\ntitle: Reference\n---\n\n# Reference\n", encoding="utf-8")
    # aa — карта с I2 (node_type вне словаря): единственный выбранный файл
    (docs / "reference" / "aa.md").write_text(
        "---\nnode_type: bogus_type\ntitle: AA\n---\n\n# AA\n", encoding="utf-8")
    # bb — та же I2 вне выборки: per-file проверки скрыты sel-фильтром
    (docs / "reference" / "bb.md").write_text(
        "---\nnode_type: bogus_type\ntitle: BB\n---\n\n# BB\n", encoding="utf-8")
    # cc — битая ссылка (I4) вне выборки: граф связей строится по всему KB
    (docs / "reference" / "cc.md").write_text(
        "---\nnode_type: reference\ntitle: CC\n---\n\n[битая](./nope.md)\n", encoding="utf-8")
    return tmp_path


# ── отказ по несуществующему пути (движок) ──────────────────────────


def test_nonexistent_path_named_refusal(kb: Path):
    with pytest.raises(ValueError, match="docs/plans/nope\\.md") as ei:
        gm.cmd_lint(kb, ["docs/plans/nope.md"])
    assert str(ei.value).startswith("путь не найден: ")


def test_every_missing_path_is_named(kb: Path):
    with pytest.raises(ValueError) as ei:
        gm.cmd_lint(kb, ["docs/aa-nope.md", "docs/bb-nope.md"])
    assert "docs/aa-nope.md" in str(ei.value) and "docs/bb-nope.md" in str(ei.value)


def test_existing_path_does_not_refuse(kb: Path):
    r = gm.cmd_lint(kb, ["docs/reference/aa.md"])
    assert isinstance(r, dict) and r["checked"] > 0


# ── семантика фильтра по существующим путям, запинена кодом ─────────


def test_selection_narrows_only_per_file_checks(kb: Path):
    """sel сужает I1/I2/I3/I6, но не I4: bb (вне выборки) скрыт, cc (вне
    выборки) с битой ссылкой — пойман; сводка checked считает весь KB."""
    r = gm.cmd_lint(kb, ["docs/reference/aa.md"])
    i2_paths = [i[2] for i in r["issues"] if i[1] == "I2"]
    assert "docs/reference/aa.md" in i2_paths, "выбранный файл не проверен"
    assert "docs/reference/bb.md" not in i2_paths, "I2 вышел за выборку"
    assert any(i[2] == "docs/reference/cc.md" and i[1] == "I4" for i in r["issues"]), \
        "I4 граф должен строиться по всему KB, а не по выборке"
    assert r["checked"] == len(list(gm.iter_md(kb))), \
        "сводка обязана считать весь KB и при выборке"


def test_full_run_reports_both_i2(kb: Path):
    """Без paths оба I2 на месте — фильтр скрывал bb, а не чинил его."""
    r = gm.cmd_lint(kb)
    i2_paths = [i[2] for i in r["issues"] if i[1] == "I2"]
    assert "docs/reference/aa.md" in i2_paths and "docs/reference/bb.md" in i2_paths


# ── CLI E2E: exit-коды и каналы вывода ──────────────────────────────


def test_cli_refusal_exit2_stderr_no_clean_line(kb: Path):
    r = subprocess.run(
        [sys.executable, str(_GITMARK), "--root", str(kb), "lint", "--strict",
         "docs/plans/nope.md"],
        capture_output=True, text=True, timeout=60,
    )
    assert r.returncode == 2, f"ожидался usage-отказ, rc={r.returncode}, stderr={r.stderr!r}"
    assert "gitmark: путь не найден: docs/plans/nope.md" in r.stderr
    assert "чисто" not in r.stdout + r.stderr, "отказ выдал строку успеха"


def test_cli_existing_path_keeps_previous_exit_and_channels(kb: Path):
    """Существующий путь: прежний контракт — ошибки в stdout, exit 1 только
    при --strict, сводка всего KB; I4 невыбранного cc виден, как раньше."""
    r = subprocess.run(
        [sys.executable, str(_GITMARK), "--root", str(kb), "lint", "--strict",
         "docs/reference/aa.md"],
        capture_output=True, text=True, timeout=60,
    )
    assert r.returncode == 1, f"у грязной выборки под --strict rc=1, получили {r.returncode}"
    assert "node_type='bogus_type' вне словаря" in r.stdout
    assert "docs/reference/cc.md" in r.stdout, "I4 невыбранного файла должен печататься"
    assert f"({len(list(gm.iter_md(kb)))} файлов" in r.stdout


def test_cli_without_strict_dirty_kb_still_exit0(kb: Path):
    """Без --strict даже ERR не меняют exit — прежнее поведение сохранено."""
    r = subprocess.run(
        [sys.executable, str(_GITMARK), "--root", str(kb), "lint",
         "docs/reference/aa.md"],
        capture_output=True, text=True, timeout=60,
    )
    assert r.returncode == 0, r.stderr[-500:]


# ── мутационная ловушка ─────────────────────────────────────────────


def test_refusal_is_driven_by_filesystem_existence(kb: Path, monkeypatch):
    """Ловушка на механизм отказа: exists() для шипуемого пути нейтрализован
    до «существует» — эквивалент удаления проверки (позитивные тесты выше в
    этот момент обязаны краснеть). Патч точечный, только на этот путь:
    глобальный рвал несвязанные exists()-проверки внутри cmd_lint
    (gitignore_warnings). Если отказ перестанет опираться на Path.exists,
    эта проба краснеет первой — проба отвязалась от реальной реализации."""
    orig = gm.Path.exists

    def fake_exists(self):
        if self.as_posix().endswith("docs/plans/nope.md"):
            return True
        return orig(self)

    monkeypatch.setattr(gm.Path, "exists", fake_exists)
    r = gm.cmd_lint(kb, ["docs/plans/nope.md"])
    assert isinstance(r, dict), "при нейтрализованном exists() отказа быть не должно"
