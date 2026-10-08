---
name: kb-search
description: Search a project's markdown knowledge base (docs/, README files, *.md) via the GitMark CLI — FTS5 ranking (bm25) plus trigram/fuzzy matching — instead of grepping across files. Use when you need to find where something is documented, "where do the docs say X", before reading files at random, or to generate an HTML overview/graph of the knowledge base. Handles substrings, typos, and non-Latin scripts.
---

# GitMark — knowledge-base search

This skill treats the repo's markdown as a **md + README(index) + git** knowledge base.
Markdown is the source of truth; the search index and HTML map are **derived** and
regenerated from md (`.gitmark/` is gitignored). The CLI is pure Python stdlib.

Script: `gitmark.py`, **next to this SKILL.md** — resolve it from this skill's directory
and run with an absolute path (the skill's own location works in any install: repo
checkout or marketplace plugin cache).

## When to use

- You need to find **where** something is documented → `gitmark search`, not a `grep`/`rg`
  fan-out. Results are `file:line · heading · snippet`.
- "How does X work here", "where are the docs for Y".
- Before reading files at random — locate the exact spots first.
- Want an overview/graph of the KB → `gitmark map`.

## Commands

```bash
python3 <this-skill-dir>/gitmark.py index                # (re)build .gitmark/index.db  (fast)
python3 <this-skill-dir>/gitmark.py search "<query>"     # bm25 + trigram(substring) + fuzzy(3-gram); -k N, --json
python3 <this-skill-dir>/gitmark.py map -o docs-map.html # self-contained HTML: tree + rendered md + radial graph
python3 <this-skill-dir>/gitmark.py serve -p 8799        # local http server to view the map
python3 <this-skill-dir>/gitmark.py stat                 # files/chunks/links/index state
python3 <this-skill-dir>/gitmark.py lint [paths…]        # ontology check (frontmatter/links/README/broken links/registries I7, index chain I10)
python3 <this-skill-dir>/gitmark.py inventory            # regenerate the registry tables (commands/skills → docs/reference/commands.md, plans → docs/plans/README.md)
python3 <this-skill-dir>/gitmark.py inventory --check    # exit 1 on registry desync (same as lint I7)
python3 <this-skill-dir>/gitmark.py version              # package version from its manifest
```

## Workflow

1. If the index may be stale (docs changed) → `gitmark index`.
2. `gitmark search "<terms>"` — typos and morphology are tolerated (trigram/fuzzy).
   `[bm25]` = exact term, `[trigram]` = substring, `[fuzzy]` = n-gram (typos/forms).
3. Open the returned `file:line` and read the exact place.
4. `--json` for machine-readable results.

## Principles

- **Markdown is the source of truth.** Edit knowledge in `.md`, never the index.
- **Don't commit `.gitmark/`** (it's in `.gitignore`).
- Index is a cache — if results look stale, rebuild with `gitmark index --force`.
