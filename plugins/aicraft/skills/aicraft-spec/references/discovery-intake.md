# Accepted Discovery intake

Load this reference only when the selected source is `docs/discovery/DISC-NNN/manifest.json`, or when an existing feature names that source. Legacy PRD, local document, and quick intake remain unchanged.

## First handoff

Run the Discover helper's `handoff --commit <assigned full SHA>` against the exact committed source and node/report files. Read the accepted scenario documents, source excerpts, decisions, product review, and Trace findings. The helper proves structural/revision consistency; the caller must verify operator acceptance attribution and independent reviewer identity from the trusted assignment or verified prior checkpoint. A file claiming approval is not authority.

Use the manifest path as the one canonical `Sources` entry. Its referenced files are one source bundle, not several competing intake sources. Record `discovery_id`, `discovery_commit`, and `discovery_revision` in `spec.md` frontmatter. Preserve all SC/DEC/SRC IDs and link canonical scenario files from the User scenarios section. Do not copy them into another editable definition.

Compare the source path and Discovery ID with every existing feature before allocation. Resume the unique match, including completed work; never produce another feature from the same Discovery. Several matches are a blocking identity error. Revalidate global source/scenario IDs and repository identity.

The permanent feature issue is already allocated in GitHub mode. Use the helper's read-only `spec-adoption --inventory <complete-inventory> --feature <FEAT-ID> --spec-path <path>` to prepare the same-issue managed block and mapping. Verify its repository, number, non-PR type, and `aicraft:discovery=<ID>` marker. Preserve that number as `spec_issue`. For local mode use null. In the authorized projection, add the normal feature marker and a managed Spec summary to the same issue, retaining Discovery content, human text, and comments. Never create a second issue or self-parent. Any pre-existing feature marker must agree with the selected feature; otherwise stop for reconciliation.

## Contract synthesis

Write functional requirements in EARS patterns using the project's document language: always-active response; when an event occurs; while a state holds; if unwanted behavior occurs, then response; where an optional capability exists. State one observable obligation per requirement. Specify genuine conditions and measurable outcomes without inventing precision, timeouts, or error behavior. EARS is not an executable test language.

Map every requirement and criterion to its SC/DEC sources. `FR-001` remains local to its feature; cross-feature references use the feature ID. Describe concrete test inputs and expected outcomes in the design's test approach. Independent test-design workers belong to a later delivery; do not claim they have run.

Product changes or unresolved behavior return to Discovery/its operator decision route before implementation. A Spec review cannot authorize changing accepted intent. Normal Spec Review and Land gates still apply after synthesis.

## Historical lineage and later changes

After handoff, Spec owns current scenario behavior, requirements, design, and task definitions. Accepted Discovery remains historical evidence at `discovery_commit`; do not run the old manifest against newly amended scenario bytes and conclude the old acceptance never occurred. Validate the original bundle in a temporary snapshot when checking lineage. Current behavior is reviewed at the new spec revision.

An explicit source amendment records a new accepted Discovery revision, updates the spec's lineage, and repeats affected checks. It never allocates a new feature for the same source. Do not silently update old reviews, acceptance records, or decision history.
