import csv
import io
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from sqlalchemy import select, or_

from app.database.session import get_db
from app.models.transaction import Transaction
from app.models.account import Account
from app.models.category import Category
from app.models.user import User
from app.models.import_history import ImportHistory
from app.models.mapping_template import ImportTemplate
from app.routers.deps import get_current_user
from app.services.import_service import ImportService
from app.services.cache import cache_service
from app.schemas.import_schemas import (
    ImportTemplateCreate, ImportTemplateResponse, ImportHistoryResponse,
    PreviewResponse, ImportAnalyzeResponse, ImportAnalyzeRow, ImportExecutePayload
)

router = APIRouter()

# --- Legacy endpoint preserved for backward compatibility ---
@router.post("/csv", status_code=status.HTTP_201_CREATED)
async def import_transactions_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Import transactions from a CSV file (legacy).
    Validates account names, category names, dates, amounts, and transaction types.
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Only CSV files are supported."
        )

    content = await file.read()
    try:
        csv_text = content.decode('utf-8')
    except UnicodeDecodeError:
        try:
            csv_text = content.decode('latin-1')
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to decode CSV file encoding."
            )

    reader = csv.DictReader(io.StringIO(csv_text))
    headers = {h.lower().strip().replace('_', ' ').replace('"', ''): h for h in reader.fieldnames or []}
    
    date_col = next((headers[k] for k in ['date', 'transaction date', 'time'] if k in headers), None)
    type_col = next((headers[k] for k in ['type', 'transaction type'] if k in headers), None)
    desc_col = next((headers[k] for k in ['description', 'name', 'memo'] if k in headers), None)
    amount_col = next((headers[k] for k in ['amount', 'value'] if k in headers), None)
    cat_col = next((headers[k] for k in ['category', 'category name', 'tag'] if k in headers), None)
    acc_col = next((headers[k] for k in ['account', 'source account', 'from account'] if k in headers), None)
    to_acc_col = next((headers[k] for k in ['to account', 'destination account'] if k in headers), None)

    required = [date_col, type_col, amount_col, acc_col]
    if any(col is None for col in required):
        missing = [req for req, col in zip(['Date', 'Type', 'Amount', 'Account'], required) if col is None]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"CSV is missing required columns: {', '.join(missing)}"
        )

    accounts_stmt = select(Account).where(Account.user_id == current_user.id)
    accounts = {a.name.lower().strip(): a for a in db.execute(accounts_stmt).scalars().all()}

    categories_stmt = select(Category).where(
        or_(
            Category.user_id == current_user.id,
            Category.user_id.is_(None)
        )
    )
    categories = {c.name.lower().strip(): c for c in db.execute(categories_stmt).scalars().all()}

    imported_transactions = []
    errors = []
    row_num = 1

    for row in reader:
        row_num += 1
        tx_type_raw = (row.get(type_col) or "").lower().strip()
        if tx_type_raw not in ['income', 'expense', 'transfer']:
            errors.append(f"Row {row_num}: Invalid type '{tx_type_raw}'. Must be income, expense, or transfer.")
            continue

        date_raw = (row.get(date_col) or "").strip()
        tx_date = None
        for fmt in ('%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S'):
            try:
                tx_date = datetime.strptime(date_raw, fmt)
                break
            except ValueError:
                continue
        if not tx_date:
            errors.append(f"Row {row_num}: Invalid date format '{date_raw}'.")
            continue

        amount_raw = (row.get(amount_col) or "").strip().replace('$', '').replace(',', '')
        try:
            amount = float(amount_raw)
            if amount <= 0:
                errors.append(f"Row {row_num}: Amount must be greater than zero.")
                continue
        except ValueError:
            errors.append(f"Row {row_num}: Invalid amount format '{amount_raw}'.")
            continue

        acc_name_raw = (row.get(acc_col) or "").lower().strip()
        account = accounts.get(acc_name_raw)
        if not account:
            errors.append(f"Row {row_num}: Account '{row.get(acc_col)}' not found in workspace.")
            continue

        to_account = None
        if tx_type_raw == 'transfer':
            to_acc_name_raw = (row.get(to_acc_col) or "").lower().strip()
            if not to_acc_name_raw:
                errors.append(f"Row {row_num}: Destination account required for transfer.")
                continue
            to_account = accounts.get(to_acc_name_raw)
            if not to_account:
                errors.append(f"Row {row_num}: Destination account '{row.get(to_acc_col)}' not found.")
                continue
            if account.id == to_account.id:
                errors.append(f"Row {row_num}: Source and destination must be different.")
                continue

        category_id = None
        if cat_col:
            cat_name_raw = (row.get(cat_col) or "").lower().strip()
            category = categories.get(cat_name_raw)
            if category:
                category_id = category.id
            elif cat_name_raw:
                new_cat = Category(
                    user_id=current_user.id,
                    name=(row.get(cat_col) or "").strip(),
                    type=tx_type_raw,
                    icon="Tag",
                    color="#6366F1"
                )
                db.add(new_cat)
                db.commit()
                db.refresh(new_cat)
                categories[cat_name_raw] = new_cat
                category_id = new_cat.id

        if tx_type_raw == 'income':
            account.balance += amount
        elif tx_type_raw == 'expense':
            account.balance -= amount
        elif tx_type_raw == 'transfer':
            account.balance -= amount
            if to_account:
                to_account.balance += amount

        tx = Transaction(
            user_id=current_user.id,
            type=tx_type_raw,
            amount=amount,
            description=(row.get(desc_col) or "").strip() or f"Imported {tx_type_raw}",
            date=tx_date,
            category_id=category_id,
            account_id=account.id,
            to_account_id=to_account.id if to_account else None
        )
        db.add(tx)
        imported_transactions.append(tx)

    if errors and len(imported_transactions) == 0:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": "Failed to parse CSV.", "errors": errors}
        )

    db.commit()
    cache_service.delete(f"user:{current_user.id}:stats")
    cache_service.delete(f"user:{current_user.id}:categories")
    cache_service.delete_pattern(f"user:{current_user.id}:insights*")

    return {
        "success": True,
        "imported_count": len(imported_transactions),
        "total_rows": row_num - 1,
        "errors": errors
    }


