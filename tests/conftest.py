import sys
from pathlib import Path

import pytest

# 讓測試可以直接 import 專案根目錄下的 expense_cli 套件
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from expense_cli.service import ExpenseService  # noqa: E402
from expense_cli.storage import JsonStorage  # noqa: E402


@pytest.fixture
def data_file(tmp_path):
    """每個測試使用獨立的暫存資料檔，不會動到真正的 expenses.json。"""
    return tmp_path / "expenses.json"


@pytest.fixture
def service(data_file):
    return ExpenseService(JsonStorage(data_file))
