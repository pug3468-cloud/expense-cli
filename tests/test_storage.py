import json

import pytest

from expense_cli.storage import JsonStorage, StorageError


def test_load_creates_file_when_missing(data_file):
    assert not data_file.exists()
    assert JsonStorage(data_file).load() == []
    assert data_file.exists()
    assert json.loads(data_file.read_text(encoding="utf-8")) == []


def test_creates_missing_parent_directory(tmp_path):
    path = tmp_path / "nested" / "dir" / "expenses.json"
    JsonStorage(path).load()
    assert path.exists()


def test_save_then_load_roundtrip_keeps_unicode(data_file):
    storage = JsonStorage(data_file)
    records = [{"amount": "120", "category": "food", "date": "2026-01-01", "note": "午餐"}]
    storage.save(records)
    assert storage.load() == records
    assert "午餐" in data_file.read_text(encoding="utf-8")  # 不轉成 \uXXXX


def test_corrupted_file_raises_clear_error(data_file):
    data_file.write_text("{not json", encoding="utf-8")
    with pytest.raises(StorageError, match="格式損毀"):
        JsonStorage(data_file).load()


def test_non_list_json_raises_error(data_file):
    data_file.write_text('{"a": 1}', encoding="utf-8")
    with pytest.raises(StorageError, match="JSON 陣列"):
        JsonStorage(data_file).load()