# --- Wizard Step 1: Upload & Preview ---
@router.post("/upload", response_model=PreviewResponse)
async def upload_file_preview(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Uploads a bank statement and returns the column headers and first 10 preview rows.
    """
    if not (file.filename.endswith('.csv') or file.filename.endswith('.xlsx')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported format. Upload CSV or Excel (.xlsx) file."
        )

    contents = await file.read()
    try:
        parsed_rows = ImportService.parse_file(file.filename, contents)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse statement file: {str(e)}"
        )

    if not parsed_rows:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty."
        )

    headers = parsed_rows[0]
    preview_data = []
    
    # Extract up to 10 rows for preview mapping UI
    for idx, r in enumerate(parsed_rows[1:11]):
        row_dict = {}
        for h_idx, h in enumerate(headers):
            row_dict[h] = r[h_idx] if h_idx < len(r) else ""
        preview_data.append(row_dict)

    return {
        "headers": headers,
        "rows": preview_data
    }


# --- Wizard Step 2 & 3: Map Columns & Analyze (Data Validation & Suggestions) ---
@router.post("/analyze", response_model=ImportAnalyzeResponse)
async def analyze_mapped_rows(
    payload: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Performs data parsing, column mapping, category suggestion, and duplicate checks.
    """
    raw_rows = payload.get("rows", [])
    mapping = payload.get("mapping", {})
    account_id = payload.get("account_id")

    if not account_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account ID is required to validate imported transactions."
        )

    # Validate mapping columns
    date_col = mapping.get("date_col")
    amount_col = mapping.get("amount_col")
    desc_col = mapping.get("desc_col")
    
    if not date_col or not amount_col or not desc_col:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mapping must specify Date, Amount, and Description column matches."
        )

    analyzed_rows = []
    dup_count = 0
    err_count = 0

    for idx, raw_row in enumerate(raw_rows):
        val_error = None
        parsed_date = None
        parsed_amount = None
        parsed_desc = None
        is_duplicate = False
        sug_cat_id = None
        sug_cat_name = None

        # 1. Parse Date
        date_raw = str(raw_row.get(date_col) or "").strip()
        for fmt in ('%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S'):
            try:
                parsed_date = datetime.strptime(date_raw, fmt)
                break
            except ValueError:
                continue

        if not parsed_date:
            val_error = f"Row {idx+1}: Date format '{date_raw}' is invalid."
            err_count += 1
        
        # 2. Parse Amount
        if parsed_date:
            amount_raw = str(raw_row.get(amount_col) or "").strip().replace('$', '').replace(',', '')
            try:
                parsed_amount = float(amount_raw)
            except ValueError:
                val_error = f"Row {idx+1}: Amount '{amount_raw}' is not numeric."
                err_count += 1

        # 3. Parse Description
        if parsed_date and parsed_amount is not None:
            parsed_desc = str(raw_row.get(desc_col) or "").strip()
            if not parsed_desc:
                parsed_desc = "Imported statement entry"

            # 4. Check for duplicate
            dup = ImportService.detect_duplicate(db, current_user.id, parsed_date, parsed_amount, parsed_desc, account_id)
            if dup:
                is_duplicate = True
                dup_count += 1

            # 5. Get category suggestion
            sug_cat = ImportService.suggest_category(db, current_user.id, parsed_desc)
            if sug_cat:
                sug_cat_id = sug_cat.id
                sug_cat_name = sug_cat.name

        analyzed_rows.append(
            ImportAnalyzeRow(
                original_row=raw_row,
                date=parsed_date.isoformat() if parsed_date else None,
                amount=parsed_amount,
                description=parsed_desc,
                account_id=account_id,
                is_duplicate=is_duplicate,
                suggested_category_id=sug_cat_id,
                suggested_category_name=sug_cat_name,
                validation_error=val_error
            )
        )

    return {
        "rows": analyzed_rows,
        "duplicate_count": dup_count,
        "error_count": err_count
    }


