"""Contract of the gate reviewer substrate (roles-fallback-substrate/03).
The lens transport of the review gate is HOST SUBAGENTS ONLY: the direct
neuraldeep API contour was demolished on 2026-10-11 — the branch, the tariff
map, the worker pool, per-call timeouts, the compact-retry, the JSON-in-fence
repair, the substrate probe and the args substrate/reviewerModel/provider are
gone. One typed agent().ask per file×lens pair; a throw is a named file
failure (never a dead run, never a silent coverage gap); a run where not a
single file got answers is a named abort (totalSubstrateFailure), not a false
green. Parallelism, provider-error retries and timeouts belong to the host
runtime (dynamic-workflows contract §16.3). Hygiene ceilings (diff/inline
lines) are literals of the constants block, not a tariff map. The absence
probe is the load-bearing negative half: any return of the direct contour
under its PINNED NAMES reintroduces one of the literals or patterns and turns
the suite red — its detector is mutation-checked live below (a bare
«substrate» word must not fire on plan names like roles-fallback-substrate,
so the word-boundary pattern carries that case); a contour rebuilt under new
names is beyond a named probe — the ticket criterion asks for the named
probe, not a behavioral ban on outgoing calls. The outcome classifier works on subagent outcomes
(typed answer | exception → answer | named error through redact) and is
pinned behaviorally together with the task runner under node's type
stripping; the runner mutation probe turns «throw instead of a named value»
red by killing the run. The A/B tails of lens-substrate-flash live on as
pins: hygiene literals bound to the constants block (no map to derive them
from), the single ask site inside the branch braces. The pool tails (driver
task identity, the N<cap branch) died with the demolition itself — no pins
required (roles-fallback-substrate/03)."""
import json
import re
import subprocess
import tempfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
WORKFLOW = REPO / "skills" / "ship" / "reviewer.workflow.ts"

# Литералы и паттерны прямого API-контура (роли-fallback-substrate/03): любой
# из них в файле — контур вернулся. Имена планов (roles-fallback-substrate,
# lens-substrate-flash) и теста (test_reviewer_substrate) легитимны — голое
# слово «substrate» пинится word-boundary-паттерном, а не подстрокой.
DIRECT_LITERALS = (
    "ND_CALL",
    "ND_PROVIDER",
    "LENS_PROFILES",
    "LensProfile",
    "lensProfile",
    "resolveLensProfile",
    "reviewerModel",
    "args.provider",
    "ndProvider",
    "extractLensJson",
    "repairJsonStrings",
    "LENS_WORKERS",
    "LENS_RETRIES",
    "LENS_CALL_TIMEOUT_MS",
    "LENS_CONCURRENCY",
    "BEGIN DIRECT LENSES",
    "SUBSTRATE CHECK",
    "LENS JSON",
    "LENS POOL",
)
DIRECT_PATTERNS = (
    r'"direct"',
    r"substrate ===",
    r"args\.substrate",
    r"(?<![\w_-])substrate(?![\w_-])",
)


def direct_leaks(text: str) -> list[str]:
    leaks = [lit for lit in DIRECT_LITERALS if lit in text]
    leaks += [f"re:{pat}" for pat in DIRECT_PATTERNS if re.search(pat, text)]
    return leaks


def run_node_slice(driver: str, suffix: str = ".mjs") -> subprocess.CompletedProcess:
    """Прогон среза воркфлоу под node: файл во временнике, rc/stdout наружу.
    Для .mts-срезов (TS-аннотации не зачищаются + top-level await): node ≥ 23
    снимает типы сам, 22.6–22.x идёт через --experimental-strip-types; ниже
    22.6 нет ни того, ни другого — именованный skip (минимум из
    docs/ops/install.md, verified confirm-рана roles-fallback-substrate/03)."""
    cmd = ["node"]
    if suffix == ".mts":
        v = subprocess.run(["node", "-p", "process.versions.node"],
                           capture_output=True, text=True, timeout=60)
        assert v.returncode == 0, f"node не отвечает версией:\n{v.stderr[:200]}"
        version = tuple(int(x) for x in v.stdout.strip().split(".")[:3])
        if version >= (23, 0, 0):
            pass  # типы снимаются сами
        elif version >= (22, 6, 0):
            cmd.append("--experimental-strip-types")
        else:
            pytest.skip(
                f"node {v.stdout.strip()} < 22.6: ни снятия типов, ни "
                "--experimental-strip-types (появился в 22.6.0) — .mts-срезы "
                "непрогоняемы; минимум зафиксирован в docs/ops/install.md")
    with tempfile.NamedTemporaryFile("w", suffix=suffix, delete=False) as fh:
        fh.write(driver)
        name = fh.name
    try:
        return subprocess.run([*cmd, name], capture_output=True, text=True, timeout=120)
    finally:
        Path(name).unlink(missing_ok=True)


