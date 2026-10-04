---
name: to-tickets
description: Break a plan (docs/plans/<slug>.md or docs/plans/<slug>/) into tracer-bullet tickets with blocking edges, carried down to indivisible units by granularity criteria before the operator sees them — published as docs/plans/<slug>/NN-<ticket>.md plus a README table, and embedded into the global execution order (docs/plans/README.md «Порядок выполнения»). Use when the user says "разбей на тикеты" or runs /to-tickets. Runs only by hand; /ship consumes one ticket per run and is never started by this skill.
---

# /to-tickets — break a plan into tickets

Break a plan, spec, or conversation into a set of **tickets**: tracer-bullet vertical
slices, each declaring the tickets that **block** it.

Argument: `$ARGUMENTS` — a plan path (`docs/plans/<slug>.md`, `docs/plans/<slug>/`, or
its `README.md`) or a topic. **Empty** → the most recent plan (a file
`docs/plans/<slug>.md` or a folder `docs/plans/<slug>/`, by `updated:`).

## Process

### 0. Promote a file plan to a folder

A plan is a **file** (`docs/plans/<slug>.md`) until this skill runs. If the target plan
is a file, first promote it to the folder form — the folder is created **only here**:

1. `mkdir docs/plans/<slug>/` and `git mv docs/plans/<slug>.md docs/plans/<slug>/README.md`
   (preserves history).
2. **Rewrite the plan's own outgoing links**: it moved one level deeper —
   relative `.md` links in its frontmatter and body gain one `../` (e.g.
   `../ontology.md` → `../../ontology.md`). Anchor-only links (`#section`)
   stay as they are; a `file.md#anchor` link changes only the file part.
3. **Rewrite incoming links** from other docs that pointed at `docs/plans/<slug>.md`
   (grep the KB for `` `<slug>.md` `` with a word boundary, so `other-<slug>.md`
   does not match) — they now point at `docs/plans/<slug>/README.md`.
4. Add a line to `docs/plans/README.md`'s index for the plan folder.

If the target is already a folder, skip this step.

### 1. Gather context

Read the plan contract (`Goal`, `Done`, `Scope`, `Context`) and the `Context` it
points at. Search the KB (`gitmark search`) for related docs and decisions. If you
have not explored the codebase, do so to understand the current state. Ticket titles
and descriptions use the project's vocabulary and respect the decisions in
`docs/decisions/`.

Look for opportunities to prefactor the code to make the implementation easier. "Make
the change easy, then make the easy change."

### 2. Draft vertical slices — down to the indivisible unit

Break the work into **tracer bullet** tickets.

- Each slice cuts a narrow but COMPLETE path through every layer (schema, API, UI,
  tests): vertical, NOT a horizontal slice of one layer.
- A completed slice is demoable or verifiable on its own.
- Each slice is sized to fit in a single fresh context window — one `/ship` run.
- Any prefactoring should be its own first ticket.

**Granularity criteria — apply while drafting, not after.** The operator quiz (step 3)
stays, but by the time it runs "too coarse" means these criteria were not carried to
the end:

1. **Unit:** one verifiable capability with its own acceptance proof (a test or
   another observable fact). Fix the draft until every ticket is exactly that.
2. **SPLIT a draft ticket when:**
   - it makes two or more independent promises;
   - its acceptance requires mechanics **not declared** in `depends_on` — an
     undeclared dependency, the ticket builds something only verifiable together
     with a neighbor's work;
   - it is not verifiable without neighbors built first and that dependency is not
     consciously fixed in `Blocked by`.
3. **MERGE a draft ticket into its neighbor when** it delivers nothing new beyond
   the neighbor.
4. **Exception — wide refactor:** one mechanical change whose blast radius fans
   across the codebase (rename a column, retype a shared symbol) is a unit by
   definition; the criteria do not apply to it. No vertical slice can land green, so
   sequence it expand–contract: expand (add the new form beside the old), migrate
   call sites in batches sized by blast radius (each batch its own ticket, blocked
   by the expand), contract (delete the old form, blocked by every batch).
5. **Pre-publish split:** an indivisibility violation found while drafting (before
   step 4) is fixed by re-drafting — renumber the drafts freely, there is no file
   or history yet.
