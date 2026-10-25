"""Shared data models used across Kavach backend modules."""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    UNKNOWN = "unknown"


class IncomingMessage(BaseModel):
    sender: str
    message_id: str
    kind: str
    text: str = ""
    button_id: str | None = None
    media_id: str | None = None
    mime_type: str | None = None
    filename: str | None = None
    timestamp: str | None = None


class AnalysisRequest(BaseModel):
    text: str = ""
    language: str = "en"
    source: str = "whatsapp"
    media_path: str | None = None
    media_type: str | None = None
    user_id: str | None = None
    district: str | None = None  # explicitly user-selected; never GPS


class RedFlag(BaseModel):
    label: str
    explanation: str


class AnalysisResult(BaseModel):
    risk_level: RiskLevel
    scam_type: str = "unknown"
    explanation: str
    red_flags: list[RedFlag] = Field(default_factory=list)
    recommended_action: str = ""
    confidence: float | None = Field(default=None, ge=0, le=1)
    links: list[dict[str, Any]] = Field(default_factory=list)


class EvidenceSummary(BaseModel):
    transaction_id: str | None = None
    amount: str | None = None
    transaction_time: str | None = None
    payee_upi: str | None = None
    scammer_number: str | None = None
    additional_details: dict[str, str] = Field(default_factory=dict)


class CaseRecord(BaseModel):
    case_id: str
    user_id: str
    status: str = "open"
    evidence: EvidenceSummary = Field(default_factory=EvidenceSummary)
    acknowledgement_number: str | None = None


class ServiceEntry(BaseModel):
    name: str
    situation: str
    description: str
    official_url: str