from __future__ import annotations

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.body_system import BodySystem
from app.domain.entities.question import Question, QuestionType
from app.domain.entities.question_group import QuestionGroup
from app.domain.entities.question_option import QuestionOption
from app.domain.entities.questionnaire_template import QuestionnaireTemplate
from app.infrastructure.persistence.models.body_system import BodySystemModel
from app.infrastructure.persistence.repositories.sql_body_system_repository import (
    SQLBodySystemRepository,
)
from app.infrastructure.persistence.repositories.sql_question_group_repository import (
    SQLQuestionGroupRepository,
)
from app.infrastructure.persistence.repositories.sql_question_option_repository import (
    SQLQuestionOptionRepository,
)
from app.infrastructure.persistence.repositories.sql_question_repository import (
    SQLQuestionRepository,
)
from app.infrastructure.persistence.repositories.sql_questionnaire_repository import (
    SQLQuestionnaireRepository,
)
from app.infrastructure.seed_medical import seed_medical

BODY_SYSTEMS: list[dict[str, Any]] = [
    {
        "code": "CV",
        "name": "Cardiovascular",
        "description": "Heart and blood vessel health assessment",
        "icon": "heart",
        "color_hex": "#E74C3C",
        "display_order": 1,
        "is_core": True,
    },
    {
        "code": "KD",
        "name": "Kidney",
        "description": "Kidney function and urinary system assessment",
        "icon": "kidney",
        "color_hex": "#8E44AD",
        "display_order": 2,
        "is_core": True,
    },
    {
        "code": "EN",
        "name": "Endocrine",
        "description": "Hormonal and metabolic health assessment",
        "icon": "thyroid",
        "color_hex": "#F39C12",
        "display_order": 3,
        "is_core": True,
    },
    {
        "code": "DI",
        "name": "Digestive",
        "description": "Gastrointestinal and digestive health assessment",
        "icon": "stomach",
        "color_hex": "#27AE60",
        "display_order": 4,
        "is_core": False,
    },
    {
        "code": "RE",
        "name": "Respiratory",
        "description": "Lung and respiratory health assessment",
        "icon": "lungs",
        "color_hex": "#3498DB",
        "display_order": 5,
        "is_core": False,
    },
    {
        "code": "MU",
        "name": "Musculoskeletal",
        "description": "Bone, joint, and muscle health assessment",
        "icon": "bone",
        "color_hex": "#E67E22",
        "display_order": 6,
        "is_core": False,
    },
    {
        "code": "NE",
        "name": "Neurological",
        "description": "Brain and nervous system health assessment",
        "icon": "brain",
        "color_hex": "#9B59B6",
        "display_order": 7,
        "is_core": False,
    },
    {
        "code": "LI",
        "name": "Liver",
        "description": "Liver function and hepatic health assessment",
        "icon": "liver",
        "color_hex": "#2ECC71",
        "display_order": 8,
        "is_core": False,
    },
    {
        "code": "BL",
        "name": "Blood",
        "description": "Hematological health assessment",
        "icon": "droplet",
        "color_hex": "#E74C3C",
        "display_order": 9,
        "is_core": False,
    },
    {
        "code": "IM",
        "name": "Immune",
        "description": "Immune system and allergy assessment",
        "icon": "shield",
        "color_hex": "#1ABC9C",
        "display_order": 10,
        "is_core": False,
    },
    {
        "code": "MH",
        "name": "Mental Health",
        "description": "Mental and emotional well-being assessment",
        "icon": "brain",
        "color_hex": "#F1C40F",
        "display_order": 11,
        "is_core": False,
    },
    {
        "code": "SK",
        "name": "Skin",
        "description": "Skin health and dermatological assessment",
        "icon": "droplet",
        "color_hex": "#E91E63",
        "display_order": 12,
        "is_core": False,
    },
    {
        "code": "EY",
        "name": "Eye",
        "description": "Vision and eye health assessment",
        "icon": "eye",
        "color_hex": "#00BCD4",
        "display_order": 13,
        "is_core": False,
    },
    {
        "code": "FH",
        "name": "Female Health",
        "description": "Female reproductive and breast health assessment",
        "icon": "female",
        "color_hex": "#FF4081",
        "display_order": 14,
        "is_core": False,
    },
    {
        "code": "MA",
        "name": "Male Health",
        "description": "Male reproductive health assessment",
        "icon": "male",
        "color_hex": "#448AFF",
        "display_order": 15,
        "is_core": False,
    },
    {
        "code": "SH",
        "name": "Sexual Health",
        "description": "Sexual health and STI assessment",
        "icon": "heartbeat",
        "color_hex": "#FF5722",
        "display_order": 16,
        "is_core": False,
    },
    {
        "code": "CA",
        "name": "Cancer Screening",
        "description": "Cancer risk screening assessment",
        "icon": "shield",
        "color_hex": "#795548",
        "display_order": 17,
        "is_core": True,
    },
]


