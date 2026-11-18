# R07: original retina R239, binary optic transfer and typed Engram

## Real sources and gating

R06 had a constructor bug: `ClusteredRetinalCircuitR239` needs `FastNeuralRetinaR188`, not plain `RetinalMosaic` R180. R07 pins the additional original `neural_retina_r188.py` and loads R180, R182, R188, R228, and R239 in that dependency order. A hash mismatch, missing source or missing NumPy suppresses the executable R239 actions. Source files remain external and read-only, not duplicated into small AI-editable files.

This checkout does not ship the actual historical retina implementations. The hashes in `heritage/retina_source_pins.json` were checked against the historical old-server source in the conversation. True original R239 simulation has NOT yet been executed in this local runtime. `tools/smoke_r239_original.py` is the explicit end-to-end acceptance gate for a staging host with the SHA-matching originals and NumPy. The old host's default Python had no NumPy at the time of inspection.

## Optic transport, no invented pixels

`retina.r239.step` requires left/right original post-optical RGB24, with exact dimensions, phase order, explicit timestamps, source body UUID and bounded frame duration. Real R239 returns `(uid uint32, at_us uint32)` in little-endian 8-byte events. R07 holds the exact raw packet in an 8-packet / 64-MiB bounded memory spool, publishes its hash, count and fetch reference on `optic.spikes.packet`, and serves chunks via `retina.r239.spikes.read` (`sequence`, `offset`, `limit`). Eviction is explicit: a reference can expire, it never silently becomes a reconstructed stream. No LGN/V1/stereo advance is inferred. Raycasts and LiDAR are independent spatial sensors, not fake photoreceptor samples.

`visual2d.open.retina.axons.left` and `.right` draw bins computed ONLY from actual R239 spike UIDs, using the retina's original optic coordinate mapping. `spike_count` is genuine and `activity` is normalized only within the observed packet. Nodes are clearly marked `aggregate`; no fictitious individual neurons are drawn. The original receptor mosaic maps remain distinct from axon output maps. Both use 2D Canvas, not WebGL.

## Retinal checkpoint, separate from LIF and research

New `.engram` kind: `retina-specimen`. Stores `mikoshi.retina-r239-state.v1` plus typed numeric buffers of original retina/sensor/circuit (bytearray, Python array, NumPy numeric arrays). It includes source SHA-256 pins, retina shape, sampling plan, body UUID, sequential phase, neuron clocks, dynamic photoreceptor/interneuron buffers and static mosaic fingerprint. NumPy arrays have explicit dtype/shape and per-buffer SHA-256. No `pickle` or executable code. ZIP-level SHA-256 checks and atomic create-only filesystem writes protect the archive.

`engram.retina.r239.snapshot` captures under eye lock. `engram.retina.r239.restore` verifies every buffer, source pin and dimension before applying, and refuses to overwrite a running retina. The R228 schedule cache is regenerated from pinned source+seed when resumed. Research Engrams and LIF specimens cannot masquerade as R239 neural state. The numeric codec roundtrip is unit-tested on structurally faithful doubles. **Actual original R239 deterministic resumed step has not yet passed integration**; do not treat the status contract as a production guarantee.

## Integration and security gates

1. On a non-production staging VM, mount the five genuine original Python sources read-only and install NumPy in a dedicated virtual environment.
2. `MIKOSHI_RETINA_LEGACY_DIR=/path/to/verified-originals python -m tools.smoke_r239_original` must compare exact true R239 optic-spike bytes and follow-on buffer state after Engram restore.
3. Test the Godot RGB adapter with valid real camera images; leave LiDAR/rays separate. Keep R257 stereo correction and motor turning disabled until physics tests.
4. Connect the new server through host IAM and TLS, with a distinct Windows client; the built-in Bearer preview remains loopback-only.
5. Only after acceptance install in VM121, with backups and an explicit rollback. Original legacy server is source-only.
