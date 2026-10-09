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
   Run the suite until green (background long runs, report honestly). A suite run is
   telemetry, not a fact by itself: it counts as a fact only with its log read — the
   first failure, the counters, the warnings. Filtering the output must not eat the
   exit code (`pytest | tail` lesson); rc=0 with the log unread is activity, not a fact.
6. **Independent review** — resolve the two gate roles (`roles.py resolve --json`,
   roles skill) — `reviewer` and `confirmer` — and verify each against **ListModels**:
   missing/disabled model or absent level → **stop the run** with a diagnostic naming
   the role and the layer file to fix (fail-closed; never review or confirm with your
   own model). Then run the gate as two CreateWorkflows:
   `CreateWorkflow(path=reviewer.workflow.ts next to this SKILL.md, args={ticket:
   "<what + acceptance criteria + touched files>", base: "<merge-base ref>",
   root: "<the worktree created in step 3>"}, subagent_model=<confirmer
   role$level>)`
   — it ends with raw findings. Then classify the diff by the same map the
   review run measured (numstat + untracked): the **light contour** iff every
   file of the map lies in `docs/**`, ends with `.md`, the raw numstat has no
   binary row (added/deleted print as `-` and the map drops them — check the
   raw rows before the map, gate-risk-scaling) and the map names none
   of the heavy paths — the heavy ones are explicit: `skills/**` (including
   `*.md`), `defaults/roles.md`, `.zcode/**`, root `README.md`/`AGENTS.md`,
   `deploy.json`, `package.json`, `.zcode-plugin/`, `hooks/**`, `scripts/**`,
   `tests/**`, `docs/ontology.md` (the engine reads it as the node_type
   dictionary — full contour regardless of the rest). Any file outside the
   light rule — the full contour, both runs as today. In the light contour at
   0 findings and full coverage the confirm run is NOT created (the
   «pass the findings array as-is, even when empty» below gets the doc-only
   branch); with findings the confirm runs unchanged. The DEFAULT lens
   substrate is host subagents
   (agent()) on the model assigned via `subagent_model` — the confirmer role
   model (lens-substrate-flash, operator decision 2026-10-09); the argument is
   live only since that migration (before it, the workflow contained no
   agent() at all). The direct neuraldeep API remains the explicit fallback:
   pass `substrate: "direct"` plus `reviewerModel: "<reviewer role model,
   API id from its zcode card>"` and `provider` (optional, default
   `neuraldeep-sub`) — credentials and baseUrl come from the provider card in
   zcode, nothing else is configured on the machine; a provider switch is
   configuration (card in zcode + `provider` + `reviewerModel`), never a repo
   edit; the run fails closed with a named diagnostic (role, config path,
   what is missing) when the config, the card, the key or the reviewer model
   is missing (external-dependencies/01). Mixed-up arguments are a named
   abort, never a silent ignore: `reviewerModel`/`provider` under the default
   substrate abort the run («имеет смысл только с substrate=direct»); both
   roles still resolve and verify fail-closed as today;
   `CreateWorkflow(path=confirm.workflow.ts next to this SKILL.md, args={root:
   "<the same worktree>", findings: <the `findings` field of the review run's
   return — the raw findings array, compact JSON>, ticket: "<the same ticket>"},
   subagent_model=<confirmer role$level>)` —
   it returns the verdicts (findings with verified/unconfirmed/unverified +
   conclusion + notCovered) — pass the findings array as-is, even when empty (the confirm
   run reports the empty case honestly). If the review run errored or stopped,
   there is nothing to confirm: stop the run and report the failure; never run
   the confirm run on a failed review. A review run that completed but did not
   cover every changed file — its report names a file as failed or the file is
   missing from the coverage — is not a review result either: a named failure
   is not «0 findings» (crossreview-adoption/03). Check the coverage in the
   report first; if a file is missing, relaunch the review run once, clean
   (same args, new run) and never confirm a partial review. If the same file
   fails again after the clean relaunch, stop the run with a diagnostic naming
   the file — accepted degradation class, output-budget overflow on big files
   (docs/reference/dependencies.md). Fix every `verified` finding; refute only
   with evidence; `unconfirmed` findings are reported to the operator, never dropped.
   `unverified` findings are a failed check, not a refutation — the confirmer
   did not answer even after one retry (a failed ask is retried exactly once,
   no cause sniffing; queue-2/17 owns cause classification); report them to
   the operator next to `unconfirmed`, never dropped.
7. **Dev checks** — the contour from step 6 picks the merge path. Full contour:
   merge the worktree branch into `dev` with a local `--no-ff` merge; MR is not
   part of this flow — only when the plan or the project explicitly assigns one
   (paired with the stop-point `stop-after-mr`). Run the full suite there.
   Red → fix in the worktree, do not merge onward. Light contour (doc-only
   ticket): the doc merge path of git-flow («Доковые и опс-коммиты») —
   straight to `main`, no dev merge and no release; suite + `lint --strict`
   before the push.
8. **Prod checks** — E2E/smoke against the real contour when one exists; skip only when
   the plan's `Constraints` say so or no contour exists (say which).
9. **Ship** — merge to `main` (a light-contour ticket merged it in step 7
   already) and deploy per the plan's deploy procedure (a doc-only ticket has
   no deploy — `deploy.json` maps no `docs/` path); mark the
   ticket `status: archived` (`updated: today`, via `kb-curate`); a plan folder whose
   tickets are all archived becomes `status: archived`. Then auto-write the rolling
   snapshot `.scratch/handoff-current.md` per the handoff skill — the same fixed file
   `/handoff` writes, full regenerate, provenance stamps from the handoff skill's own
   sources (the `.session-id` marker and the current commit) — from the run's facts:
   the ticket, the release tag and short hashes of the landed commits (feature, dev
   merge, main merge, release; a doc-only ticket has neither dev merge nor release —
   the snapshot writes «доковый мерж, без dev-hash» and the short hashes of the doc
   commits in main), the plan's Open, concrete Next. A shift that ended on
   a closed ticket still hands the next session a current snapshot; this write is
   part of shipping, not an optional extra, and is independent of the deploy
   procedure.

## Stop-points and confirmations

From the plan contract's `Constraints`, enforced verbatim:

- `stop-before-commit` — after the review (step 6: both gate runs done and the
  verified findings addressed) stop and wait for the operator's "continue",
  reporting facts only — refs and hashes, touched files, counts, gate verdicts.
  Never paste diff bodies into stop-points or confirmation windows: the operator
  reads diffs himself, when he considers it necessary (docs/ops/git-flow.md,
  «Режим»); show the diff only on his explicit request. **Default when the
  contract names nothing.**
- `stop-after-mr` — after step 7, stop for the operator's review.
- `no-deploy` — skip the deploy in step 9; the rolling-snapshot write still
  happens (it is not part of the deploy).

**Never skippable, with or without a Constraints block:** before merging to `main`
(step 9; step 7 in the light contour) and before any deploy, ask the operator — one
`AskUserQuestion` each, stating
what is about to land as facts (refs, hashes, counts; no diff bodies, same rule as
`stop-before-commit`). A "continue" the operator typed earlier in this run covers the
stop-point it answered, not these two confirmations.

## Honest degradation

The three constant deviations of this solo flow — no MR, no separate prod contour,
remote may be absent — live in docs/ops/git-flow.md («Отступления-константы»);
reference that section in the shipping note with one line instead of re-declaring
them in every run. Every deviation beyond those constants is still written into the
shipping note — the one thing that may never happen silently.
