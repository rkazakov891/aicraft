# aicraft

AiCraft is a software factory in your repository: it coordinates the work, keeps the requirements and decisions in ordinary files, and checks the code before shipping so you can see what was built and how it was verified.

It ships as agent skills for spec-driven delivery, packaged as one plugin for Claude Code, OpenAI Codex, OpenCode, and Cursor (Teams or Enterprise with marketplace-import authority). At the center is an agentic **delivery loop** — draft → review → forge → review → land — run over fresh-context worker agents, inside one Claude Code, Codex, or Cursor session or through an orchestrator over several instances. Around it: `cast` creates the project frame, `spec` creates every feature or quick contract, and `temper` learns from what shipped.

Status: alpha.

AiCraft is a fork of [Valcraft](https://github.com/valzav/valcraft), based on commit `5d3498230327352fe56eef0eb6b2c8d5290a5460` (0.8.2). The original MIT license and copyright are preserved. AiCraft uses its own plugin namespace and configuration; see [the transition guide](docs/valcraft-to-aicraft.md).

## Scenario Discovery (0.9.0)

Start with `aicraft-discover` when you have a feature idea rather than a prepared requirements document. It records sources, user scenarios, and decisions in Git. Independent `aicraft-product-review` and `aicraft-trace` check the exact snapshot before your confirmation. Trace generates Mermaid and a searchable local HTML navigator. Spec then consumes the accepted bundle, preserves scenario IDs, writes EARS requirements, and reuses the permanent feature issue.

Ask Foreman explicitly to coordinate Discovery through Spec to run that prelude through the configured backend. Discovery acceptance does not authorize implementation. Legacy Spec/task delivery remains available unchanged. Python 3.10+ is required for the optional Discovery helper. The prelude may overlap isolated snapshot reviews; concurrent implementation, release planners, test-design workers, and full release acceptance are later deliveries described in [the target architecture](docs/scenario-delivery.md).

See [the first-delivery guide](docs/discovery.md) for artifacts, commands, and verification limits.

## Problems it addresses

| If you have seen this…                                              | aicraft's answer                                                                                                                                                                                  |
| ------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| The agent forgets requirements between sessions and reinvents them. | `cast` establishes the project frame and `spec` writes git-owned contracts with stable IDs (`FR-`, `AC-`, `T-`, `ADR-`) that plans, commits, tests, and reviews cite. Context lives with the code. |
| "Make X" turns into a pile of unreviewed code.                      | `foreman` coordinates independent plan and code reviews; `land` finalizes only the exact reviewed target, so implementer verification never becomes approval.                                      |
| One long session runs out of context or reports work it never did.  | `foreman` keeps its own context small — every worker starts cold, reports land on disk, and a run resumes from the tracker, git, and those reports.                                                |
| Either you approve every step, or the agent runs away.              | Approval modes (`attended`, `unattended`) decide which decisions wait for you. Some always do: release-branch writes, feature close, and escalations.                                              |
| Task tracking drifts from what the specs say.                       | The specs are canonical; the tracker is a projection of them — the simple option is `tasks.md` checkboxes in the repo, or GitHub Issues with generated bodies and blocked-by links.                |
| The same mistakes recur project after project.                      | `temper` runs an evidence-graded retrospective over a shipped feature and proposes standing rules for `AGENTS.md`; nothing is promoted on a single unverified incident.                            |
| Prompts and skills bloat until the model ignores them.              | `hone`, `distill`, and `msw` refine, reduce, and judge prompt artifacts against a stated contract.                                                                                                 |

## AiCraft's SDD at a glance

AiCraft treats spec-driven development as a repository data model, not a session ritual. Product intent, requirements, decisions, tasks, and evidence live in ordinary files with stable IDs. Agents can resume from those artifacts without inheriting another agent's conversation.

```text
product idea:
  -> cast: ensure configuration, then create the SDD project frame
    -> spec: create the first feature contract
new feature or PRD:
  -> spec: create a feature contract or quick task
    -> foreman: infer and confirm the current state, then coordinate the remaining delivery
      -> spec / review / land: establish the contract on the default branch when needed
      -> draft: write the task plan, then apply msw
      -> review: pass the task plan or return findings
      -> forge: implement the task and produce verification evidence
      -> review: pass the change or return reproduced findings
      -> land: finalize the reviewed target and close tracker state
      -> temper (feature only): write the local retrospective report (docs/.retro/, gitignored)
        -> review: pass the report or return findings
```

`foreman` can coordinate the delivery stages in one loop or take over work started with the individual skills. Without a verified active checkpoint, it inspects durable repository, tracker, PR, and report evidence, proposes the inferred state and next action, and waits for confirmation before creating a run. An exact checkpoint resumes without that takeover confirmation.

Each skill emits its own complete report only for its current invocation. A later AiCraft skill never replays an earlier skill's report. When prior state is relevant to the current target or handoff, it may instead show one short paragraph containing only the prior outcome, exact target, relevant blocker or handoff, and a suggested next action; that summary is presentation, not routing evidence or mutation authority.

### Primitives

- **Git-owned contract.** Accepted ADRs, `specs/`, and derived project docs define what the change must do, in that precedence order. A chat message can select or clarify work, but it does not silently replace the repository contract.
- **Stable identity.** Features, requirements, acceptance criteria, tasks, decisions, and findings use IDs such as `FEAT-001`, `FR-001`, `AC-001`, `T-001`, `ADR-0001`, and `R-001`. A quick unit uses the qualified identity `Q-001 QT-001`. Plans, commits, reviews, and tracker records cite these IDs.
- **One unit of work.** Delivery operates on one feature task, one quick task, or one explicitly scoped plan at a time. Dependencies are part of the task contract, not inferred from conversation order.
- **Tracker as projection.** Git owns task definitions. Feature status can remain in `tasks.md` checkboxes or project to GitHub Issues; quick tasks always track locally. Tracker state never becomes a second source of requirements.
- **Readiness before execution.** A feature needs a complete and consistent spec, design, and task decomposition. A quick task carries the same minimum contract in one file. Missing product decisions stop implementation rather than becoming guesses.
- **Independent evidence.** Planning, implementation, and review use fresh contexts. `forge` verifies its work, but `review` independently decides whether the plan or code satisfies the contract. Findings close only when their reproductions pass.

### Artifacts and skill ownership

- **Configuration:** the committed `.aicraft/config.yaml` is the repository's shared base — tracker, Foreman, branch, Herdr worker, and pull-request settings. The optional gitignored `.aicraft/config.local.yaml` overlay overrides the user-scoped keys (approval mode, backend, and backend-specific worker settings), so collaborators can keep personal approval and backend choices without touching the shared file. `tune` is the sole writer of both and can reconfigure one section at any time.
- **Project frame:** `AGENTS.md` records standing development rules; `docs/product-brief.md` records product intent and boundaries. `cast` creates or retrofits them, and every delivery skill reads the applicable rules.
- **Decision record:** `docs/architecture/adr/NNNN-*.md` captures consequential technical decisions and their consequences. `cast` establishes the ADR structure; `forge` and `review` treat accepted ADRs as the highest project authority.
- **Feature contract:** `specs/NNN-<slug>/spec.md` owns requirements and acceptance criteria, `design.md` owns the technical realization, and `tasks.md` owns `T-XXX` decomposition and dependencies. `spec` creates or resumes the complete triplet from one accepted source, including the first MVP feature; `foreman`, `draft`, `forge`, `review`, and `land` deliver against it.
- **Quick contract:** `specs/quick/NNN-<slug>.md` combines requirements, approach, and `QT-XXX` tasks for a change that does not need a feature triplet. `spec` creates it; the normal delivery and review skills use it as the complete contract.
- **Delivery plan:** `docs/plans/*-plan.md` records implementation decisions for non-trivial work or remediation decisions for review findings. `draft` writes or revises the plan and applies `msw`; `review` checks its exact commit before `forge` implements it. Progress remains in the tracker rather than in the plan.
- **Evidence and learning:** `forge` produces a verification handoff; `review` produces stable `R-XXX` findings and reproduced evidence; `land` owns final-head checks, authorized finalization, and tracker closure. `foreman` stores attributed worker reports while coordinating transitions. After feature closure, `temper` writes an append-only local report under the gitignored `docs/.retro/`; its synthesize mode aggregates those reports and, when evidence is corroborated across reports, offers the proposals to the operator as a selection.

## Workflows

### 1. The full loop: `cast` → `spec` → `foreman`

The default path for a new project or a new body of work.

1. **`/aicraft:aicraft-cast`** — create or retrofit the project frame: README, configuration-free `AGENTS.md`, product brief, architecture and ADR structure, and the durable `specs/` root. Cast invokes `tune` when configuration is missing or invalid, records its exact proposal, and commits one clean baseline that includes `.aicraft/config.yaml` and the `.aicraft/` ignore pair. It hands the product brief to Spec and creates no feature triplet or quick task.
2. **`/aicraft:aicraft-spec`** — give `spec` one accepted PRD or requirements source. It creates or resumes the complete `spec.md`, `design.md`, and `tasks.md` triplet, including the first MVP feature. For a smaller change, it creates one complete quick-task file under `specs/quick/`. Spec owns optional authorized tracker projection, branch push, and spec PR creation or update, then returns exact Review and Land targets.
3. **`/aicraft:aicraft-foreman`** — say "start sprint" after Spec or at any later point through Temper. Foreman reads its complete settings from the resolved configuration; missing or invalid settings return to `tune` instead of triggering runtime guesses. With no verified active checkpoint, it finds the selected feature or quick task's earliest unproven state, previews the exact target, evidence, attributed dirty paths, inferred state, and next producer action, then waits for confirm, correct, or cancel even in unattended mode. It can resume Spec for an incomplete or unpublished contract, route an exact contract through Review and Land, or adopt exact later producer evidence before continuing the normal task loop: pick → Draft plan and MSW → Review plan → Forge implementation and authorized task PR → Review code → Land finalization and closure. When a feature closes, Foreman routes Temper's local retrospective report through Review; a pass completes the feature, and nothing is merged because the report is not in git. "deliver quick" applies the same takeover and task flow to `specs/quick/`. New feature and PRD intake still begins directly with Spec.

   Run `/aicraft:aicraft-tune` at any time to reconfigure one section. Tune asks only genuinely open choices with the recommended simple option first, resolves the rest from existing configuration and repository evidence, and shows the exact saved YAML in its report. A user-scoped change can apply to everyone (committed) or just to you (local overlay). Manual Forge remains available without changing the scaffold.

   `foreman` can use native subagents on Claude Code, Codex, and Cursor. Claude Code wakes the parent turn when a worker completes; Codex waits in the foreground with `wait_agent`; Cursor keeps the parent turn active while the Task call holds. The Herdr backend can assign each role to Claude, Codex, or Cursor while preserving cross-harness Review independence. OpenCode has no worker backend. External orchestrators integrate through registered Foreman backends.

### 2. Manual loop, one task at a time

Same contracts, you drive:

1. `/aicraft:aicraft-cast`, then `/aicraft:aicraft-spec` as above.
2. `/aicraft:aicraft-draft T-XXX` (or `Q-NNN QT-XXX`) — write or revise the task plan, apply MSW, verify the surviving plan, and commit that reviewable state. Run `/aicraft:aicraft-review` in plan mode on that exact commit; return findings to Draft by `R-ID`.
3. `/aicraft:aicraft-forge T-XXX` — implement only from the passed plan review, verify the change, and prepare or create the authorized task PR. Run `/aicraft:aicraft-review` in code mode on the exact head; return findings to Forge by `R-ID`.
4. `/aicraft:aicraft-land` — revalidate Review coverage and applicable checks, then perform only the authorized finalization and closure operations. In unattended mode, exact target-bound Land authority permits ordinary landing on native subagents, external orchestrators, and conforming future backends; Foreman never merges.
5. `/aicraft:aicraft-temper` over the closed feature, then run `/aicraft:aicraft-review` in plan mode on the exact report path and content hash it returns. There is no PR and no Land step.

Invoke Foreman at any point after Spec to hand over the remaining sequence. It confirms the inferred state and next action once, then continues autonomously under the configured approval mode and existing authority gates.

## Prompt tooling

- **`hone`** — refine a prompt, skill, or `AGENTS.md` against the current Claude and Codex prompting guides; deletion first, every addition justified.
- **`distill`** — reduce a prompt or skill to goal, steps, constraints, and testable behaviors; a study or a leaner drop-in copy.
- **`msw`** — apply the MSW Kernel to a markdown document: derive its contract, delete every claim the contract does not require, report what was cut and why. Kernel by "Fable at mega high monkey effort", published by [@aienginerd](https://x.com/aienginerd/status/2085342869850603672).

## Skills at a glance

| Skill | Claude Code | Codex | OpenCode | Cursor |
| --- | --- | --- | --- | --- |
| `tune` — adjust the shared configuration or your local overlay | `/aicraft:aicraft-tune` | `$aicraft:aicraft-tune` | `aicraft-tune` | `/aicraft-tune` |
| `cast` — create or retrofit the project frame | `/aicraft:aicraft-cast` | `$aicraft:aicraft-cast` | `aicraft-cast` | `/aicraft-cast` |
| `discover` — develop and resume user scenarios | `/aicraft:aicraft-discover` | `$aicraft:aicraft-discover` | `aicraft-discover` | `/aicraft-discover` |
| `product-review` — review capability conflicts and value | `/aicraft:aicraft-product-review` | `$aicraft:aicraft-product-review` | `aicraft-product-review` | `/aicraft-product-review` |
| `trace` — check lineage and generate navigation | `/aicraft:aicraft-trace` | `$aicraft:aicraft-trace` | `aicraft-trace` | `/aicraft-trace` |
| `spec` — create a feature or quick contract | `/aicraft:aicraft-spec` | `$aicraft:aicraft-spec` | `aicraft-spec` | `/aicraft-spec` |
| `draft` — write a task plan and apply MSW | `/aicraft:aicraft-draft` | `$aicraft:aicraft-draft` | `aicraft-draft` | `/aicraft-draft` |
| `forge` — implement a reviewed task | `/aicraft:aicraft-forge` | `$aicraft:aicraft-forge` | `aicraft-forge` | `/aicraft-forge` |
| `review` — review an exact plan, change, or evidence | `/aicraft:aicraft-review` | `$aicraft:aicraft-review` | `aicraft-review` | `/aicraft-review` |
| `land` — finalize reviewed work and close tracker state | `/aicraft:aicraft-land` | `$aicraft:aicraft-land` | `aicraft-land` | `/aicraft-land` |
| `foreman` — coordinate the delivery loop | `/aicraft:aicraft-foreman` | `$aicraft:aicraft-foreman` | `aicraft-foreman` | `/aicraft-foreman` |
| `temper` — produce a local retrospective and handoff | `/aicraft:aicraft-temper` | `$aicraft:aicraft-temper` | `aicraft-temper` | `/aicraft-temper` |
| `hone` — refine a prompt artifact | `/aicraft:aicraft-hone` | `$aicraft:aicraft-hone` | `aicraft-hone` | `/aicraft-hone` |
| `distill` — reduce a prompt to its essence | `/aicraft:aicraft-distill` | `$aicraft:aicraft-distill` | `aicraft-distill` | `/aicraft-distill` |
| `msw` — MSW Kernel over a document | `/aicraft:aicraft-msw` | `$aicraft:aicraft-msw` | `aicraft-msw` | `/aicraft-msw` |

Skills also trigger from natural requests ("new project", "review this PR", "retrospective on feature 3"); the command is the explicit path. The skill name is `aicraft-<skill>` on every host. Claude Code and Codex prepend the `aicraft:` plugin namespace in their explicit forms, OpenCode loads the bare name through its `skill` tool, and Cursor uses `/aicraft-<skill>`. Cursor's built-in `/review` is not AiCraft Review; invoke `/aicraft-review`.

## Compared with other SDD frameworks

| Elsewhere                                                                                    | In aicraft                                                                                                                                                                                                                                                |
| -------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| An executable, scripts, and a setup step.                                                    | Existing delivery skills are instruction-driven; optional Discovery adds Python standard-library validation and navigation helpers. `cast` writes the tracked project frame; `tune` writes the committed configuration and an optional ignored overlay.                                                                                       |
| Specs and tasks live in the framework's own folders and formats.                             | Specs are ordinary files under `specs/`, tasks are checkboxes or GitHub Issues you already use, decisions are ADRs — readable and editable without the tool.                                                                                               |
| SDD is a session ritual, not a project rule; work done outside it drifts from the specs.     | `cast` writes the discipline into `AGENTS.md`, so every agent session — inside the loop or not — cites IDs, updates the affected spec or ADR in the same change, and reviews against the same contract; `cast` retrofits an existing project the same way. |
| Roles are personas and phases are ceremony — analyst hands off to PM hands off to architect. | AiCraft's roles are skills with contracts (`spec`, `draft`, `forge`, `review`, `land`, `temper`); independence comes from a fresh context per role, not a character sheet.                                                                                |
| A dozen generated documents and a traceability matrix nobody reads.                          | The skeleton is small; every other artifact is opt-in with a stated trigger. IDs and links give traceability; the skills trim generated verbosity before committing.                                                                                       |
| Adoption is all or nothing.                                                                  | Each skill runs alone: `draft` on one task, `review` on an exact target, `forge` on a passed plan, `land` on reviewed work, or `cast` to retrofit — the loop is there when you want it.                                                                    |

## Install

Claude Code:

```bash
claude plugin marketplace add rkazakov891/aicraft
claude plugin install aicraft@aicraft
```

Codex (start a new session afterwards):

```bash
codex plugin marketplace add rkazakov891/aicraft
codex plugin add aicraft@aicraft
```

OpenCode — add the skills source to `opencode.json` (project or global) and allow the `skill` tool; OpenCode fetches `index.json` and caches every skill file, refreshing a skill when its content changes:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "skills": {
    "urls": [
      "https://raw.githubusercontent.com/rkazakov891/aicraft/main/plugins/aicraft/skills/"
    ]
  },
  "permission": { "skill": "allow" }
}
```

The URL form needs the repository to be public (raw GitHub answers anonymous requests only for public repositories). From a clone, use `"skills": { "paths": ["/path/to/aicraft/plugins/aicraft/skills"] }` instead. `foreman` has no OpenCode worker backend yet; the other skills run as they do elsewhere.

Cursor Teams or Enterprise (marketplace-import authority). Import this git repository as a team marketplace from the dashboard **Plugins → Add Marketplace**, or add it from the CLI:

```bash
agent plugin marketplace add https://github.com/rkazakov891/aicraft
```

The CLI has no `plugin install` verb. After the marketplace is visible, install `aicraft` from the Cursor Plugins UI. Do not install from a skill directory, and do not point a `~/.cursor/skills` path at this repository.

## Update

Claude Code — third-party marketplaces do not auto-update; every push is a new version:

```bash
claude plugin marketplace update aicraft
claude plugin update aicraft@aicraft
```

Codex — refresh the marketplace snapshot and re-add, then start a new session:

```bash
codex plugin marketplace upgrade aicraft
codex plugin add aicraft@aicraft
```

OpenCode — nothing to run: the source is re-read at startup, and a skill whose `version` in `index.json` changed is re-downloaded (raw GitHub caches for a few minutes).

Cursor — re-index the marketplace, then install or update the plugin from the user-scoped Plugins UI (`/plugins` → `aicraft` → Install/Update). If the re-index does not surface the new version, remove and re-add the marketplace with `agent plugin marketplace remove aicraft` followed by the `add` command above:

```bash
agent plugin marketplace update aicraft
```

A marketplace install is a cached copy. It does not read later checkout edits.

## More

- [docs/development.md](docs/development.md) — live editing, repository layout, packaging, evals.
- [docs/glossary.md](docs/glossary.md) — the terms the skills share.
- [migrations.md](plugins/aicraft/skills/aicraft-tune/references/migrations.md) — what each release changes for a repository that already uses AiCraft, and how bare `tune` applies it.
- [models.md](plugins/aicraft/skills/aicraft-tune/references/models.md) — the model aliases, effort sets, and Herdr presets Tune offers; the only file to edit when a provider adds or retires a model.

## Contributing

Pull requests are welcome. The `lint` workflow must pass, and every shipped `SKILL.md` must stay at or below 8,000 UTF-8 bytes (the Codex limit; move detail into `references/`). [docs/development.md](docs/development.md) covers live editing and packaging.

## License

[MIT](LICENSE).
