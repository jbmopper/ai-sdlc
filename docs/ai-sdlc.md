# Personal AI Development Lifecycle

Status: Maintained draft, reconciled 2026-09-11 from the September 10 draft, the September 11 alternative, and the September 11 recursive synthesis. Those three files are retired and remain in Git history; the reconciliation merged to `main` on 2026-09-14 as pull request #1. The lifecycle and standing requirements are Julius's direction, developed from his [initial wants](ai-dev-wants.md). Paragraphs marked *Proposal* are agent suggestions awaiting his decision. Nothing here authorizes a hook, merge, archival move, or deletion. Adoption is explicit and project-scoped, and no trial project is chosen. `aur-detonationpot` was named here as the first bounded trial by that same reconciliation; Julius removed it on 2026-09-17 as an artifact of the reconciliation rather than his direction. The qualification trial waits for a real change in a real project.

## 1. Purpose

Build a personal, agent-based SDLC that carries work from ideas through release and stock-taking. It preserves Julius's intent, makes consequential questions salient before their answers are embedded in code, and lets useful work proceed without constant supervision. It compensates for user omissions as well as agent errors.

The project's place in Julius's priorities guides scope, quality, and effort. The desired result is a complete release train, frequent integration, clean working environments, and a public repository that explains the finished product well.

Standing requirements:

- Preserve explicit decisions and recover lost ones from original sources, not from chains of agent summaries.
- Keep obsolete drafts and contaminated intermediates out of routine agent context.
- Preserve meaning when translating specifications into designs, prompts, code, tests, and delegated assignments.
- Surface deferred questions when work starts to depend on them, so Julius decides as matters become salient rather than anticipating every dependency.
- Gate selectively: some checks return to Julius; others use an independent subagent to confirm fidelity to a settled specification. Agents can check fidelity; they cannot establish new intent.
- Make effort predictable early enough that implementation runs independently. No approval churn, no unbounded test, review, or repair loops.
- Keep code, prompts, and documents complete yet minimal. Communicate in concise full sentences with concrete decision support.
- Explain test coverage. Catalog small bugs and corner cases and surface them before spending effort on them. Excess testing and incidental fixes are suspected waste to investigate, not settled conclusions.
- Integrate and clean up agent-owned branches and worktrees proactively under established permissions. Preserve unrelated and unintegrated work.
- Target Claude first, with records, procedures, and checks reusable elsewhere.

## 2. Phase model

Phases organize work and its outputs. They are not a fixed sequence of meetings or one agent call per row. Architecture and planning are revisited when new information changes an assumption.

| Phase | Responsibility | Result carried forward |
| --- | --- | --- |
| Intake | Understand goals, ideas, priorities, constraints, and broad effort. | A project brief and an initial scope for investigation. |
| Architecture | Context preparation, discovery, research, specification, and design, worked together. | A product specification and supporting design, with decisions and explicitly deferred questions. |
| Planning | Translate the architecture into work units, assignments, model choices, context, prompts, tests, review, and integration arrangements. | An executable plan and checked delegation instructions. |
| Implementation | Carry out scoped assignments with the planned test-driven process; record evidence and surface discoveries. | Reviewable changes, test results, and a concise work record. |
| Verification | Evaluate behavior, specification fidelity, meaningful coverage, and review findings. | Acceptance evidence and a disposition for each finding. |
| Integration | Merge reviewed increments and retire their workspaces. | Integrated work, recorded follow-ups, cleaned-up branches and worktrees. |
| Release | Build and operate the infrastructure, CI/CD, release documentation, and regression process for larger units. | A verified release and an operational handoff. |
| Operations and closure | Take stock after release, collect learnings, update documentation, clean up, propose next steps. | An accurate project state and input to the next intake. |

Implementation, verification, and integration form a frequent local cycle. Release is a separate stream that consumes integrated work and can build its tooling in parallel with product development. Operations and closure follows release; routine worktree hygiene belongs to integration.

## 3. Intake

