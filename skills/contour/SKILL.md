---
name: contour
description: Verified lessons of the zcode-workflow contour — mechanics that holds in any project CreateWorkflow/AmendWorkflow args contracts, YAML header parsing, unconditional approval windows, subagent baseline weight, agent() failure surface, world.run semantics, submit-time typechecking, args transport limits, args preflight. Use when writing or reviewing a zcode workflow (.ts with a /* zcode-workflow */ header), before submitting a run (args preflight), before running AmendWorkflow on an existing run, or when a workflow упал, стопнулся (provider-stop), was rejected at submit (invalid_yaml, args refused) — any "zcode workflow" mechanics question.
---

# Contour — verified zcode-workflow mechanics

Mechanics of the zcode workflow primitives (CreateWorkflow, AmendWorkflow,
`agent()`, `world.run`) learned the hard way in this plugin's own gated runs —
each lesson as **symptom → cause → action** so a consuming project does not
re-collect the same failures. The lessons are substrate-independent: no
provider tariffs, no credentials, no model-role assignments — those are
machine-level concerns documented in the consuming project's ops docs
(`docs/ops/install.md` of this repo) and the `/roles` skill.

A workflow here means a `.ts` file with a `/* zcode-workflow ... */` YAML
header, submitted via `CreateWorkflow(path=...)`.

## 1. AmendWorkflow starts a revision with empty args

**Symptom.** A revision of an existing run starts and immediately exits early
with the script's own missing-argument message (observed: «Тикет не передан»)
— although the same script worked with args on the original
`CreateWorkflow`.

**Cause.** `AmendWorkflow` carries the script and run settings, but **not**
`args`: the revision starts with an empty args object.

**Do.** If the args contract changed since the original run (an argument
added, renamed, or became required) — submit a fresh `CreateWorkflow`.
Amend only for script/settings revisions under an unchanged args contract.

## 2. Inline CreateWorkflow scripts accept no args

**Symptom.** `CreateWorkflow` with an inline `script` and `args` is refused
by the host at submit time.

**Cause.** `args` is bound to the declaration in the workflow header, and an
inline script has no file to carry that header.

**Do.** Save the script to a file with a `/* zcode-workflow */` header that
declares the args, and start it via `path`. Inline is for arg-less scripts.

## 3. An unquoted colon in the YAML header breaks the submit

**Symptom.** The submit is rejected with `invalid_yaml` — before any
TypeScript diagnostics, so the error looks unrelated to the code.

**Cause.** A bare `colon + space` inside a header scalar (`description`, an
arg description) parses as a nested mapping. Russian prose is a frequent
offender: any sentence with «:» in it.

**Do.** Quote every header value that may contain a colon
(`description: "…: …"`). Check the header by eye before the first submit —
the parse error reports the YAML line, not the intent.

## 4. Workflow approval windows are unconditional

**Symptom.** The run waits on an approval window although the session is in
full-access/yolo; a "continue" typed in chat does not release it, and the
agent may misread the wait as a hang.

**Cause.** Every `CreateWorkflow` shows the operator a confirmation window —
there is no trusted-workflow setting. Without a window only `AmendWorkflow`
of a run owned by the same session executes.

**Do.** Budget the windows in the run plan (a gated ship ticket means at
least two: review + confirm). A chat "continue" closes a dialogue
stop-point, never the workflow window — those are different confirmations.

## 5. Workflow subagents carry a fixed baseline request weight

**Symptom.** The first request of a workflow `agent()` does not fit the
provider's context ceiling (provider-stop) even though the ask is tiny;
splitting the task into more subagents does not help.

**Cause.** The baseline weight of every workflow-subagent request is the
workflow-agent contract plus the schemas of **all** tools the host exposes —
built-ins and every MCP server in the session — measured at ~140k tokens on
a machine with a rich MCP set. Every node pays it; topology (lenses,
fan-out) saves history, not the baseline. There is no per-subagent tool
profile, and nested workflows are not allowed.

**Do.** Levers, in order of effect: replace subagents with a micro-CLI
substrate (`world.run` calls from the workflow itself — no subagents at
all), reduce MCP servers in the session, or use a model with a larger
window. Before blaming the ask size, compute the baseline.

## 6. agent() failure paths are not live-inducible

**Symptom.** An `agent()` failure branch cannot be exercised in a live run:
runs either pass through the call or die as a whole.

