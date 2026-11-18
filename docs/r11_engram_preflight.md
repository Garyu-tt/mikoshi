# R11: Engram integrity and anatomical identity

R239 checkpoint verification is split into fully typed decode, independent
preflight and commit. Full preflight validates original source hashes,
retinal geometry, complete buffer inventory, checksums, clock coherence,
body ID and immutable anatomy.

Anatomical arrays may be serialized for reproducibility, but cannot replace
the original pinned neuronal or photoreceptor mosaic with synthetic identities.
The intended vision remains a real binocular retina with 8x8 sparse sampling.

`engram.retina.r239.preflight` validates a file against a **fresh temporary**
retina with exactly the same source pins; the active instance remains untouched.
There is no device output or fake motor control.

Prior remote original R239 numeric ZIP test and 20-phase spike test remain
valid evidence, **not** proof that stock R11 Engram v2 has been run on
the historical source host. The integration script can run on a trusted
CPU machine with the original pinned source files and NumPy.
