## Plan: Repository-Wide GitHub Actions

Create GitHub Actions coverage for all applications while keeping pull-request checks fast and separating heavyweight builds and releases.

**Steps**

1. Add `.github/workflows/ci.yml` for every branch push and pull request:
   - Use `on: push` without a branch filter so every pushed commit on every branch is checked.
   - Run the same checks for pull requests before merge.
   - Add concurrency cancellation for superseded runs while preserving the latest commit's result.
   - Use least-privilege read permissions and expose one required aggregate `ci` status for branch protection.
2. Add a **fast-checks** workflow/job group for every branch push and pull request:
   - Run Python unit tests independently for `backend`, `aibackend`, and `aimodel`.
   - Run Python Ruff format and lint checks for `backend`, `aibackend`, `aimodel`, and `scripts`, using a pinned Ruff version and committed configuration.
   - Install frontend dependencies from the committed Bun lockfile and run TypeScript checks.
   - Run TypeScript formatting and lint checks with a pinned Biome version, or use pinned Prettier and ESLint versions if Biome is not adopted.
   - Run `dart format --output=none --set-exit-if-changed`, `flutter analyze`, and `flutter test` for both Flutter apps.
   - Run `cargo fmt --check`, `cargo clippy --all-targets --all-features -- -D warnings`, and `cargo test` for `mobile/rust`.
   - Keep these checks global so shared workflow, formatter, linter, and dependency configuration changes validate every application; use path filters only to skip unrelated heavyweight jobs.
3. Add a **service-checks** workflow/job group:
   - Validate `docker compose config` and build the backend, frontend, aibackend, and aimodel images.
   - Run lightweight backend, frontend, and aibackend startup probes on every branch push without requiring the GGUF model.
   - Probe the backend root/OpenAPI/representative expense endpoints and the frontend page plus `/api` proxy.
   - Probe `aibackend` `/health` with mocked or containerized dependencies and one deterministic chat-flow endpoint.
   - Reserve model-backed health checks for the default branch, version tags, or manual runs when the GGUF artifact is available.
   - Always collect service logs and shut down processes/containers after probes, including on failure.
4. Add a **release-checks** workflow/job group for version tags and manual dispatch:
   - Build Android APKs and iOS IPAs on the appropriate runners.
   - Publish the four Docker images to the configured registry.
   - Attach APK and IPA artifacts to tagged GitHub releases.
   - Set explicit artifact retention limits for non-release APKs and IPAs to control storage costs.
   - Keep iOS signing controlled by GitHub secrets and make unsigned builds available when signing secrets are absent.
5. Pin all CI tool versions and commit lockfiles before enabling automated upgrades:
   - Pin Python/Ruff, Bun, Biome or Prettier/ESLint, Flutter/Dart, Rust toolchain, and GitHub Action versions.
   - Require lockfile updates in dependency pull requests and fail checks when generated lockfiles are stale.
6. Configure path filters carefully:
   - Run fast formatting, lint, type, and unit-test checks globally on every pushed commit and pull request.
   - Allow only heavyweight service, model, platform-build, and release jobs to use validated path or event filters.
7. Add an always-running `ci-success` aggregate job:
   - Use `if: always()` and require all fast-check and applicable service-check jobs to succeed.
   - Fail when any required job fails or is unexpectedly skipped.
   - Report intentionally skipped model and release jobs separately without hiding required-check failures.
8. Add `.github/workflows/release.yml` for `vMAJOR.MINOR.PATCH` tags and manual dispatch.
9. Add automated dependency upgrades:
   - Add `.github/dependabot.yml` for Python requirements, Bun/npm dependencies, Cargo dependencies, Flutter/Dart pubspecs, Dockerfiles, and GitHub Actions.
   - Group non-breaking patch/minor updates by ecosystem and limit update frequency to weekly.
   - Require CI checks on Dependabot pull requests before merging.
   - Keep major upgrades separate and document any manual migration steps.
10. Update setup documentation with CI commands, release tags, runner limitations, model-weight handling, dependency automation, artifact retention, and required secrets.

**Relevant files**

- `backend/tests/`
- `aibackend/tests/`
- `aimodel/tests/`
- `frontend/package.json`
- `frontend/Dockerfile`
- `mobile/pubspec.yaml`
- `mobile/rust/Cargo.toml`
- `expense-helper/mobile/pubspec.yaml`
- `docker-compose.yml`
- `README.md`
- `docs/setup.md`
- New `.github/workflows/ci.yml`
- New `.github/workflows/release.yml`
- New `.github/dependabot.yml`
- New Ruff configuration and lockfile/tool configuration
- New frontend Biome or Prettier/ESLint configuration and lockfile updates

**Verification**

1. Run all existing Python, TypeScript, Rust, and Flutter test commands.
2. Run every formatter and linter locally with the same pinned versions used by CI.
3. Validate workflow YAML, Dependabot configuration, permissions, and `docker compose config`.
4. Execute CI on multiple branches and confirm every pushed commit receives fast-check results scoped per application.
5. Confirm service checks use lightweight probes, collect logs, and clean up after success and failure.
6. Confirm the `ci-success` job always runs and fails when any required job fails or is unexpectedly skipped.
7. Perform a manual unsigned Android and iOS release rehearsal with artifact retention limits.
8. Verify tagged releases publish APKs, iOS IPAs, and Docker images.
9. Confirm fork pull requests cannot access release secrets.
10. Confirm Dependabot opens grouped patch/minor update pull requests and those pull requests run the complete required CI suite.

**Decisions**

- Docker images will be published to a configured registry.
- Android artifacts will not be built for every pull request.
- Releases use `vMAJOR.MINOR.PATCH` tags.
- Fast formatting, lint, type, and unit-test checks run on every pushed commit and pull request; service and release checks use event/path rules described above.
- Ruff is the Python formatter/linter, and Biome is the preferred TypeScript formatter/linter unless repository compatibility requires pinned Prettier and ESLint.
- GitHub Actions and language tool versions are pinned before Dependabot is enabled.
- Release and temporary mobile artifacts have explicit retention limits.
- Workflows declare explicit least-privilege permissions, with elevated release permissions isolated to tagged release jobs.
- Health, format, and lint checks run on every pushed commit across every branch and on every pull request. GitHub Actions can only check commits pushed to GitHub, not commits that exist solely in a local repository.
- Health checks run against real local service processes or containers, while model-weight-dependent checks are opt-in or tag-only.
- Dependency version upgrades are automated with Dependabot, but major upgrades remain separately reviewable.
- GPU inference and GGUF model downloads remain manual or tag-only.
- Production deployment is excluded until the target environment and deployment credentials are defined.

The plan is saved in `/memories/session/plan.md`.