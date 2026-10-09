"""Contract of the gate reviewer substrate (gate-followups-2/07 +
lens-substrate-flash). DEFAULT lens substrate since 2026-10-09: HOST
SUBAGENTS (agent()) on the model the caller assigns via the workflow's
subagent_model (the confirmer role model, ship SKILL.md step 6); the host
runtime owns parallelism, provider-error retries and timeouts (dynamic-
workflows contract §16.3) — the subagent branch has no pool, no retries, no
per-call timeouts, and one typed ask per file×lens pair (no JSON-in-fence).
The DIRECT neuraldeep API call remains the explicit fallback
(args.substrate="direct") for models whose context cannot carry the ~141k
subagent base weight (the 2026-10-06 tariff wall, three provider stops in
one day): the inline node caller travels inside the workflow file itself
(world.run("node", ["-e", ND_CALL, "--", <json>]) — no version drift), the
host-subagent substrate back then died on the tariff wall, the coddy detour
died on its own agency. The operator's decision closes the provider/model/
credential contour on zcode: the script reads apiKey and baseUrl from the
provider card in ~/.zcode/v2/provider_config.json and never prints the key.
These tests pin the script's syntax and its hygiene; the JSON extraction/
repair parsers are pinned below on synthetic samples. external-dependencies/
01: the provider is an ARG with the default neuraldeep-sub (a switch is
configuration, not a repo edit), and the direct substrate is fail-closed —
every missing piece (readable config, provider card, apiKey, the
reviewer-role model in the card) is a named abort naming the role, the
config path and what is missing, probed here live against fabricated HOMEs.
external-dependencies/04: the tariff physics is a per-model profile map
(LENS_PROFILES) resolved ONLY inside the direct branch — an unknown model is
a named abort before the lenses, never a silent transfer of the unlim-xl
constants; the subagent branch has its own hygiene literals outside the map.
Substrate args: empty = subagent, unknown = named return, reviewerModel/
provider under the default substrate = named abort (never a silent ignore)."""
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
WORKFLOW = REPO / "skills" / "ship" / "reviewer.workflow.ts"


def nd_call_source() -> str:
    """The inline API caller from the shipped workflow, extracted between
    the marker comments (they live INSIDE the template string, so they reach
    node -e as harmless JS comments)."""
    text = WORKFLOW.read_text(encoding="utf-8")
    m = re.search(r"// BEGIN ND CALL\n(.*?)// END ND CALL", text, re.S)
    assert m, "ND CALL block lost its markers in skills/ship/reviewer.workflow.ts"
    return m.group(1)


def lens_json_source() -> str:
    """The extractLensJson parser, the raw-newline repair and the outcome
    classifier from the shipped workflow, markers and TS annotations
    stripped — runs under node, no TS stripping."""
    text = WORKFLOW.read_text(encoding="utf-8")
    m = re.search(r"// BEGIN LENS JSON.*?\n(.*?)// END LENS JSON", text, re.S)
    assert m, "LENS JSON block lost its markers in skills/ship/reviewer.workflow.ts"
    body = m.group(1)
    m2 = re.search(r"// BEGIN LENS OUTCOME.*?\n(.*?)// END LENS OUTCOME", text, re.S)
    assert m2, "LENS OUTCOME block lost its markers in skills/ship/reviewer.workflow.ts"
    for old, new in (
        ("(out: string): string | null", "(out)"),
        ("(s: string): string", "(s)"),
        ("(env: { ok?: boolean; content?: string; finish?: string; error?: string }): { candidate: string | null; error: string }", "(env)"),
    ):
        body = body.replace(old, new)
        s2 = m2.group(1).replace(old, new)
    return body + "\n" + s2


def run_node_slice(driver: str) -> subprocess.CompletedProcess:
    """Прогон JS-среза воркфлоу под node: файл .mjs во временнике, rc/stdout
    наружу."""
    with tempfile.NamedTemporaryFile("w", suffix=".mjs", delete=False) as fh:
        fh.write(driver)
        name = fh.name
    try:
        return subprocess.run(["node", name], capture_output=True, text=True, timeout=60)
    finally:
        Path(name).unlink(missing_ok=True)


def lens_profile_source() -> str:
    """The model→profile map and its resolver from the shipped workflow
    (external-dependencies/04), markers and TS annotations stripped — runs
    under node."""
    text = WORKFLOW.read_text(encoding="utf-8")
    m = re.search(r"// BEGIN LENS PROFILE.*?\n(.*?)// END LENS PROFILE", text, re.S)
    assert m, "LENS PROFILE block lost its markers in skills/ship/reviewer.workflow.ts"
    body = re.sub(r"type LensProfile = \{.*?\};", "", m.group(1), flags=re.S)
    for old, new in (
        ("const LENS_PROFILES: Record<string, LensProfile> = {", "const LENS_PROFILES = {"),
        ("function resolveLensProfile(model: string): LensProfile {", "function resolveLensProfile(model) {"),
    ):
        body = body.replace(old, new)
    return body


def test_nd_call_compiles():
    with tempfile.NamedTemporaryFile("w", suffix=".cjs", delete=False) as fh:
        fh.write(nd_call_source())
        name = fh.name
    try:
        r = subprocess.run(["node", "--check", name], capture_output=True, text=True, timeout=60)
    finally:
        Path(name).unlink(missing_ok=True)
    assert r.returncode == 0, f"инлайн-скрипт вызова API не компилируется:\n{r.stderr}"


