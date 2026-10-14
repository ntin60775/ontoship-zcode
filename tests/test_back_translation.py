"""Contract of the counter-layer run (behavior-reel/03). The workflow takes the
masked drafts, the reels and the quote carrier as THREE SEPARATE string args —
the masking is visible in the run's args; the restator's ask is assembled from
the ticket body ONLY (structural blindness: the builder does not even accept
the reel or the quotes), the quote comparison is mechanical character-level
equality in code (with all roles on one model family it is the only machine
prefilter of operator→ticket substitution — the honest frame the SKILL fixes).
Named refusals instead of throws for assembly violations (unmasked input,
marker format, NN pairing, empty carrier); zero findings are NAMED «не найдено»,
never skipped. The behavioral half runs the real functions extracted from the
live file under node's type stripping; the distorted-quote case is the
load-bearing mutation direction (a comparator that «forgives» wording drift
goes red there), and the detector probes (maskingViolation firing on an
injected ## Reel header, the zero-naming anchor sensitive to its own erasure)
keep the detectors alive. The sentinel probes pin the ask topology: material
of each movement is exactly its own input — the restator never sees the reel
or the quotes, the differ never sees the body or the quotes, the hostile ask
sees all three (its reference is criteria + quotes)."""
import json
import re
import subprocess
import tempfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
WF = REPO / "skills" / "to-tickets" / "back-translation.workflow.ts"


def _text() -> str:
    return WF.read_text(encoding="utf-8")


def run_node_slice(driver: str, suffix: str = ".mts") -> subprocess.CompletedProcess:
    """Прогон среза воркфлоу под node: файл во временнике, rc/stdout наружу.
    Для .mts-срезов (TS-аннотации не зачищаются + top-level await): node ≥ 23
    снимает типы сам, 22.6–22.x идёт через --experimental-strip-types; ниже
    22.6 нет ни того, ни другого — именованный skip (минимум из
    docs/ops/install.md, идиома test_reviewer_substrate)."""
    cmd = ["node"]
    if suffix == ".mts":
        v = subprocess.run(["node", "-p", "process.versions.node"],
                           capture_output=True, text=True, timeout=60)
        assert v.returncode == 0, f"node не отвечает версией:\n{v.stderr[:200]}"
        version = tuple(int(x) for x in v.stdout.strip().split(".")[:3])
        if version >= (23, 0, 0):
            pass
        elif version >= (22, 6, 0):
            cmd.append("--experimental-strip-types")
        else:
            pytest.skip(
                f"node {v.stdout.strip()} < 22.6: ни снятия типов, ни "
                "--experimental-strip-types — .mts-срезы непрогоняемы; минимум в docs/ops/install.md")
    with tempfile.NamedTemporaryFile("w", suffix=suffix, delete=False, encoding="utf-8") as fh:
        fh.write(driver)
        name = fh.name
    try:
        return subprocess.run([*cmd, name], capture_output=True, text=True, timeout=120)
    finally:
        Path(name).unlink(missing_ok=True)


def structural_window(text: str, anchor: str, closing: str) -> str:
    """Окно от единственной строки с якорем до закрывающей строки включительно
    (идиома test_reviewer_substrate: голый str.index ловит комментарии)."""
    lines = text.splitlines(keepends=True)
    starts = [i for i, l in enumerate(lines) if anchor in l]
    assert len(starts) == 1, f"якорь неуникален или потерян: {anchor!r} ({len(starts)})"
    ends = [i for i in range(starts[0], len(lines)) if re.match(closing, lines[i])]
    assert ends, f"закрывающая строка {closing!r} не найдена после {anchor!r}"
    return "".join(lines[starts[0]:ends[0] + 1])


def fn(name: str) -> str:
    """Тело функции живого файла по её сигнатурной строке."""
    return structural_window(_text(), f"function {name}(", r"^}$")


def test_args_header_is_three_separate_inputs():
    """Маскирование видно в args рана: шапка — ровно plan/tickets/reels/quotes,
    все обязательные; лишний вход (например, слитый «всё в одном» аргумент)
    ломает якорь."""
    m = re.search(r"\nargs:\n(.*?)\n\*/", _text(), re.S)
    assert m, "args-шапка workflow не читается"
    keys = tuple(re.findall(r"^  (\w+):$", m.group(1), re.M))
    assert keys == ("plan", "tickets", "reels", "quotes"), f"args-шапка дрейфовала: {keys}"
    required = re.findall(r"^    required: (\w+)$", m.group(1), re.M)
    assert required == ["true"] * 4, f"обязательность входов дрейфула: {required}"


def test_yaml_header_has_no_colon_space_in_description():
    """Двоеточие с пробелом в YAML-описании ломает парсинг шапки (урок,
    ловленный дважды) — описание обязано жить без «: » вне кавычек."""
    m = re.search(r"^description: (.+)$", _text(), re.M)
    assert m, "строка description не найдена"
    assert ": " not in m.group(1), f"«: » в description сломает invalid_yaml: {m.group(1)[:80]}"


