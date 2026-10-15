# SPDX-License-Identifier: MPL-2.0
"""Mikoshi Children: one local individual and one active runtime per OS user.

Experimental reference simulation, NOT the private Mikoshi neural engine.
"""
from __future__ import annotations

import argparse
import contextlib
import json
import os
from pathlib import Path
import random
import sqlite3
import sys
import time
from datetime import datetime, timezone

APP_NAME = "mikoshi-children"
MAX_INDIVIDUALS = 1
NEURONS = 16


class AlreadyRunning(RuntimeError):
    pass


def default_home() -> Path:
    # Fixed per-user location: changing the working directory cannot bypass the lock.
    if os.name == "nt":
        root = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
    else:
        root = Path(os.environ.get("XDG_STATE_HOME") or Path.home() / ".local" / "state")
    return root / APP_NAME


class InstanceLock:
    """Kernel-managed nonblocking lock, released on process exit/crash."""

    def __init__(self, path: Path):
        self.path = path
        self.file = None

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.file = self.path.open("a+b")
        try:
            self.file.seek(0)
            if os.name == "nt":
                import msvcrt
                self.file.seek(0, 2)
                if self.file.tell() == 0:
                    self.file.write(b"0")
                    self.file.flush()
                self.file.seek(0)
                msvcrt.locking(self.file.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            self.file.close()
            self.file = None
            raise AlreadyRunning("Mikoshi Children is already running for this user") from exc
        return self

    def __exit__(self, *_):
        if self.file is None:
            return
        try:
            if os.name == "nt":
                import msvcrt
                self.file.seek(0)
                msvcrt.locking(self.file.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.file.fileno(), fcntl.LOCK_UN)
        finally:
            self.file.close()
            self.file = None


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(db_path)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA busy_timeout=5000")
    db.execute("""
        CREATE TABLE IF NOT EXISTS individual (
            slot INTEGER PRIMARY KEY CHECK (slot = 1),
            uid TEXT NOT NULL UNIQUE,
            generation INTEGER NOT NULL CHECK (generation = 0),
            created_at TEXT NOT NULL,
            ticks INTEGER NOT NULL DEFAULT 0,
            membrane TEXT NOT NULL
        )
    """)
    db.commit()
    return db


def create_individual(db: sqlite3.Connection, uid: str = "child-001") -> dict:
    # SQLite guarantees only one individual even if the application lock is bypassed.
    now = datetime.now(timezone.utc).isoformat()
    membrane = json.dumps([0.0] * NEURONS)
    try:
        with db:
            db.execute(
                "INSERT INTO individual (slot,uid,generation,created_at,membrane) VALUES (1,?,0,?,?)",
                (uid, now, membrane),
            )
    except sqlite3.IntegrityError as exc:
        raise ValueError("Children permits one permanent individual; an individual already exists") from exc
    return snapshot(db)


def snapshot(db: sqlite3.Connection) -> dict | None:
    row = db.execute(
        "SELECT uid,generation,created_at,ticks,membrane FROM individual WHERE slot=1"
    ).fetchone()
    if not row:
        return None
    return {
        "uid": row[0], "generation": row[1], "created_at": row[2],
        "ticks": row[3], "neurons": NEURONS, "membrane": json.loads(row[4]),
        "population_limit": MAX_INDIVIDUALS,
    }


def tick(db: sqlite3.Connection, stimulus: float = 0.0) -> dict:
    """Tiny deterministic leaky/integrate/fire demo, not a biological connectome."""
    if not -1.0 <= stimulus <= 1.0:
        raise ValueError("stimulus must be within [-1, 1]")
    state = snapshot(db)
    if state is None:
        raise RuntimeError("No individual exists")
    old = state["membrane"]
    n = state["ticks"]
    new = []
    spikes = 0
    for i, voltage in enumerate(old):
        upstream = old[(i - 1) % NEURONS]
        drive = stimulus if i == 0 else max(0.0, upstream) * 0.22
        value = voltage * 0.91 + drive + (0.015 if (n + i) % 17 == 0 else 0.0)
        if value >= 1.0:
            spikes += 1
            value = 0.0
        new.append(round(value, 6))
    with db:
        db.execute(
            "UPDATE individual SET ticks=ticks+1,membrane=? WHERE slot=1",
            (json.dumps(new),),
        )
    result = snapshot(db)
    result["spikes_last_tick"] = spikes
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Mikoshi Children single-agent demo")
    parser.add_argument("command", nargs="?", choices=["run", "status", "init"], default="run")
    parser.add_argument("--interval", type=float, default=0.1, help="simulation tick seconds")
    parser.add_argument("--stimulus", type=float, default=0.0)
    args = parser.parse_args(argv)
    if args.interval <= 0:
        parser.error("--interval must be positive")
    home = default_home()
    try:
        # All commands take the same instance lock.
        with InstanceLock(home / "instance.lock"):
            with contextlib.closing(connect(home / "individual.sqlite3")) as db:
                if args.command == "init":
                    print(json.dumps(create_individual(db), ensure_ascii=False))
                elif args.command == "status":
                    print(json.dumps(snapshot(db), ensure_ascii=False))
                else:
                    if snapshot(db) is None:
                        create_individual(db)
                    print("Mikoshi Children active. Ctrl+C stops cleanly.", flush=True)
                    while True:
                        tick(db, args.stimulus)
                        time.sleep(args.interval)
    except AlreadyRunning as exc:
        print(str(exc), file=sys.stderr)
        return 3
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("\nStopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
