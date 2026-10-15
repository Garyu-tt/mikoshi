# SPDX-License-Identifier: MPL-2.0
import multiprocessing
import sqlite3
import tempfile
import unittest
from pathlib import Path

from mikoshi_children.app import AlreadyRunning, InstanceLock, connect, create_individual, snapshot, tick


def contender(path, queue):
    try:
        with InstanceLock(path):
            queue.put("acquired")
    except AlreadyRunning:
        queue.put("blocked")


class ChildrenTests(unittest.TestCase):
    def test_only_one_individual(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = connect(Path(tmp) / "child.db")
            self.assertEqual(create_individual(db)["uid"], "child-001")
            with self.assertRaises(ValueError):
                create_individual(db, "second")
            self.assertEqual(db.execute("SELECT COUNT(*) FROM individual").fetchone()[0], 1)
            with self.assertRaises(sqlite3.IntegrityError):
                db.execute("INSERT INTO individual(slot,uid,generation,created_at,membrane) VALUES(2,'x',0,'now','[]')")
            self.assertEqual(tick(db, 0.3)["ticks"], 1)
            db.close()
            reopened = connect(Path(tmp) / "child.db")
            self.assertEqual(snapshot(reopened)["ticks"], 1)
            reopened.close()

    def test_lock_blocks_second_process(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "lock"
            ctx = multiprocessing.get_context("spawn")
            queue = ctx.Queue()
            with InstanceLock(path):
                process = ctx.Process(target=contender, args=(path, queue))
                process.start()
                process.join(10)
                self.assertEqual(process.exitcode, 0)
                self.assertEqual(queue.get(timeout=3), "blocked")
            with InstanceLock(path):
                pass


if __name__ == "__main__":
    unittest.main()
