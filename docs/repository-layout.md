# Repository layout

Setwork currently contains a Python scaffold and a draft design. The target
compiler and generated runtime layout is proposed in
[technical design §5.3](tech-design.md#53-repository-layout).

- `setwork/` contains the current package and its greeting implementation.
- `tests/` contains the scaffold test; future tests also belong in this tree.
- `docs/` contains project guides, the design, terms of reference, context, and
  delivery roadmap. [Documentation contents](contents.md) indexes these files.
- `docs/design/` contains normative and illustrative design artefacts, rather
  than installed package modules.
- `.github/` contains workflows and local composite actions.
- `Makefile` provides the local build, validation, and formatting commands.
- `pyproject.toml` defines the existing package and development dependencies.

The compiler, adapters, curated specifications, and generated package paths in
the technical design have not been implemented yet.
