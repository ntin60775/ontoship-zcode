---
node_type: runbook
title: Install ontoship into a project (marketplace runner)
service: _platform
status: active
updated: 2026-09-30
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

All commands run from a checkout of the marketplace repo
(`sot-zcode-marketplace/deploy/`), `<target>` — the project's root:

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

1. Land changes in `ontoship-zcode` (worktree → gates → review → main).
2. Bump `version` in `package.json`, tag (`v0.5.N`), **push** (operator confirms).
3. Bump the pin in `sot-zcode-marketplace/marketplace.json` (`ref` + display
   `version`), commit, push.
4. `update ontoship <target>` in every deployed project. Rollback = revert the pin
   (git history of the project restores data; the runner does not roll back refs).

## Policy in one screen

- The runner writes **only code under `.zcode/`**; data (KB, managed block,
  hook registration in `.zcode/config.json`) belongs to the project.
- `.zcode/deployed.json` (journal) is **committed** with the project; vendored
  code is committed too (self-hosting survives clones); `.zcode/.backup/` is
  not committed.
- `on_drift: fail` — locally edited vendored files block `update` (list, fix or
  remove, then retry).
- **Dev cycle is release-cadence** (no dev pin): changes are proven by
  pytest + probe runs, then land as a tag; the vendored copy always equals the
  last release, not the working tree.
