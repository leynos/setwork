"""Flag cardinality contracts for the normative IR sketch."""

from __future__ import annotations

import dataclasses as dc
import importlib
import re
import typing as typ

import pytest

if typ.TYPE_CHECKING:
    import types

    from docs.design.setwork_ir import ProgramSpec


@pytest.mark.parametrize("maximum", [1, 2, 3, None])
def test_flag_rejects_consumed_values(
    ir: types.ModuleType, maximum: int | None
) -> None:
    """A presence flag cannot consume any parameter values."""
    with pytest.raises(ValueError, match="flag parameters cannot consume values"):
        ir.ParameterSpec(
            python_name="verbose",
            role=ir.ParameterRole.OPTION,
            value=ir.ValueSpec(ir.ValueKind.FLAG, "bool"),
            values=ir.Cardinality(maximum=maximum),
            occurrences=ir.Cardinality(),
            serialization=ir.SerializationSpec(ir.SerializationKind.PRESENCE, "-v"),
            cli_names=("-v",),
        )


@pytest.mark.parametrize("maximum", [0, 1, 2, None])
def test_flag_occurrences_are_independent_of_values(
    ir: types.ModuleType, maximum: int | None
) -> None:
    """Repeatability describes flag occurrences rather than consumed values."""
    parameter = ir.ParameterSpec(
        python_name="verbose",
        role=ir.ParameterRole.OPTION,
        value=ir.ValueSpec(ir.ValueKind.FLAG, "bool"),
        values=ir.Cardinality(maximum=0),
        occurrences=ir.Cardinality(maximum=maximum),
        serialization=ir.SerializationSpec(ir.SerializationKind.PRESENCE, "-v"),
        cli_names=("-v",),
    )
    assert parameter.values.maximum == 0, "flags must consume no values"
    assert parameter.occurrences.maximum == maximum, (
        "flag repeatability must be independent of consumed values"
    )


@pytest.mark.parametrize("scope", ["program", "command", "parameter"])
@pytest.mark.parametrize("state", ["missing", "unresolved"])
def test_publication_provenance_diagnostics(
    ir: types.ModuleType, publishable_program: ProgramSpec, scope: str, state: str
) -> None:
    """Each evidence scope preserves its exact missing or unresolved diagnostic."""
    validator = importlib.import_module("docs.design.setwork_ir_validation")
    program = publishable_program
    command = program.commands[0]
    parameter = command.parameters[0]
    sources = (
        ()
        if state == "missing"
        else (dc.replace(program.sources[0], authority=ir.SourceAuthority.UNRESOLVED),)
    )
    locations = {
        "program": "echo",
        "command": "echo.echo",
        "parameter": "echo.echo.text",
    }
    subject = f"{scope} " if scope != "parameter" else ""
    if scope == "parameter":
        command = dc.replace(
            command, parameters=(dc.replace(parameter, sources=sources),)
        )
    if scope == "command":
        command = dc.replace(command, sources=sources)
    program = dc.replace(program, commands=(command,))
    if scope == "program":
        program = dc.replace(program, sources=sources)
    message = f"{locations[scope]}: {state} {subject}provenance"
    with pytest.raises(ValueError, match=f"^{re.escape(message)}$") as error:
        validator.validate_publishable(program)
    assert str(error.value) == message, "publication diagnostic wording changed"


@pytest.mark.parametrize(
    ("condition", "message"),
    [
        ("draft", "echo.echo: internal draft is not publishable"),
        ("command_effect", "echo.echo: forbidden effect"),
        ("parameter_effect", "echo.echo.text: forbidden effect"),
        ("command_value", "echo.echo.text: delegated command value"),
        ("opaque", "echo.echo.text: opaque value type"),
        ("secret", "echo.echo.text: secret argv value"),
        ("serialization", "echo.echo.text: unknown serialization"),
        ("operand_policy", "echo.echo.text: unresolved operand policy"),
    ],
)
def test_publication_policy_diagnostics(
    ir: types.ModuleType, publishable_program: ProgramSpec, condition: str, message: str
) -> None:
    """Publication failures preserve the exact scope and reason."""
    validator = importlib.import_module("docs.design.setwork_ir_validation")
    command = publishable_program.commands[0]
    parameter = command.parameters[0]
    changes = {
        "draft": {"coverage": ir.Coverage.INTERNAL_DRAFT},
        "command_effect": {"effects": frozenset({ir.Effect.SPAWNS_PROGRAM})},
    }
    parameter_changes = {
        "parameter_effect": {"effects": frozenset({ir.Effect.INTERPRETS_SHELL})},
        "command_value": {"value": ir.ValueSpec(ir.ValueKind.COMMAND, "str")},
        "opaque": {"value": ir.ValueSpec(ir.ValueKind.OPAQUE, "str")},
        "secret": {"sensitivity": ir.Sensitivity.SECRET},
        "serialization": {
            "serialization": dc.replace(
                parameter.serialization,
                kind=ir.SerializationKind.UNKNOWN,
            )
        },
        "operand_policy": {
            "serialization": dc.replace(
                parameter.serialization,
                disambiguation=ir.OperandDisambiguation.UNRESOLVED,
            )
        },
    }
    parameter = dc.replace(parameter, **parameter_changes.get(condition, {}))
    command = dc.replace(command, parameters=(parameter,), **changes.get(condition, {}))
    program = dc.replace(publishable_program, commands=(command,))
    with pytest.raises(ValueError, match=f"^{re.escape(message)}$") as error:
        validator.validate_publishable(program)
    assert str(error.value) == message, "publication diagnostic wording changed"


def test_publication_accepts_resolved_evidence_among_unresolved(
    ir: types.ModuleType, publishable_program: ProgramSpec
) -> None:
    """Unresolved evidence does not block publication when resolved evidence exists."""
    validator = importlib.import_module("docs.design.setwork_ir_validation")
    source = publishable_program.sources[0]
    sources = (dc.replace(source, authority=ir.SourceAuthority.UNRESOLVED), source)
    program = dc.replace(publishable_program, sources=sources)
    validator.validate_publishable(program)


def test_publication_preserves_failure_precedence(
    ir: types.ModuleType, publishable_program: ProgramSpec
) -> None:
    """A forbidden parameter effect still precedes sensitivity and missing evidence."""
    validator = importlib.import_module("docs.design.setwork_ir_validation")
    command = publishable_program.commands[0]
    parameter = dc.replace(
        command.parameters[0],
        effects=frozenset({ir.Effect.SPAWNS_PROGRAM}),
        sensitivity=ir.Sensitivity.SECRET,
        sources=(),
    )
    command = dc.replace(command, parameters=(parameter,))
    program = dc.replace(publishable_program, commands=(command,))
    with pytest.raises(ValueError, match="forbidden effect") as error:
        validator.validate_publishable(program)
    assert str(error.value) == "echo.echo.text: forbidden effect", (
        "effect validation must precede sensitivity and provenance checks"
    )