Establish what Julius wants, why now, possible directions, major constraints, and a broad effort estimate with its major uncertainties. The project brief states the project's place among his priorities, intended users and outcomes, and the appropriate level of finish. It lets agents tell a useful improvement from an expensive distraction. Update it when priorities change; do not ask Julius to restate settled direction per assignment.

## 4. Architecture

Context preparation, discovery, research, specification, and design inform each other rather than producing documents that quietly disagree. The work includes reading current instructions, decisions, and implementation; reconciling conflicts and recovering lost direction; researching what is possible; exploring behavior, alternatives, and tradeoffs with Julius; writing the specification and design; and identifying verification needs, release implications, and questions that can wait.

The specification describes intended behavior, boundaries, and observable success conditions. The design explains how to achieve them. Agent-proposed interpretations stay distinguishable from Julius's directions.

A deferred question records the work it affects and the trigger that makes an answer necessary. Work reaching that trigger surfaces the question, with evidence and options prepared, before implementing an assumed answer.

## 5. Planning

Planning designs how agents perform the work: division of work, assignments, model selection, context preparation, prompt writing, sequestration, cleanup, and accuracy checks.

Model choice weighs the total cost of an accepted result, including coordination and repair. Strong models go where planning, synthesis, or prompt writing warrants them; bounded assignments go to cheaper models. For each work unit, establish:

- Scope, dependencies, ownership, and the specification and design revisions it implements.
- What runs independently, what shares interfaces or files, and how results combine.
- The model and role, with a reason matched to ambiguity and consequence.
- The authoritative context to provide, what must be re-read, and what must be excluded.
- A concise prompt covering task, constraints, outputs, testing, logging, review, escalation, and handoff.
- An effort allocation with limits on experiments, tests, and repeated repair, within the allowance agreed at intake.
- The review and integration policy: which findings block, which are recorded, which return to Julius.

Each work unit carries one logical contract, scaled to the work. A small task may need only a paragraph and references; shared requirements stay in their source of record rather than being cloned into every child.

| Element | Required meaning |
| --- | --- |
| Purpose and relationship | Why this work matters, its parent if any, and the outcome it supports. |
| Scope and return | Deliverable, exclusions, affected interfaces, and where the result is accepted or released. |
| Authoritative inputs | Relevant requirements, decisions, source references, revisions, and unresolved questions. |
| Execution arrangement | Role, model, context, prompt, workspace, ownership, tools, and permitted actions. |
| Effort and stopping | Allowance, experiment and repair limits, escalation triggers, and allowed delegation. |
| Acceptance and closure | Observable criteria, evidence, review, integration, and cleanup obligations. |

Children inherit their parent's constraints and cannot enlarge authority, reset budgets, or rewrite the parent's requirements.

Before dispatch, check assignments for omissions, conflicting instructions, and specification drift, and check that context is clean. This check must not rest solely on the writer declaring its own instructions correct. The plan lets agents act within boundaries without repeated permission and says when to stop, reallocate, re-review, or ask. On return, inspect the actual artifacts and evidence before a child's findings enter the parent's context; reconcile them rather than appending a raw transcript.

## 6. Implementation, verification, and integration

**Implementation.** The writer works against the assigned specification, establishing expected behavior through tests or other acceptance evidence as it goes. It records results, assumptions, discoveries, and deviations. The test-driven procedure comes with the assignment, not each writer's guess. New bugs and corner cases are cataloged and surfaced, to Julius by preference or otherwise to the coordinator under the triage policy, before effort is spent on them. Changes of intent or scope return through architecture and planning.

**Verification.** An independent reviewer receives deliberately selected context, not the writer's whole narrative. It checks the actual changes against the specification, source decisions, and current evidence. It can judge fidelity; it cannot change acceptance criteria to fit the result. Reviews explain what the tests establish and what they miss, and assess test quality: meaningful behavior, useful assertions, duplication, maintenance cost. Findings are classified as blocking, deferred, suggestion, or needs-decision, so a review is not an instruction to fix everything.

