# GitHub CI and Release Status

Repository: [itsvrushabh/expense-organizer](https://github.com/itsvrushabh/expense-organizer)

This document separates the status of the protected `main` branch, the active development branch `ci/first_commit`, and version-tag releases. Badges show the latest GitHub Actions result for the selected ref; click a badge to open its workflow history.

## Workflow Status

### Main Branch

| Workflow | Status | Details |
|---|---|---|
| CI / Success | [![CI Success](https://github.com/itsvrushabh/expense-organizer/actions/workflows/ci-success.yml/badge.svg?branch=main)](https://github.com/itsvrushabh/expense-organizer/actions/workflows/ci-success.yml?query=branch%3Amain) | Aggregate branch-protection check |
| CI / Python | [![CI Python](https://github.com/itsvrushabh/expense-organizer/actions/workflows/ci-python.yml/badge.svg?branch=main)](https://github.com/itsvrushabh/expense-organizer/actions/workflows/ci-python.yml?query=branch%3Amain) | Python tests, Ruff formatting, and linting |
| CI / Frontend | [![CI Frontend](https://github.com/itsvrushabh/expense-organizer/actions/workflows/ci-frontend.yml/badge.svg?branch=main)](https://github.com/itsvrushabh/expense-organizer/actions/workflows/ci-frontend.yml?query=branch%3Amain) | Bun, Biome, and TypeScript checks |
| CI / Flutter | [![CI Flutter](https://github.com/itsvrushabh/expense-organizer/actions/workflows/ci-flutter.yml/badge.svg?branch=main)](https://github.com/itsvrushabh/expense-organizer/actions/workflows/ci-flutter.yml?query=branch%3Amain) | Both Flutter applications |
| CI / Rust | [![CI Rust](https://github.com/itsvrushabh/expense-organizer/actions/workflows/ci-rust.yml/badge.svg?branch=main)](https://github.com/itsvrushabh/expense-organizer/actions/workflows/ci-rust.yml?query=branch%3Amain) | rustfmt, Clippy, and native tests |
| CI / Services | [![CI Services](https://github.com/itsvrushabh/expense-organizer/actions/workflows/ci-services.yml/badge.svg?branch=main)](https://github.com/itsvrushabh/expense-organizer/actions/workflows/ci-services.yml?query=branch%3Amain) | Docker and service health probes |

### Current Branch: `ci/first_commit`

| Workflow | Status | Details |
|---|---|---|
| CI / Success | [![CI Success](https://github.com/itsvrushabh/expense-organizer/actions/workflows/ci-success.yml/badge.svg?branch=ci%2Ffirst_commit)](https://github.com/itsvrushabh/expense-organizer/actions/workflows/ci-success.yml?query=branch%3Aci%2Ffirst_commit) | Aggregate branch-protection check |
| CI / Python | [![CI Python](https://github.com/itsvrushabh/expense-organizer/actions/workflows/ci-python.yml/badge.svg?branch=ci%2Ffirst_commit)](https://github.com/itsvrushabh/expense-organizer/actions/workflows/ci-python.yml?query=branch%3Aci%2Ffirst_commit) | Python tests, Ruff formatting, and linting |
| CI / Frontend | [![CI Frontend](https://github.com/itsvrushabh/expense-organizer/actions/workflows/ci-frontend.yml/badge.svg?branch=ci%2Ffirst_commit)](https://github.com/itsvrushabh/expense-organizer/actions/workflows/ci-frontend.yml?query=branch%3Aci%2Ffirst_commit) | Bun, Biome, and TypeScript checks |
| CI / Flutter | [![CI Flutter](https://github.com/itsvrushabh/expense-organizer/actions/workflows/ci-flutter.yml/badge.svg?branch=ci%2Ffirst_commit)](https://github.com/itsvrushabh/expense-organizer/actions/workflows/ci-flutter.yml?query=branch%3Aci%2Ffirst_commit) | Both Flutter applications |
| CI / Rust | [![CI Rust](https://github.com/itsvrushabh/expense-organizer/actions/workflows/ci-rust.yml/badge.svg?branch=ci%2Ffirst_commit)](https://github.com/itsvrushabh/expense-organizer/actions/workflows/ci-rust.yml?query=branch%3Aci%2Ffirst_commit) | rustfmt, Clippy, and native tests |
| CI / Services | [![CI Services](https://github.com/itsvrushabh/expense-organizer/actions/workflows/ci-services.yml/badge.svg?branch=ci%2Ffirst_commit)](https://github.com/itsvrushabh/expense-organizer/actions/workflows/ci-services.yml?query=branch%3Aci%2Ffirst_commit) | Docker and service health probes |

## Release and Version Status

| Item | Status | Details |
|---|---|---|
| Latest published version | [![Latest release](https://img.shields.io/github/v/release/itsvrushabh/expense-organizer?display_name=tag&sort=semver)](https://github.com/itsvrushabh/expense-organizer/releases/latest) | Latest published GitHub release |
| Release history | [View releases](https://github.com/itsvrushabh/expense-organizer/releases) | APK, IPA, and release notes history |
| Version tags | [View tags](https://github.com/itsvrushabh/expense-organizer/tags) | Releases use `vMAJOR.MINOR.PATCH`, for example `v1.2.3` |
| Docker images | [View packages](https://github.com/itsvrushabh?tab=packages&repo_name=expense-organizer) | Tag-published service images in GHCR; current tag: `v0.0.2` |

A valid version tag starts the publishing workflow:

```bash
git tag v1.2.3
git push origin v1.2.3
```

Tag releases publish immutable Docker image tags and attach mobile artifacts to the GitHub release. Manual Release workflow runs are validation-only and do not publish images or create releases. Android artifacts are preview builds, iOS artifacts are unsigned, and the AI model GGUF file must be supplied separately.

### Published Images

The `v0.0.2` Docker jobs completed successfully. Four separate images are published:

```text
ghcr.io/itsvrushabh/expense-organizer-backend:v0.0.2
ghcr.io/itsvrushabh/expense-organizer-frontend:v0.0.2
ghcr.io/itsvrushabh/expense-organizer-aibackend:v0.0.2
ghcr.io/itsvrushabh/expense-organizer-aimodel:v0.0.2
```

Package pages:

- [backend](https://github.com/users/itsvrushabh/packages/container/package/expense-organizer-backend)
- [frontend](https://github.com/users/itsvrushabh/packages/container/package/expense-organizer-frontend)
- [aibackend](https://github.com/users/itsvrushabh/packages/container/package/expense-organizer-aibackend)
- [aimodel](https://github.com/users/itsvrushabh/packages/container/package/expense-organizer-aimodel)

GHCR packages are private by default. Sign in before pulling private images:

```bash
echo "$CR_PAT" | docker login ghcr.io -u itsvrushabh --password-stdin
docker pull ghcr.io/itsvrushabh/expense-organizer-backend:v0.0.2
```

To make an image visible without authentication, open the package under the repository
owner's GitHub **Packages** page, open **Package settings**, and change package visibility
to public. Repeat for each service image; repository workflow permissions alone do not
change GHCR package visibility.

## Status Meanings

| Status | Meaning |
|---|---|
| `Success` / `Passed` | All required workflow steps completed successfully. |
| `Failure` / `Failed` | At least one required job or step failed. |
| `Queued` | GitHub accepted the run but has not started it. |
| `In progress` / `Running` | The workflow is currently executing. |
| `Cancelled` | The run was manually stopped or replaced by a newer run. |
| `Skipped` | A conditional job was intentionally not executed. |
| `No status` | The selected branch or tag has not run that workflow yet. |

## Inspect Another Branch or Commit

GitHub badges are fixed to the ref shown in their table. Use the Actions page or GitHub CLI for another branch or commit:

```bash
gh run list --workflow "CI / Success" --branch BRANCH_NAME
gh run list --workflow "CI / Python" --branch BRANCH_NAME
gh run list --workflow "CI / Frontend" --branch BRANCH_NAME
gh run list --workflow "CI / Flutter" --branch BRANCH_NAME
gh run list --workflow "CI / Rust" --branch BRANCH_NAME
gh run list --workflow "CI / Services" --branch BRANCH_NAME
gh run list --workflow Release --branch BRANCH_NAME
gh run list --workflow "CI / Success" --commit COMMIT_SHA
gh run view RUN_ID --log-failed
gh run watch RUN_ID
```

For branch protection, require the `CI / Success / ci-success` check on `main`.
