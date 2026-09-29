"""Normative sketch of Setwork's command intermediate representation.

This design artefact fixes the information and invariants that the compiler
must preserve. It is source-neutral and independent of Cuprum's runtime types.
"""

from __future__ import annotations

import dataclasses as dc
import enum
import keyword


class SourceAuthority(enum.IntEnum):
    """How strongly the compiler may rely on one source fact."""

    UNRESOLVED = 0
    INFERRED = 10
    COMPLETION_SPEC = 20
    PROFILE_OVERLAY = 30
    CUSTOM_GRAMMAR = 40
    AUTHORITATIVE = 50


class GrammarKind(enum.StrEnum):
    """Top-level grammar family used to select a serializer strategy."""

    FLAT = "flat"
    SUBCOMMAND_TREE = "subcommand-tree"
    MODE = "mode"
    EXPRESSION = "expression"
    CUSTOM = "custom"


class Coverage(enum.StrEnum):
    """Completeness claim made by a generated public surface."""

    COMPLETE = "complete"
    DECLARED_SUBSET = "declared-subset"
    INTERNAL_DRAFT = "internal-draft"


class ParameterRole(enum.StrEnum):
    """Syntactic role occupied by a generated Python parameter."""

    OPTION = "option"
    POSITIONAL = "positional"
    EXPRESSION = "expression"
    REMAINDER = "remainder"


class ValueKind(enum.StrEnum):
    """Semantic value shape visible at the generated Python boundary."""

    FLAG = "flag"
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    PATH = "path"
    ENUM = "enum"
    COMMAND = "command"
    EXPRESSION = "expression"
    OPAQUE = "opaque"


class SerializationKind(enum.StrEnum):
    """Canonical mapping from a selected parameter to argv tokens."""

    UNKNOWN = "unknown"
    PRESENCE = "presence"
    SEPARATE = "separate"
    EQUALS = "equals"
    ATTACHED = "attached"
    ASSIGNMENT = "assignment"
    DELIMITED = "delimited"
    POSITIONAL = "positional"
    CUSTOM = "custom"


class OperandDisambiguation(enum.StrEnum):
    """Policy for operands whose first character is a hyphen."""

    UNRESOLVED = "unresolved"
    NOT_REQUIRED = "not-required"
    TERMINATOR = "terminator"
    NAMED_OPERAND = "named-operand"
    REJECT_AMBIGUOUS = "reject-ambiguous"
    CUSTOM = "custom"


class Effect(enum.StrEnum):
    """Capabilities relevant to generated safe-surface policy."""

    READS_FILES = "reads-files"
    WRITES_FILES = "writes-files"
    DELETES_FILES = "deletes-files"
    USES_NETWORK = "uses-network"
    CHANGES_PRIVILEGE = "changes-privilege"
    SPAWNS_PROGRAM = "spawns-program"
    INTERPRETS_SHELL = "interprets-shell"


class Sensitivity(enum.StrEnum):
    """Risk of exposing a parameter value through argv or observation."""

    PUBLIC = "public"
    CONFIDENTIAL = "confidential"
    SECRET = "secret"


@dc.dataclass(frozen=True, slots=True)
class SourceRef:
    """Provenance for one imported or curated fact."""

    source: str
    revision: str
    location: str
    authority: SourceAuthority
    note: str | None = None

    def __post_init__(self) -> None:
        fields = (self.source, self.revision, self.location)
        if any(not value or "\x00" in value for value in fields):
            raise ValueError("source references must be non-empty and NUL-free")


@dc.dataclass(frozen=True, slots=True)
class Cardinality:
    """Minimum and maximum number of values or occurrences."""

    minimum: int = 0
    maximum: int | None = 1

    def __post_init__(self) -> None:
        if self.minimum < 0:
            raise ValueError("minimum cardinality cannot be negative")
        if self.maximum is not None and self.maximum < self.minimum:
            raise ValueError("maximum cardinality cannot be below minimum")


