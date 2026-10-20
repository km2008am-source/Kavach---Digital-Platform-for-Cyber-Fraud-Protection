# M2 owns llm.py. This is the guide's own wrapper (section 7-G) so Member 3's simulator can run.
import httpx, json, re
from kavach.config import settings


class LLMError(Exception): ...


async def complete_json(system: str, user: str, timeout: float = 12) -> dict:
    if not settings.LLM_BASE_URL or not settings.LLM_API_KEY:
        raise LLMError("LLM not configured")
    payload = {"model": settings.LLM_MODEL, "temperature": 0.2,
               "messages": [{"role": "system", "content": system},
                            {"role": "user", "content": user}]}
    try:
        async with httpx.AsyncClient(timeout=timeout) as c:
            r = await c.post(f"{settings.LLM_BASE_URL}/chat/completions",
                             headers={"Authorization": f"Bearer {settings.LLM_API_KEY}"}, json=payload)
            r.raise_for_status()
            text = r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        raise LLMError(str(e))
    m = re.search(r"\{.*\}", text, re.S)          # tolerate text around the JSON
    if not m:
        raise LLMError("no JSON in reply")
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError as e:
        raise LLMError(f"bad JSON: {e}")
