"""redactLite в выводе gitmark (queue-3/01): мин-редакция секретов на границе
stdout/stderr — msg строк lint и inventory --check, правило .gitignore из
предупреждения фолбэка; пути и счётчики остаются честными.

Живые пробы до фиксы (та же фикстура, что в E2E ниже) доказали три канала
lint: I4 печатает href с ?token=…, I9 печатает значение поля карточки,
I2 печатает service='eyJ…'. inventory/map stdout секретов не несёт по
формату (счётчики и пути) — их каналы документированы в тикете как
осознанные пропуски (реестр-генерат и HTML-рендер корпуса не редактируются).

Матрица зеркалит TS-набор tests/onto_doc_matrix.mjs; правила синхронны с
TS-копией (три расширения сверх onto-doc-hygiene внесены в обе — находки
confirm-рана dwfrun-99cd0897: bearer-lookahead, KEY-граница (?![a-z]),
кавыченное значение после некавыченного ключа). Мутационная проба двухслойна:
снятие любого правила по отдельности краснит матрицу (кейс-ловушка для
правила; мутант подставляется в шипуемую gm.redact_lite через monkeypatch),
а снятие применения на печати краснит E2E — секреты оказываются в stdout
и роняют ассерты секрета."""
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
    # ── ловушки правил (снятие правила оставляет секрет в выводе) ──
    (True, "eyJ JWS целиком (правило 1)",
     "токен eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.FAKESIG123456 в логе", "FAKESIG123456"),
    (True, "bearer-литерал без словарного ключа (правило 2)",
     "hdr bearer FAKEabc123-def456=", "FAKEabc123-def456="),
    (True, "JSON-форма с кавычками (правило 3)", '{"password": "FAKEhunter2x"}', "FAKEhunter2x"),
    (True, "YAML: кавыченное значение, некавыченный ключ (правило 4)",
     'password: "FAKEkey12345"', "FAKEkey12345"),
    (True, "пароль равно, без кавычек (правило 5)", "password=FAKEabcdef123456", "FAKEabcdef123456"),
    (True, "vendor ghp_ без словарного контекста (правило 6)", "see ghp_FAKETOKEN12 end", "ghp_FAKETOKEN12"),
    # ── прочие позитивы ──
    (True, "пароль двоеточием", "конфиг: password: FAKEcolonsecret", "FAKEcolonsecret"),
    (True, "JSON-форма api_key", '{"api_key": "FAKEv1.abc123def456"}', "FAKEv1.abc123def456"),
    (True, "JSON-форма client_secret (аффикс ключа)",
     '{"client_secret": "FAKEcl13ntsec"}', "FAKEcl13ntsec"),
    (True, "python-repr client_secret", "{'client_secret': 'FAKEpysec99'}", "FAKEpysec99"),
    (True, "JSON-форма: экранированная кавычка в значении",
     '{"password": "abcd\\"EFSECRET9tail"}', "EFSECRET9tail"),
    (True, "JSON-форма с бэкслешами перед кавычками",
     '\\"password\\": \\"FAKEesc9secret99\\"', "FAKEesc9secret99"),
    (True, "python-repr форма с одинарными кавычками",
     "{'password': 'FAKEpysecret99'}", "FAKEpysecret99"),
    (True, "ключ с цифровым суффиксом (аффикс)",
     "password1=FAKEp1secret", "FAKEp1secret"),
    (True, "ключ с суффиксом _key", "secret_key=FAKEsk22key", "FAKEsk22key"),
    (True, "мн. число ключа — одна буква после KEY (гейт r2)",
     "secrets: FAKEplural123", "FAKEplural123"),
    (True, "мн. число tokens", "tokens: FAKEplural456", "FAKEplural456"),
    # формат живой пробы I9 (инвентарь тикета): средний токен «значение» —
    # служебное слово формата движка, съедается вместе с секретом
    (True, "I9: значение поля карточки вне списка",
     "поле token: значение 'FAKEprobe1' вне списка", "FAKEprobe1"),
    (True, "I9: средний токен 64 символа (длинный путь)",
     "password: " + "p" * 64 + " 'FAKElongtail9'", "FAKElongtail9"),
    (True, "basic-литерал с padding =", "basic RkFLRXVzZXI6RkFLRXBhc3N3b3Jk=", "RkFLRXVzZXI6RkFLRXBhc3N3b3Jk="),
    (True, "basic-литерал с цифрой внутри", "basic RkFLRXVzZXI6RkFLRXBhc3N3b3Jk", "RkFLRXVzZXI6RkFLRXBhc3N3b3Jk"),
    (True, "vendor sk-", "ключ sk-FAKEa1b2c3d4e5f6", "FAKEa1b2c3d4e5f6"),
    (True, "vendor AKIA", "aws AKIAFAKE12345678 key", "AKIAFAKE12345678"),
    # форматы живых проб I2/I4 (инвентарь тикета)
    (True, "I2: service-значение вне словаря",
     "service='eyJhbGciOiJIUzI1NiJ9.eyJFAKEsubIn0.FAKESIG99' вне словаря", "FAKESIG99"),
    (True, "I4: битая ссылка с токеном",
     "битая ссылка → ./nope.md?token=ghp_FAKETOKEN12345", "FAKETOKEN12345"),
    # негативы: честные строки не искажаются
    (False, "короткое значение — пропуск", "token=abc", ""),
    (False, "auth в прозе (короткое значение) — пропуск", "заголовок auth: см. документацию", ""),
    (False, "author — честное слово, auth не матчит (KEY-граница)", "author: Пушкин", ""),
    (False, "authorized — KEY + 2+ букв, граница держит", "authorized: client-id-12345", ""),
    (False, "camelCase ключ — задокументированный пропуск (KEY + 2+ букв)",
     "tokenValue: значение 'abc12345def' вне списка", ""),
    (False, "authKey — задокументированный пропуск", "authKey: s3cr3tv4lue", ""),
    (False, "чисто буквенный bearer-токен — трейд-офф lookahead",
     "bearer Zxqwvutsrqponm", ""),
    (False, "basic authentication — проза, не токен (lookahead)", "схема basic authentication запрещена", ""),
    (False, "кириллический ключ — вне словаря lite (задокументированный пропуск)",
     "токен стенда: hunter2go99", ""),
    (False, "путь с token в имени", "docs/plans/token-guide.md — нет frontmatter с node_type", ""),
    (False, "счётчики", "5 файлов · I2×2 · I4×1 · 200 KB", ""),
    (False, "русская проза без словарных ключей", "Пароль забыт — восстановление через поддержку", ""),
    (False, "service вне словаря без секрет-формы (диагностика I2 честна)",
     "service='demo' вне словаря", ""),
]


