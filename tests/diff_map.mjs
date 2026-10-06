// Кейсы парсеров карты диффа (queue-2/16): numstat, untracked-статус,
// no-index numstat для новых файлов. followups/01: парсеры живут источником
// и копиями — копии обязаны быть байт-в-байт идентичны источнику (паттерн
// redact-матрицы queue-2/15: расползание копий ловит этот тест, не глаз).
// Функции извлекаются из живых файлов — регресс парсера, выдернутый вызов
// или рассинхрон копии ломают прогон. Запуск: node tests/diff_map.mjs
// (из pytest — tests/test_diff_map.py). Форматы проверены на реальном
// git 2.51 (скретч-репо, 2026-10-04): numstat "a\td\tpath"; porcelain -z —
// записи через NUL без кавычек, intent-to-add идёт ` A`, а не `??`;
// no-index numstat — третье поле "/dev/null => path", exit 1 и для
// различий, и для нечитаемого файла.
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const SOURCE = "skills/ship/reviewer.workflow.ts";
// Копии парсеров карты диффа (followups/01): новая копия = ещё один путь
// в списке; каждый парсер каждой копии сверяется с источником байт-в-байт.
const COPIES = ["skills/code-review/code-review.workflow.ts"];

// [имя, регэксп тела, TS-сигнатура, JS-сигнатура, доп-замены в теле]
const EXTRACT = [
  [
    "parseNumstat",
    /function parseNumstat\(out: string\): FileEntry\[\] \{[\s\S]*?\n\}/,
    "function parseNumstat(out: string): FileEntry[] {",
    "function parseNumstat(out) {",
    [": FileEntry[]", ""],
  ],
  [
    "parseUntrackedStatus",
    /function parseUntrackedStatus\(out: string\): string\[\] \{[\s\S]*?\n\}/,
    "function parseUntrackedStatus(out: string): string[] {",
    "function parseUntrackedStatus(out) {",
    [],
  ],
  [
    "parseNoIndexNumstat",
    /function parseNoIndexNumstat\(out: string\): \{ added: number; binary: boolean \} \| null \{[\s\S]*?\n\}/,
    "function parseNoIndexNumstat(out: string): { added: number; binary: boolean } | null {",
    "function parseNoIndexNumstat(out) {",
    [],
  ],
  [
    "contextHint",
    /function contextHint\(fileLines: number\): string \{[\s\S]*?\n\}/,
    "function contextHint(fileLines: number): string {",
    "function contextHint(fileLines) {",
    [],
  ],
  [
    "normalizeSeverity",
    /function normalizeSeverity\(x: \{ severity\?: unknown \} \| null \| undefined\): \{ severity: "high" \| "medium" \| "low"; normalized: boolean \} \{[\s\S]*?\n\}/,
    'function normalizeSeverity(x: { severity?: unknown } | null | undefined): { severity: "high" | "medium" | "low"; normalized: boolean } {',
    "function normalizeSeverity(x) {",
    [],
  ],
];

// raw — тело как в файле (для сверки идентичности копий), js — сигнатуры
// сняты (для исполнения кейсов).
function extractParts(rel) {
  const src = readFileSync(join(ROOT, rel), "utf8");
  const raw = {};
  const js = {};
  for (const [name, re, tsSig, jsSig, extra] of EXTRACT) {
    const m = src.match(re);
    if (!m) throw new Error(`${rel}: функция ${name} не найдена по регэкспу`);
    raw[name] = m[0];
    let body = m[0].replace(tsSig, jsSig);
    for (let i = 0; i < extra.length; i += 2) {
      body = body.replaceAll(extra[i], extra[i + 1]);
    }
    js[name] = body;
  }
  return { src, raw, js };
}

const source = extractParts(SOURCE);

