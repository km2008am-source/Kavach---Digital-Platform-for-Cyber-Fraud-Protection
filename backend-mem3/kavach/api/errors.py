# Member 3: the one error format for every /api/* endpoint (section 5):
#   HTTP 4xx/5xx with {"error": "<code>", "message": "<human text>"}
# No raw exception text ever reaches a user (section 9).
import logging, time
from collections import defaultdict, deque

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException   # base class: also catches Starlette's own 404/405

log = logging.getLogger("kavach.api")


class ApiError(Exception):
    def __init__(self, code: str, message: str, status: int = 400):
        super().__init__(message)
        self.code, self.message, self.status = code, message, status


def _body(code: str, message: str) -> dict:
    return {"error": code, "message": message}


def _is_api(request: Request) -> bool:
    return request.url.path.startswith("/api/")


def install(app: FastAPI) -> None:
    from kavach.simulator.engine import SimError

    @app.exception_handler(ApiError)
    async def _api_error(request: Request, exc: ApiError):
        return JSONResponse(_body(exc.code, exc.message), status_code=exc.status)

    @app.exception_handler(SimError)
    async def _sim_error(request: Request, exc: SimError):
        return JSONResponse(_body(exc.code, exc.message), status_code=exc.status)

    @app.exception_handler(RequestValidationError)
    async def _invalid(request: Request, exc: RequestValidationError):
        if not _is_api(request):
            from fastapi.exception_handlers import request_validation_exception_handler
            return await request_validation_exception_handler(request, exc)
        return JSONResponse(_body("invalid_request", "That request was not understood. Please check it and try again."),
                            status_code=422)

    @app.exception_handler(HTTPException)
    async def _http(request: Request, exc: HTTPException):
        if not _is_api(request):
            from fastapi.exception_handlers import http_exception_handler
            return await http_exception_handler(request, exc)
        code = {404: "not_found", 405: "method_not_allowed", 403: "forbidden"}.get(exc.status_code, "error")
        return JSONResponse(_body(code, "That is not available."), status_code=exc.status_code)

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception):
        log.exception("unhandled error on %s", request.url.path)
        if _is_api(request):
            return JSONResponse(_body("server_error", "Something went wrong. Please try again."), status_code=500)
        return JSONResponse({"ok": False}, status_code=500)


# ---- tiny in-memory rate limiter: a public endpoint that spends LLM quota needs one -------------
_hits: dict[str, deque] = defaultdict(deque)


def client_key(request: Request) -> str:
    fwd = request.headers.get("x-forwarded-for", "")
    return fwd.split(",")[0].strip() or (request.client.host if request.client else "unknown")


def rate_limit(request: Request, bucket: str, limit: int, per_seconds: int = 60) -> None:
    key, now = f"{bucket}:{client_key(request)}", time.time()
    q = _hits[key]
    while q and now - q[0] > per_seconds:
        q.popleft()
    if len(q) >= limit:
        raise ApiError("rate_limited", "Too many requests. Please wait a minute and try again.", 429)
    q.append(now)
    if len(_hits) > 5000:   # keep memory bounded
        for k in [k for k, v in _hits.items() if not v or now - v[-1] > per_seconds]:
            _hits.pop(k, None)
