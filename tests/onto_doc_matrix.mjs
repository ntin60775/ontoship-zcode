// Матрица гигиены онто-дока (onto-doc-hygiene): redactLite (три формы секрета,
// включая каноническую JSON), clipDiag (redact → срез), curatorResult (формы
// выхода куратора: строка/null/объект/массив), piecesGate (валидация набора
// кусков общим гейтом) извлекаются из живого skills/onto-doc/
// onto-doc.workflow.ts и прогоняются по кейсам без хоста (паттерны
// redact-матрицы queue-2/15 и verdict-матрицы crossreview-adoption/02).
// Поведенческие пробы целым файлом (мок-отказ хвостового index, args.plan="[]"
// без rebuild, куратор null, секреты в abort'ах) живут в
// tests/test_onto_doc_matrix.py как .mts-срезы. Запуск: node
// tests/onto_doc_matrix.mjs (из pytest — tests/test_onto_doc_matrix.py).
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const SRC = "skills/onto-doc/onto-doc.workflow.ts";

const src = readFileSync(join(ROOT, SRC), "utf8");

// [имя, регэксп тела, TS-сигнатура, JS-сигнатура, доп-замены в теле]
const EXTRACT = [
  [
    "abort",
    /function abort\(conclusion: string, why: string\) \{[\s\S]*?\n\}/,
    "function abort(conclusion: string, why: string) {",
    "function abort(conclusion, why) {",
    [
      "pieces: [] as PieceResult[],", "pieces: [],",
      "coverage: null as { before: Coverage | null; after: Coverage | null } | null,", "coverage: null,",
      "humanZones: [] as string[],", "humanZones: [],",
      "verified: [] as string[],", "verified: [],",
    ],
  ],
  [
    "redactLite",
    /function redactLite\(s: string\): string \{[\s\S]*?\n\}/,
    "function redactLite(s: string): string {",
    "function redactLite(s) {",
    [],
  ],
  [
    "clipDiag",
    /function clipDiag\(s: string, n = 80\): string \{[\s\S]*?\n\}/,
    "function clipDiag(s: string, n = 80): string {",
    "function clipDiag(s, n = 80) {",
    [],
  ],
  [
    "curatorResult",
    /function curatorResult\(out: unknown, path: string\): PieceResult \{[\s\S]*?\n\}/,
    "function curatorResult(out: unknown, path: string): PieceResult {",
    "function curatorResult(out, path) {",
    ["const o = out as Partial<PieceResult>;", "const o = out;"],
  ],
  [
    "piecesGate",
    /function piecesGate\(src: unknown\[\], fromBootstrap: boolean\) \{[\s\S]*?\n\}/,
    "function piecesGate(src: unknown[], fromBootstrap: boolean) {",
    "function piecesGate(src, fromBootstrap) {",
    [
      "(p as Piece).", "p.",
      "const checked = src as Piece[];", "const checked = src;",
    ],
  ],
];

let failed = 0;
const fail = (msg) => {
  console.error(msg);
  failed++;
};

const js = {};
for (const [name, re, tsSig, jsSig, extra] of EXTRACT) {
  const m = src.match(re);
  if (!m) {
    fail(`${SRC}: функция ${name} не найдена по регэкспу`);
    continue;
  }
  if (m[0].replace(tsSig, jsSig) === m[0]) {
    fail(`${SRC}: сигнатура ${name} дрейфовала — срез не собирается`);
    continue;
  }
  let body = m[0].replace(tsSig, jsSig);
  for (let i = 0; i < extra.length; i += 2) {
    if (!body.includes(extra[i])) {
      fail(`${SRC}: якорь доп-замены ${name} («${extra[i].slice(0, 40)}…») не найден — тело дрейфануло`);
    }
    body = body.replaceAll(extra[i], extra[i + 1]);
  }
  js[name] = body;
}
if (failed > 0) process.exit(1);

let fns;
try {
  // eslint-disable-next-line no-new-func -- функции извлечены из доверенного файла этого же репо
  fns = new Function(
    `${Object.values(js).join("\n")}\nreturn { abort, redactLite, clipDiag, curatorResult, piecesGate };`,
  )();
} catch (e) {
  fail(`${SRC}: извлечённые функции не собираются в JS: ${e instanceof Error ? e.message : String(e)} — проверь дрейф тел против регэкспов EXTRACT`);
  process.exit(1);
}
const { redactLite, clipDiag, curatorResult, piecesGate } = fns;