@pytest.mark.parametrize("should_mask,name,inp,secret", REDACT_CASES)
def test_redact_matrix(should_mask, name, inp, secret):
    out = gm.redact_lite(inp)
    assert (out != inp) == should_mask, f"[{name}] => {out!r}"
    if should_mask:
        assert secret not in out, f"УТЕЧКА [{name}]: секрет остался в выводе"
        # маскировка состоялась, а не «функция стёрла строку» / частично
        assert "[REDACTED]" in out, f"[{name}]: маркер маскировки не в выводе"
    assert gm.redact_lite(out) == out, f"НЕ ИДЕМПОТЕНТНО [{name}]"


def test_mutation_every_rule_has_a_trap(monkeypatch):
    """Мутационная проба: у каждого правила есть кейс-ловушка — отключение
    правила (любого одного, через подмену gm._REDACT_RULES в шипуемой
    redact_lite) оставляет секрет хотя бы в одном выводе. Оригинал снимается
    до цикла: «восстановление» чтением атрибута накапливало мутантов и
    пропускало нечётные правила (гейт r2, подтверждено трассировкой)."""
    orig = list(gm._REDACT_RULES)
    positives = [c for c in REDACT_CASES if c[0]]
    for i in range(len(orig)):
        monkeypatch.setattr(gm, "_REDACT_RULES", orig[:i] + orig[i + 1:])
        traps = [
            name for _, name, inp, secret in positives
            if secret and secret in gm.redact_lite(inp)
        ]
        monkeypatch.setattr(gm, "_REDACT_RULES", orig)
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
    # rc=0 — контракт lint без --strict даже при ERR; падение процесса (rc=1/2)
    # не может проходить молча
    assert r.returncode == 0, f"gitmark упал: {r.stderr[-500:]}"
    out = r.stdout + r.stderr
    for secret in ("FAKEprobe12345", "FAKETOKEN12345", "FAKESIG99", "eyJhbGci"):
        assert secret not in out, f"секрет {secret!r} утёк в вывод lint"
    assert out.count("[REDACTED]") >= 3, "маскировка не применилась к каналам I2/I4/I9"
    # путь и хвост формата I9 честны; средний токен «значение» съеден вместе
    # с секретом (служебное слово формата, трейд-офф правила 4b)
    assert "docs/services/cards.md" in out
    assert "поле token: [REDACTED] вне списка" in out


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
    assert r.returncode == 0, f"gitmark упал: {r.stderr[-500:]}"
    combined = r.stdout + r.stderr
    assert "FAKEkey456789" not in combined, "секрет из .gitignore утёк (stdout/stderr)"
    assert "[REDACTED]" in combined


# ── контракты точек применения, недостижимых живой пробой формата ──
def test_inventory_check_print_redacted_contract():
    """msg инвентаря по формату не несёт значений полей — живая проба секрета
    там невозможна; точка применения (печать --check) пинится контрактом:
    литерал I7 уникален для этой ветки, снятие redact_lite краснит."""
    src = _GITMARK.read_text("utf-8")
    assert r"I7\033[0m {path} — {redact_lite(msg)}" in src, (
        "печать inventory --check потеряла redact_lite(msg) — третья точка "
        "применения очереди queue-3/01"
    )


# ── контракт TS-точки: humanZones surveyor'а проходят redactLite (queue-3/01) ──
def test_humanzones_redacted_contract():
    src = (REPO / "skills" / "onto-doc" / "onto-doc.workflow.ts").read_text("utf-8")
    assert "function redactLite" in src, "redactLite исчез из onto-doc.workflow.ts"
    # единственное присваивание humanZones — перезапись сырыми зонами после
    # редакции обходила бы точку применения (мутант confirm-рана)
    assigns = re.findall(r"\bhumanZones\s*=[^=]", src)
    assert len(assigns) == 1, (
        f"присваиваний humanZones {len(assigns)} — редакция может быть перезаписана"
    )
    m = re.search(
        r'humanZones = Array\.isArray\(sv\.humanZones\)\s*\?\s*\(sv\.humanZones as unknown\[\]\)\.filter\(\s*'
        r'\(z\): z is string => typeof z === "string" && z\.trim\(\) !== "",\s*'
        r'\)\.map\(\(z\) => redactLite\(z\)\)\s*:\s*\[\];',
        src,
    )
    assert m, (
        "humanZones surveyor'а уезжают в отчёт рана без redactLite — "
        "верни .map((z) => redactLite(z)) в парсинг выхода surveyor'а (queue-3/01)"
    )
    assert re.search(r"^\s*humanZones,\s*$", src, re.MULTILINE), (
        "humanZones не уезжает в отчёт рана (return) — редактировать нечего?"
    )