def run_nd_call(envelope: str | None, home: Path | None = None) -> subprocess.CompletedProcess:
    """Поведенческий прогон инлайн-скрипта с НАСТОЯЩИМ argv: node file.cjs --
    <конверт> (конверт — последний элемент argv; node -e съедает «--»-сепаратор:
    поиск его давал -1 и ронял JSON.parse на argv[0] — гейт v3). envelope=None —
    вызов без конверта: негативный кейс argv-разбора (гейт v6 — прежний тест
    подменял argv константой, argv-путь был мёртвым кодом). home — подменённый
    HOME: ветки fail-closed пробуются живьём на подделках конфига, не на машине."""
    with tempfile.NamedTemporaryFile("w", suffix=".cjs", delete=False) as fh:
        fh.write(nd_call_source())
        name = fh.name
    argv = ["node", name] + (["--", envelope] if envelope is not None else [])
    env = os.environ.copy()
    if home is not None:
        env["HOME"] = str(home)
    try:
        return subprocess.run(argv, capture_output=True, text=True, timeout=240, env=env)
    finally:
        Path(name).unlink(missing_ok=True)


def probe_home(root: Path, api_key: str | None, models: list[str] | None) -> Path:
    """Подделка HOME с конфигом zcode: провайдер probe-p (ключ и список моделей
    параметризуются); ключ — заведомо фейковый, сетевых вызовов тесты не делают."""
    home = root / "home"
    (home / ".zcode" / "v2").mkdir(parents=True)
    access: dict = {"type": "api-key"}
    if api_key is not None:
        access["apiKey"] = api_key
    config: dict = {
        "api": {"type": "openai-chat-completions", "baseUrl": "https://probe.invalid/v1"},
        "access": access,
    }
    if models is not None:
        config["personalModelIds"] = models
    cfg = {"schemaVersion": 1, "config": {"providerConfigRules": {"providerRules": [
        {"providerId": "probe-p", "enabled": True, "config": config},
    ]}}}
    (home / ".zcode" / "v2" / "provider_config.json").write_text(json.dumps(cfg), encoding="utf-8")
    return home


PROBE_MODEL = "qwen3.6-unlim-xl"


def probe_envelope(provider: str = "probe-p", **extra) -> str:
    return json.dumps({"provider": provider, "model": PROBE_MODEL, "prompt": "p", **extra}, ensure_ascii=False)


def test_nd_call_argv_without_separator_fails_named(tmp_path):
    """Негативный кейс argv-разбора поведенчески (verified гейта v6):
    с конвертом в argv — именованный fallthrough к ветке субстрата
    (rc=0, ok=false); без конверта — argv-путь жив (крэш на незащищённом
    JSON.parse, rc!=0), а не молчаливый успех."""
    home = probe_home(tmp_path, api_key="sk-dummy-probe", models=[PROBE_MODEL])
    envelope = probe_envelope(provider="absent-p")
    r = run_nd_call(envelope, home=home)
    assert r.returncode == 0, f"скрипт должен отвечать конвертом, а не падать:\n{r.stderr[:200]}"
    out = json.loads(r.stdout)
    assert out["ok"] is False and "absent-p" in out["error"], out
    r_noarg = run_nd_call(None, home=home)
    assert r_noarg.returncode != 0, (
        "argv-путь мёртв: вызов без конверта не крэшится — парс разборки argv не исполняется")


def test_substrate_branches_fail_closed(tmp_path):
    """Живые пробы веток fail-closed (external-dependencies/01): конфиг не
    читается, карточки провайдера нет, ключа нет — каждый отказ именует путь
    конфига zcode и недостающее; Ok-ветка не достигается ни одной."""
    # конфиг не читается: HOME без .zcode вообще
    empty = tmp_path / "empty-home"
    empty.mkdir()
    out = json.loads(run_nd_call(probe_envelope(), home=empty).stdout)
    assert out["ok"] is False, out
    assert "не читается" in out["error"] and "provider_config.json" in out["error"], out["error"]

    # карточка провайдера есть, но у запрошенного провайдера её нет
    out = json.loads(run_nd_call(probe_envelope(provider="absent-p"), home=probe_home(tmp_path / "h1", "sk-dummy-probe", [PROBE_MODEL])).stdout)
    assert out["ok"] is False, out
    assert "нет карточки провайдера «absent-p»" in out["error"], out["error"]
    assert "provider_config.json" in out["error"], out["error"]

    # карточка есть, ключа нет
    out = json.loads(run_nd_call(probe_envelope(), home=probe_home(tmp_path / "h2", None, [PROBE_MODEL])).stdout)
    assert out["ok"] is False, out
    assert "нет apiKey" in out["error"], out["error"]
    assert "probe-p" in out["error"] and "provider_config.json" in out["error"], out["error"]


def test_substrate_missing_model_fails_named_before_network(tmp_path):
    """Модель роли не добавлена провайдеру — именованный отказ ДО сетевого
    вызова (external-dependencies/01): и в вызывающем режиме (иначе все линзы
    сгорели бы HTTP-ошибкой посреди прогона), и в режиме пробы check."""
    home = probe_home(tmp_path / "h3", api_key="sk-dummy-probe", models=[])
    for mode in ({}, {"mode": "check"}):
        out = json.loads(run_nd_call(probe_envelope(**mode), home=home).stdout)
        assert out["ok"] is False, (mode, out)
        assert f"модель «{PROBE_MODEL}» не добавлена" in out["error"], out["error"]
        assert "probe-p" in out["error"] and "provider_config.json" in out["error"], out["error"]


