import json
import requests
from typing import List, Dict
from app.core.config import OPENROUTER_API_KEY, OPENROUTER_URL, DEEPSEEK_MODEL


def generate_ai_analysis(prompt: str) -> str:
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


def create_comprehensive_report_prompt(
    responses: List[Dict], total_controls: int, avg_score: float, framework: str, matrix: Dict
) -> str:
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
2. **DETAILED RISK ANALYSIS**
3. **PRIORITY ACTION PLAN**
4. **COMPLIANCE AND GOVERNANCE**
5. **RESOURCE ALLOCATION GUIDANCE**
6. **MONITORING AND METRICS**

Format as a professional executive report suitable for board presentation.
"""
    return prompt


async def generate_full_ai_report(responses, total_controls, avg_score, framework, matrix):
    prompt = create_comprehensive_report_prompt(responses, total_controls, avg_score, framework, matrix)
    ai_analysis = generate_ai_analysis(prompt)

    high_risk_count = len([r for r in responses if r['score'] >= 15])
    medium_risk_count = len([r for r in responses if 8 <= r['score'] < 15])
    low_risk_count = len([r for r in responses if r['score'] < 8])
    high_risk_percentage = (high_risk_count / total_controls * 100) if total_controls > 0 else 0

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

    anomalies = []
    extreme_scores = [r for r in responses if r['score'] >= 20]
    if extreme_scores:
        anomalies.append(f"🚨 {len(extreme_scores)} controls with critical risk scores (≥20)")

    inconsistent_patterns = [r for r in responses if r['impact_scale'] >= 4 and r['likelihood_scale'] <= 2]
    if len(inconsistent_patterns) > total_controls * 0.3:
        anomalies.append("⚠️ High number of high-impact, low-likelihood assessments detected")

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
