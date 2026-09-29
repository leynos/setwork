"""Illustrative custom grammar for a non-delegating GNU find subset."""

from __future__ import annotations

import dataclasses as dc
import enum


class FileType(enum.StrEnum):
    """Selected values accepted by GNU find's ``-type`` predicate."""

    BLOCK = "b"
    CHARACTER = "c"
    DIRECTORY = "d"
    REGULAR = "f"
    LINK = "l"
    FIFO = "p"
    SOCKET = "s"


class Expression:
    """Base class supporting typed Boolean expression composition."""

    precedence: int

    def tokens(self) -> tuple[str, ...]:
        """Return a canonical token sequence for this expression."""

        return self._tokens(parent_precedence=0)

    def _tokens(self, parent_precedence: int) -> tuple[str, ...]:
        raise NotImplementedError

    def __and__(self, other: Expression) -> Expression:
        return And(self, other)

    def __or__(self, other: Expression) -> Expression:
        return Or(self, other)

    def __invert__(self) -> Expression:
        return Not(self)

    def _parenthesize(
        self,
        tokens: tuple[str, ...],
        parent_precedence: int,
    ) -> tuple[str, ...]:
        if self.precedence < parent_precedence:
            return ("(", *tokens, ")")
        return tokens


@dc.dataclass(frozen=True, slots=True)
class Predicate(Expression):
    """A leaf predicate with fixed, already validated arguments."""

    name: str
    arguments: tuple[str, ...]
    precedence: int = dc.field(default=4, init=False)

    def _tokens(self, parent_precedence: int) -> tuple[str, ...]:
        del parent_precedence
        return (self.name, *self.arguments)


@dc.dataclass(frozen=True, slots=True)
class Not(Expression):
    """Boolean negation."""

    operand: Expression
    precedence: int = dc.field(default=3, init=False)

    def _tokens(self, parent_precedence: int) -> tuple[str, ...]:
        tokens = ("!", *self.operand._tokens(self.precedence))
        return self._parenthesize(tokens, parent_precedence)


@dc.dataclass(frozen=True, slots=True)
class And(Expression):
    """Explicit Boolean conjunction."""

    left: Expression
    right: Expression
    precedence: int = dc.field(default=2, init=False)

    def _tokens(self, parent_precedence: int) -> tuple[str, ...]:
        tokens = (
            *self.left._tokens(self.precedence),
            "-a",
            *self.right._tokens(self.precedence),
        )
        return self._parenthesize(tokens, parent_precedence)


@dc.dataclass(frozen=True, slots=True)
class Or(Expression):
    """Boolean disjunction."""

    left: Expression
    right: Expression
    precedence: int = dc.field(default=1, init=False)

    def _tokens(self, parent_precedence: int) -> tuple[str, ...]:
        tokens = (
            *self.left._tokens(self.precedence),
            "-o",
            *self.right._tokens(self.precedence),
        )
        return self._parenthesize(tokens, parent_precedence)


def _checked(value: str) -> str:
    if "\x00" in value:
        raise ValueError("find expression values cannot contain NUL")
    return value


def name(pattern: str) -> Expression:
    """Match a basename with ``-name``."""

    return Predicate("-name", (_checked(pattern),))


def path(pattern: str) -> Expression:
    """Match a path with ``-path``."""

    return Predicate("-path", (_checked(pattern),))


def file_type(value: FileType) -> Expression:
    """Match a filesystem object type with ``-type``."""

    return Predicate("-type", (value.value,))


__all__ = [
    "And",
    "Expression",
    "FileType",
    "Not",
    "Or",
    "Predicate",
    "file_type",
    "name",
    "path",
]
