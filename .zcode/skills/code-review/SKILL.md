---
name: code-review
description: Two-axis code review of an arbitrary diff (correctness; quality & dangerous places) — findings confirmed independently against code quotes by the shared ship confirm run, one merged report with verified/unconfirmed verdicts. Runs only by hand through the workflow engine: review on the reviewer-role model, confirmation on the confirmer-role model. Use when the operator says "поревьюй дифф", "code review", "ревью ветки", or runs /code-review.
---

# /code-review — two-axis review of a diff

The engine is the review workflow **next to this SKILL.md** plus the shared
confirm run `../ship/confirm.workflow.ts`; this file is the hand-launched
entry point — the same two-run shape as `/ship` step 6. One confirmer
machinery for both gates, no split-brain (ticket 14/02); the operator still
launches `/code-review` once and gets the same merged report.

1. **Resolve both models first** — `roles.py resolve --json` for the `reviewer`
   AND the `confirmer` role, verify each against ListModels (same fail-closed
   gate as `/ship` step 6). Missing or disabled model, absent level → stop and
   name the role and the layer file to fix; never fall back to the session
   model.
2. **Run the review** — `CreateWorkflow(path=<this SKILL
   dir>/code-review.workflow.ts, args={base: "<ref>", root: "<checkout dir>",
   scope?: "<pathspec>"}, subagent_model=<reviewer role$level>)`. `root` is
   what makes the review work in a worktree — point it at the checkout whose
   diff you mean; `base` is the ref the diff is measured from (`main`,
   `HEAD~1`). The split is always per file — one axis agent per changed file,
   each bounded by that file's diff (files over 2000 diff lines and diffs over
   20 files are skipped with an honest note) — so small-context models hold
   every ask. The run ends with raw findings serialized into the common gate
   form; the axis quote rides along — it is what confirmers check against.
   If this run errored or stopped, there is nothing to confirm: stop and
   report the failure. A run can also come back `completed` without a review
   having happened — diff unreadable, no file under the caps, every file task
   failed; the conclusion names it (`Дифф не читается…`, `Ревью не
   состоялось…`) and `findings` is empty. That is a failed review too: stop
   and report it. An honest zero (`Находок нет (<покрытие>)`) is a valid
   review — keep going.
3. **Run the shared confirm run** — `CreateWorkflow(path=<this SKILL
   dir>/../ship/confirm.workflow.ts, args={root: "<the same checkout dir>",
   findings: <the `findings` array from the review run's return, passed as the
   JSON argument as-is — even when empty: the confirm run then reports the
   empty case honestly and publishes no artifact>, ticket: "<one
   line: what the diff is — base ref, scope>", report: "markdown"},
   subagent_model=<confirmer role$level>)`. It confirms every finding with
   fresh eyes on the confirmer role, dedups the same file:line across the two
   axes into findings marked with both, and publishes the merged markdown
   artifact ("review") — the same report the operator got before the split.
4. **Report honestly** — the merged markdown artifact is the deliverable; if
   publishing it fails, the same report rides in the confirm run's return
   field `report`.
   `verified` findings were reproduced by independent confirmers; `unconfirmed`
   ones need human eyes and are never dropped silently. Secret-looking strings
   in quotes are redacted before findings leave the run (формат-матрица
   queue-2/15: PEM-блоки, user:pass@host, словарные key=value, bearer,
   JWS/vendor-литералы; ограничения перечислены в шапке redact — не
   гарантия); выхлоп сводчика не пост-редактируется — его вход уже
   отредактирован; the workflows themselves are read-only — they never edit or
   commit.
