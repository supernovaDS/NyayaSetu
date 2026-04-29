from pydantic import BaseModel, Field
from enum import Enum


class ActionType(str, Enum):
    compliance = "compliance"
    appeal = "appeal"
    review = "review"


class ContemptRiskLevel(str, Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"


class ReviewerRole(str, Enum):
    uploader = "uploader"
    legal_reviewer = "legal_reviewer"
    department_officer = "department_officer"
    approving_authority = "approving_authority"
    admin = "admin"


class ExtractedData(BaseModel):
    case_title: str = ""
    case_number: str = ""
    date_of_order: str = ""
    state_role: str = ""
    parties: list[str] = Field(default_factory=list)
    directives: list[str] = Field(default_factory=list)
    timelines: list[str] = Field(default_factory=list)
    confidence: float = Field(0.0, ge=0.0, le=1.0)


class SourceEvidence(BaseModel):
    page: int = 0
    quote: str = ""
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    bbox: list[float] = Field(default_factory=list)


class ReviewFlag(BaseModel):
    severity: str = "info"
    title: str = ""
    detail: str = ""


class ReviewMeta(BaseModel):
    case_category: str = "General"
    readiness_score: int = Field(0, ge=0, le=100)
    flags: list[ReviewFlag] = Field(default_factory=list)
    estimated_minutes_saved: int = 0
    pages_reduced: int = 0
    critical_pages_count: int = 0


class ActionPlan(BaseModel):
    action_type: ActionType = ActionType.review
    assigned_designation: str = ""
    calculated_deadline: str = ""
    days_remaining: int = -1
    reasoning: str = ""
    contempt_risk_level: ContemptRiskLevel = ContemptRiskLevel.low
    draft_file_note: str = ""
    deadline_rule_id: str = ""
    deadline_basis: str = ""
    deadline_override_reason: str = ""


class ExtractionResult(BaseModel):
    extracted_data: ExtractedData
    action_plan: ActionPlan
    critical_pages: list[int] = Field(default_factory=list)
    page_references: dict[str, int] = Field(default_factory=dict)
    source_evidence: dict[str, SourceEvidence] = Field(default_factory=dict)
    review_meta: ReviewMeta = Field(default_factory=ReviewMeta)
