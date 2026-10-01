# Setwork

*Turn command metadata into typed Python calls for Cuprum.*

Setwork is being designed as an offline compiler that generates ordinary Python
functions returning Cuprum `SafeCmd` values. It aims to replace repeated
argument assembly with explicit signatures, exact tokens, and traceable source
evidence.

**Status:** design and planning. The repository currently contains a Python
scaffold and design examples. The compiler CLI and `setwork.cuprum` API are
planned; the quick start below exercises the existing scaffold.

______________________________________________________________________

## Why Setwork?

- **Readable automation:** express command intent through typed function calls.
- **Normal Python composition:** reuse options with `functools.partial` and
  compose generated commands with Cuprum pipelines.
- **Explicit semantics:** select a command dialect and canonical serialization.
- **Reviewable generation:** retain locked sources, curated corrections,
  provenance, and licence evidence for every public field.

______________________________________________________________________

## Quick start

### Installation

With Python 3.12 or later, Git, and [uv](https://docs.astral.sh/uv/) installed:

```bash
git clone https://github.com/leynos/setwork.git
cd setwork
uv sync --group dev
```

### Basic usage

Run the scaffold's greeting:

```bash
uv run python -c 'from setwork import hello; print(hello())'
```

Expected output: `hello from Python`.

The [technical design](docs/tech-design.md#10-python-code-generation) describes
the proposed generated API and its partial-application contract.

______________________________________________________________________

## Planned features

- Static extraction from Fig, plus OpenCLI and Carapace adapters.
- Curated overlays and custom grammars for command-specific syntax.
- Typed bindings for an initial evaluation set of `echo`, `dd`, selected `git`
  leaves, `tar` modes, and non-delegating `find` expressions.
- Locked, reproducible generation with explainable diagnostics and semantic
  diffs.
- A generated runtime depending on Cuprum, with compiler dependencies kept at
  build time.
- Publication gates for unresolved semantics, delegated execution, and
  secret-bearing argument values.

The initial target profile, final command set, and distribution policy remain
open decisions. The [roadmap](docs/roadmap.md) records the work and decision
gates.

______________________________________________________________________

## Learn more

- [Users' guide](docs/users-guide.md) — current scaffold commands and status.
- [Developers' guide](docs/developers-guide.md) — development and quality gates.
- [Roadmap](docs/roadmap.md) — planned delivery and acceptance criteria.
- [Technical design](docs/tech-design.md) — proposed architecture and contracts.
- [Terms of reference](docs/terms-of-reference.md) — users, scope, and
  constraints.
- [Documentation contents](docs/contents.md) — the complete documentation index.

______________________________________________________________________

## Licence

ISC — see [LICENSE](LICENSE) for details. Imported corpora have separate
licence and attribution requirements; the design keeps derived Fig distribution
blocked while its recorded licence discrepancy remains unresolved.

______________________________________________________________________

## Contributing

Contributions are welcome, including reviews of the design and its open
questions. See [AGENTS.md](AGENTS.md) for repository conventions and the
[developers' guide](docs/developers-guide.md) for the local workflow.