def structural_window(text: str, anchor: str, closing: str) -> str:
    """Окно от единственной строки с якорем до закрывающей строки включительно
    (урок followups-2: структурные окна до `}`/`^};` — голый str.index не
    различает комментарии и ловит не тот фрагмент)."""
    lines = text.splitlines(keepends=True)
    starts = [i for i, l in enumerate(lines) if anchor in l]
    assert len(starts) == 1, f"якорь неуникален или потерян: {anchor!r} ({len(starts)})"
    ends = [i for i in range(starts[0], len(lines)) if re.match(closing, lines[i])]
    assert ends, f"закрывающая строка {closing!r} не найдена после {anchor!r}"
    return "".join(lines[starts[0]:ends[0] + 1])


def lens_outcome_source() -> str:
    """redact + classifyLensOutcome живого файла (классификатор ходит через
    redact); TS-аннотации не зачищаются — срез гоняется node'ом со снятием
    типов."""
    text = WORKFLOW.read_text(encoding="utf-8")
    return "\n".join((
        structural_window(text, "function redact(", r"^}$"),
        structural_window(text, "function classifyLensOutcome(", r"^}$"),
    ))


def runner_bundle() -> str:
    """Сборка среза раннера линз: redact + normalizeSeverity + toFileReview +
    classifyLensOutcome (структурные окна) + блок SUBAGENT LENSES (маркеры).
    Хост-фасад (agent/report) и материал драйвер даёт заглушками."""
    text = WORKFLOW.read_text(encoding="utf-8")
    m = re.search(r"// BEGIN SUBAGENT LENSES.*?\n(.*?)// END SUBAGENT LENSES", text, re.S)
    assert m, "SUBAGENT LENSES block lost its markers"
    return "\n".join((
        structural_window(text, "function redact(", r"^}$"),
        structural_window(text, "function normalizeSeverity(", r"^}$"),
        structural_window(text, "const toFileReview = (", r"^};$"),
        structural_window(text, "function classifyLensOutcome(", r"^}$"),
        m.group(1),
    ))


def runner_driver(throw_at: list[int], leaky: bool = False) -> str:
    """Драйвер раннера: две задачи, throw_at перечисляет индексы задач, чей
    ask бросает (текст исключения несёт фейковый секрет — проба redact);
    leaky — линза ОТВЕЧАЕТ с секретом в where и failed (проба redact модельных
    полей успешного ответа, verified находка confirm-рана
    roles-fallback-substrate/03)."""
    bundle = runner_bundle()
    leaky_answer = (
        "    if (" + ("true" if leaky else "false") + ") return { findings: [{ where: \"a.py:1 API_KEY=sk-abcdef123456\", "
        'claim: "c", evidence: "e", severity: "high" }], summary: "s", '
        'failed: "файл не читается, в логе Bearer sk-abcdef123456" };\n'
    )
    return (
        "const results: { review: any; truncated: number; normalized: number }[] = [];\n"
        "const reportLog: any[] = [];\n"
        "const report = (x: any) => { reportLog.push(x); };\n"
        "const MAX_FINDINGS = 8;\n"
        'const root = ".";\n'
        'const ticket = "тикет-проба";\n'
        "const fileMaterial = (f: any) => `- ${f.path}: материал`;\n"
        f"const throwAt = new Set({json.dumps(throw_at)});\n"
        "const agent = (name: string) => ({\n"
        "  ask: async () => {\n"
        '    if (throwAt.has(Number(name.split("-")[1]))) throw new Error("взрыв вызова с Bearer sk-abcdef123456");\n'
        f"{leaky_answer}"
        '    return { findings: [{ where: "x.py:1", claim: "c", evidence: "e", severity: "high" }], summary: "s", failed: "" };\n'
        "  },\n"
        "});\n"
        "const lensTasks = [\n"
        '  { lens: { id: "logic" }, file: { path: "a.py", diffLines: 1, untracked: false } },\n'
        '  { lens: { id: "docs" }, file: { path: "b.md", diffLines: 1, untracked: false } },\n'
        "];\n"
        f"{bundle}\n"
        "const failed0 = results[0].review.failed;\n"
        "const where0 = String(results[0].review.findings[0]?.where ?? '');\n"
        "console.log(JSON.stringify({\n"
        '  cleanRun: failed0 === "" && results[0].review.findings.length === 1,\n'
        '  namedFailure: failed0.includes("линза logic не ответила") && failed0.includes("взрыв вызова"),\n'
        '  secretHidden: !failed0.includes("sk-abcdef123456") && failed0.includes("[REDACTED]"),\n'
        '  reportNamed: reportLog[0].file === "a.py" && reportLog[0].count === 0 && reportLog[0].failed === failed0,\n'
        '  okRouted: results[1].review.file === "b.md" && results[1].review.findings.length === 1 && reportLog[1].count === 1,\n'
        '  bothAnswered: results.length === 2 && results.every((x) => x && x.review),\n'
        '  leakyRedacted: !failed0.includes("sk-abcdef123456") && !where0.includes("sk-abcdef123456") '
        '&& failed0.includes("[REDACTED]") && where0.includes("[REDACTED]"),\n'
        "}));\n"
    )


