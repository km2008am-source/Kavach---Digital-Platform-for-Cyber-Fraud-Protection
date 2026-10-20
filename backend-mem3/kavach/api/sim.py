# Member 3: /api/sim/*. The three paths below are the frozen start and turn endpoints plus one
# addition, /api/sim/quiz, for the before/after quiz (flagged for the team in the handoff).
from typing import Literal

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from kavach.api.errors import ApiError, rate_limit
from kavach.contracts import SimTurnRequest, SimTurnResponse
from kavach.simulator import engine

router = APIRouter()


class StartRequest(BaseModel):
    language: Literal["en", "ta"] = "en"


class StartResponse(BaseModel):
    session_id: str
    bot_message: str
    tactics: list[str]
    max_turns: int
    quiz: list[dict]          # [{"id", "q"}], answers are never sent to the browser


class QuizRequest(BaseModel):
    session_id: str
    phase: Literal["pre", "post"]
    answers: list[str] = Field(max_length=10)


class QuizResponse(BaseModel):
    phase: str
    score: int                # percent correct


@router.post("/api/sim/start", response_model=StartResponse)
async def start(body: StartRequest, request: Request):
    rate_limit(request, "sim", limit=60)
    s, first = await engine.start(body.language)
    return StartResponse(session_id=s.id, bot_message=first["bot_message"], tactics=first["tactics"],
                         max_turns=s.max_turns, quiz=engine.quiz_questions(s))


@router.post("/api/sim/turn", response_model=SimTurnResponse)
async def turn(body: SimTurnRequest, request: Request):
    rate_limit(request, "sim", limit=60)
    msg = body.user_message.strip()
    if not msg:
        raise ApiError("empty_input", "Type or say something first.", 422)
    if len(msg) > 500:
        raise ApiError("message_too_long", "Please keep each reply under 500 characters.", 422)
    return await engine.turn(engine.get(body.session_id), msg)


@router.post("/api/sim/quiz", response_model=QuizResponse)
async def quiz(body: QuizRequest, request: Request):
    rate_limit(request, "sim", limit=60)
    score = engine.submit_quiz(engine.get(body.session_id), body.phase, body.answers)
    return QuizResponse(phase=body.phase, score=score)
