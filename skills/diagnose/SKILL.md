---
name: diagnose
description: Diagnose a hard bug or a strange question down to a minimal reproduction — build a tight red/green feedback loop, reproduce and minimise, test ranked falsifiable hypotheses, then report the root cause with evidence and do NOT fix it here (the fix goes through /grilling → /to-tickets → /ship, where the repro becomes the regression test). Artifacts live in .scratch/diagnose-<slug>/ where the continuation work finds them. Runs only when the operator says "диагностируй", "diagnose this", "почему ломается", "разберись с багом", or runs /diagnose. Never starts itself.
---

# /diagnose — репро-цикл на вопросах

A discipline for hard bugs and strange behavior: build a tight pass/fail
signal, reproduce, minimise, hypothesise, instrument — then **report the root
cause and stop**. Code changes do not happen here; the fix goes through the
normal chain (`/grilling` → plan contract → `/to-tickets` → `/ship`, where the
minimal repro becomes the regression test). One diagnosis per invocation,
launched only by the operator.

Skip a phase only with an explicit, written justification in the report.

## Where the evidence lives

Resolve `<repo-root>` first (`git rev-parse --show-toplevel`, as the handoff
skill does) — every `.scratch/…` path below is relative to it. Derive
`<slug>` from the question: kebab-case, keep only `[A-Za-z0-9._-]`, replace
everything else with `-`; `mkdir -p` the folder before the first write. All
artifacts of one diagnosis go to
`<repo-root>/.scratch/diagnose-<slug>/` (gitignored, ephemeral by design — a
diagnosis is not a KB doc; promoting it is a manual `kb-curate` decision):
the loop scripts, captured outputs, and `REPORT.md`. The report must not get
lost: quote its path into whatever the continuation reads next — the plan
contract's `Context` (grilling folds it in), or a `/handoff` file if the
session ends first. The durable trail is downstream: the regression test in
the repo and the `gotcha` in the KB after the fix lands.

## Phase 0 — Redact

The loop shows commands, outputs and captured artifacts. **Redact every
secret first** — write `<REDACTED>` in its place:

1. Name what must never appear verbatim: credential values from env/config,
   `Authorization`/`Cookie` headers, connection strings, key material.
2. Build loops against env vars, so the credential stays in the environment
   and never lands in a captured file.
3. Redact captured files in place with a script that takes the secret from
   the environment and writes `<REDACTED>` — never pass the value as a
   command-line argument (it leaks into `ps` and shell history). Captured
   artifacts carry auth headers: quote only the lines that carry the signal.
4. Re-grep each artifact for the raw values before it goes anywhere — a
   shown artifact is already published. Record in the report what was
   redacted (patterns, never values).

## Phase 1 — Build a feedback loop

**This is the skill.** A tight pass/fail signal that goes red on *this* bug
is what bisection, hypothesis-testing and instrumentation all consume.
Without one, staring at code won't save you.

Try in roughly this order: (1) failing test at the seam that reaches the bug;
(2) curl/HTTP script against a running server; (3) CLI invocation with a
fixture input, diffing stdout; (4) headless-browser script asserting on
DOM/console/network; (5) replay a captured trace; (6) throwaway harness
(minimal subset, mocked deps); (7) property/fuzz loop for "sometimes wrong"
bugs; (8) bisection harness between two states (regressions); (9)
differential loop (old vs new); (10) human-in-the-loop script as last resort
— copy `scripts/hitl-loop.template.sh` from next to this SKILL.md, edit the
steps, run it: the agent runs the script, the operator follows the prompts in
their terminal.

**Tighten it** once it exists: assert the exact symptom, more deterministic
(pin time/seed, isolate fs/network), faster (seconds), one command,
agent-runnable (via the Bash tool) — and already run at least once, shown
redacted. **Non-deterministic bugs:** the goal is a higher reproduction rate,
not a clean repro — loop many times, parallelise, add stress. If you cannot
build a loop, stop and say so — ask for the environment, a captured artifact,
or temporary instrumentation. Do not hypothesise without a loop.

## Phase 2 — Reproduce + minimise

Run the loop; watch it go red. Confirm it is the *reported* failure mode, not
a nearby one. Shrink the repro to the smallest scenario that still goes red —
cut inputs/callers/config one at a time, re-running after each cut. A minimal
repro shrinks the hypothesis space and becomes the regression test later.

## Phase 3 — Hypothesise

Generate **3–5 ranked, falsifiable hypotheses** before testing any. Format:
"If <X> is the cause, then <changing Y> makes it disappear / <changing Z>
makes it worse." Show the ranked list to the operator before testing (cheap
checkpoint; proceed in the stated order if they are away).

## Phase 4 — Instrument

Each probe maps to one prediction of one hypothesis; change one variable at a
time. Prefer a debugger/REPL over logs; tag every debug line `[DEBUG-<id>]`
for one-grep cleanup. For performance regressions, measure first (baseline →
bisect), fix second. Record each probe's prediction and outcome in the report
— a hypothesis refuted with evidence is a result too.

## Phase 5 — Report, don't fix

Diagnosis ends at the root cause. **Do not implement the fix in this run,
even if it looks like one line.** Write `.scratch/diagnose-<slug>/REPORT.md`:

- **Question** — the bug or strange behavior, as reported.
- **Redaction** — what was redacted (patterns, never values) and the re-grep
  that confirmed it; the written justification for any skipped phase.
- **Root cause** — the single cause, stated as a falsifiable claim, with the
  evidence that pins it (`path:line`, probe outputs).
- **Minimal repro** — the exact redacted command, what it prints, and where
  the loop script lives. This becomes the regression test at fix time.
- **Refuted hypotheses** — each with the evidence that killed it.
- **Recommended fix** — what the change should be, and the test seam for the
  regression test.
- **Prevention** — what would have stopped this (a `gotcha` for the KB after
  the fix lands; an architectural note goes into the plan contract).

Then hand off: give the operator the report path plus a 3-line summary; the
fix goes through `/grilling` (quote the report path in the plan contract's
`Context`) → `/to-tickets` → `/ship` — or `/ship <plan>` directly for a
one-ticket fix.

Boundary: evidence → `.scratch/diagnose-<slug>/`; the fix → `/ship`; the
lasting knowledge → the regression test in the repo + a `gotcha` in the KB
after the fix lands.
