---
name: doc
description: Compose or update a knowledge-base document for a given topic following the OntoShip ontology (node_type, frontmatter, typed links, folder README index). Use when the user says "док", "задокументируй", "add a doc about X", "document X", or runs /doc. Searches first and edits the existing doc instead of duplicating.
---

# /doc — compose or update ONE KB document

Topic: `$ARGUMENTS` — the thing to document. If empty, ask for the topic.

Follow the `kb-curate` skill (ontology over code); the engine is `gitmark.py` in the
`kb-search` skill directory:

1. **Search first** — `python3 <kb-search-skill-dir>/gitmark.py search "$ARGUMENTS"`.
   If the topic already exists → **edit that doc**, don't create a second one.
2. **Pick a `node_type`** — `service` · `reference` · `runbook` · `gotcha` · `decision` ·
   `plan` · `guide` · `report` · `index` (unsure → spec = `reference`, how-to = `guide`).
   Ephemeral output (diagnoses, reviews, handoffs) goes to `.scratch/` — no `node_type`.
   And the **right folder** (service → `docs/services/<svc>/`, cross-cutting → `docs/reference/`,
   ops → `docs/ops/`, plan → `docs/plans/`, decision → `docs/decisions/`).
3. **Write frontmatter** — `node_type`, `title`, `service`, `status: active`, `updated: <today>`.
4. **Add ≥1 typed link** — to code (`documents`/`implemented_by`) or a sibling doc
   (`depends_on`/`relates_to`). No orphans.
5. **Add a line to the folder `README.md`** (its index): `- [Title](file.md) — hook`.
6. **Lint + reindex** — `gitmark.py lint`, then `gitmark.py index`.

Report which file you created/updated, its `node_type`, and the links you added.