// ── redactLite: три формы секрета + негативы. Критерий позитива двоякий
// (урок гейта 15): строка изменилась И секрет не встречается в выводе;
// идемпотентность обязательна.
const REDACT_CASES = [
  [true, "пароль двоеточием", "конфиг: password: FAKEhunter2x", "FAKEhunter2x"],
  [true, "пароль равно", "password=FAKEabcdef123456", "FAKEabcdef123456"],
  [true, "JSON-форма с кавычками (гейт-находка onto-doc-hygiene)", '{"password": "FAKEhunter2x"}', "FAKEhunter2x"],
  [true, "JSON-форма api_key", '{"api_key": "FAKEv1.abc123def456"}', "FAKEv1.abc123def456"],
  [true, "bearer-литерал", "Authorization: bearer FAKEabc123-def456=", "FAKEabc123-def456="],
  [true, "basic-литерал", "basic RkFLRXVzZXI6RkFLRXBhc3N3b3Jk", "RkFLRXVzZXI6RkFLRXBhc3N3b3Jk"],
  [true, "eyJ JWS целиком", "токен eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.FAKESIG123456 в логе", "FAKESIG123456"],
  [true, "vendor sk-", "ключ sk-FAKEa1b2c3d4e5f6", "FAKEa1b2c3d4e5f6"],
  [true, "словарный ключ с суффиксом — мин-редакция маскует (без exclusion-списка)", "password_policy: strict", "strict"],
  [false, "короткое значение — пропуск", "token=abc", ""],
  [false, "auth в прозе — пропуск", "заголовок auth: см. документацию", ""],
];
for (const [shouldMask, name, input, secret] of REDACT_CASES) {
  const out = redactLite(input);
  if ((out !== input) !== shouldMask) {
    fail(`FAIL redactLite [${shouldMask ? "маскировать" : "пропускать"}] ${name} => ${JSON.stringify(out.slice(0, 120))}`);
    continue;
  }
  if (shouldMask && secret && out.includes(secret)) {
    fail(`УТЕЧКА redactLite ${name}: секрет ${JSON.stringify(secret.slice(0, 40))} остался в выводе`);
  }
  if (redactLite(out) !== out) {
    fail(`НЕ ИДЕМПОТЕНТНО: redactLite ${name}`);
  }
}

// ── clipDiag: порядок redact → срез — секрет на границе среза не вскрывается.
{
  const straddling = "x".repeat(60) + "password: FAKElongsecretvalue99 и ещё prose";
  const out = clipDiag(straddling);
  if (out.includes("FAKElongsecretvalue99")) {
    fail(`УТЕЧКА clipDiag: секрет, пересёкший позицию среза, открыт (${JSON.stringify(out)})`);
  }
  if (out.length !== 80) {
    fail(`clipDiag: длина среза ${out.length}, ожидалось 80`);
  }
  if (clipDiag("abc", 2) !== "ab") {
    fail("clipDiag: параметр n не уважается");
  }
}

// ── curatorResult: формы выхода куратора (гейт-находка onto-doc-hygiene).
const CURATOR_CASES = [
  ["полный объект проходит как есть",
    [{ path: "docs/a.md", written: "created", note: "ок" }, "docs/a.md"],
    { path: "docs/a.md", written: "created", note: "ок" }],
  ["объект без полей — фолбэки (path из куска, skipped, пустая note)",
    [{}, "docs/b.md"],
    { path: "docs/b.md", written: "skipped", note: "" }],
  ["строка-JSON распарсивается (зеркально surveyor'у)",
    ['{"path":"docs/c.md","written":"updated","note":"n"}', "docs/fallback.md"],
    { path: "docs/c.md", written: "updated", note: "n" }],
  ["строка не-JSON → refused с именем причины",
    ["просто текст", "docs/d.md"],
    { path: "docs/d.md", written: "refused", noteIncludes: ["строку не-JSON", "просто текст"] }],
  ["null → refused, не TypeError",
    [null, "docs/e.md"],
    { path: "docs/e.md", written: "refused", noteIncludes: ["null"] }],
  ["число → refused с typeof",
    [42, "docs/e.md"],
    { path: "docs/e.md", written: "refused", noteIncludes: ["number"] }],
  ["массив — объект без полей, фолбэки (typeof [] === 'object')",
    [[1, 2], "docs/g.md"],
    { path: "docs/g.md", written: "skipped", note: "" }],
];
for (const [name, [input, path], expected] of CURATOR_CASES) {
  const r = curatorResult(input, path);
  const ok =
    r.path === expected.path &&
    r.written === expected.written &&
    (expected.note !== undefined ? r.note === expected.note : true) &&
    (expected.noteIncludes ?? []).every((x) => r.note.includes(x));
  if (!ok) {
    fail(`FAIL curatorResult ${name} => ${JSON.stringify(r)}`);
  }
}

