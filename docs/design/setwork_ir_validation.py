"""Normative publication checks for the Setwork IR design sketch.

The checks belong to the design artefacts, rather than the installed package.
They share the immutable types in ``setwork_ir``; compiler implementation will
preserve the same validation boundary.
"""

from __future__ import annotations

import typing as typ

from .setwork_ir import (
    Coverage,
    Effect,
    OperandDisambiguation,
    ParameterRole,
    Sensitivity,
    SerializationKind,
    SourceAuthority,
    ValueKind,
)

if typ.TYPE_CHECKING:
    from .setwork_ir import CommandSpec, ParameterSpec, ProgramSpec, SourceRef


_FORBIDDEN_SAFE_EFFECTS = frozenset({
    Effect.SPAWNS_PROGRAM,
    Effect.INTERPRETS_SHELL,
})


def _validate_provenance(
    sources: tuple[SourceRef, ...], location: str, *, subject: str = ""
) -> None:
    """Require evidence while retaining each scope's diagnostic wording.

    For example, empty sources with subject ``program`` report
    ``missing program provenance`` at the supplied location.
    """
    label = f"{subject} provenance" if subject else "provenance"
    if not sources:
        raise ValueError(f"{location}: missing {label}")
    if all(source.authority is SourceAuthority.UNRESOLVED for source in sources):
        raise ValueError(f"{location}: unresolved {label}")


def _validate_parameter(parameter: ParameterSpec, location: str) -> None:
    """Check one parameter before it enters the generated safe surface.

    For example, a secret-valued parameter reports ``secret argv value``
    before its provenance or serialization is checked.
    """
    if parameter.effects & _FORBIDDEN_SAFE_EFFECTS:
        raise ValueError(f"{location}: forbidden effect")
    if parameter.value.kind is ValueKind.COMMAND:
        raise ValueError(f"{location}: delegated command value")
    if parameter.value.kind is ValueKind.OPAQUE:
        raise ValueError(f"{location}: opaque value type")
    if parameter.sensitivity is Sensitivity.SECRET:
        raise ValueError(f"{location}: secret argv value")
    _validate_provenance(parameter.sources, location)
    serialization = parameter.serialization
    if serialization.kind is SerializationKind.UNKNOWN:
        raise ValueError(f"{location}: unknown serialization")
    if (
        parameter.role is ParameterRole.POSITIONAL
        and serialization.disambiguation is OperandDisambiguation.UNRESOLVED
    ):
        raise ValueError(f"{location}: unresolved operand policy")


def _validate_command(command: CommandSpec, prefix: str) -> None:
    """Check command policy and then its parameters in their declared order.

    For example, an internal draft reports ``internal draft is not publishable``
    before checking evidence or parameter effects.
    """
    if command.coverage is Coverage.INTERNAL_DRAFT:
        raise ValueError(f"{prefix}: internal draft is not publishable")
    _validate_provenance(command.sources, prefix, subject="command")
    if command.effects & _FORBIDDEN_SAFE_EFFECTS:
        raise ValueError(f"{prefix}: forbidden effect")
    for parameter in command.parameters:
        _validate_parameter(parameter, f"{prefix}.{parameter.python_name}")


def validate_publishable(program: ProgramSpec) -> None:
    """Reject a program that cannot enter the default generated safe surface.

    For example, a program without sources raises ``ValueError`` with
    ``<executable>: missing program provenance``.
    """
    _validate_provenance(program.sources, program.executable, subject="program")
    for command in program.commands:
        _validate_command(command, f"{program.executable}.{command.function_name}")
