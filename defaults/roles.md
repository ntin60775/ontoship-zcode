---
roles:
  reviewer:
    model: account:zai-individual-coding-plan/GLM-5.3-Flash
    level: max
  challenger:
    model: account:zai-individual-coding-plan/GLM-5.3-Flash
    level: max
---

# Plugin-default subagent model roles

The **least specific layer**: a user overrides these for all projects in
`~/.zcode/ontoship/roles.md`, a project for itself in
`<repo>/.zcode/ontoship/roles.md` — same format. Resolution is per role name
(most specific layer that defines the role wins). Edit via `/roles set`, not by hand.

- `reviewer` — /ship step 6: independent read-only review of the ticket diff.
- `challenger` — grilling: red team over the draft decisions.

These ids are the author's host plan (Z.AI individual coding plan). On another host
they may not resolve — the consuming skill must verify against ListModels and stop
with a diagnostic if the model is unavailable (fail-closed, never fall back to the
session model).
