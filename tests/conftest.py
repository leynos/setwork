"""Shared fixtures for tests of the normative source-tree IR sketch."""

from __future__ import annotations

import importlib
import typing as typ
from pathlib import Path

import pytest

if typ.TYPE_CHECKING:
    import types

    from docs.design.setwork_ir import ProgramSpec


@pytest.fixture
def ir(monkeypatch: pytest.MonkeyPatch) -> types.ModuleType:
    """Import the source-tree IR without requiring it in the runtime wheel."""
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1]))
    return importlib.import_module("docs.design.setwork_ir")


@pytest.fixture
def publishable_program(ir: types.ModuleType) -> ProgramSpec:
    """Build one valid positional command to vary publication policy independently."""
    source = ir.SourceRef("fixture", "locked", "spec", ir.SourceAuthority.AUTHORITATIVE)
    parameter = ir.ParameterSpec(
        python_name="text",
        role=ir.ParameterRole.POSITIONAL,
        value=ir.ValueSpec(ir.ValueKind.STRING, "str"),
        values=ir.Cardinality(),
        occurrences=ir.Cardinality(),
        serialization=ir.SerializationSpec(
            ir.SerializationKind.POSITIONAL,
            disambiguation=ir.OperandDisambiguation.REJECT_AMBIGUOUS,
        ),
        sources=(source,),
    )
    command = ir.CommandSpec(
        "echo",
        (),
        ir.GrammarKind.FLAT,
        ir.Coverage.COMPLETE,
        (parameter,),
        sources=(source,),
    )
    return ir.ProgramSpec(
        "echo", "echo", "gnu-linux", "9", (command,), sources=(source,)
    )