def test_substrate_check_mode_passes_without_network(tmp_path):
    """Ok-ветка пробы (external-dependencies/01): карточка на месте, модель
    добавлена — check отвечает ok=true без сетевого вызова (выход до fetch),
    ключ в stdout не попадает."""
    home = probe_home(tmp_path / "h4", api_key="sk-dummy-probe", models=[PROBE_MODEL])
    r = run_nd_call(probe_envelope(mode="check"), home=home)
    assert r.returncode == 0, r.stderr[:200]
    assert "sk-dummy-probe" not in r.stdout, "утечка фейкового ключа в stdout"
    out = json.loads(r.stdout)
    assert out["ok"] is True, out
    assert out["provider"] == "probe-p" and out["baseUrl"] == "https://probe.invalid/v1", out


def test_args_provider_pinned():
    """args.provider пинен (external-dependencies/01): объявлен в шапке
    workflow с дефолтом neuraldeep-sub; дефолт и trim поведенчески на
    настоящем выражении из файла; вызов линзы берёт провайдера из args,
    а не из константы — замена провайдера без правки репо."""
    text = WORKFLOW.read_text(encoding="utf-8")
    m = re.search(r"\nargs:\n(.*?)\n\*/", text, re.S)
    assert m, "args-шапка workflow не читается"
    provider_entry = re.search(r"\n  provider:\n((?:    [^\n]*\n)+)", m.group(1))
    assert provider_entry, "args.provider пропал из шапки"
    assert "neuraldeep-sub" in provider_entry.group(1), "в описании provider нет дефолта"

    m2 = re.search(r"const ndProvider = (.*?);", text, re.S)
    assert m2, "выражение ndProvider дрейфовало"
    driver = (
        'const ND_PROVIDER_DEFAULT = "neuraldeep-sub";\n'
        f"const resolve = (args) => {m2.group(1)};\n"
        'console.log(JSON.stringify([resolve({}), resolve({provider: " custom-p "}), resolve({provider: "  "})]));\n'
    )
    with tempfile.NamedTemporaryFile("w", suffix=".mjs", delete=False) as fh:
        fh.write(driver)
        name = fh.name
    try:
        r = subprocess.run(["node", name], capture_output=True, text=True, timeout=60)
    finally:
        Path(name).unlink(missing_ok=True)
    assert r.returncode == 0, f"срез ndProvider упал:\n{r.stderr[:300]}"
    assert json.loads(r.stdout) == ["neuraldeep-sub", "custom-p", "neuraldeep-sub"]

    assert re.search(r"provider: ndProvider,", text), "вызов линзы не берёт провайдера из args"
    assert not re.search(r"provider: ND_PROVIDER\b", text), "провайдер захардкожен в обход args.provider"


def test_substrate_fail_closed_blocks_pinned():
    """Проба субстрата до линз и страховка полного отказа на месте
    (external-dependencies/01; пин переписан поимённо под lens-substrate-flash):
    проба живёт ТОЛЬКО в direct-ветке и стоит до кода линз — отказ субстрата
    не тратит вызовы; abort именует роль; страховка полного отказа общая."""
    text = WORKFLOW.read_text(encoding="utf-8")
    m = re.search(r"// BEGIN DIRECT LENSES.*?\n(.*?)// END DIRECT LENSES", text, re.S)
    assert m, "DIRECT LENSES block lost its markers"
    direct = m.group(1)
    m2 = re.search(r"// BEGIN SUBSTRATE CHECK.*?\n(.*?)// END SUBSTRATE CHECK", text, re.S)
    assert m2, "SUBSTRATE CHECK block lost its markers"
    assert 'mode: "check"' in m2.group(1) and "throw new Error" in m2.group(1) and "роль reviewer" in m2.group(1)
    # проба внутри direct-ветки и до исполнения линз
    assert m2.group(1) in direct, "проба субстрата вне direct-ветки"
    check_pos = direct.find("// BEGIN SUBSTRATE CHECK")
    task_pos = direct.find("const runLensTask")
    assert check_pos != -1 and task_pos != -1, "якоря порядка пробы потеряны в direct-ветке"
    assert check_pos < task_pos, "проба субстрата после кода линз — отказ тратит вызовы"
    m3 = re.search(r"// BEGIN SUBSTRATE TOTAL FAIL.*?\n(.*?)// END SUBSTRATE TOTAL FAIL", text, re.S)
    assert m3, "SUBSTRATE TOTAL FAIL block lost its markers"
    assert re.search(r"const substrateAbort = totalSubstrateFailure\(reviews, lensTasks\.length\);", text)
    assert 'if (substrateAbort !== "") throw new Error(substrateAbort);' in text


