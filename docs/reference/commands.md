---
node_type: reference
title: Command registry
service: _platform
status: active
updated: 2026-09-30
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
| `doc` | Compose or update a knowledge-base document for a given topic following the OntoShip ontology (node_type, frontmatter, typed links, folder README index). Use when the user says "док", "задокументируй", "add a doc about X", "document X", or runs /doc. Searches first and edits the existing doc instead of duplicating. |
| `init` | Initialize the OntoShip entry point in this project — create or update the managed block in AGENTS.md and add the .gitignore lines the KB requires. Idempotent; touches nothing outside its own block. Use when the user says "инициализируй ontoship", "setup ontoship", or runs /init. |
| `kb-curate` | Rules for maintaining a markdown knowledge base (GitMark) — apply when adding, editing, moving, or deleting documentation (.md). A lightweight code-ontology: every document has a type, properties (frontmatter), and typed links. Keeps the KB structured instead of a pile of files. Use on "add a doc", "record a decision", "update the docs", "reorganize docs". |
| `kb-search` | Search a project's markdown knowledge base (docs/, README files, *.md) via the GitMark CLI — FTS5 ranking (bm25) plus trigram/fuzzy matching — instead of grepping across files. Use when you need to find where something is documented, "where do the docs say X", before reading files at random, or to generate an HTML overview/graph of the knowledge base. Handles substrings, typos, and non-Latin scripts. |
| `roles` | View and reassign the subagent model roles (reviewer, challenger) across three layers — plugin default, user global, per-project. Use when the user runs /roles, says "поменяй модель ревьюера", "назначь модель для ролей", or asks which model reviews their ships. Shows the effective configuration with provenance and shadowing warnings. |
<!-- END inventory:skills -->
