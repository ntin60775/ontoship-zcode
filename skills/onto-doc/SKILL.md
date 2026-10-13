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
3. **Launch through a fresh instantiation** — the engine file is a **template**:
   every subagent persona carries `model: "{{ROLE_MODEL:<role>}}"` placeholders, and
   the host rejects the placeholder ids, so the raw template is never launchable
   (fail-closed by design). The general contract is the roles skill's «Two bridges»
   (bridge №2); the mode-dependent procedure:
   - **Preflight** — bootstrap (no `plan`) resolves `curator` and `surveyor`; a ready
     `plan` resolves `curator` alone. Per role: `python3 <roles skill
     dir>/roles.py resolve --json --root <root>` — a role missing from the output is
     the same stop as a mismatch (fail-closed, roles skill) — then verify the role's
     `model$level` against **ListModels** (exists, not disabled, level available).
     Everything resolves before anything is instantiated.
   - **Instantiate** — copy the template into a **uniquely named** draft under
     `.zcode/workflow-drafts/` (one launch = one new instance; never reuse an old
     one — a stale instance silently carries another run's models), and replace each
     `{{ROLE_MODEL:<role>}}` placeholder with the resolved `model$level` as a string
     literal.
   - **Diff-preflight** — diff(instance, template) must be exactly those
     replacements: ≥ 1 placeholder in the template, 0 placeholders left in the
     instance, every inserted literal byte-equal to the resolve output. Anything
     else in the diff — stop and re-instantiate.
   - **Submit** — `CreateWorkflow(path=<the instance>, args={root: "<the root>"})`;
     add `task: "<the scope hint>"` only when there is one; add `plan` (the pieces
     array) only in the ready-plan mode.
4. **Read the report** — `{conclusion, green, rounds, pieces, coverage, humanZones,
   verified, notCovered}`: `green` means the run landed whole — `gitmark lint
   --strict` passed after the healing loop and the derived tail (registries, index,
   map) regenerated; a failure after a green lint is a tail failure that also turns
   `green` off, and `conclusion` names the real cause — it is not a red lint.
   `notCovered` names what the run did not verify — surface it together with the
   coverage delta and the surveyor's human zones.
5. **Committing is the operator's** — the workflow writes files and makes no commits;
   review the diff in `root`, then commit (or drop the worktree to roll back).

Run model — operator decision 2026-10-13, revising the 2026-10-12 chat-model decision
by its own trigger («a revision happens only by the operator's explicit request» —
that request came: per-subagent models became a host base with the October 2026
workflow facade, and roles are now the single contour of subagent LLMs). The surveyor
runs on the `surveyor` role, the fan-out curators and the healer on the `curator`
role (defaults today: surveyor GLM-5.3-Flash$max, curator GLM-5.3-Flash$high —
`tests/test_roles.py`); the run **never rides the chat model**, and there is no
fallback — everything resolves before launch. Steer the cost with `/roles set
curator|surveyor`, not with the chat model.

Boundary with `/doc`: composing or updating ONE document is `/doc` (the light
path, in conversation); a whole-KB bootstrap or a multi-document fan-out is here.
