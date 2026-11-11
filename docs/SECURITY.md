# Security notes

## Threat model

`trysac-receipt-parser` is a pure Python library. The public functions do not perform network or filesystem I/O. The CLI reads one text path or stdin and prints JSON.

### Defended

- Oversized input: `parse_receipt` rejects text longer than `max_chars` (default `100_000`) with `ReceiptError('input_too_large')` before parsing.
- Too many item lines: `parse_receipt` rejects more than `max_items` (default `500`) item lines with `ReceiptError('too_many_items')`.
- Numeric parsing: amounts are parsed into `Decimal` values. The grammar requires exactly two decimal digits and validates thousands groups. `parse_amount` raises `ReceiptError('invalid_amount')` instead of using binary floats.
- Error messages: `ReceiptError` messages are fixed strings and do not include receipt text.
- Untrusted text: the parser uses regular expressions, string operations, and `Decimal`; it does not call `eval`, `exec`, or deserialize untrusted data.
- Logging: the module logger has a `NullHandler` and does not emit receipt contents by default.

### Not defended

- Incorrect OCR text: the parser cannot know whether the merchant, date, or item descriptions are correct. It reports only the consistency issues listed in the code: `subtotal_mismatch`, `total_mismatch`, `missing_total`, `invalid_date`, `item_mismatch`, and `ocr_fixed`.
- Adversarial text within the limits: `max_chars` bounds total input length, but `_find_amount` tries suffixes of each line, so a single long line can still take time proportional to the square of its length.
- Authentication or authorization: the library and CLI do not authenticate users or restrict which files the CLI process can read.
- Secrets: the library does not read environment variables, credentials, or secret stores.

## Publishing

No release or publishing scripts are present in the repository. The library code does not publish itself.
