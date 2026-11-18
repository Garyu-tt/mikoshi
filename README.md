# Mikoshi Connectome Runtime · R14

**A recursive AdamantiumToolKit / Mechanicus IDE module, not a standalone IDE.**

Experimental, CPU-first nervous-system runtime, Engram storage, 2D eye/brain/spinal views and dynamic capability actions. The application is split into separately installable and recursively nested units. Each unit declares its identity, version, capabilities, dependencies and supported isolation in `units/**/manifest.json`. No fixed depth or static module inventory.

## Repository layout

- `units/`: plugin / module / component recursion; live capability ownership and runtime toggles.
- `server/`: authenticated preview API, sparse retina, CPU neural runtime, nervous bus, Engram checkpoints, 2D index and graph.
- `client/`: host-embeddable Mechanicus IDE client with user-arrangeable tabs, button placements and 2D maps.
- `contracts/`: typed versioned interfaces. `graph/`, `heritage/`: research provenance and code map.
- `tests/` and `tools/`: regression and size checks.

Any module can be promoted into an independently installed plugin without changing its public capability contract. Optional providers resolve by capability, not by a hardcoded module ID. Only real available actions are published. In-process isolation is implemented; separate-process containment is **not yet implemented**.

## Confirmed neural research

Pinned original retina R188 / R228 / R238 / R239 was tested at **920×920 per eye** with synthetic photons. A 7-phase Engram checkpoint + 13-phase continued run matched 802,451 optic spikes and full serialized neural state. Native R238 sparse input cut raw transport from 5,078,400 to 1,015,782 bytes per phase and matched optic output over a five-phase epoch. These experiments ran in isolated staging; they are not claims of production neural deployment.

Physical eyes, R257 depth, real spinal actuators, Dante brain, VM121 installation and Windows client E2E are **not connected or verified**.

## Local verification and preview

```bash
python -m unittest discover -s tests -q
python tools/verify_size.py
MIKOSHI_API_TOKEN='your-locally-generated-token' python -m server.api
```

The default preview binds localhost and its Bearer token is **not** Mechanicus IAM/SSO. Never expose this preview directly to public networks or commit real tokens, user Engrams or SQLite state. For recursive integration see [Adamantium contract](docs/adamantium-integration.md).

## Licensing and legacy history

GNU GPLv3 or later, see [LICENSE](LICENSE) and [AUTHORS.md](AUTHORS.md). The old Mikoshi Children v0.1.0 repo state is preserved on branch [archive/legacy-children-2026-11-18](../../tree/archive/legacy-children-2026-11-18). This is a source-tree replacement, **not** a server deployment.
