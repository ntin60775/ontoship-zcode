---
name: init
description: Initialize the OntoShip entry point in this project — create or update the managed block in AGENTS.md and add the .gitignore lines the KB requires. Idempotent; touches nothing outside its own block. Use when the user says "инициализируй ontoship", "setup ontoship", or runs /init.
---

# /init — bootstrap the project entry point

Run this once per project, right after the plugin is installed (marketplace or local).
It is **idempotent**: a second run changes nothing.

**Scope of the write.** Everything this skill owns lives between two markers in
`AGENTS.md`:

```
<!-- BEGIN ontoship -->
<!-- END ontoship -->
```

Nothing outside the markers is ever touched, and the file is never rewritten wholesale —
there is no `--force` and no overwrite mode.

## Steps

1. **Locate the project root** — `git rev-parse --show-toplevel` (fall back to the current
   directory).

2. **Manage the block in `AGENTS.md`** — exactly one of five cases:

   | Case | Action |
   |---|---|
   | `AGENTS.md` missing | create it with an H1 (`# <project-dir-name> — entry point`) and the block below |
   | file exists, no markers | append a blank line and the block at the end; every existing line stays |
   | both markers, block identical to the template | do nothing; report `блок OntoShip уже актуален` |
   | both markers, block differs | replace **only** what is between them, then print `[WARN] блок OntoShip обновлён — правки внутри блока не сохраняются, проектные правки вносите вне маркеров` |
   | one marker only, or markers out of order | change nothing, print `[FAIL] в AGENTS.md непарные маркеры OntoShip — правка не выполнена`, stop |

3. **`.gitignore`** — ensure these three lines exist, appending only the missing ones:
   `.gitmark/`, `*-map.html`, `.scratch/`.

4. **Report and hand over** — list what changed (file created / block appended / block
   updated / nothing to do), then tell the user the next step is building the KB:
   `/ontoship:doc <topic>` per area (with a local/workspace install: `/doc`) — search
   first, never duplicate; the block points at `docs/README.md`.

## The block (verbatim)

```markdown
<!-- BEGIN ontoship -->
## Knowledge base (OntoShip)

Skill names below use the plugin prefix; with a workspace install use the short form (`/kb-search`, …).

- Entry point: [`docs/README.md`](docs/README.md) — the KB master index.
- Search before answering about this project: `/ontoship:kb-search <query>`.
- New or updated docs: `/ontoship:doc` — search first, never duplicate.
- Code changes go through `/ontoship:ship`: one ticket (or one file plan) per run, launched by hand.
- The KB is markdown + git; `.gitmark/`, `*-map.html` and `.scratch/` are derived or ephemeral — never committed.
<!-- END ontoship -->
```