// Идентичность копий источнику — по каждому парсеру, тело как в файле
// (паттерн redact-матрицы queue-2/15).
let failed = 0;
for (const rel of COPIES) {
  const copy = extractParts(rel);
  for (const [name, body] of Object.entries(source.raw)) {
    if (copy.raw[name] !== body) {
      console.error(`РАССИНХРОН: ${rel}: ${name} отличается от ${SOURCE}`);
      failed++;
    }
  }
  // Структурная проверка проводки в копии: живые вызовы на верхнем уровне
  // рана. Якорь начала строки, не includes по файлу (урок гейта 16:
  // подстрока, оставшаяся в комментарии, давала ложный зелёный ровно на том
  // регрессе — потере untracked из карты, — который чинит тикет).
  if (!/^const untrackedPaths = parseUntrackedStatus\(st\.stdout\);$/m.test(copy.src)) {
    console.error(`Структура ${rel}: живой вызов parseUntrackedStatus(st.stdout) пропал (остался только в комментарии?)`);
    failed++;
  }
  if (!/^const allFiles: FileEntry\[\] = parseNumstat\(ns\.stdout\);$/m.test(copy.src)) {
    console.error(`Структура ${rel}: карта диффа строится не скопированным parseNumstat`);
    failed++;
  }
}
if (failed > 0) process.exit(1);

// Структурная проверка проводки источника (queue-2/16; гейт followups/01:
// оба якоря — как у копии, иначе мутация живого вызова parseNumstat в
// источнике проходит незамеченной).
if (!/^const untrackedPaths = parseUntrackedStatus\(st\.stdout\);$/m.test(source.src)) {
  console.error("Структура: живой вызов parseUntrackedStatus(st.stdout) пропал (остался только в комментарии?)");
  process.exit(1);
}
if (!/^const allFiles: FileEntry\[\] = parseNumstat\(ns\.stdout\);$/m.test(source.src)) {
  console.error("Структура: карта диффа источника строится не парсером parseNumstat");
  process.exit(1);
}

// Гейт followups/01: если регэкспы EXTRACT всё ещё матчатся, но собирают
// битый JS (дрейф тела, обрыв по вложенному \n}), падать нужно с именем
// источника и причиной, а не сырым SyntaxError.
// Гигиена контекста (followups/02): проводка contextHint в аске и wc-замер —
// в источнике и копии, построчными якорями (урок гейта 16). Негативный якорь:
// безусловного приглашения «Нужен контекст — читай файл целиком» в аске быть
// не должно — переполнение порождается самим аском, а ветки пишет только
// contextHint.
const HINT_WIRING = {
  "skills/ship/reviewer.workflow.ts":
    /^\s*: `Его дифф: git -C \$\{q\(root\)\} diff \$\{q\(base\)\} -- \$\{q\(f\.path\)\}\. \$\{contextHint\(fileLines\.get\(f\.path\) \?\? -1\)\}`;$/m,
  "skills/code-review/code-review.workflow.ts":
    /^\s*: `Его дифф: git -C \$\{shq\(root\)\} diff \$\{shq\(base\)\} -- \$\{shq\(f\.path\)\}\. \$\{contextHint\(fileLines\.get\(f\.path\) \?\? -1\)\}`;$/m,
};
const WC_WIRING =
  /^        const w = await world\.run\("wc", \["-l", `\$\{root\}\/\$\{p\}`\]\);$/m;
const HINT_FILES = [[SOURCE, source.src], ...COPIES.map((rel) => [rel, extractParts(rel).src])];
for (const [rel, src] of HINT_FILES) {
  if (!HINT_WIRING[rel].test(src)) {
    console.error(`Структура ${rel}: аск диффа не подсказывает contextHint(fileLines.get(f.path) ?? -1) — гигиена контекста (followups/02) отвалилась`);
    failed++;
  }
  if (!WC_WIRING.test(src)) {
    console.error(`Структура ${rel}: замер wc -l пропал — contextHint работает вслепую`);
    failed++;
  }
  if (src.includes("Нужен контекст — читай файл целиком")) {
    console.error(`Структура ${rel}: в аске снова безусловное «Нужен контекст — читай файл целиком» — регресс followups/02`);
    failed++;
  }
}

