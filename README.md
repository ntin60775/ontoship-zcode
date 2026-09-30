# OntoShip for ZCode

> **A project knowledge base is just `markdown` + a `README` index + `git`.**
> Nothing simpler works better — now driving zcode's native primitives.

The OntoShip method — a deterministic markdown knowledge base, an interview that
stress-tests plans before code exists, and a gated one-ticket-at-a-time ship flow —
rebuilt as a **zcode plugin**:

- plan approval and stop-points ride zcode's **native plan/permission gates**, not prose rules;
- the ship reviewer and the grilling challenger run on **explicitly assigned models**
  (roles: plugin default → user-global → per-project override);
- fan-out work (KB bootstrap, two-axis review, architecture scans) runs as **workflows**;
- destructive-command safety ships **in the plugin** as a PreToolUse hook.

Sister project: [ontoship-omp](https://github.com/vakovalskii/ontoship) (the omp agent
version). This repo shares only the GitMark engine (`gitmark.py`, vendored, MIT) and the
ontology model; everything else is written for zcode.

## Status

**In development** — see `AGENTS.md` (entry point) and `docs/` (the KB, dogfooded).
Not yet published to a marketplace; install from a local directory.

## License

MIT — see [LICENSE](LICENSE).
