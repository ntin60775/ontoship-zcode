---
node_type: runbook
title: Install ontoship into a project (marketplace runner)
service: _platform
status: active
updated: 2026-10-06
tags: [runbook, install, deploy, marketplace, update]
links:
  documents: [../../deploy.json]
  relates_to: [../../skills/init/SKILL.md, ../README.md]
---

# Install ontoship into a project (marketplace runner)

ontoship is a **project plugin**: it is never installed globally. The runner of
`sot-zcode-marketplace` vendors the pinned release into the project's `.zcode/`
per `deploy.json` mappings; the project's data (KB, managed block, role overrides)
is created afterwards by the plugin itself.

## Operations

All commands run from the **root** of a marketplace repo checkout
(`sot-zcode-marketplace/`), `<target>` — the project's root:

```bash
python3 deploy/deploy-plugin.py install ontoship <target>   # vendor the pinned release
python3 deploy/deploy-plugin.py update  ontoship <target>   # move to the new pin
python3 deploy/deploy-plugin.py check   ontoship <target>   # drift: vendored vs pin
python3 deploy/deploy-plugin.py remove  ontoship <target>   # un-vendor by journal
python3 deploy/deploy-plugin.py validate                    # catalog + manifests (CI)
```

After install/update, the runner's post-steps tell the agent what remains
(`post_update` in `deploy.json`): rebuild the KB index (automatic when `docs/`
exists), run the **init skill** for the managed block in `AGENTS.md` + `.gitignore`
lines, and set project role overrides in `<repo>/.zcode/ontoship/roles.md` if the
plugin defaults do not fit the host.

## Release cycle (plugin maintainers)

The branch model, the ticket loop, the tag rules and the deploy tail live in
[git-flow.md](git-flow.md) — deliveries straight from `dev` are a normal,
formalized process there (`vB.B.B-dev.N` tags). Runner-specific rules:

- Bump the pin (`ref` + display `version`) in
  `sot-zcode-marketplace/marketplace.json`, commit, push — the validator
  cross-checks `version` against the pin tag for semver refs.
- `update ontoship <target>` in every deployed project. Rollback = revert the pin
  (git history of the project restores data; the runner does not roll back refs).

## Policy in one screen

- The runner writes **only code under `.zcode/`**; data (KB, managed block,
  hook registration in `.zcode/config.json`) belongs to the project.
- `.zcode/deployed.json` (journal) is **committed** with the project; vendored
  code is committed too (self-hosting survives clones); `.zcode/.backup/` is
  not committed.
- `on_drift: fail` — locally edited vendored files block `update` (list, fix or
  remove, then retry).
- **The vendored copy equals the last pinned ref**, normally the release tag.
  A pinned `dev` tag (`vB.B.B-dev.N`) is equally normal — the formalized
  delivery-from-dev process lives in [git-flow.md](git-flow.md).