// Intent диффа в осях (crossreview-adoption/01): проводка только в копии
// code-review — у источника-гейта вместо intent тикет, его проводку этот тест
// не смотрит. Якоря построчные (урок гейта 16: includes по файлу не отличает
// живой вызов от комментария). Замысел обязан доехать до каждой оси-задачи
// (декларация args → парсинг → сигнатура → вызов → промпт), а пустой intent —
// получить честную пометку самосогласованности в conclusion.
const CR_REL = "skills/code-review/code-review.workflow.ts";
const crSrc = extractParts(CR_REL).src;
const INTENT_LINES = [
  [/^  intent:\n    type: string$/m, "декларация args.intent в шапке zcode-workflow"],
  [/^const intent = String\(args\.intent \?\? ""\)\.trim\(\);$/m, "парсинг args.intent"],
  [/^function filePrompt\(axis: string, lens: string, f: FileEntry, intent: string\): string \{$/m, "сигнатура filePrompt с intent"],
  [/^ +filePrompt\(t\.axis, t\.lens, t\.file, intent\),$/m, "аск оси-задачи получает intent"],
  [/^ +`Корень чекаута: \$\{root\}\. Твой файл: \$\{f\.path\}\. \$\{diffHint\} \$\{intentBlock\}` \+$/m, "промпт оси несёт intentBlock"],
  [/^ +: \["Ревью без замысла: intent не передан — проверена самосогласованность диффа, соответствие замыслу не оценивалось\."\]\),$/m, "честная пометка самосогласованности в conclusion"],
];
for (const [re, what] of INTENT_LINES) {
  if (!re.test(crSrc)) {
    console.error(`Структура ${CR_REL}: intent-проводка отвалилась — ${what} (crossreview-adoption/01)`);
    failed++;
  }
}