**Integration.** Julius's preferred flow: after the writer's test-driven work and review, record nonblocking bugs, merge, and delete the worktree and branch. A review hook is the candidate mechanism; its contract is designed together with the writer prompt, including the conditions that interrupt the normal flow. The subprocess accounts for the reviewed revision, concurrent changes, merge-conflict resolutions, checks on the integrated result, and evidence that useful work is preserved before cleanup. A minor finding must not become an unlimited repair cycle, and recording a finding must not silently waive an unmet specification.

Merge, push, release, and history rewriting carry different consequences and do not inherit authority from permission to implement.

## 7. Release

Release is engineering work on infrastructure, environments, CI/CD, packaging, deployment, regression testing, and release notes, planned alongside the product and developed in tracked increments. Its unit is a release candidate. Assignment tests establish the local change; integration checks establish fit; release regression establishes that the combined product can ship. Existing evidence is reused where its inputs still apply.

The stream covers infrastructure and configuration changes, secrets delivery, migrations, artifact construction; release contents, notes, user documentation, and public repository quality; regression and compatibility testing including the disposition of known defects; promotion authority, deployment, and rollback or forward repair; and verification of what actually shipped. A defect can be acceptable for integration and still block release.

## 8. Operations and closure

After release, confirm outcomes, examine regressions and user observations, and compare the result with the purpose and effort spent. Collect learnings from logs and artifacts where they reveal drift, waste, or useful practice; check a learning before it becomes a standing rule. Update specifications, designs, instructions, decisions, and tracker state where the evidence warrants. Clean up stale documentation and residue without disturbing unrelated work. Generate next-step proposals for Julius; they feed intake rather than authorizing another cycle. The handoff distinguishes implemented, integrated, released, verified, and pending work.

## 9. Records

Each kind of record has an authority and a lifecycle. This is a logical organization, not a file per row.

| Material | Authority | Maintenance |
| --- | --- | --- |
| User instructions and project brief | Establish intent, priorities, constraints. | Preserve original direction; reconcile changes explicitly. |
| Specification and design | Define the intended product and approach. | Keep current, consistent, and tied to decisions. |
| Decision record | Preserve explicit decisions with scope, source, and supersession. | Update as decisions occur or are recovered; resolve ambiguity with Julius. |
| Work tracker | Assignments, dependencies, blockers, status, follow-ups. | Reconcile with plans and decisions. |
| Plans and generated prompts | Executable assignments and context. | Review for fidelity and efficiency; keep revisions needed to explain a run. |
| Agent work logs | Observations, actions, evidence, handoffs. | Keep concise; review for correctness and learnings. |
| Verification evidence | Support acceptance and dispositions. | Name the exact code, prompt, configuration, and data assessed. |
| Public and operational documentation | Explain the maintained product and its operation. | Update with the change and at closure. |
| Historical and sequestered material | Preserve history without supplying routine context. | Restrict discovery; retrieve deliberately for recovery. |

Decisions, task status, and evidence each have one source of record; do not copy results into several stores. A polished summary does not gain authority by repetition. Product prompts and evaluation instructions are implementations of the specification too: check them for omitted requirements, invented policies, and examples that accidentally prescribe behavior.

*Proposal, restored from the September 9 draft.* Each consequential entry in the decision record preserves: the decision in plain language with its scope and conditions; the original source with enough context to check its meaning; whether it is explicit user direction, an interpretation awaiting confirmation, or an agent proposal; the date or revision and the authority that established it; and any decision it supersedes, with the work affected. A summary, a closed issue, passing tests, or an agent-authored design cannot by themselves establish that Julius approved something.

## 10. Coordinator recovery

Recovery replaces a planning or coordination session whose context was compacted or lost, and supports deliberately starting a fresh coordinator or writer. Julius describes it as a structured fold over maintained documents and the tracker: read records in a defined order, reconcile them, and produce a current working state.

Proposed order:

1. Project purpose, user instructions, and authority rules.
2. Explicit decisions and their sources, applying supersession and noting unresolved conflicts.
3. Current specification and design, reconciled with those decisions.
4. Plan and tracker state: in-progress work, blockers, deferred-question triggers, remaining allowances.
5. Relevant logs, prompts, review outcomes, evidence, and integration and release state, checked against actual artifacts.
6. A compact working account with source references, disagreements, and the next authorized actions. Verify consequential interpretations before dispatching work.