def test_total_substrate_failure_names_abort():
    """Страховка поведенчески (external-dependencies/01): все файлы failed —
    именованный abort с отказами; смешанное покрытие и ноль задач — пусто
    (гейт не абортит частичное покрытие)."""
    text = WORKFLOW.read_text(encoding="utf-8")
    m = re.search(r"// BEGIN SUBSTRATE TOTAL FAIL.*?\n(.*?)// END SUBSTRATE TOTAL FAIL", text, re.S)
    assert m, "SUBSTRATE TOTAL FAIL block lost its markers"
    body = m.group(1).replace(
        "(reviews: FileReview[], taskCount: number): string", "(reviews, taskCount)")
    assert body != m.group(1), "аннотация функции дрейфовала — срез не исполняется"
    driver = (
        f"{body}\n"
        "const failed = (n) => Array.from({ length: n }, (_, i) => ({ file: 'f' + i, failed: 'линза не ответила: x' + i }));\n"
        "const mixed = [{ file: 'a', failed: '' }, { file: 'b', failed: 'y' }];\n"
        "console.log(JSON.stringify([\n"
        "  totalSubstrateFailure(failed(3), 3).includes('ни один файл'),\n"
        "  totalSubstrateFailure(failed(2), 2).includes('линза не ответила'),\n"
        "  totalSubstrateFailure(mixed, 2) === '',\n"
        "  totalSubstrateFailure([], 0) === '',\n"
        "]));\n"
    )
    with tempfile.NamedTemporaryFile("w", suffix=".mjs", delete=False) as fh:
        fh.write(driver)
        name = fh.name
    try:
        r = subprocess.run(["node", name], capture_output=True, text=True, timeout=60)
    finally:
        Path(name).unlink(missing_ok=True)
    assert r.returncode == 0, f"срез totalSubstrateFailure упал:\n{r.stderr[:300]}"
    assert all(json.loads(r.stdout)), r.stdout


def test_nd_call_reads_envelope_from_last_argv():
    # node -e съедает "--": поиск сепаратора давал -1, обращение уходило в
    # argv[0] (путь к node) и валило все линзы JSON.parse-ом (гейт v3).
    # Конверт — строго последний элемент argv.
    src = nd_call_source()
    assert "process.argv[process.argv.length - 1]" in src
    assert 'indexOf("--")' not in src


def test_lens_pool_respects_tariff_concurrency():
    """Срез LENS TASKS поведенчески: задач ровно по паре файл×линза (без
    нарезки/дедупа). Пул «воркеры = min(cap, N)» — поведенческий прогон среза
    POOL LOOP с инструментированным runLensTask (verified confirm-рана
    2026-10-09: лексические якоря проходила и мутация «мёртвый пул +
    несвязанный Promise.all», maxInFlight 4 → 10); пул живёт ТОЛЬКО в
    direct-ветке — субагентная параллелит все задачи без своего пула."""
    text = WORKFLOW.read_text(encoding="utf-8")
    m = re.search(r"// BEGIN LENS TASKS.*?\n(.*?)// END LENS TASKS", text, re.S)
    assert m, "LENS TASKS block lost its markers"
    tasks_slice = m.group(1)
    assert "lensProfile" not in tasks_slice, "тариф/пул протёк в общий блок задач"
    mp = re.search(r"// BEGIN LENS POOL LOOP.*?\n(.*?)// END LENS POOL LOOP", text, re.S)
    assert mp, "LENS POOL LOOP block lost its markers"
    md = re.search(r"// BEGIN DIRECT LENSES.*?\n(.*?)// END DIRECT LENSES", text, re.S)
    ms = re.search(r"// BEGIN SUBAGENT LENSES.*?\n(.*?)// END SUBAGENT LENSES", text, re.S)
    assert md and ms, "маркеры веток субстрата потеряны"
    direct, subagent = md.group(1), ms.group(1)
    assert mp.group(1) in direct, "пул не в direct-ветке"
    mworkers = re.search(r"^const LENS_WORKERS = .*?;$", direct, re.M)
    assert mworkers, "строка воркеров пула потеряна в direct-ветке"
    assert "LENS_WORKERS" not in subagent, "пул протёк в субагентную ветку"
    assert "Promise.all(lensTasks.map" in subagent, "субагентная ветка не мапит все задачи"
    outside = re.sub(r"// BEGIN DIRECT LENSES.*?\n(.*?)// END DIRECT LENSES", "", text, flags=re.S)
    assert "length: LENS_WORKERS" not in outside, "параллелизм пула рождается вне direct-ветки"
    # поведенческий прогон: N=10 задач, cap=4 → максимум одновременных ровно 4
    driver = (
        "const activeLenses = [{ lens: { id: 'logic' }, files: Array.from({ length: 10 }, (_, i) => 'f' + i + '.py') }];\n"
        f"{tasks_slice}\n"
        "const LENS_CONCURRENCY = 4;\n"
        f"{mworkers.group(0)}\n"
        "let inFlight = 0, maxInFlight = 0, done = 0;\n"
        "const runLensTask = async () => {\n"
        "  inFlight += 1; maxInFlight = Math.max(maxInFlight, inFlight);\n"
        "  await new Promise((resolve) => setTimeout(resolve, 5));\n"
        "  inFlight -= 1; done += 1;\n"
        "};\n"
        f"{mp.group(1)}\n"
        "console.log(JSON.stringify({ maxInFlight, done, tasks: lensTasks.length }));\n"
    )
    r = run_node_slice(driver)
    assert r.returncode == 0, f"срез POOL LOOP упал:\n{r.stderr[:300]}"
    out = json.loads(r.stdout)
    assert out["tasks"] == 10, "пар файл×линза должно быть 10 — нарезка/дедуп"
    assert out["done"] == 10, f"пул выполнил {out['done']} из 10 задач"
    assert out["maxInFlight"] == 4, (
        f"воркеры = min(4, 10) = 4, прогон дал {out['maxInFlight']} — потолок не держится")