def test_direct_contour_absent():
    """Absence-пин (roles-fallback-substrate/03): в воркфлоу нет ни кода, ни
    args прямого API-контура; args-шапка — ровно ticket/base/root. Живая
    проба детектора: подмена текста литералом и паттерном ветки краснит —
    детектор не мёртв (урок гейта 04: presence-якорь дополняется пробой)."""
    text = WORKFLOW.read_text(encoding="utf-8")
    leaks = direct_leaks(text)
    assert not leaks, f"прямой API-контур вернулся в reviewer.workflow.ts: {leaks}"
    m = re.search(r"\nargs:\n(.*?)\n\*/", text, re.S)
    assert m, "args-шапка workflow не читается"
    keys = tuple(re.findall(r"^  (\w+):$", m.group(1), re.M))
    assert keys == ("ticket", "base", "root"), f"args-шапка дрейфовала: {keys}"
    # имена планов легитимны: голое слово в них не ловится, в коде — ловится
    for injection in ("const substrate = args.substrate ?? 'subagent';",
                      "const LENS_PROFILES = {};"):
        assert direct_leaks(text + "\n" + injection), f"детектор мёртв на: {injection}"
    assert not direct_leaks("план roles-fallback-substrate/03 и test_reviewer_substrate.py"), (
        "детектор ловит имена планов — паттерн слишком широкий")


def test_gate_constants_are_block_literals():
    """Живой хвост A/B lens-substrate-flash в форме демонтажа: гигиена —
    литералы блока констант, карты и guard'а веток больше нет, производить
    константы извне блока нельзя. «Один файл на вызов» — инвариант, ручки
    filesPerCall нет."""
    text = WORKFLOW.read_text(encoding="utf-8")
    m = re.search(r"// BEGIN GATE CONSTANTS.*?\n(.*?)// END GATE CONSTANTS", text, re.S)
    assert m, "GATE CONSTANTS block lost its markers"
    body = m.group(1)
    for line in ("const MAX_FINDINGS = 8;", "const MAX_FILES = 20;",
                 "const MAX_DIFF_LINES = 2000;", "const LENS_INLINE_LINES = 6000;"):
        assert re.search(rf"^{re.escape(line)}$", body, re.M), f"{line} потерян как литерал блока"
    outside = text.replace(m.group(0), "")
    # рождение константы вне блока — любая форма объявления/присвоения
    # (verified находка confirm-рана roles-fallback-substrate/03: голый
    # детектор пропускал let/var и деструктуризацию)
    name = r"(?:MAX_FINDINGS|MAX_FILES|MAX_DIFF_LINES|LENS_INLINE_LINES)"
    birth_patterns = (
        rf"^\s*(?:(?:const|let|var)\s+)?{name}\s*=",
        rf"^\s*(?:const|let|var)\s*\{{[^}}]*\b{name}\b[^}}]*\}}\s*=",
    )
    for pat in birth_patterns:
        assert not re.search(pat, outside, re.M), "константа гейта рождается вне блока констант"
        assert re.search(pat, "let LENS_INLINE_LINES = 5000;\nconst { MAX_FILES } = limits;\n", re.M), (
            "детектор рождения мёртв — формы let/деструктуризации не ловятся")
    assert "filesPerCall" not in text, "«один файл на вызов» протёк как ручка конфигурации"


