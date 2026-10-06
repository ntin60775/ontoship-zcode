---
name: handoff
description: Hand the session's state to the next one — regenerate the single rolling snapshot .scratch/handoff-current.md in full (provenance stamps, Task, Done, Decisions with evidence, Open, Next, Artifacts), the same file /ship rewrites automatically when it closes a ticket. Runs only when the operator says "передай смену", "handoff", or runs /handoff. Never starts itself.
---

# /handoff — передать смену

Run only by the operator (`/handoff`, «передай смену»). The output is one
file — `.scratch/handoff-current.md`, the single rolling snapshot of the
project's work state — rewritten **in full on every write**: a regenerate,
never an append or a patch. `/ship` writes the same file automatically when
it closes a ticket, so the snapshot stays current no matter how the previous
session ended. The output is ephemeral by design — `.scratch/` is gitignored;
promoting a handoff into the KB as a report is a manual `kb-curate` decision,
never automatic.

1. **Project root.** Resolve the repo root first (`git rev-parse
   --show-toplevel`, as the `init` skill does) — every `.scratch/…` path below
   is relative to it. The SessionStart hook writes and reads `.scratch/` at
   the root; a handoff written anywhere else is one the hook never announces.

2. **Provenance stamps.** Read `<root>/.scratch/.session-id` — the
   SessionStart hook writes it from its own environment at this session's
   start — and take the current commit (`git rev-parse --short HEAD`). The
   id is provenance, not an address: nothing addresses a file by it anymore,
   so a reused id is harmless. Degrade honestly, never refuse: marker
   missing or unreadable → the `From:` stamp without the id; commit
   unavailable (a repository with no commits yet) → the stamp without the
   commit — `updated:` and whatever provenance exists are still written, and
   you say so plainly in the report. The snapshot matters more than the
   stamp.

3. **Write `.scratch/handoff-current.md`** — the same fixed name every time,
   the whole file every time. Write to a temporary file in the same
   directory and rename it over the target — the rename is atomic, so the
   SessionStart hook or any concurrent reader never sees a half-written
   file. There are no collision branches and no timestamp fallback: two
   writers targeting one file is the design, not a conflict, because every
   write is a full regenerate. Template:

   ```markdown
   # Handoff

   updated: <YYYY-MM-DD>
   From: <session-id> (<YYYY-MM-DD>), commit <short-hash>

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
   - <paths: reports, plan files, memory keys>
   ```

   Degraded `From:` forms keep the shape, minus the missing part: no marker →
   `From: commit <short-hash> (<YYYY-MM-DD>)`; no commit (empty repository) →
   `From: <session-id> (<YYYY-MM-DD>)`; neither → `From: <YYYY-MM-DD>`. Never
   leave a `<session-id>` or `<short-hash>` placeholder literal in a written
   file.

4. **Glue, not a second memory.** The snapshot holds position and links: the
   plan order, commits, plan paths, memory keys. Facts that live in the repo
   or in memory are referenced, never retold — a duplicated fact becomes two
   versions the next session cannot reconcile.

5. **Decisions carry evidence** — every decision references `path:line`, a
   commit, or `#sess_*`. Repo-changed decisions live in the repo: the file
   links, it does not duplicate (code, docs, commits are the source of truth).

6. **Memory, not file.** Facts that outlive the task (conventions,
   preferences, working agreements) go into the agent's persistent memory now
   — the zcode auto-memory (its `MEMORY.md` index plus one fact per file), not
   the session context — one line each, and stay out of the handoff file. The
   handoff carries task state; memory carries standing truth. If this
   environment has no persistent memory, say so in the report instead of
   writing the facts anywhere ephemeral.

7. **Legacy cleanup while writing.** Legacy per-session files
   (`handoff-sess_*.md` and the like, from before the rolling snapshot) are
   never written by this skill and are left alone while fresh; the only thing
   that ever touches them is deleting the stale ones (>7 days) — list them
   first, then, from the root resolved in step 1,
   `find "<root>/.scratch" -maxdepth 1 -name 'handoff-*.md' ! -name 'handoff-current.md' -type f -mmin +10080 -delete`.
   A missing `.scratch/` (fresh checkout) means nothing to clean, not an
   error. The current snapshot itself is never stale: an old snapshot means
   no work happened, and it is announced all the same. The SessionStart hook never
   deletes (it only announces); this is the only cleanup.

8. **Report.** Say which file was written (always
   `.scratch/handoff-current.md`), what went to memory, and read out
   Open/Next — the operator decides what the next session picks up.

Boundary (handoff / memory / report): repo facts → the repo; task state →
the snapshot; task-surviving facts → memory. A handoff is never a KB doc;
`.scratch/` never becomes durable.
