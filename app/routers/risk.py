from fastapi import APIRouter, HTTPException, Path
from fastapi.responses import JSONResponse, FileResponse
from collections import defaultdict
from datetime import datetime

from app.models.schemas import ResponseData
from app.core.config import collections_map
from app.services.ai_report import generate_full_ai_report
from app.utils.pdf_utils import create_pdf_report

router = APIRouter()

@router.post("/save-response/{framework}")
async def save_response(
    framework: str = Path(..., regex="^(iso|nist|cis)$"),
    data: ResponseData = ...
):
    collection = collections_map.get(framework)
    if collection is None:
        raise HTTPException(status_code=400, detail="Invalid framework")

    document = {
        "id": data.id,
        "question": data.question,
        "likelihood_scale": data.likelihood_scale,
        "impact_scale": data.impact_scale,
    }

    result = await collection.update_one(
        {"id": data.id},
        {"$set": document},
        upsert=True
    )

    return {"message": "Response saved", "upserted_id": str(result.upserted_id) if result.upserted_id else None}


@router.get("/dashboard/{framework}")
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
        "responses": responses
    })


@router.get("/ai-report/{framework}")
async def ai_report(framework: str):
    collection = collections_map.get(framework)
    if collection is None:
        raise HTTPException(status_code=400, detail="Invalid framework")

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


@router.get("/ai-report/{framework}/pdf")
async def pdf_report(framework: str):
    return await create_pdf_report(framework)
