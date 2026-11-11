"""Tests for parse_receipt and dataclasses."""

from datetime import date
from decimal import Decimal

import pytest

from receipt_parser import LineItem, ReceiptError, parse_receipt


class TestParseReceipt:
    def test_full_example(self):
        text = (
            "CAFE LUNA\n"
            "2026-11-08 12:31\n"
            "Espresso 2 x 3.50 7.00\n"
            "Croissant 2.25\n"
            "SUBTOTAL 9.25\n"
            "TAX 0.74\n"
            "TOTAL 9.99\n"
            "CASH 20.00\n"
            "CHANGE 10.01\n"
        )
        receipt = parse_receipt(text)
        assert receipt.merchant == "CAFE LUNA"
        assert receipt.date == date(2026, 11, 8)
        assert len(receipt.items) == 2
        assert receipt.items[0] == LineItem("Espresso", 2, Decimal("3.50"), Decimal("7.00"))
        assert receipt.items[1] == LineItem("Croissant", 1, Decimal("2.25"), Decimal("2.25"))
        assert receipt.subtotal == Decimal("9.25")
        assert receipt.tax == Decimal("0.74")
        assert receipt.total == Decimal("9.99")
        assert receipt.issues == []

    def test_ocr_fix(self):
        text = "TOTAL 1O.50\n"
        receipt = parse_receipt(text)
        assert receipt.total == Decimal("10.50")
        assert "ocr_fixed" in receipt.issues

    def test_ocr_fix_not_applied_when_unnecessary(self):
        text = "TOTAL 10.50\n"
        receipt = parse_receipt(text)
        assert receipt.total == Decimal("10.50")
        assert "ocr_fixed" not in receipt.issues

    def test_keyword_whole_label(self):
        text = "Total Gym Bar 3.00\n"
        receipt = parse_receipt(text)
        # "Total Gym Bar" is not a keyword, should be item
        assert len(receipt.items) == 1
        assert receipt.items[0].description == "Total Gym Bar"
        assert receipt.total is None

    def test_total_mismatch(self):
        text = "Espresso 3.00\nSUBTOTAL 3.00\nTOTAL 10.99\n"
        receipt = parse_receipt(text)
        assert receipt.issues == ["total_mismatch"]

    def test_subtotal_mismatch(self):
        text = "Item1 5.00\nItem2 4.00\nSUBTOTAL 9.25\nTOTAL 9.25\n"
        receipt = parse_receipt(text)
        assert "subtotal_mismatch" in receipt.issues
        assert "total_mismatch" not in receipt.issues

    def test_date_day_first(self):
        text = "08/11/2026\nTOTAL 1.00\n"
        receipt = parse_receipt(text)
        assert receipt.date == date(2026, 11, 8)

    def test_date_month_first(self):
        text = "08/11/2026\nTOTAL 1.00\n"
        receipt = parse_receipt(text, day_first=False)
        assert receipt.date == date(2026, 8, 11)

    def test_invalid_date(self):
        text = "31/02/2026\nTOTAL 1.00\n"
        receipt = parse_receipt(text)
        assert receipt.date is None
        assert "invalid_date" in receipt.issues

    def test_spanish_labels(self):
        text = "IGV 1.62\nTOTAL A PAGAR 10.62\nEFECTIVO 20.00\nVUELTO 9.38\n"
        receipt = parse_receipt(text)
        assert receipt.tax == Decimal("1.62")
        assert receipt.total == Decimal("10.62")
        # Payment lines are ignored, no items
        assert len(receipt.items) == 0
        # No subtotal, so total check uses items_sum=0
        # expected = 0 + tax + tip = 1.62, not equal 10.62 -> total_mismatch
        assert "total_mismatch" in receipt.issues

    def test_missing_total(self):
        text = "Item 5.00\nSUBTOTAL 5.00\n"
        receipt = parse_receipt(text)
        assert receipt.total is None
        assert receipt.issues == ["missing_total"]

    def test_input_too_large(self):
        text = "a" * 100_001
        with pytest.raises(ReceiptError) as excinfo:
            parse_receipt(text)
        assert excinfo.value.code == "input_too_large"

    def test_too_many_items(self):
        lines = [f"Item{i} 1.00" for i in range(501)]
        text = "\n".join(lines) + "\nTOTAL 501.00\n"
        with pytest.raises(ReceiptError) as excinfo:
            parse_receipt(text, max_items=500)
        assert excinfo.value.code == "too_many_items"

    def test_currency_symbols(self):
        text = "SUBTOTAL $9.99\nTOTAL $9.99\n"
        receipt = parse_receipt(text)
        assert receipt.subtotal == Decimal("9.99")
        assert receipt.total == Decimal("9.99")

        text2 = "SUBTOTAL S/ 9.99\nTOTAL S/ 9.99\n"
        receipt2 = parse_receipt(text2)
        assert receipt2.subtotal == Decimal("9.99")
        assert receipt2.total == Decimal("9.99")

    def test_space_grouped_amount(self):
        text = "TOTAL 1 234,56\n"
        receipt = parse_receipt(text)
        assert receipt.total == Decimal("1234.56")

    def test_negative_item(self):
        text = "Discount -5.00\nTOTAL -5.00\n"
        receipt = parse_receipt(text)
        assert len(receipt.items) == 1
        assert receipt.items[0].amount == Decimal("-5.00")
        # subtotal absent, items_sum = -5.00, total -5.00 -> match
        assert receipt.issues == []

    def test_crlf(self):
        text = "Item 1.00\r\nTOTAL 1.00\r\n"
        receipt = parse_receipt(text)
        assert receipt.total == Decimal("1.00")
        assert len(receipt.items) == 1

    def test_only_total(self):
        text = "TOTAL 5.00\n"
        receipt = parse_receipt(text)
        assert receipt.total == Decimal("5.00")
        assert receipt.merchant is None
        assert receipt.date is None
        assert receipt.items == []
        # No items and no subtotal means the base is zero, so this
        # total does not add up and is reported as a mismatch.
        assert receipt.issues == ["total_mismatch"]
