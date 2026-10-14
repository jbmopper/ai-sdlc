# Workflow

The lifecycle from `dev-infra/docs/ai-sdlc.md`, as built here. One row per
step. A gate is what must be true before the step's deliverable counts; a gate
that fails refuses and names what would resolve it. Tools are `bin/sdlc`
subcommands unless noted. Steps marked *later* are outside increment one (D12).

| Step | Deliverable | Gate | Tool |
|---|---|---|---|
| Adopt | Project has CLAUDE.md, AGENTS.md, DOCUMENTS.md, DECISIONS.md, the git hooks, and the Claude hook config. | Dry-run plan reviewed; existing files are never overwritten without `--force`. Existing git hooks (the pre-commit framework is installed globally via `init.templateDir` and already present in `resume-lambda`) are chained, not replaced. | `sdlc adopt <repo> [--apply]` |
| Intake | A project brief: purpose, priority, users, level of finish, broad effort. Lives in AGENTS.md or a doc listed in DOCUMENTS.md. | Jules validates it. Decisions it embeds are entries in DECISIONS.md. | None. Conversation with Jules. |
| Architecture | Specification and design docs listed in DOCUMENTS.md. Deferred questions each name the work they affect and the trigger that forces an answer. | Jules's direction is distinguishable from agent proposals. | None in increment one. |
| Contract | One plan file per work unit with the section 5 elements: purpose, scope and return, authoritative inputs, execution arrangement, effort and stopping, acceptance and closure. | Definition of ready (D8): every element present, inputs cite docs listed in DOCUMENTS.md, repair limit set, reserved choices named. | `sdlc contract check <file>` |
| Dispatch | A worktree and branch for the unit, plus the curated context list the writer receives. | Contract passed its check. Worktree is clean and the branch is new. | `sdlc dispatch <contract> [--apply]` |
| Implement | Commits on the unit's branch, tests, and a short work record of assumptions, discoveries, deviations, turns, tokens, and wallclock. | Protected files (DECISIONS.md, DOCUMENTS.md, AGENTS.md, CLAUDE.md, `contracts/`, `.sdlc/`) untouched on the branch. No push to main. Turn cap and repair-round limit (D17). | `hooks/git/pre-commit`, `hooks/git/pre-push`, `hooks/claude/` PreToolUse, all calling `sdlc check-protected` |
| Review | A verdict file keyed to the reviewed commit: pass or fail, findings classified blocking, deferred, suggestion, or needs-decision, and what the tests establish and miss. | Reviewer receives only the contract, DECISIONS.md, the diff against base, and test output. Never the writer's transcript. Two failed repairs of one finding stop the unit with a report. | `sdlc review <branch>` |
| Integrate | Squash merge to main (D10), follow-ups recorded, worktree and branch deleted. | Passing verdict exists for the branch's current head. Suite passes on the merged result. Protected files unchanged. | `sdlc integrate <branch> [--apply]` |
| Summary | One batched report per unit to Jules: what merged, recorded follow-ups, needs-decision items as proposed DECISIONS.md entries. | None. It is the output of integrate. | `sdlc integrate` output |
| Release *(later)* | Release candidate, regression evidence, notes. | Promotion authority per project. | Not built. |
| Closure and recovery *(later)* | Updated docs, learnings, next-step proposals; reconstructed coordinator state. | Section 10 fold order. | Not built. |

## Open questions

Not decisions. Each closes by Jules recording an entry in DECISIONS.md.

- Whether `sdlc integrate` deletes a unit's contract file in the squash commit or keeps it. Wait for the trial.
