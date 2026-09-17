# First scenario delivery

This release implements optional Discovery before the existing Spec lifecycle. It ships three skills, a Python standard-library helper, a Foreman prelude, and Spec adoption rules. It does not implement the release/execution planners, full test-design/acceptance pipeline, concurrent implementation, or automatic release merge described in [the target architecture](scenario-delivery.md).

## Start and resume

Use `aicraft-discover` with an idea in ordinary language, or explicitly ask Foreman to coordinate Discovery through Spec. Discover reads the consumer's project context, stores the original request, and develops scenarios with focused questions and alternatives. It resumes an exact Discovery ID rather than allocating another feature on every conversation.

The first meaningful draft can project to a permanent feature issue under the configured tracker and authorized publication scope. GitHub inventory includes closed issues; the same unique marker is reused after a partial failure. Local tracker mode performs no GitHub work. This release prepares deterministic projection bodies but uses the host's GitHub tools for mutations.

Product Review and Trace run on a committed snapshot. Every finding blocks confirmation until resolved. The operator confirms the exact product revision after both pass. A changed scenario or decision invalidates old reviews and acceptance. The helper verifies bytes and references; the coordinator verifies the authenticity of the attributed answer and independent workers.

## Artifacts

| Path | Purpose |
| --- | --- |
| `docs/discovery/DISC-NNN/discovery.md` | Readable goal, scope, sources, scenarios, decisions, and questions |
| `docs/discovery/DISC-NNN/manifest.json` | IDs, typed links, exact file hashes, review references, maturity, acceptance, and issue mapping |
| `scenarios/SC-NNN.md` | Canonical user behavior |
| `docs/decisions/DEC-NNN.md` | Alternatives, positions, attributed choice, and supersession |
| `reports/reviews/<review-id>/report.json` | Durable independent finding/verdict record |
| `trace/DISC-NNN/<revision>/<view-id>/` | Generated index, Mermaid, and local HTML navigator |
| `.aicraft/foreman/<run-id>/` | Ignored assignments, identities, returns, and recovery checkpoints |

Templates and the full consumer contract ship under `aicraft-discover`. Runtime and product IDs are separate. Git owns definitions; GitHub owns work status. Discovery maturity never implies implementation or acceptance of delivered behavior.

## Helper commands

Resolve the installed Discover skill directory as `DISCOVER_SKILL`; examples assume the consumer repository is the current directory:

```sh
python3 "$DISCOVER_SKILL/scripts/discovery.py" check docs/discovery/DISC-001/manifest.json --gate review
python3 "$DISCOVER_SKILL/scripts/discovery.py" revision docs/discovery/DISC-001/manifest.json
python3 "$DISCOVER_SKILL/scripts/discovery.py" render docs/discovery/DISC-001/manifest.json --output trace/DISC-001/review-001
python3 "$DISCOVER_SKILL/scripts/discovery.py" check docs/discovery/DISC-001/manifest.json --gate confirm
python3 "$DISCOVER_SKILL/scripts/discovery.py" handoff docs/discovery/DISC-001/manifest.json --commit HEAD
```

The last command requires accepted and committed input artifacts and reviews. It never manufactures approval. Source changes, stale review targets, unresolved findings, missing lineage, unsafe paths, and unresolved GitHub mappings fail closed. Generated views refuse to overwrite different historical output; use a unique view directory for each reviewed snapshot.

`projection --inventory <path>` accepts a complete normalized issue inventory and returns a create/update/unchanged proposal. It performs no network writes. `return-check <report> --assignment <expected-envelope>` verifies worker attribution, declared status, revision, and file hashes; Foreman still validates commit reachability and semantic gate evidence.

## Spec handoff

Spec uses the manifest path as its single source and records its accepted commit and content revision separately. It adopts the existing issue number, preserves the Discovery block and human history, and adds the normal feature marker. Source/scenario IDs survive. Requirements use EARS patterns and cite scenario/decision sources.

After handoff, Spec owns current scenario behavior. Accepted Discovery remains historical evidence at its recorded commit. Later changes amend the canonical scenarios with explicit decisions; they do not rewrite old reviews or create a competing definition. Existing PRD and quick-task intake remain supported.

## Backend and verification boundaries

The prelude binds Discover to existing `spec` settings, and Product Review/Trace to separate workers using `spec_review` settings. It preserves the existing cross-harness requirement without adding mandatory configuration keys. Independent snapshot worktrees may support concurrent reviews when the runtime can verify their cwd; otherwise dispatch stays serial. This is not parallel implementation support.

The deterministic suite exercises artifact behavior, Git handoffs, interruption/resume identity, issue reconciliation, revision invalidation, and generated output. Agent eval prompts live with the new skills. Passing the script suite does not prove a live Herdr conversation, semantic review quality, or real GitHub publication. Record actual runtime results separately and never claim unexecuted evals passed.