CARDIOVASCULAR_GROUPS: list[dict[str, Any]] = [
    {
        "code": "CV_BASIC",
        "name": "Basic Information",
        "description": "Basic demographic and health info",
        "display_order": 1,
    },
    {
        "code": "CV_SYMPTOMS",
        "name": "Cardiovascular Symptoms",
        "description": "Current symptoms assessment",
        "display_order": 2,
    },
    {
        "code": "CV_RISK_FACTORS",
        "name": "Risk Factors",
        "description": "Cardiovascular risk factor assessment",
        "display_order": 3,
    },
    {
        "code": "CV_FAMILY_HX",
        "name": "Family History",
        "description": "Family history of heart disease",
        "display_order": 4,
    },
    {
        "code": "CV_LIFESTYLE",
        "name": "Lifestyle",
        "description": "Lifestyle factors affecting heart health",
        "display_order": 5,
    },
]

KIDNEY_GROUPS: list[dict[str, Any]] = [
    {
        "code": "KD_BASIC",
        "name": "Basic Information",
        "description": "Basic kidney health info",
        "display_order": 1,
    },
    {
        "code": "KD_SYMPTOMS",
        "name": "Kidney Symptoms",
        "description": "Current kidney-related symptoms",
        "display_order": 2,
    },
    {
        "code": "KD_RISK_FACTORS",
        "name": "Risk Factors",
        "description": "Kidney disease risk factors",
        "display_order": 3,
    },
    {
        "code": "KD_LIFESTYLE",
        "name": "Lifestyle",
        "description": "Lifestyle and kidney health",
        "display_order": 4,
    },
]