def test_nd_call_closes_credentials_contour_on_zcode():
    src = nd_call_source()
    # креды и baseUrl — только из карточки провайдера zcode
    assert 'join(os.homedir(), ".zcode", "v2", "provider_config.json")' in src
    # omp/coddy — лишние зависимости контура, их быть не должно
    assert ".omp" not in src and "models.yml" not in src and "coddy" not in src.lower()
    # ключ уходит только в заголовок Authorization
    assert '"Bearer " + rule.config.access.apiKey' in src
    # значение ключа не печатается ни в одном исходе: в console.log нет
    # обращения к access.apiKey (слово в прозе диагностики — можно)
    for line in src.splitlines():
        if "console.log" in line:
            assert "access.apiKey" not in line, f"ключ утекает в stdout: {line.strip()}"


def test_nd_call_stdout_is_envelope_only():
    src = nd_call_source()
    # stdout — только конверт {ok, content|error, finish, usage}: печатается
    # ровно JSON.stringify, никаких сырых тел ответов целиком
    assert src.count("console.log(") >= 4
    for line in src.splitlines():
        if "console.log(" in line:
            assert "JSON.stringify" in line, f"печать не-JSON в stdout: {line.strip()}"


def test_nd_call_never_prints_api_key(tmp_path):
    """Поведенческая проверка утечки ключа (verified гейта v5: presence-
    ассерты пропускали фактическую утечку многострочным вызовом): каждый
    stdout-фрагмент скрипта обязан быть валидным JSON-конвертом — вписанная
    утечка «DEBUG <ключ>» ломает парс фрагмента, тест-паттерн её ловит."""
    marker = "console.log(JSON.stringify({"
    assert marker in nd_call_source(), "формат ok-конверта дрейфовал"
    leaky = nd_call_source().replace(
        marker,
        'console.log("DEBUG " + rule.config.access.apiKey);\n  ' + marker, 1)
    assert leaky != nd_call_source(), "мутация утечки не применилась"
    with tempfile.NamedTemporaryFile("w", suffix=".cjs", delete=False) as fh:
        fh.write(leaky)
        name = fh.name
    try:
        # с несуществующим провайдером утечки не будет — проверяем сам канал:
        # тест-паттерн ловит любую печать вне JSON.stringify-конверта;
        # HOME подменён — ветка не зависит от машины (мутация встаёт в ветку
        # «конфиг не читается», живой путь — конверт отсутствующей карточки)
        home = probe_home(tmp_path, api_key="sk-dummy-probe", models=[PROBE_MODEL])
        env = os.environ | {"HOME": str(home)}
        r = subprocess.run(
            ["node", name, "--", json.dumps({"provider": "no-such-provider", "model": "m", "prompt": "p"})],
            capture_output=True, text=True, timeout=60, env=env)
    finally:
        Path(name).unlink(missing_ok=True)
    assert r.returncode == 0
    assert r.stdout.strip(), "скрипт ничего не напечатал — канал пуст"
    for fragment in r.stdout.strip().splitlines():
        json.loads(fragment)  # утечка-строка "DEBUG sk-…" здесь не распарсится


def test_lens_outcome_classifier_names_failures():
    """Именованные отказы линзы пинены поведенчески (verified гейта v5:
    мутации «бросить вместо отказа» и «удалить ветку length» проходили
    сьют зелёным)."""
    driver = (
        f"{lens_json_source()}\n"
        "const cases = [\n"
        '  { env: { ok: false, error: "HTTP 429: потолок одновременных" }, candidate: null, err: "HTTP 429" },\n'
        '  { env: { ok: true, content: "думание без JSON", finish: "length" }, candidate: null, err: "потолок вывода тарифа" },\n'
        '  { env: { ok: true, content: "проза без массива", finish: "stop" }, candidate: null, err: "в ответе нет JSON-массива" },\n'
        '  { env: { ok: true, content: "```json\\n[\\"x\\"]\\n```", finish: "stop" }, candidate: "[\\"x\\"]", err: "" },\n'
        "];\n"
        "const out = cases.map((c) => { const o = classifyLensOutcome(c.env); return [o.candidate === c.candidate, o.error.includes(c.err)]; });\n"
        "console.log(JSON.stringify(out));\n"
    )
    with tempfile.NamedTemporaryFile("w", suffix=".mjs", delete=False) as fh:
        fh.write(driver)
        name = fh.name
    try:
        r = subprocess.run(["node", name], capture_output=True, text=True, timeout=60)
    finally:
        Path(name).unlink(missing_ok=True)
    assert r.returncode == 0, f"классификатор упал:\n{r.stderr}"
    for candidate_ok, error_ok in json.loads(r.stdout):
        assert candidate_ok and error_ok


def run_parser(samples: dict) -> dict:
    driver = (
        f"{lens_json_source()}\n"
        f"const S = {json.dumps(samples, ensure_ascii=False)};\n"
        "const out = {};\n"
        "for (const [k, v] of Object.entries(S)) out[k] = extractLensJson(v);\n"
        "console.log(JSON.stringify(out));\n"
    )
    with tempfile.NamedTemporaryFile("w", suffix=".mjs", delete=False) as fh:
        fh.write(driver)
        name = fh.name
    try:
        r = subprocess.run(["node", name], capture_output=True, text=True, timeout=60)
    finally:
        Path(name).unlink(missing_ok=True)
    assert r.returncode == 0, f"node упал на срезе LENS JSON:\n{r.stderr}"
    return json.loads(r.stdout)


