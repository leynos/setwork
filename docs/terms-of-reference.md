# Setwork – terms of reference

**Status:** Draft v0.1 with acknowledged assumptions and open questions

**Audience:** Product owner, Setwork and Cuprum contributors, security
reviewers, and prospective maintainers

**Last substantive revision:** 18 July 2026

**Companion documents:** [`docs/context.md`](context.md),
[`docs/tech-design.md`](tech-design.md), and [`docs/design/`](design/)

**Decision authority:** This document defines the problem, users, scope, and
constraints. `docs/tech-design.md` defines the proposed solution.

## Evidence status

This is a greenfield brief reconstructed from the Setwork concept discussion,
Cuprum's current repository, and a targeted survey of command-description and
Python command-invocation projects. No Setwork repository or prior brief was
found on 18 July 2026.

The document uses three evidence states:

- **Known** means that the project intent or cited prior art states the claim
  directly.
- **Assumed** means that the project can proceed on the claim, but evidence or a
  product decision must still confirm it.
- **Open** means that the claim remains unresolved and appears in section 9.

## 1. Background and motivation

Cuprum supplies typed command values, asynchronous and synchronous execution,
scoped runtime policy, structured results, observability hooks, and pipeline
composition. Its generic builder still accepts a string-shaped argument
surface, while its command-specific builders encode exact argument vectors by
hand. The existing `tar_create` builder, for example, validates values,
constructs a canonical tuple of tokens, and passes that tuple to `sh.make`.
That pattern works, but every supported command requires new handwritten API,
validation, serialization, documentation, and tests. **Known.**
[Cuprum's users' guide][cuprum-guide] and [`tar.py`][cuprum-tar-builder]
establish the current pattern.

Completion projects have already catalogued large parts of popular command-line
interfaces. Fig's completion corpus, now associated with Amazon Q Developer
CLI, describes subcommands, options, arguments, aliases, dependencies, and
suggestions in TypeScript. Carapace offers a smaller declarative YAML format,
and OpenCLI defines a language-independent command description intended for
code and documentation generation. **Known.** These sources do not, by
themselves, form an authoritative argument-serialization contract.
[Fig][fig-readme], [Carapace spec][carapace-spec], and [OpenCLI][opencli]
document their respective purposes.

Setwork exists to close the gap between those two bodies of work. It should
turn versioned command metadata into ordinary, statically typed Python
functions that serialize exact argument vectors and return Cuprum `SafeCmd`
values. The resulting functions should retain the immediacy of the `sh` Python
library while giving type checkers enough structure to reject invalid calls and
to preserve useful signatures through `functools.partial`. **Known.** This is
the originating project intent.

The timing follows from three conditions:

1. Cuprum now has a stable-enough command and pipeline execution seam on which a
   generated library can depend.
2. Completion and command-description corpora contain enough reusable structure
   to make generation materially cheaper than writing every builder from
   scratch.
