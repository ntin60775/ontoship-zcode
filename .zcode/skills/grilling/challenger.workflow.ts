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

// args.decisions arrives either as an already-parsed array or as a JSON string,
// depending on the host — accept both. Unparsable input fails LOUD (an errored run
// is what stops the grilling pass); an explicitly empty array is a benign no-op.
let decisions: Decision[] = [];
let unparsable = false;
const raw = args.decisions;
if (Array.isArray(raw)) {
  decisions = raw as Decision[];
} else if (typeof raw === "string") {
  try {
    decisions = JSON.parse(raw) as Decision[];
  } catch {
    unparsable = true;
  }
} else if (raw !== undefined && raw !== null) {
  unparsable = true;
}
if (unparsable) {
  throw new Error(
    `args.decisions не распарсились (${typeof raw}: ${String(raw).slice(0, 80)}…) — ` +
      "красная команда не запускалась, гриллинг обязан остановиться на этом.",
  );
}
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
