---
node_type: ticket
title: handoff — ReadSessionContext + .scratch/
service: _platform
status: draft
updated: 2026-10-01
links:
  part_of: [README.md]
---

# 08: handoff — ReadSessionContext + `.scratch/`

**What to build:** сессия передаёт контекст следующей: handoff-процедура
записывает решения и незакрытое в `.scratch/` и даёт новой сессии
ReadSessionContext-подсказку, чтобы продолжение не теряло решения и не
начинало с нуля.

**Blocked by:** None (can start immediately).

- [ ] handoff-скилл/процедура записывает контекст в `.scratch/` (что класть,
      когда чистить — оговорено)
- [ ] новая сессия по ReadSessionContext продолжает работу без потерянных
      решений (проверено реальной передачей)
- [ ] `gitmark lint` + `pytest` зелёные