@dc.dataclass(frozen=True, slots=True)
class ValueSpec:
    """Type and validation information for one parameter value."""

    kind: ValueKind
    python_type: str
    values: tuple[str, ...] = ()
    pattern: str | None = None
    minimum: int | float | None = None
    maximum: int | float | None = None
    accepts_pathlike: bool = False
    source: SourceRef | None = None

    def __post_init__(self) -> None:
        if self.kind is ValueKind.ENUM and not self.values:
            raise ValueError("enum values cannot be empty")
        if self.values and len(set(self.values)) != len(self.values):
            raise ValueError("enum values must be unique")
        if self.minimum is not None and self.maximum is not None:
            if self.maximum < self.minimum:
                raise ValueError("value maximum cannot be below minimum")


@dc.dataclass(frozen=True, slots=True)
class SerializationSpec:
    """Exact canonical argv spelling for one parameter."""

    kind: SerializationKind
    spelling: str | None = None
    delimiter: str | None = None
    disambiguation: OperandDisambiguation = OperandDisambiguation.UNRESOLVED
    terminator: str | None = None
    custom_serializer: str | None = None
    accepts_bare: bool = False

    def __post_init__(self) -> None:
        needs_spelling = {
            SerializationKind.PRESENCE,
            SerializationKind.SEPARATE,
            SerializationKind.EQUALS,
            SerializationKind.ATTACHED,
            SerializationKind.ASSIGNMENT,
            SerializationKind.DELIMITED,
        }
        if self.kind in needs_spelling and not self.spelling:
            raise ValueError(f"{self.kind} serialization requires a spelling")
        if self.kind is SerializationKind.DELIMITED and not self.delimiter:
            raise ValueError("delimited serialization requires a delimiter")
        if self.kind is SerializationKind.CUSTOM and not self.custom_serializer:
            raise ValueError("custom serialization requires a serializer name")
        if (
            self.disambiguation is OperandDisambiguation.TERMINATOR
            and not self.terminator
        ):
            raise ValueError("terminator disambiguation requires a token")


@dc.dataclass(frozen=True, slots=True)
class ConstraintSpec:
    """Cross-parameter relations enforced by types or generated validation."""

    mutually_exclusive_with: frozenset[str] = frozenset()
    requires: frozenset[str] = frozenset()
    required_by: frozenset[str] = frozenset()


@dc.dataclass(frozen=True, slots=True)
class ParameterSpec:
    """One public Python parameter and its command-language meaning."""

    python_name: str
    role: ParameterRole
    value: ValueSpec
    values: Cardinality
    occurrences: Cardinality
    serialization: SerializationSpec
    cli_names: tuple[str, ...] = ()
    keyword_only: bool = True
    order: int = 0
    constraints: ConstraintSpec = ConstraintSpec()
    effects: frozenset[Effect] = frozenset()
    sensitivity: Sensitivity = Sensitivity.PUBLIC
    sources: tuple[SourceRef, ...] = ()

    def __post_init__(self) -> None:
        if not self.python_name.isidentifier() or keyword.iskeyword(self.python_name):
            raise ValueError(f"invalid Python identifier: {self.python_name!r}")
        if self.role is ParameterRole.OPTION and not self.cli_names:
            raise ValueError("option parameters require at least one CLI name")
        if len(set(self.cli_names)) != len(self.cli_names):
            raise ValueError("CLI aliases must be unique")
        if any(not name or "\x00" in name for name in self.cli_names):
            raise ValueError("CLI aliases must be non-empty and NUL-free")
        spelling = self.serialization.spelling
        if self.role is ParameterRole.OPTION and spelling is not None:
            if spelling not in self.cli_names:
                raise ValueError("canonical spelling must be one of the aliases")
        if self.value.kind is ValueKind.FLAG and self.values.maximum != 0:
            raise ValueError("flag parameters cannot consume values")


