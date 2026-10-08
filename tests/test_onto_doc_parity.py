"""Тесты нового поведения gitmark.py из плана onto-doc-parity: инвариант I10
(индексная цепочка body-ссылок от docs/README.md через подразделы) и
inventory-таргет «планы» (реестр docs/plans/README.md на генерате, I7-механизм),
плюс stat --json для coverage-дельты прогона онто-дока.
Существующее поведение покрыто test_gitmark.py."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

_GITMARK = Path(__file__).resolve().parent.parent / "skills" / "kb-search" / "gitmark.py"
_spec = importlib.util.spec_from_file_location("gitmark_parity", _GITMARK)
gm = importlib.util.module_from_spec(_spec)
sys.modules["gitmark_parity"] = gm
_spec.loader.exec_module(gm)


COMMAND = """---
description: Test command for the registry.
args: "<topic>"
drives: "test skill"
---

Run the test skill on: `$ARGUMENTS`.
"""

REGISTRY = """---
node_type: reference
title: Test commands
---

# Test commands

<!-- BEGIN inventory:commands -->
<!-- END inventory:commands -->

<!-- BEGIN inventory:skills -->
<!-- END inventory:skills -->

---

## `/foo` — test command

- **Definition:** `.zcode/commands/foo.md`
"""

PLAN = ("---\nnode_type: plan\ntitle: {title}\nservice: _platform\nstatus: {status}\n"
        "updated: 2026-10-08\n---\n\n# {title}\n")

TICKET = ("---\nnode_type: ticket\ntitle: {title}\nservice: _platform\nstatus: {status}\n"
          "updated: 2026-10-08\n---\n\n# {title}\n")


# ── I10: индексная цепочка ─────────────────────────────────────────

def _chain_repo(tmp_path: Path) -> Path:
    """docs/README → plans/ + reference/; plans/README → alpha/ (с README);
    beta/ без README — зона I5, не I10."""
    (tmp_path / "docs" / "plans" / "alpha").mkdir(parents=True)
    (tmp_path / "docs" / "plans" / "beta").mkdir()
    (tmp_path / "docs" / "reference").mkdir()
    (tmp_path / "docs" / "README.md").write_text(
        "---\nnode_type: index\ntitle: KB\n---\n\n# KB\n\n"
        "- [plans](plans/README.md)\n- [reference](reference/README.md)\n", encoding="utf-8")
    (tmp_path / "docs" / "plans" / "README.md").write_text(
        "---\nnode_type: index\ntitle: Plans\n---\n\n# Plans\n\n"
        "- [alpha](alpha/README.md)\n", encoding="utf-8")
    (tmp_path / "docs" / "plans" / "alpha" / "README.md").write_text(
        "---\nnode_type: index\ntitle: Alpha\n---\n\n# Alpha\n", encoding="utf-8")
    (tmp_path / "docs" / "plans" / "beta" / "note.md").write_text(
        "---\nnode_type: index\ntitle: Beta note\n---\n\n# Beta note\n", encoding="utf-8")
    (tmp_path / "docs" / "reference" / "README.md").write_text(
        "---\nnode_type: index\ntitle: Reference\n---\n\n# Reference\n", encoding="utf-8")
    return tmp_path


def _i10(issues: list) -> list:
    return [i for i in issues if i[1] == "I10"]


def test_i10_green_chain(tmp_path: Path):
    assert _i10(gm.cmd_lint(_chain_repo(tmp_path))["issues"]) == []


def test_i10_red_when_body_link_removed(tmp_path: Path):
    repo = _chain_repo(tmp_path)
    rm = repo / "docs" / "plans" / "README.md"
    rm.write_text(rm.read_text(encoding="utf-8").replace("- [alpha](alpha/README.md)\n", ""),
                  encoding="utf-8")
    i10 = _i10(gm.cmd_lint(repo)["issues"])
    assert len(i10) == 1
    assert i10[0][0] == "ERR" and i10[0][2] == "docs/plans/README.md"
    assert "docs/plans/alpha" in i10[0][3]


def test_i10_green_after_restoring_the_line(tmp_path: Path):
    repo = _chain_repo(tmp_path)
    rm = repo / "docs" / "plans" / "README.md"
    original = rm.read_text(encoding="utf-8")
    rm.write_text(original.replace("- [alpha](alpha/README.md)\n", ""), encoding="utf-8")
    assert _i10(gm.cmd_lint(repo)["issues"])
    rm.write_text(original, encoding="utf-8")
    assert _i10(gm.cmd_lint(repo)["issues"]) == []


def test_i10_ignores_frontmatter_links(tmp_path: Path):
    repo = _chain_repo(tmp_path)
    rm = repo / "docs" / "plans" / "README.md"
    rm.write_text(
        "---\nnode_type: index\ntitle: Plans\nlinks:\n  relates_to: [alpha/README.md]\n---\n\n"
        "# Plans\n", encoding="utf-8")
    assert len(_i10(gm.cmd_lint(repo)["issues"])) == 1


def test_i10_ignores_links_in_code_fences(tmp_path: Path):
    repo = _chain_repo(tmp_path)
    rm = repo / "docs" / "plans" / "README.md"
    rm.write_text(
        "---\nnode_type: index\ntitle: Plans\n---\n\n# Plans\n\n"
        "```\n[alpha](alpha/README.md)\n```\n", encoding="utf-8")
    assert len(_i10(gm.cmd_lint(repo)["issues"])) == 1


def test_i10_counts_a_link_to_the_folder_itself(tmp_path: Path):
    repo = _chain_repo(tmp_path)
    rm = repo / "docs" / "plans" / "README.md"
    rm.write_text(rm.read_text(encoding="utf-8").replace("(alpha/README.md)", "(alpha)"),
                  encoding="utf-8")
    assert _i10(gm.cmd_lint(repo)["issues"]) == []


def test_i10_grandchild_link_does_not_cover_the_intermediate(tmp_path: Path):
    """Ссылка из docs/README сразу на внука не заменяет ссылку на подраздел:
    цепочка — родитель → каждый следующий уровень, а не через уровень."""
    repo = _chain_repo(tmp_path)
    rm = repo / "docs" / "README.md"
    rm.write_text(
        "---\nnode_type: index\ntitle: KB\n---\n\n# KB\n\n"
        "- [reference](reference/README.md)\n- [напрямую к внуку](plans/alpha/README.md)\n",
        encoding="utf-8")
    i10 = _i10(gm.cmd_lint(repo)["issues"])
    assert [i[2] for i in i10] == ["docs/README.md"]
    assert "docs/plans" in i10[0][3]


def test_i10_silent_without_docs_readme(tmp_path: Path):
    repo = _chain_repo(tmp_path)
    (repo / "docs" / "README.md").unlink()
    assert _i10(gm.cmd_lint(repo)["issues"]) == []


def test_i10_child_without_readme_is_not_its_finding(tmp_path: Path):
    """beta/ без README — находка I5 (WARN — severity закреплён), I10 по ней молчит."""
    repo = _chain_repo(tmp_path)
    issues = gm.cmd_lint(repo)["issues"]
    assert _i10(issues) == []
    assert any(i[0] == "WARN" and i[1] == "I5" and "docs/plans/beta" in i[2] for i in issues)


# ── inventory-таргет «планы» ───────────────────────────────────────

def _plans_repo(tmp_path: Path) -> Path:
    """Репо с командой и реестром команд (чтобы I7 был чист вне планов) и
    docs/plans: папка duo (план archived, тикеты archived+draft) и файл solo.md
    (draft); README plans с пустыми маркерами plans."""
    (tmp_path / ".zcode" / "commands").mkdir(parents=True)
    (tmp_path / ".zcode" / "commands" / "foo.md").write_text(COMMAND, encoding="utf-8")
    (tmp_path / "docs" / "reference").mkdir(parents=True)
    (tmp_path / "docs" / "reference" / "commands.md").write_text(REGISTRY, encoding="utf-8")
    (tmp_path / "docs" / "reference" / "README.md").write_text(
        "---\nnode_type: index\ntitle: Reference\n---\n\n# Reference\n", encoding="utf-8")
    plans = tmp_path / "docs" / "plans"
    (plans / "duo").mkdir(parents=True)
    (plans / "README.md").write_text(
        "---\nnode_type: index\ntitle: Plans\n---\n\n# Plans\n\n"
        "<!-- BEGIN inventory:plans -->\n<!-- END inventory:plans -->\n", encoding="utf-8")
    (plans / "duo" / "README.md").write_text(PLAN.format(title="Duo", status="archived"),
                                             encoding="utf-8")
    (plans / "duo" / "01-one.md").write_text(TICKET.format(title="One", status="archived"),
                                             encoding="utf-8")
    (plans / "duo" / "02-two.md").write_text(TICKET.format(title="Two", status="draft"),
                                             encoding="utf-8")
    (plans / "solo.md").write_text(PLAN.format(title="Solo", status="draft"), encoding="utf-8")
    return tmp_path


def _between(text: str, what: str) -> str:
    b, e = f"<!-- BEGIN inventory:{what} -->", f"<!-- END inventory:{what} -->"
    return text[text.find(b) + len(b):text.find(e)].strip("\n")


def test_scan_plans_aggregates_statuses_and_ticket_counters(tmp_path: Path):
    rows = gm._scan_plans(_plans_repo(tmp_path))
    assert [(r["name"], r["status"], r["done"], r["total"]) for r in rows] == [
        ("duo", "archived", 1, 2),
        ("solo", "draft", 0, 0),
    ]
    assert rows[0]["link"] == "duo/README.md" and rows[0]["label"] == "duo/"
    assert rows[1]["link"] == "solo.md"


def test_plans_table_generated_and_idempotent(tmp_path: Path):
    repo = _plans_repo(tmp_path)
    r = gm.cmd_inventory(repo)
    assert "plans" in r["changed"] and r["plans"] == 2
    table = _between((repo / "docs" / "plans" / "README.md").read_text(encoding="utf-8"), "plans")
    assert table == "\n".join([
        "| Plan | Status | Tickets |", "|---|---|---|",
        "| [duo/](duo/README.md) | archived | 1/2 |",
        "| [solo.md](solo.md) | draft | — |"])
    assert gm.cmd_inventory(repo)["changed"] == []


def test_check_catches_plan_status_flip(tmp_path: Path):
    """Done-критерий реестра: статус носителя меняется без перегенерации —
    и `inventory --check`, и lint ловят рассинхрон (I7, ERR)."""
    repo = _plans_repo(tmp_path)
    gm.cmd_inventory(repo)
    solo = repo / "docs" / "plans" / "solo.md"
    solo.write_text(solo.read_text(encoding="utf-8").replace("status: draft", "status: archived"),
                    encoding="utf-8")
    issues = gm.cmd_inventory(repo, check=True)["issues"]
    assert issues and issues[0][0] == "docs/plans/README.md"
    assert "рассинхронизирована" in issues[0][1]
    r = gm.cmd_lint(repo)
    assert any(i[1] == "I7" and i[2] == "docs/plans/README.md" and i[0] == "ERR"
               for i in r["issues"])


def test_inventory_extinguishes_the_flip(tmp_path: Path):
    repo = _plans_repo(tmp_path)
    gm.cmd_inventory(repo)
    solo = repo / "docs" / "plans" / "solo.md"
    solo.write_text(solo.read_text(encoding="utf-8").replace("status: draft", "status: archived"),
                    encoding="utf-8")
    assert "plans" in gm.cmd_inventory(repo)["changed"]
    assert gm.cmd_inventory(repo, check=True)["issues"] == []


def test_ticket_status_flip_is_caught_too(tmp_path: Path):
    """Счётчик тикетов — тоже frontmatter-производное: flip тикета ловится так же."""
    repo = _plans_repo(tmp_path)
    gm.cmd_inventory(repo)
    t = repo / "docs" / "plans" / "duo" / "02-two.md"
    t.write_text(t.read_text(encoding="utf-8").replace("status: draft", "status: archived"),
                 encoding="utf-8")
    assert gm.cmd_inventory(repo, check=True)["issues"]
    assert "plans" in gm.cmd_inventory(repo)["changed"]
    assert gm.cmd_inventory(repo, check=True)["issues"] == []


def test_plans_target_silent_without_index_readme(tmp_path: Path):
    repo = _plans_repo(tmp_path)
    gm.cmd_inventory(repo)
    (repo / "docs" / "plans" / "README.md").unlink()
    r = gm.cmd_inventory(repo, check=True)
    assert r["plans"] == 2 and r["issues"] == []
    gm.cmd_inventory(repo)
    assert not (repo / "docs" / "plans" / "README.md").exists()  # не создаётся


def test_plans_target_requires_markers(tmp_path: Path):
    repo = _plans_repo(tmp_path)
    gm.cmd_inventory(repo)
    rm = repo / "docs" / "plans" / "README.md"
    rm.write_text("---\nnode_type: index\ntitle: Plans\n---\n\n# Plans\n", encoding="utf-8")
    issues = gm.cmd_inventory(repo, check=True)["issues"]
    assert issues == [("docs/plans/README.md", "нет или битые маркеры inventory:plans")]
    with pytest.raises(SystemExit) as ei:
        gm.cmd_inventory(repo)
    # контрактный код закреплён: «ERR напечатан, exit 0» — резиновый гейт (гейт-находка 11)
    assert ei.value.code == 2


def test_lint_strict_green_on_synced_plans_repo(tmp_path: Path):
    """Полный lint синхронного репо без ERR (I7 реестров + I10 цепочки чисты)."""
    repo = _plans_repo(tmp_path)
    (repo / "docs" / "README.md").write_text(
        "---\nnode_type: index\ntitle: KB\n---\n\n# KB\n\n"
        "- [plans](plans/README.md)\n- [reference](reference/README.md)\n", encoding="utf-8")
    gm.cmd_inventory(repo)
    assert gm.cmd_lint(repo)["errors"] == []


# ── stat --json (coverage-дельта прогона онто-дока) ────────────────

def test_stat_json_machine_readable(tmp_path: Path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.md").write_text("# A\n\nтекст\n", encoding="utf-8")
    subprocess.run([sys.executable, str(_GITMARK), "--root", str(tmp_path), "index"],
                   check=True, capture_output=True, text=True)
    out = subprocess.run(
        [sys.executable, str(_GITMARK), "--root", str(tmp_path), "stat", "--json"],
        check=True, capture_output=True, text=True).stdout
    s = json.loads(out)
    assert s["indexed"] is True and s["files"] == 1
    for key in ("chunks", "links", "bytes"):
        assert key in s


def test_stat_json_without_index_is_still_json(tmp_path: Path):
    """«До»-нога coverage-дельты: свежий чекаут без .gitmark — stdout обязан
    остаться машинным JSON (indexed: false), а не человекочитаемой строкой
    (гейт-находка 3)."""
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.md").write_text("# A\n", encoding="utf-8")
    r = subprocess.run(
        [sys.executable, str(_GITMARK), "--root", str(tmp_path), "stat", "--json"],
        capture_output=True, text=True)
    assert r.returncode == 0
    s = json.loads(r.stdout)
    assert s["indexed"] is False


# ── фикс-пойнты confirm-рана dwfrun-0f9b01df ───────────────────────

def test_inventory_is_atomic_on_missing_plans_markers(tmp_path: Path):
    """Гейт-находка 4: exit 2 из plans-ветки не пишет commands.md — по коду
    возврата «ничего не применено» и «половина применена» неотличимы."""
    repo = _plans_repo(tmp_path)
    gm.cmd_inventory(repo)
    reg = repo / "docs" / "reference" / "commands.md"
    reg.write_text(reg.read_text(encoding="utf-8").replace("| `/foo` |", "| `/foo` | STALE"),
                   encoding="utf-8")  # рассинхрон командной таблицы — регенерация хотела бы писать
    rm = repo / "docs" / "plans" / "README.md"
    rm.write_text("---\nnode_type: index\ntitle: Plans\n---\n\n# Plans\n", encoding="utf-8")
    before = reg.read_bytes()
    with pytest.raises(SystemExit) as ei:
        gm.cmd_inventory(repo)
    assert ei.value.code == 2
    assert reg.read_bytes() == before  # частичной мутации нет


def test_plans_folder_without_readme_links_to_the_folder(tmp_path: Path):
    """Гейт-находка 5: папка без README — строка таблицы ссылается на сам
    каталог, генерат не плодит битую ссылку (I4)."""
    repo = _plans_repo(tmp_path)
    gm.cmd_inventory(repo)
    (repo / "docs" / "plans" / "foo").mkdir()
    (repo / "docs" / "plans" / "foo" / "01-t.md").write_text(
        TICKET.format(title="T", status="draft"), encoding="utf-8")
    gm.cmd_inventory(repo)
    table = _between((repo / "docs" / "plans" / "README.md").read_text(encoding="utf-8"), "plans")
    assert "[foo/](foo/)" in table and "foo/README.md" not in table
    assert not [i for i in gm.cmd_lint(repo)["issues"]
                if i[1] == "I4" and "foo" in i[3]]


def test_swapped_plan_markers_are_named_broken(tmp_path: Path):
    """Гейт-находка 6: END раньше BEGIN — «нет или битые маркеры», а не ложный
    «рассинхрон» при синхронной таблице."""
    repo = _plans_repo(tmp_path)
    gm.cmd_inventory(repo)
    rm = repo / "docs" / "plans" / "README.md"
    rm.write_text(
        "---\nnode_type: index\ntitle: Plans\n---\n\n# Plans\n\n"
        "<!-- END inventory:plans -->\n<!-- BEGIN inventory:plans -->\n", encoding="utf-8")
    issues = gm.cmd_inventory(repo, check=True)["issues"]
    assert issues == [("docs/plans/README.md", "нет или битые маркеры inventory:plans")]


def test_i9_validates_every_values_spec(tmp_path: Path):
    """Гейт-находка 8 (high): проверка values обязана жить внутри цикла по
    spec'ам — валируется каждое поле, пустой values не роняет lint остаточными
    переменными."""
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "README.md").write_text("# KB\n", encoding="utf-8")
    (tmp_path / "cards").mkdir()
    (tmp_path / "cards" / "README.md").write_text("# Cards\n", encoding="utf-8")
    (tmp_path / "cards" / "_s.md").write_text(
        "---\nnode_type: schema\ncard_type: card\nrequired: [uid]\n"
        'values: ["kind: a|b", "tone: x|y"]\n---\n\n# S\n', encoding="utf-8")
    (tmp_path / "cards" / "c.md").write_text(
        "---\nnode_type: card\nuid: u1\nkind: c\ntone: z\n---\n\n# C\n", encoding="utf-8")
    msgs = [i[3] for i in gm.cmd_lint(tmp_path)["issues"] if i[1] == "I9"]
    assert any("поле kind" in m and "вне списка" in m for m in msgs)
    assert any("поле tone" in m and "вне списка" in m for m in msgs)
    # схема без values —lint не падает UnboundLocalError и не берёт чужие поля
    (tmp_path / "cards" / "_s.md").write_text(
        "---\nnode_type: schema\ncard_type: card\nrequired: [uid]\n---\n\n# S\n",
        encoding="utf-8")
    assert gm.cmd_lint(tmp_path)["checked"] >= 3
