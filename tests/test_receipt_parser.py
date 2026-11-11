"""Behavior tests for the public API of receipt_parser."""

from __future__ import annotations

import pytest

import receipt_parser


def test_normalize_trims_and_lowercases() -> None:
    assert receipt_parser.normalize("  Hello World ") == "hello world"


@pytest.mark.parametrize("value", ["", "   ", "\t\n"])
def test_normalize_rejects_blank_input(value: str) -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        receipt_parser.normalize(value)


def test_version_is_semver() -> None:
    parts = receipt_parser.__version__.split(".")
    assert len(parts) == 3
    assert all(part.isdigit() for part in parts)
