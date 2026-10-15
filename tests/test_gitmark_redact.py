"""redactLite в выводе gitmark (queue-3/01): мин-редакция секретов на границе
stdout/stderr — msg строк lint и inventory --check, правило .gitignore из
предупреждения фолбэка; пути и счётчики остаются честными.

Живые пробы до фиксы (та же фикстура, что в E2E ниже) доказали три канала
lint: I4 печатает href с ?token=…, I9 печатает значение поля карточки,
I2 печатает service='eyJ…'. inventory/map stdout секретов не несёт по
формату (счётчики и пути) — их каналы документированы в тикете как
осознанные пропуски (реестр-генерат и HTML-рендер корпуса не редактируются).

Матрица зеркалит TS-набор tests/onto_doc_matrix.mjs (redactLite тот же
профиль из onto-doc-hygiene) плюс форматы живых проб. Мутационная проба —
двухслойная: снятие каждого правила по отдельности краснит матрицу
(кейс-ловушка для правила), снятие применения на печати краснит E2E."""
from __future__ import annotations

import importlib.util
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
_GITMARK = REPO / "skills" / "kb-search" / "gitmark.py"
_spec = importlib.util.spec_from_file_location("gitmark_redact", _GITMARK)
gm = importlib.util.module_from_spec(_spec)
sys.modules["gitmark_redact"] = gm
_spec.loader.exec_module(gm)


# (маскировать?, имя, ввод, секрет-подстрока, которой в выводе быть не должно)
REDACT_CASES = [
    (True, "пароль двоеточием", "конфиг: password: FAKEhunter2x", "FAKEhunter2x"),
    (True, "пароль равно", "password=FAKEabcdef123456", "FAKEabcdef123456"),
    (True, "JSON-форма с кавычками", '{"password": "FAKEhunter2x"}', "FAKEhunter2x"),
    (True, "JSON-форма api_key", '{"api_key": "FAKEv1.abc123def456"}', "FAKEv1.abc123def456"),
    (True, "JSON-форма: экранированная кавычка в значении",
     '{"password": "abcd\\"EFSECRET9tail"}', "EFSECRET9tail"),
    (True, "JSON-форма с бэкслешами перед кавычками",
     '\\"password\\": \\"FAKEesc9secret99\\"', "FAKEesc9secret99"),
    (True, "python-repr форма с одинарными кавычками",
     "{'password': 'FAKEpysecret99'}", "FAKEpysecret99"),
    (True, "bearer-литерал", "Authorization: bearer FAKEabc123-def456=", "FAKEabc123-def456="),
    (True, "basic-литерал", "basic RkFLRXVzZXI6RkFLRXBhc3N3b3Jk", "RkFLRXVzZXI6RkFLRXBhc3N3b3Jk"),
    (True, "eyJ JWS целиком", "токен eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.FAKESIG123456 в логе",
     "FAKESIG123456"),
    (True, "vendor sk-", "ключ sk-FAKEa1b2c3d4e5f6", "FAKEa1b2c3d4e5f6"),
    (True, "vendor ghp_ без словарного контекста", "see ghp_FAKETOKEN12 end", "ghp_FAKETOKEN12"),
    (True, "vendor AKIA", "aws AKIAFAKE12345678 key", "AKIAFAKE12345678"),
    # форматы живых проб lint (инвентарь тикета)
    (True, "I2: service-значение вне словаря",
     "service='eyJhbGciOiJIUzI1NiJ9.eyJFAKEsubIn0.FAKESIG99' вне словаря", "FAKESIG99"),
    (True, "I4: битая ссылка с токеном",
     "битая ссылка → ./nope.md?token=ghp_FAKETOKEN12345", "FAKETOKEN12345"),
    (True, "I9: значение поля карточки вне списка",
     "поле token: значение 'sk-FAKEprobe12345' вне списка", "FAKEprobe12345"),
    # негативы: честные строки не искажаются
    (False, "короткое значение — пропуск", "token=abc", ""),
    (False, "auth в прозе — пропуск", "заголовок auth: см. документацию", ""),
    (False, "путь с token в имени", "docs/plans/token-guide.md — нет frontmatter с node_type", ""),
    (False, "счётчики", "5 файлов · I2×2 · I4×1 · 200 KB", ""),
    (False, "русская проза без словарных ключей", "Пароль забыт — восстановление через поддержку", ""),
    (False, "service вне словаря без секрет-формы", "service='demo' вне словаря", ""),
]


@pytest.mark.parametrize("should_mask,name,inp,secret", REDACT_CASES)
def test_redact_matrix(should_mask, name, inp, secret):
    out = gm.redact_lite(inp)
    assert (out != inp) == should_mask, f"[{name}] => {out!r}"
    if should_mask:
        assert secret not in out, f"УТЕЧКА [{name}]: секрет остался в выводе"
    assert gm.redact_lite(out) == out, f"НЕ ИДЕМПОТЕНТНО [{name}]"


