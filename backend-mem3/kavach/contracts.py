# backend/kavach/contracts.py  (frozen at H2; changes need all three members)
from enum import Enum
from typing import Optional, Literal
from pydantic import BaseModel, Field

Lang = Literal["ta", "en", "hi"]

class InputType(str, Enum):
    text = "text"; url = "url"; image = "image"; apk = "apk"; transcript = "transcript"

class ScamType(str, Enum):
    digital_arrest = "digital_arrest"; kyc_update = "kyc_update"; upi_collect = "upi_collect"
    job_offer = "job_offer"; courier_customs = "courier_customs"; investment = "investment"
    fake_scheme = "fake_scheme"; lottery_prize = "lottery_prize"; loan_app = "loan_app"
    malicious_apk = "malicious_apk"; phishing_link = "phishing_link"
    unknown = "unknown"; not_scam = "not_scam"

class RedFlag(BaseModel):
    code: str          # e.g. "urgency", "otp_request", "lookalike_domain", "apk_sms_permission"
    label_en: str      # plain-English explanation shown to the user

class Entities(BaseModel):
    phones: list[str] = []
    urls: list[str] = []
    upi_ids: list[str] = []
    amounts: list[str] = []

class LinkCheck(BaseModel):
    url: str
    domain: str
    blocklisted: bool = False
    sources: list[str] = []            # e.g. ["safe_browsing", "virustotal"]
    lookalike_of: Optional[str] = None # e.g. "sbi.co.in"
    domain_age_days: Optional[int] = None

class ApkReport(BaseModel):
    sha256: str
    package: Optional[str] = None
    app_name: Optional[str] = None
    permissions: list[str] = []
    dangerous_combo: bool = False      # SMS read + accessibility + overlay
    vt_malicious: Optional[int] = None # engines flagging it; None = unknown hash

class AnalysisRequest(BaseModel):
    request_id: str
    channel: Literal["whatsapp", "call", "web"]
    input_type: InputType
    text: Optional[str] = None         # message text, OCR output is added by M2
    file_path: Optional[str] = None    # image or APK on local disk
    language: Lang = "en"
    district: Optional[str] = None     # user-chosen, never GPS
    claimed_caller: Optional[str] = None  # Call Shield: number that called

class AnalysisResult(BaseModel):
    request_id: str
    risk_level: Literal["low", "medium", "high"]
    risk_score: int = Field(ge=0, le=100)
    scam_type: ScamType
    red_flags: list[RedFlag] = []
    explanation_en: str                # 2-3 short sentences; M1 translates
    recommended_action: Literal["ignore", "report_chakshu", "call_1930",
                                "do_not_install", "verify_official", "none"]
    entities: Entities = Entities()
    links: list[LinkCheck] = []
    apk: Optional[ApkReport] = None
    confidence: Literal["normal", "lower"] = "normal"  # "lower" if LLM was unavailable
    latency_ms: int = 0

class EvidenceExtraction(BaseModel):
    transaction_id: Optional[str] = None
    amount: Optional[str] = None
    datetime: Optional[str] = None     # as printed on the receipt
    payee_upi: Optional[str] = None
    payee_name: Optional[str] = None
    bank_name: Optional[str] = None
    scammer_phone: Optional[str] = None
    missing_fields: list[str] = []

class CallScreenResult(BaseModel):
    call_sid: str
    caller_number: str
    transcript: Optional[str] = None
    hung_up_without_reason: bool = False
    claimed_org: Optional[str] = None       # e.g. "SBI", "CBI", "FedEx"
    official_number_match: Optional[bool] = None
    analysis: Optional[AnalysisResult] = None

class SimTurnRequest(BaseModel):
    session_id: str
    user_message: str

class SimTurnResponse(BaseModel):
    bot_message: str
    tactics: list[Literal["urgency", "authority", "isolation", "fear", "secrecy", "payment_push"]]
    user_turn_score: int               # 0-10: did the user resist this turn?
    finished: bool
    debrief: Optional[str] = None
    final_score: Optional[int] = None  # 0-100 resilience score

class PulseAlert(BaseModel):
    cluster_id: str
    label: str                         # "courier-customs scam, Tamil"
    scam_type: ScamType
    district: str
    report_count: int
    distinct_reporters: int
    window_hours: int
    confidence: Literal["emerging", "confirmed"]
    sample_text: str                   # normalised, no personal data
