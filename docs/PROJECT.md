# Project record

## Objective

Parse receipts from OCR text with explicit rules and no model. Extract merchant, date, line items with quantities, subtotal, tax, tip, and total as `Decimal` values; apply OCR digit fixes; report inconsistencies instead of guessing.

## Scope

- In scope: the public API in `receipt_parser` (`parse_receipt`, `parse_amount`, `LineItem`, `Receipt`, `to_json`, `ReceiptError`), the CLI in `receipt_parser.__main__`, exact decimal parsing, OCR digit fixes for a trailing amount token, keyword-based line classification, date extraction, merchant extraction, and consistency checks.
- Out of scope: OCR itself, images, currencies without two decimal places, itemised tax per line, and language models.

## Timeline

| Date | Event |
|---|---|
| 2026 | Repository created from the factory utility template. |

## Effort metrics

Measured values only; a value that has not been measured stays "pending measurement".

| Metric | Value |
|---|---|
| Tokens (input / output) | 1025475 / 113365 |
| Hours (human) | pending measurement |
| Cost (USD) | 0.1363 |

## Factory run u297 (measured from API usage)

| Date (UTC) | Phase | Model | Batch | Input | Output | Cache write | Cache read | Cost (USD) |
|---|---|---|---|---|---|---|---|---|
| 2026-11-11 | generation | deepseek-v4-pro | yes | 1801 | 30885 | 0 | 3328 | 0.0624 |
| 2026-11-11 | fix-1 | deepseek-flash | no | 14860 | 21067 | 0 | 378880 | 0.0160 |
| 2026-11-11 | audit | deepseek-flash | no | 22064 | 35022 | 0 | 493184 | 0.0258 |
| 2026-11-11 | fix-2 | deepseek-flash | no | 8452 | 16000 | 0 | 2560 | 0.0109 |
| 2026-11-11 | docs | deepseek-flash | no | 100090 | 10391 | 0 | 256 | 0.0212 |

Total: $0.1363. Prices: deepseek line, as measured by its adapter. Providers serve the current version of each model id, so the date tells which version answered; versions, launch stages and price sources per line are in the factory's model register (docs/MODELS.md).
