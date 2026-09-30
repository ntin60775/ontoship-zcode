---
node_type: service
title: gitmark — the KB engine
service: kb-search
status: active
updated: 2026-09-30
tags: [service, cli, fts5, engine, search]
links:
  documents: [../../../skills/kb-search/gitmark.py]
  depends_on: [../../ontology.md, ../../reference/commands.md]
---

# gitmark — the KB engine

`gitmark.py` is the single **zero-dependency Python-stdlib CLI** at the heart of the
plugin: it treats the repo's markdown as a knowledge base (md + README index + git),
builds a **SQLite FTS5** search index from it, renders a self-contained HTML overview,
and lints the ontology. Everything derived is regenerated — `.gitmark/` is a build
artifact, never committed.

## Commands

| command | what |
|---|---|
| `index` | (re)build `.gitmark/index.db` — bm25 ∪ trigram ∪ fuzzy; `--force` rebuilds |
| `search "<q>"` | ranked `file:line · heading · snippet`; `-k N`, `--json` |
| `map -o <file>` | self-contained HTML: collapsible tree + rendered md + link graph |
| `serve -p <port>` | local HTTP server for the map |
| `stat` | index/KB statistics |
| `lint [paths]` | ontology invariants I1–I9 (frontmatter, links, orphans, registry) |
| `inventory [--check]` | regenerate the skill registry tables; `--check` exits 1 on drift (I7) |
| `version` | package version from the root `package.json` |

Invoked from skills as `python3 <kb-search-skill-dir>/gitmark.py <command>` — the path
resolves relative to the skill's own directory in any install.

## Search layers

`bm25` — exact terms · `trigram` — substrings and non-Latin text (SQLite ≥ 3.34,
auto-detected) · `fuzzy` — 4-char windows for typos and morphology. Good enough for
hundreds of docs with an agent as the consumer; a vector index beats it on semantic
recall — an accepted boundary, not a claim.

## Tests

`python3 -m pytest tests/ -q` — engine and roles suites (38 + 9), zcode layout.
