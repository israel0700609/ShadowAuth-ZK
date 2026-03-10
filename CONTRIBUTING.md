# Contributing to ShadowAuth-ZK

Thank you for your interest in contributing! This document outlines the process and conventions for this project.

## Branch Strategy

| Branch | Purpose | Merges Into |
|---|---|---|
| `main` | Production-ready, stable code. Protected — requires PR approvals. | — |
| `dev` | Integration branch. All features merge here first. | `main` |
| `feature/<issue>-<desc>` | Feature development tied to a GitHub Issue. | `dev` |
| `fix/<issue>-<desc>` | Bug fixes tied to a GitHub Issue. | `dev` |
| `chore/<desc>` | Maintenance, refactoring, CI changes. | `dev` |

### Workflow

1. Create a branch from `dev`: `git checkout -b feature/3-zk-circuit dev`
2. Make your changes with atomic, conventional commits.
3. Push and open a Pull Request targeting `dev`.
4. After review and CI pass, squash-merge into `dev`.
5. Periodically, `dev` is merged into `main` via a release PR.

## Commit Convention

This project follows [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <short description>

[optional body]

[optional footer]
```

### Types

| Type | Description |
|---|---|
| `feat` | A new feature |
| `fix` | A bug fix |
| `docs` | Documentation only |
| `test` | Adding or updating tests |
| `chore` | Maintenance (CI, deps, config) |
| `refactor` | Code change that neither fixes a bug nor adds a feature |
| `perf` | Performance improvement |
| `security` | Security-related changes |

### Scopes

`circuits`, `crypto`, `network`, `client`, `server`, `ci`, `docs`

## Code Standards

- **Python**: Follows `ruff` linting rules defined in `pyproject.toml`.
- **Circom**: Clean, well-commented circuit templates.
- **Tests**: Every feature PR must include corresponding tests.
- **Security**: All code must pass `ruff` security checks (bandit rules).

## Pull Request Checklist

- [ ] Branch is up to date with `dev`
- [ ] All tests pass (`make test`)
- [ ] Linter passes (`make lint`)
- [ ] Type checks pass (`make typecheck`)
- [ ] Commit messages follow Conventional Commits
- [ ] PR description references the relevant GitHub Issue

## Security

If you discover a security vulnerability, please report it privately — do **not** open a public issue.
