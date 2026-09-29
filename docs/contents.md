# Documentation contents

[Documentation contents](contents.md) is the index for setwork's documentation
set.

## Project guides

- [Repository layout](repository-layout.md) distinguishes the current scaffold
  and design artefacts from the proposed implementation layout.
- [User guide](users-guide.md) explains how to use the generated project and
  its public build and test commands.
- [Developer guide](developers-guide.md) explains the contributor workflow and
  points maintainers to script automation standards.
- [Documentation style guide](documentation-style-guide.md) defines the
  spelling, structure, Markdown, Architecture Decision Record (ADR), Request
  for Comments (RFC), and roadmap conventions used by this documentation set.

## Design and delivery

- [Terms of reference](terms-of-reference.md) defines users, scope, constraints,
  and unresolved product questions.
- [Context](context.md) defines the vocabulary used by the design.
- [Technical design](tech-design.md) describes the proposed compiler, generated
  runtime, safety boundaries, and acceptance criteria.
- [Roadmap](roadmap.md) translates the design into GIST delivery tasks.
- [Architecture diagram](design/architecture.txt) illustrates build-time and
  runtime boundaries.
- [Example manifest](design/setwork.example.toml) defines the draft
  configuration contract.
- [Intermediate representation sketch](design/setwork_ir.py) defines the
  information and invariants to preserve.
- [Publication validation sketch](design/setwork_ir_validation.py) defines the
  safe-surface gate using the shared intermediate representation types.
- [Generated API example](design/generated_api_example.py) illustrates exact
  serialization and Cuprum integration.
- [Expression grammar example](design/find_expression_example.py) illustrates
  non-delegating search expressions and precedence.

## Engineering practice

- [Complexity antipatterns and refactoring strategies](complexity-antipatterns-and-refactoring-strategies.md)
  explains cognitive complexity, the bumpy-road antipattern, and refactoring
  approaches for maintainable code.
- [Local validation of GitHub Actions with act and pytest](local-validation-of-github-actions-with-act-and-pytest.md)
  explains how to validate workflow behaviour locally before relying on remote
  Continuous Integration (CI) runs.
- [Scripting standards](scripting-standards.md) explains the preferred Python
  scripting stack, command execution patterns, and test expectations for helper
  scripts.
