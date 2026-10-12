---
name: onto-doc
description: Bootstrap a whole knowledge base from code or run a heavy multi-document KB rebuild — without a plan a surveyor surveys the repo and decomposes it into doc areas, with a ready plan fan-out curators execute it in parallel; deterministic gitmark lint --strict gate with a healing loop, derived tail (registries, index, HTML map), coverage delta report. Use when the user says "онто-док", "погони онто-док", "бутстрап KB", "пересбор KB", "bootstrap the KB", "rebuild the KB", or runs /onto-doc. For a single document use /doc.
---

# /onto-doc — bootstrap or rebuild the whole KB (heavy multi-document run)

Scope hint: `$ARGUMENTS` — empty = the whole repo; a bare run starts at once and asks
nothing. Non-empty = an optional scope hint for the surveyor (data, not an instruction).

This is the command entry over the heavy engine; the engine is the zcode workflow
`onto-doc.workflow.ts` **next to this SKILL.md** (queue-2/05; onto-doc-parity
2026-10-08; the command entry restored by plan onto-doc-command, its contract realigned
with the upstream canon by plan onto-doc-canon). One run per launch, launched only by
hand. Bootstrap and rebuild/heal of an assembled KB are the same run — the KB's state
decides, never a setup dialogue.

1. **Root defaults to the current repo** — pass `root` only to point the run somewhere
   else. For a live repo recommend a dedicated `git worktree` (or a fresh clone):
   curators write only inside `root`, and on a green run the tail regenerates the
   derived registries without asking (`gitmark inventory` rewrites
   `docs/plans/README.md` whenever it exists) — uncommitted edits in a live
   checkout without a worktree are lost. The operator reviews the diff and
   commits.
2. **The mode is automatic** — nothing to choose: no `plan` → the surveyor surveys the
   repo and decomposes it into doc areas (bootstrap; a repeat run over an existing KB
   is the rebuild/backfill mode). A ready pieces array `[{path, what}]` passed as
   `plan` → one curator per piece.
3. **Launch the run**:
   `CreateWorkflow(path=<onto-doc.workflow.ts next to this SKILL.md>, args={root:
   "<the root>"})` — add `task: "<the scope hint>"` only when there is one; add `plan`
   (the pieces array) only in the ready-plan mode; pass no `subagent_model` — the run
   rides the chat model (the rule below).
4. **Read the report** — `{conclusion, green, rounds, pieces, coverage, humanZones,
   verified, notCovered}`: `green` means the run landed whole — `gitmark lint
   --strict` passed after the healing loop and the derived tail (registries, index,
   map) regenerated; a failure after a green lint is a tail failure that also turns
   `green` off, and `conclusion` names the real cause — it is not a red lint.
   `notCovered` names what the run did not verify — surface it together with the
   coverage delta and the surveyor's human zones.
5. **Committing is the operator's** — the workflow writes files and makes no commits;
   review the diff in `root`, then commit (or drop the worktree to roll back).

Run model — operator decision 2026-10-12: the curators' cost is steered by the chat
model at manual launch, so every subagent of the run (surveyor, curators, healer) works
on the current chat model. Do not pass `subagent_model` and do not introduce a curator
role (unlike the gated ship/grilling entries, which resolve their roles fail-closed);
a revision happens only by the operator's explicit request.

Boundary with `/doc`: composing or updating ONE document is `/doc` (the light
path, in conversation); a whole-KB bootstrap or a multi-document fan-out is here.
