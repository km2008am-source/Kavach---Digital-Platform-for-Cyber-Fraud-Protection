"""Generate a concise PDF evidence pack for a cyber fraud report."""

from datetime import datetime, timezone
from pathlib import Path
import uuid

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from kavach.config import settings
from kavach.contracts import EvidenceSummary


def create_evidence_pdf(
    evidence: EvidenceSummary,
    complaint_draft: str,
    output_dir: str | Path | None = None,
) -> Path:
    """Create a PDF and return its path; caller sends it to the user."""
    target_dir = Path(output_dir or settings.files_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    output_path = target_dir / f"evidence-{uuid.uuid4().hex}.pdf"

    styles = getSampleStyleSheet()
    body = styles["BodyText"]
    body.leading = 14

    document = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=20 * mm,
        title="Fraud evidence summary",
        author="Kavach",
    )

    fields = [
        ("Transaction ID", evidence.transaction_id),
        ("Amount", evidence.amount),
        ("Transaction time", evidence.transaction_time),
        ("Payee UPI ID", evidence.payee_upi),
        ("Scammer phone number", evidence.scammer_number),
    ]

    table_rows = [["Evidence field", "Details"]]
    table_rows.extend([
        (label, value or "Not provided")
        for label, value in fields
    ])
    table_rows.extend(
        (key.replace("_", " ").title(), value)
        for key, value in evidence.additional_details.items()
    )

    table = Table(table_rows, colWidths=[48 * mm, 116 * mm], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#17324D")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [
            colors.white,
            colors.HexColor("#F1F5F9"),
        ]),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))

    safe_draft = (complaint_draft or "No complaint draft provided.")
    story = [
        Paragraph("Fraud evidence summary", styles["Title"]),
        Spacer(1, 4 * mm),
        Paragraph(
            "Generated: "
            + datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            body,
        ),
        Spacer(1, 5 * mm),
        table,
        Spacer(1, 7 * mm),
        Paragraph("Complaint draft", styles["Heading2"]),
        Paragraph(safe_draft.replace("\n", "<br/>"), body),
        Spacer(1, 8 * mm),
        Paragraph(
            "Prepared by Kavach to help you report. Call 1930 for online "
            "financial fraud and file the full complaint at cybercrime.gov.in.",
            styles["Italic"],
        ),
    ]

    document.build(story)
    return output_path