def test_counter_constants_are_block_literals():
    """Гигиена прогона — литералы блока констант (мораторий: механизм один
    файл, константы не производятся извне)."""
    m = re.search(r"// BEGIN COUNTER CONSTANTS.*?\n(.*?)// END COUNTER CONSTANTS", _text(), re.S)
    assert m, "COUNTER CONSTANTS block lost its markers"
    for line in ("const MAX_FINDINGS_PER_TICKET = 6;", "const MAX_HOSTILE_PER_TICKET = 4;",
                 "const MAX_TICKETS = 12;"):
        assert re.search(rf"^{re.escape(line)}$", m.group(1), re.M), f"{line} потерян как литерал блока"


def test_zero_findings_are_named_not_skipped():
    """Ноль назван «не найдено» — оба класса именуются в conclusion всегда,
    включая пустой исход. Якорь чувствителен: стёртая строка роняет его
    (иначе якорь матчит мусор и зелёнит пропавший ноль)."""
    text = _text()
    anchor = re.compile(r"^    \? `Сверка Целей с эталоном: не найдено\.`$", re.M)
    anchor2 = re.compile(r"^    \? `Рестатизация vs лента: не найдено\.`$", re.M)
    for a in (anchor, anchor2):
        assert a.search(text), "conclusion потерял именование «не найдено» одного из классов"
        hit = a.search(text)
        assert not a.search(text.replace(hit.group(0), "")), "якорь «не найдено» нечувствителен к стиранию"


def test_extraction_markers_present():
    """Маркеры блоков — контракт тестов; потерянный маркер = потерянный пин."""
    for marker in ("BEGIN GOALS PARSE", "END GOALS PARSE", "BEGIN VIOLATIONS", "END VIOLATIONS",
                   "BEGIN QUOTE COMPARE", "END QUOTE COMPARE", "BEGIN COUNTER ASKS", "END COUNTER ASKS"):
        assert marker in _text(), f"маркер {marker} потерян"


def test_ask_topology_wired_per_movement():
    """Проводка асков: рестатизатор — только тело (слепота), дифф — лента +
    рестатизация, враждебные — тело + цитаты + лента; по одному типизированному
    agent().ask на движение×тикет."""
    text = _text()
    for anchor in (
        r"restatorAsk\(t\.body\)",
        r"differAsk\(reel\.body, out\.restatement\)",
        r"hostileAsk\(t\.body, quotesArg, reel\.body\)",
    ):
        assert re.search(anchor, text), f"проводка аска отвалилась: {anchor}"
    for name in ("restator", "differ", "hostile"):
        assert re.search(rf"counter-\$\{{t\.id\}}-{name}", text), f"вызов agent() движения {name} потерян"


def test_assembly_refusals_wired_fail_closed():
    """Отказы сборки — проводка на верхнем уровне рана: маскирование, формат
    маркеров, парность, носитель; каждый до любого аска."""
    text = _text()
    for anchor in (
        r"^const maskV = maskingViolation\(ticketsArg\);$",
        r'^if \(maskV !== ""\) \{$',
        r"^const pairV = pairingViolation\(ticketBlocks, reelBlocks\);$",
        r"^const carrierV = carrierViolation\(quotesArg\);$",
    ):
        assert re.search(anchor, text, re.M), f"fail-closed проводка отвалилась: {anchor}"