6. **Post-publish split:** after publication, splitting means `git mv` (keeps
   history), renumbering the successor files, and rewriting every reference —
   `depends_on`, the `Blocked by:` lines, the README table, the neighboring
   tickets' texts; grep the plan folder for the old numbers — it must return
   nothing.
7. **Dependency check:** the edges form a DAG with no cycles — A never appears in
   its own `depends_on`, and no path A → B → … → A exists (check transitively).
   The three places that fix an edge must agree: frontmatter `links.depends_on`,
   the `Blocked by:` line in the ticket body, the `Blocked by` column of the plan's
   README table.

Give each ticket its **blocking edges**: the other tickets that must complete before
it can start. A ticket with no blockers can start immediately.

### 3. Quiz the operator

Present the proposed breakdown as a numbered list. For each ticket, show:

- **Title**: short descriptive name
- **Blocked by**: which other tickets (if any) must complete first
- **What it delivers**: the end-to-end behaviour this ticket makes work

Ask — one `AskUserQuestion`, then iterate until the operator approves the
breakdown. The operator may take a while to answer; that is not a decline and
is no reason to skip the quiz or proceed unilaterally:

- Does the granularity feel right? (too coarse / too fine — the criteria of step 2
  are already applied)
- Are the blocking edges correct: does each ticket only depend on tickets that
  genuinely gate it?
- Should any tickets be merged or split further?

### 4. Publish the tickets

Write one file per ticket under the plan folder, numbered in dependency order
(blockers first): `docs/plans/<slug>/NN-<slug>.md`. A fresh folder numbers from
`01`; a folder that already has tickets continues from `max(NN)+1` — never restart
the numbering (a duplicated `NN-` prefix is exactly what `gitmark lint` does not
catch). One ticket per file, never a single combined file.

Template:

```markdown
---
node_type: ticket
title: <Ticket title>
service: _platform
status: draft
updated: YYYY-MM-DD
links:
  part_of: [README.md]
  depends_on: [01-<blocker>.md]   # only if blocked by another ticket
---

# NN: <Ticket title>

**What to build:** the end-to-end behaviour this ticket makes work, from the user's
perspective, not a layer-by-layer implementation list.

**Blocked by:** the numbers/titles of the tickets that gate this one, or "None (can
start immediately)".

- [ ] Acceptance criterion 1
- [ ] Acceptance criterion 2
```

Then update the plan's `README.md` (the parent contract — the migrated file, or the
existing folder README): a **table** (not a prose listing) with columns `#`, `Title`,
`Status`, `Blocked by`, one row per ticket in numbering order; set the plan's
`status: active` only if the operator confirms shipping has started (otherwise leave
`draft`).

Avoid specific file paths or code snippets in tickets: they go stale fast. Exception:
if a prototype produced a snippet that encodes a decision more precisely than prose
can (state machine, reducer, schema, type shape), inline it and note briefly that it
came from a prototype. Trim to the decision-rich parts, not a working demo.

### 5. Embed into the execution order

Publishing a plan is not the last word on sequencing: every `/to-tickets` run
ends with the plan **embedded in the global execution order** — the
«Порядок выполнения» section of `docs/plans/README.md`. Never leave the
slotting to the operator and never assume the order is obvious: this section
is the only place cross-plan order is written down.

- Add (or update) the plan's numbered entry with the rationale for its
  position: shared files with neighboring plans (one release-cycle churn),
  cross-plan blockers, and «first/last» constraints declared in plans'
  `Constraints`.
- Reconcile both levels: the plan's internal order (its NN and blocked-by
  edges) and its global position among the other plans. If a neighbor edits
  the same files, say explicitly who goes first and why.
- While editing the section, catch stale neighbor entries (shipped remains,
  renumbered tickets) — an index that lies about the remainder is worse than
  none.

The index is a doc like any other: the order change is part of this run's
commit, not a follow-up.

### 6. Lint + reindex

`gitmark.py lint` then `gitmark.py index`. Report the ticket list and **stop**. Do
NOT launch `/ship` — the operator starts it by hand, one ticket at a time.
