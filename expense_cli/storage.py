"""資料存取層：負責 expenses.json 的讀寫，不包含任何業務規則。"""

import json
import os
import tempfile
from pathlib import Path


class StorageError(Exception):
    """資料檔無法讀取或寫入時拋出。"""


class JsonStorage:
    """以 JSON 檔案保存一個「紀錄清單」（list of dict）。"""

    def __init__(self, path):
        self.path = Path(path)

    def ensure_exists(self):
        """檔案不存在時建立一個空清單。"""
        if not self.path.exists():
            self.save([])

    def load(self):
        self.ensure_exists()
        try:
            with self.path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise StorageError(
                f"資料檔 {self.path} 格式損毀（第 {e.lineno} 行）：請修正或移除該檔案"
            ) from e
        except OSError as e:
            raise StorageError(f"無法讀取資料檔 {self.path}：{e.strerror}") from e
        if not isinstance(data, list):
            raise StorageError(f"資料檔 {self.path} 內容應為 JSON 陣列")
        return data

    def save(self, records):
        """先寫入暫存檔再原子性取代，避免寫到一半中斷導致資料檔損毀。"""
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            fd, tmp = tempfile.mkstemp(dir=self.path.parent, suffix=".tmp")
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    json.dump(records, f, ensure_ascii=False, indent=2)
                    f.write("\n")
                os.replace(tmp, self.path)
            except BaseException:
                if os.path.exists(tmp):
                    os.unlink(tmp)
                raise
        except OSError as e:
            raise StorageError(f"無法寫入資料檔 {self.path}：{e.strerror}") from e
