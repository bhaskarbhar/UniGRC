from fastapi import FastAPI, HTTPException, Path
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from collections import defaultdict
import requests
import json
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import tempfile
import os
import markdown2
from weasyprint import HTML
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB client and DB setup
MONGODB_URI = os.getenv("MONGODB_URI")
client = AsyncIOMotorClient(MONGODB_URI)
db = client.unigrc

# OpenRouter configuration - ADDED
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")  # Replace with your actual API key
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEEPSEEK_MODEL = "deepseek/deepseek-chat-v3-0324:free"

# Pydantic model for request body
class ResponseData(BaseModel):
    id: int
    question: str
    likelihood_scale: int
    impact_scale: int

# Allowed frameworks mapped to collections
collections_map = {
    "iso": db.iso,
    "nist": db.nist,
    "cis": db.cis,
}

# AI FUNCTIONS - ADDED
def generate_ai_analysis(prompt: str) -> str:
    """
    Generate AI analysis using DeepSeek V3 via OpenRouter
    """
    try:
        response = requests.post(
            url=OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://your-risk-dashboard.com",
                "X-Title": "Risk Assessment Dashboard",
            },
            data=json.dumps({
                "model": DEEPSEEK_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a cybersecurity risk assessment expert. Provide professional, actionable insights for executive reporting. Be concise but comprehensive."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.7,
                "max_tokens": 2000
            }),
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"]
        else:
            return f"Error: OpenRouter API returned status {response.status_code}"
            
    except Exception as e:
        return f"Error generating AI analysis: {str(e)}"

def create_comprehensive_report_prompt(responses, total_controls, avg_score, framework, matrix):
    """
    Create a comprehensive prompt for full AI report generation
    """
    high_risk = [r for r in responses if r['score'] >= 15]
    medium_risk = [r for r in responses if 8 <= r['score'] < 15]
    low_risk = [r for r in responses if r['score'] < 8]
    
    prompt = f"""
Generate a comprehensive cybersecurity risk assessment report for {framework.upper()} framework:

ASSESSMENT DATA:
- Total Controls: {total_controls}
- Average Risk Score: {avg_score:.2f}
- High Risk Controls: {len(high_risk)} ({len(high_risk)/total_controls*100:.1f}%)
- Medium Risk Controls: {len(medium_risk)} ({len(medium_risk)/total_controls*100:.1f}%)
- Low Risk Controls: {len(low_risk)} ({len(low_risk)/total_controls*100:.1f}%)

CRITICAL CONTROLS REQUIRING ATTENTION:
{chr(10).join([f"• Control {r['id']}: {r['question'][:100]}... (Risk Score: {r['score']})" for r in high_risk[:5]])}

RISK MATRIX ANALYSIS:
{chr(10).join([f"• Position ({pos}): {count} controls" for pos, count in matrix.items() if count > 0])}

Please provide a comprehensive executive report including:

1. **EXECUTIVE SUMMARY** 
   - Overall security posture assessment
   - Key findings and risk level classification
   - Strategic recommendations for leadership

2. **DETAILED RISK ANALYSIS**
   - Framework-specific compliance gaps
   - Critical vulnerabilities identified
   - Risk distribution patterns and trends

3. **PRIORITY ACTION PLAN**
   - Immediate actions required (next 30 days)
   - Medium-term improvements (3-6 months)
   - Long-term strategic initiatives (6-12 months)

4. **COMPLIANCE AND GOVERNANCE**
   - {framework.upper()} framework alignment
   - Regulatory considerations
   - Governance recommendations

5. **RESOURCE ALLOCATION GUIDANCE**
   - Budget prioritization suggestions
   - Staffing considerations
   - Technology investment recommendations

6. **MONITORING AND METRICS**
   - Key performance indicators to track
   - Regular assessment schedule
   - Success measurement criteria

Format as a professional executive report suitable for board presentation.
"""
    return prompt