def _apply(rules, s):
    for rx, sub in rules:
        s = rx.sub(sub, s)
    return s


def test_mutation_every_rule_has_a_trap():
    """Мутационная проба: у каждого правила есть кейс-ловушка — отключение
    правила (любого одного) оставляет секрет хотя бы в одном выводе."""
    positives = [c for c in REDACT_CASES if c[0]]
    for i in range(len(gm._REDACT_RULES)):
        mutant = gm._REDACT_RULES[:i] + gm._REDACT_RULES[i + 1:]
        traps = [
            name for _, name, inp, secret in positives
            if secret and secret in _apply(mutant, inp)
        ]
        assert traps, (
            f"правило #{i} не ловится матрицей: без него ни один кейс не утекает — "
            "матрица не проверяет это правило"
        )


# ── E2E: живая проба после фиксы — те же три канала, что в инвентаре тикета ──
CARDS_MD = """---
node_type: card
token: sk-FAKEprobe12345
links:
  relates_to: [../README.md]
---
# Карточка
"""
SCHEMA_MD = """---
node_type: schema
card_type: card
required: [token]
values: token: free|locked
links:
  relates_to: [../README.md]
---
# Схема
"""
SERVICE_MD = """---
node_type: service
service: eyJhbGciOiJIUzI1NiJ9.eyJFAKEsubIn0.FAKESIG99
status: active
links:
  relates_to: [../../README.md]
---
# Demo
"""
REFS_MD = """---
node_type: reference
service: _platform
status: active
links:
  relates_to: [../README.md]
---
# Ссылки
Смотри [вестку](./nope.md?token=ghp_FAKETOKEN12345).
"""


@pytest.fixture()
def probe_kb(tmp_path):
    (tmp_path / "docs" / "services" / "demo").mkdir(parents=True)
    (tmp_path / "docs" / "reference").mkdir(parents=True)
    (tmp_path / "docs" / "services" / "cards.md").write_text(CARDS_MD, "utf-8")
    (tmp_path / "docs" / "services" / "_schema.md").write_text(SCHEMA_MD, "utf-8")
    (tmp_path / "docs" / "services" / "demo" / "README.md").write_text(SERVICE_MD, "utf-8")
    (tmp_path / "docs" / "reference" / "refs.md").write_text(REFS_MD, "utf-8")
    (tmp_path / "docs" / "README.md").write_text("# Docs\n\n- [services](services/)\n", "utf-8")
    return tmp_path


def test_lint_stdout_redacted(probe_kb):
    r = subprocess.run(
        [sys.executable, str(_GITMARK), "--root", str(probe_kb), "lint"],
        capture_output=True, text=True, timeout=60,
    )
    out = r.stdout + r.stderr
    for secret in ("FAKEprobe12345", "FAKETOKEN12345", "FAKESIG99", "eyJhbGci"):
        assert secret not in out, f"секрет {secret!r} утёк в вывод lint"
    assert out.count("[REDACTED]") >= 3, "маскировка не применилась к каналам I2/I4/I9"
    # пути и честная проза остаются нетронутыми
    assert "docs/services/cards.md" in out
    assert "вне списка" in out


def test_gitignore_warning_redacted(tmp_path):
    """Правило .gitignore — недоверенный текст репо: уезжая в stderr через
    предупреждение фолбэка, проходит мин-редакцию. Негатив-правило ('!')
    фолбэк не поддерживает — потому и попадает в предупреждение."""
    (tmp_path / "drafts").mkdir()
    (tmp_path / "drafts" / "a.md").write_text("# a\n", "utf-8")
    (tmp_path / ".gitignore").write_text("!secret=FAKEkey456789.md\n", "utf-8")
    r = subprocess.run(
        [sys.executable, str(_GITMARK), "--root", str(tmp_path), "lint"],
        capture_output=True, text=True, timeout=60,
    )
    assert "FAKEkey456789" not in r.stderr, "секрет из .gitignore утёк в предупреждение"
    assert "[REDACTED]" in r.stderr


# ── контракт TS-точки: humanZones surveyor'а проходят redactLite (queue-3/01) ──
def test_humanzones_redacted_contract():
    src = (REPO / "skills" / "onto-doc" / "onto-doc.workflow.ts").read_text("utf-8")
    m = re.search(
        r"humanZones = Array\.isArray\(sv\.humanZones\)[\s\S]{0,400}?\.map\(\(z\) => redactLite\(z\)\)",
        src,
    )
    assert m, (
        "humanZones surveyor'а уезжают в отчёт рана без redactLite — "
        "верни .map((z) => redactLite(z)) в парсинг выхода surveyor'а (queue-3/01)"
    )
