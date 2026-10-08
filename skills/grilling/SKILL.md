---
name: grilling
description: Autonomous stress-test of a plan, decision, or idea — the agent resolves the solvable questions itself (each with evidence), a red-team challenger on its own model attacks the draft, and the operator gets one readable digest to approve. Interactive questions only where the answer cannot be derived. Ends with a plan contract (docs/plans/<slug>.md) approved via the native plan gate. Use when the user says "погрилл", "grill this", "прогони гриллинг", or runs /grilling.
---

# Grilling — autonomous decisions, one approval

The operator brings a plan, decision, or half-formed idea. You turn it into a resolved
design and a plan contract — **deciding most of it yourself**, not interviewing them
round by round. The division of labour:

> **Two-way doors you decide; one-way doors the operator decides.**

A decision is yours to make when it is reversible (redoing it is cheap), does not change
the product's observable behaviour for people, and the facts to decide it live in the
repo or the KB. Escalate only:

- taste / product choice — the user will perceive the difference;
- irreversibility or risk — money, data loss, security posture;
- external context the repo cannot supply — business priorities, budgets, deadlines;
- philosophy forks — options tie on every criterion but diverge in direction, and
  someone must live with the choice.

Everything else on the frontier is yours. Asking about a two-way door is a bug in your
execution; guessing about a one-way door is a worse one.

## The flow

1. **Enter plan mode** (the native read-only gate). Everything below happens before any
   write outside the KB.
2. **Research the frontier.** Expand the idea into the questions that must be answered
   before code exists. For each: `kb-search`'s gitmark search, read the code, run cheap
   read-only commands. Facts you find are yours to use.
3. **Resolve autonomously.** For every two-way-door question: state the options, pick
   the best against the plan's stated criteria, and record
   `{question, choice, rationale, evidence, reversible}`. **Evidence invariant:** every
   autonomous decision cites facts — `file:line` from the KB/code or command output.
   A decision you cannot back with evidence is escalated automatically, no exceptions.
   This is what keeps autonomy from decaying into guessing.
4. **Challenger pass.** Hand the whole draft to the red team — one run of the
   `challenger.workflow.ts` **next to this SKILL.md**:
   `CreateWorkflow(path=<that file>, args={decisions: <JSON array>}, subagent_model=<challenger role>)`.
   Resolve the role first: `roles.py resolve --json` (roles skill), then verify the
   model against **ListModels** — missing or disabled model **stops grilling** with a
   diagnostic (fail-closed; never fall back to your own model). Every challenger sees
   the **whole draft** and attacks one target decision — cross-decision contradictions
   are exactly what it exists to catch. Objections with `severity: substantial` are
   **not resolved silently**: re-decide the decision in light of the argument, and if
   the re-decision is not clearly better, the decision moves to escalation together
   with the dispute. A challenger that failed (reported in `failed`) is surfaced in
   the digest like an unresolved objection for its decision — a decision nobody
   attacked is not the same as a decision that held.
5. **Digest** — the operator-readable summary of what was decided:
   `question → **decided**: … → why (2–3 sentences with the evidence) → what was
   rejected and the main reason → risk/cost of revisiting`. Mark each item
   🔄 reversible / 🚪 one-way. One glance per item.
6. **Escalate the remainder** — only the true one-way doors and the
   challenger-contested items, as a single `AskUserQuestion` batch (≤4 questions per
   call, recommended option first, previews for visual forks). Never re-ask what the
   digest already settles.
7. **Write the contract, run the definition-of-done pass, ask once.** Write `docs/plans/<slug>.md`
   (`node_type: plan`, per `kb-curate`: Goal / Done / Scope / Constraints / Context)
   and crystallised terms into `CONTEXT.md` / `docs/decisions/`. Run the
   **definition-of-done pass over the contract**: every `Scope` deliverable is
   covered by a `Done` criterion stating an observable fact a third party can
   verify — a criterion naming an activity or a degree («improve», «clean up»)
   is rewritten until it names one. Then present the plan via **ExitPlanMode** —
   the contract plus the digest. The native approval **is** the
   single approval of the whole package: a rejection names the disputed item, you
   re-decide only that item and re-present. `/ship` is never started by you — the
   operator launches it by hand.

## Variants

- **No-write grill** ("погрилл", /grill): the same flow, but publish nothing — no
  contract, no CONTEXT.md, no decisions; the resolution lives in the conversation.
  Say so up front.
- **Hard bug** → the `diagnose` skill instead (root cause, not a design contract).

## Invariants

- Evidence or escalate — for autonomous decisions, no third option.
- The challenger's role model comes from the roles registry, fail-closed verified.
- KB writes go through `kb-curate` (search first, no duplicates, frontmatter, links).
- The stop-points in `Constraints` are machine-enforced downstream: write them as
  `stop-before-commit`, `stop-after-mr`, `no-deploy` — the ship skill maps them to
  native permission gates.
