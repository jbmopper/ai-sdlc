# AGENTS.md

Instructions for every agent working on this repository.

**ai-sdlc** holds the tools, templates, and hooks that run Jules's agent-based
development lifecycle in other projects. The lifecycle itself is designed in
[docs/ai-sdlc.md](docs/ai-sdlc.md); this repo makes it work. The operator is Jules.

## Start here

Read [DOCUMENTS.md](DOCUMENTS.md) and [DECISIONS.md](DECISIONS.md) before doing anything else.
[WORKFLOW.md](WORKFLOW.md) is the current build plan: steps, deliverables, gates, tools.

## Rules

- **Never assume.** If something is undecided or ambiguous, ask Jules.
- **Only listed docs are canonical.** DOCUMENTS.md lists them. Anything else is not canonical.
- **Only validated decisions go in DECISIONS.md.** Agents propose entries. Jules validates them.
- **DECISIONS.md is append-only.** A reversed decision is struck through, and notes the decision that supersedes it.
- **Claude first, provider agnostic.** Logic lives in scripts under `bin/` that any agent or Jules can run. Hooks are thin wrappers that call those scripts; they never hold logic of their own.
- **Refuse, don't warn.** A gate that fails exits nonzero and names what is missing and what would resolve it.
- **Dry-run by default.** Anything that changes a project, a branch, or a worktree shows its plan first and acts only with `--apply`.
- **Never print secret values.**
- **Work in branches and commit as you go.** Merge gates are what this repo builds; until they exist here, don't merge without Jules.
- **Keep wrong turns out.** Abandoned ideas and unvalidated proposals never go anywhere a future session will read.
- **Agent memory stays empty.** All persistent context lives in this repo.
- **Don't clutter.** Create a file only when it's needed. Scratch work goes outside the repo.
- **Write "Jules" and "agents," never "I."** Many agents and sessions work on this project.

## Running

- Tests: `uv run --with pytest python -m pytest -q tests`
- CLI: `bin/sdlc --help`
- One unit end to end: `adopt` the project, commit a contract under `contracts/`, `contract check`, `dispatch --apply`, the writer works in the worktree, `review`, `integrate --apply`. Every step refuses with a reason when its gate is not met.
