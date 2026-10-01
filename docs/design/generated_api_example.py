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
    """Convert a path-like operand to validated command-line text."""
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
    """Write text operands with the selected GNU ``echo`` profile.

    Parameters
    ----------
    *text : str or os.PathLike[str]
        Text operands, each resolving to ``str`` without a NUL character.
        A leading option-like operand is rejected when it could be parsed as
        an option. A sole ``--help`` or ``--version`` operand is also rejected
        when all output flags use their defaults; either string is literal text
        when accompanied by another operand or when any output flag is set.
    n : bool, default=False
        Suppress the trailing newline.
    enable_escapes : bool, default=False
        Enable escape interpretation.
    disable_escapes : bool, default=False
        Disable escape interpretation.

    Returns
    -------
    SafeCmd
        A safe command for the selected ``echo`` profile.

    Raises
    ------
    TypeError
        If an operand resolves to bytes.
    ValueError
        If both escape flags are enabled, an operand contains a NUL
        character, or the first operand is ambiguous with an option.

    Examples
    --------
    ``echo("hello", n=True)`` builds an ``echo`` command that prints
    ``hello`` without a trailing newline.
    """

    if enable_escapes and disable_escapes:
        raise ValueError("enable_escapes and disable_escapes conflict")

    operands = tuple(_stringify(value, role="echo operand") for value in text)
    has_output_flag = any((n, enable_escapes, disable_escapes))
    is_information_request = len(operands) == 1 and operands[0] in {
        "--help",
        "--version",
    }
    is_ambiguous_information_request = is_information_request and not has_output_flag
    has_option_operand = bool(operands) and _looks_like_echo_option(operands[0])
    if has_option_operand or is_ambiguous_information_request:
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
    """A reviewed GNU ``dd`` block-size expression.

    Parameters
    ----------
    expression : str
        Non-empty block-size expression without NUL characters.

    Raises
    ------
    ValueError
        If ``expression`` is empty or contains a NUL character.

    Examples
    --------
    ``BlockSize("4M").expression`` is ``"4M"``.
    """

    expression: str
    """Non-empty GNU ``dd`` block-size expression without NUL characters."""

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
    """Convert and copy data using GNU ``dd`` assignment operands.

    Parameters
    ----------
    input_path : str or os.PathLike[str], optional
        Input path, resolving to text without a NUL character.
    output_path : str or os.PathLike[str], optional
        Output path, resolving to text without a NUL character.
    block_size : BlockSize, optional
        Validated block-size expression for the ``bs=`` operand.
    count : int, optional
        Non-negative record count for the ``count=`` operand.
    conversions : tuple of Conversion, default=()
        Conversion flags for the ``conv=`` operand.

    Returns
    -------
    SafeCmd
        A safe command for GNU ``dd``.

    Raises
    ------
    TypeError
        If a path resolves to bytes.
    ValueError
        If a path contains a NUL character or ``count`` is negative.

    Examples
    --------
    ``dd(input_path="in.bin", output_path="out.bin", count=2)`` builds a
    ``dd`` command with input, output, and count assignment operands.
    """

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