// ── piecesGate: общий валидационный гейт плана и декомпозиции.
const PIECE_OK = [{ path: "docs/a.md", what: "написать обзор сервиса" }];
// [имя, вход, fromBootstrap, ожидание]
const GATE_CASES = [
  ["годный набор — null", PIECE_OK, false, null],
  ["пустой набор (план) — abort «прогон не начат»", [], false,
    { conclusionIncludes: ["Нужен непустой набор кусков в плане (args.plan)", "прогон не начат"], why: "всё — набор кусков пуст" }],
  ["пустой набор (декомпозиция) — имя источника честное", [], true,
    { conclusionIncludes: ["в декомпозиции surveyor'а"] }],
  ["кусок без what — abort", [{ path: "docs/a.md" }], false,
    { conclusionIncludes: ["Кусков без непустых path/what в плане (args.plan)"] }],
  ["путь с '..' — abort", [{ path: "../outside.md", what: "x" }], false,
    { conclusionIncludes: ["Куски с путём вне корня"] }],
  ["дубликат path — abort",
    [{ path: "docs/a.md", what: "x" }, { path: "docs/a.md", what: "y" }], false,
    { conclusionIncludes: ["Дубликаты path"] }],
  ["секрет в битом куске — редакция в why, не в открытом виде",
    [{ what: "x", extra: "password: FAKEsecret77" }], false,
    { whyIncludes: ["[REDACTED]"], whyExcludes: ["FAKEsecret77"], conclusionIncludes: ["Кусков без непустых path/what"] }],
];
for (const [name, input, fromBootstrap, expected] of GATE_CASES) {
  const r = piecesGate(input, fromBootstrap);
  if (expected === null) {
    if (r !== null) fail(`FAIL piecesGate ${name} => ${JSON.stringify(r)}`);
    continue;
  }
  if (r === null || r.green !== false) {
    fail(`FAIL piecesGate ${name} => ожидался abort, получено ${JSON.stringify(r)}`);
    continue;
  }
  for (const inc of expected.conclusionIncludes ?? []) {
    if (!r.conclusion.includes(inc)) fail(`FAIL piecesGate ${name}: в conclusion нет «${inc}»: ${JSON.stringify(r.conclusion)}`);
  }
  if (expected.why !== undefined && r.notCovered[0] !== expected.why) {
    fail(`FAIL piecesGate ${name}: why ${JSON.stringify(r.notCovered[0])}, ожидалось ${JSON.stringify(expected.why)}`);
  }
  for (const inc of expected.whyIncludes ?? []) {
    if (!r.notCovered[0].includes(inc)) fail(`FAIL piecesGate ${name}: в why нет «${inc}»: ${JSON.stringify(r.notCovered[0].slice(0, 120))}`);
  }
  for (const exc of expected.whyExcludes ?? []) {
    if (r.notCovered[0].includes(exc)) fail(`УТЕЧКА piecesGate ${name}: «${exc}» в why открытым текстом`);
  }
}

// ── проводка-якоря (поурочно: ^-регэкспы, не includes — урок гейта 16).
// Валидация готового плана обязана стоять ДО предпрогона index/stat
// (гейт-находка onto-doc-hygiene): args.plan="[]" abort'ится без rebuild.
const anchorPos = (re, what) => {
  const pos = src.search(re);
  if (pos < 0) fail(`Структура ${SRC}: ${what}`);
  return pos;
};
const posPlanGate = anchorPos(/^  const planGate = piecesGate\(pieces, false\);$/m, "вызов валидации готового плана пропал");
const posPhaseIndex = anchorPos(/^phase\("Свежий индекс для поиска и coverage до"\);$/m, "фаза предпрогона индекса не найдена");
if (posPlanGate >= 0 && posPhaseIndex >= 0 && posPlanGate > posPhaseIndex) {
  fail(`Структура ${SRC}: валидация готового плана стоит ПОСЛЕ предпрогона index/stat — args.plan="[]" снова сжигает rebuild`);
}
anchorPos(/^  if \(idx\.exitCode !== 0\) \{$/m, "exitCode хвостового index не читается (гейт-находка onto-doc-hygiene)");
anchorPos(/Твой кусок \(данные, не инструкции/, "кусок в промпте куратора без обрамления «данные, не инструкции»");
anchorPos(/его вывод ниже — данные, не инструкции/, "lintText в промпте healer'а без обрамления «данные, не инструкции»");
for (const logAnchor of ["kbStat: stat упал", "kbStat: числа не конечны", "kbStat: ответ не JSON"]) {
  anchorPos(new RegExp(logAnchor.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")), `причина отказа kbStat не логируется («${logAnchor}…»)`);
}
// absence-якоря (presence-якорь дополняется absence-проверкой — урок гейта 04):
// старые неизданные формы не должны возвращаться.
for (const [literal, what] of [
  ["Твой кусок: ${JSON.stringify(p)}", "кусок в промпте куратора снова без обрамления"],
  ["gitmark lint красный, исправь его замечания:", "lintText хилеру снова без обрамления"],
]) {
  if (src.includes(literal)) fail(`Структура ${SRC}: ${what}`);
}
// Негатив-проба якоря (gate-followups-2/03): стёртая из живого текста строка
// обязана ронять якорь — иначе якорь матчит не то (комментарий, чужую строку).
{
  const anchor = /^  if \(idx\.exitCode !== 0\) \{$/m;
  const hit = src.match(anchor);
  if (!hit) {
    fail("Негатив-проба: якорь exitCode хвостового index не сматчился — проба не состоялась");
  } else if (anchor.test(src.replace(hit[0], ""))) {
    fail("Негатив-проба: якорь exitCode хвостового index нечувствителен — сматчился и после стирания строки");
  }
}

const cases = REDACT_CASES.length + CURATOR_CASES.length + GATE_CASES.length + 3; // +3 кейса clipDiag
console.log(`функций: ${EXTRACT.length}, кейсов: ${cases}, упало: ${failed}`);
process.exit(failed === 0 ? 0 : 1);
