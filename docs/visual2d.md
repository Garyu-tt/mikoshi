## R04. CPU-first 2D neural visual maps (no anatomical 3D)

No built-in 3D brain, retina or spinal viewer. Three projection types use one Canvas 2D client: `topology` for a brain connectome, `retinotopic` for the two eyes, and `segmental` for the spinal network. Neither missing neurons nor missing synapses are filled in. 2D coordinates generated from topology are clearly labeled *derived not anatomical*. The spine needs genuine segment/lane metadata; retina has real optical pixel coordinates.

`visual2d.list` enumerates currently usable 2D data sources. For actual read-only imported graph views set `MIKOSHI_VISUAL2D_DIR` to an approved directory of small validated JSON datasets conforming to `contracts/visual2d.v1.json`. Its actions are automatically registered/unregistered when files are added/removed. Users can move any action button to any configurable IDE tab/area. There are no default organ tabs. No graph file is treated as a running connectome.

If genuine pinned R239 is configured, two view actions are enabled, one per eye, showing only previously observed receptor tiles with exact timestamps. Unsampled areas are not fabricated. 8x8 mosaic tiles are sampled at stride 4 for the initial CPU viewer; the 2D display is an LOD, not a replacement for the full retina model. There is no claim of full checkpoint/restore in this revision.

Interaction: mousewheel zoom, drag pan, click a point to inspect its metadata, double-click to reset. Core simulation never depends on UI frame rate or whether a view is open. The preview remains separate from the real Mechanicus host IAM until explicitly integrated.
