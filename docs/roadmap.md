# Setwork roadmap

This roadmap turns the
[technical design](tech-design.md), [terms of reference](terms-of-reference.md),
and [context](context.md) into a Goals, Ideas, Steps, Tasks (GIST) delivery
sequence. The goal is to let Python engineers construct statically checked
Cuprum commands without repeating argument-vector assembly, while preserving
explicit dialects and evidence.

Phases carry testable ideas, steps answer delivery questions, and checkbox
items are review-sized execution units. Each task includes unit and behavioural
validation of its implementation; property checks belong alongside the
invariants they verify. End-to-end and combinatorial suites receive explicit
tasks where they span multiple features. This roadmap makes no date commitments.

All tasks are initially unchecked: the existing greeting scaffold and design
sketches are not an implemented compiler. Architecture Decision Records (ADRs)
will live under `docs/` using the naming rules in the
[documentation style guide](documentation-style-guide.md#architectural-decision-records-adrs).
The ADR numbers below refer to candidates in technical design §20, not
accepted records. Later phases proceed only when their cited dependencies and
decisions are satisfied. The final phase is deferred beyond v0.1.

## 1. Settle the contracts for a reproducible first slice

Idea: explicit target, evidence, typing, and package boundaries will let a
narrow generated command prove the architecture without repeated contract
changes. Conflicting decisions or an inseparable compiler/runtime dependency
would falsify this idea.

This phase settles release-critical assumptions and the shared interfaces used
by every slice. It preserves the source-neutral model and Cuprum execution seam
from technical design §§1–5, including the rationale in §18.

### 1.1. Choose an initial promise that can be tested

Which profile and command set can represent the intended users' workflows? The
answer determines conformance environments and the scope of later slices. See
technical design §§2–4, 6.4, 12, 20 and terms of reference §§1–9.

- [ ] 1.1.1. Record ADR 001 with the first target profile, version policy, and
  agreed command evaluation set.
  - See [technical design](tech-design.md) §§6.4, 12, 20 and
    [terms of reference](terms-of-reference.md) §9, OQ-1, OQ-2, OQ-9.
  - Success: at least three representative user workflows justify a pinned
    environment and one example of each in-scope grammar class.
- [ ] 1.1.2. Record ADR 006 with a pinned reference Pyright version and the
  supported type-checker claims.
  - See [technical design](tech-design.md) §§3, 16.4, 20 and
    [terms of reference](terms-of-reference.md) §9, OQ-8.
  - Success: representative direct and partial calls have positive and
    negative fixtures; unsupported checkers carry no compatibility guarantee.
- [ ] 1.1.3. Record ADRs 004 and 005 for distribution boundaries and ownership
  of generated source.
  - Requires 1.1.1.
  - See [technical design](tech-design.md) §§5.2–5.3, 17, 20 and
    [terms of reference](terms-of-reference.md) §9, OQ-6, OQ-7, OQ-10.
  - Success: a packaging experiment separates compiler dependencies from
    runtime imports and records public-name checks before publication.
- [ ] 1.1.4. Record ADR 007 and encode source licence decisions.
  - See [technical design](tech-design.md) §§6.3, 17.2, 20 and
    [terms of reference](terms-of-reference.md) §9, OQ-3.
  - Success: allow, deny, and review-required outcomes are explicit; disputed
    Fig-derived artefacts stay blocked unless evidence resolves the discrepancy.

### 1.2. Make every later slice use the same compiler contracts

Can the normative sketches become coherent interfaces without putting compiler
concerns into Cuprum? This establishes the implementation spine and determines
which omissions must block generation. See technical design §§5, 8–9, 14–15.

- [ ] 1.2.1. Establish compiler, adapter, grammar, and generated-package
  boundaries with the existing repository gates.
  - Requires 1.1.3.
  - See [technical design](tech-design.md) §§5, 18.7 and
    [repository layout](repository-layout.md).
  - Success: build and import checks enforce the chosen package boundaries;
    the developer guide documents ownership and reuse conventions.
- [ ] 1.2.2. Implement immutable intermediate representation (IR) types and
  versioned canonical encoding from the normative sketch.
  - Requires 1.2.1.
  - See [technical design](tech-design.md) §§4, 8,
    [context](context.md), and [IR sketch](design/setwork_ir.py).
  - Success: round-trip properties preserve field evidence, cardinality,
    effects, sensitivity, and ordering; invalid names and relations fail.
- [ ] 1.2.3. Implement publishability checks and structured diagnostics.
  - Requires 1.2.2.
  - See [technical design](tech-design.md) §§7.3, 8.5, 13.1, 14–15, 17.4 and
    [publication validation sketch](design/setwork_ir_validation.py).
  - Success: complete, declared-subset, and internal-draft policies distinguish
    publishable fields from blockers with stable codes and source locations;
    delegated execution, unknown semantics, and secret `argv` values fail.
- [ ] 1.2.4. Define the overlay and custom-grammar contracts with validated
  configuration schemas and explicit replacement evidence.
  - Requires 1.2.2.
  - See [technical design](tech-design.md) §§8.4, 9.1–9.2 and
    [example manifest](design/setwork.example.toml).
  - Success: unknown keys fail; plugins receive immutable facts and profile
    data, and their outputs pass the common publication gates.

## 2. Generate and inspect a trustworthy `echo` command

Idea: static evidence plus limited curation can produce a useful typed command
through one locked compiler loop. If `echo` requires source execution or broad
handwritten generation, the corpus-reuse assumption needs revision.

This slice delivers source acquisition, checking, compilation, and provenance
for the smallest command. Distribution stays subject to the licence policy.

### 2.1. Acquire and curate `echo` without executing completion code

How much usable semantics can static extraction recover? The results determine
adapter coverage and the curation burden before more commands are added. See
technical design §§6–9, 12.1.

- [ ] 2.1.1. Implement manifest loading and `setwork lock` with canonical source
  locks and verified immutable local inputs.
  - Requires steps 1.1–1.2.
  - See [technical design](tech-design.md) §§6, 13.1.
  - Success: revisions, file and licence digests, overlays, plugin sources,
    and adapter versions are pinned; modified or missing inputs return status 3.
- [ ] 2.1.2. Implement static Fig extraction for literals, local constants,
  shorthand, static spreads, configured members, and default exports.
  - Requires 2.1.1.
  - See [technical design](tech-design.md) §§7, 14.3, 16.1, V-010.
  - Success: unsupported constructs retain unresolved fields and precise
    spans; sentinels prove no source-controlled execution or ambient I/O;
    configured resource limits bound parsing and diagnostic volume.
- [ ] 2.1.3. Implement evidence-preserving normalization and overlay merging,
  then curate the selected `echo` dialect.
  - Requires 2.1.2 and 1.2.4.
  - See [technical design](tech-design.md) §§8.3–8.4, 9.1, 12.1.
  - Success: equal-precedence conflicts block output; replacements retain
    reasons and prior evidence; leading-option operands have a verified policy.
- [ ] 2.1.4. Expose `setwork check` with text and canonical JSON diagnostics.
  - Requires 2.1.3 and 1.2.3.
  - See [technical design](tech-design.md) §§13, 15, 17.4.
  - Success: accepted and rejected `echo` inputs produce the documented exit
    statuses without generating files, including status 4 for licence blockers.

### 2.2. Deliver the first typed call and explain its tokens

Does the generated call preserve ordinary Python ergonomics and Cuprum policy?
This proves the output boundary that later grammar slices will extend. See
technical design §§10–11, 13.2, 16.

- [ ] 2.2.1. Implement structured Python generation for `echo`, its catalogue,
  `py.typed`, API manifest, provenance, and notices.
  - Requires 2.1.4.
  - See [technical design](tech-design.md) §§10.1–10.2, 10.4–10.5, 11.1–11.3,
    17.1 and [generated API example](design/generated_api_example.py).
  - Success: literals cannot inject source; sanitized docstrings and all
    public fields retain evidence; catalogue metadata matches each `SafeCmd`.
- [ ] 2.2.2. Implement `setwork compile --locked` with verification before
      atomic
  replacement of the output tree.
  - Requires 2.2.1.
  - See [technical design](tech-design.md) §§6.2, 15–17.
  - Success: compilation denies network access, checks digests, formats and
    verifies output, preserves the previous tree on failure, and generates
    byte-identical trees on repeated isolated runs (V-001).
- [ ] 2.2.3. Implement `setwork explain` for public symbols and parameters.
  - Requires 2.2.1.
  - See [technical design](tech-design.md) §§13.2, 16.1, V-009.
  - Success: every public field exposes its type, tokens, profile, evidence,
    resolutions, generated location, and verification cases.
- [ ] 2.2.4. Deliver the end-to-end `echo` acceptance workflow and user guide.
  - Requires 2.2.2, 2.2.3, and 1.1.2.
  - See [technical design](tech-design.md) §§11–12.1, 16.2, 16.4–16.5, 19.
  - Success: lock, check, compile, explain, import, partial application, scoped
    execution, and a pipeline with a handwritten Cuprum command work in the
    pinned environment; invalid types and operands fail at their stated gates.

## 3. Extend the loop to assignment operands and command families

Idea: the common IR and generator can express `dd` assignments and selected
`git` leaves without separate runtime builders. Excessive command-specific
patches would challenge the shared-model design.

These slices reuse the established compiler loop and measure whether additional
commands require limited, reviewable curation.

### 3.1. Deliver typed `dd` assignments with canonical ordering

Can assignment operands and finite conversion domains remain ordinary typed
values? This determines whether the serializer algebra covers non-flag syntax.
See technical design §§8.2, 10, 12.2.

- [ ] 3.1.1. Implement shared serialization strategies for presence, separate,
  equals, attached, repeated, assignment, and comma-joined values.
  - Requires phase 2.
  - See [technical design](tech-design.md) §§8.2, 10.2–10.4, 14.4, 16.1.
  - Success: properties verify token integrity, omission, canonicality, and
    cardinality (V-002–V-004); three-state optional arguments use typed `BARE`.
- [ ] 3.1.2. Curate and generate the selected `dd` surface, including semantic
  names, size grammar, integer bounds, paths, and conversion enums.
  - Requires 3.1.1.
  - See [technical design](tech-design.md) §12.2 and
    [generated API example](design/generated_api_example.py).
  - Success: pinned target cases match exact assignment tokens; invalid size
    expressions, counts, NULs, and non-authoritative enum domains fail.
- [ ] 3.1.3. Add a combinatorial `dd` acceptance suite across omission, zero
  values, conversions, sizes, and path forms.
  - Requires 3.1.2.
  - See [technical design](tech-design.md) §§16.2–16.3, 16.5.
  - Success: safe temporary-file runs confirm effects and canonical order;
    coverage records exercised combinations and untested higher-order cases.

### 3.2. Deliver selected `git` leaves with explicit shared options

Can a command tree become stable leaf signatures without a mutable builder? The
answer determines family flattening and signature-size policy. See technical
design §§10.2, 12.3.

- [ ] 3.2.1. Normalize selected `git` leaves and generate their modules,
  command paths, and explicit global/local option slots.
  - Requires 3.1.1.
  - See [technical design](tech-design.md) §§4, 10.1–10.2, 10.4, 12.3.
  - Success: source-to-IR snapshots capture runnable leaves; collisions and
    excessive signatures require a reviewed rename, split, or declared subset.
- [ ] 3.2.2. Deliver end-to-end `git clone` and `git status` cases using local
  temporary repositories and generated type fixtures.
  - Requires 3.2.1.
  - See [technical design](tech-design.md) §§11, 16.2, 16.4–16.5.
  - Success: paths and leaf-specific options preserve exact tokens and partial
    typing; no test requires network access; user documentation names omissions.

## 4. Deliver mode-sensitive archives and typed search expressions

Idea: explicit mode functions and reviewed expression grammars can cover
complex commands while retaining the same publication and Cuprum contracts.
Raw-token escape hatches or weakened effect checks would falsify this idea.

This phase completes the proposed grammar-class evaluation set. It includes
cross-feature coverage because mode constraints and expression precedence
cannot be demonstrated by a handful of happy-path examples.

### 4.1. Make archive modes separate and predictable

Can `tar.create` and `tar.extract` expose coherent signatures for incompatible
operations? The result tests mode partitioning and constraint enforcement. See
technical design §§9.1, 10.2–10.4, 12.4.

- [ ] 4.1.1. Implement mode partitioning and curate `tar.create` and
      `tar.extract`
  with compression, destination, dependency, and exclusion rules.
  - Requires 3.1.1 and 3.2.1.
  - See [technical design](tech-design.md) §§8.5, 12.4, 14.4.
  - Success: each mode has a concrete signature and canonical syntax;
    invalid relationships fail before `SafeCmd` construction (V-005).
- [ ] 4.1.2. Add combinatorial archive conformance for modes, compression,
  option states, conflicts, and leading-hyphen operands.
  - Requires 4.1.1.
  - See [technical design](tech-design.md) §§16.2–16.3, 16.5.
  - Success: exhaustive combinations at or below 12 finite interaction
    parameters and pairwise plus targeted cases above that threshold verify
    safe temporary archive effects; uncovered combinations remain visible.

### 4.2. Make expression structure carry `find` semantics

Can a custom grammar preserve Boolean meaning without delegated actions or raw
expression strings? This tests the plugin seam against an embedded language.
See technical design §§9.2–9.3, 12.5, 14.6.

- [ ] 4.2.1. Implement the GNU `find` grammar plugin with typed predicates,
  Boolean nodes, canonical parentheses, and a non-delegating action subset.
  - Requires 1.2.4, 2.2.1, and 3.1.1.
  - See [technical design](tech-design.md) §§9.2–9.3, 12.5 and
    [expression example](design/find_expression_example.py).
  - Success: generated-tree properties round-trip through an independent
    reference parser (V-006); unsupported arities and delegated actions fail.
- [ ] 4.2.2. Integrate the grammar with generated `find` builders, profile
  policy, provenance, and catalogue metadata.
  - Requires 4.2.1.
  - See [technical design](tech-design.md) §§9.2, 11, 12.5, 14.4.
  - Success: search roots have an explicit operand policy; plugin output
    passes common checks; raw expression tokens cannot enter the typed surface.
- [ ] 4.2.3. Deliver end-to-end expression conformance on temporary file trees.
  - Requires 4.2.2.
  - See [technical design](tech-design.md) §§16.2–16.5, 19.
  - Success: observed matches agree with independently evaluated expressions
    across nested precedence, negation, path patterns, and supported actions;
    generated calls and partials pass the pinned type-checker contract.

## 5. Prove source neutrality and reviewable updates

Idea: additional declarative sources and semantic diffs can reuse the same
contracts while keeping API changes explicit. Source-specific public APIs or
silent upstream renames would falsify this idea.

This phase broadens evidence sources, rather than expanding the initial command
promise indiscriminately. It makes corpus maintenance a reviewable workflow.

### 5.1. Import alternative sources without changing generated semantics

Can OpenCLI and Carapace facts participate in the same resolution rules? The
results determine whether source neutrality survives real format gaps. See
technical design §§1, 5.1, 8.3–8.4, 18.4–18.5.

- [ ] 5.1.1. Implement schema-validated OpenCLI YAML/JSON ingestion.
  - Requires phase 2.
  - See [technical design](tech-design.md) §§1, 5.1, 18.5 and
    [terms of reference](terms-of-reference.md) §6.1, goal 5.
  - Success: scalar types, choices, and variadics preserve evidence; missing
    serialization and dialect facts remain unresolved until curated.
- [ ] 5.1.2. Implement portable Carapace YAML ingestion.
  - Requires phase 2.
  - See [technical design](tech-design.md) §§1, 5.1 and
    [terms of reference](terms-of-reference.md) §6.1, goal 5.
  - Success: optional, repeatable, and valued flags normalize into the shared
    IR; completion-only generators are never executed or treated as semantics.
- [ ] 5.1.3. Add cross-source end-to-end equivalence and conflict cases.
  - Requires 5.1.1, 5.1.2, and phases 3–4.
  - See [technical design](tech-design.md) §§8.3–8.4, 16.1, 18.4–18.5.
  - Success: equivalent resolved inputs emit the same API and tokens, while
    provenance differs faithfully; contradictory facts require named overrides.

### 5.2. Make upstream changes reviewable before they alter APIs

Can maintainers update locks without silently changing public signatures? This
establishes compatibility policy before a second generated release. See
technical design §§10.6, 13, 17.3, 20.

- [ ] 5.2.1. Record ADR 008 with compatibility, rename, deprecation, and removal
  rules for public symbols and command-version updates.
  - Requires phases 3–4.
  - See [technical design](tech-design.md) §§10.6, 20 and
    [terms of reference](terms-of-reference.md) §9, OQ-9.
  - Success: representative additive, behavioural, and breaking changes have
    explicit review and release outcomes; alias lifetimes follow stated policy.
- [ ] 5.2.2. Implement `setwork diff` for locks and API manifests with semantic
  classifications and overlay-conflict diagnostics.
  - Requires 5.2.1 and 2.2.1.
  - See [technical design](tech-design.md) §§10.6, 13, 17.3.
  - Success: reports distinguish additive, source-compatible behavioural,
    deprecating, breaking, provenance-only, and newly unresolved changes.
- [ ] 5.2.3. Wire reviewed source updates into continuous integration (CI) and
  document the maintenance workflow.
  - Requires 5.2.2 and 5.1.3.
  - See [technical design](tech-design.md) §§15, 17.2–17.4.
  - Success: CI attaches semantic reports; removed options and stale overlays
    require compatibility decisions; new unresolved fields do not become public.

## 6. Establish a reproducible and usable v0.1 release

Idea: evidence from isolated artefacts and real automation workflows can
support an initial release with bounded guarantees. Hidden compiler
dependencies or unresolved acceptance criteria would invalidate readiness.

This phase integrates prior slices and checks operational adoption. Licence,
profile, packaging, and checker decisions remain mandatory release gates.

### 6.1. Make the generated wheel independent of the compiler

Can users install and run the chosen generated distribution offline without
source tooling? This tests the packaging decision against actual artefacts. See
technical design §§5.2, 17–19.

- [ ] 6.1.1. Implement the chosen compiler/generated distribution build with
  provenance, notices, `py.typed`, and the complete output-tree digest.
  - Requires phases 2–5 and 1.1.3–1.1.4.
  - See [technical design](tech-design.md) §§17.1–17.2, 19.
  - Success: wheel and source-distribution boundaries follow the ADRs;
    unsupported licence outcomes prevent distributable artefacts.
- [ ] 6.1.2. Add isolated artefact acceptance for direct wheels and wheels
  rebuilt from source distributions where the chosen model provides them.
  - Requires 6.1.1.
  - See [technical design](tech-design.md) §§5.2, 16.1, 17.2, 19.
  - Success: installed runtime calls import and compose with supported Cuprum
    versions offline, without Node.js, parser, source-corpus, or compiler imports;
    metadata and public-field provenance survive each supported build route.

### 6.2. Evaluate the full promise before declaring readiness

Does the initial corpus reduce repeated argument assembly for the intended
users while meeting every release criterion? The answer controls release and
any later expansion. See technical design §§16, 19 and terms of reference §7.

- [ ] 6.2.1. Deliver a package-wide end-to-end and combinatorial acceptance
  matrix for all selected commands and five CLI operations.
  - Requires 6.1.2 and 5.2.3.
  - See [technical design](tech-design.md) §§13–16, 19.
  - Success: V-001–V-011 and all 15 first-release criteria have evidence;
    failures exercise exit statuses 1–4, atomic output preservation, licence
    blocks, scope restrictions, and tampered locks in pinned environments.
- [ ] 6.2.2. Publish the supported-profile, command-coverage, and checker matrix
  with executable user workflows and an adoption decision.
  - Requires 6.2.1.
  - See [technical design](tech-design.md) §§2, 12, 19 and
    [terms of reference](terms-of-reference.md) §§4–5, 7–9, OQ-11.
  - Success: three representative workflows demonstrate useful typed command
    construction; imported versus curated fact counts and maintenance effort
    inform an explicit expansion threshold; README claims match shipped scope.

## 7. Evaluate extensions after the core release

Idea: once the bounded v0.1 promise has acceptance evidence, broader features
can be evaluated on measured value. Extensions that cannot justify their
maintenance or authorization cost remain deferred.

These tasks are outside v0.1. General shells, runtime command discovery,
executable installation, remote execution, and process supervision remain
non-goals under technical design §2.2 and terms of reference §6.2.

### 7.1. Decide whether dynamic extraction earns a new trust boundary

Would evaluated Fig constructs recover enough useful facts to justify a new
execution boundary? The result determines whether an evaluator is ever built.
See technical design §§7.4, 18.6, 20.

- [ ] 7.1.1. Record ADR 002 from measured static coverage and an evaluator
  threat model, including a decision to retain static-only ingestion if needed.
  - Requires 6.2.2.
  - See [technical design](tech-design.md) §§7.4, 18.6, 20 and
    [terms of reference](terms-of-reference.md) §9, OQ-4.
  - Success: acceptance requires measured coverage gain, licence clearance,
    deterministic output, resource bounds, and a credentials-free isolated
    process; implementation needs a subsequent scoped delivery plan.

### 7.2. Resolve authorization before enabling delegated programs

Can Cuprum authorize an immutable transitive program set before spawning the
outer command? This determines whether delegated actions may graduate. See
technical design §§11.5, 14.6, 20.

- [ ] 7.2.1. Record joint ADR 003 with Cuprum and prototype its execution
  requirements contract before exposing any delegated action.
  - Requires 6.2.2.
  - See [technical design](tech-design.md) §§11.5, 14.6, 20 and
    [terms of reference](terms-of-reference.md) §9, OQ-5.
  - Success: allowlist-bypass cases fail before spawn; both projects accept
    the contract; v0.1 rejection remains until a new policy has conformance proof.

### 7.3. Resolve transport and observation before exposing secret values

Can a safer channel deliver credentials with an explicit effect and lifetime
policy? This decides whether secret-valued features may enter a future surface.
See technical design §§14.5, 20.

- [ ] 7.3.1. Record joint ADR 009 for sensitivity, approved channels, and Cuprum
  observation/redaction requirements.
  - Requires 6.2.2.
  - See [technical design](tech-design.md) §§14.5, 20 and
    [terms of reference](terms-of-reference.md) §9, OQ-12.
  - Success: channel-specific exposure and lifetime tests justify any proposed
    exception; redaction alone does not approve secrets in process arguments.

### 7.4. Expand only where adoption evidence supports maintenance

Which additional commands, profiles, or checker guarantees earn ongoing
support? This uses the initial adoption signal to constrain catalogue growth.
See terms of reference §§8.2, 9 and technical design §§6.4, 12, 20.

- [ ] 7.4.1. Select a bounded extension using the agreed adoption threshold and
  publish its profile, curation budget, and conformance requirements.
  - Requires 6.2.2.
  - See [terms of reference](terms-of-reference.md) §9, OQ-11 and
    [technical design](tech-design.md) §§6.4, 12, 20.
  - Success: a separate roadmap amendment identifies supported workflows,
    dependencies, and acceptance criteria before implementation begins.
