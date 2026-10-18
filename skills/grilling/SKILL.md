---
name: grilling
description: Autonomous stress-test of a plan, decision, or idea — the agent resolves the solvable questions itself (each with evidence), a red-team challenger on its own model attacks the draft, and the operator gets one readable digest to approve. Interactive questions only where the answer cannot be derived. Every request to shape a plan enters this flow — "погрилл", "grill this", "прогони гриллинг", /grilling, «оформи», «оформи план» said in conversation, and the triage of open issues («триаж ишью») are equal entry points, taken at the ready-draft stage; a plan is never published without its grill (the only bypass is the operator's explicit opt-out, recorded in the contract's Context). Ends with a single-slice plan contract (docs/plans/<slug>.md) approved via the native plan gate, or — when the unit is built by more than one slice (multi-slice, step 7) — with the tickets the same session publishes by running /to-tickets in full (the plan gate plus the operator's ticket quiz are the approvals).
---

# Grilling — autonomous decisions, one approval gate

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

Вход-фразы разговора — «оформи», «оформи план», синонимы — равные входы во флоу:
остановка на файле-артефакте без грилла — ошибка маршрутизации, не завершение
(skill texts load only on invocation, so this rule also ships in the session-start
hook — the one carrier visible before this skill is ever invoked).

1. **Enter plan mode** (the native read-only gate). Everything below happens before any
   write outside the KB.
2. **Research the frontier.** Expand the idea into the questions that must be answered
   before code exists. For each: `kb-search`'s gitmark search, read the code, run cheap
   read-only commands. Facts you find are yours to use. Every entry sweeps the open
   issues — list `.zcode/ontoship/issues/*.md`, skipping files whose status block
   line starts with `**Статус.** Закрыт` (archive entries of migrated tickets,
   nothing to plan; the closed-status spelling ship's issue contour fixes — the
   same line its snapshot counter matches) (a missing folder
   means nothing to
   sweep; the flow runs on): an open issue is frontier input like any other finding,
   the «триаж ишью» entry is this sweep named as the door. A triaged issue's content
   moves into the contract and its file is deleted (git keeps the history); an issue
   left out of this plan stays open for the next triage.
3. **Resolve autonomously.** For every two-way-door question: state the options, pick
   the best against the plan's stated criteria, and record
   `{id, question, choice, rationale, evidence, reversible}` —
   `id`: короткий уникальный идентификатор d1…dN, из него строится имя
   субагента челленджа; дубль или пропуск id валит ран громко (the workflow
   validates ids before any subagent starts). **Evidence invariant:** every
   autonomous decision cites facts — `file:line` from the KB/code or command output.
   A decision you cannot back with evidence is escalated automatically, no exceptions.
   This is what keeps autonomy from decaying into guessing.
4. **Challenger pass.** Hand the whole draft to the red team — one run of the
   `challenger.workflow.ts` **next to this SKILL.md**:
   `CreateWorkflow(path=<that file>, args={decisions: <JSON array>}, subagent_model=<challenger role>)`.
   Resolve the role first: `roles.py resolve --json` (roles skill), then verify the
   model against **ListModels** — missing or disabled model **stops grilling** with a
   diagnostic (fail-closed; never fall back to your own model). A run that died for
   a model reason — a provider-stop of the whole run, or a repeated ContextLimit
   that ends the whole run — is relaunched clean exactly once on
   `subagent_model=<fallback role$level>` (the `fallback` role) with a loud note in
   the run output («ран #1 на <модель> не тянет — перезапущено на <фолбэк>»); resolve
   and verify the fallback role the same way
   before the relaunch, and a second model-death stops grilling with a diagnostic.
   Transient errors are the host runtime's retries — not a fallback signal: the
   fallback covers a model that cannot carry the run, never a configuration error
   (roles-fallback-substrate/02). Every challenger sees
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
7. **Write the contract, run the definition-of-done pass, present for
   approval.** Write `docs/plans/<slug>.md`
   (`node_type: plan`, per `kb-curate`: Goal / Done / Scope / Constraints / Context)
   and crystallised terms into `CONTEXT.md` (if the project keeps one) and
   `docs/decisions/`. The contract's `Context` carries the **provenance
   line** — exactly one, the plan's entry record (flow-semantics): either
   the grill trace — `Провенанс: грилл — dwfrun-<id>, YYYY-MM-DD`, the
   challenger run of step 4 plus its date — or the operator's explicit
   opt-out naming the rejected passes —
   `Провенанс: opt-out оператора — отклонено: <пассы>` (the live list:
   challenger — step 4; юнит-чек — the unit check, step 7; DoD-pass — step 7;
   дайджест — step 5). An artifact without the record is
   byte-identical to silently skipped grilling; `to-tickets` (step 0)
   refuses such a plan by name — this line is what the guarantee rides on.
   The `Context` also carries the **quote carrier** (behavior-reel): a
   `### Цитаты оператора (дословно)` block with every goal-shaping wording the
   operator produced in this session, verbatim, one `- «…»` bullet per wording —
   never reworded, translated, or silently dropped. A topic-run (grilling a
   bare idea, no document) sources the block from the operator's words in the
   launch argument. A wording the operator only picked from options you
   authored is not their verbatim; such a goal enters the block as
   `- парафраз: …` — the visible marker for every goal with no operator wording
   to quote. The block is the single carrier: later runs (ticket splitting,
   the counter-layer) take the goals they quote **only** from it — a quote has
   no session seam left to die at. Run the
   **definition-of-done pass over the contract**: every `Scope` deliverable is
   covered by a `Done` criterion stating an observable fact a third party can
   verify — a criterion naming an activity or a degree («improve», «clean up»)
   is rewritten until it names one. **The unit check — before presenting.**
   The contract supplies exactly one unit: whole and minimally indivisible.
   Its anchor is non-circular — one line:
   **the unit = the set of plan acceptance criteria in `Done`**
   (the observable facts the finished unit makes true), independent of the
   slice criteria its tickets will carry. If that set
   decomposes into two non-empty independent groups — either group's
   criteria could be met and shipped without the other — the draft is two
   units: cut it into two plans now, before publication; epics are issues,
   never one plan. A doc-plan's unit is a verifiable knowledge artifact: its
   criteria state what a reader can check. Several deliverables under one
   non-decomposable criteria set is still one unit — the deliverable count
   is not the unit test. Then present the plan via **ExitPlanMode** —
   the contract plus the digest. The native approval covers the whole package
   — nothing in it is re-asked afterwards: a rejection names the disputed
   item, you re-decide only that item and re-present. After the approval the
   flow continues by itself (flow-continuity): when **the unit is built by
   more than one slice** (multi-slice), the contract continues into a full
   `/to-tickets` run (steps 0–6) in this same session — no manual command
   between the approval and the ticket quiz (for that package the approvals
   are two: this gate plus the ticket quiz). The predicate is the unit's,
   decided from the contract you have just written, not left to a later
   reader: multi-slice means the one unit's plan criteria are reached
   through several working-state slices, each sized by the natural test
   «would this ship as one `/ship` slice?»; the retired predicate —
   counting independently shippable deliverables — is not the unit test (a
   unit may legitimately ship several deliverables on its way). A unit one
   slice builds — a single-slice contract — ends the chain here: the
   closing report names exactly one road (the operator's hand-run `/ship`
   on the file plan) and offers no manual `/to-tickets`. An interrupted
   session is the one legitimate gap: the operator then launches
   `/to-tickets` by hand on the written contract — the documented fallback,
   and its step 0 reads the provenance line this contract carries. `/ship`
   is never started by you — the operator launches it by hand.

## Variants

- **No-write grill** ("погрилл", /grill): the same flow, but publish nothing — no
  contract, no CONTEXT.md, no decisions; the resolution lives in the conversation.
  Say so up front.
- **Hard bug** → the `diagnose` skill instead (root cause, not a design contract).

## Invariants

- Evidence or escalate — for autonomous decisions, no third option.
- Вход-фразы разговора («оформи», «оформи план», синонимы) запускают флоу целиком —
  грилл включён; артефакт без записи грилла ловится именованным отказом
  провенанс-контура (to-tickets step 0; /ship — provenance check в Input).
- The challenger's role model comes from the roles registry, fail-closed verified.
- KB writes go through `kb-curate` (search first, no duplicates, frontmatter, links).
- The stop-points in `Constraints` are machine-enforced downstream: write them as
  `stop-before-commit`, `stop-after-mr`, `no-deploy` — the ship skill maps them to
  native permission gates.
