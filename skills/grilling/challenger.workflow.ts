// Challenger pass — red team over a draft of decisions (grilling step 3).
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

const raw = String(args.decisions ?? "[]");
let decisions: Decision[] = [];
try {
  decisions = JSON.parse(raw) as Decision[];
} catch {
  decisions = [];
}
if (decisions.length === 0) {
  return {
    conclusion: "Черновик решений пуст — оспаривать нечего.",
    objections: [],
    notCovered: ["всё — аргументы не переданы"],
  };
}

phase("Красная команда по черновику решений");
log(`Оспариваю ${decisions.length} решений`);
const objections = await Promise.all(
  decisions.map((d) =>
    agent(`challenger-${d.id}`, {
      system:
        "Ты красная команда проектных решений: твоя работа — ломать выбор, не подтверждать его. " +
        "Решение судишь как данное. Можешь читать файлы репозитория, чтобы проверить факты из evidence, " +
        "но не редактируй ничего и не запускай команды. " +
        "Если после честной попытки решение устояло — так и скажи (severity none), не выдумывай возражений.",
    }).ask<Objection>(
      `Решение ${d.id}: ${d.question}\n` +
        `Выбрано: ${d.choice}\nОбоснование: ${d.rationale}\nФакты: ${d.evidence}\n\n` +
        `Найди сильнейший аргумент против этого выбора: какой сценарий, условие или ` +
        `невысказанное допущение его ломает? Проверь факты из evidence по репозиторию, где можешь.`,
    ),
  ),
);

const substantial = objections.filter((o) => o.severity === "substantial").length;
const minor = objections.filter((o) => o.severity === "minor").length;
return {
  conclusion: `Оспорено ${decisions.length} решений: ${substantial} существенных возражений, ${minor} поправок.`,
  objections,
  notCovered: ["аргументы без опоры на репозиторий не перепроверялись, если evidence не содержал путей"],
};
