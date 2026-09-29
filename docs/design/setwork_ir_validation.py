"""Normative publication checks for the Setwork IR design sketch.

The checks belong to the design artefacts, rather than the installed package.
They share the immutable types in ``setwork_ir``; compiler implementation will
preserve the same validation boundary.
"""

from __future__ import annotations

from .setwork_ir import (
    Coverage,
    Effect,
    OperandDisambiguation,
    ParameterRole,
    ProgramSpec,
    Sensitivity,
    SerializationKind,
    SourceAuthority,
    ValueKind,
)


_FORBIDDEN_SAFE_EFFECTS = frozenset({
    Effect.SPAWNS_PROGRAM,
    Effect.INTERPRETS_SHELL,
})


def validate_publishable(program: ProgramSpec) -> None:
    """Reject a program that cannot enter the default generated safe surface."""

    if not program.sources:
        raise ValueError(f"{program.executable}: missing program provenance")
    if all(
        source.authority is SourceAuthority.UNRESOLVED for source in program.sources
    ):
        raise ValueError(f"{program.executable}: unresolved program provenance")
    for command in program.commands:
        prefix = f"{program.executable}.{command.function_name}"
        if command.coverage is Coverage.INTERNAL_DRAFT:
            raise ValueError(f"{prefix}: internal draft is not publishable")
        if not command.sources:
            raise ValueError(f"{prefix}: missing command provenance")
        if all(
            source.authority is SourceAuthority.UNRESOLVED for source in command.sources
        ):
            raise ValueError(f"{prefix}: unresolved command provenance")
        if command.effects & _FORBIDDEN_SAFE_EFFECTS:
            raise ValueError(f"{prefix}: forbidden effect")
        for parameter in command.parameters:
            location = f"{prefix}.{parameter.python_name}"
            if parameter.effects & _FORBIDDEN_SAFE_EFFECTS:
                raise ValueError(f"{location}: forbidden effect")
            if parameter.value.kind is ValueKind.COMMAND:
                raise ValueError(f"{location}: delegated command value")
            if parameter.value.kind is ValueKind.OPAQUE:
                raise ValueError(f"{location}: opaque value type")
            if parameter.sensitivity is Sensitivity.SECRET:
                raise ValueError(f"{location}: secret argv value")
            if not parameter.sources:
                raise ValueError(f"{location}: missing provenance")
            if all(
                source.authority is SourceAuthority.UNRESOLVED
                for source in parameter.sources
            ):
                raise ValueError(f"{location}: unresolved provenance")
            serialization = parameter.serialization
            if serialization.kind is SerializationKind.UNKNOWN:
                raise ValueError(f"{location}: unknown serialization")
            if (
                parameter.role is ParameterRole.POSITIONAL
                and serialization.disambiguation is OperandDisambiguation.UNRESOLVED
            ):
                raise ValueError(f"{location}: unresolved operand policy")
