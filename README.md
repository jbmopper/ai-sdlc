# ai-sdlc

Tools that run a personal, agent-based software development lifecycle in a
project: a protected decision record, a per-unit contract that is the
definition of ready, isolated worktrees for writers, an independent review
with enforced verdict rules, and a gated squash merge that cleans up after
itself. Claude first, provider agnostic: the logic is scripts and files any
agent can use; hooks are thin wrappers.

Status: increment one is built and tested. No real project has run a unit
through it yet.

- [WORKFLOW.md](WORKFLOW.md): each step, its deliverable, its gate, and the
  tool that enforces it.
- [docs/ai-sdlc.md](docs/ai-sdlc.md): the lifecycle design the tools implement.
- [DECISIONS.md](DECISIONS.md): what has been decided, by whom, and when.
- [AGENTS.md](AGENTS.md): how agents work in this repository.

```bash
bin/sdlc --help
uv run --with pytest python -m pytest -q tests
```
