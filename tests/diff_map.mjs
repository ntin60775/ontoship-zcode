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
let gateFns;
try {
  // eslint-disable-next-line no-new-func -- функции извлечены из доверенного файла этого же репо
  gateFns = new Function(
    `${Object.values(source.js).join("\n")}\nreturn { parseNumstat, parseUntrackedStatus, parseNoIndexNumstat };`,
  )();
} catch (e) {
  console.error(`Извлечённые парсеры не собираются в JS (${SOURCE}): ${e instanceof Error ? e.message : String(e)} — проверь дрейф тел функций против регэкспов EXTRACT`);
  process.exit(1);
}
const { parseNumstat, parseUntrackedStatus, parseNoIndexNumstat } = gateFns;

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