def test_lens_json_extracts_fenced_plain_and_bare():
    bare = json.dumps(
        [{"where": "x:1 [см]", "claim": "скобка] внутри строки", "evidence": "esc \" q"}],
        ensure_ascii=False)
    samples = {
        "fenced": "размышления…\n```json\n[{\"file\": \"a.py\", \"findings\": [], \"summary\": \"\", \"failed\": \"\"}]\n```\n",
        "fenced_last_wins": "```json\n[{\"stale\": 1}]\n```\nэхо-проза\n```json\n[{\"file\": \"b.py\"}]\n```\n",
        "plain_fence": "```\n[{\"file\": \"c.py\"}]\n```",
        # обрезанный фенс: кандидат не извлекается вовсе → именованный отказ
        # линзы с ретраем (негатив-кейс линзы logic из гейта 07)
        "truncated_fence": "```json\n[{\"file\": \"d.py\", \"claim\": \"оборвано",
        # закрытый фенс с невалидным JSON: извлечение отдаёт тело как есть —
        # валидность решает JSON.parse на следующем слое
        "invalid_json_fence": "```json\n[{\"file\": \"e.py\", }]\n```",
        "bare_among_prose": f"Вот находки:\n{bare} и хвост.",
        "no_array": "Находок нет, файл чист.",
    }
    out = run_parser(samples)
    assert json.loads(out["fenced"])[0]["file"] == "a.py"
    assert json.loads(out["fenced_last_wins"])[0] == {"file": "b.py"}
    assert json.loads(out["plain_fence"])[0] == {"file": "c.py"}
    assert out["truncated_fence"] is None
    assert out["invalid_json_fence"] == '[{"file": "e.py", }]'
    parsed_bare = json.loads(out["bare_among_prose"])
    assert parsed_bare[0]["claim"] == "скобка] внутри строки"
    assert out["no_array"] is None


def test_repair_escapes_raw_newlines_inside_strings():
    # живая приёмка: линза tests дважды дала JSON с сырыми переводами внутри
    # claim — «Unterminated string» на одной и той же позиции; сэмпл строится
    # из валидного JSON подменой экранированного \n на сырой перевод.
    # Починка экранирует переводы только внутри литералов, остальное не трогая
    good = json.dumps(
        [{"file": "a.py", "claim": "строка1\nстрока2 \"q\"", "findings": []}],
        ensure_ascii=False)
    broken = good.replace("строка1\\nстрока2", "строка1\nстрока2")
    assert "\\n" not in broken.split("claim")[1].split(",")[0], "сэмпл должен нести сырой перевод"
    driver = (
        f"{lens_json_source()}\n"
        f"const v = JSON.parse(repairJsonStrings({json.dumps(broken, ensure_ascii=False)}));\n"
        "console.log(JSON.stringify(v));\n"
    )
    with tempfile.NamedTemporaryFile("w", suffix=".mjs", delete=False) as fh:
        fh.write(driver)
        name = fh.name
    r = subprocess.run(["node", name], capture_output=True, text=True, timeout=60)
    Path(name).unlink()
    assert r.returncode == 0, f"node упал на срезе repair:\n{r.stderr}"
    assert json.loads(r.stdout)[0]["claim"] == "строка1\nстрока2 \"q\""

    # позитивный путь: валидный JSON починка не меняет (гейт 07: обратная
    # ветка не была покрыта)
    driver = (
        f"{lens_json_source()}\n"
        f"const same = repairJsonStrings({json.dumps(good, ensure_ascii=False)}) === {json.dumps(good, ensure_ascii=False)};\n"
        "console.log(same);\n"
    )
    with tempfile.NamedTemporaryFile("w", suffix=".mjs", delete=False) as fh:
        fh.write(driver)
        name = fh.name
    r = subprocess.run(["node", name], capture_output=True, text=True, timeout=60)
    Path(name).unlink()
    assert r.returncode == 0
    assert r.stdout.strip() == "true"


def test_lens_profile_pins_unlim_constants():
    """Профиль unlim-xl дублирует тарифные факты из dependencies.md
    (external-dependencies/04, решения оператора 2026-10-07/08: потолки в
    карточку zcode не входят, живут датированными наблюдениями, профиль в
    репо обновляется руками). Поведенческий прогон среза: карта отдаёт все
    семь значений ровно как в доке — расхождение профиля с наблюдением
    ловит сьют."""
    driver = (
        'const args = { reviewerModel: "qwen3.6-unlim-xl" };\n'
        f"{lens_profile_source()}\n"
        "console.log(JSON.stringify(lensProfile));\n"
    )
    r = run_node_slice(driver)
    assert r.returncode == 0, f"срез профиля упал:\n{r.stderr[:300]}"
    assert json.loads(r.stdout) == {
        "maxFindings": 8,
        "maxFiles": 20,
        "maxDiffLines": 2000,
        "lensInlineLines": 6000,
        "lensRetries": 1,
        "lensCallTimeoutMs": 1_500_000,
        "lensConcurrency": 4,
    }


