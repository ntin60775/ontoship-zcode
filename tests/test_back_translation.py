"""Contract of the counter-layer run (behavior-reel/03). The workflow takes the
masked drafts, the reels and the quote carrier as THREE SEPARATE string args —
the masking is visible in the run's args; the restator's ask is assembled from
the ticket body ONLY (structural blindness: the builder does not even accept
the reel or the quotes), the quote comparison is mechanical character-level
equality in code (with all roles on one model family it is the only machine
prefilter of operator→ticket substitution — the honest frame the SKILL fixes).
Named refusals instead of throws for assembly violations (unmasked input, marker
format, NN pairing, empty/unparsable carrier, preamble, NN format, fence
sentinels in the material); zero findings are NAMED «не найдено» via the
extracted classSummary() — the semantics is behavioral, not a grepped literal;
«compared goals» rides next to the verdict so a vacuum zero is not mistakable
for a clean one. The restator/differ/hostile answers are shape-checked: an
answer without its array and an answer with a failure are named skips, never an
honest empty; garbage elements (no claim/evidence, no caseText/why) are dropped
with a counter. The goal-line predicate is a bullet: template prose and
rejected-case lines («- Отклонено …») never parse as goals — an honest ticket
following the documented format is not accused. The behavioral half runs the
real functions extracted from the live file under node's type stripping; the
distorted-quote case is the load-bearing mutation direction (a comparator that
«forgives» wording drift goes red there), and the detector probes
(maskingViolation firing on injected headers in any case/spacing, fence
markers, preamble, NN format) keep the detectors alive. The fail-closed wiring
is pinned for ORDER (every guard before the first ask) and for the refusal
bodies' notCovered literals, so a guard moved below the asks or an emptied
body goes red."""
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


def node_version_tuple(s: str) -> tuple[int, int, int]:
    """Версия node в кортеж: суффиксы nightly/v8 канюлятся к цифрам —
    «23.0.0-nightly2026» → (23, 0, 0) (verified находка confirm-рана: int()
    падал на суффиксе ValueError'ом)."""
    m = re.search(r"(\d+)\.(\d+)\.(\d+)", s.strip())
    if not m:
        raise ValueError(f"версия node не парсится: {s!r}")
    return tuple(int(x) for x in m.groups())


def run_node_slice(driver: str, suffix: str = ".mts") -> subprocess.CompletedProcess:
    """Прогон среза воркфлоу под node: файл во временнике, rc/stdout наружу.
    Для .mts-срезов (TS-аннотации не зачищаются + top-level await): node ≥ 23
    снимает типы сам, 22.6–22.x идёт через --experimental-strip-types; ниже
    22.6 нет ни того, ни другого — именованный skip (минимум из
    docs/ops/install.md, идиома test_reviewer_substrate). Отсутствующий node —
    тоже именованный skip, не исключение."""
    cmd = ["node"]
    if suffix == ".mts":
        try:
            v = subprocess.run(["node", "-p", "process.versions.node"],
                               capture_output=True, text=True, timeout=60)
        except FileNotFoundError:
            pytest.skip("node отсутствует в PATH — .mts-срезы непрогоняемы; минимум в docs/ops/install.md")
        if v.returncode != 0:
            pytest.skip(f"node не отвечает версией (exit {v.returncode}) — срезы непрогоняемы")
        try:
            version = node_version_tuple(v.stdout)
        except ValueError as e:
            pytest.skip(str(e))
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
    """Тело функции живого файла по её сигнатурной строке. Баланс фигурных
    скобок проверяется: прижатый влево «}» внутри тела (flush-left JSON-пример
    в аске) обрезал бы срез по первому «^}$» с вводящей диагностикой —
    баланс ловит обрезку на месте (verified находка confirm-рана)."""
    window = structural_window(_text(), f"function {name}(", r"^}$")
    assert window.count("{") == window.count("}"), (
        f"срез функции {name} разбалансирован по скобкам — окно обрезано по «}}» внутри тела")
    return window


def test_node_version_tuple_parses_suffixes():
    assert node_version_tuple("23.0.0-nightly20261015abc") == (23, 0, 0)
    assert node_version_tuple("22.6.0") == (22, 6, 0)
    assert node_version_tuple("v24.19.0\n") == (24, 19, 0)
    with pytest.raises(ValueError):
        node_version_tuple("not-a-version")


