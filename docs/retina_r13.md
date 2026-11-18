# R13: full original retina 920x920, sparse network transport

One original Retina R188/R228/R238/R239 source-pinned population, 920x920x2
photoreceptors, five complete-tile R238 sampling phases per epoch.

The R12 `mikoshi-engram.v1/retina-r239-state.v2` remains unchanged. Original
full-size R239 passed seven phases before serialization and 13 afterward, with
802451 byte-identical spikes and byte-identical final neural state. The
compressed Engram was 4526726 bytes. Synthetic brightness stimuli only.

The source-phase action `retina.r239.photon.accept` accepts the real R238 packet
produced on a compatible sensor client. Original R238 checks body UUID, sampling
fingerprint and SHA-256 before R239 advances neuronal state. Original source
comparison at 920x920 proved 106211 identical spikes over five phases vs raw
RGB transport; last packet was 1015782 bytes vs 5078400 raw RGB bytes (4.9995x).

This API does NOT make up new photoreceptor measurements or claim a physical
camera is installed. R238 packet production requires matching source pins,
width/height, passes, sampling seed and current neural-body UUID. Clients must
not silently regenerate a new UUID. Timestamp is in unix nanoseconds.

## Safety and limits

Original historical code stays read-only. This benchmark runs only by explicit
CLI request in a separate process with pinned sources and NumPy installed.
No live neural instance, world state or motor actuator is modified. VM121 and
Windows not deployed. The R257 stereo matcher is not production-ready.

`MIKOSHI_RETINA_LEGACY_DIR=/verified/source python tools/smoke_fullscale_cli.py`

Per-source byte quotas, API authentication and time/phase checks still apply.
Final operation is designed for CPU; benchmark is hardware/environment specific.