Recovery rebuilds from durable records, never by summarizing an earlier summary. It preserves unresolved questions, distinguishes planned, attempted, and completed work, and reconstructs established allowances and permissions so a spent budget is not renewed and granted permission is not re-requested. Recovering a lost user decision consults original historical material, carries forward clear direction with provenance, and returns ambiguity to Julius. If recovered direction changes active work, identify the affected prompts, documents, and evidence before resuming.

## 11. Sequestration and cleanup

Sequestration layers measures according to material and risk: status headers, curated context lists, search and read restrictions, compressed archives, and archival branches or separate storage. Headers stay useful even under stronger isolation. Compression adds friction, not prevention; an archival branch leaves material reachable through Git. Evaluate the combined behavior under real searches, explicit reads, history access, memories, issue notes, and inherited conversation context. Moving a file does not clean a prompt that already copied it; contaminated context may need replacing.

Before retiring working material, preserve unique decisions and evidence, update links, and avoid stacking successive drafts beside current documents.

Git history rewriting is an unresolved option, not a default. Any proposal names the exposure simpler measures cannot address, the history and collaborators affected, recovery provisions, and the specific authorization sought.

## 12. Effort and authority

Agree broad effort at intake; refine during architecture and planning. Budget implementation, tests, review, repair, coordination, and release, not only the writer's calls. Routine checks and retries covered by the plan proceed without approval. Surface material scope changes, unresolved user choices, exhausted allowances, or repeated lack of progress with a short explanation and recommendation; batch minor items where useful. Reaching a limit produces an evidence-backed decision about further work. It never justifies declaring success or weakening acceptance.

Independent agents may resolve fidelity to settled specifications. New intent, reserved choices, and consequential ambiguity return to Julius. Approval attaches to the meaningful content and scope of what was approved: material changes to behavior, constraints, effort, or acceptance need reconsideration; editorial changes do not. When a shared specification or decision changes, identify the affected consumers.

Information quality is cost control. Accurate prompts, clean context, and reconstructible state reduce rework, and budget controls must not paper over contamination by asking Julius what he already said.

## 13. Gates

A gate defines its trigger, required evidence, resolver, authority, relevant input revisions, and permitted next actions. Gates are checks inside phases and inside the local cycle, not only at phase boundaries.

| Boundary | What must be established | Who resolves it |
| --- | --- | --- |
| Commit to scope or design | Purpose, observable outcome, dependencies, and salient decisions are clear enough. | Agents apply settled direction; Julius resolves new intent and reserved choices. |
| Dispatch or materially revise an assignment | Context and prompt preserve the contract; capabilities and allowance fit the work. | Mechanical checks plus independent fidelity review. |
| Change an assumption or open nested work | Impact, authority, affected consumers, and the parent's blocking condition are explicit. | Coordinator within standing policy; Julius beyond it. |
| Accept and integrate a result | Current evidence satisfies the contract and the result fits its target branch. | Checks and independent review; disputed requirements return to Julius. |
| Promote a release | The combined artifact, known defects, operational readiness, and promotion authority are acceptable. | Release checks and designated authority, including Julius where required. |
| Resume or close work | Reconstructed state is current; dependencies, evidence, obligations, and cleanup are accounted for. | Coordinator, with escalation for unresolved authority or ambiguity. |

Outcomes are proceed, repair within scope, open nested work, user decision required, or stop and defer. A failure names what is missing and what would resolve it. Legitimate waiting ends the execution loop cleanly. A required check must not silently become optional because its handler is missing or malformed, and a writer must not be able to edit its own approval record or disable a control to advance.

## 14. A small change, end to end

*Proposal.* The phases must collapse gracefully for small work. For a bug fix with a clear specification and no reserved choice:

