from fastapi import APIRouter
from app.core.config import OPENROUTER_API_KEY, OPENROUTER_URL, DEEPSEEK_MODEL
import requests
import json

router = APIRouter()

@router.get("/health/openrouter")
def check_openrouter():
    """
    Health check for OpenRouter API connectivity.
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
