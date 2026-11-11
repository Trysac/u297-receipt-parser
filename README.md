# receipt-parser

[![PyPI version](https://img.shields.io/pypi/v/trysac-receipt-parser)](https://pypi.org/project/trysac-receipt-parser/)
[![License: MIT](https://img.shields.io/pypi/l/trysac-receipt-parser)](LICENSE)
[![CI](https://github.com/Trysac/u297-receipt-parser/actions/workflows/ci.yml/badge.svg)](https://github.com/Trysac/u297-receipt-parser/actions/workflows/ci.yml)

Parse receipts from OCR text with rules, no model: merchant, date, line items with quantities, subtotal, tax and total in Decimal, OCR digit fixes and consistency checks

## Problem

Describe in two or three sentences the concrete problem this utility solves, who hits it, and what
they do today without it. Replace this paragraph when the first real feature lands.

## Install

```sh
pip install trysac-receipt-parser
# or
uv add trysac-receipt-parser
```

Requires Python 3.10 or newer. No runtime dependencies.

## Usage

```python
import receipt_parser

# normalize() trims surrounding whitespace and lower-cases the text.
print(receipt_parser.normalize("  Hello World "))  # -> "hello world"

# Blank input is rejected explicitly instead of returning an empty string.
try:
    receipt_parser.normalize("   ")
except ValueError as exc:
    print(f"rejected: {exc}")
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md) and [decisions](docs/decisions/)
- [Testing](docs/TESTING.md) and [security](docs/SECURITY.md)
- [Project record](docs/PROJECT.md) and [stack](docs/STACK.md)
- [Changelog](CHANGELOG.md) and [contributing guide](CONTRIBUTING.md)

## License

[MIT](LICENSE) (c) 2026 Miguel Gomez
