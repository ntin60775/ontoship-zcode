---
node_type: index
title: Reference
service: _platform
status: active
updated: 2026-10-08
links:
  part_of: [../README.md]
  relates_to: [commands.md, memory.md, workflow-args.md, dependencies.md, review-invariants.md]
---

# Reference

Cross-cutting specs — not about one service.

- [commands.md](commands.md) — the generated registry of skills and commands
  (regenerate with `gitmark inventory`; `gitmark lint` checks sync, I7).
- [roles.md](roles.md) — subagent model roles (reviewer, challenger): three-layer
  resolution, file format, fail-closed rule.
- [memory.md](memory.md) — the agent's persistent auto-memory: one fact per file,
  `MEMORY.md` as a thin one-line-per-memory index; what belongs in memory and
  what stays in the repo.
- [workflow-args.md](workflow-args.md) — args of CreateWorkflow are never
  truncated by the host; «не распарсились» means broken JSON at the caller, and
  workflow aborts must carry e.message + length + tail of the string.
- [dependencies.md](dependencies.md) — внешние зависимости плагина (сторонние
  решения и апстрим ontoship-omp): пин, канал обновления, владелец, деградация
  при мажоре, где ловится; контуры замены провайдера LLM и синка апстрима.
- [review-invariants.md](review-invariants.md) — инварианты слепого ревью
  гейт-прогонов (/ship, /code-review): у каждого — воркфлоу-механизм, который
  его держит; чек-лист нового рана, линзы или правки воркфлоу.