3. Python type checkers can model partial application of ordinary functions,
   provided the generated API avoids dynamic attribute lookup and broad
   `Callable[..., Any]` surfaces. Pyright's own tests cover bound positional
   and keyword parameters, variadics, and generic relationships for
   `functools.partial`. **Known.** [Pyright's partial tests][pyright-partial]
   provide the evidence for the third condition.

Without Setwork, Cuprum users can continue to assemble argument vectors
manually, maintain local builder modules, or use dynamic command wrappers.
Those alternatives remain viable, but they duplicate syntax knowledge, weaken
static checking, or move command policy out of the generated API.

## 2. Domain

Setwork operates in the overlap between:

- Python automation and utility code;
- command-line grammar and argument-vector serialization;
- source-to-source code generation;
- static type checking;
- software supply-chain provenance; and
- local process execution through Cuprum.

The domain's central distinction is between **command completion** and
**command invocation**. Completion asks what token might sensibly follow the
current token. Invocation asks which typed values form a valid semantic command
and exactly how those values become an ordered argument vector. A completion
specification may call an argument `count`, suggest numeric-looking values, or
offer a file picker without proving that the target accepts an integer, which
separator it requires, or which program version introduced the option.

Command syntaxes occupy several grammar classes:

| Grammar class          | Examples                                      | Consequence for Setwork                                            |
| ---------------------- | --------------------------------------------- | ------------------------------------------------------------------ |
| Flat option algebra    | `echo`, many core utilities                   | A generated function can usually model the full command.           |
| Assignment operands    | `dd`                                          | Named values serialize as tokens such as `bs=4M`, not POSIX flags. |
| Command family         | `git`, `docker`                               | Runnable leaves map naturally to functions in a module.            |
| Mode-sensitive command | `tar`, `openssl`                              | Separate functions should represent incompatible modes.            |
| Embedded language      | `find`, `sed`, filter expressions             | A command-specific abstract syntax tree is required.               |
| Delegated execution    | `find -exec`, `sh -c`, command-valued options | Authorization must account for programs nested inside arguments.   |

Fig's current `dd` specification demonstrates assignment-style operands and a
comma-separated conversion value. Its current `find` specification leaves the
expression as an opaque variadic token sequence and explicitly records a TODO
for predicates and operands. Its `tar` specification contains useful aliases,
dependencies, and exclusions, but it must represent several accepted option
styles. **Known.** [`dd.ts`][fig-dd], [`find.ts`][fig-find], and
[`tar.ts`][fig-tar] make the differences concrete.

The domain follows these conventions:

- A serializer produces `tuple[str, ...]` or `list[str]`; it does not produce a
  shell command string.
- A generated API may choose one unambiguous canonical representation even when
  the executable accepts several equivalent spellings.
- Command dialect and version are part of the contract. GNU, BSD, BusyBox, and
  vendor variants must not collapse into a fictional universal command.
- Static metadata is evidence, not authority. Curated overlays and
  command-specific grammars resolve gaps.
- A generated package must preserve source revision, licence evidence, and
  transformation provenance.
- Runtime command execution remains Cuprum's responsibility.

The normative vocabulary appears in [`docs/context.md`](context.md).

## 3. Market context

### 3.1 Current alternatives

| Alternative                              | What it does well                                                    | Where it falls short for this job                                                                                   |
| ---------------------------------------- | -------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| Python `subprocess` with explicit `argv` | Standard library, direct, and shell-free when used correctly         | Call sites remain stringly typed and repeat command syntax knowledge.                                               |
| Handwritten Cuprum builders              | Precise validation, exact serialization, and full Cuprum integration | Coverage grows linearly with maintainer effort and can drift between modules.                                       |
| `sh`                                     | Makes arbitrary programs feel like Python functions                  | Discovers and invokes commands dynamically; static signatures do not describe each CLI.                             |
| Plumbum                                  | Provides concise command and pipeline combinators                    | Command lookup and argument construction remain dynamic for this use case.                                          |
| Fig or Amazon Q completion specs         | Broad, maintained command metadata and dynamic suggestions           | Completion semantics are incomplete for safe, canonical invocation.                                                 |
| Carapace spec                            | Compact declarative syntax and generator ecosystem                   | Its portable spec still prioritizes completion rather than a typed Python invocation contract.                      |
| OpenCLI                                  | Language-independent typed command documents and code generation     | Its current schema lacks several serialization, dialect, conflict, and embedded-language concepts Setwork requires. |
| Project-local generated wrappers         | Can fit one organization exactly                                     | Each project must invent its own schema, generator, provenance model, and maintenance process.                      |

The `sh` project explicitly presents programs as callable Python objects, while
Plumbum exposes shell-like combinators and pipelines. They establish the
desired ergonomic baseline, not the desired static contract.
[The `sh` README][sh-readme] and [Plumbum's README][plumbum-readme] document
those surfaces.

### 3.2 Identified gap

The targeted survey found declarative CLI descriptions, completion corpora,
command-wrapper libraries, and Cuprum's typed runtime. It did not identify a
maintained tool that compiles a community completion corpus into versioned,
command-specific, typesafe Python serializers returning Cuprum values. This is
a bounded research finding, not a claim that no unpublished or niche project
exists.

The specific deficiency is not lack of command metadata. It is lack of a
trustworthy transformation from heterogeneous, sometimes executable completion
metadata into:

- explicit target profiles;
- evidence-bearing command semantics;
- exact and canonical serialization;
- ordinary Python signatures;
- Cuprum catalogue and pipeline integration; and
- reproducible generated artefacts.

Setwork competes first with handwritten builder modules and repeated raw `argv`
assembly. It does not need to displace terminal completion products or general
command-wrapper libraries to succeed.

## 4. Users and stakeholders

| Category       | User or stakeholder                                       | Context and priorities                                                                                                         | Current alternative                                  | Explicit dislikes or exclusions                                                                            |
| -------------- | --------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| Primary user   | Python automation engineer                                | Writes CI, deployment, maintenance, build, or administration code; uses static checking; wants command calls to read as Python | `subprocess`, local wrappers, shell scripts          | Dynamic discovery, shell quoting, giant untyped keyword bags, generated APIs that hide dialect assumptions |
| Primary user   | Cuprum application developer                              | Already uses `SafeCmd`, execution contexts, hooks, and pipelines; wants broader typed command coverage                         | `sh.make` plus handwritten `argv`                    | A second execution runtime or adapters that discard Cuprum metadata                                        |
| Secondary user | Wrapper and overlay maintainer                            | Curates command semantics and reviews upstream changes                                                                         | Handwritten builder code and tests                   | Silent inference, source evaluation with ambient credentials, untraceable generated changes                |
| Secondary user | Security or platform reviewer                             | Reviews which executables and option surfaces an application can invoke                                                        | Source review of scattered strings and shell scripts | Hidden delegated execution, runtime `PATH` discovery, incomplete provenance                                |
| Stakeholder    | Cuprum maintainer                                         | Owns the runtime contract on which generated functions depend                                                                  | A small handwritten builder library                  | Setwork-specific complexity leaking into Cuprum without a general runtime need                             |
| Stakeholder    | Upstream spec maintainer                                  | Maintains completion or command-description data                                                                               | Their existing consumers                             | Setwork presenting imported metadata as more authoritative than its source warrants                        |
| Non-user       | Developer needing a general shell language                | Requires globbing, control flow, substitution, redirection grammar, or arbitrary pipelines from strings                        | Bash, Zsh, Nushell, or a shell parser                | Setwork deliberately does not provide a shell                                                              |
| Non-user       | Application requiring arbitrary runtime command discovery | Program names and schemas arrive from untrusted runtime input                                                                  | Dynamic command wrappers or direct subprocess APIs   | Setwork requires curated, generated command surfaces                                                       |

The primary audience is technically fluent and will accept explicit
distinctions between target profiles, unresolved metadata, and unsafe escape
hatches. It will not accept a polished signature whose serializer rests on
guesswork.

## 5. Job to be done

> When a Python engineer needs to invoke external command-line tools from
> maintained automation or application code, they want a discoverable,
> statically checked function for each supported command operation, so they can
> compose Cuprum commands and pipelines without repeatedly reconstructing or
> reviewing string-shaped command syntax.

The functional job has four parts:

1. discover the available command operations through imports, editor completion,
   and generated documentation;
2. construct a valid semantic command from typed Python values;
3. obtain a Cuprum `SafeCmd` that participates in existing execution policy and
   pipelines; and
4. review exactly which source facts and curated decisions produced that API.

The emotional dimension is confidence without ceremony. A call such as
`git.clone(repository, depth=1)` should feel no heavier than a dynamic wrapper,
while an invalid option, wrong enum value, or unsafe delegated command should
fail before process execution.

The social dimension matters in reviewed code. A generated function call should
communicate intent to another engineer and make the accepted executable and
option surface easier to audit than a collection of string literals.

## 6. Scope

### 6.1 Goals

1. **Generate ordinary typed Python functions.** Each publishable command or
   runnable leaf exposes a stable signature and returns a Cuprum `SafeCmd`.
2. **Preserve Python composition.** Generated functions work with
   `functools.partial`, decorators that retain signatures, dependency
   injection, and ordinary imports. They do not require a custom expression
   wrapper for simple commands.
3. **Serialize exact canonical argument vectors.** Each supplied value has an
   explicit serialization rule, position, cardinality, and target profile.
4. **Integrate with Cuprum rather than duplicate it.** Generated commands retain
   Cuprum catalogue metadata, execution contexts, observability, structured
   results, cancellation, and `|` pipeline composition.
5. **Reuse existing command metadata conservatively.** Source adapters import
   useful structure from Fig, OpenCLI, Carapace, and future sources while
   retaining uncertainty and provenance.
6. **Support curated correction.** Overlays can add authoritative types,
   canonical spellings, constraints, safety rules, and dialect information
   without forking an upstream corpus.
7. **Support command-specific grammars.** The compiler provides an explicit
   extension boundary for embedded languages such as `find` expressions.
8. **Make unsafe or unresolved states visible.** A public wrapper cannot be
   generated while required serialization or authorization facts remain
   unresolved.
9. **Produce reproducible artefacts.** A source lock pins revisions and inputs;
   repeated builds from the same lock produce byte-identical generated source
   and provenance records.
10. **Ship a representative initial command set.** The first accepted release
    should exercise simple flags, assignment operands, command families,
    mode-sensitive commands, and one custom expression grammar.

### 6.2 Non-goals

1. **A general shell is out of scope.** Setwork does not parse shell strings,
   provide shell control flow, expand globs, or implement redirection syntax.
   Applications needing those features should use a shell or a dedicated parser.
2. **Process execution is out of scope.** Cuprum owns spawning, streaming,
   cancellation, timeouts, results, and observation.
3. **Runtime command discovery is out of scope.** Setwork does not inspect
   `PATH` and synthesize APIs at import time.
4. **Universal command portability is out of scope.** One generated wrapper does
   not pretend that GNU, BSD, BusyBox, and vendor variants share identical
   semantics. Users select a target profile.
5. **Perfect corpus coverage is out of scope.** Setwork may reject or quarantine
   commands whose metadata cannot support a trustworthy serializer.
6. **Completion generation is out of scope.** Existing completion projects
   already serve that job. Setwork consumes their metadata where useful.
7. **Executable installation and version management are out of scope.** The
   generated library describes an expected target; it does not install or
   update the target program.
8. **Automatic execution of imported source code is out of scope for the safe
   default.** Dynamic completion generators may be supported only through an
   explicit, isolated policy whose risks are separately accepted.
9. **Remote execution and process supervision are out of scope.** These remain
   Cuprum non-goals and do not enter through generated wrappers.
10. **A raw escape hatch is not a substitute for coverage.** Applications can
    use
    Cuprum's lower-level facilities when necessary, but Setwork does not label
    arbitrary tokens as typesafe.
11. **Typed `argv` is not a secret transport.** The safe generated surface does
    not expose password, token, or private-key values through process arguments
    until the project defines sensitivity, redaction, and safer-channel policy.
    [CWE-214][cwe-214] describes this information-exposure class.

## 7. Success criteria

### 7.1 User-facing success

- A new user can import a generated function, construct a command, partially
  apply options, compose a pipeline, and inspect its argument vector without
  learning a Setwork-specific runtime object model.
- Pyright in strict mode rejects wrong value types, unknown keywords, missing
  required operands, and invalid enum values for the supported generated
  surface.
- The accepted initial command set includes at least one representative of each
  grammar class named in goal 10. The proposed evaluation set is `echo`, `dd`,
  selected `git` leaves, `tar.create`, `tar.extract`, and a non-delegating
  `find` expression subset. **Assumed; final scope remains open.**
- Reviewers can trace every generated public parameter to source evidence or a
  curated override.

### 7.2 Operational success

- Two clean builds from the same manifest, source lock, compiler version, and
  overlays produce byte-identical generated source, notices, and provenance.
- The generated runtime package imports without Node.js, TypeScript, Fig,
  Tree-sitter, or Setwork's compiler dependencies.
- The compiler refuses publication when a parameter lacks a target profile,
  canonical spelling, serialization rule, evidence record, sensitivity
  classification, or required safety policy.
- Secret-bearing parameters do not enter the default generated `argv` surface.
- Every generated serialization branch has a checked example or generated
  property test that compares the produced token sequence with its expected
  canonical form.
- Source updates produce a semantic diff that separates added, removed, changed,
  unresolved, and overlay-conflicting command facts.

### 7.3 Strategic success

- Cuprum projects can replace repeated local argument-vector assembly with a
  shared generated package without changing their execution model.
- Adding an ordinary flat command requires source selection and limited
  curation, not a new handwritten public module from first principles.
- Difficult commands remain explicit exceptions rather than distorting the
  common intermediate representation.

Adoption, retention, and maintenance-cost thresholds remain open because no
Setwork implementation or user cohort exists yet.

## 8. Constraints and assumptions

### 8.1 Hard constraints

| Constraint                                                                                                                                 | Status                      | Consequence                                                                      |
| ------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------- | -------------------------------------------------------------------------------- |
| Generated calls return Cuprum `SafeCmd` values.                                                                                            | Known                       | Setwork cannot replace or wrap away Cuprum's command and pipeline semantics.     |
| Generated code passes exact token sequences, not shell strings.                                                                            | Known                       | No shell interpolation or quoting layer belongs in the serializer.               |
| The initial Python floor follows Cuprum's supported floor, currently Python 3.12 or later.                                                 | Known, externally versioned | A Cuprum compatibility policy must govern future changes.                        |
| Public APIs are ordinary Python functions with concrete annotations.                                                                       | Known                       | Dynamic module attributes cannot form the primary API.                           |
| Imported source licences and attribution requirements apply to generated distributions.                                                    | Known                       | Release tooling must retain notices and may need legal review.                   |
| Command dialect is explicit.                                                                                                               | Known                       | The manifest or package name must identify a target profile.                     |
| Unresolved serializer semantics block publication.                                                                                         | Known                       | Coverage will be lower than the raw completion corpus.                           |
| Secret-bearing `argv` parameters block the safe surface until an explicit policy resolves their operating-system and observation exposure. | Known security constraint   | Some upstream options remain omitted even when their grammar is otherwise known. |
| Paragraphs and public documentation use British English with Oxford spelling.                                                              | Known                       | Generated prose and maintained docs follow the df12 documentation convention.    |

### 8.2 Assumptions

| Assumption                                                                                        | Failure consequence                                                                               | Required response                                                                            |
| ------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| Completion corpora contain enough static structure to reduce curation effort for common commands. | The compiler becomes a thin front end over mostly handwritten overlays.                           | Measure imported versus curated facts across the initial command set before expanding scope. |
| Users accept target-specific packages or profiles.                                                | A demand for one portable signature creates unions, runtime branching, and misleading guarantees. | Validate packaging and naming with early adopters.                                           |
| Pyright remains the reference type checker for partial-application acceptance.                    | Other type checkers may expose weaker inferred signatures.                                        | Publish a supported-checker matrix and avoid claims beyond tested behaviour.                 |
| Cuprum preserves a stable construction seam equivalent to `sh.make` and `SafeCmd`.                | Generated packages break on Cuprum upgrades.                                                      | Pin a compatibility range and run contract tests against supported Cuprum releases.          |
| Curated maintainers can determine authoritative semantics for disputed commands.                  | Ambiguous commands remain unpublished.                                                            | Record the gap rather than infer through parameter names or descriptions.                    |
| Static extraction covers a useful subset of Fig TypeScript.                                       | Many specs become dynamic and unavailable to the safe adapter.                                    | Add explicitly sandboxed evaluation only after a separate threat and licence review.         |

### 8.3 Dependencies

| Dependency                                            | Role                                                       | Critical-path concern                                           |
| ----------------------------------------------------- | ---------------------------------------------------------- | --------------------------------------------------------------- |
| Cuprum                                                | Runtime command, catalogue, context, and pipeline contract | API compatibility and delegated-program authorization           |
| Python type checker, initially Pyright                | Validates generated call surfaces and partial application  | Cross-checker differences                                       |
| Source corpora such as Fig, Carapace, and OpenCLI     | Bootstrap command metadata                                 | Accuracy, dialect, update cadence, and licence terms            |
| Target command documentation and conformance fixtures | Authoritative corrections and expected serialization       | Version-specific availability and maintenance cost              |
| TypeScript parser for static Fig extraction           | Reads syntax without executing imported code               | Unsupported dynamic constructs must produce precise diagnostics |
| Package index and project naming                      | Distribution of compiler and generated library             | The `setwork` name must be checked before publication           |

## 9. Open questions

| ID    | Question                                                                                                         | Why it matters                                                                                       | Resolution criterion                                                                                                   | Suggested owner or path                               |
| ----- | ---------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------- |
| OQ-1  | Which target profile ships first: GNU/Linux, macOS/BSD, BusyBox, or a narrower pinned toolchain?                 | It determines command semantics, fixtures, package naming, and initial users.                        | Product decision backed by at least three representative workflows.                                                    | Product owner; user interviews or a repository survey |
| OQ-2  | Which commands define the first releasable corpus?                                                               | The set must prove the architecture without becoming an open-ended catalogue project.                | Accepted vertical slice with one example from every in-scope grammar class.                                            | Product owner and compiler maintainer                 |
| OQ-3  | May Setwork redistribute normalized or generated material derived from the Fig corpus?                           | Fig's root `LICENSE` says MIT, while its `package.json` declares ISC at the examined revision.       | Written licence interpretation, upstream clarification, or a distribution model that avoids copying disputed material. | Maintainer with legal review or upstream issue        |
| OQ-4  | Does the compiler permanently reject executable completion constructs, or support an opt-in sandboxed evaluator? | Static extraction limits coverage; evaluation introduces code-execution and supply-chain risk.       | ADR with threat model, isolation requirements, and measured coverage gain.                                             | Security reviewer and compiler maintainer             |
| OQ-5  | How should Cuprum authorize delegated execution such as `find -exec`?                                            | Authorizing only the outer `find` program can bypass a scoped executable allowlist.                  | Cuprum contract for transitive program sets or an explicit decision to exclude delegated execution.                    | Joint Setwork and Cuprum ADR                          |
| OQ-6  | Does the project publish one generated package, target-specific extras, or user-generated source only?           | The choice changes release cadence, licence obligations, wheel size, and compatibility promises.     | Packaging experiment and accepted support policy.                                                                      | Product owner and release maintainer                  |
| OQ-7  | Are generated sources committed to the repository?                                                               | Committed source improves review and source distributions; generated-only builds reduce duplication. | ADR covering reproducibility, review, and release failure modes.                                                       | Compiler maintainer                                   |
| OQ-8  | Which type checkers receive compatibility guarantees?                                                            | `functools.partial` and overload inference differ between checkers.                                  | Automated matrix and documented minimum versions.                                                                      | Type-system maintainer                                |
| OQ-9  | What command-version policy applies inside a target profile?                                                     | A profile without version bounds becomes stale or internally inconsistent.                           | Semantic version or capability policy plus update and deprecation rules.                                               | Specification maintainer                              |
| OQ-10 | Is `setwork` available and defensible as the public distribution and import name?                                | A name collision would force a late API and branding change.                                         | Checks across PyPI, major source hosts, and relevant trademarks before first publication.                              | Product owner                                         |
| OQ-11 | What usage signal will justify expansion beyond the initial corpus?                                              | Otherwise corpus growth can consume maintenance effort without proving value.                        | Agreed adoption or contribution threshold after the first release.                                                     | Product owner                                         |
| OQ-12 | How should secret-bearing options interact with Cuprum observation and operating-system process visibility?      | A typed password or token in `argv` can still leak through logs, traces, and process inspection.     | Sensitivity policy, safer-channel guidance, and any Cuprum redaction contract.                                         | Joint Setwork and Cuprum security review              |

None of OQ-1, OQ-3, OQ-5, OQ-6, or OQ-12 should remain implicit at the first
public release. OQ-5 blocks delegated-command features, but it does not block a
safe initial subset.

## 10. Handoff

### 10.1 Downstream readiness

The terms of reference is sufficient for a draft technical design because the
primary user, job, scope, safety boundary, and principal uncertainties are
explicit. The companion design deliberately excludes delegated execution from
its publishable v0.1 surface and treats packaging and target-profile choices as
configurable or deferred where possible.

### 10.2 Context additions

[`docs/context.md`](context.md) records the initial vocabulary. Contributors
should add terms there before introducing alternate names in code or design
prose.

### 10.3 Architecture decision record candidates

1. Static-only Fig extraction versus sandboxed evaluation.
2. Target-profile and command-version policy.
3. Transitive program authorization for delegated execution.
4. Generated-source and distribution packaging policy.
5. Source licensing, attribution, and derived-data policy.
6. Reference type checker and cross-checker support policy.
7. Secret-bearing argument and observability policy.

## References

All sources were accessed on 18 July 2026. Repository links are pinned where
the examined revision matters.

- [Cuprum README][cuprum-readme]
- [Cuprum users' guide][cuprum-guide]
- [Cuprum `tar` builder][cuprum-tar-builder]
- [Cuprum roadmap][cuprum-roadmap]
- [Fig or Amazon Q completion corpus README][fig-readme]
- [Fig `dd` specification][fig-dd]
- [Fig `find` specification][fig-find]
- [Fig `tar` specification][fig-tar]
- [Fig root licence][fig-license]
- [Fig package metadata][fig-package]
- [Carapace spec README][carapace-spec]
- [OpenCLI README][opencli]
- [Python `sh` README][sh-readme]
- [Plumbum README][plumbum-readme]
- [Pyright `functools.partial` test cases][pyright-partial]
- [MITRE CWE-214][cwe-214]

[cuprum-readme]: https://github.com/leynos/cuprum/blob/ba5e4ab7b9e2d760aec56caa45b88d8d67da7e55/README.md
[cuprum-guide]: https://github.com/leynos/cuprum/blob/ba5e4ab7b9e2d760aec56caa45b88d8d67da7e55/docs/users-guide.md
[cuprum-tar-builder]: https://github.com/leynos/cuprum/blob/ba5e4ab7b9e2d760aec56caa45b88d8d67da7e55/cuprum/builders/tar.py
[cuprum-roadmap]: https://github.com/leynos/cuprum/blob/ba5e4ab7b9e2d760aec56caa45b88d8d67da7e55/docs/roadmap.md
[fig-readme]: https://github.com/withfig/autocomplete/blob/aef52acff84c45edde61ae610cc2c964802b9a38/README.md
[fig-dd]: https://github.com/withfig/autocomplete/blob/aef52acff84c45edde61ae610cc2c964802b9a38/src/dd.ts
[fig-find]: https://github.com/withfig/autocomplete/blob/aef52acff84c45edde61ae610cc2c964802b9a38/src/find.ts
[fig-tar]: https://github.com/withfig/autocomplete/blob/aef52acff84c45edde61ae610cc2c964802b9a38/src/tar.ts
[fig-license]: https://github.com/withfig/autocomplete/blob/aef52acff84c45edde61ae610cc2c964802b9a38/LICENSE
[fig-package]: https://github.com/withfig/autocomplete/blob/aef52acff84c45edde61ae610cc2c964802b9a38/package.json
[carapace-spec]: https://github.com/carapace-sh/carapace-spec/blob/master/README.md
[opencli]: https://github.com/bcdxn/opencli/blob/main/README.md
[sh-readme]: https://github.com/amoffat/sh/blob/develop/README.rst
[plumbum-readme]: https://github.com/tomerfiliba/plumbum/blob/master/README.rst
[pyright-partial]: https://github.com/microsoft/pyright/blob/93ea6468a40c7c8cdab5643f66411da5e0414742/packages/pyright-internal/src/tests/samples/partial1.py
[cwe-214]: https://cwe.mitre.org/data/definitions/214.html