def test_lens_tasks_one_task_per_pair():
    """Топология поведенчески (инвариант файл×линза): задач ровно по паре
    файл×линза, без нарезки и дедупа, идентичность — пара из плана. Пул-
    хвосты (воркеры = min(cap, N), ветка N<cap) пинов не требуют — умерли
    с демонтажем (roles-fallback-substrate/03)."""
    text = WORKFLOW.read_text(encoding="utf-8")
    m = re.search(r"// BEGIN LENS TASKS.*?\n(.*?)// END LENS TASKS", text, re.S)
    assert m, "LENS TASKS block lost its markers"
    driver = (
        "const activeLenses = [\n"
        "  { lens: { id: 'logic' }, files: ['a.py', 'b.py', 'c.py'] },\n"
        "  { lens: { id: 'docs' }, files: ['b.md', 'c.py'] },\n"
        "];\n"
        f"{m.group(1)}\n"
        "console.log(JSON.stringify({ n: lensTasks.length, pairs: lensTasks.map((t) => t.lens.id + ':' + t.file) }));\n"
    )
    r = run_node_slice(driver)
    assert r.returncode == 0, f"срез LENS TASKS упал:\n{r.stderr[:300]}"
    out = json.loads(r.stdout)
    assert out["n"] == 5, "пар файл×линза должно быть 5 — нарезка/дедуп"
    assert out["pairs"] == ["logic:a.py", "logic:b.py", "logic:c.py", "docs:b.md", "docs:c.py"], out["pairs"]


def test_lens_outcome_classifier_names_subagent_failures():
    """Классификатор исходов линз — на исходах субагентов (roles-fallback-
    substrate/03) поведенчески: типизированный ответ проходит как есть;
    исключение и молчание — именованный отказ с именем линзы, секрет в тексте
    исключения до оператора не доходит (redact)."""
    driver = (
        f"{lens_outcome_source()}\n"
        "const ok = classifyLensOutcome({ id: 'logic' }, { findings: [], summary: 's', failed: '' }, null);\n"
        "const thrown = classifyLensOutcome({ id: 'docs' }, null, new Error('взрыв с Bearer sk-abcdef123456'));\n"
        "const silent = classifyLensOutcome({ id: 'tests' }, null, null);\n"
        "console.log(JSON.stringify({\n"
        "  okAnswer: ok.answer !== null && ok.error === '',\n"
        "  named: thrown.answer === null && thrown.error.includes('линза docs не ответила') && thrown.error.includes('взрыв'),\n"
        "  secretHidden: !thrown.error.includes('sk-abcdef123456') && thrown.error.includes('[REDACTED]'),\n"
        "  noCause: silent.answer === null && silent.error.includes('линза tests не ответила') && silent.error.includes('нет ни ответа, ни причины'),\n"
        "}));\n"
    )
    r = run_node_slice(driver, suffix=".mts")
    assert r.returncode == 0, f"срез классификатора упал:\n{r.stderr[:300]}"
    assert all(json.loads(r.stdout).values()), r.stdout


