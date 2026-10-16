---
name: to-tickets
description: Break a plan (docs/plans/<slug>.md or docs/plans/<slug>/) into tracer-bullet tickets with blocking edges, carried down to indivisible units by granularity criteria before the operator sees them — published as docs/plans/<slug>/NN-<ticket-slug>.md plus a README table, and embedded into the global execution order (docs/plans/README.md «Порядок выполнения»). Launched by grilling right after the plan approval of a contract whose unit is built by more than one slice — the full run, steps 0–6, in the same session — or by hand on a plan that carries its provenance record in Context (a grill trace or the operator's explicit opt-out); a plan without the record is refused at entry by name, the breakdown does not start. Use when the user says "разбей на тикеты" or runs /to-tickets. /ship consumes one ticket per run and is never started by this skill.
---

# /to-tickets — break a plan into tickets

Break a plan into a set of **tickets**: tracer-bullet vertical
slices, each declaring the tickets that **block** it. A spec, a conversation, or
a bare topic is not an input: tickets come only from plans (operator rule,
flow-semantics), and shaping any of those into a plan is grilling's door
(«оформи план» / «триаж ишью» / /grilling) — route it there, never break it
down directly.

Two entry modes: **by hand** — the operator names the plan in the argument —
or **chained from grilling**: the same session that just got a contract
approved whose unit is built by more than one slice (the predicate is
defined in grilling step 7) runs this skill on it in full, with no manual
command in between (flow-continuity). The chain changes who starts the run,
nothing else — every step below runs the same way, and every run opens with
the step 0 provenance check.

Argument: `$ARGUMENTS` — a plan path (`docs/plans/<slug>.md`, `docs/plans/<slug>/`, or
its `README.md`). **Empty** → the most recent plan (a file
`docs/plans/<slug>.md` or a folder `docs/plans/<slug>/`, by `updated:`); the
grilling chain works on the contract it has just written, no argument needed.

## Process

### 0. Provenance check, then promote a file plan to a folder

**The provenance check is the run's first action — before any promotion.**
Read the plan's `Context` and find the provenance record (flow-semantics):
exactly one line of one of the two forms grilling step 7 writes — the grill
trace `Провенанс: грилл — dwfrun-<id>, YYYY-MM-DD`, or the operator's
explicit opt-out `Провенанс: opt-out оператора — отклонено: <пассы>`. No
such line — **refuse the plan by name and stop**: «отказ: нет записи
грилла/opt-out в Context — разбивка не начинается; провенанс-строку пишет
грилл (skills/grilling/SKILL.md, шаг 7)». Nothing is promoted, nothing is
drafted; the operator either runs the grill on the draft or records an
explicit opt-out. An artifact without the record is byte-identical to a
silently skipped grill — that is what this check refuses. The chained entry
passes by construction: the contract the same session has just grilled
carries its trace.

A plan is a **file** (`docs/plans/<slug>.md`) until this skill runs. If the target plan
is a file, first promote it to the folder form — the folder is created **only here**:

1. `mkdir docs/plans/<slug>/`, then move the plan file by its git state:
   **tracked** → `git mv docs/plans/<slug>.md docs/plans/<slug>/README.md`
   (preserves history); **untracked** → plain `mv` + `git add` — `git mv` on
   an untracked file dies rc=128 (live anti-precedent), and a contract this
   session has just written, chained straight from grilling, is exactly that
   file.
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

Read the plan contract (`Goal`, `Done`, `Scope`, `Constraints`, `Context`) and the `Context` it
points at. Read the plan's **quote carrier** — the `### Цитаты оператора (дословно)`
block in its `Context` (behavior-reel/01): every Reel `Цель` in the tickets below
quotes **only** this block, verbatim; a goal with no operator wording to quote is a
marked paraphrase. Search the KB (`gitmark search`) for related docs and decisions. If you
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
- **Every slice is a working state of the consumer's system** («каждый срез —
  рабочее состояние потребителя», flow-semantics): a slice lands green and
  leaves the consumer working — a staging step that breaks the system until a
  later slice arrives is not a slice. Intermediate slice releases are the
  normal delivery mechanics, not an exception to apologise for; the slice's
  criteria state what works for the consumer when it lands.
