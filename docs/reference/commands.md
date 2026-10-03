---
node_type: reference
title: Command registry
service: _platform
status: active
updated: 2026-10-03
links:
  part_of: [README.md]
---

# Commands

The single registry, generated from the payload frontmatter by
`gitmark inventory` and checked by `gitmark lint` (I7). Do not edit the tables
between the markers by hand.

## Summary

<!-- BEGIN inventory:commands -->
| Command | What it does | Args | Drives |
|---|---|---|---|
<!-- END inventory:commands -->

<!-- BEGIN inventory:skills -->
| Skill | What it does |
|---|---|
| `architecture` | Background architecture scan of a repo — a module/connection map cross-checked against the documented architecture (KB) for drift; drift findings confirmed independently by the shared ship confirm run. Runs by hand; the scan is a background workflow and never blocks the session. Use when the operator says "просканируй архитектуру", "architecture scan", "карта модулей", "найди дрейф с доками", or runs /architecture. |
| `code-review` | Two-axis code review of an arbitrary diff (correctness; quality & dangerous places) — findings confirmed independently against code quotes by the shared ship confirm run, one merged report with verified/unconfirmed verdicts. Runs only by hand through the workflow engine: review on the reviewer-role model, confirmation on the confirmer-role model. Use when the operator says "поревьюй дифф", "code review", "ревью ветки", or runs /code-review. |
| `diagnose` | Diagnose a hard bug or a strange question down to a minimal reproduction — build a tight red/green feedback loop, reproduce and minimise, test ranked falsifiable hypotheses, then report the root cause with evidence and do NOT fix it here (the fix goes through /grilling → /to-tickets → /ship, where the repro becomes the regression test). Artifacts live in .scratch/diagnose-<slug>/ where the continuation work finds them. Runs only when the operator says "диагностируй", "diagnose this", "почему ломается", "разберись с багом", or runs /diagnose. Never starts itself. |
| `doc` | Compose or update a knowledge-base document for a given topic following the OntoShip ontology (node_type, frontmatter, typed links, folder README index). Use when the user says "док", "задокументируй", "add a doc about X", "document X", or runs /doc. Searches first and edits the existing doc instead of duplicating. |
| `grilling` | Autonomous stress-test of a plan, decision, or idea — the agent resolves the solvable questions itself (each with evidence), a red-team challenger on its own model attacks the draft, and the operator gets one readable digest to approve. Interactive questions only where the answer cannot be derived. Ends with a plan contract (docs/plans/<slug>.md) approved via the native plan gate. Use when the user says "погрилл", "grill this", "прогони гриллинг", or runs /grilling. |
| `handoff` | Hand the session's context to the next one — write a per-session handoff file (.scratch/handoff-<id>.md with From, Task, Done, Decisions with evidence, Open, Next, Artifacts) without overwriting previous handoffs, and carry task-surviving facts into memory. Runs only when the operator says "передай смену", "handoff", or runs /handoff. Never starts itself. |
| `init` | Initialize the OntoShip entry point in this project — create or update the managed block in AGENTS.md and add the .gitignore lines the KB requires. Idempotent; touches nothing outside its own block. Use when the user says "инициализируй ontoship", "setup ontoship", or runs /init. |
| `kb-curate` | Rules for maintaining a markdown knowledge base (GitMark) — apply when adding, editing, moving, or deleting documentation (.md). A lightweight code-ontology: every document has a type, properties (frontmatter), and typed links. Keeps the KB structured instead of a pile of files. Use on "add a doc", "record a decision", "update the docs", "reorganize docs". |
| `kb-search` | Search a project's markdown knowledge base (docs/, README files, *.md) via the GitMark CLI — FTS5 ranking (bm25) plus trigram/fuzzy matching — instead of grepping across files. Use when you need to find where something is documented, "where do the docs say X", before reading files at random, or to generate an HTML overview/graph of the knowledge base. Handles substrings, typos, and non-Latin scripts. |
| `roles` | View and reassign the subagent model roles (reviewer, confirmer, challenger) across three layers — plugin default, user global, per-project. Use when the user runs /roles, says "поменяй модель ревьюера", "назначь модель для ролей", or asks which model reviews their ships. Shows the effective configuration with provenance and shadowing warnings. |
| `ship` | Ship ONE ticket through the gated dev-flow — worktree → implement → tests → independent review on an explicitly assigned model → dev/prod checks → merge, one ticket per run, strictly sequential, launched only by hand by the operator. Use when the operator runs /ship with a plan folder, a ticket path, a file plan, or an ad-hoc what+why+done. Never starts itself and is never started by another skill. |
| `to-tickets` | Break a plan (docs/plans/<slug>.md or docs/plans/<slug>/) into tracer-bullet tickets with blocking edges, carried down to indivisible units by granularity criteria before the operator sees them — published as docs/plans/<slug>/NN-<ticket>.md plus a README table. Use when the user says "разбей на тикеты" or runs /to-tickets. Runs only by hand; /ship consumes one ticket per run and is never started by this skill. |
<!-- END inventory:skills -->
