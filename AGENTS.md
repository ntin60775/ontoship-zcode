# OntoShip (zcode) — entry point

OntoShip is a **zcode plugin** — `skills/` (Agent Skills), `.zcode-plugin/plugin.json`
(manifest), hooks/agents as they land — shipping **GitMark** (an md+git knowledge base
with FTS5 search and an ontology linter) plus the spec-driven dev-flow and the
autonomous grilling built on top of it, on zcode-native primitives.

> Sister project: [ontoship-omp](https://github.com/vakovalskii/ontoship) — the same
> method for the omp agent. This repo shares only the GitMark engine (`gitmark.py`,
> vendored) and the ontology model; the method texts are rewritten for zcode
> (AskUserQuestion, plan approval gates, workflows, hooks, explicit subagent models).

## Where things live

```
.zcode-plugin/plugin.json   the plugin manifest (skills)
package.json                the package manifest (gitmark version reads it)
skills/
  kb-search/                the gitmark CLI engine (gitmark.py) + SKILL.md
docs/                       the knowledge base itself (this is the KB)
tests/                      engine tests (pytest, zcode layout)
AGENTS.md                   this entry point (read by zcode)
```

## Principle

Markdown + git is the source of truth. Everything derived — the search index
(`.gitmark/index.db`), the HTML graph — is regenerated, never committed as truth.
Every folder's `README.md` is its index; never let a doc become an orphan.
Search the KB before answering or writing a new doc.

## Maintain

```bash
python3 skills/kb-search/gitmark.py index    # rebuild the index after editing docs
python3 skills/kb-search/gitmark.py lint     # check the ontology (broken links, orphans, frontmatter)
python3 skills/kb-search/gitmark.py map -o docs-map.html   # regenerate the graph
python3 -m pytest tests/ -q                  # engine tests
```
