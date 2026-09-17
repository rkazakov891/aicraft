#!/usr/bin/env python3
"""Measured runtime events and bounded native-session bootstrap for Herdr."""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys


BOOTSTRAP_PROMPT = (
    "Runtime identity initialization only. Reply READY. Do not use tools, read or write files, "
    "run commands, start agents, or perform product work. A separate assignment will follow."
)


def event(path, name, data=None):
    record = {"observed_at": datetime.now(timezone.utc).isoformat(),
              "event": name, "data": data or {}}
    path.parent.mkdir(parents=True, exist_ok=True)
    # Foreman is the sole writer under its project lease. One append preserves prior observations.
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, sort_keys=True) + "\n")
    return record


def call(args):
    result = subprocess.run(["herdr", *args], capture_output=True, text=True, timeout=35)
    payload = result.stdout.strip() or result.stderr.strip()
    try:
        parsed = json.loads(payload)
    except json.JSONDecodeError:
        raise ValueError("Herdr returned non-JSON output") from None
    return result.returncode, parsed


def observe(agent, pane, cwd, invoke):
    code, response = invoke(["agent", "get", agent])
    if code:
        raise ValueError("cannot resolve the recorded agent")
    info = response["result"]["agent"]
    if (info.get("name") != agent or info.get("pane_id") != pane or
            Path(info.get("foreground_cwd") or info.get("cwd", "")).resolve() != cwd.resolve()):
        raise ValueError("agent, pane, or cwd changed")
    if not info.get("terminal_id"):
        raise ValueError("missing physical terminal identity")
    return info


def bootstrap(agent, pane, cwd, record_path, invoke=call):
    info = observe(agent, pane, cwd, invoke)
    record = None
    if record_path.exists():
        record = json.loads(record_path.read_text())
        if (record.get("agent") != agent or record.get("pane") != pane or
                record.get("terminal") != info["terminal_id"]):
            raise ValueError("bootstrap record belongs to a different occupant")
    session = info.get("agent_session")
    if session and session.get("value"):
        if info.get("agent_status") not in {"idle", "done"}:
            return {"status": "waiting", "reason": "native session exists but worker is not settled"}
        return {"status": "ready", "agent_session": session, "terminal_id": info["terminal_id"]}
    if info.get("agent") != "codex" or info.get("agent_status") not in {"idle", "done"}:
        return {"status": "blocked", "reason": "identity missing on a worker that cannot bootstrap"}
    if record is not None:
        return {"status": "blocked", "reason": "bootstrap already submitted; never resend unknown delivery"}
    record_path.parent.mkdir(parents=True, exist_ok=True)
    record = {"agent": agent, "pane": pane, "terminal": info["terminal_id"],
              "observed_at": datetime.now(timezone.utc).isoformat(), "phase": "submission-recorded"}
    with record_path.open("x", encoding="utf-8") as stream:
        json.dump(record, stream, indent=2)
    # No business instruction or artifact authority is included in this first turn.
    code, returned = invoke(["agent", "prompt", agent, BOOTSTRAP_PROMPT, "--wait", "--timeout", "20000"])
    record.update({"returncode": code, "transport_return": returned})
    record_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    current = observe(agent, pane, cwd, invoke)
    if current["terminal_id"] != info["terminal_id"]:
        raise ValueError("occupant changed during bootstrap")
    session = current.get("agent_session")
    if not session or not session.get("value"):
        return {"status": "blocked", "reason": "no native session identity after bootstrap"}
    if current.get("agent_status") not in {"idle", "done"}:
        return {"status": "waiting", "reason": "bootstrap has not settled", "agent_session": session}
    return {"status": "ready", "agent_session": session, "terminal_id": current["terminal_id"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    stamp = sub.add_parser("event")
    stamp.add_argument("log", type=Path)
    stamp.add_argument("name")
    stamp.add_argument("--data", type=Path)
    boot = sub.add_parser("bootstrap")
    boot.add_argument("agent")
    boot.add_argument("--pane", required=True)
    boot.add_argument("--cwd", required=True, type=Path)
    boot.add_argument("--record", required=True, type=Path)
    args = parser.parse_args()
    try:
        if args.command == "event":
            data = json.loads(args.data.read_text()) if args.data else None
            result = event(args.log, args.name, data)
        else:
            if os.environ.get("HERDR_ENV") != "1":
                raise ValueError("bootstrap must run inside the controller's Herdr session")
            result = bootstrap(args.agent, args.pane, args.cwd, args.record)
        print(json.dumps(result))
        return 1 if result.get("status") == "blocked" else 0
    except (OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired) as exc:
        print(json.dumps({"status": "blocked", "reason": str(exc)}))
        return 1


if __name__ == "__main__":
    sys.exit(main())
