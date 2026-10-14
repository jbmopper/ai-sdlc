# Hooks

Thin wrappers only. Each calls a `bin/sdlc` subcommand that holds the logic
and has tests. A hook that cannot find `sdlc` fails closed.

- `git/pre-commit`, `git/pre-push`: templates installed into an adopted
  project's git hooks directory by `sdlc adopt`, which fills `@SDLC@` with the
  absolute path to `bin/sdlc` and `@CHAINED@` with any pre-existing hook,
  which runs after the gate passes. Provider agnostic.
- `claude/settings.json`: a Claude Code hook fragment, merged into the adopted
  project's `.claude/settings.json` by `sdlc adopt`. Gives the writer an
  immediate refusal instead of a failure at commit time.
