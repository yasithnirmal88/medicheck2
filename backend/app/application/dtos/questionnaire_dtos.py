from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class QuestionOptionResponse(BaseModel):
    id: str
    code: str
    text: str
    value: str
    score_value: float
    severity: str
    color_hex: str | None = None
    display_order: int = 0

    model_config = {"from_attributes": True}


class QuestionResponse(BaseModel):
    id: str
    code: str
    text: str | dict[str, Any]
    question_type: str
    description: str | None = None
    tooltip: str | None = None
    medical_notes: str | None = None
    evidence_ref: str | None = None
    order_index: int = 0
    priority: int = 3
    difficulty: str = "basic"
    is_required: bool = False
    validation_rules: dict[str, Any] = {}
    scoring_weight: float = 1.0
    options: list[QuestionOptionResponse] = []

    model_config = {"from_attributes": True}

    @classmethod
    def from_entity(
        cls, question: Any, options: list[Any] | None = None
    ) -> QuestionResponse:
        data = question.to_dict() if hasattr(question, "to_dict") else question
        opts = []
        if options is not None:
            opts = [
                QuestionOptionResponse(**o.to_dict() if hasattr(o, "to_dict") else o)
                for o in options
            ]
        return cls(**data, options=opts)


class QuestionGroupResponse(BaseModel):
    id: str
    code: str
    name: str
    description: str | None = None
    display_order: int = 0
    questions: list[QuestionResponse] = []

    model_config = {"from_attributes": True}


class QuestionnaireTemplateResponse(BaseModel):
    id: str
    code: str
    name: str
    description: str | None = None
    body_system_id: str | None = None
    target_audience: str = "all"
    estimated_time_minutes: int = 10
    is_active: bool = True
    version: int = 1

    model_config = {"from_attributes": True}


class StartSessionRequest(BaseModel):
    template_id: str | None = None
    device_info: str | None = None
    metadata: dict[str, Any] = {}


class StartSessionResponse(BaseModel):
    session_id: str
    status: str = "active"
    current_question: QuestionResponse | None = None
    message: str = "Session started successfully"


class SaveAnswerRequest(BaseModel):
    question_id: str
    response_value: dict[str, Any] = Field(default_factory=dict)
    time_taken_seconds: int = 0
    is_skipped: bool = False


class AnswerResponse(BaseModel):
    id: str
    question_id: str
    question_code: str
    response_value: dict[str, Any]
    score_value: float
    is_skipped: bool
    time_taken_seconds: int

    model_config = {"from_attributes": True}


class SaveAnswerResponse(BaseModel):
    answer: AnswerResponse
    next_question: QuestionResponse | None = None

    model_config = {"from_attributes": True}


class SessionProgressResponse(BaseModel):
    session_id: str
    current_section: str | None = None
    completed_questions: int = 0
    total_questions: int = 0
    answered_questions: int = 0
    skipped_questions: int = 0
    estimated_time_remaining: int = 0
    completion_percentage: float = 0.0

    model_config = {"from_attributes": True}


class AssessmentSessionResponse(BaseModel):
    id: str
    status: str
    current_question: QuestionResponse | None = None
    progress: SessionProgressResponse | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None

    model_config = {"from_attributes": True}


class SubmitSessionResponse(BaseModel):
    session_id: str
    status: str = "completed"
    message: str = "Assessment completed successfully"
    score_summary: dict[str, Any] | None = None
