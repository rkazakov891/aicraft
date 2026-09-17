# Transition from Valcraft to AiCraft

AiCraft 0.8.3 forks Valcraft 0.8.2 at commit `5d3498230327352fe56eef0eb6b2c8d5290a5460`. This release renames the plugin; it does not implement a different delivery loop. The MIT copyright in `LICENSE` remains unchanged.

## Names

| Surface | Valcraft | AiCraft |
| --- | --- | --- |
| Repository | `valzav/valcraft` | `rkazakov891/aicraft` |
| Marketplace and plugin | `valcraft@valcraft` | `aicraft@aicraft` |
| Skill | `valcraft-<role>` | `aicraft-<role>` |
| Claude Code command | `/valcraft:valcraft-<role>` | `/aicraft:aicraft-<role>` |
| Codex invocation | `$valcraft:valcraft-<role>` | `$aicraft:aicraft-<role>` |
| Configuration directory | `.valcraft/` | `.aicraft/` |
| Configuration version key | `valcraft_version` | `aicraft_version` |
| Generated tracker namespace | `valcraft` | `aicraft` |

## New projects

Install AiCraft using the README instructions, start a new session, then run AiCraft Tune and Cast. AiCraft resolves its own configuration. Installing it does not upgrade or uninstall Valcraft.

## Existing projects

Do not replace strings across a live consumer repository automatically. The changed namespace affects configuration, ignored runtime state, tracker ownership markers, and skill invocations.

1. Finish or explicitly stop the existing delivery run. Preserve its reports and history. Never run both coordinators against the same work or resume a Valcraft checkpoint as an AiCraft checkpoint.
2. Preserve `.valcraft/` as the old state. Prepare `.aicraft/config.yaml` from the reviewed base configuration, renaming only the top-level version key to `aicraft_version`. Retain the recorded version so Tune can apply inherited migrations. Review any explicit paths or skill invocations separately.
3. If a local overlay exists, prepare `.aicraft/config.local.yaml` separately and keep it ignored. Retain its user-specific values; never publish it. Add `/.aicraft/*` and `!/.aicraft/config.yaml` to the project's ignore rules before writing runtime state or the overlay.
4. Run AiCraft Tune to validate the configuration and migrate it to the installed AiCraft version. Update project instructions and invocation references deliberately.
5. For GitHub-tracked work, stop before projection or delivery until existing issue mappings, generated-body markers, labels, and ownership have been reconciled under an explicitly authorized migration. Preserve issue IDs and human history. This release does not supply an automatic cross-namespace tracker migration; starting a fresh, non-overlapping contract is the supported alternative.
6. Start a new AiCraft run from verified repository and tracker evidence. Preserve historical Valcraft reports and identifiers rather than rewriting their attribution.

The installed Valcraft plugin, upstream Git remote, and other repositories are unaffected by renaming this checkout.