// Счётчик нормализаций severity (gate-followups-2/03): функция — в EXTRACT и
// копиях (сверка выше), проводка — построчными якорями здесь: инкремент в
// коалесации, reduce/пункт conclusion в источнике; let/log/conclusion в
// копии. При нуле пунктов и лога нет — вывод не мусорит (тернарники в якорях).
const SEV_WIRING = {
  [SOURCE]: [
    [/^\s*const s = normalizeSeverity\(x\);$/m, "коалесация идёт через normalizeSeverity"],
    [/^\s*if \(s\.normalized\) normalized \+= 1;$/m, "инкремент счётчика нормализаций"],
    [/^const totalNormalized = results\.reduce\(\(n, x\) => n \+ x\.normalized, 0\);$/m, "сумма по всем находкам прогона"],
    [/^  \.\.\.\(totalNormalized > 0 \? \[`severity вне high\/low нормализовано в medium: \$\{totalNormalized\}`\] : \[\]\),$/m, "conclusion называет число при N>0 и молчит при N=0"],
  ],
  [CR_REL]: [
    [/^let normalizedSeverity = 0;$/m, "счётчик нормализаций рядом с droppedEmpty"],
    [/^\s*const s = normalizeSeverity\(x\);$/m, "коалесация идёт через normalizeSeverity"],
    [/^\s*if \(s\.normalized\) normalizedSeverity \+= 1;$/m, "инкремент счётчика нормализаций"],
    [/^\s*log\(`Severity вне high\/low нормализовано в medium: \$\{normalizedSeverity\}`\);$/m, "лог при N>0"],
    [/^  \.\.\.\(normalizedSeverity > 0$/m, "conclusion называет число при N>0"],
    [/^    \? \[`severity вне high\/low нормализовано в medium: \$\{normalizedSeverity\}`\]$/m, "формулировка нормализации в conclusion"],
  ],
};
for (const [rel, src] of [[SOURCE, source.src], [CR_REL, crSrc]]) {
  for (const [re, what] of SEV_WIRING[rel]) {
    if (!re.test(src)) {
      console.error(`Структура ${rel}: счётчик нормализаций severity отвалился — ${what} (gate-followups-2/03)`);
      failed++;
    }
  }
}

// Негатив-проба якоря (gate-followups-2/03): стёртый из живого текста
// инкремент обязан ронять якорь — иначе якорь матчит не то (комментарий,
// чужую строку) и зелёный при исчезнувшем счётчике ложный.
for (const [rel, src, anchor] of [
  [SOURCE, source.src, /^\s*if \(s\.normalized\) normalized \+= 1;$/m],
  [CR_REL, crSrc, /^\s*if \(s\.normalized\) normalizedSeverity \+= 1;$/m],
]) {
  const hit = src.match(anchor);
  if (!hit) {
    console.error(`Негатив-проба ${rel}: якорь инкремента не сматчился — проба не состоялась`);
    failed++;
    continue;
  }
  if (anchor.test(src.replace(hit[0], ""))) {
    console.error(`Негатив-проба ${rel}: якорь инкремента нечувствителен — сматчился и после стирания строки (проверь границы ^…$)`);
    failed++;
  }
}
if (failed > 0) process.exit(1);

let gateFns;
try {
  // eslint-disable-next-line no-new-func -- функции извлечены из доверенного файла этого же репо
  gateFns = new Function(
    `${Object.values(source.js).join("\n")}\nreturn { parseNumstat, parseUntrackedStatus, parseNoIndexNumstat, contextHint, normalizeSeverity };`,
  )();
} catch (e) {
  console.error(`Извлечённые парсеры не собираются в JS (${SOURCE}): ${e instanceof Error ? e.message : String(e)} — проверь дрейф тел функций против регэкспов EXTRACT`);
  process.exit(1);
}
const { parseNumstat, parseUntrackedStatus, parseNoIndexNumstat, contextHint, normalizeSeverity } = gateFns;

// [имя, fn, вход, ожидаемое значение (deep-equal)]
const CASES = [
  ["numstat: два текстовых файла", parseNumstat, "2\t1\ttracked.txt\n1\t0\tita.txt\n", [
    { path: "tracked.txt", diffLines: 3, untracked: false },
    { path: "ita.txt", diffLines: 1, untracked: false },
  ]],
  ["numstat: бинарная строка пропускается", parseNumstat, "-\t-\tpic.png\n3\t2\ta.py\n", [
    { path: "a.py", diffLines: 5, untracked: false },
  ]],
  ["numstat: пустой вывод", parseNumstat, "", []],
  ["numstat: путь с пробелом", parseNumstat, "2\t0\twith space.txt\n", [
    { path: "with space.txt", diffLines: 2, untracked: false },
  ]],
  ["numstat: мусорные строки игнорируются", parseNumstat, "random noise\n\n4\t0\tb.py\n", [
    { path: "b.py", diffLines: 4, untracked: false },
  ]],
  ["numstat: rename берёт новый путь", parseNumstat, "0\t0\told.py => new.py\n1\t2\tbig => bigger\n", [
    { path: "new.py", diffLines: 0, untracked: false },
    { path: "bigger", diffLines: 3, untracked: false },
  ]],
  ["numstat: не-ASCII путь сырым UTF-8 (контракт quotepath=false)", parseNumstat, "2\t0\tтест-файл.txt\n", [
    { path: "тест-файл.txt", diffLines: 2, untracked: false },
  ]],
  ["status -z: полный живой образец", parseUntrackedStatus, " A ita.txt\0 M tracked.txt\0?? bin.dat\0?? untracked.txt\0", [
    "bin.dat",
    "untracked.txt",
  ]],
  ["status -z: intent-to-add ( A) не попадает в untracked", parseUntrackedStatus, " A ita.txt\0", []],
  ["status -z: пустой статус", parseUntrackedStatus, "", []],
  ["status -z: только изменённые, без новых", parseUntrackedStatus, " M a.py\0M  b.py\0", []],
  ["status -z: имя с пробелом без кавычек", parseUntrackedStatus, "?? with space.txt\0", ["with space.txt"]],
  ["status -z: запись ?? без пути отбрасывается", parseUntrackedStatus, "??\0?? x.py\0", ["x.py"]],
  ["no-index: новый файл две строки", parseNoIndexNumstat, "2\t0\t/dev/null => untracked.txt\n", { added: 2, binary: false }],
  ["no-index: бинарный новый файл", parseNoIndexNumstat, "-\t-\t/dev/null => bin.dat\n", { added: 0, binary: true }],
  ["no-index: пустой файл", parseNoIndexNumstat, "0\t0\t/dev/null => empty.txt\n", { added: 0, binary: false }],
  ["no-index: пустой вывод — не распарсилось", parseNoIndexNumstat, "", null],
  ["no-index: ошибка git — не распарсилось", parseNoIndexNumstat, "error: Could not access 'nope.txt'\n", null],
  ["no-index: числа без третьего поля — не распарсилось", parseNoIndexNumstat, "2\t0\n", null],
  ["no-index: берёт первую непустую строку", parseNoIndexNumstat, "\n1\t0\t/dev/null => x.py\n", { added: 1, binary: false }],
  ["contextHint: малый файл — читай целиком", contextHint, 100, "Файл небольшой: для контекста читай его целиком в корне чекаута."],
  ["contextHint: пустой файл — читай целиком", contextHint, 0, "Файл небольшой: для контекста читай его целиком в корне чекаута."],
  ["contextHint: ровно порог — читай целиком", contextHint, 300, "Файл небольшой: для контекста читай его целиком в корне чекаута."],
  ["contextHint: за порогом — адресные чтения", contextHint, 301, "Файл тяжёлый (порог гигиены 300 строк; в файле 301): файл целиком не читай — переполнит контекст, и запрос упадёт у провайдера. Материал — дифф и адресные чтения: диапазоны вокруг изменённых строк из @@-заголовков диффа (read с offset/limit или sed -n 'A,Bp'), при необходимости короткий верх файла для ориентира."],
  ["contextHint: сильно тяжёлый — адресные чтения", contextHint, 5000, "Файл тяжёлый (порог гигиены 300 строк; в файле 5000): файл целиком не читай — переполнит контекст, и запрос упадёт у провайдера. Материал — дифф и адресные чтения: диапазоны вокруг изменённых строк из @@-заголовков диффа (read с offset/limit или sed -n 'A,Bp'), при необходимости короткий верх файла для ориентира."],
  ["contextHint: не измерился — тяжёлый (фейл-сейф в гигиену)", contextHint, -1, "Файл тяжёлый (порог гигиены 300 строк; размер не измерился): файл целиком не читай — переполнит контекст, и запрос упадёт у провайдера. Материал — дифф и адресные чтения: диапазоны вокруг изменённых строк из @@-заголовков диффа (read с offset/limit или sed -n 'A,Bp'), при необходимости короткий верх файла для ориентира."],
  // normalizeSeverity (gate-followups-2/03): известные уровни насквозь и без
  // пометки; всё прочее, включая отсутствующее, — medium с пометкой. Кейс
  // «critical → normalized: true» — негатив-проба уровня функции: если
  // функция перестала сообщать факт подмены, матрица падает здесь.
  ["severity: high проходит насквозь", normalizeSeverity, { severity: "high" }, { severity: "high", normalized: false }],
  ["severity: low проходит насквозь", normalizeSeverity, { severity: "low" }, { severity: "low", normalized: false }],
  ["severity: честный medium без пометки (счётчик не мусорит)", normalizeSeverity, { severity: "medium" }, { severity: "medium", normalized: false }],
  ["severity: junk-строка подменяется с пометкой", normalizeSeverity, { severity: "critical" }, { severity: "medium", normalized: true }],
  ["severity: регистр не high/low/medium — подмена", normalizeSeverity, { severity: "HIGH" }, { severity: "medium", normalized: true }],
  ["severity: нет поля — подмена", normalizeSeverity, {}, { severity: "medium", normalized: true }],
  ["severity: объект отсутствует — подмена", normalizeSeverity, null, { severity: "medium", normalized: true }],
  ["severity: undefined — подмена", normalizeSeverity, undefined, { severity: "medium", normalized: true }],
];

for (const [name, fn, input, expected] of CASES) {
  const out = fn(input);
  if (JSON.stringify(out) !== JSON.stringify(expected)) {
    console.error(`FAIL ${name} => ${JSON.stringify(out)} (ожидалось ${JSON.stringify(expected)})`);
    failed++;
  }
}
console.log(`парсеров: ${EXTRACT.length}, копий: ${COPIES.length}, кейсов: ${CASES.length}, упало: ${failed}`);
process.exit(failed === 0 ? 0 : 1);
