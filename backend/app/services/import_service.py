import csv
import io
import openpyxl
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_
from app.models.transaction import Transaction
from app.models.category import Category
from app.models.account import Account
from app.models.import_history import ImportHistory
from app.models.mapping_template import ImportTemplate
from app.routers.transactions import sync_budget_for_transaction
from app.services.cache import cache_service

KEYWORDS_MAPPING = {
    ("uber", "lyft", "taxi", "cab", "metro", "transit", "bus", "train", "flight", "airlines"): "Transportation",
    ("starbucks", "mcdonalds", "restaurant", "food", "cafe", "uber eats", "doordash", "grubhub", "pizza", "burger", "diner"): "Food & Dining",
    ("amazon", "walmart", "target", "grocery", "groceries", "supermarket", "costco", "kroger", "safeway"): "Groceries",
    ("netflix", "spotify", "hulu", "disney", "youtube", "theater", "cinema", "showtime", "hbo"): "Entertainment",
    ("comcast", "verizon", "t-mobile", "att", "utility", "electric", "power", "water", "gas", "sewer"): "Utilities",
    ("salary", "payroll", "stripe transfer", "direct deposit", "invoice", "dividend", "interest"): "Income"
}

class ImportService:
    @staticmethod
    def parse_file(filename: str, contents: bytes) -> List[List[str]]:
        """
        Parses CSV or Excel (.xlsx) file contents into a list of row lists.
        """
        if filename.endswith(".xlsx"):
            f = io.BytesIO(contents)
            wb = openpyxl.load_workbook(f, data_only=True)
            sheet = wb.active
            rows = []
            for r in sheet.iter_rows(values_only=True):
                # Ensure it's not a completely empty row
                if any(v is not None for v in r):
                    rows.append([str(v) if v is not None else "" for v in r])
            return rows
        else:
            # Assume CSV by default
            text = contents.decode("utf-8", errors="ignore")
            f = io.StringIO(text)
            reader = csv.reader(f)
            return [row for row in reader if row]

    @staticmethod
    def suggest_category(db: Session, user_id: int, description: str) -> Optional[Category]:
        """
        Suggests a category based on previous description match, merchant string, or predefined rules.
        """
        if not description:
            return None
        desc_lower = description.lower()

        # 1. Previous exact or partial merchant name selections
        prev_tx = db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.description.ilike(f"%{description}%"),
            Transaction.category_id != None
        ).order_by(Transaction.date.desc()).first()
        
        if prev_tx and prev_tx.category:
            return prev_tx.category

        # 2. Keyword rules mapping
        for keywords, cat_name in KEYWORDS_MAPPING.items():
            if any(kw in desc_lower for kw in keywords):
                cat = db.query(Category).filter(
                    Category.user_id == user_id,
                    Category.name.ilike(cat_name)
                ).first()
                if not cat:
                    cat_type = "income" if cat_name == "Income" else "expense"
                    cat = Category(user_id=user_id, name=cat_name, type=cat_type, icon="Tag", color="#8B5CF6")
                    db.add(cat)
                    db.commit()
                    db.refresh(cat)
                return cat
        return None

    @staticmethod
    def detect_duplicate(
        db: Session, 
        user_id: int, 
        date_obj: datetime, 
        amount: float, 
        description: str, 
        account_id: int
    ) -> Optional[Transaction]:
        """
        Scans DB for a transaction matching date (same day), amount, description, and account.
        """
        start_of_day = date_obj.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = date_obj.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        abs_amount = abs(amount)
        existing = db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.account_id == account_id,
            Transaction.amount == abs_amount,
            Transaction.date >= start_of_day,
            Transaction.date <= end_of_day,
            Transaction.description.ilike(description)
        ).first()
        return existing

    @staticmethod
    def execute_import(
        db: Session, 
        user_id: int, 
        filename: str, 
        rows: List[Dict[str, Any]], 
        duplicate_action: str
    ) -> ImportHistory:
        """
        Executes a batch transactional import of list items, resolving duplicates and balance impacts.
        """
        import_job = ImportHistory(
            user_id=user_id,
            filename=filename,
            rows_imported=0,
            rows_skipped=0,
            rows_failed=0,
            status="completed"
        )
        db.add(import_job)
        db.commit()
        db.refresh(import_job)

        categories_to_sync = set()

        for row in rows:
            try:
                # 1. Parse date string
                dt = datetime.fromisoformat(row["date"].replace("Z", "+00:00"))
                amount = float(row["amount"])
                desc = row["description"]
                account_id = row["account_id"]
                category_id = row.get("category_id")
                tx_type = row.get("type", "expense")

                # 2. Check for duplicate
                duplicate = ImportService.detect_duplicate(db, user_id, dt, amount, desc, account_id)
                
                if duplicate:
                    if duplicate_action == "skip":
                        import_job.rows_skipped += 1
                        continue
                    elif duplicate_action in ("replace", "merge"):
                        # Revert old balance
                        account = db.query(Account).filter(Account.id == duplicate.account_id).first()
                        if account:
                            if duplicate.type == "income":
                                account.balance -= duplicate.amount
                            elif duplicate.type == "expense":
                                account.balance += duplicate.amount
                            elif duplicate.type == "transfer":
                                account.balance += duplicate.amount
                                
                        if duplicate.type == "transfer" and duplicate.to_account_id:
                            to_account = db.query(Account).filter(Account.id == duplicate.to_account_id).first()
                            if to_account:
                                to_account.balance -= duplicate.amount

                        # Update fields
                        duplicate.amount = amount
                        duplicate.description = desc
                        duplicate.category_id = category_id
                        duplicate.type = tx_type
                        
                        # Apply new balance
                        new_account = db.query(Account).filter(Account.id == account_id).first()
                        if new_account:
                            if tx_type == "income":
                                new_account.balance += amount
                            elif tx_type == "expense":
                                new_account.balance -= amount
                            elif tx_type == "transfer":
                                new_account.balance -= amount
                                
                        if tx_type == "transfer" and row.get("to_account_id"):
                            duplicate.to_account_id = row["to_account_id"]
                            new_to_acct = db.query(Account).filter(Account.id == row["to_account_id"]).first()
                            if new_to_acct:
                                new_to_acct.balance += amount

                        if category_id:
                            categories_to_sync.add((category_id, dt))
                        import_job.rows_imported += 1
                        continue

                # 3. Create fresh transaction
                tx = Transaction(
                    user_id=user_id,
                    type=tx_type,
                    amount=amount,
                    description=desc,
                    date=dt,
                    category_id=category_id,
                    account_id=account_id,
                    to_account_id=row.get("to_account_id"),
                    import_id=import_job.id
                )
                db.add(tx)

                # Reconcile account balance
                account = db.query(Account).filter(Account.id == account_id).first()
                if account:
                    if tx_type == "income":
                        account.balance += amount
                    elif tx_type == "expense":
                        account.balance -= amount
                    elif tx_type == "transfer":
                        account.balance -= amount

                if tx_type == "transfer" and row.get("to_account_id"):
                    to_account = db.query(Account).filter(Account.id == row["to_account_id"]).first()
                    if to_account:
                        to_account.balance += amount

                if category_id:
                    categories_to_sync.add((category_id, dt))
                
                import_job.rows_imported += 1

            except Exception as e:
                import_job.rows_failed += 1

        db.commit()

        # Re-sync budgets
        for cat_id, date_val in categories_to_sync:
            try:
                sync_budget_for_transaction(db, user_id, cat_id, date_val)
            except Exception:
                pass

        # Clear cache stats
        cache_service.delete(f"user:{user_id}:stats")
        cache_service.delete_pattern(f"user:{user_id}:insights*")

        return import_job

    @staticmethod
    def rollback_import(db: Session, user_id: int, import_id: int) -> bool:
        """
        Reverts an entire import batch by deleting transactions and undoing account balance changes.
        """
        import_job = db.query(ImportHistory).filter(
            ImportHistory.id == import_id, 
            ImportHistory.user_id == user_id
        ).first()
        
        if not import_job or import_job.status == "rolled_back":
            return False

        transactions = db.query(Transaction).filter(
            Transaction.import_id == import_id,
            Transaction.user_id == user_id
        ).all()

        categories_to_sync = set()

        for tx in transactions:
            # Reverse original balances
            account = db.query(Account).filter(Account.id == tx.account_id).first()
            if account:
                if tx.type == "income":
                    account.balance -= tx.amount
                elif tx.type == "expense":
                    account.balance += tx.amount
                elif tx.type == "transfer":
                    account.balance += tx.amount

            if tx.type == "transfer" and tx.to_account_id:
                to_account = db.query(Account).filter(Account.id == tx.to_account_id).first()
                if to_account:
                    to_account.balance -= tx.amount

            if tx.category_id:
                categories_to_sync.add((tx.category_id, tx.date))

            db.delete(tx)

        import_job.status = "rolled_back"
        db.commit()

        # Re-sync budget logs
        for cat_id, date_val in categories_to_sync:
            try:
                sync_budget_for_transaction(db, user_id, cat_id, date_val)
            except Exception:
                pass

        # Clear cache keys
        cache_service.delete(f"user:{user_id}:stats")
        cache_service.delete_pattern(f"user:{user_id}:insights*")

        return True
