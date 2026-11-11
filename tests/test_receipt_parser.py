"""Behavior tests for the public API of receipt_parser."""

from __future__ import annotations

from decimal import Decimal

import pytest

import receipt_parser


def test_public_names_are_exported() -> None:
    for name in (
        "LineItem",
        "Receipt",
        "ReceiptError",
        "parse_amount",
        "parse_receipt",
        "to_json",
    ):
        assert hasattr(receipt_parser, name)


def test_parse_amount_round_trip() -> None:
    assert receipt_parser.parse_amount("12,50") == Decimal("12.50")


def test_parse_amount_rejects_bad_input() -> None:
    with pytest.raises(receipt_parser.ReceiptError) as excinfo:
        receipt_parser.parse_amount("3.5")
    assert excinfo.value.code == "invalid_amount"


def test_error_message_is_short() -> None:
    err = receipt_parser.ReceiptError("invalid_amount")
    assert err.code == "invalid_amount"
    assert len(str(err)) <= 200
