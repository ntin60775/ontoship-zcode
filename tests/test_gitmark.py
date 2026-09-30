"""Тесты нового поведения gitmark.py из плана command-inventory:
идемпотентность inventory, поимка рассинхрона --check, парсер .gitignore, I7.
Существующее поведение не покрывается (вне scope плана)."""
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


COMMAND = """---
description: Test command for the registry.
args: "<topic>"
drives: "test skill"
---

Run the test skill on: `$ARGUMENTS`.
"""

SKILL = """---
name: test-skill
description: A skill for the registry tests.
---

Body.
"""

REGISTRY = """---
node_type: reference
title: Test commands
---

# Test commands

## Summary

<!-- BEGIN inventory:commands -->
<!-- END inventory:commands -->

<!-- BEGIN inventory:skills -->
<!-- END inventory:skills -->

---

## `/foo` — test command

- **Definition:** `.zcode/commands/foo.md`
"""


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    """Минимальный репо: одна команда, один навык, реестр с маркерами."""
    (tmp_path / ".zcode" / "commands").mkdir(parents=True)
    (tmp_path / ".zcode" / "skills" / "test-skill").mkdir(parents=True)
    (tmp_path / "docs" / "reference").mkdir(parents=True)
    (tmp_path / ".zcode" / "commands" / "foo.md").write_text(COMMAND, encoding="utf-8")
    (tmp_path / ".zcode" / "skills" / "test-skill" / "SKILL.md").write_text(SKILL, encoding="utf-8")
    (tmp_path / "docs" / "reference" / "commands.md").write_text(REGISTRY, encoding="utf-8")
    return tmp_path


def _between(text: str, what: str) -> str:
    b, e = f"<!-- BEGIN inventory:{what} -->", f"<!-- END inventory:{what} -->"
    return text[text.find(b) + len(b):text.find(e)].strip("\n")


# ── парсер .gitignore ──────────────────────────────────────────────

def test_gitignore_excludes_dirs_and_files(repo: Path):
    (repo / ".gitignore").write_text(".scratch/\ndraft.md\n", encoding="utf-8")
    (repo / ".scratch").mkdir()
    (repo / ".scratch" / "report.md").write_text("ephemeral", encoding="utf-8")
    (repo / "draft.md").write_text("draft", encoding="utf-8")
    (repo / "keep.md").write_text("keep", encoding="utf-8")
    found = {p.name for p in gm.iter_md(repo)}
    assert "report.md" not in found
    assert "draft.md" not in found
    assert "keep.md" in found


def test_gitignore_wildcard(repo: Path):
    (repo / ".gitignore").write_text("*-map.html\n", encoding="utf-8")
    (repo / "notes.md").write_text("notes", encoding="utf-8")
    dir_pats, file_pats, path_pats, unsupported = gm.parse_gitignore(repo)
    assert dir_pats == [] and path_pats == [] and unsupported == []
    assert file_pats == ["*-map.html"]
    assert gm._wild_match("docs-map.html", "*-map.html")
    assert not gm._wild_match("notes.md", "*-map.html")


def test_gitignore_path_rules_are_not_dropped(repo: Path):
    """Репро баг-репорта 2026-09-15: правила с путём терялись молча.

    Правило с '/' и без хвостового слэша не попадало ни в один список, а шаблон
    каталога с путём не матчился никогда — индекс набирал мусор из бэкапов.
    """
    (repo / ".gitignore").write_text(
        "build/\n.zcode/plugins/\n.zcode/.backup-*\ndrafts/secret.md\n", encoding="utf-8")
    for rel in ("docs/live.md", ".zcode/plugins/x.md", "drafts/secret.md", "build/b.md",
                ".zcode/.backup-20260101-000000/rules/r.md"):
        path = repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("текст", encoding="utf-8")

    hidden = (".zcode/plugins/x.md", "drafts/secret.md", "build/b.md",
              ".zcode/.backup-20260101-000000/rules/r.md")
    for source in (gm.iter_md_fallback, gm.iter_md):
        found = {p.relative_to(repo).as_posix() for p in source(repo)}
        assert "docs/live.md" in found, f"{source.__name__}: живой документ потерян"
        for rel in hidden:
            assert rel not in found, f"{source.__name__}: {rel} попало в список"