def markdown_to_pdf_bytes(markdown_text):
    """
    Convert markdown text to PDF bytes using WeasyPrint
    """
    # Add basic CSS styling for better PDF appearance
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
    .highlight { background-color: #fff3cd; padding: 10px; border-left: 4px solid #ffc107; }
    </style>
    """
    
    # Convert markdown to HTML
    html_content = markdown2.markdown(markdown_text, extras=['tables', 'fenced-code-blocks'])
    
    # Combine CSS and HTML
    full_html = f"<!DOCTYPE html><html><head>{css_style}</head><body>{html_content}</body></html>"
    
    # Generate PDF bytes
    pdf_bytes = HTML(string=full_html).write_pdf()
    return pdf_bytes

async def generate_full_ai_report(responses, total_controls, avg_score, framework, matrix):
    """
    Generate complete AI analysis report using DeepSeek V3
    """
    # Create comprehensive prompt for full report
    prompt = create_comprehensive_report_prompt(responses, total_controls, avg_score, framework, matrix)
    
    # Get AI analysis
    ai_analysis = generate_ai_analysis(prompt)
    
    # Statistical analysis
    high_risk_count = len([r for r in responses if r['score'] >= 15])
    medium_risk_count = len([r for r in responses if 8 <= r['score'] < 15])
    low_risk_count = len([r for r in responses if r['score'] < 8])
    high_risk_percentage = (high_risk_count / total_controls * 100) if total_controls > 0 else 0
    
    # Risk level classification
    if high_risk_percentage > 30:
        risk_level = "CRITICAL"
        risk_color = "#dc2626"
    elif high_risk_percentage > 15:
        risk_level = "HIGH" 
        risk_color = "#ea580c"
    elif high_risk_percentage > 5:
        risk_level = "MODERATE"
        risk_color = "#eab308"
    else:
        risk_level = "LOW"
        risk_color = "#16a34a"
    
    # Anomaly detection
    anomalies = []
    extreme_scores = [r for r in responses if r['score'] >= 20]
    if extreme_scores:
        anomalies.append(f"🚨 {len(extreme_scores)} controls with critical risk scores (≥20)")
    
    inconsistent_patterns = [r for r in responses if r['impact_scale'] >= 4 and r['likelihood_scale'] <= 2]
    if len(inconsistent_patterns) > total_controls * 0.3:
        anomalies.append("⚠️ High number of high-impact, low-likelihood assessments detected")
    
    # Top risk areas
    top_risks = sorted(responses, key=lambda x: x['score'], reverse=True)[:10]
    
    return {
        "ai_executive_summary": ai_analysis,
        "overall_risk_assessment": {
            "risk_level": risk_level,
            "risk_color": risk_color,
            "confidence_score": min(1.0, total_controls / 20),
            "assessment_completeness": f"{total_controls} controls analyzed"
        },
        "statistical_breakdown": {
            "risk_distribution": {
                "critical_high": high_risk_count,
                "moderate_medium": medium_risk_count, 
                "acceptable_low": low_risk_count
            },
            "percentages": {
                "high_risk_percentage": round(high_risk_percentage, 1),
                "average_risk_score": round(avg_score, 2)
            }
        },
        "priority_controls": [
            {
                "rank": idx + 1,
                "control_id": risk['id'],
                "question": risk['question'],
                "risk_score": risk['score'],
                "likelihood": risk['likelihood_scale'],
                "impact": risk['impact_scale'],
                "priority_level": "IMMEDIATE" if risk['score'] >= 20 else "HIGH" if risk['score'] >= 15 else "MEDIUM"
            }
            for idx, risk in enumerate(top_risks)
        ],
        "anomalies_and_flags": anomalies,
        "framework_compliance": {
            "framework": framework.upper(),
            "model_used": "DeepSeek V3 0324 (Free)",
            "analysis_depth": "Comprehensive"
        }
    }

# YOUR ORIGINAL ENDPOINTS - UNCHANGED
@app.post("/save-response/{framework}")
async def save_response(
    framework: str = Path(..., regex="^(iso|nist|cis)$"),
    data: ResponseData = ...
):
    collection = collections_map.get(framework)
    if collection is None:
        raise HTTPException(status_code=400, detail="Invalid framework")

    # Prepare document
    document = {
        "id": data.id,
        "question": data.question,
        "likelihood_scale": data.likelihood_scale,
        "impact_scale": data.impact_scale,
    }

    # Upsert: if question_id exists, update; else insert new
    result = await collection.update_one(
        {"id": data.id},
        {"$set": document},
        upsert=True
    )

    return {"message": "Response saved", "upserted_id": str(result.upserted_id) if result.upserted_id else None}

@app.get("/dashboard/{framework}")
async def get_dashboard(framework: str):
    collection = collections_map.get(framework)
    if collection is None:
        raise HTTPException(status_code=400, detail="Invalid framework")

    cursor = collection.find({})
    total_controls = 0
    high = 0
    medium = 0
    low = 0
    total_score = 0
    responses = []  # Add this to collect detailed responses

    # Matrix counts for 5x5 grid (keys will be "1,1", "2,3", etc.)
    matrix = defaultdict(int)

    async for doc in cursor:
        likelihood = doc.get("likelihood_scale", 0)
        impact = doc.get("impact_scale", 0)
        score = likelihood * impact

        total_controls += 1
        total_score += score

        # Add detailed response data
        responses.append({
            "id": doc.get("id"),
            "question": doc.get("question"),
            "likelihood_scale": likelihood,
            "impact_scale": impact,
            "score": score
        })

        if score >= 15:
            high += 1
        elif score >= 8:
            medium += 1
        else:
            low += 1

        if 1 <= likelihood <= 5 and 1 <= impact <= 5:
            matrix[f"{likelihood},{impact}"] += 1

    avg = (total_score / total_controls) if total_controls > 0 else 0

    return JSONResponse(content={
        "total_controls": total_controls,
        "high": high,
        "medium": medium,
        "low": low,
        "avg": avg,
        "matrix": matrix,
        "responses": responses  # Include detailed responses
    })

# NEW AI ENDPOINTS - ADDED
@app.get("/ai-report/{framework}")
async def generate_comprehensive_ai_report(framework: str):
    """
    Generate a complete AI-powered risk assessment report
    Combines analysis, insights, recommendations, and executive summary
    """
    collection = collections_map.get(framework)
    if collection is None:
        raise HTTPException(status_code=400, detail="Invalid framework")

    # Fetch all assessment data
    cursor = collection.find({})
    total_controls = 0
    total_score = 0
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

        if 1 <= likelihood <= 5 and 1 <= impact <= 5:
            matrix[f"{likelihood},{impact}"] += 1

    if total_controls == 0:
        raise HTTPException(status_code=404, detail="No assessment data found")

    avg_score = total_score / total_controls

    # Generate comprehensive AI analysis
    ai_report = await generate_full_ai_report(responses, total_controls, avg_score, framework, dict(matrix))

    return JSONResponse(content={
        "report_metadata": {
            "framework": framework.upper(),
            "generated_at": datetime.now().isoformat(),
            "total_controls_analyzed": total_controls,
            "report_type": "Comprehensive AI Risk Assessment"
        },
        "executive_dashboard": {
            "total_controls": total_controls,
            "high_risk": len([r for r in responses if r['score'] >= 15]),
            "medium_risk": len([r for r in responses if 8 <= r['score'] < 15]),
            "low_risk": len([r for r in responses if r['score'] < 8]),
            "average_score": round(avg_score, 2),
            "risk_matrix": dict(matrix)
        },
        "detailed_responses": responses,
        "ai_comprehensive_report": ai_report
    })

# NEW PDF ENDPOINT - ADDED
from weasyprint import HTML
import markdown2
from PyPDF2 import PdfMerger

@app.get("/ai-report/{framework}/pdf")
async def generate_pdf_report(framework: str):
    collection = collections_map.get(framework)
    if collection is None:
        raise HTTPException(status_code=400, detail="Invalid framework")

    # Step 1: Fetch Data
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
        raise HTTPException(status_code=404, detail="No assessment data found")

    avg_score = total_score / total_controls
    ai_report = await generate_full_ai_report(responses, total_controls, avg_score, framework, dict(matrix))

    # Step 2: Generate Executive Summary as PDF using WeasyPrint
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

    # Step 3: Generate rest of PDF using ReportLab
    temp_report_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    doc = SimpleDocTemplate(temp_report_pdf.name, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=24, spaceAfter=30)
    story.append(Paragraph(f"{framework.upper()} Risk Assessment Report", title_style))
    story.append(Spacer(1, 20))

    # Risk Statistics
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

    # Step 4: Merge both PDFs
    final_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    merger = PdfMerger()
    merger.append(temp_summary_pdf.name)   # Formatted Executive Summary
    merger.append(temp_report_pdf.name)    # Risk stats and top controls
    merger.write(final_pdf.name)
    merger.close()

    return FileResponse(
        final_pdf.name,
        media_type='application/pdf',
        filename=f"{framework}_risk_assessment_report.pdf"
    )

@app.get("/health/openrouter")
async def check_openrouter_health():
    """
    Test OpenRouter API connectivity
    """
    try:
        response = requests.post(
            url=OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            data=json.dumps({
                "model": DEEPSEEK_MODEL,
                "messages": [
                    {
                        "role": "user",
                        "content": "Hello, this is a connectivity test."
                    }
                ],
                "max_tokens": 10
            }),
            timeout=10
        )
        
        if response.status_code == 200:
            return {
                "status": "healthy",
                "model": DEEPSEEK_MODEL,
                "provider": "OpenRouter",
                "response_preview": response.json()["choices"][0]["message"]["content"][:50]
            }
        else:
            return {"status": "unhealthy", "error": f"API returned {response.status_code}"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
