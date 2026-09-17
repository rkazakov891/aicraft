# ADR 0001: Revision-bound scenario discovery

Status: accepted for the first discovery delivery.

## Context

The existing feature triplet starts from one prepared source and creates its feature issue during Spec projection. Free-form discovery needs durable decisions and independent product review before that handoff. Creating a second issue or copying scenarios into separate editable definitions loses identity and provenance.

## Decision

Introduce an opt-in discovery bundle with Markdown sources and a JSON manifest of IDs, typed links, file digests, findings, and references. The bundle's content revision hashes product fields and source bytes, excluding review, acceptance, and tracker bookkeeping. Reviews and the attributed operator acceptance bind to that revision. A committed snapshot makes the content available to independent reviewers.

Discover owns scenarios before handoff. Spec takes ownership after handoff and preserves their IDs; the accepted discovery remains historical lineage. Spec uses one canonical Discovery path as its source and records the accepted commit and digest separately. A verified Discovery issue is adopted as the feature issue rather than parented beneath a new issue.

Trace runs deterministic structural validation and derives Mermaid/HTML. A separate reviewer evaluates semantic consistency. Mechanical success never substitutes for product review or operator acceptance. All findings block the affected gate. Missing context and unsupported claims remain visible.

The first delivery adds an explicit Foreman discovery prelude. It reuses configured spec/spec_review worker settings with an explicit role binding and the existing independence check. It stops at a reviewed Spec handoff unless delivery is separately authorized. Legacy intake, ten-role configuration, and task delivery remain compatible. Parallel read-only review is allowed only on isolated committed snapshots; shared-checkout dispatch stays serial.

## Consequences

Python 3 standard-library helpers become shipped resources and must be included in the remote skill index. Existing projects do not need discovery manifests unless they opt into this entrypoint. Historical artifacts are not mass-converted. Validators reject changed input bytes even when an agent forgets to update metadata. Semantic adequacy and the authenticity of recorded operator decisions still require trusted coordinator attribution.
