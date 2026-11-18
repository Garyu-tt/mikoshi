# R185 in a single Mikoshi nervous-system branch

Two distinct protocols retain their separate provenance:

1. User report (18 November 2026): side ankle drive, torque around Z
   at -2, 0, +2 N*m, final rightward velocity 0.174, 0.042,
   -0.086 m/s respectively, with both feet reported in contact
   through 90 frames. These results are not independently replayed.
2. Historical QA (17 October 2026): a surrogate contact-body
   mechanics experiment for X actuation. Original QA_R185.json
   and QA_R185_PHYSICS.json were read on mirbi-linux and SHA-pinned.
   It did not prove Z actuation or autonomous balance learning.

Both are searchable read-only research reports through discovered actions.
No physical motor control or spinal closed loop has been enabled.
The motor nerve, eyes and brain remain parts of one versioned API/graph.

## Original R239 neural continuity test

On the old source host in isolated NumPy 2.3.5 environment,
`/tmp/mikoshi-r09-true-state-verify.py` captured real R239 typed
numeric buffers as ZIP, restored into a second original instance,
and compared 13 continuation phases following 7 saved phases.
All 1,083 optic spikes matched byte-for-byte and final numeric
buffers matched. This is evidence for complete dynamic-state
continuity, not yet an integration pass of the exact R08 Engram v2 code.
