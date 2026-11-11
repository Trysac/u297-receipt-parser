"""Command-line interface for the receipt parser."""

from __future__ import annotations

import argparse
import pathlib
import sys

from . import ReceiptError, parse_receipt, to_json


def main(argv: list[str] | None = None) -> int:
    """Run the CLI.

    Args:
        argv: Command-line arguments (defaults to ``sys.argv[1:]``).

    Returns:
        Exit code: 0 on success, 1 if issues and ``--strict``, 2 on usage or
        I/O errors.
    """
    parser = argparse.ArgumentParser(
        prog="receipt_parser",
        description="Parse a receipt from OCR text and output JSON.",
    )
    parser.add_argument("path", help="receipt text file path, or '-' for stdin")
    parser.add_argument(
        "--month-first",
        action="store_true",
        help="interpret ambiguous dates as MM/DD/YYYY instead of DD/MM/YYYY",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit with code 1 if the receipt has any issues",
    )
    args = parser.parse_args(argv)

    try:
        if args.path == "-":
            text = sys.stdin.read()
        else:
            text = pathlib.Path(args.path).read_text(encoding="utf-8")
    except OSError:
        return 2

    try:
        receipt = parse_receipt(text, day_first=not args.month_first)
    except ReceiptError:
        return 2

    print(to_json(receipt))

    if args.strict and receipt.issues:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