def _cv_questions(cv_id: str, groups: dict[str, str]) -> list[dict[str, Any]]:
    return [
        {
            "group_id": groups["CV_BASIC"],
            "code": "cv_age",
            "text": "What is your age?",
            "qtype": QuestionType.NUMERIC,
            "order": 1,
            "required": True,
            "validation_rules": {"min": 1, "max": 120},
        },
        {
            "group_id": groups["CV_BASIC"],
            "code": "cv_gender",
            "text": "What is your gender?",
            "qtype": QuestionType.SINGLE_CHOICE,
            "order": 2,
            "required": True,
        },
        {
            "group_id": groups["CV_SYMPTOMS"],
            "code": "cv_chest_pain",
            "text": "Do you experience chest pain or discomfort?",
            "qtype": QuestionType.YES_NO,
            "order": 1,
            "required": True,
        },
        {
            "group_id": groups["CV_SYMPTOMS"],
            "code": "cv_shortness_breath",
            "text": "Do you experience shortness of breath during normal activities?",
            "qtype": QuestionType.YES_NO,
            "order": 2,
            "required": True,
        },
        {
            "group_id": groups["CV_SYMPTOMS"],
            "code": "cv_palpitations",
            "text": "Do you feel heart palpitations or irregular heartbeats?",
            "qtype": QuestionType.YES_NO,
            "order": 3,
            "required": True,
        },
        {
            "group_id": groups["CV_SYMPTOMS"],
            "code": "cv_dizziness",
            "text": "Do you experience dizziness or fainting spells?",
            "qtype": QuestionType.YES_NO,
            "order": 4,
            "required": False,
        },
        {
            "group_id": groups["CV_SYMPTOMS"],
            "code": "cv_swelling",
            "text": "Do you have swelling in your feet, ankles, or legs?",
            "qtype": QuestionType.YES_NO,
            "order": 5,
            "required": True,
        },
        {
            "group_id": groups["CV_RISK_FACTORS"],
            "code": "cv_blood_pressure",
            "text": "Do you have high blood pressure?",
            "qtype": QuestionType.YES_NO,
            "order": 1,
            "required": True,
        },
        {
            "group_id": groups["CV_RISK_FACTORS"],
            "code": "cv_systolic_bp",
            "text": "What is your typical systolic blood pressure?",
            "qtype": QuestionType.NUMERIC,
            "order": 2,
            "required": False,
            "validation_rules": {"min": 60, "max": 300},
        },
        {
            "group_id": groups["CV_RISK_FACTORS"],
            "code": "cv_diastolic_bp",
            "text": "What is your typical diastolic blood pressure?",
            "qtype": QuestionType.NUMERIC,
            "order": 3,
            "required": False,
            "validation_rules": {"min": 30, "max": 200},
        },
        {
            "group_id": groups["CV_RISK_FACTORS"],
            "code": "cv_cholesterol",
            "text": "Do you have high cholesterol?",
            "qtype": QuestionType.YES_NO,
            "order": 4,
            "required": True,
        },
        {
            "group_id": groups["CV_RISK_FACTORS"],
            "code": "cv_ldl_level",
            "text": "What is your LDL cholesterol level (mg/dL)?",
            "qtype": QuestionType.NUMERIC,
            "order": 5,
            "required": False,
            "validation_rules": {"min": 10, "max": 500},
        },
        {
            "group_id": groups["CV_RISK_FACTORS"],
            "code": "cv_hdl_level",
            "text": "What is your HDL cholesterol level (mg/dL)?",
            "qtype": QuestionType.NUMERIC,
            "order": 6,
            "required": False,
            "validation_rules": {"min": 5, "max": 200},
        },
        {
            "group_id": groups["CV_RISK_FACTORS"],
            "code": "cv_diabetes",
            "text": "Do you have diabetes?",
            "qtype": QuestionType.YES_NO,
            "order": 7,
            "required": True,
        },
        {
            "group_id": groups["CV_RISK_FACTORS"],
            "code": "cv_bmi",
            "text": "What is your height (cm) and weight (kg)?",
            "qtype": QuestionType.DECIMAL,
            "order": 8,
            "required": False,
            "validation_rules": {"min": 10, "max": 500},
        },
        {
            "group_id": groups["CV_FAMILY_HX"],
            "code": "cv_family_heart",
            "text": "Does anyone in your immediate family have heart disease?",
            "qtype": QuestionType.YES_NO,
            "order": 1,
            "required": True,
        },
        {
            "group_id": groups["CV_FAMILY_HX"],
            "code": "cv_family_relative",
            "text": "Which relative has heart disease?",
            "qtype": QuestionType.SINGLE_CHOICE,
            "order": 2,
            "required": False,
        },
        {
            "group_id": groups["CV_LIFESTYLE"],
            "code": "cv_smoking",
            "text": "Do you smoke or use tobacco products?",
            "qtype": QuestionType.YES_NO,
            "order": 1,
            "required": True,
        },
        {
            "group_id": groups["CV_LIFESTYLE"],
            "code": "cv_cigarettes_per_day",
            "text": "How many cigarettes do you smoke per day?",
            "qtype": QuestionType.NUMERIC,
            "order": 2,
            "required": False,
            "validation_rules": {"min": 0, "max": 100},
        },
        {
            "group_id": groups["CV_LIFESTYLE"],
            "code": "cv_alcohol",
            "text": "How many alcoholic drinks do you consume per week?",
            "qtype": QuestionType.DROPDOWN,
            "order": 3,
            "required": True,
        },
        {
            "group_id": groups["CV_LIFESTYLE"],
            "code": "cv_exercise",
            "text": "How many minutes of moderate exercise do you get per week?",
            "qtype": QuestionType.NUMERIC,
            "order": 4,
            "required": True,
            "validation_rules": {"min": 0, "max": 3000},
        },
        {
            "group_id": groups["CV_LIFESTYLE"],
            "code": "cv_diet",
            "text": "How would you describe your diet?",
            "qtype": QuestionType.SINGLE_CHOICE,
            "order": 5,
            "required": True,
        },
        {
            "group_id": groups["CV_LIFESTYLE"],
            "code": "cv_stress",
            "text": "How would you rate your stress level?",
            "qtype": QuestionType.SLIDER,
            "order": 6,
            "required": True,
        },
    ]


