"""端對端測試：從命令列參數一路到資料檔與輸出文字。"""

import io
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

import pytest

from expense_cli.cli import main


def run(data_file, *argv):
    out, err = io.StringIO(), io.StringIO()
    code = main(list(argv), data_file=data_file, out=out, err=err)
    return code, out.getvalue(), err.getvalue()


def test_add_command_writes_json(data_file):
    code, out, err = run(data_file, "add", "120", "food", "--note", "午餐")
    assert code == 0 and err == ""
    assert "已新增" in out and "120.00" in out and "午餐" in out
    [record] = json.loads(data_file.read_text(encoding="utf-8"))
    assert record == {
        "amount": "120",
        "category": "food",
        "date": date.today().isoformat(),
        "note": "午餐",
    }


def test_add_command_with_date_option(data_file):
    run(data_file, "add", "50", "transport", "--date", "2026-01-15")
    [record] = json.loads(data_file.read_text(encoding="utf-8"))
    assert record["date"] == "2026-01-15"


@pytest.mark.parametrize("bad", ["-50", "0", "abc"])
def test_add_command_invalid_amount(data_file, bad):
    code, out, err = run(data_file, "add", bad, "food")
    assert code == 1
    assert out == ""
    assert err.startswith("錯誤：金額必須是")
    assert not data_file.exists()  # 驗證在存取檔案之前，失敗時不寫入任何資料


def test_add_command_invalid_date(data_file):
    code, _, err = run(data_file, "add", "10", "food", "--date", "2026/1/1")
    assert code == 1 and "YYYY-MM-DD" in err


def test_list_command_sorted(data_file):
    run(data_file, "add", "30", "late", "--date", "2026-02-01")
    run(data_file, "add", "10", "early", "--date", "2026-01-01")
    code, out, _ = run(data_file, "list")
    assert code == 0
    assert out.index("2026-01-01") < out.index("2026-02-01")
    assert "10.00" in out and "30.00" in out


def test_list_command_empty_creates_file(data_file):
    code, out, _ = run(data_file, "list")
    assert code == 0
    assert "沒有任何支出紀錄" in out
    assert data_file.exists()


def test_summary_command(data_file):
    run(data_file, "add", "100", "food")
    run(data_file, "add", "50", "food")
    run(data_file, "add", "1000", "rent")
    code, out, _ = run(data_file, "summary")
    assert code == 0
    lines = out.strip().splitlines()
    assert "rent" in lines[2] and "1,000.00" in lines[2]
    assert "food" in lines[3] and "150.00" in lines[3]
    assert "總計" in lines[-1] and "1,150.00" in lines[-1]


def test_summary_command_empty(data_file):
    code, out, _ = run(data_file, "summary")
    assert code == 0 and "沒有任何支出紀錄" in out


def test_corrupted_data_file_reports_error(data_file):
    data_file.write_text("oops", encoding="utf-8")
    code, _, err = run(data_file, "list")
    assert code == 1 and "格式損毀" in err


def test_missing_required_args_exits_with_usage(data_file):
    with pytest.raises(SystemExit) as exc:
        run(data_file, "add", "10")
    assert exc.value.code == 2


def test_script_entry_point(tmp_path):
    """確認 python expense.py 真的可以執行（以 --help 避免寫入真實資料檔）。"""
    script = Path(__file__).resolve().parent.parent / "expense.py"
    result = subprocess.run(
        [sys.executable, str(script), "--help"],
        capture_output=True, text=True, cwd=tmp_path,
    )
    assert result.returncode == 0
    assert "add" in result.stdout and "summary" in result.stdout