def test_lens_profile_unknown_model_fails_named():
    """Фолбэка нет (решение оператора 2026-10-08): модель роли без профиля —
    именованный отказ до линз, диагност называет модель, карту для правки и
    место тарифных фактов. Мутационная проба: пустая карта роняет и
    дефолтную модель — спрятанного дефолта внутри резолвера быть не должно."""
    driver = (
        "const args = {};\n"
        f"{lens_profile_source()}\n"
        "const out = {};\n"
        'try { resolveLensProfile("no-such-model"); out.refused = false; }\n'
        'catch (e) { out.refused = true; out.msg = String(e.message); }\n'
        "for (const k of Object.keys(LENS_PROFILES)) delete LENS_PROFILES[k];\n"
        'try { resolveLensProfile("qwen3.6-unlim-xl"); out.hiddenDefault = false; }\n'
        "catch (e) { out.hiddenDefault = true; }\n"
        "console.log(JSON.stringify(out));\n"
    )
    r = run_node_slice(driver)
    assert r.returncode == 0, f"срез отказа упал:\n{r.stderr[:300]}"
    out = json.loads(r.stdout)
    assert out["refused"], "модель без профиля не отказана — фолбэк протёк в резолвер"
    assert out["hiddenDefault"], "после опустошения карты дефолтная модель разрешилась — в резолвере спрятанный дефолт"
    assert "no-such-model" in out["msg"], "отказ не называет модель"
    assert "LENS_PROFILES" in out["msg"], "отказ не называет карту для правки"
    assert "dependencies.md" in out["msg"], "отказ не указывает место тарифных фактов"


def test_lens_profile_flows_into_constants():
    """Пин переписан поимённо под lens-substrate-flash: тарифные константы
    читают профиль ТОЛЬКО внутри direct-ветки — живыми строками (^-привязка,
    урок гейта 04: голый str.index не различает комментарии), под guard'ом
    if (substrate === "direct") (verified confirm-рана 2026-10-09: перенос
    блока профиля над guard'ом и присвоение-в-комментарии проходили зелёным);
    у субагентной ветки — литералы гигиены вне карты; MAX_FINDINGS/MAX_FILES —
    константы гейта для обеих веток (из профиля не читаются). «Один файл
    на вызов» — инвариант гейта, ручки filesPerCall в профиле нет."""
    text = WORKFLOW.read_text(encoding="utf-8")
    m = re.search(r"// BEGIN SUBSTRATE CONSTANTS.*?\n(.*?)// END SUBSTRATE CONSTANTS", text, re.S)
    assert m, "SUBSTRATE CONSTANTS block lost its markers"
    span, outside = m.group(1), text.replace(m.group(0), "")
    for const, key in (
        ("MAX_DIFF_LINES", "maxDiffLines"),
        ("LENS_INLINE_LINES", "lensInlineLines"),
        ("LENS_RETRIES", "lensRetries"),
        ("LENS_CALL_TIMEOUT_MS", "lensCallTimeoutMs"),
        ("LENS_CONCURRENCY", "lensConcurrency"),
    ):
        line = rf"^\s*{const} = lensProfile\.{key};\s*$"
        assert re.search(line, span, re.M), f"{const} не читает профиль живой строкой в direct-ветке"
        assert not re.search(line, outside, re.M), f"{const} читает профиль вне direct-ветки"
    # субагентная ветка — литералы гигиены, не тариф
    assert re.search(r"^\s*MAX_DIFF_LINES = \d+;\s*$", span, re.M), "литерал гигиены субагентной ветки пропал"
    assert re.search(r"^\s*LENS_INLINE_LINES = \d+;\s*$", span, re.M), "литерал гигиены субагентной ветки пропал"
    # константы гейта обеих веток — литералы, профиль на них не влияет
    assert "const MAX_FINDINGS = 8;" in text and "const MAX_FILES = 20;" in text
    assert "MAX_FINDINGS = lensProfile" not in text and "MAX_FILES = lensProfile" not in text
    assert "filesPerCall" not in text, "«один файл на вызов» протёк в профиль как ручка"

    def line_pos(pattern: str, src: str) -> int:
        mm = re.search(pattern, src, re.M)
        assert mm, f"якорь порядка потерян: {pattern}"
        return mm.start()

    # контейнмент: guard direct-ветки стоит ДО блока профиля (перенос над
    # guard'ом сделал бы профиль безусловным)
    guard = span.find('if (substrate === "direct") {')
    profile = span.find("// BEGIN LENS PROFILE")
    assert guard != -1, "guard direct-ветки потерян в блоке констант"
    assert profile != -1, "блок LENS PROFILE потерян в блоке констант"
    assert guard < profile, "профиль резолвится вне guard'а direct-ветки"
    # порядок: резолвер профиля до первого присвоения константе
    resolver = r"^\s*const lensProfile = resolveLensProfile\(reviewerModel\);\s*$"
    assert line_pos(r"^\s*// BEGIN LENS PROFILE", span) < line_pos(resolver, span), (
        "резолвер профиля не после маркера блока")
    assert line_pos(resolver, span) < line_pos(r"^\s*MAX_DIFF_LINES = lensProfile\.maxDiffLines;", span), (
        "профиль резолвится после констант — они прочитают мусор")
    # тарифных литералов вне карты профилей нет — все пять тарифных имён
    assert not re.search(
        r"const (MAX_DIFF_LINES|LENS_INLINE_LINES|LENS_RETRIES|LENS_CALL_TIMEOUT_MS|LENS_CONCURRENCY) = \d",
        outside), "тарифная константа задана литералом вне карты профилей"


