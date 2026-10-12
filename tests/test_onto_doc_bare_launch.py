"""Голый запуск онто-дока (onto-doc-canon/01, 2026-10-12).

Два слоя:
1. Факты файла: хедер объявляет task и root необязательными, строка
   task-ассерта «Нужен непустой args.task» из файла исчезла.
2. Поведенческие пробы целым файлом (паттерн test_onto_doc_matrix.py):
   живой onto-doc.workflow.ts под мок-фасадом хоста запускается без ключа
   task — бутстрап идёт как при явной задаче, дефолт «весь репозиторий»
   доезжает до промптов surveyor'а и кураторов; пустая и пробельная задача
   дают тот же дефолт; явная задача проходит без подмены. Каждая проба
   снабжена мутационной: снятие дефолта опустошает задачу в промптах.
Приёмка уровня хоста (required: false принимает args без task на сабмите)
живой — tmp-фикстура канона onto-doc-parity, см. план тикета.
"""
import json
import re
import subprocess
import tempfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
WORKFLOW = REPO / "skills" / "onto-doc" / "onto-doc.workflow.ts"

# Мок-фасад хоста + запуск завёрнутого воркфлоу. Сценарий управляет args и
# ответом агентам (surveyor и кураторы получают один ответ — для бутстрапа
# это валидная декомпозиция, для куратора — объект без written: skipped).
HARNESS = """
const sc = __SCENARIO__;
const calls = [];
const prompts = [];
const logs = [];
let threw = "";
let result = null;
try {
  result = await __body(
    sc.args,
    {
      run: async (cmd, argv) => {
        calls.push(argv.join(" "));
        if (cmd === "test") return { exitCode: 1, stdout: "", stderr: "" };
        if (argv.includes("stat")) return { exitCode: 0, stdout: '{"files":3,"chunks":9,"links":5}', stderr: "" };
        if (argv.includes("lint")) return { exitCode: 0, stdout: "lint mock", stderr: "" };
        return { exitCode: 0, stdout: "", stderr: "" };
      },
    },
    (name) => ({ ask: async (q) => { prompts.push(String(q)); return sc.agentAnswer; } }),
    (m) => logs.push(String(m)),
    () => {},
    () => {},
  );
} catch (e) {
  threw = e instanceof Error ? `${e.name}: ${e.message}` : String(e);
}
console.log(JSON.stringify({ result, threw, calls, prompts, logs }));
"""

SURVEY = {"pieces": [{"path": "docs/services/mock/README.md", "what": "обзор сервиса"}],
          "humanZones": []}

NODE_MTS_CMD: list[str] | None = None


def node_mts_cmd() -> list[str]:
    """Команда node для .mts-срезов (канон test_onto_doc_matrix.py:79-96):
    ≥23 снимает типы сам, 22.6–22.x — через --experimental-strip-types,
    ниже — именованный skip."""
    v = subprocess.run(["node", "-p", "process.versions.node"],
                       capture_output=True, text=True, timeout=60)
    assert v.returncode == 0, f"node не отвечает версией:\n{v.stderr[:200]}"
    version = tuple(int(x) for x in v.stdout.strip().split(".")[:3])
    if version >= (23, 0, 0):
        return ["node"]
    if version >= (22, 6, 0):
        return ["node", "--experimental-strip-types"]
    pytest.skip(
        f"node {v.stdout.strip()} < 22.6: ни снятия типов, ни "
        "--experimental-strip-types — .mts-срезы непрогоняемы (минимум в docs/ops/install.md)")


def run_flow(scenario: dict, mutations: list[tuple[str, str]] | None = None) -> dict:
    """Прогон живого воркфлоу под моками; mutations — текстовые (старое, новое)
    пары с проверкой единственности вхождения до подмены."""
    global NODE_MTS_CMD
    if NODE_MTS_CMD is None:
        NODE_MTS_CMD = node_mts_cmd()
    body = WORKFLOW.read_text(encoding="utf-8")
    for old, new in mutations or []:
        assert body.count(old) == 1, f"якорь мутации дрейфовал (count={body.count(old)}): {old[:60]!r}"
        body = body.replace(old, new)
    driver = (
        "const __body = async (args, world, agent, log, phase, report) => {\n"
        + body
        + "\n};\n"
        + HARNESS.replace("__SCENARIO__", json.dumps(scenario, ensure_ascii=False))
    )
    with tempfile.NamedTemporaryFile("w", suffix=".mts", delete=False, encoding="utf-8") as fh:
        fh.write(driver)
        name = fh.name
    try:
        r = subprocess.run([*NODE_MTS_CMD, name], capture_output=True, text=True, timeout=120)
    finally:
        Path(name).unlink(missing_ok=True)
    assert r.returncode == 0, f"срез прогона упал:\n{r.stderr[:500]}"
    return json.loads(r.stdout)


