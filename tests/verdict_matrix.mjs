// Матрица вердикта конфирмера (crossreview-adoption/02): трёхстороннее
// отображение «ответ конфирмера + отказы вызовов → verified/unconfirmed/
// unverified» извлекается из живого confirm.workflow.ts и прогоняется по
// кейсам без хоста (аналог redact-матрицы queue-2/15). Заодно проверяет,
// что фаза подтверждения вызывает verdict() — функция не остаётся сиротой,
// а отказ не формулируется как опровержение. Запуск: node
// tests/verdict_matrix.mjs (из pytest — tests/test_verdict_matrix.py).
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const SRC = "skills/ship/confirm.workflow.ts";

const src = readFileSync(join(ROOT, SRC), "utf8");
if (!src.includes("verdict(e1, e2, c)")) {
  console.error(`${SRC}: фаза подтверждения не вызывает verdict() — матрица тестирует сироту`);
  process.exit(1);
}
const m = src.match(
  /function verdict\(e1: string, e2: string, c: Confirmation \| null\): Confirmation \{[\s\S]*?\n\}/,
);
if (!m) {
  console.error(`${SRC}: function verdict не найдена`);
  process.exit(1);
}
const body = m[0].replace(
  "function verdict(e1: string, e2: string, c: Confirmation | null): Confirmation {",
  "function verdict(e1, e2, c) {",
);

// eslint-disable-next-line no-new-func -- функция извлечена из доверенного файла этого же репо
const verdict = new Function(`${body}\nreturn verdict;`)();

let failed = 0;
const check = (name, cond, detail) => {
  if (!cond) {
    console.error(`FAIL ${name}${detail ? `: ${detail}` : ""}`);
    failed++;
  }
};

// [имя, e1, e2, ответ конфирмера, ожидания {status, holds?, note?, noteIncludes?, noteExcludes?}]
const CASES = [
  ["двойной отказ → unverified, обе причины в note", "boom A", "boom B", null,
    { status: "unverified", holds: false, noteIncludes: ["проверка не состоялась", "boom A", "boom B"] }],
  ["отказ сформулирован как отказ, не как опровержение", "x", "y", null,
    { status: "unverified", noteExcludes: ["не подтверждено", "не воспроизведено"] }],
  ["первый отказ + удачный ретрай (holds=true) → verified, первая ошибка не протекает", "net down", "",
    { holds: true, note: "воспроизвёл по строке 42" },
    { status: "verified", holds: true, note: "воспроизвёл по строке 42", noteExcludes: ["net down"] }],
  ["первый отказ + удачный ретрай (holds=false) → unconfirmed, отказ не влияет", "net down", "",
    { holds: false, note: "не воспроизводится" },
    { status: "unconfirmed", holds: false }],
  ["без отказов holds=false → unconfirmed, note проходит как есть", "", "",
    { holds: false, note: "не воспроизводится" },
    { status: "unconfirmed", note: "не воспроизводится" }],
  ["без отказов holds=true → verified", "", "",
    { holds: true, note: "ок" },
    { status: "verified", note: "ок" }],
  ["мусор вместо ответа ({}), отказов нет → unconfirmed с пустой note", "", "", {},
    { status: "unconfirmed", holds: false, note: "" }],
  ["ответ null без отказов (защитный) → unconfirmed", "", "", null,
    { status: "unconfirmed", holds: false, note: "" }],
  ["e2 без e1 — защитный контракт самой функции (из живого потока недостижимо: e2 ⇒ e1): ответ не читается, note без пунктуационного артефакта", "", "упало",
    { holds: true, note: "заглушка" },
    { status: "unverified", holds: false, noteIncludes: ["после ретрая: упало"], noteExcludes: [": ;", "первый отказ", "заглушка"] }],
];

for (const [name, e1, e2, answer, exp] of CASES) {
  const v = verdict(e1, e2, answer);
  check(name, v.status === exp.status, `status=${v.status}, ожидалось ${exp.status}`);
  if (exp.holds !== undefined) check(name, v.holds === exp.holds, `holds=${v.holds}`);
  if (exp.note !== undefined) check(name, v.note === exp.note, `note=${JSON.stringify(v.note)}`);
  for (const inc of exp.noteIncludes ?? []) check(name, v.note.includes(inc), `в note нет «${inc}»: ${JSON.stringify(v.note.slice(0, 120))}`);
  for (const exc of exp.noteExcludes ?? []) check(name, !v.note.includes(exc), `в note лишнее «${exc}»: ${JSON.stringify(v.note.slice(0, 120))}`);
}
console.log(`кейсов: ${CASES.length}, упало: ${failed}`);
process.exit(failed === 0 ? 0 : 1);