def _kd_questions(kd_id: str, groups: dict[str, str]) -> list[dict[str, Any]]:
    return [
        {
            "group_id": groups["KD_BASIC"],
            "code": "kd_age",
            "text": "What is your age?",
            "qtype": QuestionType.NUMERIC,
            "order": 1,
            "required": True,
            "validation_rules": {"min": 1, "max": 120},
        },
        {
            "group_id": groups["KD_BASIC"],
            "code": "kd_gender",
            "text": "What is your gender?",
            "qtype": QuestionType.SINGLE_CHOICE,
            "order": 2,
            "required": True,
        },
        {
            "group_id": groups["KD_SYMPTOMS"],
            "code": "kd_frequent_urination",
            "text": "Do you experience frequent urination, especially at night?",
            "qtype": QuestionType.YES_NO,
            "order": 1,
            "required": True,
        },
        {
            "group_id": groups["KD_SYMPTOMS"],
            "code": "kd_foamy_urine",
            "text": "Have you noticed foamy or bubbly urine?",
            "qtype": QuestionType.YES_NO,
            "order": 2,
            "required": True,
        },
        {
            "group_id": groups["KD_SYMPTOMS"],
            "code": "kd_blood_urine",
            "text": "Have you noticed blood in your urine?",
            "qtype": QuestionType.YES_NO,
            "order": 3,
            "required": True,
        },
        {
            "group_id": groups["KD_SYMPTOMS"],
            "code": "kd_swelling",
            "text": "Do you have swelling in your hands, feet, or face?",
            "qtype": QuestionType.YES_NO,
            "order": 4,
            "required": True,
        },
        {
            "group_id": groups["KD_SYMPTOMS"],
            "code": "kd_fatigue",
            "text": "Do you experience unexplained fatigue or weakness?",
            "qtype": QuestionType.YES_NO,
            "order": 5,
            "required": False,
        },
        {
            "group_id": groups["KD_SYMPTOMS"],
            "code": "kd_itching",
            "text": "Do you experience persistent itching?",
            "qtype": QuestionType.YES_NO,
            "order": 6,
            "required": False,
        },
        {
            "group_id": groups["KD_RISK_FACTORS"],
            "code": "kd_high_bp",
            "text": "Do you have high blood pressure?",
            "qtype": QuestionType.YES_NO,
            "order": 1,
            "required": True,
        },
        {
            "group_id": groups["KD_RISK_FACTORS"],
            "code": "kd_diabetes",
            "text": "Do you have diabetes?",
            "qtype": QuestionType.YES_NO,
            "order": 2,
            "required": True,
        },
        {
            "group_id": groups["KD_RISK_FACTORS"],
            "code": "kd_family_kidney",
            "text": "Does anyone in your family have kidney disease?",
            "qtype": QuestionType.YES_NO,
            "order": 3,
            "required": True,
        },
        {
            "group_id": groups["KD_RISK_FACTORS"],
            "code": "kd_egfr",
            "text": "What is your most recent eGFR value?",
            "qtype": QuestionType.NUMERIC,
            "order": 4,
            "required": False,
            "validation_rules": {"min": 0, "max": 200},
        },
        {
            "group_id": groups["KD_RISK_FACTORS"],
            "code": "kd_creatinine",
            "text": "What is your most recent serum creatinine level (mg/dL)?",
            "qtype": QuestionType.DECIMAL,
            "order": 5,
            "required": False,
            "validation_rules": {"min": 0.1, "max": 20},
        },
        {
            "group_id": groups["KD_LIFESTYLE"],
            "code": "kd_smoking",
            "text": "Do you smoke?",
            "qtype": QuestionType.YES_NO,
            "order": 1,
            "required": True,
        },
        {
            "group_id": groups["KD_LIFESTYLE"],
            "code": "kd_nsaid_use",
            "text": "Do you regularly take NSAID pain relievers (ibuprofen, naproxen)?",
            "qtype": QuestionType.YES_NO,
            "order": 2,
            "required": True,
        },
        {
            "group_id": groups["KD_LIFESTYLE"],
            "code": "kd_salt_intake",
            "text": "How would you describe your salt intake?",
            "qtype": QuestionType.DROPDOWN,
            "order": 3,
            "required": True,
        },
        {
            "group_id": groups["KD_LIFESTYLE"],
            "code": "kd_water_intake",
            "text": "How many glasses of water do you drink per day?",
            "qtype": QuestionType.NUMERIC,
            "order": 4,
            "required": True,
            "validation_rules": {"min": 0, "max": 50},
        },
    ]