# ── факты файла ────────────────────────────────────────────────────

def test_header_declares_task_and_root_optional():
    """Хедер — живой контракт args: task и root объявлены required: false,
    иначе хост отбивает args без ключей до старта тела (contour, урок 10)."""
    src = WORKFLOW.read_text(encoding="utf-8")
    header = re.search(r"/\* zcode-workflow[\s\S]*?\*/", src)
    assert header, "хедер zcode-workflow не найден"
    for arg in ("task", "root"):
        m = re.search(rf"^  {arg}:\n(?:    .*\n)*?    required: (\w+)$",
                      header.group(0), re.M)
        assert m, f"флаг required для {arg} не найден в хедере"
        assert m.group(1) == "false", f"{arg} всё ещё required: {m.group(1)}"


def test_task_abort_branch_is_gone():
    """Строка ассерта и его ветка исчезли из файла (критерий тикета — grep
    без совпадений)."""
    src = WORKFLOW.read_text(encoding="utf-8")
    assert "Нужен непустой args.task" not in src
    assert "!task.trim()" not in src


# ── поведенческие пробы ────────────────────────────────────────────

def test_bare_args_bootstrap_green_with_default_scope():
    """Args без ключа task (и без plan) — бутстрап идёт как при явной задаче:
    зелёный прогон, куски есть, дефолт «весь репозиторий» доезжает до
    промптов surveyor'а и кураторов. Мутационная проба: дефолт снят —
    задача в промптах пуста, ассерт пробы падает (пин жив)."""
    out = run_flow({"args": {"root": "/tmp/kb"}, "agentAnswer": SURVEY})
    assert out["threw"] == "", f"голый запуск упал: {out['threw']}"
    res = out["result"]
    assert res is not None and res["green"], res["conclusion"]
    assert len(res["pieces"]) > 0, res["pieces"]
    assert any("lint" in c for c in out["calls"]), "гейт lint не выполнялся"
    assert "весь репозиторий" in out["prompts"][0], out["prompts"][0][:200]
    assert "весь репозиторий" in out["prompts"][1], out["prompts"][1][:200]
    # мутационная проба: дефолт снят — задача в промптах пуста
    mutant = run_flow(
        {"args": {"root": "/tmp/kb"}, "agentAnswer": SURVEY},
        mutations=[('const task = String(args.task ?? "").trim() || "весь репозиторий";',
                    'const task = String(args.task ?? "").trim();')],
    )
    assert "весь репозиторий" not in mutant["prompts"][0], (
        "мутация «дефолт снят» всё ещё несёт дефолт в промпт — проба мертва"
    )


def test_empty_and_whitespace_task_fall_back_to_default():
    """Оба живых ключа покрыты: пустая строка и пробельная задача дают дефолт
    «весь репозиторий» (старый ассерт считал пробельную пустой — симметрия)."""
    for task_value in ("", "   "):
        out = run_flow({"args": {"task": task_value, "root": "/tmp/kb"},
                        "agentAnswer": SURVEY})
        res = out["result"]
        assert res is not None and res["green"], f"task={task_value!r}: {res['conclusion']}"
        assert "весь репозиторий" in out["prompts"][0], f"task={task_value!r}: дефолт не в промпте"


def test_explicit_task_passes_through():
    """Явная задача — данные оператора, не подмена: проходит в промпты
    (после трима), дефолт не вклинивается."""
    out = run_flow({"args": {"task": "  док по API лимитов  ", "root": "/tmp/kb"},
                    "agentAnswer": SURVEY})
    res = out["result"]
    assert res is not None and res["green"], res["conclusion"]
    assert "док по API лимитов" in out["prompts"][0], out["prompts"][0][:200]
    assert "весь репозиторий" not in out["prompts"][0], out["prompts"][0][:200]
