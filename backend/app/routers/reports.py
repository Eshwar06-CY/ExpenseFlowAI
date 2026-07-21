from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_
from io import BytesIO
from datetime import datetime, timezone, timedelta
from typing import Optional
import calendar

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

from app.database.session import get_db
from app.models.account import Account
from app.models.budget import Budget
from app.models.transaction import Transaction
from app.models.category import Category
from app.models.user import User
from app.routers.deps import get_current_user

router = APIRouter()


# ═══════════════════════════════════════════════════════════════════════════
# Analytics Data Endpoints (JSON — for frontend charts)
# ═══════════════════════════════════════════════════════════════════════════

def _parse_date_range(period: str, start: Optional[str], end: Optional[str]):
    """Return (start_dt, end_dt) from period shorthand or explicit dates."""
    now = datetime.utcnow()
    if start and end:
        try:
            return datetime.fromisoformat(start), datetime.fromisoformat(end)
        except ValueError:
            pass
    periods = {
        "7d":  (now - timedelta(days=7),  now),
        "30d": (now - timedelta(days=30), now),
        "90d": (now - timedelta(days=90), now),
        "1y":  (now - timedelta(days=365), now),
        "mtd": (now.replace(day=1, hour=0, minute=0, second=0), now),
        "ytd": (now.replace(month=1, day=1, hour=0, minute=0, second=0), now),
    }
    return periods.get(period, (now - timedelta(days=30), now))