1. Intake and architecture are satisfied by the existing brief and specification. The coordinator confirms nothing deferred is triggered.
2. Planning is one assignment: a cheap model, the failing case, the relevant specification text, an explicit test procedure, and a small repair limit.
3. The writer reproduces the bug in a test, fixes it, and records any adjacent corner cases without touching them.
4. Verification is one independent review confirming the fix matches the specification and the test is meaningful.
5. Integration merges, records the corner cases as follow-ups, and deletes the worktree and branch under standing permission.
6. Release and closure occur with the next release candidate.

Julius hears about it once, at a batched summary, unless a step trips a return-to-user condition. If a real project change cannot be walked through this cleanly, the process is too heavy for its class of work.

## 15. Qualification and open decisions

Qualify the process on deliberate failures and on useful autonomy: unapproved design, lost decisions, contaminated context, stale evidence, broken controls, incidental scope growth, failed releases, unsafe cleanup; and normal progress without repeated permission, delegation to cheaper models, coordinator restart, and merging with a recorded nonblocking bug. A configured hook or role name is not proof of enforcement. Measure correction effort, rework, verification cost, false blocks, escaped defects, interruptions, and leftover artifacts; consolidate machinery that adds cost without improving outcomes.

Open decisions, unordered. Each closes by recording a decision, not by shipping code, and listing it here is not permission to choose it.

These arrived with `P0`/`P1`/`P2` labels and a gating order when they moved here from the retired `ai-sdlc-backlog.jsonl` during the September 11 reconciliation. Those priorities were an artifact of the beads tracker that reconciliation removed, not Julius's direction, and were dropped on 2026-09-17. Nothing below is sequenced until he sequences it.

1. The decision record's form and protected location, and how approval is recorded without friction.
2. How gates map onto tracker records, workflow state, and skills without excessive artifacts.
3. How recovery reaches history while routine agents stay isolated. This is in direct tension with the want that agents not pollute themselves with old documents.
4. Which changes always return to Julius versus standing authority.
5. Which commit, merge, push, release, and cleanup permissions are granted proactively, and at what scope.
6. What an independent reviewer receives and how disputes resolve.
7. What verification and triage visibility is useful without interruption noise.
8. Effort limits, no-progress rules, and fast paths by class of work.
9. Which release responsibilities are common versus per-project.

Running the first bounded qualification trial is the open action rather than a decision: one real change through the complete workflow, deliberately exercising gate failures before relying on unattended execution. It was listed as a tenth decision until 2026-09-17. No project is chosen for it.

Closed on 2026-09-10: rebuilding this document around the revised phase model.

*Proposal: interim answers, parked.* These were written to let a first trial start in `aur-detonationpot`. That trial is not happening and nothing has replaced it, so they are parked rather than pending: none is direction, each still assumes a trial, and each becomes direction only when Julius confirms it against whatever project he picks, with the confirmation recorded in that project's decision record.

1. Decision record: a `docs/decisions.md` file in the project repository, append-only by convention, one entry per decision in the section 9 format. Approval is recorded by Julius merging the pull request that adds the entry, or by a quoted, dated instruction. Protection is Git history and review, with no mechanism yet.
2. Gates: prose checklists in the plan, applied by the coordinator. No hooks or skills until the trial shows which gates actually trip.
3. History: routine agents read only the current documents the project's `AGENTS.md` lists. Recovery may read Git history and retired material on explicit instruction and must reconcile before use.
4. Always return to Julius: new intent, scope change, reserved choices named in the brief, an exhausted allowance, a disputed specification, and anything the project's working agreement reserves.
5. Standing permissions for the trial: commit and push to feature branches, open pull requests. Merge, push to main, history rewriting, release, and deleting branches with unintegrated work are not granted.
6. Reviewer inputs: the specification text, the decision record, the diff, and test output, never the writer's transcript. Disputes return to Julius.
7. Visibility: one batched summary per work unit in the pull request description, with findings classified as blocking, deferred, suggestion, or needs-decision.
8. Effort: set per work unit in its contract. Two failed repairs of the same finding stop the work and produce a report.
9. Release: per-project until a second project shows what is common.

Adoption remains explicit and project-scoped, following this repository's inspect-and-plan working agreement.