def test_iter_md_takes_the_list_from_git(repo: Path):
    """Основной путь — git: он понимает и вложенные .gitignore, чего фолбэк не умеет."""
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    (repo / "docs" / "nested").mkdir()
    (repo / "docs" / "nested" / ".gitignore").write_text("hidden.md\n", encoding="utf-8")
    (repo / "docs" / "nested" / "hidden.md").write_text("скрытый", encoding="utf-8")
    (repo / "docs" / "nested" / "shown.md").write_text("видимый", encoding="utf-8")

    assert gm.git_md_files(repo) is not None, "в репозитории список обязан приходить от git"
    found = {p.relative_to(repo).as_posix() for p in gm.iter_md(repo)}
    assert "docs/nested/shown.md" in found
    assert "docs/nested/hidden.md" not in found


def test_unsupported_rules_warn_when_git_is_absent(repo: Path, monkeypatch):
    """Без git фолбэк не исполняет негативы и '**' — обязан сказать вслух."""
    (repo / ".gitignore").write_text("!keep.md\n**/generated\n", encoding="utf-8")
    monkeypatch.setattr(gm, "git_md_files", lambda root: None)

    warnings = gm.gitignore_warnings(repo)

    assert any("!keep.md" in w for w in warnings)
    assert any("**/generated" in w for w in warnings)


def test_no_gitignore_warnings_on_the_git_path(repo: Path):
    """На основном пути подмножество не задействовано — предупреждать не о чем."""
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    (repo / ".gitignore").write_text("!keep.md\n", encoding="utf-8")

    assert gm.gitignore_warnings(repo) == []


# ── inventory: генерация и идемпотентность ─────────────────────────

def test_inventory_generates_tables(repo: Path):
    r = gm.cmd_inventory(repo)
    assert set(r["changed"]) == {"commands", "skills"}
    text = (repo / "docs" / "reference" / "commands.md").read_text(encoding="utf-8")
    assert "| `/foo` |" in _between(text, "commands")
    assert "| `test-skill` |" in _between(text, "skills")
    # вне маркеров файл не тронут
    assert "## `/foo` — test command" in text


def test_inventory_idempotent(repo: Path):
    gm.cmd_inventory(repo)
    before = (repo / "docs" / "reference" / "commands.md").read_text(encoding="utf-8")
    r = gm.cmd_inventory(repo)
    assert r["changed"] == []
    assert (repo / "docs" / "reference" / "commands.md").read_text(encoding="utf-8") == before


# ── inventory --check: поимка рассинхрона ──────────────────────────

def test_check_clean_after_generate(repo: Path):
    gm.cmd_inventory(repo)
    assert gm.cmd_inventory(repo, check=True)["issues"] == []


def test_check_catches_missing_frontmatter_fields(repo: Path):
    gm.cmd_inventory(repo)
    # убираем args:/drives: у команды
    (repo / ".zcode" / "commands" / "foo.md").write_text(
        "---\ndescription: Test command for the registry.\n---\n\nBody.\n", encoding="utf-8")
    issues = gm.cmd_inventory(repo, check=True)["issues"]
    msgs = " ".join(m for _, m in issues)
    assert "args:" in msgs and "drives:" in msgs


def test_check_catches_missing_section(repo: Path):
    gm.cmd_inventory(repo)
    reg = repo / "docs" / "reference" / "commands.md"
    reg.write_text(reg.read_text(encoding="utf-8").replace("## `/foo` — test command", "## `/bar`"),
                   encoding="utf-8")
    issues = gm.cmd_inventory(repo, check=True)["issues"]
    msgs = " ".join(m for _, m in issues)
    assert "/foo" in msgs and "/bar" in msgs


def test_check_catches_stale_table(repo: Path):
    gm.cmd_inventory(repo)
    reg = repo / "docs" / "reference" / "commands.md"
    reg.write_text(reg.read_text(encoding="utf-8").replace("| `/foo` |", "| `/foo` | STALE"),
                   encoding="utf-8")
    issues = gm.cmd_inventory(repo, check=True)["issues"]
    assert any("рассинхронизирована" in m for _, m in issues)


# ── I7 в lint ──────────────────────────────────────────────────────

