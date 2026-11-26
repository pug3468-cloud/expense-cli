# expense-cli

在終端機使用的個人記帳工具。純 Python 3 標準函式庫實作，不需安裝任何第三方套件。

## 安裝

需求：Python 3.9 以上。

```bash
git clone https://github.com/pug3468-cloud/expense-cli.git
cd expense-cli
python3 expense.py --help
```

不需要額外安裝。若要執行測試，才需要安裝 pytest：

```bash
pip install pytest
```

## 使用方式

### 新增支出 `add`

```bash
python3 expense.py add <金額> <類別> [--note 備註] [--date YYYY-MM-DD]
```

```bash
$ python3 expense.py add 120 food --note "午餐"
已新增：2026-11-26 food 120.00（午餐）

$ python3 expense.py add 45.5 交通 --date 2026-11-20
已新增：2026-11-20 交通 45.50
```

- 金額必須是正數，可含小數
- `--note` / `-n`：備註，選填
- `--date` / `-d`：日期，預設為今天

### 列出支出 `list`

依日期由舊到新排序（同一天依輸入順序）：

```bash
$ python3 expense.py list
日期        類別    金額  備註
----------  ----  ------  ----
2026-11-20  交通   45.50
2026-11-26  food  120.00  午餐
```

### 分類統計 `summary`

依類別加總，金額由大到小排列，最後一列為總計：

```bash
$ python3 expense.py summary
類別    金額
----  ------
food  120.00
交通   45.50
總計  165.50
```

### 錯誤訊息

輸入錯誤時會在 stderr 顯示訊息，並以結束碼 `1` 離開：

```bash
$ python3 expense.py add -50 food
錯誤：金額必須是正數，收到：-50

$ python3 expense.py add abc food
錯誤：金額必須是數字，收到：'abc'

$ python3 expense.py add 10 food --date 2026/1/1
錯誤：日期格式錯誤，請使用 YYYY-MM-DD，收到：'2026/1/1'
```

## 資料儲存

資料存在專案目錄下的 `expenses.json`（不論從哪個目錄執行），不存在時會自動建立。
金額以字串保存（如 `"45.5"`）以確保精確，不會有浮點誤差。此檔案已列入 `.gitignore`。

```json
[
  {"amount": "120", "category": "food", "date": "2026-11-26", "note": "午餐"}
]
```

## 專案結構

```
expense.py            進入點
expense_cli/
  storage.py          資料存取：讀寫 JSON 檔
  service.py          業務邏輯：驗證、新增、排序、統計
  cli.py              命令列介面：參數解析與輸出格式
tests/                pytest 測試
```

## 執行測試

```bash
python3 -m pytest
```
