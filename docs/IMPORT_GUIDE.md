# Data Import Guide — ExpenseFlow AI

ExpenseFlow AI provides an interactive **Smart Import Wizard** that allows you to easily migrate your financial history from bank statements in **CSV** or **Excel (.xlsx)** format into your ledger.

---

## 📋 Supported Formats

The importer supports two file types:
1. **Comma Separated Values (.csv):** Standard text-based statements.
2. **Microsoft Excel Spreadsheet (.xlsx):** Native spreadsheet worksheets.

### Statement Columns
The statement can have any column headers (e.g. `Tx Date`, `Transaction Date`, `Value`, `Outflow`, `Details`, `Merchant`). During step 2 of the wizard, you can manually map these to ExpenseFlow's standard ledger attributes:
- **Date (Required):** Transaction timestamp. Supports formats: `YYYY-MM-DD`, `MM/DD/YYYY`, `DD/MM/YYYY`, and ISO timestamps.
- **Amount (Required):** Transaction quantity. Can include currency signs (e.g. `$`, `€`) or commas; outflows can be represented as negative numbers (e.g. `-150.00`) which will be saved as positive values of type `expense`.
- **Description (Required):** The merchant or details of the cash flow.
- **Category (Optional):** Pre-classified category values.
- **Account (Optional):** Source/Target bank account.
- **Reference (Optional):** Unique transaction ID or checksum.

---

## ⚡ Interactive Wizard Steps

1. **Upload File:** Select a file and pick the target ledger Account in your workspace.
2. **Column Mapping:** Select which statement headers match Date, Amount, and Description. You can save your configurations as a **Mapping Template** for reuse.
3. **Validate & Suggest:** The backend reviews date/amount formats, automatically suggests categories using matching transaction rules and predefined merchants offline, and highlights duplicate candidates.
4. **Resolve Duplicates:** Select how to process duplicates:
   - **Skip:** Do not import row (Recommended).
   - **Replace/Merge:** Reconciles balance to overwrite the matching transaction with new statement details.
   - **Import Anyway:** Add as a separate entry regardless of duplication.
5. **Finalize:** Apply overrides (you can correct categories inside the grid table) and click import to sync account balances and monthly budgets.

---

## 🛡️ Import Auditing & Rollback Safety

All statements successfully imported are recorded under **Import History**.
- **Audit Logs:** View the file name, import date, rows imported, rows skipped, and rows failed.
- **Transactional Rollback:** Click **Rollback Import** on any batch. The engine will automatically find all transactions created via that import batch, reverse their account balance changes, and delete the ledger entries, returning your workspace accounts to their clean initial state.
