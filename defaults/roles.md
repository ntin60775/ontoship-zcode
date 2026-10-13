---
roles:
  reviewer:
    model: account:zai-individual-coding-plan/GLM-5.3-Flash
    level: max
  confirmer:
    model: account:zai-individual-coding-plan/GLM-5.3-Flash
    level: high
  challenger:
    model: account:zai-individual-coding-plan/GLM-5.3-Flash
    level: max
  curator:
    model: account:zai-individual-coding-plan/GLM-5.3-Flash
    level: high
  surveyor:
    model: account:zai-individual-coding-plan/GLM-5.3-Flash
    level: max
  fallback:
    model: account:zai-individual-coding-plan/GLM-5.3-Flash
    level: max
---

# Plugin-default subagent model roles

The **least specific layer**: a user overrides these for all projects in
`~/.zcode/ontoship/roles.md`, a project for itself in
`<repo>/.zcode/ontoship/roles.md` — same format. Resolution is per role name
(most specific layer that defines the role wins). Edit via `/roles set`, not by hand.

- `reviewer` — /ship step 6, first run: independent read-only review of the
  ticket diff; ends with raw findings.
- `confirmer` — /ship step 6, second run: confirms the reviewer's findings with
  fresh eyes (read-only) and merges the verdicts into one report; deliberately
  a lighter configuration than the reviewer (`high` reasoning level vs the
  reviewer's `max` on the author's host — if the level is missing there, the
  gate stops, fail-closed). Operator decision, ticket 14.
- `challenger` — grilling: red team over the draft decisions.
- `curator` — onto-doc fan-out (skills/onto-doc): one curator per plan piece
  plus the lint healer; deliberately `high`, not `max` — the run buys many
  parallel curators, the lighter level keeps the fan-out affordable (operator
  decision, 2026-10-13).
- `surveyor` — onto-doc bootstrap (skills/onto-doc): surveys the repo into
  plan pieces before the fan-out. Named `surveyor`, not `synthesizer`: the
  gate's confirm run already has an agent named `synthesizer`
  (skills/ship/confirm.workflow.ts), and a role colliding with it would
  confuse the /roles dashboard.

`curator` and `surveyor` are the **target** assignments of the onto-doc run:
the wiring itself ships in roles-per-agent/02. Until that ticket lands,
onto-doc's own skill keeps the run on the chat model and forbids role wiring
(its 2026-10-12 decision, still in force).

**Record rule** (roles-per-agent/01): a new role without specific needs is
added as `GLM-5.3-Flash` with an explicit `level: max` — never level-less;
every record here carries its level, and a missing level line reddens the
suite (`tests/test_roles.py`). Named exceptions, each with its reason:
`confirmer` — `high` (ticket 14), `curator` — `high` (operator decision,
2026-10-13). The gate's summarizer agent (the `synthesizer` inside the confirm
run, three gate skills) is not a role and stays on the confirmer's model —
operator decision, 2026-10-13; migrating the gates onto the multi-role bridge
is a separate future ticket.

`fallback` is a service constant, not a step assignment: the designated holder
of the restart model for a run that died for a model reason (provider-stop,
repeated ContextLimit that ends the run). No workflow script reads it as its model —
the restart lives at the calling-skill level: one clean rerun with a loud
degradation note (ship step 6, grilling — roles-fallback-substrate/02,
2026-10-11). Layers work as for any other role: user/project may override it.

These ids are the author's host plan (Z.AI individual coding plan). On another host
they will not resolve — by design the consuming skill then stops with a diagnostic
(fail-closed, never falls back to the session model — not to be confused with the
`fallback` role above: fail-closed answers an id that never resolved on this host,
while the `fallback` role answers a run whose assigned model resolved but died at
runtime). Follow the diagnostic's
layer-aware guidance (roles skill, fail-closed rule): a bare `/roles set` writes the
user layer and is a no-op whenever a project layer pins the role.
