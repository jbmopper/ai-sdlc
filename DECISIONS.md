# Decisions

Only decisions Jules has validated. Append-only: a reversed decision is struck through, and notes the decision that supersedes it.

| # | Date | Decision |
|---|---|---|
| D1 | 2026-09-22 | Build the SDLC system first, then use it to finish `resume-lambda`. `resume-lambda` is the motivating failure: a lightweight "just talk to agents" approach drifted requirements despite care. |
| D2 | 2026-09-22 | `resume-lambda` runs the first bounded qualification trial. `aur-detonationpot` never was the trial. |
| D3 | 2026-09-22 | Claude first, ultimately provider agnostic. CLAUDE.md points to AGENTS.md. Logic lives in files and scripts any agent can use. |
| D4 | 2026-09-22 | Enforcement lives on the machine. No GitHub branch protection or rulesets. |
| D5 | 2026-09-22 | Integration flow: writer, then independent review, then record nonblocking findings, then the agent merges and deletes the worktree and branch. Not "agent opens PR, Jules merges." |
| D6 | 2026-09-22 | Retired documents are deleted. Git history is the archive. |
| D7 | 2026-10-02 | The `exoplanet` layout (CLAUDE.md, AGENTS.md, DOCUMENTS.md, DECISIONS.md) is the shape for adopted projects. Not necessarily exact. |
| D8 | 2026-10-02 | A work-unit plan document (the section 5 contract) is the launch point for a subagent. It is the definition of ready. |
| D9 | 2026-10-02 | Verdicts are not decisions. A verdict is the reviewer's output for one branch at one commit; a decision is Jules's validated direction. They do not share a file. |
| D10 | 2026-10-02 | Squash merge on integration. |
| D11 | 2026-10-13 | The tools live in `~/Dev/ai-sdlc`, a separate repository from `dev-infra`. |
| D12 | 2026-10-13 | Increment one: the adopt template, the contract convention, the review script with verdict storage, the integrate script, and git and Claude Code hooks that wrap those scripts. No tracker, coordinator recovery, or release stream until the trial shows they earn their cost. |
| D13 | 2026-10-13 | Review verdicts live outside the writer's worktree, in the main checkout. Trial of the agent proposal; revisit if it fails. |
| D14 | 2026-10-13 | Agents run the scripts. A coordinator agent calls `sdlc` subcommands; Jules is not the operator of the pipeline. |
| D15 | 2026-10-13 | The lifecycle design moves from `dev-infra/docs/ai-sdlc.md` into this repository as `docs/ai-sdlc.md`. |
| D16 | 2026-10-14 | Proposed decisions have no file of their own. A proposal from a work unit goes in the verdict's needs-decision list and reaches Jules in the batched summary; he accepts it by appending to DECISIONS.md, or it dies with the branch. A proposal that must outlive a unit is a deferred question and lives in the spec or design doc with its trigger. |
| D17 | 2026-10-14 | Effort units: a per-dispatch turn cap and the repair-round limit are enforced. Tokens and wallclock are recorded in the work record, not enforced. |
| D18 | 2026-10-14 | Contracts live in a `contracts/` directory in the adopted project, one file per unit named by date and slug. The branch, worktree, and verdict share the unit id. The coordinator commits the contract to main before dispatch, so it is protected from the writer. Contracts are not listed in DOCUMENTS.md; the directory is the index. |