- Slices build the one unit (grilling step 7): «independently shippable» is
  the plan's property — the unit ships as a whole when its plan criteria
  are met — never a per-ticket demand. A slice belongs to its unit's
  contract; a ticket whose promise only makes sense together with another
  unit's work is an undeclared dependency (item 2 below).
- Each slice is sized to fit in a single fresh context window — one `/ship` run.
- Any prefactoring should be its own first ticket.
- Each ticket with observable behavior carries its **Reel** — the behavior examples
  the ticket promises («Цель → Вход → Наблюдаемый выход», minimum two: normal and
  edge/error; the section lands with the template in step 4). Draft it with the
  slice, not after the quiz.

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
8. **Post-publish edit:** an edit to a published ticket (a `/ship` run's
   drift mini-grill is the live case) keeps its number and its blocking edges
   — only the affected text changes, and every reference to the changed text
   (`depends_on`, the `Blocked by:` lines, the README table) is rewritten to
   match. A change that must renumber tickets or rewire edges is a
   post-publish split (item 6), not an edit.

Give each ticket its **blocking edges**: the other tickets that must complete before
it can start. A ticket with no blockers can start immediately.

### 2a. Counter-layer — the blind run before the quiz

Every run whose plan carries a contract runs the **counter-layer** over the
drafts BEFORE the quiz (operator decision 2026-10-13: the counter-layer is
mandatory on every run with a contract). Flow-semantics removed the
no-contract case: a spec, conversation, or topic no longer enters this skill
at all, and every plan that passes the step 0 check was authored by grilling
or carries the operator's recorded opt-out.

Assemble the run's three inputs — the masking is visible in the run's args:

- `tickets` — every draft's body **without** its `## Reel` section; each block
  opened by the marker line `=== ТИКЕТ NN: <title> ===`;
- `reels` — the `## Reel` sections of the same drafts, the same markers, the
  same `NN` set;
- `quotes` — the plan's quote carrier block (`### Цитаты оператора (дословно)`
  with its bullets), verbatim from the contract's `Context`.

Resolve the `challenger` role (`roles.py resolve --json`, roles skill) and
verify it against **ListModels**: a missing/disabled model or an absent level
stops the run with a diagnostic naming the role and the layer file to fix
(fail-closed — never run the counter-layer on your own model). Then launch:

`CreateWorkflow(path=skills/to-tickets/back-translation.workflow.ts, args={plan:
"<slug>", tickets: "<masked bodies>", reels: "<reel sections>", quotes:
"<carrier block>"}, subagent_model=<challenger role$level>)`

Act on the return:

- Named discrepancies of both classes (`restatement` — internal contradictions,
  `quote-mismatch` — formulation substitutions) are **fixed in the drafts**, not
  argued away; a fix that reshapes the breakdown goes back to step 2 drafting.
- The hostile cases ride into the quiz (step 3): the operator accepts a case —
  it joins that ticket's Reel as an example; rejects it — the case stays in the
  Reel by name («Отклонено оператором (контрслой): <case>»), so the decision
  survives into the published ticket. The workflow skips such lines when
  parsing goals — a rejected case is a record, not a promise.
- Zero findings arrive named «не найдено» — relay that naming to the operator;
  never paraphrase it as silence.

The paraphrase marker is the drafter's claim, not a verified fact: the machine
compares only the verbatim goals, names the paraphrase count in its output, and
flags a reel whose goals are all paraphrases while the carrier has quotes —
the quiz is where the operator holds that line.

Honest frame, fixed here and not in advertising: the restatization is a catcher
of internal contradictions, nothing more; with all roles on one model family
the interpretive substitution operator→ticket is machine-prefiltered **only**
by the character-level quote comparison — the full power of the counter-layer
arrives with a second model family in the role registry. The seeding probe
(lens-substrate-flash canon) certified this run once, at the shipping of
behavior-reel/03; a regular /to-tickets run does not repeat it.

### 3. Quiz the operator

Present the proposed breakdown as a numbered list. For each ticket, show:

- **Title**: short descriptive name
- **Blocked by**: which other tickets (if any) must complete first
- **What it delivers**: the end-to-end behaviour this ticket makes work
- **Reel**: every example «Цель → Вход → Наблюдаемый выход», normal and edge — the
  operator approves the behavior the ticket promises, not only its title; a `Цель`
  that is a paraphrase shows its marker here too
