"""命令列介面層：解析參數、呼叫 service、格式化輸出、把錯誤轉成訊息與結束碼。"""

import argparse
import sys
import unicodedata
from pathlib import Path

from .service import ExpenseService, ValidationError
from .storage import JsonStorage, StorageError

DEFAULT_DATA_FILE = Path(__file__).resolve().parent.parent / "expenses.json"


def build_parser():
    parser = argparse.ArgumentParser(
        prog="expense.py", description="命令列記帳工具"
    )
    sub = parser.add_subparsers(dest="command", required=True, metavar="COMMAND")

    p_add = sub.add_parser("add", help="新增一筆支出")
    p_add.add_argument("amount", help="金額（正數）")
    p_add.add_argument("category", help="類別，例如 food、transport")
    p_add.add_argument("--note", "-n", default="", help="備註（選填）")
    p_add.add_argument("--date", "-d", default=None, help="日期 YYYY-MM-DD（預設今天）")

    sub.add_parser("list", help="列出所有支出（依日期排序）")
    sub.add_parser("summary", help="依類別統計金額")
    return parser


# ---- 輸出格式 ----

def fmt_amount(amount):
    return f"{amount:,.2f}"


def display_width(text):
    """中文等全形字元在終端機佔兩格，用來對齊欄位。"""
    return sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in text)


def pad(text, width, align="left"):
    gap = " " * max(width - display_width(text), 0)
    return text + gap if align == "left" else gap + text


def render_table(headers, rows, aligns):
    widths = [
        max(display_width(str(x)) for x in col) for col in zip(headers, *rows)
    ]

    def line(cells):
        return "  ".join(
            pad(str(c), w, a) for c, w, a in zip(cells, widths, aligns)
        ).rstrip()

    sep = "  ".join("-" * w for w in widths)
    return "\n".join([line(headers), sep] + [line(r) for r in rows])


# ---- 子命令 ----

def cmd_add(service, args, out):
    e = service.add(args.amount, args.category, note=args.note, on_date=args.date)
    note = f"（{e.note}）" if e.note else ""
    print(f"已新增：{e.date.isoformat()} {e.category} {fmt_amount(e.amount)}{note}", file=out)


def cmd_list(service, args, out):
    expenses = service.list()
    if not expenses:
        print("目前沒有任何支出紀錄。", file=out)
        return
    rows = [
        (e.date.isoformat(), e.category, fmt_amount(e.amount), e.note)
        for e in expenses
    ]
    print(
        render_table(("日期", "類別", "金額", "備註"), rows,
                     ("left", "left", "right", "left")),
        file=out,
    )


def cmd_summary(service, args, out):
    totals, grand_total = service.summary()
    if not totals:
        print("目前沒有任何支出紀錄。", file=out)
        return
    rows = [(cat, fmt_amount(amt)) for cat, amt in totals.items()]
    rows.append(("總計", fmt_amount(grand_total)))
    print(render_table(("類別", "金額"), rows, ("left", "right")), file=out)


COMMANDS = {"add": cmd_add, "list": cmd_list, "summary": cmd_summary}


def main(argv=None, data_file=None, out=None, err=None):
    out = out or sys.stdout
    err = err or sys.stderr
    args = build_parser().parse_args(argv)
    service = ExpenseService(JsonStorage(data_file or DEFAULT_DATA_FILE))
    try:
        COMMANDS[args.command](service, args, out)
    except (ValidationError, StorageError) as e:
        print(f"錯誤：{e}", file=err)
        return 1
    return 0
