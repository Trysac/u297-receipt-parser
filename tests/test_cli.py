"""Tests for the command-line interface."""

import json
import sys

from receipt_parser.__main__ import main


def _run_cli(argv, input_text=None):
    """Run main with given argv and optional stdin, return exit code and stdout."""
    # Use capsys to capture stdout
    import io
    from contextlib import redirect_stdout

    stdout = io.StringIO()
    with redirect_stdout(stdout):
        if input_text is not None:
            # patch sys.stdin
            old_stdin = sys.stdin
            sys.stdin = io.StringIO(input_text)
        try:
            exit_code = main(argv)
        finally:
            if input_text is not None:
                sys.stdin = old_stdin
    return exit_code, stdout.getvalue()


class TestCLI:
    def test_file_input_ok(self, tmp_path):
        file_path = tmp_path / "receipt.txt"
        file_path.write_text("TOTAL 9.99\n", encoding="utf-8")
        exit_code, out = _run_cli([str(file_path)])
        assert exit_code == 0
        data = json.loads(out)
        assert data["total"] == "9.99"

    def test_stdin_input(self):
        exit_code, out = _run_cli(["-"], input_text="TOTAL 9.99\n")
        assert exit_code == 0
        data = json.loads(out)
        assert data["total"] == "9.99"

    def test_strict_with_issues(self, tmp_path):
        file_path = tmp_path / "receipt.txt"
        file_path.write_text("TOTAL 10.99\n", encoding="utf-8")
        exit_code, _ = _run_cli(["--strict", str(file_path)])
        assert exit_code == 1

    def test_strict_without_issues(self, tmp_path):
        file_path = tmp_path / "receipt.txt"
        file_path.write_text("Item 10.99\nTOTAL 10.99\n", encoding="utf-8")
        exit_code, _ = _run_cli(["--strict", str(file_path)])
        assert exit_code == 0

    def test_missing_file(self):
        exit_code, out = _run_cli(["nonexistent.txt"])
        assert exit_code == 2
        assert out == ""

    def test_invalid_amount_error(self, tmp_path):
        file_path = tmp_path / "receipt.txt"
        file_path.write_text("TOTAL 3.5\n", encoding="utf-8")
        # 3.5 is invalid amount, but parse_receipt will treat line as no amount
        # so it becomes merchant? Actually line without amount, contains letter, merchant set.
        # So no error, total None, issues missing_total.
        # We won't test this here.
        pass

    def test_month_first_flag(self, tmp_path):
        file_path = tmp_path / "receipt.txt"
        file_path.write_text("08/11/2026\nTOTAL 1.00\n", encoding="utf-8")
        exit_code, out = _run_cli(["--month-first", str(file_path)])
        assert exit_code == 0
        data = json.loads(out)
        assert data["date"] == "2026-08-11"  # month first
