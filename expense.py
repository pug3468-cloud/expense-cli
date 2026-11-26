#!/usr/bin/env python3
"""進入點：python expense.py <command> ..."""

import sys

from expense_cli.cli import main

if __name__ == "__main__":
    sys.exit(main())