def test_lint_reports_i7_on_desync(repo: Path):
    # маркеры пусты, секции нет → рассинхрон
    r = gm.cmd_lint(repo)
    i7 = [i for i in r["issues"] if i[1] == "I7"]
    assert i7 and all(lvl == "ERR" for lvl, *_ in i7)
    # после генерации реестр синхронен (секция `/foo` уже в шаблоне) → I7 чист
    gm.cmd_inventory(repo)
    r = gm.cmd_lint(repo)
    assert [i for i in r["issues"] if i[1] == "I7"] == []


# ── frontmatter: вложенный блок links ──────────────────────────────

def test_parse_frontmatter_nested_links_inline():
    fm = gm.parse_frontmatter(
        "---\nnode_type: runbook\ntitle: T\n"
        "links:\n  part_of: [../README.md]\n  relates_to: [a.md, b.md]\n---\n"
    )
    assert fm["links"] == {"part_of": ["../README.md"], "relates_to": ["a.md", "b.md"]}
    assert "part_of" not in fm


def test_parse_frontmatter_nested_links_block_list():
    fm = gm.parse_frontmatter("---\nlinks:\n  relates_to:\n    - a.md\n    - b.md\n---\n")
    assert fm["links"] == {"relates_to": ["a.md", "b.md"]}


def test_parse_frontmatter_scalar_after_links_stays_on_top():
    fm = gm.parse_frontmatter("---\nlinks:\n  part_of: [README.md]\nstatus: active\n---\n")
    assert fm["links"] == {"part_of": ["README.md"]}
    assert fm["status"] == "active"


def test_parse_frontmatter_top_level_list_still_works():
    fm = gm.parse_frontmatter("---\ntags:\n  - a\n  - b\n---\n")
    assert fm["tags"] == ["a", "b"]


def test_lint_does_not_call_a_frontmatter_linked_doc_an_orphan(tmp_path: Path):
    """Документ со связями только во frontmatter — не сирота (I3)."""
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "README.md").write_text(
        "---\nnode_type: index\ntitle: KB\n---\n\n# KB\n", encoding="utf-8")
    (tmp_path / "docs" / "note.md").write_text(
        "---\nnode_type: runbook\ntitle: Заметка\nlinks:\n  part_of: [README.md]\n---\n\n# Заметка\n",
        encoding="utf-8")
    r = gm.cmd_lint(tmp_path)
    assert [i for i in r["issues"] if i[1] == "I3"] == []


# ── резолв: мягкий (граф) и строгий (линт) ─────────────────────────

def _fs_fixture(tmp_path: Path) -> Path:
    """KB с каталогом, `.md` и файлом кода — цели всех видов."""
    (tmp_path / "docs" / "ops").mkdir(parents=True)
    (tmp_path / "docs" / "README.md").write_text("# KB\n", encoding="utf-8")
    (tmp_path / "docs" / "ops" / "dev-contour.md").write_text("# Контур\n", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "module.bsl").write_text("// код\n", encoding="utf-8")
    (tmp_path / "my file.md").write_text("# Пробел\n", encoding="utf-8")
    return tmp_path


def test_fs_resolve_checks_directories_and_non_md_files(tmp_path: Path):
    """Строгая цель — не только `.md`: каталог и файл кода проверяются так же."""
    root = _fs_fixture(tmp_path)
    assert gm.fs_resolve(root, "docs/README.md", "ops")[0] is True
    assert gm.fs_resolve(root, "docs/README.md", "../src/module.bsl")[0] is True
    assert gm.fs_resolve(root, "docs/README.md", "../src/gone.bsl")[0] is False
    assert gm.fs_resolve(root, "docs/README.md", "ops/gone")[0] is False


def test_fs_resolve_decodes_url_encoding_and_strips_selectors(tmp_path: Path):
    """`%20`, `:строки` и `#якорь` срезаются до проверки — как их видит читатель."""
    root = _fs_fixture(tmp_path)
    assert gm.fs_resolve(root, "docs/README.md", "../my%20file.md")[0] is True
    assert gm.fs_resolve(root, "docs/README.md", "../my file.md:12-34")[0] is True
    assert gm.fs_resolve(root, "docs/README.md", "ops/dev-contour.md#шаг")[0] is True


