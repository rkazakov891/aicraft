#!/usr/bin/env python3
"""Exercise actual artifact gates, issue identity, resume, and generated evidence."""

import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "plugins/aicraft/skills/aicraft-discover/scripts/discovery.py"
sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location("discovery", SCRIPT)
d = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d)


class DiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.manifest = "docs/discovery/DISC-001/manifest.json"
        self.bundle = {
            "schema_version": 1, "id": "DISC-001", "title": "Filtered export",
            "goal": "Use selected records offline", "scope": "CSV; no scheduled export",
            "state": "discussing", "nodes": [], "links": [], "questions": [],
            "tracker": {"mode": "local", "repository": None, "issue": None},
            "reviews": {}, "acceptance": None,
        }
        self.node("SRC-001", "source", "docs/discovery/DISC-001/source.md", "Export only selected records.")
        self.node("SC-001", "scenario", "scenarios/SC-001.md", "Select January; download CSV; only January appears.")
        self.node("CTX-001", "context", "docs/discovery/DISC-001/discovery.md", "CSV download, not scheduled export.")
        self.bundle["links"] = [{"from": "SC-001", "relation": "derived-from", "to": "SRC-001"}]

    def write(self, path, text):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        return target

    def node(self, nid, kind, path, text):
        target = self.write(path, text)
        self.bundle["nodes"].append({"id": nid, "kind": kind, "title": nid,
                                      "path": path, "sha256": d.file_hash(target)})

    def review(self, role, findings=None):
        path = f"reports/reviews/{role}/report.json"
        report = {"discovery": self.bundle["id"], "role": role,
                  "revision": d.content_revision(self.bundle), "reviewer": "reviewer-" + role,
                  "outcome": "pass", "findings": findings or []}
        self.write(path, json.dumps(report))
        self.bundle["reviews"][role] = {"path": path, "sha256": d.file_hash(self.root / path)}

    def accept(self):
        self.review("product")
        self.review("trace")
        self.bundle["state"] = "accepted"
        self.bundle["acceptance"] = {"revision": d.content_revision(self.bundle), "actor": "operator",
                                     "source": "session:test/message:4", "quote": "Accept this revision",
                                     "recorded_at": "2026-09-17T12:00:00Z"}

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.root, text=True, capture_output=True, check=True).stdout.strip()

    def test_end_to_end_committed_handoff_and_resume(self):
        self.accept()
        self.write(self.manifest, json.dumps(self.bundle))
        self.git("init", "-q")
        self.git("add", ".")
        self.git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", "fixture")
        cmd = [sys.executable, str(SCRIPT), "handoff", self.manifest, "--root", str(self.root)]
        first = subprocess.run(cmd, capture_output=True, text=True, check=True)
        second = subprocess.run(cmd, capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(first.stdout), json.loads(second.stdout))
        self.assertEqual(json.loads(first.stdout)["scenarios"], ["SC-001"])
        self.write("scenarios/SC-001.md", "Export every record, ignoring filters.")
        self.assertNotEqual(subprocess.run(cmd, capture_output=True).returncode, 0)

    def test_uncommitted_acceptance_cannot_handoff(self):
        self.write(self.manifest, json.dumps(self.bundle))
        self.git("init", "-q")
        self.git("add", ".")
        self.git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", "draft")
        self.accept()
        self.write(self.manifest, json.dumps(self.bundle))
        with self.assertRaisesRegex(d.Invalid, "uncommitted"):
            d.verify_commit(self.root, self.manifest, self.bundle, "HEAD")

    def test_source_mutation_rejects_old_file_hash(self):
        self.accept()
        self.write("scenarios/SC-001.md", "Different behavior")
        with self.assertRaisesRegex(d.Invalid, "changed artifact"):
            d.validate(self.root, self.bundle, "accepted")

    def test_updated_hash_still_invalidates_reviews(self):
        self.accept()
        path = self.write("scenarios/SC-001.md", "Different behavior")
        self.bundle["nodes"][1]["sha256"] = d.file_hash(path)
        with self.assertRaisesRegex(d.Invalid, "stale product"):
            d.validate(self.root, self.bundle, "accepted")

    def test_new_reviews_do_not_renew_operator_acceptance(self):
        self.accept()
        self.bundle["scope"] = "Include scheduled delivery"
        self.review("product")
        self.review("trace")
        with self.assertRaisesRegex(d.Invalid, "stale acceptance"):
            d.validate(self.root, self.bundle, "accepted")

    def test_bookkeeping_does_not_change_product_revision(self):
        original = d.content_revision(self.bundle)
        self.accept()
        self.bundle["tracker"] = {"mode": "github", "repository": "github.com/example/project", "issue": 9}
        self.assertEqual(original, d.validate(self.root, self.bundle, "accepted"))

    def test_open_finding_blocks_even_if_report_says_pass(self):
        self.accept()
        self.review("trace", [{"id": "TRC-001", "state": "open", "evidence": "Broken diagram"}])
        with self.assertRaisesRegex(d.Invalid, "unresolved finding"):
            d.validate(self.root, self.bundle, "confirm")

    def test_missing_provenance_blocks_review(self):
        self.bundle["links"] = []
        with self.assertRaisesRegex(d.Invalid, "no source lineage"):
            d.validate(self.root, self.bundle, "review")

    def test_provenance_cycle_is_not_a_source(self):
        self.bundle["links"] = [
            {"from": "SC-001", "relation": "derived-from", "to": "CTX-001"},
            {"from": "CTX-001", "relation": "derived-from", "to": "SC-001"}]
        with self.assertRaisesRegex(d.Invalid, "no source lineage"):
            d.validate(self.root, self.bundle, "review")

    def test_blocking_question_survives_resume(self):
        self.bundle["questions"] = [{"id": "Q-001", "text": "Who may export?", "blocking": True, "resolved": False}]
        path = self.write(self.manifest, json.dumps(self.bundle))
        resumed = d.read_json(path)
        with self.assertRaisesRegex(d.Invalid, "blocking question"):
            d.validate(self.root, resumed, "review")

    def test_missing_discovery_document_blocks_review(self):
        self.bundle["nodes"].pop()
        with self.assertRaisesRegex(d.Invalid, "Discovery document"):
            d.validate(self.root, self.bundle, "review")

    def test_deferred_work_cannot_enter_spec(self):
        self.accept()
        self.bundle["state"] = "deferred"
        with self.assertRaisesRegex(d.Invalid, "inactive"):
            d.validate(self.root, self.bundle, "accepted")

    def test_unprojected_github_work_cannot_enter_spec(self):
        self.accept()
        self.bundle["tracker"] = {"mode": "github", "repository": "github.com/example/project", "issue": None}
        with self.assertRaisesRegex(d.Invalid, "projection pending"):
            d.validate(self.root, self.bundle, "accepted")

    def inventory(self):
        self.bundle["tracker"] = {"mode": "github", "repository": "github.com/example/project", "issue": None}
        return [{"repository": "github.com/example/project", "number": 42, "state": "closed",
                 "body": "<!-- aicraft:discovery=DISC-001 -->", "is_pull_request": False}]

    def test_closed_issue_is_reused_after_interrupted_mapping_write(self):
        issues = self.inventory()
        self.assertEqual(d.reconcile_issue(self.bundle, issues), 42)
        self.bundle["tracker"]["issue"] = 42
        self.assertEqual(d.reconcile_issue(self.bundle, issues), 42)

    def test_duplicate_marker_never_creates_third_issue(self):
        issues = self.inventory()
        issues.append(dict(issues[0], number=43))
        with self.assertRaisesRegex(d.Invalid, "duplicate"):
            d.reconcile_issue(self.bundle, issues)

    def test_wrong_mapping_and_repository_are_blocked(self):
        issues = self.inventory()
        self.bundle["tracker"]["issue"] = 100
        with self.assertRaisesRegex(d.Invalid, "mapping conflict"):
            d.reconcile_issue(self.bundle, issues)
        issues[0]["repository"] = "github.com/other/project"
        with self.assertRaisesRegex(d.Invalid, "repository mismatch"):
            d.reconcile_issue(self.bundle, issues)

    def test_spec_adopts_original_issue_without_replacing_history(self):
        issues = self.inventory()
        issues[0]["body"] = "Human introduction.\n" + d.issue_body(self.bundle)
        original = issues[0]["body"].rstrip()
        result = d.spec_adoption(self.bundle, issues, "FEAT-001", "specs/001-export/spec.md")
        self.assertEqual(result["spec_issue"], 42)
        self.assertTrue(result["body"].startswith(original))
        self.assertIn("aicraft:feature=FEAT-001", result["body"])
        issues[0]["body"] = result["body"]
        repeated = d.spec_adoption(self.bundle, issues, "FEAT-001", "specs/001-export/spec.md")
        self.assertEqual(repeated["operation"], "unchanged")
        with self.assertRaisesRegex(d.Invalid, "feature marker conflict"):
            d.spec_adoption(self.bundle, issues, "FEAT-002", "specs/002-export/spec.md")

    def test_issue_update_preserves_human_history_and_is_idempotent(self):
        body = d.issue_body(self.bundle, "Human introduction.") + "\nHuman follow-up."
        self.bundle["title"] = "New title"
        updated = d.issue_body(self.bundle, body)
        self.assertTrue(updated.startswith("Human introduction."))
        self.assertTrue(updated.endswith("Human follow-up."))
        self.assertEqual(d.issue_body(self.bundle, updated), updated)

    def test_partial_generated_block_cannot_overwrite_body(self):
        with self.assertRaisesRegex(d.Invalid, "ambiguous"):
            d.issue_body(self.bundle, "Human text <!-- aicraft:discovery-summary:start -->")

    def test_render_escapes_source_and_preserves_links(self):
        self.bundle["title"] = '<script>alert("unsafe")</script>'
        out = self.root / "trace/run-1"
        d.render(self.root, self.bundle, out)
        page = (out / "index.html").read_text()
        self.assertNotIn('<script>alert("unsafe")</script>', page)
        self.assertIn("&lt;script&gt;", page)
        self.assertIn('href="#SRC-001"', page)
        self.assertIn("derived-from", (out / "graph.mmd").read_text())
        self.bundle["title"] = "Changed"
        with self.assertRaisesRegex(d.Invalid, "historical"):
            d.render(self.root, self.bundle, out)

    def test_path_escape_and_symlink_are_rejected(self):
        with self.assertRaises(d.Invalid):
            d.path_in(self.root, "../outside.md")
        (self.root / "escape").symlink_to(self.root.parent)
        with self.assertRaises(d.Invalid):
            d.path_in(self.root, "escape/outside.md")

    def test_duplicate_json_keys_are_rejected(self):
        path = self.write("duplicate.json", '{"id":"one","id":"two"}')
        with self.assertRaisesRegex(d.Invalid, "duplicate JSON"):
            d.read_json(path)

    def test_cross_bundle_identity_collision(self):
        other = copy.deepcopy(self.bundle)
        other["id"] = "DISC-002"
        other["nodes"][1]["path"] = "scenarios/different.md"
        self.write("docs/discovery/DISC-002/manifest.json", json.dumps(other))
        with self.assertRaisesRegex(d.Invalid, "collision"):
            d.validate_inventory(self.root, self.manifest, self.bundle)

    def test_late_worker_and_stale_revision_returns_are_rejected(self):
        expected = {"assignment_id": "A-2", "worker_id": "worker-2", "role": "trace",
                    "discovery": "DISC-001", "manifest": self.manifest, "revision": "new"}
        report = dict(expected, schema_version=1, status="done", artifacts=[self.bundle["nodes"][0]],
                      open_findings=[], commit="a" * 40, question=None)
        self.assertEqual(d.validate_return(self.root, expected, report), "done")
        report["worker_id"] = "worker-1"
        with self.assertRaisesRegex(d.Invalid, "worker_id"):
            d.validate_return(self.root, expected, report)
        report["worker_id"] = "worker-2"
        report["revision"] = "old"
        with self.assertRaisesRegex(d.Invalid, "stale"):
            d.validate_return(self.root, expected, report)


if __name__ == "__main__":
    unittest.main()
