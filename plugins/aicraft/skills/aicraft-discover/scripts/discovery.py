#!/usr/bin/env python3
"""Validate discovery lineage and generate revision-bound navigation using stdlib."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import subprocess
import sys
from pathlib import Path


KINDS = {"source", "scenario", "decision", "context", "requirement", "criterion"}
RELATIONS = {"derived-from", "decided-by", "depends-on", "extends", "duplicates",
             "alternative-to", "conflicts-with", "replaces", "supersedes", "satisfies"}
STATES = {"draft", "discussing", "ready_for_confirmation", "accepted", "deferred", "cancelled"}
ID = re.compile(r"[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+\Z")
PREFIXES = {"source": "SRC-", "scenario": "SC-", "decision": "DEC-"}


class Invalid(ValueError):
    """An artifact cannot support the requested transition."""


def require(condition, message):
    if not condition:
        raise Invalid(message)


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"duplicate JSON key: {key}")
        result[key] = value
    return result


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_object)


def path_in(root, relative):
    require(nonempty(relative), "empty artifact path")
    rel = Path(relative)
    require(not rel.is_absolute() and ".." not in rel.parts, f"unsafe artifact path: {relative}")
    path = root / rel
    require(path.resolve().is_relative_to(root.resolve()), f"artifact escapes repository: {relative}")
    require(relative == rel.as_posix(), f"noncanonical artifact path: {relative}")
    return path


def file_hash(path):
    require(path.is_file(), f"missing file: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False).encode()).hexdigest()


def content_revision(bundle):
    return digest({key: bundle[key] for key in
                   ("schema_version", "id", "title", "goal", "scope", "nodes", "links", "questions")})


def verify_ref(root, ref):
    require(isinstance(ref, dict), "file reference must be an object")
    require(file_hash(path_in(root, ref.get("path"))) == ref.get("sha256"),
            f"changed artifact: {ref.get('path')}")


def review_findings(root, bundle, role, revision):
    review = bundle.get("reviews", {}).get(role)
    require(isinstance(review, dict), f"missing {role} review")
    verify_ref(root, review)
    report = read_json(path_in(root, review["path"]))
    require(report.get("discovery") == bundle["id"] and report.get("role") == role,
            f"wrong target or role in {role} review")
    require(report.get("revision") == revision, f"stale {role} review")
    require(nonempty(report.get("reviewer")), f"missing {role} reviewer identity")
    require(report.get("outcome") == "pass", f"{role} review has not passed")
    findings = report.get("findings")
    require(isinstance(findings, list), f"missing {role} findings")
    seen = set()
    for finding in findings:
        require(isinstance(finding, dict) and nonempty(finding.get("id")), "invalid finding")
        require(finding["id"] not in seen, "duplicate finding ID")
        seen.add(finding["id"])
        require(finding.get("state") == "resolved" and nonempty(finding.get("evidence")),
                f"unresolved finding: {finding['id']}")
    return report


def validate(root, bundle, gate="draft"):
    require(isinstance(bundle, dict) and bundle.get("schema_version") == 1, "unsupported discovery schema")
    require(re.fullmatch(r"DISC-\d{3,}", bundle.get("id", "")) is not None, "invalid Discovery ID")
    for field in ("title", "goal", "scope"):
        require(nonempty(bundle.get(field)), f"missing {field}")
    require(bundle.get("state") in STATES, "invalid discovery state")
    require(isinstance(bundle.get("reviews"), dict), "reviews must be an object")
    require(set(bundle["reviews"]) <= {"product", "trace"}, "unknown review role")
    require(isinstance(bundle.get("nodes"), list), "nodes must be a list")
    nodes = {}
    for node in bundle["nodes"]:
        require(isinstance(node, dict), "node must be an object")
        nid = node.get("id", "")
        require(isinstance(nid, str) and ID.fullmatch(nid), f"invalid node ID: {nid}")
        require(nid not in nodes and nid != bundle["id"], f"duplicate node: {nid}")
        require(node.get("kind") in KINDS and nonempty(node.get("title")), f"invalid node: {nid}")
        prefix = PREFIXES.get(node["kind"])
        require(prefix is None or nid.startswith(prefix), f"wrong ID prefix: {nid}")
        require(node.get("path", "").endswith(".md"), f"node must reference Markdown: {nid}")
        verify_ref(root, node)
        require(path_in(root, node["path"]).read_text(encoding="utf-8").strip(), f"empty node: {nid}")
        nodes[nid] = node
    require(len({n["path"] for n in nodes.values()}) == len(nodes), "multiple IDs reference one editable file")
    require(isinstance(bundle.get("links"), list), "links must be a list")
    edges = set()
    for edge in bundle["links"]:
        require(isinstance(edge, dict), "link must be an object")
        triple = (edge.get("from"), edge.get("relation"), edge.get("to"))
        require(all(isinstance(x, str) for x in triple), "invalid link fields")
        source, relation, target = triple
        require(source in nodes and target in nodes, f"dangling link: {triple}")
        require(source != target and relation in RELATIONS, f"invalid link: {triple}")
        require(triple not in edges, f"duplicate link: {triple}")
        edges.add(triple)
    require(isinstance(bundle.get("questions"), list), "questions must be a list")
    qids = set()
    for question in bundle["questions"]:
        require(isinstance(question, dict) and nonempty(question.get("id")) and
                nonempty(question.get("text")), "invalid question")
        require(question["id"] not in qids, "duplicate question ID")
        qids.add(question["id"])
        require(type(question.get("blocking")) is bool and type(question.get("resolved")) is bool,
                "question flags must be booleans")
        if question["resolved"]:
            require(nonempty(question.get("resolution")) and nonempty(question.get("source")),
                    "resolved question needs resolution and source")
    tracker = bundle.get("tracker")
    require(isinstance(tracker, dict) and tracker.get("mode") in {"local", "github"}, "invalid tracker")
    if tracker["mode"] == "github":
        require(re.fullmatch(r"[A-Za-z0-9.-]+/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+",
                             tracker.get("repository", "")) is not None, "invalid tracker repository")
        require(tracker.get("issue") is None or
                (type(tracker["issue"]) is int and tracker["issue"] > 0), "invalid issue number")
    else:
        require(tracker.get("issue") is None and tracker.get("repository") is None,
                "local tracker must not carry GitHub mapping")
    revision = content_revision(bundle)
    if gate == "draft":
        return revision
    require(bundle["state"] not in {"deferred", "cancelled"}, "inactive discovery")
    require(any(n["kind"] == "source" for n in nodes.values()), "missing original source")
    scenarios = [nid for nid, n in nodes.items() if n["kind"] == "scenario"]
    require(scenarios, "missing user scenario")
    # Every scenario must lead to an original source through provenance links.
    def has_source(nid, visited):
        if nid in visited:
            return False
        if nodes[nid]["kind"] == "source":
            return True
        return any(has_source(t, visited | {nid}) for s, r, t in edges
                   if s == nid and r in {"derived-from", "decided-by", "supersedes"})
    for nid in scenarios:
        require(has_source(nid, set()), f"scenario has no source lineage: {nid}")
    discovery_doc = f"docs/discovery/{bundle['id']}/discovery.md"
    require(any(n["path"] == discovery_doc and n["kind"] == "context" for n in nodes.values()),
            "Discovery document must be included in the revision")
    require(not any(q["blocking"] and not q["resolved"] for q in bundle["questions"]),
            "unresolved blocking question")
    if gate == "review":
        return revision
    for role in ("product", "trace"):
        review_findings(root, bundle, role, revision)
    if gate == "confirm":
        return revision
    require(bundle["state"] == "accepted", "Discovery is not accepted")
    approval = bundle.get("acceptance")
    require(isinstance(approval, dict) and approval.get("revision") == revision, "missing or stale acceptance")
    for field in ("actor", "source", "quote", "recorded_at"):
        require(nonempty(approval.get(field)), f"acceptance lacks {field}")
    if tracker["mode"] == "github":
        require(tracker.get("issue") is not None, "feature issue projection pending")
    return revision


def reconcile_issue(bundle, issues):
    """Pure identity reconciliation over a complete open-and-closed inventory."""
    tracker = bundle["tracker"]
    require(tracker["mode"] == "github", "local mode cannot project to GitHub")
    marker = f"<!-- aicraft:discovery={bundle['id']} -->"
    matches = []
    for issue in issues:
        require(issue.get("repository") == tracker["repository"], "issue inventory repository mismatch")
        if not issue.get("is_pull_request") and marker in issue.get("body", ""):
            require(type(issue.get("number")) is int and issue["number"] > 0, "invalid inventory issue")
            matches.append(issue)
    require(len(matches) <= 1, "duplicate discovery issue markers")
    mapped = tracker.get("issue")
    if mapped is not None:
        require(matches and matches[0]["number"] == mapped, "issue mapping conflict")
    return matches[0]["number"] if matches else None


def issue_body(bundle, previous=""):
    marker = f"<!-- aicraft:discovery={bundle['id']} -->"
    start, end = "<!-- aicraft:discovery-summary:start -->", "<!-- aicraft:discovery-summary:end -->"
    scenarios = [f"- {n['id']}: {n['title']} (`{n['path']}`)" for n in bundle["nodes"] if n["kind"] == "scenario"]
    block = "\n".join([start, marker, f"## {bundle['title']}", "", bundle["goal"], "",
                        "Git owns definitions. This card does not attest implementation or acceptance.",
                        f"Discovery: `{bundle['id']}` · `{bundle['state']}`", "", *scenarios, end])
    if start in previous or end in previous:
        require(previous.count(start) == previous.count(end) == 1 and
                previous.index(start) < previous.index(end), "ambiguous generated issue block")
        a, b = previous.index(start), previous.index(end) + len(end)
        return previous[:a] + block + previous[b:]
    return previous.rstrip() + ("\n\n" if previous else "") + block + "\n"


def spec_adoption(bundle, issues, feature_id, spec_path):
    """Prepare a same-issue Spec mapping without changing Discovery or human text."""
    require(re.fullmatch(r"FEAT-\d{3,}", feature_id), "invalid feature ID")
    require(re.fullmatch(r"specs/\d{3,}-[a-z0-9]+(?:-[a-z0-9]+)*/spec\.md", spec_path),
            "invalid spec path")
    require(spec_path.split("/")[1].split("-")[0] == feature_id.removeprefix("FEAT-"),
            "feature/path identity mismatch")
    number = reconcile_issue(bundle, issues)
    require(number is not None, "Discovery issue must exist before Spec adoption")
    issue = next(i for i in issues if i["number"] == number)
    old = issue["body"]
    markers = re.findall(r"<!-- aicraft:feature=([^\s]+) -->", old)
    require(not markers or markers == [feature_id], "existing feature marker conflict")
    start, end = "<!-- aicraft:spec-summary:start -->", "<!-- aicraft:spec-summary:end -->"
    block = "\n".join([start, f"<!-- aicraft:feature={feature_id} -->", f"Specification: `{spec_path}`", end])
    if start in old or end in old:
        require(old.count(start) == old.count(end) == 1 and old.index(start) < old.index(end),
                "ambiguous Spec summary block")
        body = old[:old.index(start)] + block + old[old.index(end) + len(end):]
    else:
        require(not markers, "unmanaged feature marker requires reconciliation")
        body = old.rstrip() + "\n\n" + block + "\n"
    return {"issue": number, "spec_issue": number, "body": body,
            "operation": "unchanged" if body == old else "update"}


def render(root, bundle, output):
    revision = validate(root, bundle)
    nodes = bundle["nodes"]
    names = {n["id"]: f"n{i}" for i, n in enumerate(nodes)}
    mermaid = ["flowchart LR"]
    for node in nodes:
        # Mermaid labels use validated IDs; free-form text stays in escaped HTML.
        mermaid.append(f'  {names[node["id"]]}["{node["id"]}"]')
    for edge in bundle["links"]:
        mermaid.append(f'  {names[edge["from"]]} -->|{edge["relation"]}| {names[edge["to"]]}')
    cards = []
    for node in nodes:
        links = []
        for edge in bundle["links"]:
            if edge["from"] == node["id"] or edge["to"] == node["id"]:
                other = edge["to"] if edge["from"] == node["id"] else edge["from"]
                links.append(f'<li>{html.escape(edge["from"])} {html.escape(edge["relation"])} '
                             f'{html.escape(edge["to"])} — <a href="#{other}">open {other}</a></li>')
        content = path_in(root, node["path"]).read_text(encoding="utf-8")
        cards.append(f'<article id="{node["id"]}"><h2>{node["id"]}: {html.escape(node["title"])}</h2>'
                     f'<p>{html.escape(node["kind"])} · {html.escape(node["path"])}</p>'
                     f'<ul>{"".join(links)}</ul><details><summary>Source at this revision</summary>'
                     f'<pre>{html.escape(content)}</pre></details></article>')
    page = ('<!doctype html><html lang="en"><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>Discovery trace</title><style>body{font:16px system-ui;max-width:1100px;margin:2rem auto;padding:1rem}'
            'article{border:1px solid #bbb;padding:1rem;margin:1rem 0}pre{white-space:pre-wrap;overflow-wrap:anywhere}'
            'input{padding:.6rem;width:90%}a{color:#1658bb}</style>'
            f'<h1>{html.escape(bundle["title"])}</h1><p>{html.escape(bundle["id"])} · '
            f'{html.escape(bundle["state"])} · Content revision: {revision}</p>'
            '<p>This is a derived snapshot, not a delivery-status or approval record.</p>'
            '<label>Find an artifact <input id="filter" type="search"></label>'
            + "".join(cards) + '<script>const input=document.getElementById("filter");'
            'input.addEventListener("input",()=>{const q=input.value.toLowerCase();'
            'document.querySelectorAll("article").forEach(a=>a.hidden=!a.textContent.toLowerCase().includes(q))});'
            'document.querySelectorAll("a").forEach(a=>a.addEventListener("click",()=>{'
            'input.value="";document.querySelectorAll("article").forEach(n=>n.hidden=false)}));'
            '</script></html>')
    outputs = {"index.html": page, "graph.mmd": "\n".join(mermaid) + "\n",
               "index.json": json.dumps({"discovery": bundle["id"], "revision": revision,
                                          "nodes": nodes, "links": bundle["links"]}, indent=2) + "\n"}
    for name, value in outputs.items():
        target = output / name
        require(target.resolve().is_relative_to(root.resolve()), "generated output escapes repository")
        require(not target.exists() or target.read_text(encoding="utf-8") == value,
                f"refusing to overwrite historical output: {target}")
    output.mkdir(parents=True, exist_ok=True)
    for name, value in outputs.items():
        (output / name).write_text(value, encoding="utf-8")
    return revision


def verify_commit(root, manifest_path, bundle, commit):
    require(commit == "HEAD" or re.fullmatch(r"[0-9a-f]{40,64}", commit), "commit must be HEAD or a full SHA")
    result = subprocess.run(["git", "rev-parse", "--verify", f"{commit}^{{commit}}"], cwd=root,
                            text=True, capture_output=True, check=True)
    sha = result.stdout.strip()
    refs = [manifest_path] + [n["path"] for n in bundle["nodes"]]
    refs += [ref["path"] for ref in bundle.get("reviews", {}).values()]
    for relative in refs:
        data = subprocess.run(["git", "show", f"{sha}:{relative}"], cwd=root,
                              capture_output=True, check=True).stdout
        require(data == path_in(root, relative).read_bytes(), f"uncommitted or changed handoff file: {relative}")
    return sha


def validate_inventory(root, current_path, bundle):
    """Reject cross-bundle identity collisions without invalidating historical hashes."""
    current = path_in(root, current_path).resolve()
    ids = {n["id"]: (n["path"], n["kind"]) for n in bundle["nodes"]}
    paths = {n["path"]: n["id"] for n in bundle["nodes"]}
    for candidate in (root / "docs/discovery").glob("DISC-*/manifest.json"):
        if candidate.resolve() == current:
            continue
        other = read_json(candidate)
        require(other.get("id") != bundle["id"], "duplicate Discovery identity")
        for node in other.get("nodes", []):
            if node["id"] in ids:
                require(ids[node["id"]] == (node["path"], node["kind"]),
                        f"cross-bundle ID collision: {node['id']}")
            if node["path"] in paths:
                require(paths[node["path"]] == node["id"], f"cross-bundle path collision: {node['path']}")


def validate_return(root, expected, report):
    require(report.get("schema_version") == 1, "invalid worker report schema")
    for key in ("assignment_id", "worker_id", "role", "discovery", "manifest"):
        require(nonempty(expected.get(key)) and report.get(key) == expected[key], f"wrong report {key}")
    require(report["role"] in {"discover", "product_review", "trace"}, "invalid report role")
    status = report.get("status")
    require(status in {"done", "waiting_user", "changes_requested", "blocked", "prepared"}, "unknown status")
    require(isinstance(report.get("artifacts"), list) and isinstance(report.get("open_findings"), list),
            "missing report artifacts or findings")
    for ref in report["artifacts"]:
        verify_ref(root, ref)
    if expected.get("revision") is not None:
        require(report.get("revision") == expected["revision"], "stale report revision")
    if status == "done":
        require(not report["open_findings"], "done report has open findings")
        require(report["artifacts"], "done report has no durable output")
        require(re.fullmatch(r"[0-9a-f]{40,64}", report.get("commit", "")), "missing output commit")
    elif status in {"waiting_user", "blocked", "prepared"}:
        require(report.get("question"), "nonterminal report must identify its blocker or prepared operation")
    return status


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("check", "revision", "render", "handoff", "projection", "spec-adoption", "return-check"))
    parser.add_argument("manifest", help="repository-relative discovery manifest")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--gate", choices=("draft", "review", "confirm", "accepted"), default="draft")
    parser.add_argument("--output", help="repository-relative directory for generated views")
    parser.add_argument("--commit", default="HEAD")
    parser.add_argument("--inventory", help="complete normalized issue inventory JSON")
    parser.add_argument("--assignment", help="trusted expected assignment JSON for return-check")
    parser.add_argument("--coordination-root", type=Path, help="Foreman root for return-check report and assignment; artifacts stay under --root")
    parser.add_argument("--feature", help="feature ID for spec-adoption")
    parser.add_argument("--spec-path", help="canonical spec path for spec-adoption")
    args = parser.parse_args(argv)
    try:
        root = args.root.resolve()
        if args.command == "return-check":
            require(args.assignment is not None, "return-check requires --assignment")
            coordination = (args.coordination_root or root).resolve()
            bundle = read_json(path_in(coordination, args.manifest))
            expected = read_json(path_in(coordination, args.assignment))
            status = validate_return(root, expected, bundle)
            print(json.dumps({"status": status, "assignment_id": expected["assignment_id"]}))
            return 0
        require(args.coordination_root is None, "--coordination-root is only valid for return-check")
        bundle = read_json(path_in(root, args.manifest))
        revision = validate(root, bundle, "accepted" if args.command in {"handoff", "spec-adoption"} else args.gate)
        validate_inventory(root, args.manifest, bundle)
        result = {"discovery": bundle["id"], "revision": revision, "gate": args.gate}
        if args.command == "render":
            require(args.output is not None, "render requires --output")
            out = path_in(root, args.output)
            inputs = {path_in(root, args.manifest).resolve()}
            inputs.update(path_in(root, n["path"]).resolve() for n in bundle["nodes"])
            inputs.update(path_in(root, n["path"]).resolve() for n in bundle.get("reviews", {}).values())
            require(not any(p.is_relative_to(out.resolve()) for p in inputs), "output overlaps source artifacts")
            render(root, bundle, out)
        elif args.command == "handoff":
            sha = verify_commit(root, args.manifest, bundle, args.commit)
            result.update({"commit": sha, "source": args.manifest, "tracker": bundle["tracker"],
                           "scenarios": [n["id"] for n in bundle["nodes"] if n["kind"] == "scenario"]})
        elif args.command in {"projection", "spec-adoption"}:
            require(args.inventory is not None, "projection requires complete --inventory")
            inventory = read_json(path_in(root, args.inventory))
            require(inventory.get("complete") is True and inventory.get("includes_closed") is True,
                    "projection requires complete open-and-closed inventory")
            require(inventory.get("repository") == bundle["tracker"].get("repository"), "wrong inventory repository")
            issues = inventory["issues"]
            if args.command == "spec-adoption":
                require(args.feature is not None and args.spec_path is not None,
                        "spec-adoption requires --feature and --spec-path")
                result.update(spec_adoption(bundle, issues, args.feature, args.spec_path))
                result["inventory_digest"] = digest(inventory)
                print(json.dumps(result, indent=2, ensure_ascii=False))
                return 0
            number = reconcile_issue(bundle, issues)
            old = next((i["body"] for i in issues if i["number"] == number), "")
            body = issue_body(bundle, old)
            result.update({"operation": "create" if number is None else "unchanged" if body == old else "update",
                           "issue": number, "body": body, "inventory_digest": digest(inventory)})
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except (Invalid, OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError) as exc:
        print(json.dumps({"status": "blocked", "reason": str(exc)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