def test_args_header_is_three_separate_inputs():
    """Маскирование видно в args рана: шапка — ровно plan/tickets/reels/quotes,
    все обязательные; лишний вход (например, слитный «всё в одном» аргумент)
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
    """Ноль назван «не найдено»: семантика — поведенческая, в извлечённой
    classSummary (0 → «не найдено.», N>0 → число), инверсия условия роняет
    матрицу; проводка — якорями вызовов в conclusion для обоих классов; якорь
    литерала единственен и чувствителен к стиранию одной копии."""
    text = _text()
    for prefix in ("Сверка Целей с эталоном", "Рестатизация vs лента"):
        anchor = re.compile(rf'classSummary\("{re.escape(prefix)}", \w+\.length, ', re.M)
        assert anchor.search(text), f"проводка classSummary для «{prefix}» отвалилась"
    hits = re.findall(r"не найдено\.", text)
    assert hits, "литерал «не найдено.» пропал из файла"
    stripped, n = re.subn(r"не найдено\.", "", text, count=1)
    assert n == 1 and "не найдено." not in stripped, "стирание одной копии «не найдено.» должно убивать литерал"


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
    """Отказы сборки: каждый guard (маскирование, формат маркеров, парность,
    носитель, преамбула, формат номеров, фенсы) — до ПЕРВОГО аска; тела
    отказов закреплены якорями notCovered-литералов (перенос guard'а за аски,
    опустошение или удаление тела роняют пин)."""
    text = _text()
    first_ask = text.index("await agent(")
    guard_anchors = [
        r"^const maskV = maskingViolation\(ticketsArg\);$",
        r"^if \(maskV !== \"\"\) \{$",
        r"^const pairV = pairingViolation\(ticketBlocks, reelBlocks\);$",
        r"^const carrierV = carrierViolation\(quotesArg\);$",
        r"^const preT = preambleViolation\(ticketsArg\);$",
        r"^const idV = idFormatViolation\(ticketBlocks\);$",
        r"^const fenceT = fenceViolation\(ticketsArg, \"DRAFT-DATA\"\);$",
    ]
    for anchor in guard_anchors:
        m = re.search(anchor, text, re.M)
        assert m, f"fail-closed проводка отвалилась: {anchor}"
        assert text.index(m.group(0)) < first_ask, f"guard за асками: {anchor}"
    for literal in (
        "всё — вход не замаскирован",
        "всё — формат маркеров",
        "всё — наборы тикетов расходятся",
        "всё — носитель цитат пуст либо не парсится",
        "всё — преамбула входа",
        "всё — формат номеров тикетов",
        "всё — маркер фенса в материале",
    ):
        assert re.search(rf"notCovered: \[\"{re.escape(literal)}\"\]", text), f"тело отказа потеряло литерал: {literal}"
    # отказ «формат маркеров» — живой return, не только присутствие условия
    m = re.search(r"^if \(ticketBlocks\.length === 0\) \{$", text, re.M)
    assert m, "guard формата маркеров потерян"


def test_answer_shape_checks_wired():
    """Форма ответа диффа/хостайла проверяется: отказ и ответ без массива —
    именованные пропуски (не честное пустое); мусорные элементы отбрасываются
    со счётчиком; рестатизация проверяется на маркер фенса перед диффом."""
    text = _text()
    for anchor in (
        r"fenceViolation\(out\.restatement, \"RESTATE-DATA\"\)",
        r"arrD === null",
        r"arrH === null",
        r"форма ответа не распознана",
        r"out\.garbageDropped \+=",
    ):
        assert re.search(anchor, text), f"проверка формы ответа отвалилась: {anchor}"


def test_behavioral_matrix():
    """Матрица живых функций под node: разбор маркеров, разбор целей (строка-
    цель — буллет; проза шаблона и отклонённые случаи не разбираются), носитель
    (жадный захват заменён именованием мусора), посимвольная сверка (искажённая
    цитата — мутационное направление; чистый вход — пусто строго; evidence
    режется), именованные отказы сборки, classSummary, сентовые пробы слепоты
    асков."""
    driver = (
        "\n".join((
            fn("parseTicketBlocks"),
            fn("parseGoals"),
            fn("parseCarrier"),
            fn("maskingViolation"),
            fn("preambleViolation"),
            fn("idFormatViolation"),
            fn("fenceViolation"),
            fn("pairingViolation"),
            fn("carrierViolation"),
            fn("classSummary"),
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
  "проза шаблона: carries the visible marker `Цель (парафраз): …` и `Цель` is quoted verbatim\n" +
  "- Отклонено оператором (контрслой): Цель: … → Вход: … → Наблюдаемый выход: …\n");
out.goalsVerbatim = goals.verbatim.length === 1 && goals.verbatim[0].quote === "дубликаты обязаны ловиться и при полном совпадении строк" && goals.verbatim[0].line === 1;
out.goalsParaphrase = goals.paraphrase === 1;
out.goalsUnmarked = goals.unmarked.length === 1 && goals.unmarked[0].line === 3;
out.proseNotGoal = goals.verbatim.length + goals.paraphrase + goals.unmarked.length === 3;
const carrier = parseCarrier("### Цитаты оператора (дословно)\n\n- «дубликаты обязаны ловиться и при полном совпадении строк»\n- «порог сходности крутится ключом, дефолт не трогаем»\n- парафраз: выгрузка без танцев с кодировкой\n- «а», «б»\n");
out.carrierQuotes = carrier.carrier.length === 2 && carrier.carrier[1] === "порог сходности крутится ключом, дефолт не трогаем";
out.carrierParaphrases = carrier.paraphrases.length === 1;
out.carrierMalformed = carrier.malformed.length === 1 && carrier.malformed[0].includes("«а», «б»");
const verbatimOnly = parseGoals("- Цель (дословно: «дубликаты обязаны ловиться и при полном совпадении строк») → Вход: … → Наблюдаемый выход: …\n");
out.compareCleanStrict = compareGoals("01", verbatimOnly, carrier.carrier).length === 0;
const distorted = parseGoals("- Цель (дословно: «дубликаты должны ловиться и при полном совпадении строк») → Вход: … → Наблюдаемый выход: …\n");
const dOut = compareGoals("01", distorted, carrier.carrier);
out.compareDistorted = dOut.length === 1 && dOut[0].klass === "quote-mismatch" && dOut[0].evidence.includes("должны");
out.compareUnmarked = compareGoals("02", goals, carrier.carrier).some((d) => d.klass === "quote-mismatch" && d.claim.includes("без маркера"));
const longQ = "А".repeat(500);
const longGoals = parseGoals(`- Цель (дословно: «${longQ}») → Вход: … → Наблюдаемый выход: …\n`);
const longOut = compareGoals("01", longGoals, carrier.carrier);
out.evidenceSliced = longOut.length === 1 && longOut[0].evidence.length < 300;
out.maskClean = maskingViolation("тело без ленты") === "";
const maskDirty = maskingViolation("тело\n## Reel\n- Цель …\n");
const maskGlued = maskingViolation("тело\n##Reel x");
const maskLower = maskingViolation("тело\n## reel x");
const maskUpper = maskingViolation("тело\n## REEL x");
out.maskDirty = [maskDirty, maskGlued, maskLower, maskUpper].every((s) => s !== "" && s.includes("не замаскирован"));
out.preambleClean = preambleViolation("=== ТИКЕТ 01: A ===\nтело") === "";
const pre = preambleViolation("мусор до маркера\n=== ТИКЕТ 01: A ===\nтело");
out.preambleDirty = pre !== "" && pre.includes("до первого маркера") && pre.includes("мусор");
const t01 = { id: "01", title: "a", body: "b" };
const t02 = { id: "02", title: "c", body: "d" };
const tBad = { id: "../x\"'", title: "e", body: "f" };
out.idOk = idFormatViolation([t01, t02]) === "";
const idBad = idFormatViolation([t01, tBad]);
out.idBad = idBad !== "" && idBad.includes("../x\"'");
out.fenceClean = fenceViolation("чистый материал", "DRAFT-DATA") === "";
const fClose = fenceViolation("тело с DRAFT-DATA>>> внутри", "DRAFT-DATA");
const fOpen = fenceViolation("тело с <<<DRAFT-DATA внутри", "DRAFT-DATA");
out.fenceDirty = fClose !== "" && fOpen !== "" && fClose.includes("рамка");
out.pairOk = pairingViolation([t01, t02], [t02, t01]) === "";
const pairMiss = pairingViolation([t01, t02], [t01]);
out.pairMiss = pairMiss !== "" && pairMiss.includes("02");
const pairDup = pairingViolation([t01, t01], [t01]);
out.pairDup = pairDup !== "" && pairDup.includes("дублируются");
out.carrierOk = carrierViolation("- «цитата»") === "";
const carrierEmpty = carrierViolation("блока нет — только проза");
out.carrierEmpty = carrierEmpty !== "" && carrierEmpty.includes("пуст");
const carrierMalformed = carrierViolation("- «цитата»\n- «а», «б»\n");
out.carrierMalformedRefusal = carrierMalformed !== "" && carrierMalformed.includes("не распарсены");
out.classZero = classSummary("Сверка Целей с эталоном", 0, "расхождений") === "Сверка Целей с эталоном: не найдено.";
out.classCount = classSummary("Рестатизация vs лента", 3, "расхождений") === "Рестатизация vs лента: 3 расхождений.";
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
    подсунутом заголовке Reel — стреляет в любом регистре и без пробела
    (детектор не мёртв)."""
    driver = fn("maskingViolation") + r"""
const clean = maskingViolation("тело тикета без ленты");
const dirty = maskingViolation("тело\n## Reel\nпример");
const glued = maskingViolation("тело\n##REEL");
const lower = maskingViolation("тело\n## reel");
console.log(JSON.stringify({ clean: clean === "", dirtyFires: dirty.includes("не замаскирован"), gluedFires: glued !== "", lowerFires: lower !== "" }));
"""
    res = run_node_slice(driver)
    assert res.returncode == 0, f"срез упал:\n{res.stderr[:400]}"
    got = json.loads(res.stdout.strip().splitlines()[-1])
    assert got == {"clean": True, "dirtyFires": True, "gluedFires": True, "lowerFires": True}, got