- **Hostile cases of the counter-layer** (step 2a): each proposed case is offered
  to the operator — accepted joins the Reel, rejected stays in it by name; a case
  the operator rejected is a recorded decision, not a dropped suggestion

Ask — one `AskUserQuestion`, then iterate until the operator approves the
breakdown. The operator may take a while to answer; that is not a decline and
is no reason to skip the quiz or proceed unilaterally:

- Does the granularity feel right? (too coarse / too fine — the criteria of step 2
  are already applied)
- Are the blocking edges correct: does each ticket only depend on tickets that
  genuinely gate it?
- Should any tickets be merged or split further?
- Do the Reel examples carry the promised behavior — each criterion's observable
  fact presentable as the triple, quotes verbatim where the carrier has them?

### 4. Publish the tickets

**Definition-of-done pass — before writing any file.** Walk the approved
breakdown ticket by ticket and state, in one sentence each, the observable
result (what works, from the user's perspective, when the ticket is done) and
the completion criterion (a fact a third party can verify without the author).
A result that cannot be stated as behaviour, or a criterion that names an
activity rather than an observable fact («add tests», «update docs»), means
the ticket is not finished being drafted — fix it now, while draft renumbering
is still free (step 2, item 5). For a criterion that names a test run, the
observable fact is the run's read log — first failure, counters, warnings —
not the launch itself: a green rc nobody read is still activity, not a fact. Step 2's granularity criteria size the unit;
this pass checks what its «done» says. A fix that reshapes the breakdown
(split, merge, rewired edges) goes back through the quiz (step 3) before any
file is written.

**Every criterion has an example.** The same pass walks each ticket's Reel:
every acceptance criterion is illustrated by at least one of the ticket's
examples. The class «не иллюстрируемо» does not exist — a criterion that
produced no example means the ticket is not finished being drafted: an
observable fact a third party can verify is presentable as
«Цель → Вход → Наблюдаемый выход» by definition (precedent: the redact matrix).
Rework the criterion — or the slice — until the example exists.

Write one file per ticket under the plan folder, numbered in dependency order
(blockers first): `docs/plans/<slug>/NN-<ticket-slug>.md`. A fresh folder numbers from
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

## Reel

The behavior this ticket promises, by example — the acceptance reference. Each
`Цель` is quoted **verbatim** from the plan's quote carrier block
(`### Цитаты оператора (дословно)` in its `Context`); a goal with no operator
wording to quote carries the visible marker `Цель (парафраз): …`. Minimum two
examples: the normal path and an edge/error path.

- Цель (дословно: «…») → Вход: … → Наблюдаемый выход: …
- Цель (дословно: «…») → Вход: … (краевой/ошибочный) → Наблюдаемый выход: …

Отклонённые случаи контрслоя: нет — или по строке «Отклонено оператором
(контрслой): <случай>» на каждый случай, отклонённый в шаге 2a (решение
оператора переживает публикацию).
```

**The Reel is detachable — masking of the counter-layer input.** The
counter-layer run (step 2a, behavior-reel/03) restores «what the system will
do» from ticket bodies it has not seen illustrated: its input is the draft
tickets **without the `## Reel` section**, while the reel itself and the quote
reference (the plan's quote carrier block) are fed as **separate inputs** —
visible in the run's args. Write every section so the removal is clean: no
criterion, promise, or dependency lives only inside the Reel; the
rejected-cases lines above are part of the Reel and travel with it.

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

### 6. Lint, reindex, commit the split

`gitmark.py lint` then `gitmark.py index`. Then commit the split as **one
piece**: the promoted contract (`README.md`), every ticket, the
execution-order change, and this session's crystallised terms
(`docs/decisions/`) land in a single commit — a multi-slice split leaves
nothing uncommitted. (The auto-chain never brings a single-slice contract
here — from `grilling` it stays written-but-uncommitted until its `/ship`, a
window kept on purpose, and that is why the nothing-uncommitted claim is
scoped to multi-slice splits. A manual run on any plan — single-slice
included — is a run like any other: it promotes, publishes, and commits by
the same one-piece rule.) Report the ticket list and **stop**. Do NOT launch
`/ship` — the operator starts it by hand, one ticket at a time.
