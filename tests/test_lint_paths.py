"""Тикет queue-3/02: lint валидирует path-аргументы (гейт r1/r2).

Два guard'а закрывают один вред — молчаливую пустую выборку с «✓ чисто»:
несуществующий путь («путь не найден») и существующий, но не совпадающий
строкой ни с одним rel — каталог, «./»-префикс, абсолютный, gitignored,
пустая строка («путь не выбирает ни одного файла KB»). CLI печатает отказ в
stderr с exit 2 (usage-класс, отделён от exit 1 = ERR при --strict) и вырезает
управляющие из сообщения: C0/DEL и C1 U+0080–U+009F, включая переводы строк
(argv — недоверенный текст на границе вывода).

Семантика фильтра запинена представителями обеих семей: per-file I1/I2/I3/I6
сужаются выборкой, сквозные I4/I5/I7/I9/I10 и счётчик checked всегда весь KB.
I8 не пинится кейсом: требует онтологию-близнеца пакета, в tmp-фикстуре
структурно недостижим; его семья вне-выборочных вызовов закрыта I7/I9/I10.
Ловушки на мутации — ассертами точных сообщений и поведенческим кейсом
except-оговорки CLI; живые мутации обоих guard'ов прогнаны в тикете.
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
import unicodedata
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
    (docs / "ops").mkdir()
    (docs / "notes").mkdir()
    (docs / "services").mkdir()
    (docs / "README.md").write_text(
        "---\nnode_type: index\ntitle: KB\n---\n\n# KB\n", encoding="utf-8")
    (docs / "reference" / "README.md").write_text(
        "---\nnode_type: index\ntitle: Reference\n---\n\n# Reference\n", encoding="utf-8")
    # aa — карта с I2 (node_type вне словаря): единственный выбранный файл
    (docs / "reference" / "aa.md").write_text(
        "---\nnode_type: bogus_type\ntitle: AA\n---\n\n# AA\n", encoding="utf-8")
    # bb — I2 + I6 (supersedes aa, тот не deprecated) вне выборки: per-file
    (docs / "reference" / "bb.md").write_text(
        "---\nnode_type: bogus_type\ntitle: BB\nlinks:\n  supersedes: [aa.md]\n---\n\n# BB\n",
        encoding="utf-8")
    # cc — битая ссылка (I4, сквозная) и сирота (I3, per-file): один файл
    # демонстрирует обе семьи сразу
    (docs / "reference" / "cc.md").write_text(
        "---\nnode_type: reference\ntitle: CC\n---\n\n[битая](./nope.md)\n", encoding="utf-8")
    # dd — gitignored: существует на диске, но iter_md его не выдаёт (fallback
    # чтает .gitignore) — единственная форма, отличающая rel-индекс от диска
    (docs / "reference" / "dd.md").write_text(
        "---\nnode_type: reference\ntitle: DD\n---\n\n# DD\n", encoding="utf-8")
    (tmp_path / ".gitignore").write_text("docs/reference/dd.md\n", encoding="utf-8")
    # xx — I1: несущий docs/ops/ без frontmatter (per-file)
    (docs / "ops" / "xx.md").write_text("# XX без frontmatter\n", encoding="utf-8")
    # notes/ без README — I5 (сквозная) для обеих папок без индекса
    (docs / "notes" / "n1.md").write_text("# N1\n", encoding="utf-8")
    # карточка вне списка значений схемы — I9 (сквозная), невыбираемая выборкой
    (docs / "services" / "_schema.md").write_text(
        "---\nnode_type: schema\ncard_type: card\nrequired: [env]\n"
        "values: env: prod|stage\nlinks:\n  relates_to: [../README.md]\n---\n\n# Схема\n",
        encoding="utf-8")
    (docs / "services" / "cards.md").write_text(
        "---\nnode_type: card\ntitle: Карточка\nservice: demo\nstatus: active\n"
        "card_type: card\nenv: bogus_env\nlinks:\n  relates_to: [../README.md]\n---\n\n# Карточка\n",
        encoding="utf-8")
    return tmp_path


# ── отказ по несуществующему пути (движок, первый guard) ────────────


def test_nonexistent_path_named_refusal(kb: Path):
    with pytest.raises(gm.LintPathError, match="docs/plans/nope\\.md") as ei:
        gm.cmd_lint(kb, ["docs/plans/nope.md"])
    assert str(ei.value).startswith("путь не найден: ")


def test_every_missing_path_is_named(kb: Path):
    with pytest.raises(gm.LintPathError) as ei:
        gm.cmd_lint(kb, ["docs/aa-nope.md", "docs/bb-nope.md"])
    assert "docs/aa-nope.md" in str(ei.value) and "docs/bb-nope.md" in str(ei.value)


def test_refusal_class_is_not_catch_all_valueerror():
    """Отказ — именованный класс: будущий ValueError внутри lint-логики не
    переклассифицируется CLI в usage-отказ (ловится только LintPathError)."""
    assert issubclass(gm.LintPathError, ValueError)
    assert gm.LintPathError is not ValueError


def test_cli_catches_only_lintpatherror_behaviorally(kb: Path, monkeypatch, capsys):
    """Поведенческий мутант-ловушка на except-оговорку main: плоский ValueError
    из тела lint обязан вылететь трейсбеком (внутренняя ошибка), а не стать
    «gitmark: …» exit 2; LintPathError — обязан стать SystemExit(2)."""
    def _boom(root, paths=None):
        raise ValueError("внутренняя проба: симуляция будущего бага в теле lint")

    monkeypatch.setattr(gm, "cmd_lint", _boom)
    with pytest.raises(ValueError, match="внутренняя проба"):
        gm.main(["--root", str(kb), "lint", "docs/reference/aa.md"])
    out = capsys.readouterr()
    assert "gitmark:" not in out.err, "плоский ValueError переклассифицирован в usage-отказ"

    def _refuse(root, paths=None):
        raise gm.LintPathError("путь не найден: docs/reference/aa.md")

    monkeypatch.setattr(gm, "cmd_lint", _refuse)
    with pytest.raises(SystemExit) as ei:
        gm.main(["--root", str(kb), "lint", "docs/reference/aa.md"])
    assert ei.value.code == 2


# ── отказ по существующему, но невыбираемому пути (второй guard) ────


@pytest.mark.parametrize("bad,shown", [
    ("docs/reference", "docs/reference"),          # каталог
    ("./docs/reference/aa.md", "./docs/reference/aa.md"),  # «./»-префикс
    ("/etc/passwd", "/etc/passwd"),                # абсолютный путь вне KB
    ("", "(пустой аргумент)"),                     # пустая строка (существует как root)
    ("docs/reference/dd.md", "docs/reference/dd.md"),  # gitignored: на диске есть, в iter_md нет
])
def test_existing_but_unselectable_path_refuses(kb: Path, bad: str, shown: str):
    with pytest.raises(gm.LintPathError, match="не выбирает ни одного файла KB") as ei:
        gm.cmd_lint(kb, [bad])
    assert shown in str(ei.value)


def test_whitespace_only_argument_gets_placeholder(kb: Path):
    """Вырожденный аргумент guard 1 — та же заглушка, что у guard 2: без неё
    C0-стрип делал бы имя невидимым («путь не найден: » с табом)."""
    with pytest.raises(gm.LintPathError) as ei:
        gm.cmd_lint(kb, ["\t"])
    assert "(пустой аргумент)" in str(ei.value)


def test_stat_failure_hands_decision_to_guard2(kb: Path, monkeypatch):
    """EACCES/stat-отказ по argv-пути: guard 1 не называет путь «не найден» и
    не крашится — решение уходит guard 2 по rel-индексу (ловушка на мутанты
    ok=True→ok=False и снятый try/except)."""
    orig = gm.Path.exists

    def raising(self, _orig=orig):
        if self.as_posix().endswith("docs/secret.md"):
            raise PermissionError(13, "Permission denied")
        return _orig(self)

    monkeypatch.setattr(gm.Path, "exists", raising)
    with pytest.raises(gm.LintPathError, match="не выбирает ни одного файла KB") as ei:
        gm.cmd_lint(kb, ["docs/secret.md"])
    assert "docs/secret.md" in str(ei.value)


def test_unicode_forms_are_byte_exact(kb: Path):
    """Выборка байт-точная — как sel-фильтр до правки: NFD-имя на диске
    выбирается своей формой; NFC-форма того же слова — честный отказ guard 1
    (файла с такими байтами на ФС нет). Нормализация argv — именованное
    ограничение: отказ с именем пути вместо молчаливой пустоты."""
    word_nfd = unicodedata.normalize("NFD", "ёмкость")  # е + U+0308
    (kb / "docs" / "notes" / (word_nfd + ".md")).write_text("# Ё\n", encoding="utf-8")
    nfd = "docs/notes/" + word_nfd + ".md"
    nfc = "docs/notes/" + unicodedata.normalize("NFC", "ёмкость") + ".md"
    r = gm.cmd_lint(kb, [nfd])
    assert isinstance(r, dict), "байт-в-байт совпавшая форма обязана выбирать"
    with pytest.raises(gm.LintPathError, match="путь не найден") as ei:
        gm.cmd_lint(kb, [nfc])
    assert nfc in str(ei.value)


def test_mixed_paths_refuse_naming_only_missing(kb: Path):
    with pytest.raises(gm.LintPathError) as ei:
        gm.cmd_lint(kb, ["docs/reference/aa.md", "docs/nope.md"])
    msg = str(ei.value)
    assert "docs/nope.md" in msg and "путь не найден" in msg
    assert "docs/reference/aa.md" not in msg


def test_canonical_path_does_not_refuse(kb: Path):
    r = gm.cmd_lint(kb, ["docs/reference/aa.md"])
    assert isinstance(r, dict) and r["checked"] > 0


# ── семантика фильтра по существующим путям, представителями семей ──


def test_selection_narrows_only_per_file_checks(kb: Path):
    """Per-file I1/I2/I3/I6 сужаются выборкой; сквозные I4/I5/I7/I9/I10 и
    счётчик checked идут по всему KB; сводка считает весь KB и при выборке."""
    r = gm.cmd_lint(kb, ["docs/reference/aa.md"])
    codes = lambda rel, code: any(i[2] == rel and i[1] == code for i in r["issues"])
    # выбранный файл проверен; невыбранные per-file (I1/I2/I3/I6) скрыты
    assert codes("docs/reference/aa.md", "I2"), "выбранный файл не проверен"
    assert not codes("docs/reference/bb.md", "I2"), "I2 вышел за выборку"
    assert not codes("docs/ops/xx.md", "I1"), "I1 вышел за выборку"
    assert not codes("docs/reference/cc.md", "I3"), "I3 вышел за выборку"
    assert not codes("docs/reference/bb.md", "I6"), "I6 вышел за выборку"
    # сквозные — по всему KB, включая невыбранные файлы
    assert codes("docs/reference/cc.md", "I4"), "I4 граф обязан идти по всему KB"
    assert any(i[1] == "I5" and i[2] in ("docs/notes/", "docs/ops/") for i in r["issues"]), \
        "I5 README папок обязан идти по всему KB"
    assert any(i[1] == "I7" for i in r["issues"]), "I7 реестр обязан идти по всему KB"
    assert any(i[1] == "I9" and i[2] == "docs/services/cards.md" for i in r["issues"]), \
        "I9 схема карточек обязана идти по всему KB"
    assert any(i[1] == "I10" for i in r["issues"]), "I10 цепочка индексов — весь KB"
    assert r["checked"] == len(list(gm.iter_md(kb))), \
        "сводка обязана считать весь KB и при выборке"


def test_full_run_reports_all_per_file_issues(kb: Path):
    """Без paths все per-file находки на месте — фильтр скрывал их, а не чинил."""
    r = gm.cmd_lint(kb)
    codes = lambda rel, code: any(i[2] == rel and i[1] == code for i in r["issues"])
    assert codes("docs/reference/aa.md", "I2") and codes("docs/reference/bb.md", "I2")
    assert codes("docs/ops/xx.md", "I1") and codes("docs/reference/cc.md", "I3")
    assert codes("docs/reference/bb.md", "I6")


# ── CLI E2E: exit-коды, каналы вывода, гигиена сообщения ────────────


def _run(kb: Path, *argv: str):
    return subprocess.run(
        [sys.executable, str(_GITMARK), "--root", str(kb), "lint", *argv],
        capture_output=True, text=True, timeout=60,
    )


def test_cli_refusal_exit2_stderr_stdout_empty(kb: Path):
    """Сценарий тикета: отказ до единой проверки — stdout пуст (ни issues,
    ни строки успеха «✓ чисто»), сообщение в stderr, exit 2 под --strict."""
    r = _run(kb, "--strict", "docs/plans/nope.md")
    assert r.returncode == 2, f"rc={r.returncode}, stderr={r.stderr!r}"
    assert "gitmark: путь не найден: docs/plans/nope.md" in r.stderr
    assert r.stdout == "", "отказ не должен печатать ничего в stdout"
    assert "чисто" not in r.stdout + r.stderr


def test_cli_refusal_without_strict_is_still_exit2(kb: Path):
    """exit 2 — безусловный usage-класс, не только при --strict (ловушка на
    мутанта «path-аргументы действуют только со --strict»)."""
    r = _run(kb, "docs/plans/nope.md")
    assert r.returncode == 2, f"без --strict отказ обязан оставаться rc 2, rc={r.returncode}"
    assert "gitmark: путь не найден: docs/plans/nope.md" in r.stderr


def test_cli_dir_argument_refuses_instead_of_silent_clean(kb: Path):
    """Каталог — исходный вред «тихий пустой прогон»: отказ, а не «✓ чисто»."""
    r = _run(kb, "--strict", "docs/reference")
    assert r.returncode == 2
    assert "gitmark: путь не выбирает ни одного файла KB: docs/reference" in r.stderr
    assert r.stdout == "" and "чисто" not in r.stderr


def test_cli_mixed_paths_exit2(kb: Path):
    r = _run(kb, "--strict", "docs/reference/aa.md", "docs/nope.md")
    assert r.returncode == 2
    assert "docs/nope.md" in r.stderr and "docs/reference/aa.md" not in r.stderr


def test_cli_control_chars_stripped_from_refusal(kb: Path):
    """argv-путь — недоверенный текст на границе вывода: C0/DEL и C1-управляющие
    вырезаются из сообщения (ESC-инъекция экрана, 8-битный CSI U+009B,
    подделка строки отчёта через \\n, DEL \\x7f)."""
    r = subprocess.run(
        [sys.executable, str(_GITMARK), "--root", str(kb), "lint",
         "docs/\x1b[2J\x7f\u009bfake\nERR I9 подделка-nope"],
        capture_output=True, timeout=60,
    )
    assert r.returncode == 2
    for raw, name in ((b"\x1b", "ESC"), (b"\x7f", "DEL"), ("\u009b".encode(), "C1 CSI")):
        assert raw not in r.stderr, f"{name}-байт дошёл до stderr"
    assert r.stderr.count(b"\n") == 1, "перевод строки подделал вторую строку"
    assert b"\nERR" not in r.stderr, "подделанная строка отчёта встала началом строки"
    # печатный остаток argv пережил стрип — ловушка на мутантов условной
    # перезачистки «при наличии управляющих» (заглушка/класс, сносящий кириллицу)
    assert b"docs/" in r.stderr and b"fake" in r.stderr, "ASCII-остаток снесён"
    assert "подделка".encode() in r.stderr, "кириллица остатка снесена"


def test_cli_existing_path_keeps_previous_exit_and_channels(kb: Path):
    """Существующий канонический путь: прежний контракт — ошибки в stdout,
    exit 1 только при --strict, сводка всего KB; I4/I5 невыбранных видны."""
    r = _run(kb, "--strict", "docs/reference/aa.md")
    assert r.returncode == 1, f"у грязной выборки под --strict rc=1, получили {r.returncode}"
    assert "node_type='bogus_type' вне словаря" in r.stdout
    assert "docs/reference/cc.md" in r.stdout, "I4 невыбранного файла должен печататься"
    assert "нет README.md" in r.stdout, "I5 невыбранной папки должен печататься"
    assert f"({len(list(gm.iter_md(kb)))} файлов" in r.stdout


def test_cli_without_strict_dirty_kb_still_exit0(kb: Path):
    """Без --strict даже ERR не меняют exit — прежнее поведение сохранено."""
    r = _run(kb, "docs/reference/aa.md")
    assert r.returncode == 0, r.stderr[-500:]
