---
name: architecture
description: Background architecture scan of a repo — a module/connection map cross-checked against the documented architecture (KB) for drift; drift findings confirmed independently by the shared ship confirm run. Runs by hand; the scan is a background workflow and never blocks the session. Use when the operator says "просканируй архитектуру", "architecture scan", "карта модулей", "найди дрейф с доками", or runs /architecture.
---

# /architecture — background architecture scan

The engine is the scan workflow **next to this SKILL.md** plus the shared
confirm run `../ship/confirm.workflow.ts` — the same two-run shape as
`/code-review` (one confirmer machinery for every gate, no split-brain).
Ported from the omp prototype's scan part (mp-improve-codebase-architecture):
the interactive grilling of candidates stays interactive and is not part of
this run — the scan produces the facts (map + drift), the operator decides.
Read-only: nobody edits or commits anything.

1. **Resolve both models first** — `roles.py resolve --json` for the `reviewer`
   AND the `confirmer` role, verify each against ListModels (same fail-closed
   gate as `/ship` step 6). Missing or disabled model, absent level → stop and
   name the role and the layer file to fix; never fall back to the session
   model.
2. **Launch the scan in the background** — `CreateWorkflow(path=<this SKILL
   dir>/architecture.workflow.ts, args={root: "<repo root to scan>",
   direction?: "<module, subsystem or pain point>"}, subagent_model=<reviewer
   role$level>)`. CreateWorkflow starts the run in the background by design —
   **do not wait, do not poll**: tell the operator the scan is running (name
   the run), and let the session do other work. The completion notification
   arrives on its own and only then does step 3 happen; the session is never
   blocked on the scan.
3. **On the completion notification — confirm the drift findings.** If the
   run errored, or stopped for a non-user reason (`stop_reason`
   `provider`/`model`/`interrupted`), stop and report the failure — there is
   nothing to confirm; `stop_reason: user` is the operator cancelling on
   purpose — acknowledge it, do not dress it up as a failure. A completed
   run can also be a failed scan: a hard abort (not a git repo, no code
   areas) comes back with `areas: []` and a one-item `notCovered` naming the
   cause, and a drift-stage failure says so in `conclusion`/`notCovered`
   («Скан без сверки…», «сверка не состоялась…») — judge by those fields,
   not by string-matching conclusion literals. Either way: stop and report
   it. Otherwise take the run's `findings` array (raw drift, gate form) and
   pass it as-is — even when empty — to the shared confirm run:
   `CreateWorkflow(path=<this SKILL dir>/../ship/confirm.workflow.ts,
   args={root: "<the same root>", findings: <the findings array>, ticket:
   "architecture-скан <repo basename>: расхождения карты кода с KB;
   подтверждается факт расхождения, не пожелание об улучшении", report:
   "markdown"}, subagent_model=<confirmer role$level>)` — `<repo basename>`
   is the short last path segment of root (what the run's own map title
   uses), not the absolute path: the ticket line lands in every per-finding
   confirmer's prompt.
4. **Relay both deliverables.** The scan run publishes the module/connection
   map (artifact «map»; when that publish fails, the same map rides in the
   run's `map` return field — the conclusion names the fallback); the
   confirm run publishes the merged drift report
   (artifact «review» — verified findings plus the «не подтверждено»
   section). `verified` findings were reproduced by independent confirmers on
   the confirmer model; `unconfirmed` ones need human eyes and are never
   dropped. Secret-looking strings in output are best-effort redacted (common
   token/key shapes — not a guarantee). Known cosmetic: the confirm run's
   report header says "Code-review" — the machinery is shared with the review
   gates by design; the content is the drift report.
