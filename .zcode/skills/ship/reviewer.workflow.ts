/* zcode-workflow
description: Независимый ревью диффа тикета — шаг 6 девфлоу /ship.
args:
  ticket:
    type: string
    description: "Что строит тикет: поведение, критерии приёмки, затронутые файлы."
    required: true
  base:
    type: string
    description: "Реф, от которого меряется дифф (например main или HEAD~1)."
    required: true
*/

// Independent review gate (/ship step 6). Invoked by the ship skill:
// CreateWorkflow(path=<this file>, args={ticket, base}, subagent_model=<reviewer role>).
// The reviewer runs on the model assigned to the `reviewer` role — fail-closed
// verified by the skill before this call. Read-only: nobody here edits anything.

interface Finding {
  /** Путь к файлу и строка: "src/a.py:42". */
  where: string;
  /** Одно предложение: в чём проблема, не как чинить. */
  claim: string;
  /** Чем показано: строки кода, сценарий, вывод команды. */
  evidence: string;
  /** high — баг, который попадёт в прод; medium — реальный дефект без взрыва; low — пограничное. */
  severity: "high" | "medium" | "low";
}

interface Confirmation {
  /** true — находка воспроизводится по evidence независимо. */
  holds: boolean;
  /** Что увидел подтверждающий: воспроизвёл / не воспроизвёл и почему. */
  note: string;
}

const ticket = String(args.ticket ?? "");
const base = String(args.base ?? "HEAD");
if (!ticket.trim()) {
  return { conclusion: "Тикет не передан (args.ticket) — ревью нечего мерять.", findings: [], notCovered: ["всё"] };
}

phase("Независимый ревью диффа");
log(`Ревью диффа от ${base}`);
const reviewer = agent("reviewer", {
  system:
    "Ты независимый ревьюер чужого диффа: логические и security-баги, только чтение. " +
    "Ничего не редактируй и не коммить. Каждый claim подкрепляй точным местом и сценарием, " +
    "при котором поведение ломается. Если находка невозможна — не выдумывай. " +
    "Если дифф не найти — остановись и скажи об этом прямо.",
});
const review = await reviewer.ask<{ findings: Finding[] }>(
  `Тикет: ${ticket}\n\n` +
    `Сам посмотри дифф: git diff ${base} — и прочитай затронутые файлы целиком там, где ` +
    `нужен контекст. Найди логические и security-баги до попадания в прод: сломанные инварианты, ` +
    `незакрытые ресурсы, инъекции, гонки, потерянные ошибки. Стиль не ревьюится.`,
);

phase("Подтверждение находок свежими глазами");
log(`Находок: ${review.findings.length}, подтверждаю каждую независимо`);
const confirmed = await Promise.all(
  review.findings.map(async (f, i) => {
    const c = await agent(`confirmer-${i}`, {
      system:
        "Ты подтверждающий: воспроизводишь находку ревьюера строго по её evidence, читая код. " +
        "Ничего не редактируй. Не воспроизводится — говори прямо, согласие без проверки запрещено.",
    }).ask<Confirmation>(
      `Находка ревьюера:\nгде: ${f.where}\nпроблема: ${f.claim}\nдоказательство: ${f.evidence}\n\n` +
        `Открой файл и воспроизведи проблему сама по себе. holds=true только если проблема реально там.`,
    );
    return { finding: f, confirmation: c };
  }),
);

const kept = confirmed.filter((x) => x.confirmation.holds);
const dropped = confirmed.length - kept.length;
return {
  conclusion:
    review.findings.length === 0
      ? "Находок нет: дифф чист по логике и security."
      : `Находок: ${confirmed.length}, подтверждено независимо: ${kept.length}, не воспроизведено: ${dropped}.`,
  findings: confirmed.map((x) => ({
    ...x.finding,
    status: x.confirmation.holds ? "verified" : "unconfirmed",
    confirmationNote: x.confirmation.note,
  })),
  notCovered: ["стиль и архитектура — не входят в этот гейт; тесты — отдельный шаг лупа"],
};
