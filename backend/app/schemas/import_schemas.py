from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class ImportTemplateBase(BaseModel):
    name: str
    date_col: Optional[str] = None
    amount_col: Optional[str] = None
    desc_col: Optional[str] = None
    cat_col: Optional[str] = None
    acc_col: Optional[str] = None
    ref_col: Optional[str] = None

class ImportTemplateCreate(ImportTemplateBase):
    pass

class ImportTemplateResponse(ImportTemplateBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True

class ImportHistoryResponse(BaseModel):
    id: int
    user_id: int
    filename: str
    date: datetime
    rows_imported: int
    rows_skipped: int
    rows_failed: int
    status: str

    class Config:
        from_attributes = True

class PreviewResponse(BaseModel):
    headers: List[str]
    rows: List[Dict[str, Any]]

class ImportAnalyzeRow(BaseModel):
    original_row: Dict[str, Any]
    date: Optional[str] = None
    amount: Optional[float] = None
    description: Optional[str] = None
    category_id: Optional[int] = None
    account_id: Optional[int] = None
    reference: Optional[str] = None
    is_duplicate: bool = False
    suggested_category_id: Optional[int] = None
    suggested_category_name: Optional[str] = None
    validation_error: Optional[str] = None

class ImportAnalyzeResponse(BaseModel):
    rows: List[ImportAnalyzeRow]
    duplicate_count: int
    error_count: int

class ImportRowPayload(BaseModel):
    date: str
    amount: float
    description: str
    category_id: Optional[int] = None
    account_id: int
    to_account_id: Optional[int] = None
    reference: Optional[str] = None
    type: str = "expense"  # income, expense, transfer
    is_duplicate: bool = False

class ImportExecutePayload(BaseModel):
    filename: str
    rows: List[ImportRowPayload]
    duplicate_action: str = "skip"  # skip, replace, merge, anyway
