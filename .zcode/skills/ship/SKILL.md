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
   exit code (`pytest | tail` ate rc — gate-followups-2/02); rc=0 with the log
   unread is activity, not a fact. A new test matrix ships with a negative or
   mutation probe — a case that must fail while the behavior under test is broken;
   a matrix without one is not evidence. Live precedents: the redact matrix (a
   positive must both change the line and keep the secret out of the output;
   out≠input alone masks partial replacement — tests/redact_matrix.mjs), the
   verdict matrix (tests/verdict_matrix.mjs), the extractParts one-shot probe
   (reads must equal extracted files — tests/diff_map.mjs).
6. **Independent review** — resolve the two gate roles (`roles.py resolve --json`,
   roles skill) — `reviewer` and `confirmer` — and verify each against **ListModels**:
   missing/disabled model or absent level → **stop the run** with a diagnostic naming
   the role and the layer file to fix (fail-closed; never review or confirm with your
   own model). Preflight the assembled args before every submit of either run:
   re-read the literal args about to be sent against what the script reads in this
   call (ticket, base, root; the findings array in full — a stub compiles and starts
   exactly like a real array, and its verdicts are garbage; dwfrun-5d20732c,
   roles-fallback-substrate/01); garbage is never launched — a run that did start on
   garbage args is stopped immediately and relaunched clean. A run that died for a
   model reason — a provider-stop of the whole run, or a repeated ContextLimit that
   ends the whole run — is relaunched clean exactly once on
   `subagent_model=<fallback role$level>` with a loud degradation note in the run
   output («ран #1 на <модель> не тянет — перезапущено на <фолбэк>»); resolve the
   `fallback` role
   (roles-fallback-substrate/01) and verify it against ListModels before the
   relaunch, fail-closed as above; a second model-death stops the shipping run with
   a diagnostic. Transient errors are the host runtime's retries — not a fallback
   signal — and a model missing from ListModels stays a fail-closed stop before
   launch: the fallback covers a model that cannot carry the run, never a
   configuration error. The fallback branch is live-non-inducible (deterministic
   model refusals kill the run before the script — the contour skill, lesson 6):
   it is anchored by this text, not by a live proof. Then run the gate as two
   CreateWorkflows, each on its own role's model — review on `reviewer`, confirm
   on `confirmer` (roles-fallback-substrate/02):
   `CreateWorkflow(path=reviewer.workflow.ts next to this SKILL.md, args={ticket:
   "<what + acceptance criteria + touched files; a ticket with a Reel section
   adds its example lines «Цель → Вход → Наблюдаемый выход» verbatim — the
   workflow redacts secret-looking fragments to [REDACTED] before the lenses
   see them, the honest degradation its args contract names; a ticket
   without one adds the line «Reel: отсутствует»>", base: "<merge-base ref>",
   root: "<the worktree created in step 3>"}, subagent_model=<reviewer
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
   branch); with findings the confirm runs unchanged. The lens transport is
   host subagents (agent()) only — there is no direct-API fallback: the
   workflow takes no substrate/provider/model arguments and makes no API calls
   of its own (roles-fallback-substrate/03 demolished the direct fallback,
   2026-10-11); the lens model is the one assigned via
   `subagent_model` — each run's own role
   model: the reviewer's for the review run, the confirmer's for the confirm
   run (lens-substrate-flash put the gate on the confirmer, operator decision
   2026-10-09; roles-fallback-substrate/02 moved the review run onto the
   reviewer, 2026-10-11); the `subagent_model` argument is live only since the
   lens-substrate-flash migration (before it, the workflow contained no
   agent() at all). Both roles still resolve and verify fail-closed as before;
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
   the plan's `Constraints` say so or no contour exists (say which). For a ticket with
   a `## Reel` section the live E2E runs every example's «Вход» against the real
   contour — the observed outputs re-derive the «обещано → фактически» lines of the
   merge-to-main window (the form and the «совпало» ban live in the stop-points
   section; the stop-before-commit line already carries the step 5 outputs).
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
  reporting facts only — refs and hashes, touched files, counts, gate verdicts,
  and the Reel diff line (behavior-reel/04): a ticket with a `## Reel` section
  carries one line per example — «обещано → фактически», where «обещано» is the
  example's «Наблюдаемый выход» verbatim and «фактически» is the output a live
  E2E run of the example's «Вход» actually printed (at this stop-point that is
  the step 5 run; an example without a live case has no step 5 output — run its
  «Вход» live as a probe, or carry «фактически: живого прогона нет» for the
  operator to close, and never write the side from memory; a prod contour
  re-derives the same line from the step 8 run for the merge-to-main window). The executor's self-report «совпало» — in any
  form, including «all M examples matched» — is forbidden: the pair travels
  whole, the operator compares the two sides himself, and a discrepancy between
  them is closed only by the operator (fix the code, fix the Reel, or accept —
  his call, never the executor's). A ticket without a `## Reel` section carries
  the line «Reel: отсутствует» instead. A Reel-carrying ticket whose diff
  brought no test files carries the named line «лента без живых кейсов в
  диффе: tests-линза не стартовала» — lens routing is path-only (the
  operator's invariant), the gap is named here for the operator to close,
  not left silent. Never paste diff bodies into stop-points
  or confirmation windows: the operator reads diffs himself, when he considers
  it necessary (docs/ops/git-flow.md, «Режим»); show the diff only on his
  explicit request. The «фактически» side is a command's observed output, not a
  diff body — the ban covers source diffs, not live E2E output.
  **Default when the contract names nothing.**
- `stop-after-mr` — after step 7, stop for the operator's review.
- `no-deploy` — skip the deploy in step 9; the rolling-snapshot write still
  happens (it is not part of the deploy).

**Never skippable, with or without a Constraints block:** before merging to `main`
(step 9; step 7 in the light contour) and before any deploy, ask the operator — one
`AskUserQuestion` each, stating
what is about to land as facts (refs, hashes, counts; for a Reel ticket — its
latest «обещано → фактически» lines: the step 8 re-derivation when a prod
contour ran, the step 5 stop-point lines otherwise — a light contour merges at
step 7 before step 8, and a ticket with no contour never writes the side from
memory; no diff bodies, same rule as
`stop-before-commit`). A "continue" the operator typed earlier in this run covers the
stop-point it answered, not these two confirmations.

## Honest degradation

The three constant deviations of this solo flow — no MR, no separate prod contour,
remote may be absent — live in docs/ops/git-flow.md («Отступления-константы»);
reference that section in the shipping note with one line instead of re-declaring
them in every run. Every deviation beyond those constants is still written into the
shipping note — the one thing that may never happen silently.
