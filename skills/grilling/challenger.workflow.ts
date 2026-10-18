/* zcode-workflow
description: Красная команда по черновику решений — pass гриллинга.
args:
  decisions:
    type: json
    description: Черновик решений (массив {id, question, choice, rationale, evidence, reversible})
    required: true
*/

// Challenger pass — red team over a draft of decisions (grilling step 4).
// Invoked by the grilling skill: CreateWorkflow(path=<this file>,
// args={decisions: <JSON array of Decision>}, subagent_model=<challenger role>).
// The challenger runs on the model assigned to the `challenger` role
// (fail-closed verified by the skill before this call).

interface Decision {
  /** Short decision id, e.g. "d3". */
  id: string;
  /** The question the decision answers. */
  question: string;
  /** The chosen option. */
  choice: string;
  /** Why this option won. */
  rationale: string;
  /** Facts the choice rests on: file:line pointers or command output. */
  evidence: string;
  /** Optional: whether redoing this decision is cheap (two-way door). */
  reversible?: boolean;
}

// BEGIN DECISION VALIDATION
// Loud validation before any subagent is named from the array: the live
// failure (ишью 09, dwfrun-62a83e74) was a host name collision —
// «challenger-undefined is used twice» — and a single missing id among valid
// ones does not fail at all (its objection would come back with id: undefined).
// A broken id is the same caller bug as broken syntax: it aborts here, with
// every broken position named, instead of falling over in a foreign layer.
// The id must be canonical d1…dN (/^d\d+$/): anything else — spaces, case
// drift, control characters — would flow into subagent names and abort text
// as-is. Plain JS semantics in the body; the three TS annotations are
// stripped verbatim by tests/test_challenger_validation.py, which pins them
// by name — a new annotation reds that driver with its name, not as a raw
// node SyntaxError.
function validateDecisions(decisions: Decision[]) {
  const broken: string[] = [];
  const seen = new Map<string, number>();
  decisions.forEach((d, i) => {
    const pos = `#${i + 1}`;
    if (d === null || typeof d !== "object" || Array.isArray(d)) {
      broken.push(`${pos}: решение — не объект`);
      return;
    }
    const id = d.id;
    if (typeof id !== "string" || id.length === 0) {
      broken.push(`${pos}: id отсутствует или пуст`);
    } else if (!/^d\d+$/.test(id)) {
      broken.push(`${pos}: id не каноничен — ожидается d1…dN (буква d и цифры)`);
    } else if (seen.has(id)) {
      broken.push(`${pos}: id "${id}" дублирует #${seen.get(id)}`);
    } else {
      seen.set(id, i + 1);
    }
  });
  return broken;
}
// END DECISION VALIDATION

interface Objection {
  /** id of the decision this objection targets. */
  id: string;
  /** substantial — the argument genuinely undermines the choice; minor — a fixable amendment; none — holds up. */
  severity: "substantial" | "minor" | "none";
  /** The argument itself: what breaks, under which scenario or unstated assumption. */
  argument: string;
  /** What observation or fact would make this argument decisive. */
  whatWouldDecide: string;
}

