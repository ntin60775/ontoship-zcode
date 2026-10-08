---
name: init
description: Initialize the OntoShip entry point in this project — create or update the managed block in AGENTS.md, add the .gitignore lines the KB requires, and seed the command registry docs/reference/commands.md when missing. Idempotent; touches nothing outside its own scope. Use when the user says "инициализируй ontoship", "setup ontoship", or runs /init.
---

# /init — bootstrap the project entry point

Run this once per project, right after the plugin is installed (marketplace or local).
It is **idempotent**: a second run changes nothing.

**Scope of the write.** The skill owns three things: the managed block in
`AGENTS.md`, the `.gitignore` lines, and the initial command registry
(created once, only when missing). In `AGENTS.md` everything it owns lives
between two markers:

```
<!-- BEGIN ontoship -->
<!-- END ontoship -->
```

Nothing outside the markers is ever touched, and the file is never rewritten
wholesale — there is no `--force` and no overwrite mode.

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

4. **Command registry** — `docs/reference/commands.md`, create only when missing:

   | Case | Action |
   |---|---|
   | file exists, both marker pairs present | do nothing; the registry is generated content — never rewrite it, never merge into it |
   | file exists, a marker pair missing | do not rewrite the file either — report `[WARN] docs/reference/commands.md существует без маркеров inventory — lint I7 останется красным, а gitmark inventory упадёт (exit 2): вставь недостающие пары BEGIN/END inventory:commands и inventory:skills из скелета ниже либо удали файл и повтори /init, затем прогони gitmark inventory` |
   | file missing | create it from the skeleton below (substitute `<today, YYYY-MM-DD>` with the run date), then fill the tables by running `python3 .zcode/skills/kb-search/gitmark.py inventory` from the project root — the step is done only when it prints `✓ inventory: …` |

   Without this file `gitmark lint --strict` fails with I7 «реестр не найден» on
   every future run — the skeleton plus the inventory run closes it for good.

5. **Report and hand over** — list what changed (file created / block appended / block
   updated / registry created / nothing to do), then tell the user the next step is building the KB:
   `/doc <topic>` per area — search first, never duplicate; the block points at
   `docs/README.md`.

## The block (verbatim)

```markdown
<!-- BEGIN ontoship -->
## Knowledge base (OntoShip)

- Entry point: [`docs/README.md`](docs/README.md) — the KB master index.
- Search before answering about this project: `/kb-search <query>`.
- New or updated docs: `/doc` — search first, never duplicate.
- Code changes go through `/ship`: one ticket (or one file plan) per run, launched by hand.
- The KB is markdown + git; `.gitmark/`, `*-map.html` and `.scratch/` are derived or ephemeral — never committed.
<!-- END ontoship -->
```

## The registry skeleton (verbatim)

```markdown
---
node_type: reference
title: Command registry
service: _platform
status: active
updated: <today, YYYY-MM-DD>
---

# Commands

Generated from the payload frontmatter by `gitmark inventory` and checked by
`gitmark lint` (I7). Do not edit the tables between the markers by hand.

<!-- BEGIN inventory:commands -->
<!-- END inventory:commands -->

<!-- BEGIN inventory:skills -->
<!-- END inventory:skills -->
```