def test_subagent_runner_routes_answers_and_failures():
    """Раннер линз поведенчески (узкое место «молчаливого выпадения» файла из
    coverage): отказ ask — именованный failed в results и в report, через
    redact; ответ маршрутизируется через toFileReview — идентичность файла
    присвоенным путём; модельные where/failed УСПЕШНОГО ответа тоже через
    redact (verified находка confirm-рана roles-fallback-substrate/03 —
    модель уже наблюдалась путающей поля); чистый прогон не мусорит отказами.
    Мутационная проба: «бросить вместо отказа» в классификаторе роняет ран —
    пин жив и отличает значение-отказ от смерти рана."""
    r = run_node_slice(runner_driver([]), suffix=".mts")
    assert r.returncode == 0, f"чистый прогон раннера упал:\n{r.stderr[:300]}"
    out = json.loads(r.stdout)
    assert out["cleanRun"] and out["okRouted"] and out["bothAnswered"], out

    r = run_node_slice(runner_driver([], leaky=True), suffix=".mts")
    assert r.returncode == 0, f"прогон с секретом в where/failed ответа упал:\n{r.stderr[:300]}"
    out = json.loads(r.stdout)
    assert out["leakyRedacted"], out

    r = run_node_slice(runner_driver([0]), suffix=".mts")
    assert r.returncode == 0, f"прогон с отказом линзы упал (отказ — не смерть рана):\n{r.stderr[:300]}"
    out = json.loads(r.stdout)
    assert out["namedFailure"] and out["secretHidden"] and out["reportNamed"] and out["okRouted"], out

    r = run_node_slice(runner_driver([0, 1]), suffix=".mts")
    assert r.returncode == 0, f"прогон с отказом обеих линз упал (аборт живёт ниже, страховкой):\n{r.stderr[:300]}"
    out = json.loads(r.stdout)
    assert out["namedFailure"] and out["bothAnswered"], out

    bundle = runner_bundle()
    old_line = "return { answer: null, error: `линза ${lens.id} не ответила: ${redact(raw)}` };"
    assert bundle.count(old_line) == 1, "строка отказа классификатора дрейфовала — мутация не встанет"
    mutant = bundle.replace(old_line, 'throw new Error("мутация: отказ вместо значения"); ' + old_line)
    mutant_driver = runner_driver([0]).replace(bundle, mutant)
    r = run_node_slice(mutant_driver, suffix=".mts")
    assert r.returncode != 0, (
        "мутация «бросить вместо отказа» прошла зелёным — отказ линзы стал смертью рана, а пин этого не видит")
    # проба и второго класса мутации: снять redact с модельных полей ответа
    m_where = "where: redact(String(x?.where ?? \"\")),"
    m_failed = 'failed: redact(String(rRaw?.failed ?? (rRaw == null ? `линза ${lens.id}: нет ответа по файлу` : ""))),'
    assert bundle.count(m_where) == 1 and bundle.count(m_failed) == 1, (
        "якоря redact модельных полей дрейфовали — мутация не встанет")
    mutant2 = bundle.replace(m_where, 'where: String(x?.where ?? ""),').replace(
        m_failed, 'failed: String(rRaw?.failed ?? (rRaw == null ? `линза ${lens.id}: нет ответа по файлу` : "")),')
    mutant2_driver = runner_driver([], leaky=True).replace(bundle, mutant2)
    r = run_node_slice(mutant2_driver, suffix=".mts")
    assert r.returncode != 0 or not all(json.loads(r.stdout).values()), (
        "мутация «снять redact с where/failed» прошла зелёным — пин утечки мёртв")


def test_subagent_branch_structure():
    """Структурные пины ветки: один сайт ask и один сайт agent() на блок
    (brace-контейнмент — живой хвост A/B), явной model в agent() нет (модель
    линз — subagent_model воркфлоу), своего ретрая нет (повторы — рантайм
    хоста, §16.3); маршрут отказа идёт через классификатор и пишет failed
    в results внутри ветки outcome.answer === null (поведенчески пинено
    раннер-тестом, здесь якорь места)."""
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "interface LensReviewResult" in text, "типизированный интерфейс линзы потерян"
    m = re.search(r"// BEGIN SUBAGENT LENSES.*?\n(.*?)// END SUBAGENT LENSES", text, re.S)
    assert m, "SUBAGENT LENSES block lost its markers"
    block = m.group(1)
    assert block.count(".ask<LensReviewResult>(") == 1, "ask не один на блок"
    assert block.count("await agent(") == 1, "сайт agent() не один"
    # бан на КОДЕ блока, не на комментариях-прозе (verified находка
    # confirm-рана roles-fallback-substrate/03: безобидный комментарий вида
    # «модель линз — subagent_model: …» не должен краснить сьют)
    code = "\n".join(l for l in block.splitlines() if not l.lstrip().startswith("//"))
    assert "model:" not in code, "явная model в agent() молча перекрывает subagent_model воркфлоу"
    assert "lensTasks.map((_, i) => runSubagentLensTask(i))" in block, "задачи не мапятся по парам файл×линза"
    assert "retry" not in code.lower() and "attempt" not in code.lower(), "у линз появился свой ретрай"
    mif = re.search(r"if \(outcome\.answer === null\) \{(.*?)\n  \}", block, re.S)
    assert mif, "ветка отказа классификатора потеряна"
    assert 'results[taskIndex] = { review: { file: file.path, findings: [], summary: "", failed: outcome.error }' in mif.group(1), (
        "отказ не пишет failed в results — файл молча выпадает из coverage")


