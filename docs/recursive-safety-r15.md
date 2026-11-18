# R15 — recursive module safety

Mikoshi remains an AdamantiumToolKit / Mechanicus IDE plugin. The module
tree organizes packages, but inter-module use is resolved through live,
versioned capability declarations, not source-path dependencies.

## Guarantees implemented in R15

- Any number of nested plugin modules/components may be discovered from
  colocated `manifest.json` files. The parent path must match the parent ID.
- Contract types, versions, optional dependency flags and capability
  action/prefix ownership are validated before a manifest becomes active.
- Module toggles persist atomically. A corrupt toggle file fails closed.
- Protected management modules cannot be disabled indirectly by switching off
  their ancestor; rejected mutations do not alter persistent state.
- A failed manifest reload leaves the previous in-memory catalog intact.
- Only live API actions claimed by a manifest and backed by a registered
  handler can be invoked or displayed. Unclaimed actions remain visible only
  in diagnostic metadata, never as functional UI controls.
- Dependency providers are selected by capability name, minimum version,
  readiness and an optional explicit provider identity.

## Important boundaries

This revision gates exposed API actions. It **does not** start, stop, unload
or sandbox arbitrary user-supplied executable code. `inprocess` is the only
declared isolation model; a crashing component can still affect its host
process. No separate-process or container lifecycle is advertised.

Unit manifests are read from the plugin's trusted local installation.
Re-indexing manifests does not hot-load executable Python modules.
Live hardware, original 920x920 retina deployment, physical spinal
actuators and Windows client installation remain separate integration tasks.

## Verification

```sh
python -m unittest discover -s tests -q
python tools/verify_size.py
```

The repository CI runs these checks on Python 3.11 and 3.13.
