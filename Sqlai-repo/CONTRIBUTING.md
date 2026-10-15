# Contributing to SQL.AI

Thanks for helping. SQL.AI protects other people's data, so a few rules matter more here than in most projects.

## Before you start

1. Read the eight non-negotiable rules in [DEVELOPER_MANUAL.md §1](DEVELOPER_MANUAL.md#1-the-rules-that-never-bend).
2. For anything bigger than a small fix, open an issue describing the problem first.
3. Security issues go to [SECURITY.md](SECURITY.md), never to public issues.

## Making a change

1. Branch from `main`: `feat/<short-name>`, `fix/<short-name>` or `docs/<short-name>`.
2. Write tests with the change:
   - policy changes: golden tests (`policy/tests/`), including at least one allow, one block and one edge case;
   - gate logic: lineage, suppression or budget tests, including an attempt to get around the rule;
   - prompts or models: all three eval suites.
3. Update documentation in the same pull request ([DOCUMENTATION_GUIDELINES.md §12.4](DOCUMENTATION_GUIDELINES.md#124-when-docs-must-change)).
4. Add an entry to [CHANGELOG.md](CHANGELOG.md) under an *Unreleased* heading.
5. Use Conventional Commits: `feat(analyzer): resolve aliases through derived tables`.

## Pull request checklist

- [ ] Keeps every rule in DEVELOPER_MANUAL §1.
- [ ] No check depends on column names or raw SQL text where lineage or the AST should be used.
- [ ] Tests added and passing, including a bypass attempt for gate changes.
- [ ] No real data, secrets or internal hostnames in code, tests, fixtures, screenshots or logs.
- [ ] User-facing messages say what happened and what to do next.
- [ ] Docs and changelog updated.
- [ ] Security reviewer requested for `policy/`, `services/executor/`, `services/audit/`, `services/ai/prompts/` and lineage, suppression or budget code.

## Changing the standalone demo

`index.html` is built from a template plus the bundled query engine. Keep it a single file with no network dependencies other than fonts. After changes:
- run the bypass probes and end-to-end tests;
- confirm no page errors and no horizontal scrolling at 390 px width;
- update the README's "Things to try" if behavior changed.

## Code of conduct

Be respectful, assume good intent, and keep discussion on the work. Report unacceptable behavior to [CONDUCT CONTACT].
