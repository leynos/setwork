# Setwork context

**Status:** Draft v0.1

**Last substantive revision:** 18 July 2026

**Audience:** Setwork contributors, Cuprum contributors, and reviewers

This document defines Setwork's ubiquitous language. Terms in backticks name
public or source-level identifiers. The terms of reference and technical design
use these definitions normatively.

## Terms

### Argument vector

An ordered sequence of strings passed directly to an executable without a
shell. Python and Cuprum commonly call this sequence `argv`. The executable
name may appear separately or as element zero, depending on the API.

### Canonical serialization

The one argument-vector representation that Setwork emits for a semantic
command, even when the target executable accepts several equivalent forms. For
example, a serializer may always emit `--file archive.tar` and never emit an
old-style `tar` option cluster.

### Command family

A program whose first operands select a subcommand, such as `git clone` and
`git status`. Setwork normally maps a command family to a Python module with
one generated function per runnable leaf command.

### Command specification

A normalized description of a program, command path, parameters, constraints,
value types, target dialect, and serialization rules. A command specification
is the compiler's semantic input after source adapters and overlays run.

### Completion corpus

A versioned collection of completion specifications. A completion corpus is a
source of evidence about command structure, not an authoritative execution
contract.

### Completion specification

Metadata used by an interactive shell or terminal tool to suggest subcommands,
options, and arguments. Completion specifications optimize human input and may
omit serialization details required by a command builder.

### Custom grammar

A command-specific model used when a flat collection of options and operands
cannot represent the command language. GNU `find` expressions are the primary
example: predicates, operators, parentheses, precedence, and actions form an
embedded language.

### Delegated execution

A command feature that causes one program to execute another program encoded in
its arguments. Examples include `find -exec`, `sh -c`, and command-valued
options. Delegated execution creates a transitive authorization requirement
that a flat executable allowlist cannot express by itself.

### Evidence level

The confidence and authority attached to an intermediate-representation field.
Setwork distinguishes authoritative declarations, curated overrides, imported
metadata, conservative inference, and unresolved values.

### Generated command function

An ordinary, statically typed Python function that serializes its arguments and
returns a Cuprum `SafeCmd`. It is not a dynamic proxy and does not inspect
`PATH` to discover commands.

### Overlay

Curated metadata that corrects, completes, or narrows imported source data.
Overlays record command dialect, value type, canonical spelling, serialization
form, exclusions, dependencies, and safety policy that a completion source
cannot establish.

### Publishable command

A command specification whose target profile, parameter types, serialization
rules, provenance, and safety constraints are sufficiently resolved for code
generation. Setwork may retain incomplete commands in its intermediate
representation but must not expose them in a generated public package.

### Serializer

Code that transforms typed Python values into an exact argument vector. A
serializer does not execute the command and does not quote values for a shell.

### Sensitive value

A command value whose disclosure could harm the user or system, including a
password, access token, private key, or equivalent credential. A Python type
annotation does not make process arguments confidential. Setwork records
sensitivity separately from value type and excludes secret-bearing `argv`
parameters from the default publishable surface.

### Safe surface

The generated API subset that passes Setwork's default publication policy. The
safe surface excludes unresolved serialization, delegated execution, shell
interpretation, and secret-bearing argument-vector values.

### Sensitivity classification

A field-level classification of whether a value is public, confidential, or
secret when it appears in an argument vector, generated source, provenance, or
observation. Static typing does not make a secret safe to place in `argv`.

### Source lock

A machine-readable record of each source repository, immutable revision,
selected files, checksums, adapter version, licence evidence, and overlay set
used to generate an output package.

### Target profile

A named, versioned command environment, such as GNU userland on Linux or BSD
userland on macOS. A target profile resolves dialect and version differences;
Setwork does not silently infer one from the build host or runtime host.

### Transitive program set

The complete set of executables that a prepared command may cause the operating
system to execute, including delegated commands. Cuprum currently authorizes a
`SafeCmd` by its direct `Program`; Setwork treats transitive authorization as
an explicit unresolved design boundary.

## External terms

### `Program`

Cuprum's nominal identifier for an executable.

### `SafeCmd`

Cuprum's immutable prepared-command value. A generated Setwork function returns
this type so commands retain Cuprum's execution, context, observability, and
pipeline semantics.

### `Pipeline`

Cuprum's ordered composition of two or more `SafeCmd` values, constructed with
the `|` operator.
