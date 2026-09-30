---
name: roles
description: View and reassign the subagent model roles (reviewer, challenger) across three layers — plugin default, user global, per-project. Use when the user runs /roles, says "поменяй модель ревьюера", "назначь модель для ролей", or asks which model reviews their ships. Shows the effective configuration with provenance and shadowing warnings.
---

# /roles — subagent model roles

A **role** names which model a subagent step runs on: `reviewer` (/ship step 6,
independent diff review) and `challenger` (grilling red team) by default. Resolution
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
4. If the user picks a change, go to `set` below.

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

## Fail-closed rule (applies everywhere a role is consumed)

Before running a subagent step on a role: `roles.py resolve --json`, take the role's
`model$level`, verify it against **ListModels** (exists, not disabled, level available).
Any mismatch → **stop the step** with a diagnostic naming the role, the expected id,
and the layer file to fix. **Never fall back to the session model** — the entire value
of an assigned role is that a different model does the step.