def test_fs_resolve_checks_a_path_that_leaves_the_repo(tmp_path: Path):
    """Ссылка за корень репозитория проверяется там, куда ведёт: KB читается
    в многорепозиторной раскладке, соседний репозиторий — рабочая цель."""
    root = tmp_path / "repo"
    (root / "docs").mkdir(parents=True)
    (root / "docs" / "README.md").write_text("# KB\n", encoding="utf-8")
    (tmp_path / "sibling").mkdir()
    (tmp_path / "sibling" / "note.md").write_text("# Сосед\n", encoding="utf-8")
    assert gm.fs_resolve(root, "docs/README.md", "../../sibling/note.md")[0] is True
    assert gm.fs_resolve(root, "docs/README.md", "../../nowhere/note.md")[0] is False


def test_fs_resolve_unwraps_an_angle_bracket_destination(tmp_path: Path):
    """`[x](</abs/path.pdf>)` — корне-абсолютная цель в обёртке: вне проверки."""
    root = _fs_fixture(tmp_path)
    assert gm.fs_resolve(root, "docs/README.md", "</home/nobody/file.pdf>") == (True, None)


def test_fs_resolve_skips_external_anchors_and_root_absolute(tmp_path: Path):
    """Внешние URI, якоря и `/…` — вне проверки: вердикт по ним не выносится."""
    root = _fs_fixture(tmp_path)
    for href in ("https://example.com/x.md", "mailto:a@b.c", "#якорь", "/docs/README.md"):
        assert gm.fs_resolve(root, "docs/README.md", href) == (True, None)


def _link_fixture(tmp_path: Path, href: str) -> Path:
    """KB из трёх документов, где ссылка из docs/reference/ ведёт на CONTEXT.md."""
    (tmp_path / "docs" / "reference").mkdir(parents=True)
    (tmp_path / "docs" / "README.md").write_text(
        "---\nnode_type: index\ntitle: KB\n---\n\n# KB\n", encoding="utf-8")
    (tmp_path / "CONTEXT.md").write_text(
        "---\nnode_type: reference\ntitle: Контекст\n---\n\n# Контекст\n", encoding="utf-8")
    (tmp_path / "docs" / "reference" / "README.md").write_text(
        f"---\nnode_type: index\ntitle: Reference\n---\n\n# Reference\n\n[CONTEXT]({href})\n",
        encoding="utf-8")
    return tmp_path


def test_lint_catches_a_link_that_only_the_basename_saves(tmp_path: Path):
    """I4 ловит ссылку, которую вытягивает только совпадение по имени файла."""
    repo = _link_fixture(tmp_path, "../CONTEXT.md")
    r = gm.cmd_lint(repo)
    assert [i for i in r["issues"] if i[1] == "I4"] != []


def test_lint_accepts_a_link_that_resolves_exactly(tmp_path: Path):
    """I4 молчит на точной ссылке — и на файл, и на папку."""
    repo = _link_fixture(tmp_path, "../../CONTEXT.md")
    r = gm.cmd_lint(repo)
    assert [i for i in r["issues"] if i[1] == "I4"] == []


def test_lint_skips_a_root_absolute_link(tmp_path: Path):
    """Корне-абсолютные `/…` вне проверки: у формы нет единого читательского смысла
    (VS Code и Obsidian разрешают от корня, GitHub — как site-absolute)."""
    repo = _link_fixture(tmp_path, "/docs/README.md")
    r = gm.cmd_lint(repo)
    assert [i for i in r["issues"] if i[1] == "I4"] == []


def test_lint_hints_the_target_the_basename_would_save(tmp_path: Path):
    """Подсказка называет цель мягкого резолва — случай zupupr: `dev-contour.md`
    из `docs/reference/` при файле в `docs/ops/`."""
    (tmp_path / "docs" / "reference").mkdir(parents=True)
    (tmp_path / "docs" / "ops").mkdir(parents=True)
    (tmp_path / "docs" / "README.md").write_text(
        "---\nnode_type: index\ntitle: KB\n---\n\n# KB\n", encoding="utf-8")
    (tmp_path / "docs" / "ops" / "dev-contour.md").write_text(
        "---\nnode_type: runbook\ntitle: Контур\n---\n\n# Контур\n", encoding="utf-8")
    (tmp_path / "docs" / "reference" / "configuration.md").write_text(
        "---\nnode_type: reference\ntitle: Настройка\n---\n\n[контур](dev-contour.md)\n",
        encoding="utf-8")
    r = gm.cmd_lint(tmp_path)
    msgs = [i[3] for i in r["issues"] if i[1] == "I4"]
    assert len(msgs) == 1 and "docs/ops/dev-contour.md" in msgs[0]


