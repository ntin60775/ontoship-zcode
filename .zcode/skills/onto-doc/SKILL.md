---
name: onto-doc
description: Bootstrap a whole knowledge base from code or run a heavy multi-document KB rebuild — without a plan a surveyor surveys the repo and decomposes it into doc areas, with a ready plan fan-out curators execute it in parallel; deterministic gitmark lint --strict gate with a healing loop, derived tail (registries, index, HTML map), coverage delta report. Use when the user says "онто-док", "погони онто-док", "бутстрап KB", "пересбор KB", "bootstrap the KB", "rebuild the KB", or runs /onto-doc. For a single document use /doc.
---

# /onto-doc — bootstrap or rebuild the whole KB (heavy multi-document run)

Task: `$ARGUMENTS` — what the KB covers (bootstrap) or what to rebuild and why.
If empty, ask for the task.

This is the command entry over the heavy engine; the engine is the zcode workflow
`onto-doc.workflow.ts` **next to this SKILL.md** (queue-2/05; onto-doc-parity
2026-10-08; the command entry restored by plan onto-doc-command). One run per
launch, launched only by hand.

1. **Pick the `root`** — the KB project's root. For a live repo pass a dedicated
   `git worktree` (or a fresh clone): curators write only inside `root`, the main
   checkout stays untouched; the operator reviews the diff and commits.
2. **Choose the mode.**
   - **Bootstrap / rebuild (default)** — do not pass `plan`: the surveyor surveys
     the repo and decomposes it into doc areas itself (steps 1–2 of the upstream
     canon; repeat runs over an existing KB are the rebuild/backfill mode).
   - **Ready edit plan** — a pieces array `[{path, what}]`, one curator per piece:
     pass it as `plan` (JSON array in the workflow args).
3. **Launch the run**:
   `CreateWorkflow(path=<onto-doc.workflow.ts next to this SKILL.md>, args={task:
   "<the task>", root: "<the root>"})` — add `plan` only in the ready-plan mode.
4. **Read the report** — `{conclusion, green, rounds, pieces, coverage,
   humanZones, verified, notCovered}`: `green` means `gitmark lint --strict` passed after the healing
   loop; `notCovered` names what the run did not verify — surface it together
   with the coverage delta and the surveyor's human zones.
5. **Committing is the operator's** — the workflow writes files and makes no
   commits; review the diff in `root`, then commit (or drop the worktree to roll
   back).

Boundary with `/doc`: composing or updating ONE document is `/doc` (the light
path, in conversation); a whole-KB bootstrap or a multi-document fan-out is here.