def test_behavioral_matrix():
    """Матрица живых функций под node: разбор маркеров, разбор целей и
    носителя, посимвольная сверка (искажённая цитата — мутационное
    направление: «прощающий» компаратор краснеет здесь), именованные отказы
    сборки, сентовые пробы слепоты асков."""
    driver = (
        "\n".join((
            fn("parseTicketBlocks"),
            fn("parseGoals"),
            fn("parseCarrier"),
            fn("maskingViolation"),
            fn("pairingViolation"),
            fn("carrierViolation"),
            fn("compareGoals"),
            fn("restatorAsk"),
            fn("differAsk"),
            fn("hostileAsk"),
        ))
        + r"""
const out = {};
const ticketsTwo = parseTicketBlocks("=== ТИКЕТ 01: Первый ===\nтело один\nстрока два\n=== ТИКЕТ 02: Второй ===\nтело два\n");
out.blocksTwo = ticketsTwo.length === 2 && ticketsTwo[0].id === "01" && ticketsTwo[0].title === "Первый" && ticketsTwo[0].body === "тело один\nстрока два" && ticketsTwo[1].id === "02";
out.blocksNone = parseTicketBlocks("просто текст без маркеров").length === 0;
const goals = parseGoals(
  "- Цель (дословно: «дубликаты обязаны ловиться и при полном совпадении строк») → Вход: … → Наблюдаемый выход: …\n" +
  "- Цель (парафраз): похожая строка флагуется → Вход: … → Наблюдаемый выход: …\n" +
  "- Цель без маркера вообще → Вход: … → Наблюдаемый выход: …\n" +
  "проза секции без слова цели\n");
out.goalsVerbatim = goals.verbatim.length === 1 && goals.verbatim[0].quote === "дубликаты обязаны ловиться и при полном совпадении строк" && goals.verbatim[0].line === 1;
out.goalsParaphrase = goals.paraphrase === 1;
out.goalsUnmarked = goals.unmarked.length === 1 && goals.unmarked[0].line === 3;
const carrier = parseCarrier("### Цитаты оператора (дословно)\n\n- «дубликаты обязаны ловиться и при полном совпадении строк»\n- «порог сходности крутится ключом, дефолт не трогаем»\n- парафраз: выгрузка без танцев с кодировкой\n");
out.carrierQuotes = carrier.carrier.length === 2 && carrier.carrier[1] === "порог сходности крутится ключом, дефолт не трогаем";
out.carrierParaphrases = carrier.paraphrases.length === 1;
const clean = compareGoals("01", goals, carrier.carrier).filter((d) => d.klass === "quote-mismatch" && d.claim.includes("не совпадает"));
out.compareClean = clean.length === 0;
const distorted = parseGoals("- Цель (дословно: «дубликаты должны ловиться и при полном совпадении строк») → Вход: … → Наблюдаемый выход: …\n");
const dOut = compareGoals("01", distorted, carrier.carrier);
out.compareDistorted = dOut.length === 1 && dOut[0].klass === "quote-mismatch" && dOut[0].evidence.includes("должны");
out.compareUnmarked = compareGoals("02", goals, carrier.carrier).some((d) => d.klass === "quote-mismatch" && d.claim.includes("без маркера"));
out.maskClean = maskingViolation("тело без ленты") === "";
const maskDirty = maskingViolation("тело\n## Reel\n- Цель …\n");
out.maskDirty = maskDirty !== "" && maskDirty.includes("не замаскирован");
const t01 = { id: "01", title: "a", body: "b" };
const t02 = { id: "02", title: "c", body: "d" };
out.pairOk = pairingViolation([t01, t02], [t02, t01]) === "";
const pairMiss = pairingViolation([t01, t02], [t01]);
out.pairMiss = pairMiss !== "" && pairMiss.includes("02");
const pairDup = pairingViolation([t01, t01], [t01]);
out.pairDup = pairDup !== "" && pairDup.includes("дублируются");
out.carrierOk = carrierViolation("- «цитата»") === "";
const carrierEmpty = carrierViolation("блока нет — только проза");
out.carrierEmpty = carrierEmpty !== "" && carrierEmpty.includes("пуст");
const bodyS = "BODY-SENTINEL тело тикета";
const reelS = "REEL-SENTINEL лента";
const quotesS = "QUOTES-SENTINEL цитаты";
const rA = restatorAsk(bodyS);
out.restatorBlind = rA.includes(bodyS) && !rA.includes(reelS) && !rA.includes(quotesS) && rA.includes("DRAFT-DATA");
const dA = differAsk(reelS, "рестатизация");
out.differScope = dA.includes(reelS) && dA.includes("рестатизация") && !dA.includes(bodyS) && !dA.includes(quotesS);
const hA = hostileAsk(bodyS, quotesS, reelS);
out.hostileScope = hA.includes(bodyS) && hA.includes(quotesS) && hA.includes(reelS);
console.log(JSON.stringify(out));
"""
    )
    res = run_node_slice(driver)
    assert res.returncode == 0, f"срез упал:\n{res.stderr[:600]}"
    got = json.loads(res.stdout.strip().splitlines()[-1])
    bad = [k for k, v in got.items() if v is not True]
    assert not bad, f"красные кейсы матрицы: {bad} => {json.dumps({k: got[k] for k in bad}, ensure_ascii=False)}"


def test_masking_detector_is_alive():
    """Живая проба детектора маскирования: на чистом входе молчит, на
    подсунутом заголовке ## Reel — стреляет (детектор не мёртв)."""
    driver = fn("maskingViolation") + r"""
const clean = maskingViolation("тело тикета без ленты");
const dirty = maskingViolation("тело\n## Reel\nпример");
console.log(JSON.stringify({ clean: clean === "", dirtyFires: dirty.includes("не замаскирован") }));
"""
    res = run_node_slice(driver)
    assert res.returncode == 0, f"срез упал:\n{res.stderr[:400]}"
    got = json.loads(res.stdout.strip().splitlines()[-1])
    assert got == {"clean": True, "dirtyFires": True}, got