def test_lint_catches_broken_body_and_frontmatter_links(tmp_path: Path):
    """Приёмка: тело + `documents` + `depends_on` битые → ровно 3 ERR I4."""
    (tmp_path / "docs" / "reference").mkdir(parents=True)
    (tmp_path / "docs" / "README.md").write_text(
        "---\nnode_type: index\ntitle: KB\n---\n\n# KB\n", encoding="utf-8")
    (tmp_path / "docs" / "reference" / "README.md").write_text(
        "---\nnode_type: index\ntitle: Reference\n---\n\n# Reference\n", encoding="utf-8")
    (tmp_path / "docs" / "reference" / "note.md").write_text(
        "---\nnode_type: reference\ntitle: Заметка\nservice: _platform\n"
        "links:\n  documents: [../../nope_does_not_exist]\n"
        "  depends_on: [../missing_doc.md]\n---\n\n"
        "Тело: [битая ссылка](../../nope2.md)\n", encoding="utf-8")
    r = gm.cmd_lint(tmp_path)
    i4 = [i for i in r["issues"] if i[1] == "I4"]
    assert len(i4) == 3, i4
    assert any("documents:" in i[3] for i in i4) and any("depends_on:" in i[3] for i in i4)


def test_lint_checks_non_md_targets(tmp_path: Path):
    """Ссылка на файл кода проверяется так же, как на `.md`."""
    (tmp_path / "docs").mkdir()
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "module.bsl").write_text("// код\n", encoding="utf-8")
    (tmp_path / "docs" / "README.md").write_text(
        "---\nnode_type: index\ntitle: KB\n---\n\n# KB\n"
        "[код](../src/module.bsl) · [нет](../src/gone.bsl)\n", encoding="utf-8")
    r = gm.cmd_lint(tmp_path)
    msgs = [i[3] for i in r["issues"] if i[1] == "I4"]
    assert len(msgs) == 1 and "gone.bsl" in msgs[0]


def test_lint_ignores_a_link_title(tmp_path: Path):
    """`[x](doc.md "подсказка")` — валидная ссылка, а не битая."""
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "README.md").write_text(
        "---\nnode_type: index\ntitle: KB\n---\n\n# KB\n", encoding="utf-8")
    (tmp_path / "docs" / "note.md").write_text(
        "---\nnode_type: reference\ntitle: Заметка\n---\n\n"
        '[README](README.md "индекс папки")\n', encoding="utf-8")
    r = gm.cmd_lint(tmp_path)
    assert [i for i in r["issues"] if i[1] == "I4"] == []


def test_lint_catches_a_scalar_supersedes(tmp_path: Path):
    """`supersedes:` скаляром — не молчаливый пропуск: I6 проверяет и его."""
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "README.md").write_text(
        "---\nnode_type: index\ntitle: KB\n---\n\n# KB\n", encoding="utf-8")
    (tmp_path / "docs" / "old.md").write_text(
        "---\nnode_type: reference\ntitle: Старое\nstatus: active\n---\n\n# Старое\n",
        encoding="utf-8")
    (tmp_path / "docs" / "new.md").write_text(
        "---\nnode_type: reference\ntitle: Новое\nlinks:\n  supersedes: old.md\n---\n\n"
        "# Новое\n", encoding="utf-8")
    r = gm.cmd_lint(tmp_path)
    assert [i for i in r["issues"] if i[1] == "I6"] != []


# ── схемы карточек (I9) и словарь типов из онтологии ───────────────

ONTOLOGY = """# GitMark ontology

## Semantic layer

| node_type | what it is | lives in |
|---|---|---|
| `reference` | a spec | `docs/reference/` |
| `index` | a folder index | any `README.md` |
| `schema` | a card schema | the cards' folder |
| `wallet` | a wallet card | `wallets/` |
"""


