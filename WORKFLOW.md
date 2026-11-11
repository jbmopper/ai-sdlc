# Workflow

The lifecycle from `dev-infra/docs/ai-sdlc.md`, as built here. One row per
step. A gate is what must be true before the step's deliverable counts; a gate
that fails refuses and names what would resolve it. Tools are `bin/sdlc`
subcommands unless noted. Steps marked *later* are outside increment one (D12).

| Step | Deliverable | Gate | Tool |
|---|---|---|---|
| Adopt | Project has CLAUDE.md, AGENTS.md, DOCUMENTS.md, DECISIONS.md, the git hooks, and the Claude hook config. | Dry-run plan reviewed; existing files are never overwritten without `--force`. Existing git hooks (the pre-commit framework is installed globally via `init.templateDir` and already present in `resume-lambda`) are chained, not replaced. | `sdlc adopt <repo> [--apply]` |
| Sync | An adopted project's substrate carries later template changes, merged three ways with the project's own edits kept; hooks and settings refreshed; the sync point recorded at the end of AGENTS.md. | Runs on the project's integration branch, with ai-sdlc's templates committed. A merge conflict refuses and writes nothing. The dry run shows each change as a diff; `--apply` writes but does not commit. | `sdlc sync <repo> [--apply]` |
| Intake | A project brief: purpose, priority, users, level of finish, broad effort. Lives in AGENTS.md or a doc listed in DOCUMENTS.md. | Jules validates it. Decisions it embeds are entries in DECISIONS.md. | None. Conversation with Jules. |
| Architecture | Specification and design docs listed in DOCUMENTS.md. Research and drafts that inform them may be listed too, marked as not validated in their row and at the top of the file. Deferred questions each name the work they affect and the trigger that forces an answer. | Jules's direction is distinguishable from agent proposals. When Jules validates a spec, its row says so, and research it superseded is deleted or relabeled as the sources behind it. | None in increment one. |
| Contract | `contracts/YYYY-MM-DD-slug.md` with the section 5 elements and the machine-read lines `Reserved:`, `Model:`, `Turns:`, `Repairs:`, `Tests:`. | Definition of ready (D8): every element has content, citations resolve to DOCUMENTS.md entries and live D-numbers, `Reserved:` present, `Turns:` and `Repairs:` positive, `Tests:` names the command. | `sdlc contract check <file> [--json]` |
| Dispatch | Branch `unit/<id>` from main, a worktree at `<parent>/<project>.units/<id>`, a unit record in `.sdlc/units/<id>/` in the main checkout, and the printed package the coordinator hands the writer: worktree, contract, documents to read, limits. | Contract passed its check and is committed on main unchanged. Branch, worktree, and record do not exist yet. Runs from the main checkout on main. | `sdlc dispatch <contract> [--apply]` |
| Implement | Commits on the unit's branch, tests, and a short work record of assumptions, discoveries, deviations, turns, tokens, and wallclock. | Protected files (DECISIONS.md, DOCUMENTS.md, AGENTS.md, CLAUDE.md, `contracts/`, `.sdlc/`) untouched on the branch. No push to main. Repair-round limit enforced by review; the turn cap is an instruction to the writer, not a gate (D20). | `hooks/git/pre-commit`, `hooks/git/pre-push`, `hooks/claude/` PreToolUse, all calling `sdlc check-protected` |
| Review | `.sdlc/units/<id>/reviews/<round>-<sha>.json`: pass or fail, summary, findings classified blocking, deferred, suggestion, or needs-decision, what the tests establish and miss. The package the reviewer saw is stored beside it. | Reviewer receives only the contract, DECISIONS.md, the documents the contract cites (at the base commit), the diff against base, the branch's commit messages, and the `Tests:` output. Never the writer's transcript. Enforced regardless of the model: a blocking finding or failing tests means fail. A needs-decision finding on a unit with reserved choices yields the third outcome, decision: no round spent, integrate refuses until DECISIONS.md answers it, and the same head may be reviewed again. Rounds allowed = 1 + `Repairs`; the last failure writes `STOP.md` and further review is refused. A head with a pass or fail is never reviewed twice. | `sdlc review <unit> [--reviewer CMD]`; reviewer from flag, `$SDLC_REVIEWER`, `.sdlc/config.json`, or default `claude -p` with tools off and a JSON schema |
| Integrate | Squash commit on main (D10) carrying the contract title, review summary, follow-ups, needs-decision items, and `Unit-Id`; worktree removed and branch deleted; `integrated.json` recorded. | From the main checkout with no modified tracked files. Latest verdict is a pass for the branch's current head. No protected file changed against base. Squash applies without conflict and `Tests:` passes on the merged tree, else main is left untouched. | `sdlc integrate <unit> [--apply]` |
| Summary | `.sdlc/units/<id>/summary.md`: what merged, findings by class, what tests establish and miss, merged-tree test output, changed files. Needs-decision items are the proposed DECISIONS.md entries (D16). | None. It is the output of integrate. | `sdlc integrate` writes it |
| Release *(later)* | Release candidate, regression evidence, notes. | Promotion authority per project. | Not built. |
| Closure and recovery *(later)* | Updated docs, learnings, next-step proposals; reconstructed coordinator state. | Section 10 fold order. | Not built. |

## Re-entering architecture

Settled direction can turn out wrong or incomplete after work has been built on it. Architecture then reopens for the affected docs (D24). Entry and exit are both decisions.

1. **Enter.** Jules records a decision naming what is being revised and why. It supersedes the decision that validated the affected docs, so `sdlc contract check` refuses any contract that cites the old one.
2. **Mark.** Each affected doc says it is under revision, citing the new decision, in a status line at the top of the file and in its DOCUMENTS.md row.
3. **Stop dependent work.** Identify work in flight that relies on the affected docs (design section 12). It stops, or its contract is revised before it continues. No new contract is written against docs under revision, and the re-entry decision is never cited as a basis for work.
4. **Work.** Architecture runs as normal: research and drafts are listed as not validated (D23), and decisions are recorded as Jules makes them.
5. **Exit.** The normal architecture gate. Jules records the decision that validates the revised docs; their status lines and rows say so; research they superseded is deleted or relabeled as their sources. Contracts cite the new decision.

## Open questions

Not decisions. Each closes by Jules recording an entry in DECISIONS.md.

- Whether `sdlc integrate` deletes a unit's contract file in the squash commit or keeps it. Wait for the trial.
- Whether `.sdlc/` unit records and verdicts are tracked. Currently gitignored by adopt: machine-side records, with what matters carried into the squash commit and the summary.
