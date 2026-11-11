# Deterministic rule-based receipt parsing

Status: accepted (generated, pending human review)

## Context

Expense tools receive OCR text of photographed receipts and need reliable extraction of totals. OCR output is noisy, mixes decimal conventions, and includes payment lines that can be confused with the real total. Language-model-based extraction is slow, costly, and not reproducible.

## Decision

Implement a rule-based parser in Python using only the standard library (`re`, `decimal`). The parser explicitly defines an amount grammar, identifies keyword labels (subtotal, tax, tip, total, payment), extracts merchant and date, and applies OCR digit fixes before parsing. Consistency checks compare item sums, subtotal, tax, and total, reporting mismatches as issues.

## Consequences

The library is free, offline, deterministic, and explicit about inconsistencies. It handles common receipt layouts and edge cases. Out of scope: OCR itself, images, currencies without two decimals, itemised tax per line, and language models. New layouts may require extending keyword sets or amount heuristics.
