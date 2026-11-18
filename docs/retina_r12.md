# Mikoshi retina R12: audit and isolated self-test

- Stock R11 `smoke_r239_original.py` was executed against pinned legacy
  R180/R182/R188/R228/R238/R239 sources with NumPy 2.3.5, on mirbi-linux.
- Observed `PASS`: 7 frames before checkpoint, 13 identical post-restore
  phases, 1,083 identical spikes, exact numeric state bytes, 25,979-byte Engram.
- The source host was used **only for QA**, not as the canonical deployment.
- R12 adds `engram.retina.r239.selftest`. This runs an isolated 32x32 original
  retina + Engram v2 roundtrip without mutating the active retina. The status
  is false until the self-test succeeds **in the current runtime process**.
- Selftest stimuli are synthetic light, not a live camera or actual vision.
- Still blocked: production 920x920 performance, camera integration, Z/ankle
  control feedback, R257 stereo, host IAM, VM121 and Windows deployment.
- Run:
  `MIKOSHI_RETINA_LEGACY_DIR=... python -m tools.smoke_r239_selftest_r12`
