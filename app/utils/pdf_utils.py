import tempfile
from datetime import datetime
from collections import defaultdict

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from weasyprint import HTML
import markdown2
from PyPDF2 import PdfMerger
from fastapi.responses import FileResponse

from app.core.config import collections_map
from app.services.ai_report import generate_full_ai_report


async def create_pdf_report(framework: str):
    collection = collections_map.get(framework)
    if collection is None:
        raise ValueError("Invalid framework")

    cursor = collection.find({})
    total_controls, total_score = 0, 0
    responses = []
    matrix = defaultdict(int)

    async for doc in cursor:
        likelihood = doc.get("likelihood_scale", 0)
        impact = doc.get("impact_scale", 0)
        score = likelihood * impact
        total_controls += 1
        total_score += score
        responses.append({
            "id": doc.get("id"),
            "question": doc.get("question"),
            "likelihood_scale": likelihood,
            "impact_scale": impact,
            "score": score
        })
        matrix[f"{likelihood},{impact}"] += 1

    if total_controls == 0:
        raise ValueError("No assessment data found")

    avg_score = total_score / total_controls
    ai_report = await generate_full_ai_report(responses, total_controls, avg_score, framework, dict(matrix))

    # Step 1: Executive Summary as HTML->PDF
    css_style = """
    <style>
    body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
    h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }
    h2 { color: #34495e; border-bottom: 1px solid #bdc3c7; padding-bottom: 5px; }
    h3 { color: #7f8c8d; }
    table { border-collapse: collapse; width: 100%; margin: 20px 0; }
    th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
    th { background-color: #f2f2f2; font-weight: bold; }
    ul, ol { margin: 10px 0; padding-left: 30px; }
    </style>
    """
    html_summary = markdown2.markdown(ai_report['ai_executive_summary'], extras=['tables', 'fenced-code-blocks'])
    full_html = f"<!DOCTYPE html><html><head>{css_style}</head><body>{html_summary}</body></html>"
    temp_summary_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    HTML(string=full_html).write_pdf(temp_summary_pdf.name)

    # Step 2: Additional PDF via ReportLab
    temp_report_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    doc = SimpleDocTemplate(temp_report_pdf.name, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=24, spaceAfter=30)
    story.append(Paragraph(f"{framework.upper()} Risk Assessment Report", title_style))
    story.append(Spacer(1, 20))

    # Risk Stats Table
    story.append(Paragraph("Risk Statistics", styles['Heading2']))
    stats_data = [
        ['Metric', 'Value'],
        ['Total Controls', str(total_controls)],
        ['High Risk', str(ai_report['statistical_breakdown']['risk_distribution']['critical_high'])],
        ['Medium Risk', str(ai_report['statistical_breakdown']['risk_distribution']['moderate_medium'])],
        ['Low Risk', str(ai_report['statistical_breakdown']['risk_distribution']['acceptable_low'])],
        ['Average Score', str(round(avg_score, 2))],
        ['Risk Level', ai_report['overall_risk_assessment']['risk_level']]
    ]
    stats_table = Table(stats_data)
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(stats_table)
    story.append(Spacer(1, 20))

    # Top Risk Controls
    story.append(Paragraph("Top Risk Controls", styles['Heading2']))
    for control in ai_report['priority_controls'][:5]:
        story.append(Paragraph(f"<b>Control {control['control_id']}</b> (Score: {control['risk_score']})", styles['Normal']))
        story.append(Paragraph(control['question'][:200] + "...", styles['Normal']))
        story.append(Spacer(1, 10))

    doc.build(story)

    # Step 3: Merge PDFs
    final_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    merger = PdfMerger()
    merger.append(temp_summary_pdf.name)
    merger.append(temp_report_pdf.name)
    merger.write(final_pdf.name)
    merger.close()

    return FileResponse(
        final_pdf.name,
        media_type='application/pdf',
        filename=f"{framework}_risk_assessment_report.pdf"
    )
