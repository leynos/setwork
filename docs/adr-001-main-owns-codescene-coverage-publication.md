# ADR-001: `main` owns CodeScene coverage publication

- Status: Accepted
- Date: 2026-10-31

## Context and Problem Statement

Coverage was measured in `ci.yml`, and the pull-request job held the CodeScene
token and checksum in its `env`. CodeScene accepts an upload only for a branch
it analyses, and a pull request's head is not one. A pull request from a fork
cannot read `secrets.CS_ACCESS_TOKEN`, so any CodeScene step there is skipped
for exactly the changes that most need review. The shared uploader pins the
`cs-coverage` archive by digest, but it cannot pin the CodeScene API the tool
calls. A lane that holds the token is also a lane that a pull request's
workflow edit could try to reach.

## Decision drivers

- Keep a failing coverage ratchet on every pull request.
- Keep the CodeScene credential, host and client off every workflow a pull
  request can start.
- Give the ratchet baseline exactly one writer, so every pull request is
  measured against `main`.
- Hold the split with an executable contract rather than a convention.

## Considered options

- Keep a CodeScene step in `ci.yml`, guarded to pushes to `main`. Rejected: the
  job that holds the token is the one pull requests run.
- Drop CodeScene coverage altogether. Rejected: the trunk figure is still
  wanted, and the ratchet needs a baseline written on `main` anyway.
- Protect the publisher with a deployment environment restricted to `main`.
  Adopted for the credential, as the owner's step: the publisher's job declares
  the `codescene` environment, the owner restricts it to `main` and stores the
  token there, and any broader repository- or organization-level copy is
  deleted. The ref guard on the upload stops a dispatch of the unedited
  publisher from a branch; it cannot stop a writer who edits and dispatches a
  branch's copy.

## Decision

Two workflows split the work, as CV-005 of the estate's continuous integration
standards requires.

- `ci.yml` runs the shared `generate-coverage` action on pull requests only,
  with `with-ratchet: 'true'` and `publish-artefact: 'false'`. Nothing a pull
  request can start touches CodeScene.
- `coverage-main.yml` is the one publisher. On a push to `main` it measures the
  same selection, which writes the ratchet baseline, then uploads the report in
  explicit upload mode. A check step with one exact command binds nothing. The
  upload runs only when that output is `true` and the ref is `refs/heads/main`,
  and passes the secret straight to its `access-token` input. With no token a
  separate step writes a warning and the run still succeeds, so the arrangement
  works before a CodeScene project exists.

`make test-workflow-contracts` runs the shared `cv005-contracts` checker,
pinned to one full `leynos/shared-actions` commit in the `Makefile`, against
this repository's workflows. The first run fetches the checker, so it needs
network access.

## Consequences

- A pull request's coverage is judged only by the ratchet; CodeScene sees `main`
  alone.
- Merges made with `GITHUB_TOKEN`, such as Dependabot automerge, fire no push,
  so they reach the publisher only through a later push or a dispatch. A
  dispatch uploads but writes no baseline, so the baseline can lag until a
  later push saves it.
- Adding a workflow that touches CodeScene, runs ratcheted coverage on a push,
  or changes the coverage selection on one side only fails the contract, which
  names the clause.

The [developers' guide](developers-guide.md) records the publisher's shape and
its operational exceptions.
