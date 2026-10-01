---
name: code-review
description: Two-axis code review of an arbitrary diff (correctness; quality & dangerous places) — findings confirmed independently against code quotes, one merged report with verified/unconfirmed verdicts. Runs only by hand through the workflow engine on the reviewer-role model. Use when the operator says "поревьюй дифф", "code review", "ревью ветки", or runs /code-review.
---

# /code-review — two-axis review of a diff

The engine is the workflow **next to this SKILL.md**; this file is the hand-launched
entry point, the same split as `ship`/`reviewer.workflow.ts`.

1. **Resolve the model first** — `roles.py resolve --json` for the `reviewer` role,
   verify against ListModels (same fail-closed gate as `/ship` step 6). Missing or
   disabled model → stop and name the role and the layer file to fix; never fall
   back to the session model.
2. **Run the workflow** — `CreateWorkflow(path=<this SKILL dir>/code-review.workflow.ts,
   args={base: "<ref>", root: "<checkout dir>", scope?: "<pathspec>"}, subagent_model=<reviewer role$level>)`.
   `root` is what makes the review work in a worktree — point it at the checkout
   whose diff you mean; `base` is the ref the diff is measured from (`main`, `HEAD~1`).
   The split is always per file — one axis agent per changed file, each bounded by
   that file's diff (files over 2000 diff lines and diffs over 20 files are skipped
   with an honest note) — so small-context models hold every ask.
3. **Report honestly** — the merged markdown artifact is the deliverable. `verified`
   findings were reproduced by independent confirmers; `unconfirmed` ones need human
   eyes and are never dropped silently. Secret-looking strings in quotes are
   best-effort redacted on output (common token/key shapes — not a guarantee); the
   workflow itself is read-only — it never edits or commits.