# --- Wizard Step 4: Execute final import ---
@router.post("/execute", response_model=ImportHistoryResponse)
def execute_mapped_import(
    payload: ImportExecutePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Processes final imported transactions list and logs the history job.
    """
    rows_data = [r.dict() for r in payload.rows]
    try:
        job = ImportService.execute_import(
            db=db,
            user_id=current_user.id,
            filename=payload.filename,
            rows=rows_data,
            duplicate_action=payload.duplicate_action
        )
        return job
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Import execution failed: {str(e)}"
        )


# --- Import History Audits ---
@router.get("/history", response_model=List[ImportHistoryResponse])
def get_import_history_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Lists past data statement uploads.
    """
    stmt = select(ImportHistory).where(ImportHistory.user_id == current_user.id).order_by(ImportHistory.date.desc())
    return db.execute(stmt).scalars().all()


@router.post("/history/{import_id}/rollback")
def rollback_import_batch(
    import_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Rolls back all transactions entered via the given import job batch.
    """
    success = ImportService.rollback_import(db, current_user.id, import_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rollback failed. Import job not found or already rolled back."
        )
    return {"success": True, "message": "Import batch successfully rolled back."}


# --- Column Mapping Templates Management ---
@router.get("/templates", response_model=List[ImportTemplateResponse])
def get_mapping_templates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves all column mapping configurations.
    """
    stmt = select(ImportTemplate).where(ImportTemplate.user_id == current_user.id)
    return db.execute(stmt).scalars().all()


@router.post("/templates", response_model=ImportTemplateResponse)
def create_mapping_template(
    template: ImportTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Saves a new column mapping configuration.
    """
    db_template = ImportTemplate(
        user_id=current_user.id,
        name=template.name,
        date_col=template.date_col,
        amount_col=template.amount_col,
        desc_col=template.desc_col,
        cat_col=template.cat_col,
        acc_col=template.acc_col,
        ref_col=template.ref_col
    )
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return db_template


@router.delete("/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_mapping_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Deletes a column mapping configuration.
    """
    stmt = select(ImportTemplate).where(
        ImportTemplate.id == template_id, 
        ImportTemplate.user_id == current_user.id
    )
    db_template = db.execute(stmt).scalar_one_or_none()
    if not db_template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found.")
    
    db.delete(db_template)
    db.commit()
    return