**Cause.** `subagent_model` is validated by the host before the run;
transient model errors are retried by the runtime, deterministic ones stop
the whole run as a provider-stop — outside the script. Only logic-level
refusals (e.g. ContextLimit) ever reach a `catch` in the script.

**Do.** Cover failure branches with unit matrices over pure functions and
with gate reviews; in the acceptance report mark such paths
«live-неиндусируемо» instead of claiming a live proof.

## 7. world.run: literal command names, exit codes are values, timeouts are rejections

**Symptom.** Two different surprises: passing the command name as a runtime
value fails at submit, and a run dies on `world.run` where a handled failure
was expected.

**Cause.** The command name must be a compile-time literal (the submit shows
the operator the exact command list — that is the security contract). A
nonzero exit code is an ordinary value: no exception is thrown. A timeout or
a spawn failure, however, is a rejection (exception).

**Do.** Command name — literal; runtime values — in the args array. Branch
on nonzero exits, do not catch them. Catch rejections (timeout, spawn
failure) only where the failure is a logic branch, and let it propagate
otherwise.

## 8. Workflow .ts runs without tsc — the full typecheck happens at submit

**Symptom.** The file "runs" locally, then hidden type errors surface on the
first submit — most often on the first submit after a host self-update.

**Cause.** The engine executes workflow `.ts` without a full typecheck; the
only complete check is the host's compilation at submit time.

**Do.** Smoke locally with `node --experimental-strip-types` — and wrap the
entry in an async function: a top-level `return` without a wrapper fails
spuriously (strip-types tolerates it, the engine does not — or vice versa;
the wrapper makes both agree). Treat the first submit after a host update as
the real typecheck and expect it to surface latent errors.

## 9. The host does not truncate CreateWorkflow args

**Symptom.** A large structured argument "fails to parse" at start.

**Cause.** A truncated transport would be the host's fault; measured, the
host transports at least ~25 KB per argument intact. "Failed to parse" means
the JSON was already broken at the caller.

**Do.** Validate the JSON (and the `json`-typed args schema) before the
submit; treat parse failures as caller bugs, not transport limits.

## 10. The host validates args against the declaration — nothing more

**Symptom.** Two silent transport failures from gated runs: a review run
starts cleanly and reports the diffs unreadable — its `root` argument was
never passed, and the run went on with the silent default; a confirm run
aborts honestly on its own guard — the `findings` argument arrived as a
pre-serialized JSON string where an array was declared.

**Cause.** The host checks the call against the header declaration and
nothing else: unknown keys, missing required values and wrong types are
rejected. But `required: false` with a default passes silently when the
argument is omitted, and a `type: json` argument accepts a string as a valid
value. Whether a semantically needed argument was actually passed for *this*
call is the caller's knowledge — no declaration carries it.

**Do.** Preflight the args before every submit, against what the script
reads in this call, not against the declaration alone:

- name every argument the script actually reads in this run and pass it
  non-empty — a `required: false` declaration is a lower bound, not a
  checklist (the required-check misses exactly the omitted-args incident);
- pass `json`-typed arguments as structural values, never as pre-serialized
  strings; build the strings you do pass with `JSON.stringify`, not by hand
  (lesson 9);
- the script needs args — submit via `path` with a header; an inline script
  accepts none (lesson 2);
- a revision whose args contract changed — a fresh `CreateWorkflow`
  (lesson 1);
- re-eye the quoted header values before the first submit (lesson 3).

## 11. `node -e` eats the `--` separator

**Symptom.** An inline script launched as
`world.run("node", ["-e", script, "--", envelope])` never finds its payload:
the script searches `process.argv` for `--` and gets `-1`.

**Cause.** `node` itself consumes the `--` separator before the script sees
argv; the envelope is simply the last remaining element.

**Do.** Keep the template `world.run("node", ["-e", script, "--", json])` —
the separator stays a harmless visual convention (and the runtime values stay
in the args array, lesson 7) — but locate the envelope as the last argv
element, `process.argv[process.argv.length - 1]`, never as "the element
after `--`". The direct-API fallback of this repo's review gate is built on
this template; its transport fixes travel together with lesson 10.

## What does not belong here

Provider tariff ceilings, credentials, model-role assignments and
provider-card configuration are machine-level, substrate-specific concerns —
they change with the provider, not with zcode. This skill carries only the
mechanics of zcode primitives, which holds in any project. For the review
gate's substrate prerequisites see this repo's `docs/ops/install.md`
(vendored only into projects that have it) and the `/roles` skill.