COMMON_OPTIONS: dict[str, list[dict[str, Any]]] = {
    "yes_no": [
        {
            "code": "yes",
            "text": "Yes",
            "value": "yes",
            "score_value": 1.0,
            "severity": "moderate",
            "display_order": 1,
        },
        {
            "code": "no",
            "text": "No",
            "value": "no",
            "score_value": 0.0,
            "severity": "none",
            "display_order": 2,
        },
    ],
    "gender": [
        {
            "code": "male",
            "text": "Male",
            "value": "male",
            "score_value": 0.0,
            "display_order": 1,
        },
        {
            "code": "female",
            "text": "Female",
            "value": "female",
            "score_value": 0.0,
            "display_order": 2,
        },
        {
            "code": "other",
            "text": "Prefer not to say",
            "value": "other",
            "score_value": 0.0,
            "display_order": 3,
        },
    ],
    "alcohol": [
        {
            "code": "none",
            "text": "None",
            "value": "0",
            "score_value": 0.0,
            "display_order": 1,
        },
        {
            "code": "light",
            "text": "1-3 per week",
            "value": "1-3",
            "score_value": 0.5,
            "display_order": 2,
        },
        {
            "code": "moderate",
            "text": "4-7 per week",
            "value": "4-7",
            "score_value": 1.0,
            "severity": "mild",
            "display_order": 3,
        },
        {
            "code": "heavy",
            "text": "8-14 per week",
            "value": "8-14",
            "score_value": 2.0,
            "severity": "moderate",
            "display_order": 4,
        },
        {
            "code": "very_heavy",
            "text": "15+ per week",
            "value": "15+",
            "score_value": 3.0,
            "severity": "severe",
            "display_order": 5,
        },
    ],
    "diet": [
        {
            "code": "healthy",
            "text": "Healthy and balanced",
            "value": "healthy",
            "score_value": 0.0,
            "display_order": 1,
        },
        {
            "code": "moderate",
            "text": "Moderately healthy",
            "value": "moderate",
            "score_value": 0.5,
            "display_order": 2,
        },
        {
            "code": "unhealthy",
            "text": "Mostly unhealthy",
            "value": "unhealthy",
            "score_value": 1.5,
            "severity": "mild",
            "display_order": 3,
        },
        {
            "code": "very_unhealthy",
            "text": "Very unhealthy",
            "value": "very_unhealthy",
            "score_value": 2.5,
            "severity": "moderate",
            "display_order": 4,
        },
    ],
    "family_relative": [
        {
            "code": "parent",
            "text": "Parent",
            "value": "parent",
            "score_value": 1.0,
            "severity": "mild",
            "display_order": 1,
        },
        {
            "code": "sibling",
            "text": "Sibling",
            "value": "sibling",
            "score_value": 1.0,
            "severity": "mild",
            "display_order": 2,
        },
        {
            "code": "grandparent",
            "text": "Grandparent",
            "value": "grandparent",
            "score_value": 0.5,
            "display_order": 3,
        },
        {
            "code": "child",
            "text": "Child",
            "value": "child",
            "score_value": 1.5,
            "severity": "moderate",
            "display_order": 4,
        },
        {
            "code": "multiple",
            "text": "Multiple relatives",
            "value": "multiple",
            "score_value": 2.0,
            "severity": "moderate",
            "display_order": 5,
        },
    ],
    "salt_intake": [
        {
            "code": "low",
            "text": "Low salt intake",
            "value": "low",
            "score_value": 0.0,
            "display_order": 1,
        },
        {
            "code": "moderate",
            "text": "Moderate salt intake",
            "value": "moderate",
            "score_value": 0.5,
            "display_order": 2,
        },
        {
            "code": "high",
            "text": "High salt intake",
            "value": "high",
            "score_value": 1.5,
            "severity": "mild",
            "display_order": 3,
        },
    ],
}