def _cards_fixture(tmp_path: Path) -> Path:
    """KB с папкой карточек: схема кошелька и одна соответствующая карточка."""
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "README.md").write_text("# KB\n", encoding="utf-8")
    (tmp_path / "docs" / "ontology.md").write_text(ONTOLOGY, encoding="utf-8")
    (tmp_path / "wallets").mkdir()
    (tmp_path / "wallets" / "README.md").write_text("# Кошельки\n", encoding="utf-8")
    (tmp_path / "wallets" / "_schema.md").write_text(
        "---\nnode_type: schema\ntitle: Кошелёк\ncard_type: wallet\n"
        "required: [uid, kind, balance]\n"
        'values: ["kind: карта|счёт"]\n---\n\n# Схема\n', encoding="utf-8")
    (tmp_path / "wallets" / "main.md").write_text(
        "---\nnode_type: wallet\ntitle: Основной\nuid: main\nkind: карта\n"
        "balance: 100\n---\n\nПроза вольная: схема её не ограничивает.\n", encoding="utf-8")
    return tmp_path


def test_lint_reads_node_types_from_the_ontology(tmp_path: Path):
    """Словарь типов — из таблицы онтологии: тип из неё проходит, вне её — ERR."""
    repo = _cards_fixture(tmp_path)
    (repo / "docs" / "reference").mkdir()
    doc = repo / "docs" / "reference" / "README.md"
    doc.write_text("---\nnode_type: wallet\ntitle: Док\n---\n\n# Док\n", encoding="utf-8")
    assert [i for i in gm.cmd_lint(repo)["issues"] if i[1] == "I2"] == []
    doc.write_text("---\nnode_type: nosuchtype\ntitle: Док\n---\n\n# Док\n", encoding="utf-8")
    assert [i for i in gm.cmd_lint(repo)["issues"]
            if i[1] == "I2" and "вне словаря" in i[3]] != []


def test_node_types_fall_back_without_an_ontology(tmp_path: Path):
    """Онтологии нет — словарь типов берётся из фолбэк-константы."""
    (tmp_path / "docs").mkdir()
    assert gm.node_types(tmp_path) == gm.NODE_TYPES


def test_lint_requires_declared_type_in_a_card_folder(tmp_path: Path):
    """Карточка без node_type в папке со схемой — ошибка, а не тихий пропуск."""
    repo = _cards_fixture(tmp_path)
    (repo / "wallets" / "bare.md").write_text(
        "---\ntitle: Без типа\n---\n\nПроза.\n", encoding="utf-8")
    msgs = [i[3] for i in gm.cmd_lint(repo)["issues"] if i[1] == "I9"]
    assert any("без объявленного типа" in m for m in msgs)


def test_lint_reports_a_type_the_folder_schema_does_not_declare(tmp_path: Path):
    """Тип, не объявленный схемой папки, — ошибка: карточка не выбирает схему сама."""
    repo = _cards_fixture(tmp_path)
    (repo / "wallets" / "alien.md").write_text(
        "---\nnode_type: reference\ntitle: Чужой\n---\n\nПроза.\n", encoding="utf-8")
    msgs = [i[3] for i in gm.cmd_lint(repo)["issues"] if i[1] == "I9"]
    assert any("не объявлен схемой" in m for m in msgs)


def test_lint_requires_schema_fields(tmp_path: Path):
    """Нет обязательного поля — ERR с именем поля."""
    repo = _cards_fixture(tmp_path)
    (repo / "wallets" / "no-kind.md").write_text(
        "---\nnode_type: wallet\ntitle: Без вида\nuid: x\nbalance: 1\n---\n\nПроза.\n",
        encoding="utf-8")
    assert [i[3] for i in gm.cmd_lint(repo)["issues"] if i[1] == "I9"] == [
        "нет обязательного поля: kind"]


def test_lint_keeps_schema_values_within_the_list(tmp_path: Path):
    """Значение вне списка схемы — ERR с именем поля."""
    repo = _cards_fixture(tmp_path)
    (repo / "wallets" / "bad-kind.md").write_text(
        "---\nnode_type: wallet\ntitle: Плохой\nuid: y\nkind: наличные\nbalance: 2\n---\n\nПроза.\n",
        encoding="utf-8")
    msgs = [i[3] for i in gm.cmd_lint(repo)["issues"] if i[1] == "I9"]
    assert any("поле kind" in m and "вне списка" in m for m in msgs)


def test_lint_leaves_a_conforming_card_and_its_prose_alone(tmp_path: Path):
    """Соответствующая карточка проходит: README и схема — не карточки, проза свободна."""
    repo = _cards_fixture(tmp_path)
    assert [i for i in gm.cmd_lint(repo)["issues"] if i[1] == "I9"] == []