@dc.dataclass(frozen=True, slots=True)
class CommandSpec:
    """One generated callable returning a Cuprum SafeCmd."""

    function_name: str
    command_path: tuple[str, ...]
    grammar: GrammarKind
    coverage: Coverage
    parameters: tuple[ParameterSpec, ...]
    omitted_features: tuple[str, ...] = ()
    effects: frozenset[Effect] = frozenset()
    custom_grammar: str | None = None
    sources: tuple[SourceRef, ...] = ()

    def __post_init__(self) -> None:
        if not self.function_name.isidentifier() or keyword.iskeyword(
            self.function_name
        ):
            raise ValueError(f"invalid function name: {self.function_name!r}")
        if any(not token or "\x00" in token for token in self.command_path):
            raise ValueError("command-path tokens must be non-empty and NUL-free")
        names = [parameter.python_name for parameter in self.parameters]
        if len(set(names)) != len(names):
            raise ValueError("parameter Python names must be unique")
        if self.grammar in {GrammarKind.EXPRESSION, GrammarKind.CUSTOM}:
            if not self.custom_grammar:
                raise ValueError("custom grammars require an implementation")
        if self.coverage is Coverage.DECLARED_SUBSET:
            if not self.omitted_features:
                raise ValueError("declared subsets require omission records")
        if self.coverage is Coverage.COMPLETE and self.omitted_features:
            raise ValueError("complete commands cannot list omitted features")
        self._validate_positionals()
        self._validate_constraints(names)

    def _validate_positionals(self) -> None:
        positionals = [
            parameter
            for parameter in self.parameters
            if parameter.role is ParameterRole.POSITIONAL
        ]
        optional_seen = False
        variadic_seen = False
        for index, parameter in enumerate(positionals):
            optional = parameter.values.minimum == 0
            if optional_seen and not optional:
                raise ValueError("required positional follows optional positional")
            optional_seen = optional_seen or optional
            variadic = parameter.values.maximum is None
            if variadic_seen:
                raise ValueError("more than one variadic positional parameter")
            if variadic and index != len(positionals) - 1:
                raise ValueError("variadic positional parameter must be last")
            variadic_seen = variadic_seen or variadic

    def _validate_constraints(self, names: list[str]) -> None:
        known = set(names)
        for parameter in self.parameters:
            related = (
                parameter.constraints.mutually_exclusive_with
                | parameter.constraints.requires
                | parameter.constraints.required_by
            )
            if not related <= known:
                raise ValueError("constraint refers to an unknown parameter")


@dc.dataclass(frozen=True, slots=True)
class ProgramSpec:
    """Generated callables for one executable and target profile."""

    executable: str
    module_name: str
    profile: str
    target_version: str
    commands: tuple[CommandSpec, ...]
    documentation: tuple[str, ...] = ()
    noise_rules: tuple[str, ...] = ()
    sources: tuple[SourceRef, ...] = ()

    def __post_init__(self) -> None:
        if not self.executable or "\x00" in self.executable:
            raise ValueError("executable must be a non-empty NUL-free string")
        if not self.module_name.isidentifier() or keyword.iskeyword(self.module_name):
            raise ValueError(f"invalid module name: {self.module_name!r}")
        if not self.target_version:
            raise ValueError("target version policy is required")
        names = [command.function_name for command in self.commands]
        if len(set(names)) != len(names):
            raise ValueError("function names must be unique within a module")


@dc.dataclass(frozen=True, slots=True)
class CompilationUnit:
    """Complete, reproducible input to one code-generation run."""

    schema_version: int
    compiler_version: str
    package: str
    profile: str
    programs: tuple[ProgramSpec, ...]
    source_revisions: tuple[SourceRef, ...]
    overlay_digests: tuple[str, ...]
    source_lock_digest: str

    def __post_init__(self) -> None:
        if self.schema_version < 1:
            raise ValueError("schema version must be positive")
        if not self.package or not self.source_lock_digest:
            raise ValueError("package and source-lock digest are required")
        if not self.source_revisions:
            raise ValueError("at least one locked source revision is required")
        keys = {(program.executable, program.profile) for program in self.programs}
        if len(keys) != len(self.programs):
            raise ValueError("program and profile pairs must be unique")
        if any(program.profile != self.profile for program in self.programs):
            raise ValueError("program profile differs from compilation profile")