def test_total_substrate_failure_names_abort():
    """Страховка поведенчески И по месту подключения (verified находка
    confirm-рана roles-fallback-substrate/03: position-free якоря пропускали
    мёртвую ветку и перенос блока выше populated-точки). Позиция: join →
    reviews → abort → throw. Вход ([], N>0) — именованный abort (vacuous
    every не проходит молча); смешанное покрытие и ноль задач — пусто (гейт
    не абортит частичное покрытие). Подключение исполняется живым срезом
    хвоста: все failed — бросок с причинами, смешанное — нет (мутация
    «мёртвая ветка» краснеет именно здесь)."""
    text = WORKFLOW.read_text(encoding="utf-8")
    m = re.search(r"// BEGIN SUBSTRATE TOTAL FAIL.*?\n(.*?)// END SUBSTRATE TOTAL FAIL", text, re.S)
    assert m, "SUBSTRATE TOTAL FAIL block lost its markers"
    body = m.group(1).replace(
        "(reviews: FileReview[], taskCount: number): string", "(reviews, taskCount)")
    assert body != m.group(1), "аннотация функции дрейфовала — срез не исполняется"
    join_marker = "await Promise.all(lensTasks.map((_, i) => runSubagentLensTask(i)));"
    reviews_marker = "const reviews = results.map((x) => x.review);"
    abort_marker = "const totalAbort = totalSubstrateFailure(reviews, lensTasks.length);"
    throw_marker = 'if (totalAbort !== "") throw new Error(totalAbort);'
    p_join = text.find(join_marker)
    p_reviews = text.find(reviews_marker)
    p_abort = text.find(abort_marker)
    p_throw = text.find(throw_marker)
    assert -1 not in (p_join, p_reviews, p_abort, p_throw), "маркеры подключения страховки потеряны"
    assert p_join < p_reviews < p_abort < p_throw, (
        "страховка оторвана от populated-точки: abort обязан стоять после join и после сборки reviews "
        "(мутация «блок выше join» делает abort вечным, «мёртвая ветка» — никогда)")
    driver = (
        f"{body}\n"
        "const failed = (n) => Array.from({ length: n }, (_, i) => ({ file: 'f' + i, failed: 'линза не ответила: x' + i }));\n"
        "const mixed = [{ file: 'a', failed: '' }, { file: 'b', failed: 'y' }];\n"
        "console.log(JSON.stringify([\n"
        "  totalSubstrateFailure(failed(3), 3).includes('ни один файл'),\n"
        "  totalSubstrateFailure(failed(2), 2).includes('линза не ответила'),\n"
        "  totalSubstrateFailure([], 2).includes('ни один файл'),\n"
        "  totalSubstrateFailure(mixed, 2) === '',\n"
        "  totalSubstrateFailure([], 0) === '',\n"
        "]));\n"
    )
    r = run_node_slice(driver)
    assert r.returncode == 0, f"срез totalSubstrateFailure упал:\n{r.stderr[:300]}"
    assert all(json.loads(r.stdout)), r.stdout
    # живое исполнение подключения: срез хвоста от reviews до throw
    tail = text[text.find(reviews_marker):text.find(throw_marker) + len(throw_marker)]
    tail_driver = (
        f"{body}\n"
        "const lensTasks = [1, 2];\n"
        "const item = (file, failed) => ({ review: { file, failed, findings: [], summary: '' }, truncated: 0, normalized: 0 });\n"
        "const run = (results) => { let threw = '';\n"
        f"  try {{ {tail} }} catch (e) {{ threw = String(e.message); }}\n"
        "  return threw;\n"
        "};\n"
        "const allFailed = [item('a', 'линза logic не ответила: x'), item('b', 'линза docs не ответила: y')];\n"
        "const mixedResults = [item('a', ''), item('b', 'y')];\n"
        "console.log(JSON.stringify([\n"
        "  run(allFailed).includes('ни один файл'),\n"
        "  run(allFailed).includes('линза logic не ответила'),\n"
        "  run(mixedResults) === '',\n"
        "]));\n"
    )
    r = run_node_slice(tail_driver)
    assert r.returncode == 0, f"срез подключения страховки упал:\n{r.stderr[:300]}"
    assert all(json.loads(r.stdout)), r.stdout
