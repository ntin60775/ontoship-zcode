---
node_type: index
title: Reference
service: _platform
status: active
updated: 2026-10-04
links:
  part_of: [../README.md]
  relates_to: [commands.md, memory.md]
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
