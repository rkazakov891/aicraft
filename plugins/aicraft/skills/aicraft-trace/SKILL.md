---
name: aicraft-trace
description: Validate provenance and revision-bound links in a Discovery bundle, generate Mermaid and a searchable HTML navigator, and report missing or contradictory traceability. Use at Discovery gates and its Spec handoff; broader release/test tracing is not implemented by this first slice.
---

# aicraft-trace

Never replay another AiCraft skill's report. Omit unrelated prior state. When relevant prior state is necessary, summarize it in one prose paragraph containing only the prior outcome, exact target, relevant blocker or handoff, and one suggested next action. The suggested action is advisory and grants no authority.

Read root `AGENTS.md`, [the artifact contract](../aicraft-discover/references/artifacts.md), and the assigned manifest and snapshot. Work independently from the source author. Under Herdr use spec_review settings with a fresh identity; never share the producer's conversation.

1. Verify the repository, input commit, and current content revision. Run `python3 <discover-skill-dir>/scripts/discovery.py check <manifest> --root <repository> --gate review`. Mechanical failure blocks the affected gate; do not repair source data or bless an incomplete graph.
2. Inspect whether declared source/scenario/decision links are true and complete. Check repository-wide IDs, canonical paths, decision supersession, original user intent, unresolved alternatives, and the difference between planned and delivered behavior. Verify the input includes the capability context used by Product Review. A valid ID does not establish semantic coverage.
3. Run `render` into `trace/<DISC-ID>/<content-revision>/<view-id>/`. Inspect the index, Mermaid, and HTML. Confirm labels, links, source text, and revision are correct and usable. Include presentation defects as findings. Never embed secrets or sensitive source excerpts in published output; a required redaction is resolved at the source owner/publication boundary, not by silently altering evidence.
4. Write the durable trace report using the shared contract, with stable finding IDs, owners, evidence, closure conditions, and exact generated artifact hashes. A structural pass alone is not a semantic pass. Do not record a pass while any finding is open.
5. Return the worker envelope and review artifact. Foreman routes source findings to their owners. Fix only generated representations or their generator. On recheck, verify each prior finding and reject results for superseded revisions.

Parallel review requires a separate snapshot worktree. Read product sources without modification and write only assigned report/view outputs. A reviewer output commit is distinct from the input commit. Publishing those outputs is serialized by the assigned artifact owner after confirming that input nodes have not changed. On a shared checkout, run serially.

The helper produces a feature-level navigator and graph. Do not claim a portfolio-wide graph, implementation status, test coverage, GitHub synchronization, or release acceptance that this slice does not yet verify.
