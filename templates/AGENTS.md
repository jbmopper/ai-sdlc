# AGENTS.md

Instructions for every agent working on this repository.

**{{project}}** — {{one-line description}}. The operator is Jules.

## Start here

Read [DOCUMENTS.md](DOCUMENTS.md) and [DECISIONS.md](DECISIONS.md) before doing anything else.

## Rules

- **Never assume.** If something is undecided or ambiguous, ask Jules.
- **Only listed docs are canonical.** DOCUMENTS.md lists them. Anything else is not canonical.
- **Only validated decisions go in DECISIONS.md.** Agents propose entries. Jules validates them.
- **DECISIONS.md is append-only.** A reversed decision is struck through, and notes the decision that supersedes it.
- **Work from a contract.** A work unit starts when its contract passes `@SDLC@ contract check`. The contract is the specification you are held to.
- **Work in a branch and commit as you go.** Integration is `@SDLC@ integrate` after review, never a manual merge.
- **The tool is `@SDLC@`.** Always call it by that full path; it is not on PATH.
- **Keep wrong turns out.** Abandoned ideas and unvalidated proposals never go anywhere a future session will read.
- **Agent memory stays empty.** All persistent context lives in this repo.
- **Don't clutter.** Create a file only when it's needed. Scratch work goes outside the repo.
- **Write "Jules" and "agents," never "I."** Many agents and sessions work on this project.
