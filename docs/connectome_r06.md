# R06: Executable connectome contract

A connectome runtime is **not** the 2D viewer. Import real topology only via
`MIKOSHI_CONNECTOME_DIR`, with one `<id>.connectome.json` per registered circuit.
The JSON requires schema, ID, organ (`brain` or `spinal`), source provenance,
coordinate_kind, `dt_ms`, explicitly numbered neurons and weighted synapses.
See `contracts/connectome.cpu.v1.json` for the full contract.

Each neuron requires stable ID, 2D coordinates (with declared origin),
`tau_ms`, threshold and optional refractory duration. Spinal neurons require
segment and lane. All synapses must reference existing IDs. No visual edges
are automatically turned into neural synapses. Loader has conservative CPU
limits (2,500 neurons / 20,000 synapses), with no implicit GPU requirement.

## Live graph and actions

On presence of a valid file, the API discovers
`connectome.status.<id>`, `connectome.step.<id>`, `visual2d.open.connectome.<id>`,
`engram.snapshot.<id>` and `engram.restore.<id>`.
Removed files disappear from capability discovery; a modified/removed source
with active state is retained in a blocked, checkpointable state until the
original pinned bytes return. R06 processes only explicitly requested steps.
No undocumented free-running loop, background training, or motor outputs.

`connectome.step.<id>` accepts a clock domain, strictly increasing
`sample_at_ns`, and a dictionary of externally supplied stimulation pulses
`{neuron_id: finite_amplitude}`. The LIF engine uses a previous-tick spike to
propagate current across weighted synapses. Its 2D map shows **computed**
spikes from the last tick (`activity` 0 or 1), not interpolated animation.

## Specimen safety

`engram.snapshot.<id>` writes a create-only archive with the **actual** LIF
potentials, refractory state, last spiking neurons, clock, the exact source
file and SHA-256 manifest. `engram.restore.<id>` checks every payload, the
source hash and topology identity before replacing an empty engine state.
Research Engrams cannot be restored as living neural specimens. This restores
the CPU-LIF circuit only, not R239/retinal physiology, world/body state or
Dante's complete memory. The existing provenance graph remains separate.

## Explicit limitations

- Source topology must be provided; **no default fake brain or spinal cord**.
- Original retina R228/R239 still requires source pins, NumPy and real RGB24.
- LIF neural tick is manually API-driven, not a guaranteed real-time clock.
- Real retina-to-LIF wiring and full specimen migration are not implemented.
- Hosting IAM, browser E2E, Windows installation and VM121 integration remain
  pending. Do not expose development bearer authentication publicly.
