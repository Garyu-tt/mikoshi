"""Verified Engram ZIP. Explicit research vs neural-state semantics."""
import hashlib
import json
import os
import re
import tempfile
import zipfile
from pathlib import Path

VALID = re.compile(r"^[a-zA-Z0-9_.-]{1,100}$")
MAX_ENTRY = 1024 * 1024 * 512


def verify(path):
    path = Path(path)
    if not path.is_file() or path.suffix != ".engram":
        raise ValueError("Engram not found")
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        if len(set(names)) != len(names) or "manifest.json" not in names:
            raise ValueError("Engram duplicate entry or missing manifest")
        if any(n.startswith("/") or ".." in Path(n).parts or "\\" in n for n in names):
            raise ValueError("Unsafe Engram path")
        if sum(i.file_size for i in z.infolist()) > MAX_ENTRY:
            raise ValueError("Engram exceeds quota")
        manifest = json.loads(z.read("manifest.json"))
        if manifest.get("format") != "mikoshi-engram.v1":
            raise ValueError("Unsupported Engram format")
        blobs = manifest.get("blobs")
        if not isinstance(blobs, list):
            raise ValueError("Missing blob inventory")
        if set(names) != {"manifest.json"} | {x["name"] for x in blobs}:
            raise ValueError("Blob inventory does not match archive")
        for row in blobs:
            data = z.read(row["name"])
            if len(data) != row["bytes"] or hashlib.sha256(data).hexdigest() != row["sha256"]:
                raise ValueError("Corrupt Engram blob: " + row["name"])
        kind = manifest.get('kind')
        if kind not in ('research', 'specimen', 'retina-specimen'):
            raise ValueError('Unknown Engram kind')
        if kind == 'research' and any(n.startswith('neural/') for n in names):
            raise ValueError('Research Engram cannot contain neural-state claims')
        if kind == 'specimen':
            state_path = 'neural/connectome_state.json'
            source_path = 'neural/connectome_source.json'
            if state_path not in names or source_path not in names:
                raise ValueError('Specimen requires actual topology and checkpoint')
            state = json.loads(z.read(state_path))
            if not isinstance(state, dict) or state.get('schema') != 'mikoshi.connectome-state.v1':
                raise ValueError('Unsupported executable state schema')
            if state.get('source_sha256') != hashlib.sha256(z.read(source_path)).hexdigest():
                raise ValueError('Neural-state topology does not match source')
        if kind == 'retina-specimen':
            from server.engram_retina import verify as verify_retina
            verify_retina(z, set(names)-{'manifest.json'})
        return {"valid": True, "kind": manifest["kind"],
                "blobs": len(blobs), "identity": manifest.get("identity"),
                "state_present": any(x["name"].startswith("neural/") for x in blobs)}


def create(path, blobs, kind="research", identity=None):
    path = Path(path)
    if path.suffix != ".engram" or kind not in ("research", "specimen", "retina-specimen"):
        raise ValueError("Invalid Engram kind/name")
    if not isinstance(blobs, dict) or not blobs:
        raise ValueError("Engram must include actual blobs")
    if kind in ('specimen', 'retina-specimen') and not any(x.startswith('neural/') for x in blobs):
        raise ValueError("Specimen requires actual neural state")
    entries = []
    for name, content in sorted(blobs.items()):
        if (not isinstance(content, bytes) or not name or name.startswith("/") or
            "\\" in name or ".." in Path(name).parts or name == "manifest.json"):
            raise ValueError("Invalid blob entry")
        entries.append({"name": name, "bytes": len(content),
                        "sha256": hashlib.sha256(content).hexdigest()})
    manifest = {"format": "mikoshi-engram.v1", "kind": kind,
                "identity": identity, "blobs": entries}
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, tmpname = tempfile.mkstemp(prefix='.engram-',suffix='.pending.engram',dir=path.parent)
    tmp = Path(tmpname)
    try:
        with os.fdopen(handle, 'wb') as out:
            with zipfile.ZipFile(out, 'w',
                                 compression=zipfile.ZIP_DEFLATED if kind == 'retina-specimen'
                                 else zipfile.ZIP_STORED, compresslevel=4) as z:
                z.writestr('manifest.json', json.dumps(manifest, sort_keys=True))
                for name, content in sorted(blobs.items()):
                    z.writestr(name, content)
            out.flush()
            os.fsync(out.fileno())
        verify(tmp)
        os.link(tmp, path)  # Atomic create-only; never silently overwrite an Engram.
    finally:
        tmp.unlink(missing_ok=True)
    return path
