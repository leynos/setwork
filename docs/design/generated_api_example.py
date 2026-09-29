"""Illustrative generated API surface for Setwork.

The compiler would generate source of this shape. It is ordinary Python so
static checkers, ``functools.partial``, documentation tools, and IDEs see the
real signatures without a plugin.
"""

from __future__ import annotations

import dataclasses as dc
import enum
import os

from cuprum import Program, ProgramCatalogue, ProjectSettings, SafeCmd, sh

ECHO = Program("echo")
DD = Program("dd")
_PROJECT = ProjectSettings(
    name="setwork-generated",
    programs=(ECHO, DD),
    documentation_locations=("docs/generated-commands.md",),
    noise_rules=(),
)
CATALOGUE = ProgramCatalogue(projects=(_PROJECT,))
_BUILD_ECHO = sh.make(ECHO, catalogue=CATALOGUE)
_BUILD_DD = sh.make(DD, catalogue=CATALOGUE)

type TextOperand = str | os.PathLike[str]
type FileOperand = str | os.PathLike[str]


def _stringify(value: str | os.PathLike[str], *, role: str) -> str:
    token = os.fspath(value)
    if isinstance(token, bytes):
        raise TypeError(f"{role} must resolve to str, not bytes")
    if "\x00" in token:
        raise ValueError(f"{role} cannot contain a NUL character")
    return token


def _looks_like_echo_option(value: str) -> bool:
    """Return whether the selected echo profile may parse text as an option."""

    return (
        len(value) > 1
        and value.startswith("-")
        and set(value[1:])
        <= {
            "n",
            "e",
            "E",
        }
    )


def echo(
    *text: TextOperand,
    n: bool = False,
    enable_escapes: bool = False,
    disable_escapes: bool = False,
) -> SafeCmd:
    """Write operands with the selected GNU ``echo`` profile."""

    if enable_escapes and disable_escapes:
        raise ValueError("enable_escapes and disable_escapes conflict")

    operands = tuple(_stringify(value, role="echo operand") for value in text)
    if operands and _looks_like_echo_option(operands[0]):
        msg = (
            f"ambiguous first echo operand {operands[0]!r}; the selected profile "
            "has no verified option terminator for this position"
        )
        raise ValueError(msg)

    argv: list[str] = []
    if n:
        argv.append("-n")
    if enable_escapes:
        argv.append("-e")
    if disable_escapes:
        argv.append("-E")
    argv.extend(operands)
    return _BUILD_ECHO(*argv)


@enum.unique
class Conversion(enum.StrEnum):
    """Selected GNU ``dd`` conversion values for the design example."""

    NOERROR = "noerror"
    NOTRUNC = "notrunc"
    SPARSE = "sparse"
    SYNC = "sync"


@dc.dataclass(frozen=True, slots=True)
class BlockSize:
    """A reviewed GNU ``dd`` block-size expression."""

    expression: str

    def __post_init__(self) -> None:
        if not self.expression:
            raise ValueError("block-size expression cannot be empty")
        if "\x00" in self.expression:
            raise ValueError("block-size expression cannot contain NUL")

    def __str__(self) -> str:
        return self.expression


def dd(
    *,
    input_path: FileOperand | None = None,
    output_path: FileOperand | None = None,
    block_size: BlockSize | None = None,
    count: int | None = None,
    conversions: tuple[Conversion, ...] = (),
) -> SafeCmd:
    """Convert and copy data using GNU ``dd`` assignment operands."""

    if count is not None and count < 0:
        raise ValueError("count must be non-negative")

    argv: list[str] = []
    if input_path is not None:
        value = _stringify(input_path, role="dd input path")
        argv.append(f"if={value}")
    if output_path is not None:
        value = _stringify(output_path, role="dd output path")
        argv.append(f"of={value}")
    if block_size is not None:
        argv.append(f"bs={block_size}")
    if count is not None:
        argv.append(f"count={count}")
    if conversions:
        argv.append("conv=" + ",".join(value.value for value in conversions))
    return _BUILD_DD(*argv)


__all__ = [
    "BlockSize",
    "CATALOGUE",
    "Conversion",
    "DD",
    "ECHO",
    "dd",
    "echo",
]
