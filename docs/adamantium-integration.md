# Recursion contract · R14

The **plugin** is the installable package with lifecycle; a **module** is an independently switchable feature where supported; a **component** is a reusable implementation. Any one may expose a **capability**. Modules and components may contain children recursively without a fixed depth.

- `server/recursive_load.py`: locate/validate nested manifests; organization is a containment tree.
- `server/recursive_resolve.py`: resolve required and optional external capabilities across a directed graph.
- `server/recursive_catalog.py`: persist toggles, project only active providers, isolate unready dependent branches.
- `server/recursive_api.py`: expose real graph, reload, capability resolution and toggles.

All requests route by versioned capability contract rather than concrete plugin name. Root Mikoshi needs only Adamantium Core; other providers are optional. Reload reindexes manifests but **does not hotload Python code**. In-process isolation only; fault isolation across processes is future work.

The client declares host-embeddable integration through `client/plugin.json`, with user-managed tabs and action placement. The 2D retinal, brain and spinal projections share the graph. No 3D brain editor.

No production IAM, public ingress or actual body/retina input is claimed working.
