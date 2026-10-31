# Developer guide

This guide explains the contributor workflow for the generated project.

## Local workflow

The public entrypoint for formatting, linting, typechecking, tests, and
spelling is `make all`. Narrower Make targets may be invoked when investigating
a specific failure, and changes should be reconciled with the aggregate gate
before being considered complete.

`make lint` runs Ruff, `interrogate --fail-under 100 $(PYTHON_TARGETS)` for
100% docstring coverage across `$(PYTHON_TARGETS)`, and Pylint.

`make typecheck` runs `ty`, pinned in the dev dependency group (`ty==0.0.56`):
unpinned installations broke repositories when ty 0.0.56 landed. Bump the pin
deliberately — update the version and fix any new diagnostics in the same pull
request.

Run `make audit` as the dependency vulnerability gate. It runs `pip-audit` for
Python dependencies, and Rust-enabled projects also run `cargo audit` from the
`rust_extension` crate directory.

## Automation scripts

The [Scripting standards](scripting-standards.md) document provides guidance
for adding or updating helper scripts. New and updated scripts are expected to
use `Cyclopts` for command-line interfaces, `cuprum` for typed and
catalogue-bound external command execution, `pathlib` for filesystem paths, and
`cmd-mox` for tests that mock external executables.

Script changes should update the scripting guide when they introduce a new
convention, command catalogue, testing pattern, or operational expectation that
future contributors need to follow.

## GitHub Actions

The generated repository includes GitHub Actions workflows and local composite
actions under `.github/`.

- `.github/workflows/ci.yml` runs on pushes to `main` and on pull requests. It
  sets up Python 3.13, installs `uv`, validates the generated `Makefile` with
  `mbake`, runs `make build`, `make check-fmt`, `make lint` (Ruff +
  `interrogate --fail-under 100 $(PYTHON_TARGETS)` + Pylint), `make typecheck`,
  `make spelling`, and `make audit` except for Dependabot pull requests via
  `if: github.actor != 'dependabot[bot]'`, then delegates coverage generation
  to the shared coverage action. When the Rust extension is enabled, it also
  sets up Rust, installs Rust lint and test tools, and passes
  `rust_extension/Cargo.toml` to coverage.
- `.github/workflows/audit.yml` runs `make audit` against the default branch
  weekly as the compensating control for the Dependabot CI bypass.
- `.github/workflows/act-validation.yml` runs rendered workflow validation in a
  separate workflow. It installs `act`, checks Docker availability, and runs
  `make test WITH_ACT=1` outside the coverage path.
- `.github/workflows/release.yml` publishes wheels when a `v*.*.*` tag is
  pushed. It builds a pure Python wheel, creates a GitHub release with
  generated release notes, downloads wheel artefacts, and uploads them to the
  tag release.
- `.github/workflows/build-wheels.yml` is a reusable workflow for extension
  builds. It accepts a Python version and builds wheels across Linux, Windows,
  and macOS architectures via `.github/actions/build-wheels`.
- `.github/workflows/coverage-main.yml` is the one CodeScene publisher; see
  "CodeScene coverage publication" below.

- `.github/actions/build-wheels` wraps `cibuildwheel` with `uvx` and uploads
  architecture-specific wheel artefacts.
- `.github/actions/pure-python-wheel` builds a pure Python wheel with
  `uv build --wheel` and uploads the resulting artefact.
- `.github/dependabot.yml` enables dependency update pull requests for GitHub
  Actions and Python packages. Rust-enabled projects also receive Cargo updates.

The `CS_ACCESS_TOKEN` secret belongs in the `codescene` environment, whose
deployment policy admits `main` alone. Without it the publisher skips the
upload, writes a warning and still succeeds. If a repository- or
organization-level `CS_ACCESS_TOKEN` also exists, move it into the environment
and delete the broader copy: GitHub makes broader secrets available to
workflows outside the environment, and the publisher falls back to them when
the environment has none.

## Shared spelling configuration

Run `make spelling` to enforce en-GB-oxendict spelling. The shared
`typos-config-builder` gate regenerates `typos.toml` from the live estate
dictionary in `leynos/agent-helper-scripts` and the `typos.local.toml` overlay
on every run, then checks tracked Markdown. A word added to the shared
dictionary therefore needs no change here, and `typos.toml` must never be drift
checked in continuous integration. `typos.toml` is therefore a generated
artefact and is ignored by Git, as is the local cache that keeps the gate
usable when the authority is temporarily unreachable. Add only narrow
project-specific terms and exclusions to `typos.local.toml`; never edit
generated `typos.toml` by hand.

## CodeScene coverage publication

Main owns CodeScene (CV-005). Nothing a pull request can start talks to
CodeScene or holds its credential.

- **Pull requests** (`.github/workflows/ci.yml`) run the tests, then measure
  coverage and ratchet it with the shared `generate-coverage` action over the
  whole tree, as it measured before the move. The report is not uploaded
  anywhere.
- **Main** (`.github/workflows/coverage-main.yml`) is the one publisher. It
  runs on each push to `main` and on manual dispatch (which must target `main`:
  the `codescene` environment, whose deployment policy admits `main` alone,
  refuses a dispatch from any other branch before the job runs). It generates
  the same coverage, writes the ratchet baseline that pull requests compare
  against, and uploads through the shared `upload-codescene-coverage` action.
  With no `CS_ACCESS_TOKEN` in the environment, the upload step is skipped and
  a separate step writes a warning, so the run still succeeds and the publisher
  works before a CodeScene project exists.
- **Known exception.** Merges made with `GITHUB_TOKEN`, such as Dependabot
  automerge, fire no push event, so they reach the publisher only through a
  later push or a manual dispatch. A manual dispatch uploads coverage but does
  not save the ratchet baseline, which the shared action writes only on a push
  to `main`; pull requests keep comparing against the older baseline until a
  later push advances it.

The `generate-coverage` selection in both workflows must match field for field
(format and interpreter), and `.github/cv005.toml` names the interpreter.

### The CV-005 contract check

The decision is recorded in
[ADR-001](adr-001-main-owns-codescene-coverage-publication.md).

`make test-workflow-contracts` runs the shared `cv005-contracts` checker
against this repository's workflows. `make all` includes it, and CI runs it.
The checker is fetched from the `leynos/shared-actions` commit named by
`CV005_CONTRACTS_REF` in the `Makefile`, so the first run needs network access.
Always pin a full 40-character commit: a fix to the contract arrives as a pin
bump, never as a local copy of the rules. The command exits 0 when every clause
holds, 1 with one `clause: message` line per violation, and 2 when the tree or
the configuration cannot be read.