def test_substrate_args_resolution():
    """Новый пин (lens-substrate-flash): шапка субстрата поведенчески —
    пусто = subagent; неизвестное значение — именованный возврат, не ранняя
    смерть; reviewerModel/provider при дефолтном субстрате — именованный
    abort («имеет смысл только с substrate=direct»), не молчаливый игнор;
    пустые (после trim) значения не аборят; позитивный путь direct + явные
    reviewerModel/provider проходит (verified confirm-рана 2026-10-09:
    безусловный guard, убивающий весь direct-фолбэк, зелёным не отличался)."""
    text = WORKFLOW.read_text(encoding="utf-8")
    m = re.search(r"// BEGIN SUBSTRATE ARGS.*?\n(.*?)// END SUBSTRATE ARGS", text, re.S)
    assert m, "SUBSTRATE ARGS block lost its markers"
    slice_src = m.group(1).replace(
        "const directOnlyArgs: string[] = [];", "const directOnlyArgs = [];")
    assert "string[]" not in slice_src, "TS-аннотация в срезе не снята — node срез не исполнит"
    driver = (
        "async function run(args) {\n"
        f"{slice_src}\n"
        "return { ok: true, substrate };\n"
        "}\n"
        "const out = [];\n"
        "out.push((await run({})).substrate === 'subagent');\n"
        "const unknown = await run({ substrate: 'wat' });\n"
        "out.push(unknown.ok === undefined && unknown.conclusion.includes('неизвестный substrate'));\n"
        "let aborted = '';\n"
        "try { await run({ reviewerModel: 'x' }); } catch (e) { aborted = String(e.message); }\n"
        "out.push(aborted.includes('args.reviewerModel') && aborted.includes('только с substrate=direct'));\n"
        "aborted = '';\n"
        "try { await run({ provider: 'p' }); } catch (e) { aborted = String(e.message); }\n"
        "out.push(aborted.includes('args.provider') && aborted.includes('только с substrate=direct'));\n"
        "out.push((await run({ reviewerModel: ' ', provider: ' ' })).substrate === 'subagent');\n"
        "out.push((await run({ substrate: 'direct' })).substrate === 'direct');\n"
        "out.push((await run({ substrate: 'direct', reviewerModel: 'x', provider: 'p' })).substrate === 'direct');\n"
        "console.log(JSON.stringify(out));\n"
    )
    r = run_node_slice(driver)
    assert r.returncode == 0, f"срез шапки субстрата упал:\n{r.stderr[:300]}"
    assert all(json.loads(r.stdout)), r.stdout


def test_nd_call_absent_from_subagent_branch():
    """Новый пин (lens-substrate-flash, absence-якорь — урок гейта 04:
    presence-якорь дополняется absence-проверкой): в субагентной ветке нет
    ND_CALL, прямых world.run-вызовов API и JSON-ремонта — там типизированный
    ask; ND_CALL живёт только в direct-ветке."""
    text = WORKFLOW.read_text(encoding="utf-8")
    md = re.search(r"// BEGIN DIRECT LENSES.*?\n(.*?)// END DIRECT LENSES", text, re.S)
    ms = re.search(r"// BEGIN SUBAGENT LENSES.*?\n(.*?)// END SUBAGENT LENSES", text, re.S)
    assert md and ms, "маркеры веток субстрата потеряны"
    direct, subagent = md.group(1), ms.group(1)
    assert "BEGIN ND CALL" in direct and "ND_CALL" in direct, "ND_CALL потерян в direct-ветке"
    assert "ND_CALL" not in subagent, "ND_CALL протёк в субагентную ветку"
    assert "world.run(" not in subagent, "прямой вызов API в субагентной ветке"
    assert "extractLensJson" not in subagent and "repairJsonStrings" not in subagent, (
        "JSON-в-фенсе протёк в субагентную ветку")


def test_subagent_lens_one_typed_ask_per_pair():
    """Новый пин (lens-substrate-flash): инвариант «одна пара файл×линза =
    ровно один agent().ask» — сайт вызова ask в субагентной ветке один, ветка
    мапит все задачи по парам, результат типизированный (LensReviewResult),
    явной model в agent() нет (модель линз — subagent_model воркфлоу);
    отказ вызова изолирован в catch, именует линзу, идёт через redact и
    ОБЯЗАН записать failed в results именно внутри catch (verified
    confirm-рана 2026-10-09: presence-пин проходил catch без записи — файл
    молча выпадал из coverage)."""
    text = WORKFLOW.read_text(encoding="utf-8")
    ms = re.search(r"// BEGIN SUBAGENT LENSES.*?\n(.*?)// END SUBAGENT LENSES", text, re.S)
    assert ms, "SUBAGENT LENSES block lost its markers"
    subagent = ms.group(1)
    assert "interface LensReviewResult" in text, "типизированный интерфейс линзы потерян"
    assert subagent.count(".ask<LensReviewResult>(") == 1, "ask не один на ветку"
    assert subagent.count("await agent(") == 1, "сайт agent() не один"
    assert "model:" not in subagent, (
        "явная model в agent() молча перекрывает subagent_model воркфлоу")
    assert "lensTasks.map((_, i) => runSubagentLensTask(i))" in subagent, (
        "задачи не мапятся по парам файл×линза")
    mcatch = re.search(r"catch \(e\) \{(.*?)\n  \}", subagent, re.S)
    assert mcatch, "catch-ветка отказа вызова потеряна"
    catch = mcatch.group(1)
    assert 'results[taskIndex] = { review: { file: file.path, findings: [], summary: "", failed }' in catch, (
        "catch не пишет failed в results — отказавший файл молча выпадает из coverage")
    assert "${lens.id}" in catch, "отказ вызова не именует линзу"
    assert "redact(" in catch, "текст исключения уходит наружу без redact"
    # без своего ретрая: повторы решает рантайм хоста (dynamic-workflows §16.3)
    assert "retry" not in subagent.lower() and "attempt" not in subagent.lower(), (
        "у субагентной ветки появился свой ретрай")
