# Mikoshi Children

**Free, local, GPL-3.0-or-later licensed, single-individual experimental edition.**

> **Status: v0.1.0 reference runtime, not a port of the private Mikoshi engine.** This repository currently contains a minimal persistent 16-neuron demonstration and lifecycle infrastructure, not the actual Silico Animus connectome, Voxer, retina, spinal cord, physiology, Minecraft RELIC adapter, or an autonomous intelligent organism.

## Quick start

Requirements: Python 3.10+ on Windows, Linux or macOS.

```bash
python -m pip install .
mikoshi-children init
mikoshi-children status
mikoshi-children run
```

`run` creates the first individual if none exists, advances demonstration neural state, and stops with Ctrl+C. `init` creates exactly one individual and refuses to create another. `status` prints the persistent state.

## Limits (enforced by the stock application)

- **Population: one persistent individual**. An SQLite primary key plus `CHECK (slot = 1)` enforces this at the storage layer. There is no generations or second-individual creation API.
- **Runtime: one active process per operating-system user** using an OS-managed exclusive, nonblocking filesystem lock at a fixed per-user location, independent of the current working directory.
- The lock is released by the operating system when the process crashes. Stale lock files are harmless.
- Additional launches return exit code 3. Attempting to initialize a second individual returns exit code 2.
- No remote activation, device fingerprinting, account, tracking, or telemetry.

State defaults to `~/.local/state/mikoshi-children/` on Linux/macOS (or `$XDG_STATE_HOME` if set), and `%LOCALAPPDATA%\\mikoshi-children\\` on Windows. Treat state and engrams as **private user data**; do not commit them.

**Scope of enforcement:** Locks are local, per OS user, and rely on the filesystem's correct locking semantics. They cannot stop a different OS account, VM, container, machine, separate data root, or a user modifying open-source code. Guaranteed cross-machine single-instance enforcement is incompatible with an unrestricted offline open-source edition without some shared trusted authority. This edition makes no such DRM claim.

## License and fork policy

Original project code in this release is licensed under **GNU GPLv3 or later** (SPDX: `GPL-3.0-or-later`). See [LICENSE](LICENSE) and [AUTHORS.md](AUTHORS.md). Forks and commercial redistribution are permitted under the GPL, including its source-sharing obligations for covered derivative works.

Mikoshi Light and Pro are **not shipped** in this release. The stock single-individual limit is a design choice, not a restriction on users' GPL freedoms to inspect or modify the source. Private user data, engrams and privately developed connectomes are not included here. Previously published MPL-2.0 revisions retain their original grants.

## Tests

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
```

## Security and future work

Before connecting this experimental runtime to network APIs, Minecraft, or third-party plugins, implement authentication, sandboxed plugin loading, input limits, backups and migration tests. No network listener is enabled in this release.