// BEGIN ARGS CONTRACT
// args.decisions arrives either as an already-parsed array or as a JSON string,
// depending on the host — accept both. Unparsable input fails LOUD (an errored run
// is what stops the grilling pass); an explicitly empty array is a benign no-op.
let decisions: Decision[] = [];
let unparsable = "";
const raw = args.decisions;
if (Array.isArray(raw)) {
  // densify first: a sparse array (a host-side delete leaves holes) would
  // let forEach skip the holes — positions neither validated nor challenged
  // (gate r3).
  decisions = Array.from(raw) as Decision[];
} else if (typeof raw === "string") {
  try {
    const parsed: unknown = JSON.parse(raw);
    // A string that parses to a non-array (null, object, number…) is the same
    // caller bug as broken syntax — abort with the value, not a bare TypeError.
    if (!Array.isArray(parsed)) {
      const text = JSON.stringify(parsed) ?? String(parsed);
      const kind = parsed === null ? "null" : typeof parsed;
      unparsable = `JSON распарсился, но это не массив (${kind}: ${text.slice(0, 80)})`;
    } else {
      decisions = parsed as Decision[];
    }
  } catch (e) {
    // The abort must carry the parser's own message plus length and TAIL of the
    // string: a truncated payload (no closing `]}`) and broken syntax (error with
    // a position) are told apart at a glance — both look identical from the head.
    const msg = e instanceof Error ? e.message : String(e);
    const head = raw.length > 80 ? `${raw.slice(0, 80)}…` : "";
    const tail = raw.length > 80 ? `…${raw.slice(-80)}` : raw;
    unparsable =
      `JSON.parse: ${msg}; получено ${raw.length} симв.` +
      (head ? `, голова: "${head}", хвост: "${tail}"` : `, строка: "${tail}"`);
  }
} else {
  // Missing and null are loud on purpose: a required arg must not silently
  // become an empty draft — that benign no-op is only for an explicitly
  // passed empty array (gate r1: undefined slipped through as one).
  unparsable = `не строка и не массив (${raw === null ? "null" : typeof raw}: ${String(raw).slice(0, 80)})`;
}
if (unparsable) {
  throw new Error(
    `args.decisions не распарсились (${unparsable}) — ` +
      "красная команда не запускалась, гриллинг обязан остановиться на этом.",
  );
}
// id validation runs after the parse abort and before the empty-array no-op:
// an empty draft has nothing to break, and no agent name is built until every
// id checks out (the abort names the broken positions — the caller-bug class
// of ишью 09).
const brokenIds = validateDecisions(decisions);
if (brokenIds.length > 0) {
  throw new Error(
    `args.decisions не прошли валидацию id (${brokenIds.join("; ")}) — ` +
      "красная команда не запускалась, гриллинг обязан остановиться на этом. " +
      "Контракт решения — шаг 3 skills/grilling/SKILL.md: {id, question, choice, rationale, evidence, reversible}.",
  );
}
// END ARGS CONTRACT
if (decisions.length === 0) {
  return {
    conclusion: "Черновик решений пуст — оспаривать нечего.",
    objections: [],
    failed: [],
    notCovered: ["всё — аргументы не переданы"],
  };
}

// Every challenger sees the WHOLE draft (cross-decision contradictions are the
// red team's main catch), attacks its own target, calibrates severity alike.
const draft = JSON.stringify(decisions, null, 2);

phase("Красная команда по черновику решений");
log(`Оспариваю ${decisions.length} решений — каждый challenger видит весь черновик`);
const settled = await Promise.all(
  decisions.map(async (d) => {
    try {
      const o = await agent(`challenger-${d.id}`, {
        system:
          "Ты красная команда проектных решений: твоя работа — ломать выбор, не подтверждать его. " +
          "Решение судишь как данное. Можешь читать файлы репозитория, чтобы проверить факты из evidence, " +
          "но не редактируй ничего и не запускай команды. severity калибруй одинаково: " +
          "substantial — аргумент реально подрывает выбор или вскрывает противоречие с другим решением черновика; " +
          "minor — поправка, не ломающая выбор; none — устояло, не выдумывай возражений. " +
          "Если после честной попытки решение устояло — так и скажи.",
      }).ask<Objection>(
        `Весь черновик решений:\n${draft}\n\n` +
          `Твоя цель — решение ${d.id}: ${d.question}\nВыбрано: ${d.choice}\n` +
          `Обоснование: ${d.rationale}\nФакты: ${d.evidence}\n` +
          `${d.reversible === false ? "Дверь односторонняя (решение дорого переделать).\n" : ""}` +
          `Найди сильнейший аргумент против: сценарий, условие, невысказанное допущение — ` +
          `или противоречие с другим решением этого же черновика. ` +
          `Факты из evidence проверь по репозиторию, где можешь.`,
      );
      return { ok: true as const, objection: { ...o, id: d.id } };
    } catch (err) {
      // Ловятся только логические отказы (валидация, контекст). Модельные ошибки —
      // rate limit, перегрузка, сеть — ретраит сам рантайм workflow до успеха.
      return { ok: false as const, id: d.id, error: String(err) };
    }
  }),
);

// Один упавший challenger не хоронит возражения остальных.
const objections = settled.filter((s) => s.ok).map((s) => s.objection);
const failed = settled.filter((s) => !s.ok).map((s) => ({ id: s.id, error: s.error }));

const substantial = objections.filter((o) => o.severity === "substantial").length;
const minor = objections.filter((o) => o.severity === "minor").length;
return {
  conclusion: `Оспорено ${decisions.length} решений: ${substantial} существенных возражений, ` +
    `${minor} поправок${failed.length ? `, упало challengers: ${failed.length}` : ""}.`,
  objections,
  failed,
  notCovered: ["аргументы без опоры на репозиторий не перепроверялись, если evidence не содержал путей"],
};
