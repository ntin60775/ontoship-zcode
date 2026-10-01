/* zcode-workflow
description: Онтодок-прогон — план правок KB расходится fan-out по кураторам, собранное проходит gitmark lint как гейт, провалившееся долечивается до зелёного.
args:
  task:
    type: string
    description: "Док-задача: что документируем и зачем."
    required: true
  plan:
    type: json
    description: "План правок: массив кусков [{path, what}] — по одному куратору на кусок."
    required: true
  root:
    type: string
    description: "Корень KB-проекта (worktree): кураторы правят файлы только внутри него."
    required: true
*/

// onto-doc workflow (/ship queue-2/05): doc-task → fan-out curators → lint gate
// → healing loop. The gate is deterministic (world.run gitmark lint); curators
// write, they do not gate. Everything happens inside `root` — callers pass a
// worktree so the main checkout stays untouched.

interface Piece {
  /** Путь к файлу куска, от корня KB. */
  path: string;
  /** Что именно написать/обновить в этом куске. */
  what: string;
}

interface PieceResult {
  /** Путь к файлу куска. */
  path: string;
  /** Создан новый файл, обновлён существующий или правок не было. */
  written: "created" | "updated" | "skipped";
  /** Одно предложение: что сделано, и любые отклонения от куска плана. */
  note: string;
}

const task = String(args.task ?? "");
const root = String(args.root ?? ".").replace(/\/+$/, "");
function abort(conclusion: string, why: string) {
  return {
    conclusion,
    green: false,
    rounds: 0,
    pieces: [] as PieceResult[],
    verified: [] as string[],
    notCovered: [why],
  };
}
let parsed: unknown = args.plan;
if (typeof parsed === "string") {
  try {
    parsed = JSON.parse(parsed);
  } catch {
    return abort("План правок (args.plan) не распарсился как JSON-массив — прогон не начат.", "всё — план не распарсился");
  }
}
const pieces: Piece[] = Array.isArray(parsed) ? (parsed as Piece[]) : [];
const malformed = pieces.filter(
  (p) =>
    typeof p !== "object" ||
    p === null ||
    typeof p.path !== "string" ||
    !p.path.trim() ||
    typeof p.what !== "string" ||
    !p.what.trim(),
);
if (malformed.length > 0) {
  return abort(
    `Кусков без непустых path/what: ${malformed.length} — кураторов не запускал, почини план.`,
    `куски плана без path/what: ${JSON.stringify(malformed)}`,
  );
}
const paths = pieces.map((p) => p.path);
const dupes = [...new Set(paths.filter((x, i) => paths.indexOf(x) !== i))];
if (dupes.length > 0) {
  return abort(
    `Дубликаты path в плане (${[...new Set(dupes)].join(", ")}): кураторы писали бы в один файл параллельно — прогон не начат.`,
    `дубликаты path: ${dupes.join(", ")}`,
  );
}
if (!task.trim() || pieces.length === 0) {
  return abort("Нужны непустые args.task и args.plan (массив кусков) — прогон не начат.", "всё — задача или план не переданы");
}

const curatorRules =
  "Ты куратор KB онтошипа. Правишь ТОЛЬКО файлы своего куска внутри корня; " +
  "за его пределами — ничего, коммитить нельзя. Перед правкой прочитай " +
  `${root}/skills/kb-curate/SKILL.md и ${root}/skills/doc/SKILL.md и следуй им. ` +
  `Search first — только так: python3 ${root}/skills/kb-search/gitmark.py --root ${root} search "запрос" ` +
  "(обязательно с --root, иначе возьмёшь чужой или несуществующий индекс); существующий " +
  "документ редактируй, а не дублируй; frontmatter (node_type, title, service, " +
  "status: active, updated: сегодняшняя дата — узнай `date +%F`); ≥1 типизированная " +
  "ссылка на код или сиблинг-док; индексная строка — только в README своей папки. " +
  "Факты бери из кода и файлов корня, не выдумывай; если кусок плана противоречит " +
  "фактам — сделай по фактам и скажи об этом в note. lint и index запускает скрипт " +
  "после тебя — сама не запускай. Если кусок невозможно выполнить честно — не " +
  "работай в обход: верни written: skipped и объяснение в note.";

