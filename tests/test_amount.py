"""Tests for parse_amount."""

from decimal import Decimal

import pytest

from receipt_parser import ReceiptError, parse_amount


class TestParseAmount:
    def test_valid_amounts(self):
        assert parse_amount("1.234,56") == Decimal("1234.56")
        assert parse_amount("1,234.56") == Decimal("1234.56")
        assert parse_amount("12,50") == Decimal("12.50")
        assert parse_amount("-3.00") == Decimal("-3.00")

    def test_invalid_amounts(self):
        with pytest.raises(ReceiptError) as excinfo:
            parse_amount("3.5")
        assert excinfo.value.code == "invalid_amount"

        with pytest.raises(ReceiptError):
            parse_amount("abc")
        with pytest.raises(ReceiptError):
            parse_amount("1.234")
        with pytest.raises(ReceiptError):
            parse_amount("1,234")
        with pytest.raises(ReceiptError):
            parse_amount("1.234,567")
        with pytest.raises(ReceiptError):
            parse_amount("1.23.45")
        with pytest.raises(ReceiptError):
            parse_amount("1,23,45")

    def test_space_as_thousands_separator(self):
        assert parse_amount("1 234,56") == Decimal("1234.56")

    def test_apostrophe_as_thousands_separator(self):
        assert parse_amount("1'234.56") == Decimal("1234.56")

    def test_currency_symbol_not_accepted(self):
        with pytest.raises(ReceiptError):
            parse_amount("$9.99")

    def test_negative_zero(self):
        assert parse_amount("-0.00") == Decimal("-0.00")

    def test_empty_and_whitespace(self):
        with pytest.raises(ReceiptError):
            parse_amount("")
        with pytest.raises(ReceiptError):
            parse_amount("   ")

    def test_leading_space_stripped(self):
        assert parse_amount("  12.50") == Decimal("12.50")

    def test_invalid_group_sizes(self):
        # the second group must have exactly three digits
        with pytest.raises(ReceiptError):
            parse_amount("12.34,56")
        with pytest.raises(ReceiptError):
            parse_amount("1,23.56")  # 23 not 3 digits
        with pytest.raises(ReceiptError):
            parse_amount("1,2345.56")  # group of 4
