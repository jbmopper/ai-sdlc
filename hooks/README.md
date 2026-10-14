# Hooks

Thin wrappers only. Each calls a `bin/sdlc` subcommand that holds the logic
and has tests. A hook that cannot find `sdlc` must fail closed.

- `git/pre-commit`, `git/pre-push`: installed into an adopted project by
  `sdlc adopt`. Provider agnostic.
- `claude/settings.json`: a Claude Code hook fragment, merged into the adopted
  project's `.claude/settings.json` by `sdlc adopt`. Gives the writer an
  immediate refusal instead of a failure at commit time.
