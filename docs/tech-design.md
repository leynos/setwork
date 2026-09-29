# Setwork – technical design

**Status:** Draft v0.1

**Audience:** Setwork implementers and reviewers, Cuprum maintainers, and
security reviewers

**Last substantive revision:** 18 July 2026

**Companion documents:** [`docs/terms-of-reference.md`](terms-of-reference.md),
[`docs/context.md`](context.md),
and [`docs/design/`](design/)

**Target implementation language:** Python 3.12 or later

**Reference type checker:** Pyright, subject to ADR 006

## Executive summary

Setwork is an offline compiler and generated Python library. The compiler reads
versioned command descriptions, imports only statically recoverable facts,
applies curated overlays and custom grammars, validates an evidence-bearing
intermediate representation, and emits ordinary Python functions. Each function
serializes typed values into an exact argument vector and returns a Cuprum
`SafeCmd`.

The generated runtime is deliberately dull. It contains Python source,
`py.typed`, Cuprum catalogue metadata, provenance, and no parser or Node.js
dependency. Calls compose through normal Python mechanisms:

```python
from functools import partial

from setwork.cuprum import echo

continue_echo = partial(echo, n=True)
cmd = continue_echo("hello events")
```

Cuprum retains responsibility for process execution, runtime allowlists,
observation, cancellation, results, and pipelines. Setwork owns the command
vocabulary and the transformation from typed values to tokens.

The default Fig adapter parses TypeScript without executing it. Dynamic
constructs become diagnostics and unresolved evidence. A command reaches code
generation only when the selected public surface has an explicit target
profile, type, canonical spelling, serialization rule, provenance, and safety
policy. Difficult commands use command-specific grammars rather than forcing an
embedded language into a flat option model.

Delegated execution, including `find -exec`, is excluded from the publishable
v0.1 surface. Cuprum currently authorizes the direct `Program` carried by a
`SafeCmd`; it does not model programs embedded in arguments. Supporting that
feature without a transitive authorization contract would turn an outer
allowlist into theatre.

## 1. Design context

