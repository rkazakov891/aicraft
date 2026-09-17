# <Project name>

<One-paragraph description: what it is and its primary value.>

## Status

Pre-development | Prototype | Alpha | Beta | Production

## Repository structure

- `docs/` — product brief, plans, and architecture documentation.
- `specs/` — Spec-owned feature triplets and quick-task contracts.
- `<source dirs>` — application code.

## Documentation

- [Product brief](docs/product-brief.md)
- [Architecture overview](docs/architecture/overview.md)
- [Architecture decisions](docs/architecture/adr/)
- [Feature specifications](specs/)
<!-- When docs/status.md exists, render this bullet and remove this instruction:
- [Operational snapshot](docs/status.md) — dated, non-authoritative external observations.
Omit both the bullet and this instruction when the snapshot is absent. -->

## Development

### Spec-driven workflow

Claude Code `/aicraft:aicraft-<name>`; Codex `$aicraft:aicraft-<name>`; OpenCode `aicraft-<name>`; Cursor `/aicraft-<name>`.

Start with the project frame and product brief created by Cast. Run `aicraft-spec` to create the first MVP feature, a later feature triplet, or a quick task. For task delivery, use Draft, Review, Forge, Review, and Land directly, or let Foreman coordinate those stages.

AiCraft's shared settings live in the committed `.aicraft/config.yaml`; personal overrides live in the gitignored `.aicraft/config.local.yaml`. Run `aicraft-tune` to change tracker, approval, Foreman, branch, Herdr worker, or pull-request choices.

### Prerequisites

<Runtimes, package managers, databases, external tools.>

### Install / run / test

```bash
<install command>
<dev command>
<test command>
<lint + type-check commands>
```

## Configuration

<Environment variables and local setup. No secrets in the repo — references only.>
