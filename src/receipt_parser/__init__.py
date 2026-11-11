"""Parse receipts from OCR text with explicit rules.

This module provides a deterministic, offline parser for common receipt
layouts. It extracts merchant, date, line items, subtotal, tax, tip, and
total as ``Decimal`` values, applying OCR digit fixes and reporting
inconsistencies instead of guessing.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Literal

__all__ = [
    "LineItem",
    "Receipt",
    "ReceiptError",
    "parse_amount",
    "parse_receipt",
    "to_json",
]

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class ReceiptError(Exception):
    """Base error for receipt parsing failures."""

    def __init__(
        self,
        code: Literal["input_too_large", "too_many_items", "invalid_amount"],
    ) -> None:
        self.code = code
        super().__init__(_ERROR_MESSAGES[code])


_ERROR_MESSAGES: dict[str, str] = {
    "input_too_large": "receipt text exceeds maximum allowed characters",
    "too_many_items": "too many item lines",
    "invalid_amount": "invalid amount format",
}


@dataclass(frozen=True)
class LineItem:
    """A single purchased item with quantity and prices."""

    description: str
    quantity: int
    unit_price: Decimal
    amount: Decimal


@dataclass(frozen=True)
class Receipt:
    """A parsed receipt with all extracted fields and issues."""

    merchant: str | None
    date: date | None
    items: list[LineItem]
    subtotal: Decimal | None
    tax: Decimal | None
    tip: Decimal | None
    total: Decimal | None
    issues: list[str] = field(default_factory=list)


def parse_amount(token: str) -> Decimal:
    """Parse a single amount token into a :class:`Decimal`.

    The token must follow the grammar:
    - optional leading ``-``
    - digits with optional thousands groups of exactly three digits
      separated by ``.``, ``,``, a space or an apostrophe
    - a decimal separator (``.`` or ``,``) and exactly two digits
    - the last separator is the decimal separator.

    Args:
        token: The amount string.

    Returns:
        The parsed amount as a :class:`Decimal`.

    Raises:
        ReceiptError: with code ``'invalid_amount'`` if the token does not
            match the grammar.
    """
    token = token.strip()
    if not token:
        raise ReceiptError("invalid_amount")

    sign = 1
    if token.startswith("-"):
        sign = -1
        token = token[1:]

    if not token:
        raise ReceiptError("invalid_amount")

    # Find decimal separator: the last occurrence of '.' or ','
    decimal_idx = -1
    for i, ch in enumerate(token):
        if ch in (".", ","):
            decimal_idx = i
    if decimal_idx == -1:
        raise ReceiptError("invalid_amount")

    # Decimal part must be exactly two digits
    if len(token) - decimal_idx - 1 != 2:
        raise ReceiptError("invalid_amount")
    if not token[decimal_idx + 1 :].isdigit():
        raise ReceiptError("invalid_amount")

    integer_part = token[:decimal_idx]
    if not integer_part:
        raise ReceiptError("invalid_amount")

    # Validate integer part: digits and thousands separators
    # Allowed separators: '.', ',', ' ', "'"
    allowed_seps = {".", ",", " ", "'"}
    groups: list[str] = []
    current_group: list[str] = []
    sep_count = 0
    for ch in integer_part:
        if ch.isdigit():
            current_group.append(ch)
        elif ch in allowed_seps:
            if not current_group:
                raise ReceiptError("invalid_amount")
            groups.append("".join(current_group))
            current_group = []
            sep_count += 1
        else:
            raise ReceiptError("invalid_amount")
    if current_group:
        groups.append("".join(current_group))
    else:
        raise ReceiptError("invalid_amount")

    # If there were separators, validate group sizes
    if sep_count > 0:
        if len(groups) == 1:
            raise ReceiptError("invalid_amount")
        for group in groups[1:]:
            if len(group) != 3:
                raise ReceiptError("invalid_amount")
        if not (1 <= len(groups[0]) <= 3):
            raise ReceiptError("invalid_amount")
    else:
        # No separators: just digits, any length >= 1
        if not all(part.isdigit() for part in groups):
            # groups is a list with one element, already checked isdigit
            pass

    integer_str = "".join(groups)
    if not integer_str.isdigit():
        raise ReceiptError("invalid_amount")

    decimal_part = token[decimal_idx + 1 :]
    try:
        return sign * Decimal(f"{integer_str}.{decimal_part}")
    except InvalidOperation:
        raise ReceiptError("invalid_amount") from None


def _strip_currency_and_whitespace(s: str) -> str:
    """Remove leading whitespace and known currency symbols from *s*."""
    s = s.lstrip()
    currency_symbols = ["$", "€", "£", "¥", "S/", "s/"]
    while True:
        stripped = False
        for cs in currency_symbols:
            if s.startswith(cs):
                s = s[len(cs) :].lstrip()
                stripped = True
                break
        if not stripped:
            break
    return s


def _fix_ocr(s: str) -> str:
    """Apply OCR digit fixes to the string."""
    table = str.maketrans({"O": "0", "o": "0", "l": "1", "I": "1", "S": "5"})
    return s.translate(table)


def _find_amount(line: str) -> tuple[str, Decimal, int, bool] | None:
    """Find the trailing amount in *line*.

    Returns a tuple ``(amount_str, amount_value, start_index, ocr_fixed)``
    or ``None`` if no amount is found.
    """
    # Iterate over possible suffixes from longest to shortest
    for i in range(len(line)):
        suffix = line[i:]
        candidate = _strip_currency_and_whitespace(suffix)
        if not candidate:
            continue
        # Try strict parse first
        try:
            value = parse_amount(candidate)
            return suffix, value, i, False
        except ReceiptError:
            pass
        # OCR fixes only if candidate has at least one digit and fixable letters
        if any(ch.isdigit() for ch in candidate) and any(ch in candidate for ch in "OolIS"):
            fixed = _fix_ocr(candidate)
            try:
                value = parse_amount(fixed)
                return suffix, value, i, True
            except ReceiptError:
                pass
    return None


def _clean_label(s: str) -> str:
    """Strip, drop a trailing colon and collapse inner spaces, preserving case."""
    s = s.strip()
    if s.endswith(":"):
        s = s[:-1]
    return " ".join(s.split())


def _normalize_label(s: str) -> str:
    """Normalize a label for keyword matching: clean and uppercase."""
    return _clean_label(s).upper()


def _extract_date(line: str, day_first: bool) -> tuple[bool, date | None, bool]:
    """Extract the first date from *line*.

    Returns ``(found, date, invalid)``.
    """
    # YYYY-MM-DD
    m = re.search(r"\b(\d{4})-(\d{2})-(\d{2})\b", line)
    if m:
        year, month, day = map(int, m.groups())
        try:
            return True, date(year, month, day), False
        except ValueError:
            return True, None, True

    # Ambiguous DD/MM/YYYY or DD-MM-YYYY (or MM/DD/YYYY when day_first=False)
    m = re.search(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b", line)
    if m:
        a, b, year = map(int, m.groups())
        if day_first:
            day, month = a, b
        else:
            month, day = a, b
        try:
            return True, date(year, month, day), False
        except ValueError:
            return True, None, True

    return False, None, False


def _parse_item_label(label: str, line_amount: Decimal) -> tuple[str, int, Decimal, bool]:
    """Parse an item label for quantity/unit price patterns.

    Returns ``(description, quantity, unit_price, mismatch)``.
    """
    pattern = re.compile(r"(\d+)\s*[xX@]\s*([0-9.,' -]+)$")
    match = pattern.search(label)
    if match:
        qty_str = match.group(1)
        unit_str = match.group(2).strip()
        try:
            unit_price = parse_amount(unit_str)
            quantity = int(qty_str)
            if line_amount != quantity * unit_price:
                return label[: match.start()].strip(), quantity, unit_price, True
            return label[: match.start()].strip(), quantity, unit_price, False
        except ReceiptError:
            pass
    return label, 1, line_amount, False


# Keyword sets (all uppercase)
_SUBTOTAL_KEYWORDS = {"SUBTOTAL", "SUB-TOTAL", "SUB TOTAL"}
_TAX_KEYWORDS = {"TAX", "VAT", "IVA", "IGV", "SALES TAX"}
_TIP_KEYWORDS = {"TIP", "PROPINA"}
_TOTAL_KEYWORDS = {"TOTAL", "TOTAL A PAGAR", "AMOUNT DUE", "IMPORTE TOTAL"}
_PAYMENT_KEYWORDS = {"CASH", "CARD", "CHANGE", "EFECTIVO", "TARJETA", "VUELTO", "CAMBIO"}


def parse_receipt(
    text: str,
    *,
    day_first: bool = True,
    max_chars: int = 100_000,
    max_items: int = 500,
) -> Receipt:
    """Parse a complete receipt from OCR text.

    Args:
        text: The OCR text of the receipt.
        day_first: If ``True`` (default), ambiguous dates are interpreted as
            DD/MM/YYYY; if ``False``, as MM/DD/YYYY.
        max_chars: Maximum allowed characters in *text*.
        max_items: Maximum allowed number of item lines.

    Returns:
        A :class:`Receipt` object.

    Raises:
        ReceiptError: with code ``'input_too_large'`` if ``len(text) >
            max_chars``, or ``'too_many_items'`` if the number of item lines
            exceeds ``max_items``.
    """
    if len(text) > max_chars:
        raise ReceiptError("input_too_large")

    lines = text.splitlines()
    merchant: str | None = None
    date_val: date | None = None
    date_processed = False
    items: list[LineItem] = []
    subtotal: Decimal | None = None
    tax: Decimal | None = None
    tip: Decimal | None = None
    total: Decimal | None = None
    ocr_fixed_flag = False
    issues_set: set[str] = set()

    for line in lines:
        line = line.rstrip("\r\n")
        line = line.rstrip()
        if not line:
            continue

        amt = _find_amount(line)
        if amt is not None:
            _, amount_val, start_idx, ocr_fixed = amt
            if ocr_fixed:
                ocr_fixed_flag = True
            label_raw = line[:start_idx]
            label_display = _clean_label(label_raw)
            label = _normalize_label(label_raw)
            if label in _SUBTOTAL_KEYWORDS:
                subtotal = amount_val
            elif label in _TAX_KEYWORDS:
                tax = amount_val
            elif label in _TIP_KEYWORDS:
                tip = amount_val
            elif label in _TOTAL_KEYWORDS:
                total = amount_val  # last total wins
            elif label in _PAYMENT_KEYWORDS:
                pass  # ignored
            else:
                if len(items) >= max_items:
                    raise ReceiptError("too_many_items")
                description, quantity, unit_price, mismatch = _parse_item_label(
                    label_display, amount_val
                )
                item = LineItem(
                    description=description,
                    quantity=quantity,
                    unit_price=unit_price,
                    amount=amount_val,
                )
                items.append(item)
                if mismatch:
                    issues_set.add("item_mismatch")
        else:
            # no amount on this line
            found, d, invalid = _extract_date(line, day_first)
            if found:
                if not date_processed:
                    date_processed = True
                    if invalid:
                        issues_set.add("invalid_date")
                    else:
                        date_val = d
                # if already processed, ignore this date for merchant
            else:
                if merchant is None and any(ch.isalpha() for ch in line):
                    merchant = line.strip()

    # Consistency checks
    final_issues: list[str] = []
    items_sum = sum((item.amount for item in items), Decimal(0))

    if subtotal is not None and subtotal != items_sum:
        final_issues.append("subtotal_mismatch")

    base = subtotal if subtotal is not None else items_sum
    tax_val = tax if tax is not None else Decimal(0)
    tip_val = tip if tip is not None else Decimal(0)
    if total is not None:
        expected = base + tax_val + tip_val
        if expected != total:
            final_issues.append("total_mismatch")
    else:
        final_issues.append("missing_total")

    if "invalid_date" in issues_set:
        final_issues.append("invalid_date")
    if "item_mismatch" in issues_set:
        final_issues.append("item_mismatch")
    if ocr_fixed_flag:
        final_issues.append("ocr_fixed")

    return Receipt(
        merchant=merchant,
        date=date_val,
        items=items,
        subtotal=subtotal,
        tax=tax,
        tip=tip,
        total=total,
        issues=final_issues,
    )


def to_json(receipt: Receipt) -> str:
    """Serialize a :class:`Receipt` to a JSON string.

    Keys are sorted alphabetically. Amounts are represented as strings,
    the date as an ISO 8601 string or ``null``.
    """
    import json

    data = {
        "merchant": receipt.merchant,
        "date": receipt.date.isoformat() if receipt.date else None,
        "items": [
            {
                "description": item.description,
                "quantity": item.quantity,
                "unit_price": str(item.unit_price),
                "amount": str(item.amount),
            }
            for item in receipt.items
        ],
        "subtotal": str(receipt.subtotal) if receipt.subtotal is not None else None,
        "tax": str(receipt.tax) if receipt.tax is not None else None,
        "tip": str(receipt.tip) if receipt.tip is not None else None,
        "total": str(receipt.total) if receipt.total is not None else None,
        "issues": receipt.issues,
    }
    return json.dumps(data, sort_keys=True)
