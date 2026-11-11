# Testing

## Running

```sh
uv run pytest
```

## Policy

The tests use pytest and synthetic receipt text only. They do not require network access. CLI tests call `receipt_parser.__main__.main` in-process, replace `sys.stdin` when needed, and capture stdout with `contextlib.redirect_stdout`. File tests use pytest's `tmp_path`.

## Tiers

There is one pytest suite. No separate conformance tier, marker, or external-tool setup is present in the test files.

## Layout

- `tests/test_amount.py` covers `parse_amount`: valid amounts with `.`, `,`, space, and apostrophe thousands separators; negative values; invalid decimal precision; invalid group sizes; currency symbols rejected; empty and whitespace input.
- `tests/test_cli.py` covers `main`: file input, stdin input (`-`), `--strict` with and without issues, missing file, invalid amount exit code, and `--month-first`.
- `tests/test_json.py` covers `to_json`: all fields, sorted keys, amounts as strings, date as ISO 8601 or null, and null optional values.
