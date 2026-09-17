# Discovery artifact contract

This optional contract adds a discovery prelude; it does not replace the existing feature triplet or delivery reports. Python 3.10+ is required for the shipped helper. All paths below are consumer-repository paths. Keep manifests and authored documents in Git; keep worker transport reports in ignored Foreman runtime storage.

## Bundle and identities

Use `docs/discovery/DISC-NNN/manifest.json` and `discovery.md`. Nodes reference Markdown files, usually sources in that directory, scenarios under `scenarios/`, decisions under `docs/decisions/`, and existing product/architecture documents. A node carries `id`, `kind`, `title`, `path`, and `sha256` of its exact bytes. IDs and canonical paths must not collide across bundles. Shared context may reference the same ID/path; copied editable definitions are forbidden. Source/scenario/decision IDs use SRC/SC/DEC prefixes. Cross-feature FR/AC references use qualified IDs such as `FEAT-001-FR-001`.

The manifest contains:

```json
{
  "schema_version": 1,
  "id": "DISC-001",
  "title": "Export filtered records",
  "goal": "Let a user take the selected records into another tool.",
  "scope": "CSV download; scheduled delivery is excluded.",
  "state": "discussing",
  "nodes": [],
  "links": [],
  "questions": [],
  "tracker": {"mode": "local", "repository": null, "issue": null},
  "reviews": {},
  "acceptance": null
}
```

This example is a draft skeleton, not a review-ready artifact. Include discovery.md itself as a context node so changes to its decisions or boundaries invalidate the revision. The content revision hashes schema version, ID, title, goal, scope, ordered nodes, links, and questions. Each file hash is validated against its bytes. State, tracker bookkeeping, reviews, and acceptance are excluded to avoid self-referential approval hashes. Changes to the reviewed inventory or linked context require refreshing its node and repeating the affected review; do not silently approve a new digest.

Allowed kinds: source, scenario, decision, context, requirement, criterion. Each link has `from`, `relation`, `to`. Relations: derived-from, decided-by, depends-on, extends, duplicates, alternative-to, conflicts-with, replaces, supersedes, satisfies. Every review-ready scenario must have a provenance path to a source through derived-from/decided-by/supersedes edges. Product Review checks whether links are true and complete.

Questions have `id`, `text`, boolean `blocking`, and boolean `resolved`. Resolved questions also have `resolution` and `source`. Nonblocking assumptions remain visible; a question affecting observable behavior is blocking unless its uncertainty was explicitly accepted and represented honestly.

States: draft, discussing, ready_for_confirmation, accepted, deferred, cancelled. These are discovery maturity, not feature implementation status. Preserve Git history on every revision. Decisions retain alternatives, each agent's position, the operator's choice/source, and supersession rather than erasing rejected alternatives.

## Independent reports and acceptance

Persist each review at `reports/reviews/<unique-review-id>/report.json`; never overwrite an earlier completed report. `reviews.product` and `reviews.trace` reference that report's repository-relative `path` and `sha256`. Each report contains:

```json
{
  "discovery": "DISC-001",
  "role": "product",
  "revision": "<content digest>",
  "reviewer": "<attributed independent worker identity>",
  "outcome": "pass",
  "findings": [],
  "summary": "<checks performed and evidence>",
  "inputs_commit": "<full snapshot SHA>"
}
```

Role is product or trace. Outcome is pass, changes_requested, or blocked. Findings have stable `id`, `state` (open/resolved), `owner`, `claim`, `evidence`, and `closure_condition`. Every finding, including view defects, blocks confirmation until resolved with evidence. All later reports retain references to prior findings; an empty findings list must not silently discard outstanding findings.

Acceptance contains `revision`, `actor`, `source`, `quote`, and `recorded_at`. Foreman verifies the source against the live operator answer or previously attributed checkpoint. Neither a file nor the validator authenticates the operator. GitHub comments require verified authorship; a quoted comment embedded in another comment is not confirmation. A chat source may use an attributed session/message locator and saved excerpt without inventing a URL.

## Deterministic gates

- `check --gate draft`: structural integrity and exact file hashes.
- `check --gate review`: additionally source lineage, at least one scenario, active state, no blocking questions.
- `check --gate confirm`: additionally current independent product and trace pass reports, no open findings.
- `check --gate accepted`: additionally accepted state, current attributed approval fields, and a positive feature issue mapping in GitHub mode.
- `handoff --commit <SHA>`: accepted gate plus exact committed manifest, node, and review-report bytes. Returns the canonical source, SHA, content revision, scenario IDs, and tracker mapping. The caller still verifies approval attribution, reviewer independence, and live GitHub identity.

`render --output trace/DISC-NNN/<revision>/<view-id>` produces `index.json`, `graph.mmd`, and a self-contained searchable `index.html` with escaped source snapshots and bidirectional links. Preserve prior revisions. Rendering never records a passing review. Local file previews need no hosted service. Hosted HTML and a portfolio-wide navigator are later extensions; this delivery provides one complete feature graph.

## Worker return

The discovery prelude uses a separate JSON report rather than changing existing Spec/Review reports. Required fields:

```json
{
  "schema_version": 1,
  "assignment_id": "<assigned ID>",
  "worker_id": "<current physical identity>",
  "role": "discover",
  "status": "done",
  "discovery": "DISC-001",
  "manifest": "docs/discovery/DISC-001/manifest.json",
  "commit": "<full SHA>",
  "revision": "<content digest>",
  "artifacts": [],
  "open_findings": [],
  "question": null,
  "next": "product_review"
}
```

Role is discover, product_review, or trace. Status is done, waiting_user, changes_requested, blocked, or prepared. `artifacts` contains path/hash references; reviewer results include their durable report reference. `question` names a missing decision or authority and its source. `prepared` names exact proposed outward operations; it never means they succeeded. `next` is advisory; only the prelude's transition rules route work. Reviewers report their isolated output commit when applicable; the reviewed input SHA is also recorded in the durable review. Foreman verifies the assignment envelope and target rather than accepting a producer's claimed next stage.

`return-check <report> --assignment <expected-envelope>` validates attributed worker fields and output hashes before routing. The expected envelope must come from Foreman's checkpoint, not the producer. For isolated review worktrees, Foreman passes `--coordination-root <main-checkout>` for report/envelope paths and `--root <reviewer-worktree>` for artifact paths; both are trusted assignment inputs. Paths must remain relative to their corresponding root, and containment applies independently to each root. `spec-adoption` prepares the same-issue Spec block using a complete normalized inventory; it never creates an issue.

## Handoff ownership

Spec reads `references/discovery-intake.md` in its own skill. Discovery is historical lineage after handoff. Spec owns current requirements, design, task definitions, and scenario behavior; amend original scenario files without renumbering or copying them. New product meaning requires a new decision and operator confirmation. Existing accepted snapshots remain available at their recorded commits. A later source amendment is explicit work, not evidence that the old handoff never occurred.
