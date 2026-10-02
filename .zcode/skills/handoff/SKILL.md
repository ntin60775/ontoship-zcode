---
name: handoff
description: Hand the session's context to the next one — write a per-session handoff file (.scratch/handoff-<id>.md with From, Task, Done, Decisions with evidence, Open, Next, Artifacts) without overwriting previous handoffs, and carry task-surviving facts into memory. Runs only when the operator says "передай смену", "handoff", or runs /handoff. Never starts itself.
---

# /handoff — передать смену

Run only by the operator (`/handoff`, «передай смену»). One handoff per
invocation. The output is ephemeral by design — `.scratch/` is gitignored;
promoting a handoff into the KB as a report is a manual `kb-curate` decision,
never automatic.

1. **Project root.** Resolve the repo root first (`git rev-parse
   --show-toplevel`, as the `init` skill does) — every `.scratch/…` path below
   is relative to it. The SessionStart hook writes and reads `.scratch/` at
   the root; a handoff written anywhere else is one the hook never announces.
2. **Session id.** Read `<root>/.scratch/.session-id` — the SessionStart hook
   writes it from its own environment at this session's start (a bare session
   id, no date, rewritten every session — so its content cannot tell you
   whether it is stale; trust the hook that wrote it this session). Marker
   missing → fall back to `date -u +%Y%m%dT%H%M%SZ` as the id and say so
   plainly: honest degradation — the operator passes the real `#sess_*`
   manually, or the next session continues by file alone.
3. **Write `.scratch/handoff-<id>.md`** — one file per handoff, never
   overwrite a previous one. Sanitize `<id>` for the filename first: keep only
   `[A-Za-z0-9._-]`, replacing everything else with `-` — an id containing
   `/` or `..` must never reach a path (the hook validates its marker, but an
   old or hand-made one is read as-is). Template:

   ```markdown
   # Handoff <YYYY-MM-DD>

   From: <session-id> (<YYYY-MM-DD>)

   ## Task
   <ticket or plan path this session worked on>

   ## Done
   - <what actually landed, referenced rather than retold>

   ## Decisions
   - <decision> — evidence: <path:line | commit | #sess_*>

   ## Open
   - <unresolved questions, blockers>

   ## Next
   - <concrete first steps for the next session>

   ## Artifacts
   - <paths: worktrees, reports, plan files>
   ```

4. **Decisions carry evidence** — every decision references `path:line`, a
   commit, or `#sess_*`. Repo-changed decisions live in the repo: the file
   links, it does not duplicate (code, docs, commits are the source of truth).
5. **Memory, not file.** Facts that outlive the task (conventions,
   preferences, working agreements) go into the agent's persistent memory now
   — the zcode auto-memory (its `MEMORY.md` index plus one fact per file), not
   the session context — one line each, and stay out of the handoff file. The
   handoff carries task state; memory carries standing truth. If this
   environment has no persistent memory, say so in the report instead of
   writing the facts anywhere ephemeral.
6. **Cleanup while writing.** Delete stale (>7 days) handoff files — list
   them first, then
   `find .scratch -maxdepth 1 -name 'handoff-*.md' -type f -mmin +10080 -delete`.
   The SessionStart hook never deletes (it only announces fresh ones); this is
   the only cleanup.
7. **Report.** Say which file was written, what went to memory, and read out
   Open/Next — the operator decides what the next session picks up.

Boundary (handoff / memory / report): repo facts → the repo; task state → the
handoff file; task-surviving facts → memory. A handoff is never a KB doc.
