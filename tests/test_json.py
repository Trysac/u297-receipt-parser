"""Tests for to_json."""

import json
from datetime import date
from decimal import Decimal

from receipt_parser import LineItem, Receipt, to_json


def test_to_json_all_fields():
    receipt = Receipt(
        merchant="STORE",
        date=date(2023, 1, 2),
        items=[LineItem("A", 2, Decimal("3.50"), Decimal("7.00"))],
        subtotal=Decimal("9.25"),
        tax=Decimal("0.74"),
        tip=Decimal("1.00"),
        total=Decimal("10.99"),
        issues=["subtotal_mismatch"],
    )
    s = to_json(receipt)
    data = json.loads(s)
    assert data == {
        "merchant": "STORE",
        "date": "2023-01-02",
        "items": [
            {
                "description": "A",
                "quantity": 2,
                "unit_price": "3.50",
                "amount": "7.00",
            }
        ],
        "subtotal": "9.25",
        "tax": "0.74",
        "tip": "1.00",
        "total": "10.99",
        "issues": ["subtotal_mismatch"],
    }
    # keys sorted
    assert list(data.keys()) == sorted(data.keys())


def test_to_json_nulls():
    receipt = Receipt(None, None, [], None, None, None, None, [])
    s = to_json(receipt)
    data = json.loads(s)
    assert data["merchant"] is None
    assert data["date"] is None
    assert data["subtotal"] is None
    assert data["tax"] is None
    assert data["tip"] is None
    assert data["total"] is None
