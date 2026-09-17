# Foreman runtime configuration

Read the committed `.aicraft/config.yaml`, the optional gitignored `.aicraft/config.local.yaml` overlay, and [`../../aicraft-tune/references/config.md`](../../aicraft-tune/references/config.md) completely. Tune is the sole configuration writer.

Resolution rules:

- Resolve the configuration per the Tune contract: the base overridden by the overlay on the user-scoped keys `foreman.approval_mode`, `foreman.backend`, `foreman.herdr`, and `foreman.ao`, with `backend` and its backend-specific mapping overriding as a unit. Require the resolved configuration to be complete and valid. Never apply read-time defaults or inspect legacy declarations in `AGENTS.md`.
- A repo-scoped key in the overlay is invalid configuration; delegate it to `aicraft-tune`.
- Use `tracker.mode` to select intake. Use the resolved `foreman.backend` and `foreman.approval_mode`, and the base `foreman.default_branch` and `foreman.release_branch`, exactly as stored.
- In GitHub mode, use `foreman.clarification_assignees` exactly as stored.
- For Herdr, use the resolved session and complete worker map. See its backend reference for translation to native command arguments.
- For AO, use the resolved `foreman.ao.project_id` exactly as stored, only as an argument value.
- Delegate any missing or invalid value to `aicraft-tune` for the affected section. Resume only after `Status: done` and a complete re-read.
- Everything under `.aicraft/` except `config.yaml` must be gitignored; `aicraft-cast` establishes the `/.aicraft/*` and `!/.aicraft/config.yaml` pair at scaffold time.

Before constructing a dispatch, re-read the configuration entries that supply its backend and worker settings. Record the effective harness, model, and effort with the actual source file and key in the assignment checkpoint when the backend configures them. Preserve overlay precedence; a value from `.aicraft/config.local.yaml` must not be attributed to the base. For a backend that supplies worker settings itself, record that source instead of inventing configuration keys.