@router.get("/analytics/cash-flow")
def get_cash_flow_chart(
    period: str = Query("30d", description="7d|30d|90d|1y|mtd|ytd"),
    group_by: str = Query("day", description="day|week|month"),
    start: Optional[str] = Query(None),
    end: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns time-bucketed income, expense, and net values for charting.
    Response: { labels: [...], income: [...], expense: [...], net: [...] }
    """
    start_dt, end_dt = _parse_date_range(period, start, end)

    txs = db.execute(
        select(Transaction).where(
            and_(
                Transaction.user_id == current_user.id,
                Transaction.date >= start_dt,
                Transaction.date <= end_dt,
                Transaction.type.in_(["income", "expense"])
            )
        ).order_by(Transaction.date.asc())
    ).scalars().all()

    # Group by bucket
    buckets: dict = {}
    for tx in txs:
        d = tx.date
        if group_by == "week":
            # ISO week key
            key = f"{d.isocalendar()[0]}-W{d.isocalendar()[1]:02d}"
        elif group_by == "month":
            key = d.strftime("%Y-%m")
        else:  # day
            key = d.strftime("%Y-%m-%d")

        if key not in buckets:
            buckets[key] = {"income": 0.0, "expense": 0.0}
        if tx.type == "income":
            buckets[key]["income"] += tx.amount
        else:
            buckets[key]["expense"] += tx.amount

    labels = sorted(buckets.keys())
    return {
        "labels":  labels,
        "income":  [round(buckets[k]["income"], 2) for k in labels],
        "expense": [round(buckets[k]["expense"], 2) for k in labels],
        "net":     [round(buckets[k]["income"] - buckets[k]["expense"], 2) for k in labels],
        "period":  period,
        "group_by": group_by,
        "start": start_dt.isoformat(),
        "end":   end_dt.isoformat(),
    }


@router.get("/analytics/categories")
def get_category_distribution(
    period: str = Query("30d"),
    tx_type: str = Query("expense", description="income|expense"),
    start: Optional[str] = Query(None),
    end: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns spending/income per category for a donut/pie chart.
    Response: { labels: [...], values: [...], colors: [...] }
    """
    start_dt, end_dt = _parse_date_range(period, start, end)

    rows = db.execute(
        select(Category.name, Category.color, func.sum(Transaction.amount))
        .join(Transaction, Transaction.category_id == Category.id)
        .where(
            and_(
                Transaction.user_id == current_user.id,
                Transaction.type == tx_type,
                Transaction.date >= start_dt,
                Transaction.date <= end_dt,
            )
        )
        .group_by(Category.id, Category.name, Category.color)
        .order_by(func.sum(Transaction.amount).desc())
    ).all()

    # Uncategorized bucket
    uncategorized = db.execute(
        select(func.sum(Transaction.amount)).where(
            and_(
                Transaction.user_id == current_user.id,
                Transaction.type == tx_type,
                Transaction.category_id.is_(None),
                Transaction.date >= start_dt,
                Transaction.date <= end_dt,
            )
        )
    ).scalar() or 0.0

    labels  = [r[0] for r in rows]
    values  = [round(float(r[2]), 2) for r in rows]
    cat_colors = [r[1] or "#6366f1" for r in rows]

    if uncategorized > 0:
        labels.append("Uncategorized")
        values.append(round(uncategorized, 2))
        cat_colors.append("#94a3b8")

    total = sum(values) or 1
    percentages = [round(v / total * 100, 1) for v in values]

    return {
        "labels": labels,
        "values": values,
        "colors": cat_colors,
        "percentages": percentages,
        "total": round(total, 2),
    }


@router.get("/analytics/merchants")
def get_top_merchants(
    period: str = Query("30d"),
    limit: int = Query(10, ge=1, le=50),
    start: Optional[str] = Query(None),
    end: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns top merchants by total expense amount.
    Uses transaction description as merchant name proxy.
    """
    start_dt, end_dt = _parse_date_range(period, start, end)

    txs = db.execute(
        select(Transaction.description, func.sum(Transaction.amount), func.count(Transaction.id))
        .where(
            and_(
                Transaction.user_id == current_user.id,
                Transaction.type == "expense",
                Transaction.description.isnot(None),
                Transaction.description != "",
                Transaction.date >= start_dt,
                Transaction.date <= end_dt,
            )
        )
        .group_by(Transaction.description)
        .order_by(func.sum(Transaction.amount).desc())
        .limit(limit)
    ).all()

    return {
        "merchants": [
            {
                "name": r[0],
                "total": round(float(r[1]), 2),
                "count": r[2],
            }
            for r in txs
        ]
    }


@router.get("/analytics/net-worth")
def get_net_worth_trend(
    months: int = Query(12, ge=1, le=36),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns monthly net worth (sum of account balances) trend.
    Approximated from cumulative income minus cumulative expense per month.
    """
    now = datetime.utcnow()
    result_labels = []
    result_values = []

    # Get starting baseline from actual account balances (current snapshot)
    current_balance = db.execute(
        select(func.sum(Account.balance)).where(Account.user_id == current_user.id)
    ).scalar() or 0.0

    # Walk backwards building cumulative view per month
    monthly_nets = []
    for i in range(months - 1, -1, -1):
        target = now - timedelta(days=i * 30)
        y, m = target.year, target.month
        _, last_day = calendar.monthrange(y, m)
        s = datetime(y, m, 1)
        e = datetime(y, m, last_day, 23, 59, 59)

        inc = db.execute(
            select(func.sum(Transaction.amount)).where(
                and_(Transaction.user_id == current_user.id,
                     Transaction.type == "income",
                     Transaction.date >= s, Transaction.date <= e)
            )
        ).scalar() or 0.0

        exp = db.execute(
            select(func.sum(Transaction.amount)).where(
                and_(Transaction.user_id == current_user.id,
                     Transaction.type == "expense",
                     Transaction.date >= s, Transaction.date <= e)
            )
        ).scalar() or 0.0

        monthly_nets.append({"label": f"{y}-{m:02d}", "net": inc - exp})

    # Forward-accumulate from the most recent snapshot
    balance = current_balance
    # subtract recent months to get starting point, then rebuild
    for entry in reversed(monthly_nets):
        balance -= entry["net"]
    running = balance
    for entry in monthly_nets:
        running += entry["net"]
        result_labels.append(entry["label"])
        result_values.append(round(running, 2))

    return {
        "labels": result_labels,
        "values": result_values,
        "current": round(current_balance, 2),
    }


@router.get("/analytics/summary")
def get_analytics_summary(
    period: str = Query("30d"),
    start: Optional[str] = Query(None),
    end: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns high-level KPIs for the analytics dashboard header:
    total income, total expenses, net savings, savings rate,
    avg daily spend, transaction count, vs previous period.
    """
    start_dt, end_dt = _parse_date_range(period, start, end)
    delta = end_dt - start_dt

    # Previous period for comparison
    prev_end   = start_dt
    prev_start = start_dt - delta

    def _totals(s, e):
        inc = db.execute(
            select(func.sum(Transaction.amount)).where(
                and_(Transaction.user_id == current_user.id,
                     Transaction.type == "income",
                     Transaction.date >= s, Transaction.date <= e)
            )
        ).scalar() or 0.0
        exp = db.execute(
            select(func.sum(Transaction.amount)).where(
                and_(Transaction.user_id == current_user.id,
                     Transaction.type == "expense",
                     Transaction.date >= s, Transaction.date <= e)
            )
        ).scalar() or 0.0
        cnt = db.execute(
            select(func.count(Transaction.id)).where(
                and_(Transaction.user_id == current_user.id,
                     Transaction.date >= s, Transaction.date <= e)
            )
        ).scalar() or 0
        return float(inc), float(exp), int(cnt)

    income, expense, count = _totals(start_dt, end_dt)
    prev_income, prev_expense, prev_count = _totals(prev_start, prev_end)

    days = max((end_dt - start_dt).days, 1)
    net = income - expense
    savings_rate = (net / income * 100) if income > 0 else 0.0
    avg_daily_expense = expense / days

    def _pct_change(curr, prev):
        if prev == 0:
            return None
        return round((curr - prev) / prev * 100, 1)

    return {
        "income":           round(income, 2),
        "expense":          round(expense, 2),
        "net":              round(net, 2),
        "savings_rate":     round(savings_rate, 1),
        "avg_daily_expense": round(avg_daily_expense, 2),
        "transaction_count": count,
        "income_change_pct":  _pct_change(income, prev_income),
        "expense_change_pct": _pct_change(expense, prev_expense),
        "net_change_pct":     _pct_change(net, income - prev_expense),
        "period": period,
        "start": start_dt.isoformat(),
        "end":   end_dt.isoformat(),
    }


@router.get("/analytics/budget-adherence")
def get_budget_adherence(
    month: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns budget vs actual spend per category for the given month.
    """
    if not month:
        month = datetime.utcnow().strftime("%Y-%m")

    budgets = db.execute(
        select(Budget).where(
            and_(Budget.user_id == current_user.id, Budget.month == month)
        )
    ).scalars().all()

    result = []
    for b in budgets:
        cat = db.get(Category, b.category_id)
        pct = (b.spent / b.amount * 100) if b.amount > 0 else 0
        result.append({
            "category": cat.name if cat else "Unknown",
            "budget":   round(b.amount, 2),
            "spent":    round(b.spent, 2),
            "remaining": round(max(b.amount - b.spent, 0), 2),
            "over_budget": b.spent > b.amount,
            "pct_used":  round(pct, 1),
        })

    result.sort(key=lambda x: x["pct_used"], reverse=True)
    return {"month": month, "budgets": result}



@router.get("/monthly")
def generate_monthly_report(
    month: str = Query(..., pattern=r"^\d{4}-\d{2}$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate a monthly PDF financial report containing accounts, cash flows, category spending, and budgets.
    """
    # 1. Fetch data for month
    try:
        year, m_val = map(int, month.split("-"))
        _, last_day = calendar.monthrange(year, m_val)
        start_date = datetime(year, m_val, 1, 0, 0, 0)
        end_date = datetime(year, m_val, last_day, 23, 59, 59)
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid month format. Use YYYY-MM."
        )

    # Accounts
    stmt_acct = select(Account).where(Account.user_id == current_user.id)
    accounts = db.execute(stmt_acct).scalars().all()

    # Cash flows
    stmt_inc = select(func.sum(Transaction.amount)).where(
        Transaction.user_id == current_user.id,
        Transaction.type == "income",
        Transaction.date >= start_date,
        Transaction.date <= end_date
    )
    income_sum = db.execute(stmt_inc).scalar() or 0.0

    stmt_exp = select(func.sum(Transaction.amount)).where(
        Transaction.user_id == current_user.id,
        Transaction.type == "expense",
        Transaction.date >= start_date,
        Transaction.date <= end_date
    )
    expense_sum = db.execute(stmt_exp).scalar() or 0.0
    net_savings = income_sum - expense_sum
    savings_rate = (net_savings / income_sum) * 100 if income_sum > 0 else 0.0

    # Category Spending (expenses only)
    stmt_cats = (
        select(Category.name, func.sum(Transaction.amount))
        .join(Transaction, Transaction.category_id == Category.id)
        .where(
            Transaction.user_id == current_user.id,
            Transaction.type == "expense",
            Transaction.date >= start_date,
            Transaction.date <= end_date
        )
        .group_by(Category.id, Category.name)
    )
    category_spending = db.execute(stmt_cats).all()

    # Budgets
    stmt_bud = select(Budget).join(Category).where(Budget.user_id == current_user.id, Budget.month == month)
    budgets = db.execute(stmt_bud).scalars().all()

    # 2. Build PDF Document
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story = []

    styles = getSampleStyleSheet()
    
    # Custom Brand Colors matching ExpenseFlow AI styling theme
    brand_primary = colors.HexColor("#6366F1")
    dark_gray = colors.HexColor("#1F2937")
    light_bg = colors.HexColor("#F9FAFB")
    text_color = colors.HexColor("#374151")

    # Custom Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=brand_primary,
        spaceAfter=5
    )
    subtitle_style = ParagraphStyle(
        'DocSub',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor("#6B7280"),
        spaceAfter=15
    )
    h2_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=dark_gray,
        spaceBefore=12,
        spaceAfter=6
    )

    # Document Header
    story.append(Paragraph("ExpenseFlow AI — Monthly Statement", title_style))
    story.append(Paragraph(f"Financial summary statement for period: {month} | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", subtitle_style))
    story.append(Spacer(1, 10))

    # Cash Flow Summary Card Table
    summary_data = [
        ["Total Income", "Total Expenses", "Net Savings", "Savings Rate"],
        [f"${income_sum:,.2f}", f"${expense_sum:,.2f}", f"${net_savings:,.2f}", f"{savings_rate:.1f}%"]
    ]
    summary_table = Table(summary_data, colWidths=[130]*4)
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), brand_primary),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 10),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('BACKGROUND', (0,1), (-1,-1), light_bg),
        ('TEXTCOLOR', (0,1), (-1,-1), text_color),
        ('FONTSIZE', (0,1), (-1,-1), 11),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E5E7EB"))
    ]))
    story.append(Paragraph("Cash Flow Overview", h2_style))
    story.append(summary_table)
    story.append(Spacer(1, 15))

    # Accounts Breakdown Table
    story.append(Paragraph("Accounts Balance Sheets", h2_style))
    account_data = [["Account Name", "Account Type", "Balance"]]
    for acct in accounts:
        account_data.append([acct.name, acct.type.capitalize(), f"{acct.currency} {acct.balance:,.2f}"])
        
    if len(accounts) == 0:
        account_data.append(["No accounts configured", "", ""])
        
    acct_table = Table(account_data, colWidths=[200, 160, 160])
    acct_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#374151")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 9),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BACKGROUND', (0,1), (-1,-1), light_bg),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E5E7EB")),
        ('ALIGN', (2,0), (2,-1), 'RIGHT')
    ]))
    story.append(acct_table)
    story.append(Spacer(1, 15))

    # Category Spending Table
    story.append(Paragraph("Category Expenses Distribution", h2_style))
    cat_data = [["Category Tag", "Spent Amount"]]
    for cat_name, spent in category_spending:
        cat_data.append([cat_name, f"${spent:,.2f}"])
        
    if len(category_spending) == 0:
        cat_data.append(["No expense transactions", "$0.00"])
        
    cat_table = Table(cat_data, colWidths=[300, 220])
    cat_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#4B5563")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 9),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BACKGROUND', (0,1), (-1,-1), light_bg),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E5E7EB")),
        ('ALIGN', (1,0), (1,-1), 'RIGHT')
    ]))
    story.append(cat_table)
    story.append(Spacer(1, 15))

    # Budgets Table
    story.append(Paragraph("Monthly Budgets Adherence", h2_style))
    bud_data = [["Category", "Budget Limit", "Amount Spent", "Status"]]
    for bud in budgets:
        status_txt = "Over Budget" if bud.spent > bud.amount else "Adhered"
        bud_data.append([bud.category.name, f"${bud.amount:,.2f}", f"${bud.spent:,.2f}", status_txt])
        
    if len(budgets) == 0:
        bud_data.append(["No budgets configured", "", "", ""])
        
    bud_table = Table(bud_data, colWidths=[150, 120, 120, 130])
    bud_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1F2937")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 9),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BACKGROUND', (0,1), (-1,-1), light_bg),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E5E7EB")),
        ('ALIGN', (1,0), (2,-1), 'RIGHT'),
        ('ALIGN', (3,0), (3,-1), 'CENTER')
    ]))
    story.append(bud_table)

    # Build
    doc.build(story)
    buffer.seek(0)
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=expenseflow_statement_{month}.pdf"}
    )
