# trysac-receipt-parser

Parse receipts from OCR text with explicit rules and no model. The library extracts merchant, date, line items with quantities, subtotal, tax, tip, and total as `Decimal` values, applies a small set of OCR digit fixes, and reports inconsistencies instead of guessing.

## Installation

```bash
pip install trysac-receipt-parser
```

The package has no runtime dependencies outside the Python standard library.

## Problem

OCR text from photographed receipts is noisy, mixes decimal conventions, and includes payment lines such as `CASH` and `CHANGE` next to the real total. Sending every receipt to a language model is slow, costly, and not reproducible. This library parses common receipt layouts with explicit rules, normalises amounts exactly, and reports when the numbers do not add up.

## Usage

```python
from receipt_parser import parse_receipt, to_json

text = "CAFE LUNA\n2026-11-08 12:31\nEspresso 2 x 3.50 7.00\nCroissant 2.25\nSUBTOTAL 9.25\nTAX 0.74\nTOTAL 9.99\nCASH 20.00\nCHANGE 10.01\n"
receipt = parse_receipt(text)
assert receipt.merchant == "CAFE LUNA"
assert str(receipt.total) == "9.99"
print(to_json(receipt))
```

## Public API

- `parse_receipt(text: str, *, day_first: bool = True, max_chars: int = 100_000, max_items: int = 500) -> Receipt` parses a complete receipt. `day_first=True` reads ambiguous dates as `DD/MM/YYYY`; `False` reads them as `MM/DD/YYYY`. `max_chars` and `max_items` raise `ReceiptError` when exceeded.
- `parse_amount(token: str) -> Decimal` parses one amount token. The token may start with `-`, may use `.`, `,`, a space, or an apostrophe as thousands separators in groups of exactly three digits, and must end with `.` or `,` followed by exactly two digits. The last separator is the decimal separator.
- `LineItem(description: str, quantity: int, unit_price: Decimal, amount: Decimal)` is a frozen dataclass.
- `Receipt(merchant: str | None, date: date | None, items: list[LineItem], subtotal: Decimal | None, tax: Decimal | None, tip: Decimal | None, total: Decimal | None, issues: list[str])` is a frozen dataclass.
- `to_json(receipt: Receipt) -> str` returns JSON with sorted keys. Amounts are strings and the date is an ISO 8601 string or `null`.

`ReceiptError` has a `code` attribute:

- `input_too_large`: `receipt text exceeds maximum allowed characters`
- `too_many_items`: `too many item lines`
- `invalid_amount`: `invalid amount format`

Keyword labels are matched exactly after stripping, uppercasing, removing a trailing colon, and collapsing inner spaces. `SUBTOTAL`, `SUB-TOTAL`, and `SUB TOTAL` set the subtotal; `TAX`, `VAT`, `IVA`, `IGV`, and `SALES TAX` set tax; `TIP` and `PROPINA` set tip; `TOTAL`, `TOTAL A PAGAR`, `AMOUNT DUE`, and `IMPORTE TOTAL` set total; `CASH`, `CARD`, `CHANGE`, `EFECTIVO`, `TARJETA`, `VUELTO`, and `CAMBIO` are ignored. Other lines with a trailing amount are items. An item label ending in `<int> x <amount>` or `<int> @ <amount>` sets quantity and unit price; if the amount does not equal quantity times unit price, the issue `item_mismatch` is reported.

## CLI

```bash
python -m receipt_parser receipt.txt --strict
```

The path can be `-` to read from stdin. `--month-first` interprets ambiguous dates as `MM/DD/YYYY`. `--strict` exits with code 1 when the receipt has any issues. Exit codes: 0 success, 1 issues with `--strict`, 2 usage or I/O errors.

## Why not a language model

A language model can extract fields from arbitrary receipt layouts, but it requires a model call per receipt, can change output between runs, and may invent a total instead of reporting a mismatch. This parser is free, offline, deterministic, and explicit about inconsistencies.

## Testing

```bash
uv run pytest
```

## Security

See [docs/SECURITY.md](docs/SECURITY.md).
