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
| `kb-search` | Search a project's markdown knowledge base (docs/, README files, *.md) via the GitMark CLI — FTS5 ranking (bm25) plus trigram/fuzzy matching — instead of grepping across files. Use when you need to find where something is documented, "where do the docs say X", before reading files at random, or to generate an HTML overview/graph of the knowledge base. Handles substrings, typos, and non-Latin scripts. |
<!-- END inventory:skills -->
