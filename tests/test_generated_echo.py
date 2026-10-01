"""Regression contracts for the illustrative echo serializer."""

from __future__ import annotations

import sys
import types
from importlib import util
from pathlib import Path
from unittest import mock

import pytest


@pytest.fixture
def generated_api(monkeypatch: pytest.MonkeyPatch) -> types.ModuleType:
    """Load the design example with Cuprum construction isolated from execution."""
    cuprum = types.ModuleType("cuprum")
    for name in ("Program", "ProgramCatalogue", "ProjectSettings", "SafeCmd", "sh"):
        setattr(cuprum, name, mock.MagicMock())
    monkeypatch.setitem(sys.modules, "cuprum", cuprum)
    module_name = "_setwork_generated_api_example"
    path = Path(__file__).resolve().parents[1] / "docs/design/generated_api_example.py"
    spec = util.spec_from_file_location(module_name, path)
    assert spec is not None, "the generated API example must have an import spec"
    assert spec.loader is not None, "the generated API example must have a loader"
    module = util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, module_name, module)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("operand", ["--help", "--version"])
def test_echo_rejects_sole_information_operand(
    generated_api: types.ModuleType, operand: str
) -> None:
    """An information request must not masquerade as printed text."""
    with pytest.raises(ValueError, match="ambiguous first echo operand"):
        generated_api.echo(operand)
    generated_api._BUILD_ECHO.assert_not_called()


@pytest.mark.parametrize("operand", ["--help", "--version"])
@pytest.mark.parametrize("flag", ["n", "enable_escapes", "disable_escapes"])
def test_echo_keeps_information_operand_with_selected_flag(
    generated_api: types.ModuleType, operand: str, flag: str
) -> None:
    """Selected output flags make GNU echo treat information options literally."""
    generated_api.echo(operand, **{flag: True})
    assert generated_api._BUILD_ECHO.call_args.args[-1] == operand, (
        "an output flag must preserve the information operand as literal text"
    )


@pytest.mark.parametrize("operand", ["--help", "--version"])
def test_echo_keeps_information_operand_with_more_text(
    generated_api: types.ModuleType, operand: str
) -> None:
    """More than one operand makes an information option literal text."""
    generated_api.echo(operand, "literal")
    assert generated_api._BUILD_ECHO.call_args.args == (operand, "literal"), (
        "additional text must preserve both literal operands"
    )


@pytest.mark.parametrize("operand", ["-n", "-e", "-E", "-neE"])
def test_echo_preserves_existing_option_operand_rejection(
    generated_api: types.ModuleType, operand: str
) -> None:
    """Option-shaped first operands remain rejected with or without flags."""
    with pytest.raises(ValueError, match="ambiguous first echo operand"):
        generated_api.echo(operand, "literal", n=True)


@pytest.mark.parametrize("operand", ["--help", "--version"])
def test_echo_false_flags_do_not_disambiguate_information_operand(
    generated_api: types.ModuleType, operand: str
) -> None:
    """Explicit False emits no flag and cannot disambiguate an information request."""
    with pytest.raises(ValueError, match="ambiguous first echo operand"):
        generated_api.echo(operand, n=False)
