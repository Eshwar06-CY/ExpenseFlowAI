"""
PDF Report Generator Service - ExpenseFlowAI

Generates professional, bank-grade PDF financial reports with ReportLab:
- Executive Cover Page & Health Score Gauge Box
- Income, Category Expenses & Budget Adherence Tables
- Savings Goals Progress & Forecast Runway Analysis
- AI Personal CFO Strategic Advice
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
)

logger = logging.getLogger(__name__)

STORAGE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "storage", "digests")
os.makedirs(STORAGE_DIR, exist_ok=True)


class PDFGenerator:
    @classmethod
    def generate_digest_pdf(cls, user_name: str, digest_data: Dict[str, Any], output_path: str) -> str:
        """
        Generates a professional financial PDF report and saves it to output_path.
        """
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()

        # Custom Palette
        PRIMARY = colors.HexColor("#4f46e5")    # Indigo-600
        SECONDARY = colors.HexColor("#0f172a")  # Dark Slate
        ACCENT_EMERALD = colors.HexColor("#10b981") # Emerald
        ACCENT_ROSE = colors.HexColor("#f43f5e")    # Rose
        LIGHT_BG = colors.HexColor("#f8fafc")   # Slate-50
        BORDER_CLR = colors.HexColor("#e2e8f0")

        # Custom Styles
        title_style = ParagraphStyle(
            "CoverTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=26,
            leading=32,
            textColor=SECONDARY,
            alignment=0
        )

        subtitle_style = ParagraphStyle(
            "CoverSubtitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=18,
            textColor=PRIMARY,
            alignment=0
        )

        heading_style = ParagraphStyle(
            "SectionHeading",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=18,
            textColor=PRIMARY,
            spaceAfter=8
        )

        body_style = ParagraphStyle(
            "BodyTextCustom",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#334155")
        )

        table_header_style = ParagraphStyle(
            "TableHeader",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=12,
            textColor=colors.white
        )

        table_cell_style = ParagraphStyle(
            "TableCell",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=SECONDARY
        )

        story = []

        # ─── COVER HEADER ──────────────────────────────────────────────────
        story.append(Paragraph("ExpenseFlowAI", subtitle_style))
        story.append(Paragraph("Executive Financial Digest", title_style))
        story.append(Spacer(1, 4))
        
        digest_type = str(digest_data.get("digest_type", "monthly")).upper()
        date_str = datetime.now().strftime("%B %d, %Y")
        story.append(Paragraph(f"<b>Prepared for:</b> {user_name} | <b>Period:</b> {digest_type} | <b>Generated:</b> {date_str}", body_style))
        story.append(Spacer(1, 12))
        story.append(HRFlowable(width="100%", thickness=2, color=PRIMARY, spaceAfter=15))

        # ─── EXECUTIVE SUMMARY & HEALTH SCORE GAUGE ───────────────────────
        health = digest_data.get("financial_health", {})
        score = health.get("score", 88)
        status_text = health.get("status", "Excellent")

        metrics = digest_data.get("metrics", {})
        tot_bal = metrics.get("total_balance", 0.0)
        net_worth = metrics.get("net_worth", 0.0)
        inc = metrics.get("period_income", 0.0)
        exp = metrics.get("period_expense", 0.0)
        sav = metrics.get("period_savings", 0.0)
        sav_rate = metrics.get("savings_rate", 0.0)

        # Health Score Box
        summary_box_data = [
            [
                Paragraph(f"<font size=18 color='#4f46e5'><b>{score} / 100</b></font><br/><b>Health Score ({status_text})</b>", body_style),
                Paragraph(f"<b>Total Balance:</b> ${tot_bal:,.2f}<br/><b>Net Worth:</b> ${net_worth:,.2f}", body_style),
                Paragraph(f"<b>Period Income:</b> ${inc:,.2f}<br/><b>Expenses:</b> ${exp:,.2f}<br/><b>Savings Rate:</b> {sav_rate:.1f}%", body_style)
            ]
        ]
        summary_table = Table(summary_box_data, colWidths=[160, 180, 200])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), LIGHT_BG),
            ('BOX', (0, 0), (-1, -1), 1, BORDER_CLR),
            ('PADDING', (0, 0), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 15))

        # AI Briefing Paragraph
        exec_summary = digest_data.get("summary", "Your financial performance remains strong with healthy savings reserves.")
        story.append(Paragraph(f"<b>Executive AI Briefing:</b> {exec_summary}", body_style))
        story.append(Spacer(1, 15))

        # ─── CATEGORY SPENDING TABLE ──────────────────────────────────────
        story.append(Paragraph("Category Spending Breakdown", heading_style))
        cat_spending = digest_data.get("category_spending", [])

        cat_table_data = [[
            Paragraph("Category", table_header_style),
            Paragraph("Amount Spent", table_header_style),
            Paragraph("% of Total", table_header_style)
        ]]

        tot_exp_sum = max(sum(c.get("amount", 0.0) for c in cat_spending), 1.0)
        for cat in cat_spending[:6]:
            amt = cat.get("amount", 0.0)
            pct = (amt / tot_exp_sum) * 100
            cat_table_data.append([
                Paragraph(str(cat.get("category", "General")), table_cell_style),
                Paragraph(f"${amt:,.2f}", table_cell_style),
                Paragraph(f"{pct:.1f}%", table_cell_style)
            ])

        if len(cat_table_data) == 1:
            cat_table_data.append([Paragraph("No expenses recorded", table_cell_style), Paragraph("$0.00", table_cell_style), Paragraph("0%", table_cell_style)])

        cat_table = Table(cat_table_data, colWidths=[240, 150, 150])
        cat_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, BORDER_CLR),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(cat_table)
        story.append(Spacer(1, 15))

        # ─── BUDGET ADHERENCE & GOALS PROGRESS ──────────────────────────────
        story.append(Paragraph("Budget Limits & Savings Goals", heading_style))
        budgets = digest_data.get("budget_overview", [])
        goals = digest_data.get("goal_overview", [])

        bg_table_data = [[
            Paragraph("Item", table_header_style),
            Paragraph("Target / Limit", table_header_style),
            Paragraph("Current / Spent", table_header_style),
            Paragraph("Status", table_header_style)
        ]]

        for b in budgets[:3]:
            bg_table_data.append([
                Paragraph(f"Budget: {b.get('category', 'General')}", table_cell_style),
                Paragraph(f"${b.get('budget_amount', 0.0):,.2f}", table_cell_style),
                Paragraph(f"${b.get('spent_amount', 0.0):,.2f}", table_cell_style),
                Paragraph(f"{b.get('risk_level', 'safe').upper()} ({b.get('burn_rate_pct', 0)}%)", table_cell_style)
            ])

        for g in goals[:3]:
            bg_table_data.append([
                Paragraph(f"Goal: {g.get('title', 'Target')}", table_cell_style),
                Paragraph(f"${g.get('target_amount', 0.0):,.2f}", table_cell_style),
                Paragraph(f"${g.get('current_amount', 0.0):,.2f}", table_cell_style),
                Paragraph(f"{g.get('progress_pct', 0)}% Complete", table_cell_style)
            ])

        if len(bg_table_data) == 1:
            bg_table_data.append([Paragraph("No active budgets or goals", table_cell_style), Paragraph("-", table_cell_style), Paragraph("-", table_cell_style), Paragraph("-", table_cell_style)])

        bg_table = Table(bg_table_data, colWidths=[200, 110, 110, 120])
        bg_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), SECONDARY),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, BORDER_CLR),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(bg_table)
        story.append(Spacer(1, 15))

        # ─── FORECAST RUNWAY & STRATEGIC RECOMMENDATIONS ───────────────────
        story.append(Paragraph("30-Day Forecast & AI Strategic Action Plan", heading_style))
        fc = digest_data.get("forecast_snapshot", {})
        proj_end = fc.get("projected_end_balance", tot_bal)
        expected_surplus = fc.get("expected_surplus", 0.0)

        fc_box_data = [[
            Paragraph(f"<b>30-Day Projected End Balance:</b> ${proj_end:,.2f}<br/><b>Expected Net Surplus:</b> ${expected_surplus:,.2f}", body_style),
            Paragraph("<b>AI Strategic Action Plan:</b><br/>1. Maintain discretionary category budgets below 80%.<br/>2. Allocate surplus funds to top emergency goal.<br/>3. Review upcoming bill due dates.", body_style)
        ]]
        fc_table = Table(fc_box_data, colWidths=[260, 280])
        fc_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), LIGHT_BG),
            ('BOX', (0, 0), (-1, -1), 1, BORDER_CLR),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        story.append(fc_table)
        story.append(Spacer(1, 20))

        # ─── FOOTER ──────────────────────────────────────────────────────
        story.append(HRFlowable(width="100%", thickness=1, color=BORDER_CLR, spaceAfter=10))
        story.append(Paragraph("<font size=8 color='#94a3b8'>Generated automatically by ExpenseFlowAI Personal Financial Operating System. Confidential - For Personal Use Only.</font>", body_style))

        doc.build(story)
        return output_path