Cuprum exposes a typed `Program`, a curated `ProgramCatalogue`, immutable
`SafeCmd` values, `sh.make`, execution contexts, and `Pipeline` composition.
`SafeCmd.__or__` combines commands into a pipeline, so a generated function
only needs to return the existing type.
[Cuprum's command implementation][cuprum-sh] defines this seam.

Cuprum's generic keyword serializer emits `--name=value` tokens. That behaviour
is useful as a convenience but cannot represent presence flags, separate option
values, assignment operands, attached values, optional option arguments, or
embedded command languages. Generated functions therefore build exact tokens
and call a cached `sh.make` builder with positional tokens only. Cuprum's
handwritten `tar` builder already uses this architecture.
[Cuprum's serializer][cuprum-sh] and
[`cuprum/builders/tar.py`][cuprum-tar-builder] provide the current evidence.

Fig describes a completion spec as a declarative schema for subcommands,
options, and arguments. The corpus is written in TypeScript and can contain
custom generators that execute during completion. [The Fig README][fig-readme]
states both properties. Completion metadata is therefore useful input but not a
safe executable build script and not a complete invocation contract.

Carapace and OpenCLI provide additional inputs. Carapace's YAML syntax captures
optional, repeatable, and valued flags, while OpenCLI supplies explicit scalar
types, choices, variadic arguments, and a JSON Schema. Neither current format
expresses every serialization and embedded-language requirement in this design.
[Carapace spec][carapace-spec], [OpenCLI's README][opencli-readme], and
[OpenCLI's schema][opencli-schema] define those surfaces.

## 2. Goals, non-goals, and design intent

### 2.1 Goals

The implementation must:

1. compile heterogeneous command metadata into one normalized, evidence-bearing
   intermediate representation;
2. generate ordinary Python functions with precise annotations and stable
   import paths;
3. produce exact, canonical argument vectors for a named target profile;
4. return Cuprum `SafeCmd` values without changing Cuprum's runtime model;
5. preserve useful `functools.partial` typing under the reference checker;
6. reject or quarantine unresolved and unsafe command surfaces;
7. support declarative overlays and command-specific grammar plugins;
8. emit deterministic source, tests, documentation metadata, licence notices,
   and provenance from a locked input set; and
9. explain every generated field and every rejected field through diagnostics.

### 2.2 Non-goals

The implementation does not:

- parse or execute shell command strings;
- discover commands from the runtime `PATH`;
- execute imported TypeScript in the default policy;
- install target executables;
- promise one API across incompatible command dialects;
- replace Cuprum's runtime, context, or pipeline code;
- generate a wrapper for every source command regardless of evidence quality;
- hide unsupported options and call the result complete; or
- authorize programs delegated through command arguments; or
- treat typed process arguments as a safe channel for passwords, tokens, or
  private-key material.

### 2.3 Design intent

**Compile uncertainty out, not confidence in.** Imported metadata enters the
intermediate representation with its source and authority. Curated facts may
resolve it. The publishability gate rejects what remains ambiguous. The
compiler optimizes for trustworthy generated APIs rather than maximum corpus
coverage.

## 3. Design decisions

| ID    | Decision                                                                                                                            | Status                                                 |
| ----- | ----------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------ |
| D-001 | Setwork remains a separate project from Cuprum and targets Cuprum as its first runtime.                                             | Accepted for v0.1                                      |
| D-002 | Generated public commands are ordinary Python functions returning `SafeCmd`.                                                        | Accepted                                               |
| D-003 | The default Fig adapter performs static TypeScript extraction and never evaluates source code.                                      | Accepted for v0.1; ADR candidate for future evaluation |
| D-004 | Every generated command belongs to an explicit target profile and version policy.                                                   | Accepted; first profile remains open                   |
| D-005 | The compiler uses a source-neutral intermediate representation rather than Fig or OpenCLI as its internal model.                    | Accepted                                               |
| D-006 | Curated overlays outrank imported completion evidence, and conflicts fail unless an override names what it replaces.                | Accepted                                               |
| D-007 | Generated code emits one canonical syntax rather than preserving every accepted spelling.                                           | Accepted                                               |
| D-008 | The generated runtime has no compiler, Tree-sitter, TypeScript, Node.js, or source-corpus dependency.                               | Accepted                                               |
| D-009 | Delegated execution is not publishable until Cuprum can authorize the transitive program set.                                       | Accepted for v0.1                                      |
| D-010 | Pyright is the initial reference checker; broader compatibility requires measured evidence.                                         | Provisional                                            |
| D-011 | Human configuration uses TOML; generated locks and provenance use canonical JSON.                                                   | Accepted                                               |
| D-012 | Complex mode commands generate separate leaf functions; embedded languages use custom abstract syntax trees.                        | Accepted                                               |
| D-013 | Secret-bearing values are not publishable through the default `argv` surface until sensitivity and observation policy are resolved. | Accepted for v0.1                                      |

## 4. Terminology and command classification

[`docs/context.md`](context.md) defines the normative vocabulary. The compiler
uses five command shapes:

| Shape      | Structure                                             | Default generated surface                                                    |
| ---------- | ----------------------------------------------------- | ---------------------------------------------------------------------------- |
| Flat       | One executable, positionals, and options              | Top-level function, for example `echo(...)`                                  |
| Family     | Subcommands select runnable leaves                    | Module and leaf functions, for example `git.clone(...)`                      |
| Mode       | One operation mode changes valid options and operands | Separate functions, for example `tar.create(...)` and `tar.extract(...)`     |
| Expression | Operands include an embedded language                 | Module with expression nodes and a command builder                           |
| Custom     | Semantics do not fit the shared model                 | Reviewed plugin that still produces the common IR or generated API contracts |

This classification selects a code-generation strategy. It does not imply that
every field imported from a completion source is correct for that strategy.

## 5. Architecture

The build-time compiler and generated runtime form separate trust and
dependency boundaries.
[`docs/design/architecture.txt`](design/architecture.txt) contains the external
architecture artefact.

```text
locked sources + overlays + custom grammars
                    |
              source adapters
                    |
        evidence-bearing command IR
                    |
       resolution and publishability gate
                    |
         generated Python + provenance
                    |
      typed call -> argv -> Cuprum SafeCmd
```

**Figure 1: Setwork's compiler and runtime flow.** Source adapters may accept
untrusted repository content. Only validated data crosses into generated Python
source. Runtime calls never load the source adapters.

### 5.1 Components

| Component                | Responsibility                                                 | Consumes                                   | Produces                                         |
| ------------------------ | -------------------------------------------------------------- | ------------------------------------------ | ------------------------------------------------ |
| Manifest loader          | Parse project intent and target selection                      | `setwork.toml`                             | Validated compiler configuration                 |
| Source resolver          | Resolve and verify pinned source material                      | Manifest and local or fetched repositories | Source lock entries and immutable file views     |
| Fig adapter              | Recover a safe static subset of TypeScript specs               | Fig source files                           | Imported command facts and diagnostics           |
| OpenCLI adapter          | Decode and validate OpenCLI documents                          | YAML or JSON documents                     | Imported command facts and diagnostics           |
| Carapace adapter         | Decode portable Carapace spec files                            | YAML documents                             | Imported command facts and diagnostics           |
| Normalizer               | Map source-specific concepts to the common model               | Imported facts                             | Draft command specifications                     |
| Overlay engine           | Apply curated, reviewable corrections                          | Draft specifications and TOML overlays     | Resolved or conflicted specifications            |
| Custom grammar registry  | Model embedded languages and exceptional syntax                | Reviewed Python plugins                    | Expression types, serializers, and command specs |
| Publishability validator | Enforce semantic, provenance, naming, and safety invariants    | Resolved specifications                    | Publishable units or blocking diagnostics        |
| Python generator         | Emit stable modules, tests, catalogue data, and docs metadata  | Publishable compilation unit               | Generated package tree                           |
| Provenance writer        | Record exact inputs and transformations                        | Source lock and generated unit             | Canonical JSON, notices, and semantic report     |
| CLI                      | Orchestrate lock, check, compile, explain, and diff operations | User commands                              | Files, diagnostics, and exit status              |

### 5.2 Dependency boundaries

The compiler package may depend on parsers, schema validators, and
code-formatting libraries. The generated package may depend only on:

- the supported Python standard library;
- a compatible Cuprum release; and
- optional target-specific helper packages explicitly named by an overlay.

A generated wheel must remain usable in an offline runtime environment after
installation. Source acquisition and compilation are build concerns.

### 5.3 Repository layout

The initial repository should keep the compiler, curated specifications, and a
reference generated package together while preserving package boundaries:

```text
setwork/
├── pyproject.toml
├── setwork.toml
├── setwork.lock.json
├── src/setwork/
│   ├── compiler/
│   ├── adapters/
│   ├── grammars/
│   ├── ir.py
│   └── cli.py
├── specs/overlays/
├── generated/setwork/cuprum/
├── docs/
└── tests/
```

A later packaging ADR may split compiler and generated wheels. The source tree
must not make such a split expensive.

## 6. Source acquisition and locking

### 6.1 Manifest

The human-authored manifest names target profile, package path, source
repositories, overlays, custom grammars, selected commands, and publication
policy. [`docs/design/setwork.example.toml`](design/setwork.example.toml) is
the normative configuration example for this draft.

A manifest may name a branch or tag only while creating or updating a lock. A
locked compile consumes immutable commit identifiers and content hashes.

### 6.2 Source lock

`setwork.lock.json` contains, in canonical key order:

- manifest schema version;
- compiler version and adapter versions;
- target-profile identifier and version policy;
- each repository URL and resolved commit;
- each consumed path and SHA-256 digest;
- relevant licence-file paths and digests;
- overlay paths and digests;
- custom grammar module and source digest; and
- the resulting compilation-unit digest.

`setwork compile --locked` refuses to resolve floating references, access the
network, or accept a file whose digest differs from the lock. `setwork lock`
performs source resolution and creates an explicit reviewable change.

### 6.3 Licence evidence

Source resolution records licence evidence separately from semantic provenance.
A source adapter cannot decide that generated output is redistributable.
Release policy applies an allow, deny, or review-required decision to each
source.

At the examined Fig revision, the repository's root `LICENSE` contains the MIT
licence, while `package.json` declares `ISC`. [The root licence][fig-license]
and [package metadata][fig-package] conflict. The example manifest therefore
uses `licence-policy = "review-required"`; public redistribution remains
blocked until the project resolves the discrepancy.

### 6.4 Target profiles

A target profile is immutable input, not a runtime guess. It defines:

- operating-system family and userland dialect;
- command project and accepted version range or capability set;
- option terminator behaviour;
- canonical spelling policy;
- command-specific safety rules;
- source priority; and
- conformance environment, such as a pinned container image.

The generated package records the profile in its module metadata and
provenance. Importing a GNU-targeted package on macOS is allowed, but Setwork
makes no claim that the host commands match. An optional runtime probe may
report a mismatch; it must not silently change serialization.

## 7. Static Fig extraction

### 7.1 Parser choice

The reference adapter uses Python Tree-sitter bindings with the maintained
TypeScript grammar. The bindings parse source into a syntax tree and support
node traversal without requiring the TypeScript program to run.
[Python Tree-sitter][py-tree-sitter] documents the Python parser API and
precompiled language wheels; [the TypeScript grammar][tree-sitter-typescript]
supplies the language implementation.

This choice keeps the safe adapter inside the Python compiler process and
avoids a Node.js execution boundary. It does not make arbitrary TypeScript
statically evaluable.

### 7.2 Accepted static subset

The adapter recognizes:

- `const` declarations initialized by object, array, string, number, Boolean,
  `null`, and substitution-free template literals;
- references to statically resolved local constants;
- property shorthand where the referenced value is static;
- object and array spreads whose source is statically resolved;
- selected enum-like member references configured by the adapter; and
- a default export that resolves to one static completion-spec object.

The adapter rejects or marks unresolved:

- function and method calls;
- imported runtime values;
- `await`, promises, and custom generators;
- conditional, logical, or arithmetic expressions not covered by an explicit
  constant-folding rule;
- computed property names;
- environment, filesystem, network, or process access;
- mutation after declaration; and
- any syntax node the adapter does not recognize.

A rejected construct produces a diagnostic with source ID, revision, path,
syntax span, command path where known, and the property it prevented from being
resolved. The adapter never replaces an unknown value with a plausible default.

### 7.3 Partial extraction

One dynamic property does not necessarily discard an entire command. The
adapter retains statically known siblings and marks the dynamic field
unresolved. Publication then follows the selected coverage policy:

- **complete** requires every command feature in scope to be resolved;
- **declared subset** permits a named subset only when the manifest and
  generated documentation list omitted features; and
- **internal draft** permits unresolved facts but generates no public wrapper.

A subset cannot omit a feature whose existence changes parsing of the selected
surface. For example, unresolved option-order rules or a dynamic mode selector
block the command rather than merely hiding one option.

### 7.4 No default evaluator

The v0.1 compiler does not import the Fig package, run its compiled JavaScript,
or execute custom generators. A future evaluator would require a separate
process with no network, no repository credentials, a read-only source tree,
resource limits, deterministic environment, and an output schema. It would also
need evidence that the additional coverage justifies the new attack surface.

## 8. Intermediate representation

[`docs/design/setwork_ir.py`](design/setwork_ir.py) is the normative external
type sketch. The
[publication validation sketch](design/setwork_ir_validation.py) keeps
publication policy alongside those types without expanding the type module.
These artefacts define design contracts, rather than installed compiler
modules. The implementation may split the types across modules, but it must
preserve their information and invariants.

### 8.1 Required information

Each command specification records:

- direct executable and command path;
- generated Python import path;
- command shape;
- target profile;
- public coverage mode;
- parameters in semantic and serialization order;
- Python-facing value type;
- cardinality and requiredness;
- all accepted CLI spellings and one canonical spelling;
- serialization kind;
- dependencies and conflicts;
- option-terminator policy;
- delegated-execution status;
- argument sensitivity and approved transport policy;
- descriptions retained as untrusted text; and
- field-level evidence.

### 8.2 Serialization kinds

| Kind         | Example input           | Emitted tokens                   |
| ------------ | ----------------------- | -------------------------------- |
| Presence     | `n=True`                | `-n`                             |
| Separate     | `branch="main"`         | `--branch`, `main`               |
| Equals       | `colour="always"`       | `--color=always`                 |
| Attached     | `include=Path("inc")`   | `-Iinc`                          |
| Assignment   | `block_size=Size("4M")` | `bs=4M`                          |
| Repeated     | `header=("A", "B")`     | `--header`, `A`, `--header`, `B` |
| Comma joined | `conv=(SYNC, NOERROR)`  | `conv=sync,noerror`              |
| Custom       | `find` expression tree  | Grammar-owned token sequence     |

A source may establish that a value exists without establishing its
serialization kind. Such a field remains unresolved.

### 8.3 Evidence model

Evidence levels, from strongest to weakest, are:

1. **authoritative**: target command documentation, machine-readable schema
   published by the command owner, or verified conformance fixture;
2. **curated**: a reviewed Setwork overlay or custom grammar;
3. **imported**: completion or third-party command-description metadata;
4. **inferred**: a conservative rule whose output still requires explicit
   acceptance; and
5. **unresolved**: insufficient or conflicting evidence.

Evidence attaches to fields rather than whole commands. An imported command
name may coexist with a curated serialization rule and an authoritative enum
domain.

### 8.4 Source precedence and conflicts

The merge order is:

1. custom grammar output for fields the plugin owns;
2. explicit Setwork overlay;
3. command-owner specification selected by the target profile;
4. imported completion metadata; and
5. inference.

Higher precedence does not silently erase lower-precedence disagreement. An
overlay that changes a populated field must name the evidence it replaces and
provide a reason. The provenance report retains both values and the resolution.
Two values at the same precedence form a blocking conflict.

### 8.5 Invariants

The publishability validator enforces at least these properties:

- generated Python paths are unique and valid identifiers;
- parameter names are unique within a function;
- aliases contain the canonical spelling;
- required positional parameters precede optional positional parameters;
- at most one variadic positional parameter exists and it is last;
- dependencies and conflicts refer to known parameters;
- finite enum domains are non-empty and authoritative or curated;
- every emitted token is a string and contains no NUL;
- target profile and option-terminator policy are resolved;
- every selected parameter has a non-unresolved serialization kind;
- source evidence exists for every public field;
- every value has an explicit sensitivity classification;
- secret-bearing `argv` parameters are rejected by the default safe policy; and
- delegated execution is rejected unless the selected policy explicitly
  authorizes it.

Flag parameters consume no values: their `values.maximum` cardinality is zero.
The v0.1 sketch validator should keep command and parameter validation in
focused helpers and reuse provenance checks for program, command, and parameter
sources. This organization is local to sketch publication checks; it does not
introduce a general compiler abstraction. Refactoring must preserve diagnostic
text, validation behaviour, and diagnostic ordering.

## 9. Overlays and custom grammars

### 9.1 Declarative overlays

TOML overlays handle corrections that fit the common model. They can:

- rename a Python parameter;
- select a target dialect and command version range;
- choose a canonical spelling;
- set value kind and nominal type;
- declare serialization kind and separator;
- mark repeatability, dependencies, and conflicts;
- classify value sensitivity and select an approved transport policy;
- state option-terminator and leading-hyphen operand policy;
- group subcommands into generated modules;
- split command modes into leaf functions;
- declare subset coverage and omitted features; and
- attach authoritative documentation references.

An overlay cannot contain executable Python. Schema validation rejects unknown
keys so misspellings do not become inert configuration.

### 9.2 Custom grammar plugins

A custom grammar is reviewed Python code loaded by an explicit manifest entry.
It may define:

- expression or command-domain types;
- validation rules;
- a serializer returning `tuple[str, ...]`;
- generated public API templates; and
- additional property-test strategies.

The plugin receives immutable normalized source facts and target-profile data.
It does not receive ambient network credentials or a generic compiler object.
Its output passes the same naming, provenance, token, catalogue, and generation
checks as ordinary commands.

### 9.3 GNU `find`

The initial `find` plugin models predicates and Boolean operators as an
abstract syntax tree. Parentheses are generated from precedence, not copied
from user strings:

```python
expr = (
    (find.name("*.py") | find.name("*.pyi"))
    & find.type(find.FileType.REGULAR)
    & ~find.path("*/generated/*")
)
cmd = find.files(Path("src"), expression=expr)
```

The serializer emits explicit parentheses where a child expression has lower
precedence than its parent. It may add harmless parentheses to keep output
canonical. `find -exec`, `-execdir`, `-ok`, and other delegated actions remain
unavailable in v0.1.

[`docs/design/find_expression_example.py`](design/find_expression_example.py)
shows the precedence and canonical-parenthesis mechanism as executable Python.

## 10. Python code generation

### 10.1 Output structure

A generated package has this shape:

```text
setwork/cuprum/
├── __init__.py
├── _catalogue.py
├── _support.py
├── echo.py
├── dd.py
├── git.py
├── tar.py
├── find.py
├── provenance.json
├── THIRD_PARTY_NOTICES.md
└── py.typed
```

Simple commands may be re-exported as functions from `__init__.py`. Command
families and mode-sensitive commands are modules:

```python
from setwork.cuprum import echo, git, tar

cmd1 = echo("hello", n=True)
cmd2 = git.clone(repo, depth=1)
cmd3 = tar.create(archive, sources, compression=tar.Compression.GZIP)
```

### 10.2 Signature rules

The generator applies deterministic rules:

- required and optional CLI operands become positional-or-keyword parameters;
- a variadic operand becomes `*values` when no later positional operand exists;
- options are keyword-only;
- the preferred long spelling supplies the snake-case Python name;
- a short spelling supplies the name only when no usable long spelling exists;
- Python keywords gain a trailing underscore;
- built-in collisions receive a semantic overlay name where available, then a
  deterministic `_option` suffix as a last resort;
- presence flags use `bool = False`;
- absent valued options use `T | None = None`;
- repeatable options use immutable `tuple[T, ...] = ()` or accept
  `Sequence[T]` and snapshot it in order;
- closed string domains generate `StrEnum` only when evidence says the list is
  exhaustive;
- filesystem values accept `str | os.PathLike[str]` unless a stricter curated
  nominal type applies; and
- cross-parameter constraints use separate functions where possible, then
  runtime validation when the type system cannot express them cleanly.

Imported completion suggestions do not automatically become enums. A suggestion
list often describes useful completions rather than the complete accepted
language.

`functools.partial(echo, n=True)` retains ordinary Python semantics: a later
call may override the bound keyword with `n=False`. Setwork treats partial
application as reusable defaulting, not sealed policy. A future immutable
binding helper would need a separate API and threat model.

### 10.3 Optional option arguments

An option that distinguishes absent, bare, and valued forms requires three
states. The generated `_support.py` defines a typed `BARE` singleton. A
parameter then uses `T | Bare | None`:

```python
checkpoint: int | Bare | None = None
```

`None` omits the option, `BARE` emits only `--checkpoint`, and an integer emits
the canonical valued form. A Boolean cannot represent this grammar.

### 10.4 Canonical ordering

The command specification owns output order. The default policy emits:

1. fixed command-path tokens;
2. global or mode options in declared canonical groups;
3. command-local options;
4. an end-of-options marker where required and supported; and
5. positional operands.

Commands with order-sensitive options declare explicit slots or use a custom
serializer. The generator never sorts repeated values or user-provided operands.

### 10.5 Source generation safety

The generator constructs a Python abstract syntax tree or uses a structured
writer that quotes every literal with Python's literal rules. It never inserts
source descriptions, option names, or paths through raw template interpolation.
Generated files pass the formatter, parser, linter, and type checker before the
compiler reports success.

Descriptions become docstrings only after control-character removal and length
limits. Full upstream text remains in provenance where licence policy permits.

### 10.6 Stable generated API

Generation is deterministic, but upstream change does not imply automatic API
breakage. `setwork diff` classifies changes as:

- additive;
- behavioural but source-compatible;
- deprecating;
- breaking;
- provenance-only; or
- newly unresolved.

Renames require an overlay decision. The compiler may generate a deprecated
alias for a bounded period, but it must not silently rename a public keyword
because an upstream description changed.

### 10.7 Illustrative source

[`docs/design/generated_api_example.py`](design/generated_api_example.py) shows
the expected generated shape for a conservative GNU `echo` binding. It uses a
cached Cuprum builder, explicit validation, and exact argument construction.

## 11. Cuprum integration

### 11.1 Builder construction

Each generated command module creates its builder once:

```python
_ECHO = sh.make(ECHO, catalogue=CATALOGUE)
```

A public function serializes tokens and calls `_ECHO(*argv)`. It never passes
command options as Python keyword arguments to `sh.make`, because Cuprum's
generic keyword convention is not the target command's grammar.

`sh.make` resolves the program in its supplied catalogue before returning the
builder. This keeps an invalid generated catalogue as an import- or build-time
failure rather than a late execution surprise. [Cuprum's `make`][cuprum-sh]
defines that behaviour.

### 11.2 Generated catalogue

`_catalogue.py` exports:

- one `Program` constant per executable;
- `PROJECTS`, grouped by command project and target profile;
- `CATALOGUE`, used by every generated builder; and
- `PROGRAMS`, the immutable set of directly executable programs.

Setwork does not mutate `cuprum.DEFAULT_CATALOGUE`. Separate catalogues may
contain equal `Program` values with different project metadata; each generated
`SafeCmd` carries the metadata from Setwork's catalogue.

### 11.3 Runtime allowlists

Cuprum's unrestricted default context permits commands, while a scoped context
can narrow execution to an explicit set. Generated documentation shows how to
scope to the generated package:

```python
from cuprum import ScopeConfig, scoped
from setwork.cuprum import CATALOGUE, echo

with scoped(ScopeConfig(allowlist=CATALOGUE.allowlist)):
    echo("hello").run_sync()
```

The construction catalogue and runtime context serve different purposes. The
first establishes known program metadata; the second authorizes execution in a
logical scope.

### 11.4 Pipelines

No Setwork pipeline type exists. `SafeCmd | SafeCmd` already produces a Cuprum
`Pipeline`, so generated and handwritten builders interoperate:

```python
pipeline = echo("one\ntwo\nthree") | grep("two", fixed_strings=True)
result = pipeline.run_sync(context=ctx)
```

The generated function's return annotation is sufficient for static
composition. [Cuprum's `SafeCmd` and `Pipeline`][cuprum-sh] own the runtime
algebra.

### 11.5 Delegated execution boundary

A command such as `find -exec grep ...` carries `find` as its direct Cuprum
`Program`, but process execution may launch `grep`. Cuprum's current `SafeCmd`
shape records one direct program and an argument tuple. It does not expose a
transitive program set for context authorization.

Setwork therefore marks command-valued parameters and delegated actions in the
intermediate representation and rejects them at the v0.1 publishability gate. A
future joint design should let a prepared command declare immutable execution
requirements that Cuprum checks before spawning the outer process. Until then,
embedding another `SafeCmd.argv_with_program` would be syntactically neat and
security-significant in exactly the wrong order.

## 12. Command-specific generation strategies

### 12.1 `echo`: simple function, non-trivial dialect

`echo` proves the desired import and partial-application ergonomics. The target
profile must still decide supported flags, escape behaviour, and how operands
beginning with `-` are handled. Setwork does not assume that every `echo`
implementation supports `--` as an option terminator.

With default output flags, a sole `--help` or `--version` operand is rejected
because the command would interpret it as a control flag. Either string remains
literal operand text when other operands are present or when any output flag is
explicitly selected.

### 12.2 `dd`: assignment operands

Fig's `dd` specification marks operands such as `bs`, `if`, and `of` as
POSIX-noncompliant option-like entries requiring a separator. The adapter can
recover names and file suggestions; an overlay supplies semantic Python names,
size grammar, integer constraints, canonical ordering, and the fact that the
separator is `=` inside one token. [`dd.ts`][fig-dd] supplies the imported
facts.

The generated API should prefer names such as `input_file`, `output_file`, and
`block_size` over syntax-shaped identifiers such as `if_`, `of`, and `bs`.
Provenance records the mapping.

### 12.3 `git`: command family

The adapter flattens the subcommand tree into runnable leaves. The generator
creates `git.py` and functions such as `clone`, `status`, and `checkout`.
Shared options remain explicit data; the generator does not create a mutable
command builder that accumulates options across calls.

A large leaf signature may indicate that the source model needs semantic
subdivision. If a function would exceed the configured parameter threshold, the
publishability gate requires an overlay that splits modes, introduces a typed
options object for a coherent group, or declares a smaller supported subset.
The threshold prevents completion corpora from generating a hundred-keyword
python-shaped landfill.

### 12.4 `tar`: mode-sensitive command

The generator exposes modes as functions rather than a `mode` enum plus one
union of every possible option:

```python
tar.create(archive, sources, compression=tar.Compression.GZIP)
tar.extract(archive, destination=Path("restore"))
```

Each function emits canonical long or separated short options selected by the
target profile. It never generates old-style clusters such as `czf`, because
canonical output need not preserve input shorthand. Fig's aliases,
dependencies, and exclusions remain useful evidence for constructing the mode
specifications. [`tar.ts`][fig-tar] provides those imported relationships.

### 12.5 `find`: expression language

Fig currently represents paths and the expression as variadic token lists and
contains a TODO for predicates. That source cannot generate a typesafe
expression surface by itself. [`find.ts`][fig-find] establishes the gap.

The custom grammar owns expression nodes, precedence, predicate arity, path
patterns, numeric comparison syntax, and action safety. The first public subset
contains pure tests and non-delegating actions only. Raw expression tokens are
not accepted by the typed builder.

## 13. Compiler command-line interface

The initial CLI exposes five commands:

```text
setwork lock     resolve sources and write setwork.lock.json
setwork check    parse, normalize, merge, and report without generating
setwork compile  generate from locked inputs
setwork explain  show provenance and decisions for one public symbol
setwork diff     compare two locks or generated API manifests
```

### 13.1 Exit status

| Status | Meaning                                                              |
| ------ | -------------------------------------------------------------------- |
| `0`    | Operation completed and all selected commands met policy.            |
| `1`    | Semantic, source, generation, or verification errors blocked output. |
| `2`    | CLI usage or manifest-schema error.                                  |
| `3`    | Locked source material was missing or did not match its digest.      |
| `4`    | Licence policy blocked generation or distribution.                   |

Diagnostics also use stable machine-readable codes. Text is for humans; CI
should consume canonical JSON diagnostics when requested.

### 13.2 Explainability

`setwork explain setwork.cuprum.dd:block_size` reports:

- public Python path and type;
- CLI spelling and serialization;
- target profile and command version;
- source evidence in precedence order;
- applied overlays and reasons;
- conflicts considered and their resolution;
- generated source location; and
- verification cases covering the field.

An explain command that cannot answer those questions indicates missing
provenance, not a documentation inconvenience.

## 14. Security design

### 14.1 Protected assets

Setwork protects:

- build-host credentials and network access;
- integrity of generated Python source;
- accuracy of command serialization;
- Cuprum runtime allowlists;
- reviewability of executable and option surfaces;
- confidentiality of credentials and other secret values; and
- licence and attribution compliance.

### 14.2 Threat actors and failures

The design considers:

- a compromised or malicious source corpus;
- a malformed completion spec designed to exploit a parser or generator;
- an incorrect or malicious overlay;
- untrusted runtime values intended to become options rather than operands;
- a credential or secret passed through process arguments or observation;
- a target executable whose version differs from the profile; and
- a delegated command hidden inside an outer allowed program.

### 14.3 Build-time controls

- The default adapter parses but does not execute imported code.
- Locked compilation denies network access and verifies file digests.
- Source text crosses into generated Python only through structured literals.
- Unknown syntax and conflicting facts fail closed for selected public fields.
- Custom grammar plugins are local trusted code named explicitly in the
  manifest and reviewed like compiler code.
- Resource limits bound parser depth, file size, command count, generated output
  size, and diagnostic volume.
- Licence policy runs before distributable artefacts are assembled.

### 14.4 Runtime value controls

Avoiding a shell removes shell interpolation, but it does not remove option
injection. A positional operand such as `--checkpoint-action=exec=...` may
alter a target command if it appears before parsing has ended.

Each command profile therefore declares one of these operand policies:

1. emit `--` before operands at the grammar-defined position;
2. use an explicit operand-bearing option;
3. transform through a command-specific safe representation;
4. reject leading-hyphen operands; or
5. mark the surface unsafe and do not publish it.

There is no universal fallback. The generated serializer rejects NUL in every
string token before constructing `SafeCmd`, snapshots iterables to prevent
mutation during serialization, and preserves user order where semantics depend
on it.

Filesystem types convey value shape, not filesystem authorization. Setwork does
not globally resolve paths, ban relative paths, or assert that a path is safe.
Command or project overlays may impose stronger policies.

### 14.5 Secret-bearing values

A typed value in `argv` may still appear in process listings, operating-system
telemetry, crash reports, Cuprum observations, or application logs. Static
typing does not make that channel confidential. Every value therefore carries a
sensitivity classification. The v0.1 safe policy rejects passwords, tokens,
private keys, and equivalent secrets when the command would receive them through
`argv`. [CWE-214][cwe-214] describes the weakness class, while
[`proc_pid_cmdline(5)`][proc-cmdline] documents one concrete operating-system
surface on Linux.

An overlay may expose an authoritative safer channel, such as standard input, a
credential file, a file descriptor, or an environment variable, but that
channel requires its own effect and lifetime analysis. A future Cuprum
redaction contract would reduce observation leakage; it could not hide
arguments from the operating system itself.

### 14.6 Delegated execution

Any feature that accepts a command, script, interpreter expression, or callback
program is tagged `delegated_execution = true`. The v0.1 gate rejects it. This
includes obvious forms such as `find -exec` and less obvious command-valued
options in archive, build, and network tools.

## 15. Failure modes

| Failure                                     | Detection                                 | Behaviour                                                               | Recovery                                                         |
| ------------------------------------------- | ----------------------------------------- | ----------------------------------------------------------------------- | ---------------------------------------------------------------- |
| Source file cannot be parsed                | Adapter parse diagnostic                  | Command or source fails according to selection policy                   | Pin a valid revision or repair the adapter                       |
| Dynamic TypeScript blocks a field           | Unsupported-syntax diagnostic with span   | Field remains unresolved; selected wrapper may fail publication         | Add a curated overlay or approved static rule                    |
| Two sources disagree                        | Merge conflict                            | No automatic winner at equal precedence                                 | Add an explicit reviewed resolution                              |
| Overlay refers to a removed option          | Overlay validation                        | Locked build fails                                                      | Update or remove the overlay after semantic review               |
| Python identifier collision                 | Naming pass                               | Deterministic alternate proposed; public generation blocks if ambiguous | Add a semantic rename overlay                                    |
| Serialization remains unknown               | Publishability validation                 | No public wrapper                                                       | Supply authoritative evidence or narrow the supported subset     |
| Target executable is missing                | Cuprum process spawn                      | Cuprum reports execution failure                                        | Install the target outside Setwork                               |
| Target version differs                      | Optional probe or conformance environment | Warning or policy failure; serializer does not mutate                   | Install a compatible version or select another profile           |
| Generated catalogue is invalid              | Import/build verification                 | Package generation fails                                                | Correct project ownership metadata                               |
| Licence evidence is conflicting             | Release policy                            | Distribution artefact is withheld                                       | Resolve upstream terms or exclude the source                     |
| Runtime operand resembles an option         | Generated validator                       | Reject unless a known terminator or safe form exists                    | Use a safe command-specific route or lower-level Cuprum API      |
| Secret-bearing `argv` parameter is selected | Publishability validator                  | Feature is unavailable in the safe surface                              | Use an approved non-`argv` channel or resolve sensitivity policy |
| Delegated execution is selected             | Publishability validator                  | Feature is unavailable                                                  | Resolve transitive authorization design                          |
| Repeated build differs                      | Reproducibility check                     | Release fails                                                           | Remove nondeterminism and regenerate                             |

The compiler writes output to a temporary directory and atomically replaces the
configured destination only after parsing, validation, generation, formatting,
type checking, and verification succeed. A failed build leaves the previous
output intact.

## 16. Verification strategy

This section defines properties, not a catalogue of test genres.

### 16.1 Named properties

| Property                      | Statement                                                                                                                                          | Verification method                                                                                                   | Known gap                                                        |
| ----------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------- |
| V-001 Determinism             | The same compiler, manifest, lock, overlays, and custom grammar sources produce byte-identical output.                                             | Generate twice in isolated directories and compare every byte and ordered manifest entry.                             | Does not prove semantic correctness.                             |
| V-002 Token integrity         | Every generated serializer returns only NUL-free strings in deterministic order.                                                                   | Property-based generation over each parameter type, plus a package-wide serializer hook.                              | Target programs may reject otherwise valid strings.              |
| V-003 Omission                | An absent optional parameter emits no token; a supplied parameter emits exactly its declared cardinality.                                          | Generated property tests from IR cardinality and serialization.                                                       | Custom grammars require plugin-supplied strategies.              |
| V-004 Canonicality            | Equivalent API values have one documented token representation per profile.                                                                        | Golden vectors and duplicate-output checks across generated cases.                                                    | Cannot prove that an undocumented target spelling is equivalent. |
| V-005 Constraint enforcement  | Conflicts, dependencies, required operands, and mode boundaries fail before `SafeCmd` construction.                                                | Exhaustive combinations below the configured threshold; pairwise plus targeted cases above it.                        | Pairwise coverage cannot prove all high-order interactions.      |
| V-006 Expression precedence   | A custom expression serializer preserves the abstract syntax tree's Boolean meaning.                                                               | Generate expression trees, serialize, parse with an independent reference parser, and compare normalized trees.       | Reference parser defects can correlate with fixtures.            |
| V-007 Catalogue alignment     | Every public command returns a `SafeCmd` whose direct `Program` belongs to the generated catalogue and whose project metadata matches the profile. | Import every public function, generate minimum valid calls, and inspect `SafeCmd`.                                    | Does not cover delegated programs, which v0.1 rejects.           |
| V-008 Partial typing          | Binding supported parameters with `functools.partial` retains the remaining call contract under Pyright strict mode.                               | Generated positive and negative type-check fixtures based on each signature shape.                                    | Other type checkers require a separate matrix.                   |
| V-009 Provenance completeness | Every public symbol and parameter resolves to at least one locked source or curated evidence record.                                               | Traverse generated API manifest against provenance JSON; fail on missing links.                                       | Evidence can still be wrong.                                     |
| V-010 Source isolation        | The default Fig adapter performs no source-controlled code execution or ambient I/O.                                                               | Replace process, network, filesystem-write, and import boundaries with failing sentinels during adapter corpus tests. | Parser-library vulnerabilities remain a dependency risk.         |
| V-011 Sensitivity gate        | No value classified as secret can enter a publishable `argv` serializer under the default policy.                                                  | Traverse the resolved IR and generated API manifest; include negative fixtures for every secret-bearing source field. | A value classified incorrectly may still leak.                   |

### 16.2 Reference command matrix

The initial conformance set should exercise distinct grammar risks:

| Command                          | Risk exercised                                                         | Minimum verification                                                      |
| -------------------------------- | ---------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| `echo`                           | Variadic operands, short flags, operand ambiguity, partial application | Strict type fixtures and target-profile golden vectors                    |
| `dd`                             | Assignment operands, numeric and size types, comma-joined enums        | Property tests for ordering and token shape                               |
| `git clone` and `git status`     | Command-family flattening and leaf-specific options                    | Source-to-IR snapshots and executable conformance cases                   |
| `tar.create` and `tar.extract`   | Mode separation, option conflicts, canonical syntax                    | Exhaustive mode fixture set and target invocation in a pinned environment |
| `find` without delegated actions | Expression precedence and custom grammar                               | Generated-tree round trips against an independent parser                  |

### 16.3 Combinatorial coverage

For a leaf with up to 12 Boolean or finite-domain interaction parameters, the
generator enumerates every valid and invalid combination after applying
constraints. Above that threshold, it generates pairwise coverage and requires
explicit targeted cases for:

- every conflict edge;
- every dependency edge;
- every mode transition;
- every optional-argument state;
- every serialization kind; and
- every leading-hyphen operand policy.

The coverage report lists untested higher-order combinations rather than
calling pairwise coverage comprehensive.

### 16.4 Type-check fixtures

The generator writes non-runtime fixtures that must pass or fail under the
reference Pyright version. Cases include:

- correct direct calls;
- missing required operands;
- unknown keywords;
- wrong scalar, enum, path, and sequence types;
- option names after `functools.partial` binds positional or keyword arguments;
- variadic operands after partial application; and
- return types composing through Cuprum `Pipeline`.

Pyright's repository contains explicit `functools.partial` tests for these
inference classes. [The upstream test file][pyright-partial] is the baseline,
not a substitute for testing generated signatures.

### 16.5 Conformance execution

Executable conformance runs in pinned target environments. It must avoid
destructive operations and network access. Tests prefer:

- argument-inspection modes where the command exposes them;
- temporary files and directories;
- list or dry-run operations;
- known small fixtures; and
- independent observation of effects and exit status.

Parsing `--help` alone does not prove serialization. It can supplement source
updates but does not replace command cases.

## 17. Build, distribution, and operations

### 17.1 Generated artefacts

A successful compile emits:

- formatted Python source with inline annotations;
- `py.typed`;
- generated positive and negative type fixtures;
- runtime property and golden fixtures;
- `api-manifest.json` describing public symbols and signatures;
- `provenance.json` linking symbols to evidence;
- `THIRD_PARTY_NOTICES.md`;
- a semantic diagnostics report; and
- a digest of the complete output tree.

The generator prefers annotations in `.py` over a parallel handwritten `.pyi`
surface. Stubs are generated only where runtime implementation and public
typing cannot share one source without unacceptable complexity.

### 17.2 Release policy

A release is blocked when:

- locked inputs cannot be reproduced;
- licence policy is unresolved or denied;
- generated source differs from a clean regeneration;
- any public symbol lacks provenance;
- formatter, parser, linter, or reference type checks fail;
- named verification properties fail; or
- the target-profile conformance suite reports a regression.

### 17.3 Updates

A source update is a reviewed lock change. CI runs `setwork diff` and attaches
the semantic report. Newly imported options do not appear in the public API
until their semantics pass the same gate as existing fields. Removed upstream
options trigger a compatibility decision rather than immediate deletion.

### 17.4 Observability

The compiler emits structured diagnostics with source, phase, command path,
severity, and stable code. It does not send telemetry. Runtime observation
remains Cuprum's responsibility and receives the exact generated `SafeCmd`
metadata.

## 18. Alternatives considered

### 18.1 Continue handwritten Cuprum builders

Handwritten builders offer the strongest local control and remain appropriate
for unsupported commands. They do not exploit the existing metadata commons,
and they repeat naming, serialization, provenance, documentation, and test
infrastructure. Setwork generalizes their pattern without removing the escape
route.

### 18.2 Dynamic `sh`-style command proxies

A dynamic module can discover any executable and accept arbitrary arguments.
That recreates the desired surface quickly but cannot provide command-specific
signatures, finite value domains, or a reviewable allowlisted vocabulary. It
also conflicts with Cuprum's explicit catalogue design.

### 18.3 Generate command dataclasses instead of functions

Dataclasses can model modes and validation cleanly, but they make simple calls
heavier and weaken the exact `functools.partial` experience that motivates the
project. Setwork uses classes for value types and expression trees where they
earn their weight; leaf command construction remains a function.

### 18.4 Use Fig as the canonical intermediate representation

Fig supplies broad source data but includes completion-only concepts, dynamic
TypeScript, and incomplete serializer semantics. Binding internal design to Fig
would make every other source an awkward translation and would expose source
uncertainty poorly.

### 18.5 Use OpenCLI as the canonical intermediate representation

OpenCLI is language-independent and already designed for generation. Its
current schema covers useful scalar types, choices, and variadic values, but
lacks the full serialization algebra, evidence model, dialect profile,
dependency graph, option-terminator policy, and custom expression grammar
required here. An OpenCLI adapter remains valuable.

### 18.6 Execute Fig through Node.js

Evaluation would recover more computed objects and imported helpers. It would
also execute a large, changing third-party codebase during generation and make
network, filesystem, process, and secret isolation part of the trusted build.
The v0.1 design chooses lower coverage and a smaller trust boundary.

### 18.7 Put the compiler inside Cuprum

Cuprum owns command execution; Setwork owns source ingestion and generated
vocabularies. Keeping them separate prevents parser and source-corpus
dependencies from entering Cuprum and lets each project evolve independently. A
small future Cuprum extension for transitive program requirements may still be
appropriate.

## 19. Acceptance criteria

The design counts as correctly implemented for its first release when all of
the following are true:

1. `setwork lock`, `check`, `compile`, `explain`, and `diff` implement the
   contracts in section 13.
2. Locked compilation performs no network access and detects every modified
   input digest.
3. The Fig adapter parses the accepted static subset, rejects executable
   constructs, and reports source spans for unresolved fields.
4. The intermediate representation and publishability validator enforce the
   invariants in section 8.
5. The initial generated package exposes the agreed vertical slice as ordinary
   typed functions returning Cuprum `SafeCmd` values.
6. `functools.partial` positive and negative fixtures pass under the pinned
   Pyright version.
7. Generated commands compose with handwritten Cuprum commands through `|`
   without adapters.
8. Repeated clean generation is byte-identical.
9. Every public symbol and parameter appears in `provenance.json` with locked
   evidence.
10. Every selected command passes its target-profile golden and conformance
    cases.
11. Operand-injection policy is explicit for every positional surface.
12. Delegated execution cannot pass the v0.1 publishability gate.
13. Secret-bearing `argv` parameters cannot pass the v0.1 publishability gate.
14. Licence policy prevents a distributable artefact while the Fig licence
    evidence remains unresolved.
15. The generated wheel imports and runs without compiler or Node.js
    dependencies.

## 20. Deferred decisions and ADR candidates

| ADR     | Decision required                                                            | Latest safe resolution point                          |
| ------- | ---------------------------------------------------------------------------- | ----------------------------------------------------- |
| ADR 001 | First target profile and command-version policy                              | Before writing target conformance fixtures            |
| ADR 002 | Static-only Fig ingestion versus opt-in sandboxed evaluation                 | After measuring static coverage on the vertical slice |
| ADR 003 | Transitive program requirements in Cuprum                                    | Before any delegated action is exposed                |
| ADR 004 | Compiler wheel, generated wheel, extras, or user-generated-only distribution | Before first public package release                   |
| ADR 005 | Generated source committed versus release-generated                          | Before repository CI and review policy settle         |
| ADR 006 | Reference type checker and supported checker matrix                          | Before claiming typesafe partial application publicly |
| ADR 007 | Licence and attribution policy for imported corpora                          | Before publishing derived generated packages          |
| ADR 008 | Public API compatibility and deprecation policy                              | Before the second generated release                   |
| ADR 009 | Secret-bearing argument, redaction, and safer-channel policy                 | Before any secret-valued option is exposed            |

## References

All sources were accessed on 18 July 2026.

- [Cuprum command and pipeline implementation][cuprum-sh]
- [Cuprum handwritten `tar` builder][cuprum-tar-builder]
- [Cuprum catalogue implementation][cuprum-catalogue]
- [Cuprum context implementation][cuprum-context]
- [Fig or Amazon Q completion corpus README][fig-readme]
- [Fig `dd` specification][fig-dd]
- [Fig `find` specification][fig-find]
- [Fig `tar` specification][fig-tar]
- [Fig root licence][fig-license]
- [Fig package metadata][fig-package]
- [Carapace spec README][carapace-spec]
- [OpenCLI README][opencli-readme]
- [OpenCLI JSON Schema][opencli-schema]
- [Python Tree-sitter README][py-tree-sitter]
- [Tree-sitter TypeScript grammar][tree-sitter-typescript]
- [Pyright `functools.partial` test cases][pyright-partial]
- [MITRE CWE-214][cwe-214]
- [Linux `proc_pid_cmdline(5)`][proc-cmdline]

[cuprum-sh]: https://github.com/leynos/cuprum/blob/ba5e4ab7b9e2d760aec56caa45b88d8d67da7e55/cuprum/sh.py
[cuprum-tar-builder]: https://github.com/leynos/cuprum/blob/ba5e4ab7b9e2d760aec56caa45b88d8d67da7e55/cuprum/builders/tar.py
[cuprum-catalogue]: https://github.com/leynos/cuprum/blob/ba5e4ab7b9e2d760aec56caa45b88d8d67da7e55/cuprum/catalogue.py
[cuprum-context]: https://github.com/leynos/cuprum/blob/ba5e4ab7b9e2d760aec56caa45b88d8d67da7e55/cuprum/context.py
[fig-readme]: https://github.com/withfig/autocomplete/blob/aef52acff84c45edde61ae610cc2c964802b9a38/README.md
[fig-dd]: https://github.com/withfig/autocomplete/blob/aef52acff84c45edde61ae610cc2c964802b9a38/src/dd.ts
[fig-find]: https://github.com/withfig/autocomplete/blob/aef52acff84c45edde61ae610cc2c964802b9a38/src/find.ts
[fig-tar]: https://github.com/withfig/autocomplete/blob/aef52acff84c45edde61ae610cc2c964802b9a38/src/tar.ts
[fig-license]: https://github.com/withfig/autocomplete/blob/aef52acff84c45edde61ae610cc2c964802b9a38/LICENSE
[fig-package]: https://github.com/withfig/autocomplete/blob/aef52acff84c45edde61ae610cc2c964802b9a38/package.json
[carapace-spec]: https://github.com/carapace-sh/carapace-spec/blob/master/README.md
[opencli-readme]: https://github.com/bcdxn/opencli/blob/main/README.md
[opencli-schema]: https://github.com/bcdxn/opencli/blob/main/spec.schema.json
[py-tree-sitter]: https://github.com/tree-sitter/py-tree-sitter/blob/master/README.md
[tree-sitter-typescript]: https://github.com/tree-sitter/tree-sitter-typescript
[pyright-partial]: https://github.com/microsoft/pyright/blob/93ea6468a40c7c8cdab5643f66411da5e0414742/packages/pyright-internal/src/tests/samples/partial1.py
[cwe-214]: https://cwe.mitre.org/data/definitions/214.html
[proc-cmdline]: https://man7.org/linux/man-pages/man5/proc_pid_cmdline.5.html