async def seed_database(session: AsyncSession) -> None:
    # Check if already seeded
    stmt = select(func.count()).select_from(BodySystemModel)
    result = await session.execute(stmt)
    count = result.scalar() or 0
    if count > 0:
        return

    bs_repo = SQLBodySystemRepository(session)
    qg_repo = SQLQuestionGroupRepository(session)
    q_repo = SQLQuestionRepository(session)
    opt_repo = SQLQuestionOptionRepository(session)
    template_repo = SQLQuestionnaireRepository(session)

    body_system_map: dict[str, str] = {}

    # Seed body systems
    for bs_data in BODY_SYSTEMS:
        bs = BodySystem.create(
            code=bs_data["code"],
            name=bs_data["name"],
            description=bs_data["description"],
            icon=bs_data["icon"],
            color_hex=bs_data["color_hex"],
            display_order=bs_data["display_order"],
            is_core=bs_data["is_core"],
        )
        created = await bs_repo.create(bs)
        body_system_map[bs_data["code"]] = created.id

    # Seed cardiovascular groups + questions
    cv_id = body_system_map["CV"]
    cv_group_map: dict[str, str] = {}
    for g in CARDIOVASCULAR_GROUPS:
        qg = QuestionGroup.create(
            body_system_id=cv_id,
            code=g["code"],
            name=g["name"],
            description=g["description"],
            display_order=g["display_order"],
        )
        created = await qg_repo.create(qg)
        cv_group_map[g["code"]] = created.id

    for q_data in _cv_questions(cv_id, cv_group_map):
        q = Question.create(
            body_system_id=cv_id,
            question_group_id=q_data["group_id"],
            code=q_data["code"],
            question_type=q_data["qtype"],
            text=q_data["text"],
            order_index=q_data["order"],
            is_required=q_data.get("required", False),
            validation_rules=q_data.get("validation_rules"),
            scoring_weight=(
                1.0
                if q_data["qtype"]
                in (
                    QuestionType.YES_NO,
                    QuestionType.SINGLE_CHOICE,
                    QuestionType.DROPDOWN,
                )
                else 0.5
            ),
        )
        created = await q_repo.create(q)

        # Add options for choice questions
        opt_key = None
        if q_data["code"] == "cv_gender":
            opt_key = "gender"
        elif q_data["code"] == "cv_alcohol":
            opt_key = "alcohol"
        elif q_data["code"] == "cv_diet":
            opt_key = "diet"
        elif q_data["code"] == "cv_family_relative":
            opt_key = "family_relative"
        elif q_data["qtype"] == QuestionType.YES_NO:
            opt_key = "yes_no"

        if opt_key and opt_key in COMMON_OPTIONS:
            for opt_data in COMMON_OPTIONS[opt_key]:
                opt = QuestionOption.create(
                    question_id=created.id,
                    code=opt_data["code"],
                    text=opt_data["text"],
                    value=opt_data["value"],
                    score_value=opt_data.get("score_value", 0.0),
                    severity=opt_data.get("severity", "none"),
                    display_order=opt_data["display_order"],
                )
                await opt_repo.create(opt)

    # Seed kidney groups + questions
    kd_id = body_system_map["KD"]
    kd_group_map: dict[str, str] = {}
    for g in KIDNEY_GROUPS:
        qg = QuestionGroup.create(
            body_system_id=kd_id,
            code=g["code"],
            name=g["name"],
            description=g["description"],
            display_order=g["display_order"],
        )
        created = await qg_repo.create(qg)
        kd_group_map[g["code"]] = created.id

    for q_data in _kd_questions(kd_id, kd_group_map):
        q = Question.create(
            body_system_id=kd_id,
            question_group_id=q_data["group_id"],
            code=q_data["code"],
            question_type=q_data["qtype"],
            text=q_data["text"],
            order_index=q_data["order"],
            is_required=q_data.get("required", False),
            validation_rules=q_data.get("validation_rules"),
            scoring_weight=(
                1.0
                if q_data["qtype"]
                in (
                    QuestionType.YES_NO,
                    QuestionType.SINGLE_CHOICE,
                    QuestionType.DROPDOWN,
                )
                else 0.5
            ),
        )
        created = await q_repo.create(q)

        opt_key = None
        if q_data["code"] == "kd_gender":
            opt_key = "gender"
        elif q_data["code"] == "kd_salt_intake":
            opt_key = "salt_intake"
        elif q_data["qtype"] == QuestionType.YES_NO:
            opt_key = "yes_no"

        if opt_key and opt_key in COMMON_OPTIONS:
            for opt_data in COMMON_OPTIONS[opt_key]:
                opt = QuestionOption.create(
                    question_id=created.id,
                    code=opt_data["code"],
                    text=opt_data["text"],
                    value=opt_data["value"],
                    score_value=opt_data.get("score_value", 0.0),
                    severity=opt_data.get("severity", "none"),
                    display_order=opt_data["display_order"],
                )
                await opt_repo.create(opt)

    # Seed questionnaire templates
    cv_template = QuestionnaireTemplate.create(
        code="CV_ASSESS",
        name="Cardiovascular Health Assessment",
        description="Comprehensive cardiovascular risk assessment questionnaire",
        body_system_id=cv_id,
        target_audience="all",
        estimated_time_minutes=15,
    )
    await template_repo.create(cv_template)

    kd_template = QuestionnaireTemplate.create(
        code="KD_ASSESS",
        name="Kidney Health Assessment",
        description="Comprehensive kidney function risk assessment questionnaire",
        body_system_id=kd_id,
        target_audience="all",
        estimated_time_minutes=12,
    )
    await template_repo.create(kd_template)

    general_template = QuestionnaireTemplate.create(
        code="GENERAL_HEALTH",
        name="General Health Assessment",
        description="General health risk assessment covering all body systems",
        target_audience="all",
        estimated_time_minutes=30,
    )
    await template_repo.create(general_template)

    await session.commit()

    # Seed medical knowledge (indicators, conditions, recommendations, lab tests, evidence, links)
    await seed_medical(session, body_system_map)
