---
name: roles
description: View and reassign the subagent model roles (reviewer, confirmer, challenger, curator, surveyor, fallback) across three layers — plugin default, user global, per-project. Use when the user runs /roles, says "поменяй модель ревьюера", "назначь модель для ролей", or asks which model reviews their ships. Shows the effective configuration with provenance and shadowing warnings.
---

# /roles — subagent model roles

A **role** names which model a subagent step runs on: `reviewer` (/ship step 6,
independent diff review), `confirmer` (/ship step 6, second run — confirms the
reviewer's findings), `challenger` (grilling red team), `curator` and `surveyor`
(onto-doc run — fan-out curators with the lint healer, and the bootstrap
surveyor; bridge 2 below). The plugin
also ships `fallback` — a service constant holding the restart model for a run that
died for a model reason; it is never a step's model (see the dashboard note
below). Resolution
is three layers, most specific wins, **merged per role name** (a project `reviewer`
does not hide a user `challenger`):

```
<plugin>/defaults/roles.md  →  ~/.zcode/ontoship/roles.md  →  <repo>/.zcode/ontoship/roles.md
```

The resolver script is `roles.py`, **next to this SKILL.md**. This skill is the UI;
the script does file work; zcode tools do verification.

## Verbs

### `/roles` (no arguments) — dashboard

1. `python3 <this-skill-dir>/roles.py resolve --root <project-root>` — effective
   roles with provenance (which layer, which file).
2. Call **ListModels** — the host's available models with their `reasoningLevels`.
3. Print a dashboard: per role, the effective `model$level` and its source; **⚠ mark
   any role that comes from the project layer** (it shadows the user's global choice —
   offer `/roles unset <role>` right on that line); then the ListModels list as "what
   you can switch to".
4. The `fallback` role, when present, gets its own line with the note
   **«константа фолбэка, потребителям не назначается»** — it holds the restart
   model for a dead run; it is never a step's model, so never suggest it as one.
5. If the user picks a change, go to `set` below.

### `/roles set <role> <model>[$level]` — assign (writes the USER layer by default)

1. Validate `<model>[$level]` against **ListModels**: exact id exists, not `disabled`,
   and `$level` is in that model's `reasoningLevels` (a bare `<model>` is fine — the
   model's default level applies). Unknown model/level → stop with the ListModels
   rows that almost matched; write nothing.
2. `python3 <this-skill-dir>/roles.py set <role> <model>[$level]` — writes
   `~/.zcode/ontoship/roles.md` (all projects). Only an explicit **`--project`**
   (or the user choosing "only this repo") writes
   `<repo>/.zcode/ontoship/roles.md` — the project layer must never appear by accident.
3. **Smoke** the new assignment: run a micro-workflow on it — `CreateWorkflow` with a
   one-trivial-step script and `subagent_model` set to the resolved value. It must
   complete; a failure means the model is not actually usable on this host — report,
   and suggest reverting (`roles.py set` back).

### `/roles unset <role>` — remove the project override

`python3 <this-skill-dir>/roles.py unset <role>` removes the role from the project
layer (the value falls back to the user layer or plugin default). `--user` targets the
user layer instead. Confirm before unsetting a user-layer role — that reverts every
project to the plugin default.

### `/roles help` (and any unrecognized input) — help

Print the layers, the verbs with one example each, and where the roles are used
(read the role list from `defaults/roles.md` — do not hardcode it here). End with the
fail-closed rule below, verbatim.

## Two bridges role→model (roles-per-agent/01)

Roles are the only contour for subagent LLMs: a run never reads the session
model and a workflow file never hardcodes model ids. Getting a role's model
into a run has exactly two bridges, because the host compiler accepts a
subagent's `model` only when it is known before the run starts — «A subagent's
`model` must be known before the run starts: a string literal, a union of
string literals, or a ModelRef from model("…")»; a string built from args is
rejected, so a role cannot flow into a persona at runtime (live compiler
probe, 2026-10-13).

**Bridge 1 — single-role run.** The whole run sits on one role. Resolve the
role (`roles.py resolve --json`) and verify it against ListModels, then
`CreateWorkflow(path=<workflow>, …, subagent_model=<model$level>)` — the host
validates it at submit. Gate pattern: ship step 6 runs the review on
`reviewer` and the confirm on `confirmer` this way. An exception recorded
here: the confirm run also has an internal summarizer agent (`synthesizer`)
that stays on the run's confirmer model — not a role, operator decision
2026-10-13.

**Bridge 2 — multi-role engine template.** A workflow whose subagents carry
several different roles ships as a **template**: every role-bearing `agent()`
call holds `model: "{{ROLE_MODEL:<role>}}"` as a placeholder. The launching
skill instantiates it:

1. **Preflight.** Resolve **every role whose placeholder the template
   carries** — the placeholders are unconditional text in the template file,
   so a mode that will not *run* some agent still needs its literal for the
   instance (onto-doc: `curator` + `surveyor` in every launch; in the
   ready-plan mode the `if (bootstrap)` guard keeps the surveyor agent from
   running). Per role: `roles.py resolve --json`; a role missing
   from the output is the same stop as a mismatch (fail-closed rule below);
   then verify `model$level` against ListModels (exists, not disabled, level
   available). Everything resolves before anything is instantiated — «всё
   известно заранее».
2. **Instantiate.** Copy the template into a **uniquely named** draft under
   `.zcode/workflow-drafts/` — one launch = one new instance; reusing an old
   instance is forbidden: a stale instance silently carries the models of the
   run that created it (precedent: a dead reviewer-15 draft has sat in the
   directory since 2026-10-04). Replace each `{{ROLE_MODEL:<role>}}`
   placeholder with the resolved `model$level` as a **string literal** — not
   the `model("…")` form, which breaks the text-level mock tests; a plain
   literal keeps the instance diffable.
3. **Diff-preflight.** diff(instance, template) must be **exactly** the
   placeholder replacements: ≥ 1 placeholder in the template, 0 placeholders
   left in the instance, every inserted literal byte-equal to the resolve
   output. A diff showing anything else — stop, re-instantiate.
4. **Launch.** `CreateWorkflow(path=<instance>)`. Do not delete the instance
   after submit — AmendWorkflow holds its scriptPath.

## Fail-closed rule (applies everywhere a role is consumed)

Before running a subagent step on a role: `roles.py resolve --json`, take the role's
`model$level`, verify it against **ListModels** (exists, not disabled, level available).
Any mismatch → **stop the step** with a diagnostic naming the role, the expected id,
and the layer file to fix. A role **missing from the `resolve --json` output
entirely is the same stop with the same diagnostic** — a typo in a role name
must fail loudly, never silently resolve to some implicit default model.
**Never fall back to the session model** — the entire value
of an assigned role is that a different model does the step.

The diagnostic must name the fix **with its layer**: read the role's `_source` first.
A project-layer id stops resolving on a foreign host, and a plain `/roles set` writes
the user layer — which the project layer shadows, so the fix silently does nothing.
Correct guidance: `/roles unset <role>` (drop the stale project override) or
`/roles set <role> <model>$<level> --project` (re-pin the project deliberately).
Prefer an explicit `$level` in every set — a bare model replaces the whole role record,
silently dropping any level inherited from a lower layer. In `defaults/roles.md`
every record carries an explicit `level` (pinned by `tests/test_roles.py`); a new
role without specific needs is added as `GLM-5.3-Flash` with `level: max`.
