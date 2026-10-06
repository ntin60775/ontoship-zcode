---
name: ship
description: Ship ONE ticket through the gated dev-flow — worktree → implement → tests → independent review on an explicitly assigned model → dev/prod checks → merge, one ticket per run, strictly sequential, launched only by hand by the operator. Use when the operator runs /ship with a plan folder, a ticket path, a file plan, or an ad-hoc what+why+done. Never starts itself and is never started by another skill.
---

# /ship — one ticket through the gated loop

**This skill runs only when the operator launches it by hand.** Entry skills
(grilling, to-tickets, diagnose, prototype, handoff, code-review, architecture) end in
plans, tickets, or reports — they never call this. One ticket (or one file plan) per
run, strictly sequential.

## Input

| argument | meaning |
|---|---|
| `docs/plans/<slug>/` | plan folder → take the **first non-archived ticket** (by `NN`); verify its `Blocked by` are all `archived` first |
| `docs/plans/<slug>/NN-<ticket>.md` | that specific ticket (blockers still checked) |
| `docs/plans/<slug>.md` | file plan → ship as a **single slice** on its `Goal`/`Done` |
| what + why + done-criteria | ad-hoc run — write the contract down in the run report |
| *(empty)* | the most recent plan (file or folder, by `updated:`) |

## The loop — track it as a TodoWrite checklist from step 1

1. **Research** — facts, not guesses: read the code, logs, traces; reproduce before
   fixing. The ticket's acceptance criteria are the spec.
2. **Goal** — restate the ticket's `What to build` + acceptance criteria as the
   TodoWrite goal line (or the plan's `Goal`/`Done` for a file plan).
3. **Isolate** — dedicated **`git worktree`**: `git worktree add ../<repo>-ship-<nn> -b
   ship/<slug>-<nn>`. `main` stays untouched; rollback is dropping the worktree.
4. **Implement** — to the acceptance criteria inside the worktree; keep doc↔code
   linked (`implemented_by`) per `kb-curate`.
5. **Tests** — write/adjust unit + E2E for the ticket; the test is part of the feature.
   Run the suite until green (background long runs, report honestly).
6. **Independent review** — resolve the two gate roles (`roles.py resolve --json`,
   roles skill) — `reviewer` and `confirmer` — and verify each against **ListModels**:
   missing/disabled model or absent level → **stop the run** with a diagnostic naming
   the role and the layer file to fix (fail-closed; never review or confirm with your
   own model). Then run the gate as two CreateWorkflows:
   `CreateWorkflow(path=reviewer.workflow.ts next to this SKILL.md, args={ticket:
   "<what + acceptance criteria + touched files>", base: "<merge-base ref>",
   root: "<the worktree created in step 3>", reviewerModel: "<reviewer role model,
   API id from its zcode card>"})`
   — it ends with raw findings; the lens substrate is direct neuraldeep API calls
   made by the workflow itself (gate-followups-2/07): `reviewerModel` is the bare
   API id of the reviewer-role model (its zcode card, e.g. "qwen3.6-unlim-xl");
   credentials and baseUrl come from the provider card in zcode, nothing else
   is configured on the machine;
   `CreateWorkflow(path=confirm.workflow.ts next to this SKILL.md, args={root:
   "<the same worktree>", findings: <the `findings` field of the review run's
   return — the raw findings array, compact JSON>, ticket: "<the same ticket>"},
   subagent_model=<confirmer role$level>)` —
   it returns the verdicts (findings with verified/unconfirmed/unverified +
   conclusion + notCovered) — pass the findings array as-is, even when empty (the confirm
   run reports the empty case honestly). If the review run errored or stopped,
   there is nothing to confirm: stop the run and report the failure; never run
   the confirm run on a failed review. Fix every `verified` finding; refute only
   with evidence; `unconfirmed` findings are reported to the operator, never dropped.
   `unverified` findings are a failed check, not a refutation — the confirmer
   did not answer even after one retry (a failed ask is retried exactly once,
   no cause sniffing; queue-2/17 owns cause classification); report them to
   the operator next to `unconfirmed`, never dropped.
7. **Dev checks** — merge the worktree branch into `dev` (local branch when there is no
   remote; MR when there is) and run the full suite there. Red → fix in the worktree,
   do not merge onward.
8. **Prod checks** — E2E/smoke against the real contour when one exists; skip only when
   the plan's `Constraints` say so or no contour exists (say which).
9. **Ship** — merge to `main` and deploy per the plan's deploy procedure; mark the
   ticket `status: archived` (`updated: today`, via `kb-curate`); a plan folder whose
   tickets are all archived becomes `status: archived`. Then auto-write the rolling
   snapshot `.scratch/handoff-current.md` per the handoff skill — the same fixed file
   `/handoff` writes, full regenerate, provenance stamps from the handoff skill's own
   sources (the `.session-id` marker and the current commit) — from the run's facts:
   the ticket, the release tag and short hashes of the landed commits (feature, dev
   merge, main merge, release), the plan's Open, concrete Next. A shift that ended on
   a closed ticket still hands the next session a current snapshot; this write is
   part of shipping, not an optional extra, and is independent of the deploy
   procedure.

## Stop-points and confirmations

From the plan contract's `Constraints`, enforced verbatim:

- `stop-before-commit` — after the review (step 6: both gate runs done and the
  verified findings addressed) stop with the uncommitted diff and
  wait for the operator's "continue". **Default when the contract names nothing.**
- `stop-after-mr` — after step 7, stop for the operator's review.
- `no-deploy` — skip the deploy in step 9; the rolling-snapshot write still
  happens (it is not part of the deploy).

**Never skippable, with or without a Constraints block:** before merging to `main`
(step 9) and before any deploy, ask the operator — one `AskUserQuestion` each, showing
what is about to land. A "continue" the operator typed earlier in this run covers the
stop-point it answered, not these two confirmations.

## Honest degradation

No remote → "MR" is a local merge into `dev`; say so in the run report. No deploy
contour → step 8 is the test suite; say so. Every deviation from the full loop is
written into the ticket's shipping note — the one thing that may never happen silently.
