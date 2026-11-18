# R05: indexed, viewport-bounded 2D neural maps

A single Canvas 2D client represents three **real-source** kinds of neural data:
brain connectome topology, left/right retinal mosaics and spinal segments.
This is a host-IDE module, not an independent IDE. Views, commands, buttons,
subtabs and areas enter the shared graph dynamically, never as empty shells.

## Scalable indexed views

A verified metadata file plus JSONL neurons and synapses is converted into
an immutable SQLite source index with source SHA-256 and a validated identity:

```sh
python -m tools.index_visual2d metadata.json neurons.jsonl synapses.jsonl \
  /approved/visual2d/organ-name.m2d.sqlite
```

`metadata.json` must declare schema `mikoshi.visual2d.v1`, a unique `id`,
`title`, source provenance (`source.id`), `organ` (`brain`, `retina`, `spinal`),
`projection` (`topology`, `retinotopic`, `segmental`) and `coordinate_kind`
(`source` or `derived`). Each neuron JSONL record supplies a globally stable ID
and normalized `x,y` in [0,1]. `spinal` neurons additionally need a source
`segment`. Synapse JSONL records supply genuine existing `source,target` IDs.

The importer fails on duplicates, dangling connections and invalid values,
creates no partial destination and refuses to overwrite an existing index.
It does **not** infer absent synapses, neurons, neuron positions or spinal
segment IDs. The source dataset owner is responsible for deriving projected
2D positions if the original specimen contains only 3D coordinates. Derived
2D geometry must be explicitly labeled and is not anatomical ground truth.

Point the server to an approved **read-only** visual data folder using
`MIKOSHI_VISUAL2D_DIR`; files with `.m2d.sqlite` are discovered alongside
small `.json` views. The resulting API actions are registered automatically:
`visual2d.open.<view-id>` and `visual2d.query.<view-id>`. Every indexed query
accepts bounded `x0,y0,x1,y1,limit`. The response explicitly marks when
points or edges are incomplete; it never claims a partial sample is the whole
connectome. At most 2,500 points / 6,000 connections per request.

The client asks for the visible region when panning/zooming, discards stale
requests, and retains the selected neuron's stable ID. 2D rendering never
drives, advances or pauses the actual neural simulation.

## Accurate R239 retina LOD

The read-only eye map now **aggregates**, rather than skips, every observed
8x8 tile within a requested LOD block. Values `sampled_receptors` and
`fresh_receptors` come from observed samples and original timestamps; the
`observed_fraction` is *not* luminance or neuron membrane activity.
Unobserved receptors remain unobserved; historical receptor values do not
become new photons. Real R239 source is an opt-in SHA-pinned dependency.

## Limits and security

These indexed maps are imported **data**, not proof of a running connectome.
They are not neural checkpoints. Full brain/spinal engines, R257 depth gate,
Godot R86/R88 physical controls, IDE SSO and complete neural Engram restore
are still independent, unverified integration gates. The HTTP preview uses its
own token on loopback and must not be published on the Internet.

The original sources on mirbi-linux remain untouched. The canonical future
server is VM121; Windows is the intended client, but this archive is a local
integration build, not a deployment report.
