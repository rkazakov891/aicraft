#!/usr/bin/env python3
"""Exercise native-identity bootstrap and measured checkpoint behavior."""

from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
SCRIPT = Path(__file__).resolve().parents[2] / "plugins/aicraft/skills/aicraft-foreman/scripts/runtime.py"
spec = importlib.util.spec_from_file_location("runtime", SCRIPT)
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.record = self.root / "bootstrap.json"
        self.calls = []

    def agent(self, session=None, **changes):
        info = {"name": "worker", "pane_id": "w1:p2", "cwd": str(self.root),
                "terminal_id": "terminal-one", "agent": "codex", "agent_status": "idle"}
        if session:
            info["agent_session"] = {"kind": "id", "value": session}
        info.update(changes)
        return (0, {"result": {"agent": info}})

    def invoke(self, *responses):
        queue = iter(responses)
        def call(args):
            self.calls.append(args)
            return next(queue)
        return call

    def test_first_turn_initializes_native_identity_without_product_work(self):
        invoke = self.invoke(self.agent(), (0, {"result": {}}), self.agent("native-session"))
        result = r.bootstrap("worker", "w1:p2", self.root, self.record, invoke)
        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["agent_session"]["value"], "native-session")
        self.assertEqual(self.calls[1][3], r.BOOTSTRAP_PROMPT)
        self.assertEqual(len([c for c in self.calls if c[1] == "prompt"]), 1)

    def test_existing_native_identity_needs_no_bootstrap_turn(self):
        result = r.bootstrap("worker", "w1:p2", self.root, self.record, self.invoke(self.agent("existing")))
        self.assertEqual(result["status"], "ready")
        self.assertEqual(len(self.calls), 1)

    def test_unknown_delivery_is_not_replayed(self):
        invoke = self.invoke(self.agent(), (1, {"error": {"code": "timeout"}}), self.agent())
        self.assertEqual(r.bootstrap("worker", "w1:p2", self.root, self.record, invoke)["status"], "blocked")
        result = r.bootstrap("worker", "w1:p2", self.root, self.record, self.invoke(self.agent()))
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(len([c for c in self.calls if c[1] == "prompt"]), 1)

    def test_running_bootstrap_waits_before_product_dispatch(self):
        invoke = self.invoke(self.agent(), (1, {"error": {"code": "timeout"}}),
                             self.agent("native", agent_status="working"))
        self.assertEqual(r.bootstrap("worker", "w1:p2", self.root, self.record, invoke)["status"], "waiting")
        result = r.bootstrap("worker", "w1:p2", self.root, self.record, self.invoke(self.agent("native")))
        self.assertEqual(result["status"], "ready")

    def test_wrong_occupant_cannot_be_initialized(self):
        with self.assertRaises(ValueError):
            r.bootstrap("worker", "w1:p2", self.root, self.record, self.invoke(self.agent(name="other")))
        self.assertEqual(len(self.calls), 1)

    def test_changed_terminal_after_bootstrap_is_rejected(self):
        invoke = self.invoke(self.agent(), (0, {"result": {}}), self.agent("native", terminal_id="replacement"))
        with self.assertRaisesRegex(ValueError, "occupant changed"):
            r.bootstrap("worker", "w1:p2", self.root, self.record, invoke)

    def test_clock_events_preserve_measured_order(self):
        before = datetime.now(timezone.utc)
        log = self.root / "events.jsonl"
        first = r.event(log, "dispatch", {"assignment": "A-001"})
        second = r.event(log, "return", {"assignment": "A-001"})
        after = datetime.now(timezone.utc)
        self.assertLessEqual(before, datetime.fromisoformat(first["observed_at"]))
        self.assertLessEqual(datetime.fromisoformat(second["observed_at"]), after)
        self.assertLessEqual(datetime.fromisoformat(first["observed_at"]), datetime.fromisoformat(second["observed_at"]))
        self.assertEqual([json.loads(line)["event"] for line in log.read_text().splitlines()], ["dispatch", "return"])


if __name__ == "__main__":
    unittest.main()
