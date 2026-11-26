"""業務邏輯層：支出模型、輸入驗證、新增 / 列出 / 統計。

這層不處理命令列參數也不輸出文字，只回傳資料或拋出 ValidationError，
因此可以獨立測試，未來換成其他介面（例如 GUI）也能直接重用。
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation


class ValidationError(Exception):
    """使用者輸入不符合規則時拋出，訊息可直接顯示給使用者。"""


@dataclass(frozen=True)
class Expense:
    amount: Decimal
    category: str
    date: date
    note: str = ""

    def to_dict(self):
        # 金額存成字串以保留精確值（JSON number 會被讀成 float）
        return {
            "amount": str(self.amount),
            "category": self.category,
            "date": self.date.isoformat(),
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            amount=Decimal(str(data["amount"])),
            category=data["category"],
            date=date.fromisoformat(data["date"]),
            note=data.get("note", ""),
        )


def parse_amount(value):
    """把輸入轉成正的 Decimal，否則拋出 ValidationError。"""
    try:
        amount = Decimal(str(value).strip())
    except InvalidOperation:
        raise ValidationError(f"金額必須是數字，收到：{value!r}") from None
    if not amount.is_finite():
        raise ValidationError(f"金額必須是有限的數字，收到：{value!r}")
    if amount <= 0:
        raise ValidationError(f"金額必須是正數，收到：{value}")
    return amount


def parse_category(value):
    category = (value or "").strip()
    if not category:
        raise ValidationError("類別不可為空白")
    return category


def parse_date(value):
    """None 代表今天；否則必須是 YYYY-MM-DD。"""
    if value is None:
        return date.today()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ValidationError(
            f"日期格式錯誤，請使用 YYYY-MM-DD，收到：{value!r}"
        ) from None


class ExpenseService:
    def __init__(self, storage):
        self.storage = storage

    def add(self, amount, category, note=None, on_date=None):
        expense = Expense(
            amount=parse_amount(amount),
            category=parse_category(category),
            date=parse_date(on_date),
            note=(note or "").strip(),
        )
        records = self.storage.load()
        records.append(expense.to_dict())
        self.storage.save(records)
        return expense

    def list(self):
        """依日期由舊到新排序；同一天保留輸入順序（sorted 為穩定排序）。"""
        expenses = [Expense.from_dict(r) for r in self.storage.load()]
        return sorted(expenses, key=lambda e: e.date)

    def summary(self):
        """回傳 ({類別: 總金額}, 總計)，類別依金額由大到小排列。"""
        totals = {}
        for e in self.list():
            totals[e.category] = totals.get(e.category, Decimal("0")) + e.amount
        ordered = dict(sorted(totals.items(), key=lambda kv: (-kv[1], kv[0])))
        return ordered, sum(totals.values(), Decimal("0"))
