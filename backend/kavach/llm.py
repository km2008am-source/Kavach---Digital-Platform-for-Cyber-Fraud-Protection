"""One JSON-returning LLM wrapper. Every LLM call in Kavach goes through `complete_json()`.

Targets any OpenAI-compatible `/chat/completions` endpoint. Callers always catch
`LLMError` and fall back to a rules-only answer, so the LLM is never a single point
of failure for a verdict.
"""
import asyncio
import json

import httpx
from tenacity import AsyncRetrying, retry_if_exception, stop_after_attempt, wait_exponential_jitter

from kavach.analysis.settings import settings


class LLMError(Exception):
    """The LLM was not configured, unreachable, too slow, or returned no usable JSON."""


_client: httpx.AsyncClient | None = None
_client_loop: asyncio.AbstractEventLoop | None = None


def _get_client() -> httpx.AsyncClient:
    # One reused client per event loop (connection pooling). A client's connections belong to the
    # loop that opened them, so a second asyncio.run() (CLI, evaluation) must not reuse it.
    # Member 1 can call `aclose()` from the app lifespan.
    global _client, _client_loop
    loop = asyncio.get_running_loop()
    if _client is None or _client.is_closed or _client_loop is not loop:
        _client, _client_loop = httpx.AsyncClient(), loop
    return _client


async def aclose() -> None:
    if _client is not None:
        await _client.aclose()


def _transient(exc: BaseException) -> bool:
    if isinstance(exc, (httpx.TransportError, httpx.TimeoutException)):
        return True
    return isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code in (429, 500, 502, 503, 504)


def quote_untrusted(text: str, tag: str = "message") -> str:
    """Wrap user-supplied text in tags so the model treats it as data.

    A scam message could contain `</message>` to break out of the quote and smuggle
    instructions; neutralise any copy of the tag inside the text first.
    """
    safe = text.replace(f"<{tag}>", f"<{tag}_>").replace(f"</{tag}>", f"</{tag}_>")
    return f"<{tag}>{safe}</{tag}>"


def extract_json(text: str) -> dict:
    """Return the first JSON object in `text`, tolerating prose or code fences around it."""
    decoder = json.JSONDecoder()
    for i, ch in enumerate(text):
        if ch == "{":
            try:
                obj, _ = decoder.raw_decode(text, i)
            except json.JSONDecodeError:
                continue
            if isinstance(obj, dict):
                return obj
    raise LLMError("no JSON object in reply")


async def complete_json(system: str, user: str, timeout: float = 12) -> dict:
    if not (settings.LLM_BASE_URL and settings.LLM_MODEL):
        raise LLMError("LLM not configured")
    payload = {"model": settings.LLM_MODEL, "temperature": 0.2,
               "messages": [{"role": "system", "content": system},
                            {"role": "user", "content": user}]}
    headers = {"Authorization": f"Bearer {settings.LLM_API_KEY}"}
    url = settings.LLM_BASE_URL.rstrip("/") + "/chat/completions"
    try:
        # Two attempts at most: the whole verdict has a 10 s budget.
        async for attempt in AsyncRetrying(stop=stop_after_attempt(2),
                                           wait=wait_exponential_jitter(multiplier=0.3, max=1),
                                           retry=retry_if_exception(_transient), reraise=True):
            with attempt:
                r = await _get_client().post(url, headers=headers, json=payload, timeout=timeout)
                r.raise_for_status()
        text = r.json()["choices"][0]["message"]["content"]
    except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as e:
        # Never include the API key or the request body in the error.
        raise LLMError(f"{type(e).__name__}") from e
    return extract_json(text)