phase("Свежий индекс для поиска");
// Свежий worktree не имеет .gitmark (gitignored) — без этой команды «search
// first» кураторов деградирует в grep (замечено приёмочным прогоном 05).
const pre = await world.run("python3", [
  `${root}/skills/kb-search/gitmark.py`,
  "--root",
  root,
  "index",
]);
log(`index: ${(pre.stdout + pre.stderr).trim()}`);
if (pre.exitCode !== 0) {
  return abort(
    `Предпрогон индекса не удался (exit ${pre.exitCode}) — кураторов не запускал: без «search first» они работали бы вслепую.`,
    `gitmark index:\n${(pre.stdout + pre.stderr).trim()}`,
  );
}

phase("Кураторы пишут свои куски KB параллельно");
log(`Кусков: ${pieces.length}, каждый ведёт свой куратор`);
const results = await Promise.all(
  pieces.map(async (p, i) => {
    let r: PieceResult;
    try {
      r = await agent(`curator-${i}`, { system: curatorRules }).ask<PieceResult>(
        `Корень KB: ${root}\nОбщая задача: ${task}\n\nТвой кусок: ${JSON.stringify(p)}\n` +
          `Выполни его по правилам выше и верни {path, written, note}.`,
      );
    } catch (e) {
      // Один отказавший куратор не хоронит остальных — как в challenger.workflow.ts.
      r = { path: p.path, written: "skipped", note: `куратор не отработал: ${String(e)}` };
    }
    report({ path: r.path ?? p.path, written: r.written ?? "skipped", note: r.note ?? "" });
    return r;
  }),
);

phase("Lint-гейт после сборки");
const lint = await world.run("python3", [`${root}/skills/kb-search/gitmark.py`, "--root", root, "lint"]);
let lintText = `${lint.stdout}\n${lint.stderr}`.trim();
log(lint.exitCode === 0 ? "lint зелёный с первого прогона" : `lint красный:\n${lintText}`);

phase("Долечивание до зелёного lint");
const healer = agent("healer", {
  system:
    "Ты долечиватель KB: правишь ровно то, на что указал lint (битые ссылки, сироты, " +
    "рассинхрон реестра), внутри корня, ничего не коммитишь и не выдумываешь. " +
    "Если замечание линтера невыполнимо — скажи прямо, не имитируй починку.",
});
let green = lint.exitCode === 0;
let rounds = 0;
let healFailed = "";
for (let round = 1; !green && round <= 4; round += 1) {
  rounds = round;
  log(`Круг долечивания ${round} из 4`);
  try {
    await healer.ask(
      `Корень KB: ${root}. gitmark lint красный, исправь его замечания:\n${lintText}\n` +
        `Правки ограничь тем, что требует lint; содержательное не переписывай.`,
    );
  } catch (e) {
    healFailed = `долечивание прервано: healer не отработал (${String(e)})`;
    break;
  }
  const recheck = await world.run("python3", [
    `${root}/skills/kb-search/gitmark.py`,
    "--root",
    root,
    "lint",
  ]);
  green = recheck.exitCode === 0;
  if (!green) {
    lintText = `${recheck.stdout}\n${recheck.stderr}`.trim();
  }
}

phase("Пересборка индекса и отчёт");
if (green) {
  const idx = await world.run("python3", [
    `${root}/skills/kb-search/gitmark.py`,
    "--root",
    root,
    "index",
  ]);
  log(`index: ${idx.stdout.trim() || idx.stderr.trim()}`);
}

return {
  conclusion: green
    ? `Собрано и долечено до зелёного lint: кусков ${results.length}, кругов долечивания ${rounds}.`
    : healFailed || `Потолок долечивания: после ${rounds} кругов lint остался красным — смотри последний вывод в notCovered.`,
  green,
  rounds,
  pieces: results,
  verified: green
    ? ["gitmark lint (world.run, exit 0)", "gitmark index (world.run)"]
    : ["gitmark lint (world.run) — красный, перечислен в notCovered"],
  notCovered: green ? [] : [`хвост lint:\n${lintText}`],
};
