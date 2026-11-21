# CYCLON Twins R0 · CPU-first research prototype

## What works now

- Two recurrent byte-level **toy agents** with a single shared NumPy backbone.
- Distinct hidden states, output-to-input feedback, separate low-rank adapters.
- Synchronous peer-state exchange at each bounded compute step.
- One-step next-byte online gradient updates, diagnostic counters, budget limits.
- GitHub history metadata indexer for a project-lifecycle curriculum.
- Optional Mikoshi module manifest, **disabled**, with no advertised actions.

**This is not an 80B model, not a chatbot, and not a pretrained GitHub programmer.** R0 consists of ~30K parameters at the default dimensions. Tests establish only toy recurrent learning and separate state. No production Mikoshi integration or server deployment has been verified.

## Target architecture (not yet implemented)

Two logical CYCLON-80B agents share one quantized, pretrained 80B base model and have independent LoRA/adapters, contexts, memories, tool permissions, GitHub worktrees, and training curricula. They exchange messages asynchronously through a bounded queue with versioned event IDs and causal history. Each model's output may re-enter its input as additional reasoning, subject to compute/time/token limits and explicit stop/idle policies.

This is **two agents sharing a single 80B parameter tensor**, not two separate 80B weight sets. Separate training of two complete 80B models is outside the Mikoshi budget. Keep the architecture honest: shared weights imply correlated errors, and low-bit weights do not prove low latency or trainability.

## Hardware envelope

Mikoshi target: 2x E5-2680 v4, 128GB RAM, 7x P106-100 6GB. Verify actual availability, CUDA/drivers, power stability and system headroom before enabling a real backbone.

- One 80B Q4 backbone: theoretical 40GB decimal for weights, excluding scales, activation/KV cache, allocator, model metadata, OS and offload buffers.
- One 80B Q2 backbone: theoretical 20GB decimal weights but unproven accuracy and missing runtime support.
- Two separate Q4 80B backbones: theoretical 80GB weights before overhead, substantially higher bandwidth/compute.
- 7x6GB GPUs do not form transparent 42GB VRAM; distribution/offload requires explicit runtime support and communication overhead.
- BitWare/BitWeave is **benchmark code**, not a drop-in inference backend. Validate end-to-end tokens/s and quantization error before adopting.
- Low idle CPU budget: event-driven scheduler and sleep/heartbeat, **not** continuous high-cost inference loops.

## GitHub-first curriculum

Teach CYCLON to run a project from idea through issues, branching, commits, tests, review, releases and regression support. Real repositories: karpathy/nanoGPT, karpathy/nanochat, karpathy/llm.c, Lightning-AI/litgpt, allenai/OLMo.

Index issues, PR metadata, commits and releases chronologically. Each lesson gives a point-in-time issue and a repository snapshot **at or before** the issue; ask the student for plan, patch, tests, review, release notes. Evaluate with tests + independent held-out reviewer. Do not show future commits/PR solutions during the attempt. Split by time **and by repository** for generalization. Titles/metadata alone are not a complete training dataset. Verify licenses and redistribution terms before using code and texts for actual model training.

Never execute untrusted GitHub repository code automatically. Run candidate tests in isolated throwaway environments, with bounded CPU/RAM/time, restricted networking and credentials. Never provide production secrets to training agents. Human approves irreversible repository or deployment operations.

## Commands

```sh
python -m pip install 'numpy>=2.1,<3'
PYTHONPATH=. python -m unittest tests.test_cyclon_r0 -v
PYTHONPATH=. python tools/cyclon_demo.py
python tools/cyclon_github_curriculum.py --repo karpathy/nanochat --limit 20 \
  --output runs/github-events.jsonl
```

The dataset script makes **read-only requests** to GitHub REST API and saves bounded event metadata only. `GH_TOKEN` is optional and is never emitted. `--cutoff` selects chronological evaluation split; archived issue state is **not** historical state and must not be given as a label to past-time prompts. Use point-in-time Git trees and history for faithful replay.

## Next implementation gates

1. Validate Mikoshi node remotely; preserve existing running services.
2. Choose or load an appropriately licensed base model that is proven to fit and generate on the actual host.
3. Implement backend interface (prompt/response/adapter/kv state), bounded dual-agent scheduler and stop controls; benchmark single vs twins.
4. Test BitWeave adapters only for supported matrix shapes and correctness against baseline, with fallbacks.
5. Add GitHub tool permissions, issue-driven worktrees, CI checks, safe feedback and versioned Engram snapshots.
6. Scale only after quality and power/throughput budgets are demonstrated.
