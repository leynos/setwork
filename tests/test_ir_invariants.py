"""Constructor contracts for the normative intermediate representation."""

from __future__ import annotations

import dataclasses as dc
import re
import typing as typ

import pytest

if typ.TYPE_CHECKING:
    import types

    from docs.design.setwork_ir import ProgramSpec


@pytest.mark.parametrize(
    ("minimum", "maximum", "message"),
    [
        (-1, 1, "minimum cardinality cannot be negative"),
        (2, 1, "maximum cardinality cannot be below minimum"),
    ],
)
def test_cardinality_rejects_invalid_bounds(
    ir: types.ModuleType, minimum: int, maximum: int, message: str
) -> None:
    """Cardinality bounds cannot describe a negative or inverted range."""
    with pytest.raises(ValueError, match=f"^{re.escape(message)}$"):
        ir.Cardinality(minimum=minimum, maximum=maximum)


@pytest.mark.parametrize(
    ("values", "message"),
    [
        ((), "enum values cannot be empty"),
        (("one", "one"), "enum values must be unique"),
    ],
)
def test_enum_rejects_invalid_choices(
    ir: types.ModuleType, values: tuple[str, ...], message: str
) -> None:
    """An enumeration must have a non-empty set of distinct choices."""
    with pytest.raises(ValueError, match=f"^{re.escape(message)}$"):
        ir.ValueSpec(ir.ValueKind.ENUM, "str", values=values)


@pytest.mark.parametrize(("minimum", "maximum"), [(1, 0), (1.5, 1.0)])
def test_numeric_value_rejects_inverted_bounds(
    ir: types.ModuleType, minimum: int | float, maximum: int | float
) -> None:
    """Numeric validation cannot impose a maximum below its minimum."""
    with pytest.raises(ValueError, match="value maximum cannot be below minimum"):
        ir.ValueSpec(ir.ValueKind.INTEGER, "int", minimum=minimum, maximum=maximum)


@pytest.mark.parametrize(
    "kind", ["PRESENCE", "SEPARATE", "EQUALS", "ATTACHED", "ASSIGNMENT", "DELIMITED"]
)
def test_option_serialization_requires_spelling(
    ir: types.ModuleType, kind: str
) -> None:
    """Every option serializer needs an exact canonical argv spelling."""
    serialization_kind = ir.SerializationKind[kind]
    with pytest.raises(ValueError, match="serialization requires a spelling"):
        ir.SerializationSpec(serialization_kind)


@pytest.mark.parametrize(
    ("kind", "message"),
    [
        ("DELIMITED", "delimited serialization requires a delimiter"),
        ("CUSTOM", "custom serialization requires a serializer name"),
    ],
)
def test_serialization_requires_its_strategy_setting(
    ir: types.ModuleType, kind: str, message: str
) -> None:
    """Strategy-specific settings must be present before publication."""
    with pytest.raises(ValueError, match=f"^{re.escape(message)}$"):
        ir.SerializationSpec(ir.SerializationKind[kind], spelling="--value")


def test_terminator_policy_requires_token(ir: types.ModuleType) -> None:
    """Operand disambiguation cannot invent an unspecified terminator."""
    with pytest.raises(ValueError, match="terminator disambiguation requires a token"):
        ir.SerializationSpec(
            ir.SerializationKind.POSITIONAL,
            disambiguation=ir.OperandDisambiguation.TERMINATOR,
        )


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"python_name": "not-valid"}, "invalid Python identifier"),
        ({"python_name": "class"}, "invalid Python identifier"),
        ({"cli_names": ("-v", "-v")}, "CLI aliases must be unique"),
        ({"cli_names": ("",)}, "CLI aliases must be non-empty and NUL-free"),
        ({"cli_names": ("a\x00b",)}, "CLI aliases must be non-empty and NUL-free"),
    ],
)
def test_parameter_rejects_invalid_names(
    publishable_program: ProgramSpec, changes: dict[str, object], message: str
) -> None:
    """Python names and CLI aliases must be valid and unambiguous."""
    parameter = publishable_program.commands[0].parameters[0]
    with pytest.raises(ValueError, match=message):
        dc.replace(parameter, **changes)


@pytest.mark.parametrize("aliases", [(), ("--other",)])
def test_option_requires_matching_alias(
    ir: types.ModuleType, publishable_program: ProgramSpec, aliases: tuple[str, ...]
) -> None:
    """An option must declare aliases including its canonical spelling."""
    parameter = publishable_program.commands[0].parameters[0]
    with pytest.raises(ValueError, match=r"CLI name|canonical spelling"):
        dc.replace(
            parameter,
            role=ir.ParameterRole.OPTION,
            cli_names=aliases,
            serialization=ir.SerializationSpec(
                ir.SerializationKind.SEPARATE, "--value"
            ),
        )


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"function_name": "class"}, "invalid function name"),
        ({"command_path": ("",)}, "command-path tokens must be non-empty and NUL-free"),
        (
            {"command_path": ("a\x00b",)},
            "command-path tokens must be non-empty and NUL-free",
        ),
        (
            {"omitted_features": ("unsupported",)},
            "complete commands cannot list omitted features",
        ),
    ],
)
def test_command_rejects_invalid_identity_or_coverage(
    publishable_program: ProgramSpec, changes: dict[str, object], message: str
) -> None:
    """Command identity and complete-coverage declarations must be coherent."""
    with pytest.raises(ValueError, match=message):
        dc.replace(publishable_program.commands[0], **changes)


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"executable": ""}, "executable must be a non-empty NUL-free string"),
        ({"executable": "a\x00b"}, "executable must be a non-empty NUL-free string"),
        ({"module_name": "class"}, "invalid module name"),
        ({"target_version": ""}, "target version policy is required"),
    ],
)
def test_program_rejects_invalid_identity(
    publishable_program: ProgramSpec, changes: dict[str, object], message: str
) -> None:
    """An executable binding requires a valid module and explicit target policy."""
    with pytest.raises(ValueError, match=message):
        dc.replace(publishable_program, **changes)
