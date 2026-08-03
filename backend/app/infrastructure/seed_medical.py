from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.clinical_indicator import ClinicalIndicator
from app.domain.entities.laboratory_test import LaboratoryTest
from app.domain.entities.recommendation import Recommendation
from app.infrastructure.persistence.models.clinical_indicator import (
    ClinicalIndicatorModel,
)
from app.infrastructure.persistence.models.evidence_reference import (
    EvidenceReferenceModel,
)
from app.infrastructure.persistence.models.laboratory_test import LaboratoryTestModel
from app.infrastructure.persistence.models.links import (
    ConditionLaboratoryTestLinkModel,
    ConditionRecommendationLinkModel,
    IndicatorConditionLinkModel,
    IndicatorEvidenceLinkModel,
    QuestionIndicatorLinkModel,
    QuestionOptionIndicatorLinkModel,
)
from app.infrastructure.persistence.models.possible_condition import (
    PossibleConditionModel,
)
from app.infrastructure.persistence.models.recommendation import RecommendationModel
from app.infrastructure.persistence.repositories.sql_clinical_indicator_repository import (
    SQLClinicalIndicatorRepository,
)
from app.infrastructure.persistence.repositories.sql_laboratory_test_repository import (
    SQLLaboratoryTestRepository,
)
from app.infrastructure.persistence.repositories.sql_recommendation_repository import (
    SQLRecommendationRepository,
)


# ---------------------------------------------------------------------------
# Conditions
# ---------------------------------------------------------------------------
def _conditions() -> list[dict[str, Any]]:
    return [
        # Cardiovascular conditions
        {"code": "CV_CAD",      "name": "Coronary Artery Disease",           "body_system_code": "CV", "severity": "high",     "icd10": "I25.10"},
        {"code": "CV_HTN",      "name": "Hypertension",                      "body_system_code": "CV", "severity": "moderate", "icd10": "I10"},
        {"code": "CV_HLD",      "name": "Hyperlipidemia",                     "body_system_code": "CV", "severity": "moderate", "icd10": "E78.5"},
        {"code": "CV_HF",       "name": "Heart Failure",                      "body_system_code": "CV", "severity": "high",     "icd10": "I50.9"},
        {"code": "CV_ARR",      "name": "Arrhythmia",                         "body_system_code": "CV", "severity": "moderate", "icd10": "I49.9"},
        {"code": "CV_AFIB",     "name": "Atrial Fibrillation",                "body_system_code": "CV", "severity": "high",     "icd10": "I48.91"},
        {"code": "CV_ANGINA",   "name": "Angina Pectoris",                    "body_system_code": "CV", "severity": "high",     "icd10": "I20.9"},
        {"code": "CV_PAD",      "name": "Peripheral Artery Disease",          "body_system_code": "CV", "severity": "moderate", "icd10": "I73.9"},
        {"code": "CV_CMP",      "name": "Cardiomyopathy",                     "body_system_code": "CV", "severity": "high",     "icd10": "I42.9"},
        {"code": "CV_OH",       "name": "Orthostatic Hypotension",            "body_system_code": "CV", "severity": "mild",     "icd10": "I95.1"},
        # Kidney conditions
        {"code": "KD_CKD",      "name": "Chronic Kidney Disease",             "body_system_code": "KD", "severity": "moderate", "icd10": "N18.9"},
        {"code": "KD_DN",       "name": "Diabetic Nephropathy",               "body_system_code": "KD", "severity": "high",     "icd10": "E11.21"},
        {"code": "KD_GN",       "name": "Glomerulonephritis",                 "body_system_code": "KD", "severity": "moderate", "icd10": "N05.9"},
        {"code": "KD_AKI",      "name": "Acute Kidney Injury",                "body_system_code": "KD", "severity": "high",     "icd10": "N17.9"},
        {"code": "KD_NS",       "name": "Nephrotic Syndrome",                 "body_system_code": "KD", "severity": "high",     "icd10": "N04.9"},
        {"code": "KD_PKD",      "name": "Polycystic Kidney Disease",          "body_system_code": "KD", "severity": "moderate", "icd10": "Q61.3"},
        {"code": "KD_KS",       "name": "Kidney Stones",                       "body_system_code": "KD", "severity": "mild",     "icd10": "N20.0"},
        {"code": "KD_UTI",      "name": "Urinary Tract Infection",            "body_system_code": "KD", "severity": "mild",     "icd10": "N39.0"},
        {"code": "KD_ANEMIA",   "name": "Anemia of Chronic Kidney Disease",   "body_system_code": "KD", "severity": "moderate", "icd10": "D63.1"},
        {"code": "KD_BCA",      "name": "Bladder Cancer",                     "body_system_code": "KD", "severity": "high",     "icd10": "C67.9"},
    ]


# ---------------------------------------------------------------------------
# Clinical Indicators
# ---------------------------------------------------------------------------
def _indicators() -> list[dict[str, Any]]:
    return [
        # ---- Cardiovascular ----
        {"key": "CV_CHEST_PAIN",      "name": "Chest Pain / Angina Equivalent",
         "body_system_code": "CV", "severity": "high",     "evidence_strength": "A", "confidence": 0.85},
        {"key": "CV_DYSPNEA",         "name": "Dyspnea on Exertion",
         "body_system_code": "CV", "severity": "moderate", "evidence_strength": "B", "confidence": 0.70},
        {"key": "CV_PALPITATIONS",    "name": "Palpitations / Irregular Heartbeat",
         "body_system_code": "CV", "severity": "moderate", "evidence_strength": "B", "confidence": 0.65},
        {"key": "CV_SYNCOPE",         "name": "Dizziness / Syncope",
         "body_system_code": "CV", "severity": "moderate", "evidence_strength": "C", "confidence": 0.50},
        {"key": "CV_EDEMA",           "name": "Peripheral Edema",
         "body_system_code": "CV", "severity": "moderate", "evidence_strength": "B", "confidence": 0.70},
        {"key": "CV_HYPERTENSION",    "name": "Hypertension (Self-Reported)",
         "body_system_code": "CV", "severity": "moderate", "evidence_strength": "A", "confidence": 0.80},
        {"key": "CV_HIGH_CHOL",       "name": "Hypercholesterolemia (Self-Reported)",
         "body_system_code": "CV", "severity": "moderate", "evidence_strength": "A", "confidence": 0.75},
        {"key": "CV_DIABETES",        "name": "Diabetes Mellitus (Self-Reported)",
         "body_system_code": "CV", "severity": "high",     "evidence_strength": "A", "confidence": 0.90},
        {"key": "CV_FAMILY_CAD",      "name": "Family History of Premature CAD",
         "body_system_code": "CV", "severity": "moderate", "evidence_strength": "A", "confidence": 0.75},
        {"key": "CV_TOBACCO",         "name": "Tobacco Use",
         "body_system_code": "CV", "severity": "high",     "evidence_strength": "A", "confidence": 0.90},
        {"key": "CV_ALCOHOL_EXCESS",  "name": "Excessive Alcohol Consumption",
         "body_system_code": "CV", "severity": "mild",     "evidence_strength": "B", "confidence": 0.60},
        {"key": "CV_SEDENTARY",       "name": "Sedentary Lifestyle",
         "body_system_code": "CV", "severity": "mild",     "evidence_strength": "A", "confidence": 0.70},
        {"key": "CV_POOR_DIET",       "name": "Poor Dietary Habits",
         "body_system_code": "CV", "severity": "mild",     "evidence_strength": "A", "confidence": 0.70},
        {"key": "CV_HIGH_STRESS",     "name": "High Perceived Stress",
         "body_system_code": "CV", "severity": "mild",     "evidence_strength": "B", "confidence": 0.55},
        # ---- Kidney ----
        {"key": "KD_NOCTURIA",        "name": "Nocturia / Frequent Urination",
         "body_system_code": "KD", "severity": "mild",     "evidence_strength": "C", "confidence": 0.50},
        {"key": "KD_PROTEINURIA",     "name": "Proteinuria (Foamy Urine)",
         "body_system_code": "KD", "severity": "moderate", "evidence_strength": "A", "confidence": 0.85},
        {"key": "KD_HEMATURIA",       "name": "Hematuria (Blood in Urine)",
         "body_system_code": "KD", "severity": "moderate", "evidence_strength": "B", "confidence": 0.70},
        {"key": "KD_EDEMA",           "name": "Peripheral / Periorbital Edema",
         "body_system_code": "KD", "severity": "moderate", "evidence_strength": "B", "confidence": 0.70},
        {"key": "KD_FATIGUE",         "name": "Unexplained Fatigue",
         "body_system_code": "KD", "severity": "mild",     "evidence_strength": "C", "confidence": 0.40},
        {"key": "KD_PRURITUS",        "name": "Persistent Pruritus (Itching)",
         "body_system_code": "KD", "severity": "mild",     "evidence_strength": "C", "confidence": 0.45},
        {"key": "KD_HTN_KIDNEY",      "name": "Hypertension (Kidney-Related)",
         "body_system_code": "KD", "severity": "moderate", "evidence_strength": "A", "confidence": 0.80},
        {"key": "KD_DM_KIDNEY",       "name": "Diabetes (Kidney-Related)",
         "body_system_code": "KD", "severity": "high",     "evidence_strength": "A", "confidence": 0.90},
        {"key": "KD_FAMILY_CKD",      "name": "Family History of Kidney Disease",
         "body_system_code": "KD", "severity": "moderate", "evidence_strength": "B", "confidence": 0.60},
        {"key": "KD_LOW_EGFR",        "name": "Reduced eGFR (<60)",
         "body_system_code": "KD", "severity": "high",     "evidence_strength": "A", "confidence": 0.95},
        {"key": "KD_HIGH_CREAT",      "name": "Elevated Serum Creatinine",
         "body_system_code": "KD", "severity": "moderate", "evidence_strength": "A", "confidence": 0.90},
        {"key": "KD_TOBACCO_KIDNEY",  "name": "Tobacco Use (Kidney Risk)",
         "body_system_code": "KD", "severity": "moderate", "evidence_strength": "A", "confidence": 0.80},
        {"key": "KD_NSAID",           "name": "Chronic NSAID Use",
         "body_system_code": "KD", "severity": "moderate", "evidence_strength": "A", "confidence": 0.75},
        {"key": "KD_HIGH_SALT",       "name": "High Sodium Intake",
         "body_system_code": "KD", "severity": "mild",     "evidence_strength": "B", "confidence": 0.55},
        {"key": "KD_LOW_INTAKE",      "name": "Inadequate Fluid Intake",
         "body_system_code": "KD", "severity": "mild",     "evidence_strength": "C", "confidence": 0.40},
    ]


# ---------------------------------------------------------------------------
# Evidence References (simulated PubMed / guideline references)
# ---------------------------------------------------------------------------
def _evidence_references() -> list[dict[str, Any]]:
    now = datetime.now(UTC)
    return [
        {
            "id": uuid.uuid4().hex,
            "title": "2024 ACC/AHA Guideline for the Management of Patients With Chronic Coronary Disease",
            "url": "https://doi.org/10.1016/j.jacc.2024.05.001",
            "source": "Journal of the American College of Cardiology",
            "evidence_level": "A",
            "created_at": now,
        },
        {
            "id": uuid.uuid4().hex,
            "title": "KDIGO 2024 Clinical Practice Guideline for the Evaluation and Management of Chronic Kidney Disease",
            "url": "https://doi.org/10.1016/j.kint.2024.01.001",
            "source": "Kidney International",
            "evidence_level": "A",
            "created_at": now,
        },
        {
            "id": uuid.uuid4().hex,
            "title": "ESC Guidelines for the Diagnosis and Management of Atrial Fibrillation",
            "url": "https://doi.org/10.1093/eurheartj/ehad190",
            "source": "European Heart Journal",
            "evidence_level": "A",
            "created_at": now,
        },
        {
            "id": uuid.uuid4().hex,
            "title": "Seventh Report of the Joint National Committee on Prevention, Detection, Evaluation, and Treatment of High Blood Pressure",
            "url": "https://doi.org/10.1001/jama.289.19.2560",
            "source": "JAMA",
            "evidence_level": "A",
            "created_at": now,
        },
        {
            "id": uuid.uuid4().hex,
            "title": "UK National Institute for Health and Care Excellence Guideline: Chronic Kidney Disease (NG203)",
            "url": "https://www.nice.org.uk/guidance/ng203",
            "source": "NICE",
            "evidence_level": "A",
            "created_at": now,
        },
    ]


# ---------------------------------------------------------------------------
# Link definitions: question_code/option_code -> indicator_key
# ---------------------------------------------------------------------------
def _question_indicator_links() -> list[tuple[str, str]]:
    return [
        ("cv_chest_pain",       "CV_CHEST_PAIN"),
        ("cv_shortness_breath",  "CV_DYSPNEA"),
        ("cv_palpitations",     "CV_PALPITATIONS"),
        ("cv_dizziness",        "CV_SYNCOPE"),
        ("cv_swelling",         "CV_EDEMA"),
        ("cv_blood_pressure",   "CV_HYPERTENSION"),
        ("cv_cholesterol",      "CV_HIGH_CHOL"),
        ("cv_diabetes",         "CV_DIABETES"),
        ("cv_family_heart",     "CV_FAMILY_CAD"),
        ("cv_smoking",          "CV_TOBACCO"),
        ("cv_exercise",         "CV_SEDENTARY"),
        ("cv_diet",             "CV_POOR_DIET"),
        ("cv_stress",           "CV_HIGH_STRESS"),
        ("kd_frequent_urination", "KD_NOCTURIA"),
        ("kd_foamy_urine",      "KD_PROTEINURIA"),
        ("kd_blood_urine",      "KD_HEMATURIA"),
        ("kd_swelling",         "KD_EDEMA"),
        ("kd_fatigue",          "KD_FATIGUE"),
        ("kd_itching",          "KD_PRURITUS"),
        ("kd_high_bp",          "KD_HTN_KIDNEY"),
        ("kd_diabetes",         "KD_DM_KIDNEY"),
        ("kd_family_kidney",    "KD_FAMILY_CKD"),
        ("kd_smoking",          "KD_TOBACCO_KIDNEY"),
        ("kd_nsaid_use",        "KD_NSAID"),
        ("kd_salt_intake",      "KD_HIGH_SALT"),
        ("kd_water_intake",     "KD_LOW_INTAKE"),
    ]


def _option_indicator_links() -> list[tuple[str, str, str]]:
    """(question_code, option_code, indicator_key)"""
    return [
        ("cv_alcohol",  "heavy",      "CV_ALCOHOL_EXCESS"),
        ("cv_alcohol",  "very_heavy",  "CV_ALCOHOL_EXCESS"),
        ("cv_diet",     "unhealthy",   "CV_POOR_DIET"),
        ("cv_diet",     "very_unhealthy", "CV_POOR_DIET"),
        ("kd_salt_intake", "high",     "KD_HIGH_SALT"),
    ]


def _indicator_condition_links() -> list[tuple[str, str]]:
    return [
        ("CV_CHEST_PAIN",     "CV_CAD"),
        ("CV_CHEST_PAIN",     "CV_ANGINA"),
        ("CV_DYSPNEA",        "CV_CAD"),
        ("CV_DYSPNEA",        "CV_HF"),
        ("CV_PALPITATIONS",   "CV_ARR"),
        ("CV_PALPITATIONS",   "CV_AFIB"),
        ("CV_SYNCOPE",        "CV_ARR"),
        ("CV_SYNCOPE",        "CV_OH"),
        ("CV_EDEMA",          "CV_HF"),
        ("CV_EDEMA",          "KD_CKD"),
        ("CV_HYPERTENSION",   "CV_HTN"),
        ("CV_HYPERTENSION",   "CV_CAD"),
        ("CV_HYPERTENSION",   "CV_HF"),
        ("CV_HIGH_CHOL",      "CV_HLD"),
        ("CV_HIGH_CHOL",      "CV_CAD"),
        ("CV_DIABETES",       "CV_CAD"),
        ("CV_DIABETES",       "CV_PAD"),
        ("CV_DIABETES",       "KD_DN"),
        ("CV_FAMILY_CAD",     "CV_CAD"),
        ("CV_FAMILY_CAD",     "CV_HLD"),
        ("CV_TOBACCO",        "CV_CAD"),
        ("CV_TOBACCO",        "CV_PAD"),
        ("CV_ALCOHOL_EXCESS", "CV_HTN"),
        ("CV_ALCOHOL_EXCESS", "CV_CMP"),
        ("CV_SEDENTARY",      "CV_CAD"),
        ("CV_SEDENTARY",      "CV_HTN"),
        ("CV_SEDENTARY",      "CV_HLD"),
        ("CV_POOR_DIET",      "CV_HLD"),
        ("CV_POOR_DIET",      "CV_CAD"),
        ("CV_HIGH_STRESS",    "CV_HTN"),
        ("CV_HIGH_STRESS",    "CV_CAD"),
        # Kidney indicator -> condition links
        ("KD_NOCTURIA",       "KD_CKD"),
        ("KD_NOCTURIA",       "KD_DN"),
        ("KD_NOCTURIA",       "KD_UTI"),
        ("KD_PROTEINURIA",    "KD_CKD"),
        ("KD_PROTEINURIA",    "KD_GN"),
        ("KD_PROTEINURIA",    "KD_NS"),
        ("KD_HEMATURIA",      "KD_CKD"),
        ("KD_HEMATURIA",      "KD_KS"),
        ("KD_HEMATURIA",      "KD_BCA"),
        ("KD_EDEMA",          "KD_CKD"),
        ("KD_EDEMA",          "KD_NS"),
        ("KD_EDEMA",          "CV_HF"),
        ("KD_FATIGUE",        "KD_CKD"),
        ("KD_FATIGUE",        "KD_ANEMIA"),
        ("KD_PRURITUS",       "KD_CKD"),
        ("KD_HTN_KIDNEY",     "KD_CKD"),
        ("KD_HTN_KIDNEY",     "CV_HTN"),
        ("KD_DM_KIDNEY",      "KD_CKD"),
        ("KD_DM_KIDNEY",      "KD_DN"),
        ("KD_FAMILY_CKD",     "KD_CKD"),
        ("KD_FAMILY_CKD",     "KD_PKD"),
        ("KD_LOW_EGFR",       "KD_CKD"),
        ("KD_LOW_EGFR",       "KD_AKI"),
        ("KD_HIGH_CREAT",     "KD_CKD"),
        ("KD_HIGH_CREAT",     "KD_AKI"),
        ("KD_TOBACCO_KIDNEY", "KD_CKD"),
        ("KD_TOBACCO_KIDNEY", "KD_BCA"),
        ("KD_NSAID",          "KD_CKD"),
        ("KD_NSAID",          "KD_AKI"),
        ("KD_HIGH_SALT",      "KD_CKD"),
        ("KD_HIGH_SALT",      "CV_HTN"),
        ("KD_LOW_INTAKE",     "KD_KS"),
        ("KD_LOW_INTAKE",     "KD_UTI"),
    ]


# ---------------------------------------------------------------------------
# Recommendations
# ---------------------------------------------------------------------------
def _recommendations() -> list[dict[str, Any]]:
    return [
        # CAD
        {"key": "REC_CAD_CARDIOLOGY",   "body_system_code": "CV", "category": "referral",
         "title": "Cardiology Referral",
         "text": "Refer to cardiology for comprehensive evaluation including stress testing or coronary angiography.",
         "priority": 10, "urgency": "urgent", "evidence_level": "A",
         "condition_code": "CV_CAD"},
        {"key": "REC_CAD_ASPIRIN",      "body_system_code": "CV", "category": "medication",
         "title": "Low-Dose Aspirin Therapy",
         "text": "Consider low-dose aspirin (75-100 mg daily) for secondary prevention of cardiovascular events.",
         "priority": 9, "urgency": "routine", "evidence_level": "A",
         "condition_code": "CV_CAD"},
        {"key": "REC_CAD_STATIN",       "body_system_code": "CV", "category": "medication",
         "title": "Statin Therapy",
         "text": "Initiate moderate-to-high intensity statin (atorvastatin 20-80 mg or rosuvastatin 10-40 mg daily) for LDL target <70 mg/dL.",
         "priority": 9, "urgency": "routine", "evidence_level": "A",
         "condition_code": "CV_CAD"},
        # Hypertension
        {"key": "REC_HTN_BP_MONITOR",   "body_system_code": "CV", "category": "monitoring",
         "title": "Home Blood Pressure Monitoring",
         "text": "Monitor blood pressure at home twice daily (morning and evening) and maintain a log for 7 days.",
         "priority": 8, "urgency": "routine", "evidence_level": "A",
         "condition_code": "CV_HTN"},
        {"key": "REC_HTN_ANTIHYPERTENSIVE", "body_system_code": "CV", "category": "medication",
         "title": "Antihypertensive Medication",
         "text": "Initiate or adjust antihypertensive therapy (ACEi/ARB as first-line) to achieve BP target <130/80 mmHg.",
         "priority": 9, "urgency": "routine", "evidence_level": "A",
         "condition_code": "CV_HTN"},
        {"key": "REC_HTN_LIFESTYLE",    "body_system_code": "CV", "category": "lifestyle",
         "title": "Hypertension Lifestyle Modification",
         "text": "Implement DASH diet, reduce sodium intake to <2g/day, limit alcohol, increase physical activity to 150 min/week, maintain healthy weight.",
         "priority": 8, "urgency": "routine", "evidence_level": "A",
         "condition_code": "CV_HTN"},
        # Hyperlipidemia
        {"key": "REC_HLD_LIPID_PANEL",  "body_system_code": "CV", "category": "testing",
         "title": "Comprehensive Lipid Panel",
         "text": "Order fasting lipid panel (total cholesterol, LDL, HDL, triglycerides) and calculate non-HDL cholesterol and apoB if indicated.",
         "priority": 7, "urgency": "routine", "evidence_level": "A",
         "condition_code": "CV_HLD"},
        {"key": "REC_HLD_DIET",         "body_system_code": "CV", "category": "lifestyle",
         "title": "Heart-Healthy Diet",
         "text": "Adopt a Mediterranean-style diet rich in fruits, vegetables, whole grains, lean protein, and healthy fats (olive oil, nuts).",
         "priority": 7, "urgency": "routine", "evidence_level": "A",
         "condition_code": "CV_HLD"},
        # Heart Failure
        {"key": "REC_HF_ECHO",          "body_system_code": "CV", "category": "testing",
         "title": "Echocardiogram",
         "text": "Order transthoracic echocardiogram to assess left ventricular ejection fraction and diastolic function.",
         "priority": 10, "urgency": "urgent", "evidence_level": "A",
         "condition_code": "CV_HF"},
        {"key": "REC_HF_CARDIOLOGY",    "body_system_code": "CV", "category": "referral",
         "title": "Heart Failure Cardiology Referral",
         "text": "Urgent cardiology referral for comprehensive heart failure management including GDMT optimization.",
         "priority": 10, "urgency": "urgent", "evidence_level": "A",
         "condition_code": "CV_HF"},
        {"key": "REC_HF_SODIUM_RESTRICT", "body_system_code": "CV", "category": "lifestyle",
         "title": "Sodium Restriction",
         "text": "Limit sodium intake to <2g/day and monitor daily weight to detect fluid retention early.",
         "priority": 8, "urgency": "routine", "evidence_level": "B",
         "condition_code": "CV_HF"},
        # Atrial Fibrillation
        {"key": "REC_AFIB_CARDIOLOGY",  "body_system_code": "CV", "category": "referral",
         "title": "Atrial Fibrillation Cardiology Referral",
         "text": "Refer to cardiology for rate/rhythm control strategy and CHA2DS2-VASc stroke risk assessment.",
         "priority": 10, "urgency": "urgent", "evidence_level": "A",
         "condition_code": "CV_AFIB"},
        {"key": "REC_AFIB_ANTICOAG",    "body_system_code": "CV", "category": "medication",
         "title": "Anticoagulation for Stroke Prevention",
         "text": "Assess CHA2DS2-VASc score; if >=2 in men or >=3 in women, initiate anticoagulation (DOAC preferred over warfarin).",
         "priority": 10, "urgency": "urgent", "evidence_level": "A",
         "condition_code": "CV_AFIB"},
        # Angina
        {"key": "REC_ANGINA_NITRATE",   "body_system_code": "CV", "category": "medication",
         "title": "Sublingual Nitroglycerin",
         "text": "Prescribe sublingual nitroglycerin (0.3-0.6 mg) for acute angina relief. Instruct to use at onset of chest pain and seek emergency care if pain persists >5 min.",
         "priority": 9, "urgency": "urgent", "evidence_level": "A",
         "condition_code": "CV_ANGINA"},
        {"key": "REC_ANGINA_CARDIOLOGY", "body_system_code": "CV", "category": "referral",
         "title": "Angina Cardiology Referral",
         "text": "Urgent cardiology referral for stress testing and consideration of revascularization.",
         "priority": 10, "urgency": "urgent", "evidence_level": "A",
         "condition_code": "CV_ANGINA"},
        # CKD
        {"key": "REC_CKD_NEPHROLOGY",   "body_system_code": "KD", "category": "referral",
         "title": "Nephrology Referral",
         "text": "Refer to nephrology for eGFR <30 mL/min/1.73m² or rapid decline in kidney function.",
         "priority": 10, "urgency": "urgent", "evidence_level": "A",
         "condition_code": "KD_CKD"},
        {"key": "REC_CKD_MONITORING",   "body_system_code": "KD", "category": "monitoring",
         "title": "CKD Monitoring",
         "text": "Monitor eGFR, serum creatinine, and urine ACR every 3-6 months. Measure serum potassium, bicarbonate, calcium, phosphate, PTH annually.",
         "priority": 8, "urgency": "routine", "evidence_level": "A",
         "condition_code": "KD_CKD"},
        {"key": "REC_CKD_ACEI",         "body_system_code": "KD", "category": "medication",
         "title": "ACE Inhibitor / ARB for CKD",
         "text": "Initiate ACE inhibitor or ARB for patients with CKD and albuminuria (ACR >30 mg/g) regardless of blood pressure.",
         "priority": 9, "urgency": "routine", "evidence_level": "A",
         "condition_code": "KD_CKD"},
        {"key": "REC_CKD_DIET",         "body_system_code": "KD", "category": "lifestyle",
         "title": "CKD Diet Modification",
         "text": "Restrict dietary protein to 0.8 g/kg/day, limit sodium to <2g/day, and adjust potassium and phosphate intake based on serum levels.",
         "priority": 7, "urgency": "routine", "evidence_level": "B",
         "condition_code": "KD_CKD"},
        # Diabetic Nephropathy
        {"key": "REC_DN_SGLT2",         "body_system_code": "KD", "category": "medication",
         "title": "SGLT2 Inhibitor for Diabetic Nephropathy",
         "text": "Initiate SGLT2 inhibitor (dapagliflozin 10 mg or empagliflozin 10 mg daily) to slow progression of diabetic kidney disease regardless of glycemic control.",
         "priority": 9, "urgency": "routine", "evidence_level": "A",
         "condition_code": "KD_DN"},
        {"key": "REC_DN_ENDOCRINE",     "body_system_code": "KD", "category": "referral",
         "title": "Endocrinology Referral for Diabetes Management",
         "text": "Refer to endocrinology for optimization of glycemic control in the setting of nephropathy.",
         "priority": 8, "urgency": "routine", "evidence_level": "C",
         "condition_code": "KD_DN"},
        # Kidney Stones
        {"key": "REC_KS_HYDRATION",     "body_system_code": "KD", "category": "lifestyle",
         "title": "Increase Fluid Intake for Kidney Stone Prevention",
         "text": "Increase water intake to achieve urine output of 2.5 L/day to reduce stone recurrence risk.",
         "priority": 7, "urgency": "routine", "evidence_level": "A",
         "condition_code": "KD_KS"},
        {"key": "REC_KS_UROLOGY",       "body_system_code": "KD", "category": "referral",
         "title": "Urology Referral for Kidney Stones",
         "text": "Refer to urology for stone analysis and metabolic evaluation if recurrent stone former.",
         "priority": 7, "urgency": "routine", "evidence_level": "C",
         "condition_code": "KD_KS"},
        # UTI
        {"key": "REC_UTI_CULTURE",      "body_system_code": "KD", "category": "testing",
         "title": "Urine Culture and Sensitivity",
         "text": "Obtain urine culture and sensitivity before starting empiric antibiotics for symptomatic UTI.",
         "priority": 8, "urgency": "routine", "evidence_level": "A",
         "condition_code": "KD_UTI"},
        {"key": "REC_UTI_ANTIBIOTIC",   "body_system_code": "KD", "category": "medication",
         "title": "Empiric Antibiotic Therapy for UTI",
         "text": "Initiate empiric antibiotics based on local resistance patterns: nitrofurantoin 100 mg BID x 5 days or TMP-SMX DS BID x 3 days.",
         "priority": 8, "urgency": "routine", "evidence_level": "A",
         "condition_code": "KD_UTI"},
        # General lifestyle
        {"key": "REC_SMOKING_CESSATION", "body_system_code": "CV", "category": "lifestyle",
         "title": "Smoking Cessation Counseling",
         "text": "Provide brief smoking cessation counseling (5 A's model). Offer pharmacotherapy (NRT, bupropion, varenicline) and refer to quitline.",
         "priority": 9, "urgency": "routine", "evidence_level": "A",
         "condition_code": None},
        {"key": "REC_EXERCISE",          "body_system_code": "CV", "category": "lifestyle",
         "title": "Physical Activity Prescription",
         "text": "Prescribe at least 150 minutes of moderate-intensity aerobic activity per week (30 min, 5 days/week) plus resistance training 2 days/week.",
         "priority": 7, "urgency": "routine", "evidence_level": "A",
         "condition_code": None},
        {"key": "REC_WEIGHT_MANAGEMENT", "body_system_code": "CV", "category": "lifestyle",
         "title": "Weight Management",
         "text": "Target BMI <25 kg/m². Recommend 5-10% weight loss over 6 months through caloric restriction and increased physical activity.",
         "priority": 7, "urgency": "routine", "evidence_level": "A",
         "condition_code": None},
        {"key": "REC_NSAID_EDUCATION",   "body_system_code": "KD", "category": "education",
         "title": "NSAID Avoidance Education",
         "text": "Educate patient about nephrotoxic effects of chronic NSAID use. Recommend acetaminophen as alternative for pain management.",
         "priority": 8, "urgency": "routine", "evidence_level": "B",
         "condition_code": None},
        # Anemia of CKD
        {"key": "REC_ANEMIA_CBC",       "body_system_code": "KD", "category": "testing",
         "title": "Complete Blood Count for Anemia Evaluation",
         "text": "Order CBC with differential to evaluate for anemia. In CKD, target hemoglobin 10-11.5 g/dL with iron supplementation and/or ESA as indicated.",
         "priority": 7, "urgency": "routine", "evidence_level": "A",
         "condition_code": "KD_ANEMIA"},
        # Acute Kidney Injury
        {"key": "REC_AKI_HOSPITAL",     "body_system_code": "KD", "category": "referral",
         "title": "Hospitalization for Acute Kidney Injury",
         "text": "Hospitalize for acute kidney injury management: identify and treat underlying cause, optimize volume status, monitor electrolytes, adjust medications.",
         "priority": 10, "urgency": "urgent", "evidence_level": "A",
         "condition_code": "KD_AKI"},
        # Arrhythmia
        {"key": "REC_ARR_ECG",          "body_system_code": "CV", "category": "testing",
         "title": "12-Lead ECG",
         "text": "Obtain 12-lead ECG to evaluate for arrhythmia. Consider 24-hour Holter monitor if symptoms are intermittent.",
         "priority": 8, "urgency": "routine", "evidence_level": "A",
         "condition_code": "CV_ARR"},
    ]


# ---------------------------------------------------------------------------
# Laboratory Tests
# ---------------------------------------------------------------------------
def _lab_tests() -> list[dict[str, Any]]:
    return [
        {"code": "LAB_CBC",        "name": "Complete Blood Count",
         "body_system_code": "BL", "loinc_code": "58410-2", "normal_range": "See ref", "unit": "see ref"},
        {"code": "LAB_BMP",        "name": "Basic Metabolic Panel",
         "body_system_code": "BL", "loinc_code": "51990-0", "normal_range": "See ref", "unit": "see ref"},
        {"code": "LAB_CMP",        "name": "Comprehensive Metabolic Panel",
         "body_system_code": "BL", "loinc_code": "24323-8", "normal_range": "See ref", "unit": "see ref"},
        {"code": "LAB_LIPID",      "name": "Lipid Panel",
         "body_system_code": "BL", "loinc_code": "57698-3", "normal_range": "See ref", "unit": "mg/dL"},
        {"code": "LAB_EGFR",       "name": "eGFR (Estimated Glomerular Filtration Rate)",
         "body_system_code": "KD", "loinc_code": "98979-5", "normal_range": ">60 mL/min/1.73m²", "unit": "mL/min/1.73m²"},
        {"code": "LAB_CREATININE", "name": "Serum Creatinine",
         "body_system_code": "KD", "loinc_code": "2160-0",  "normal_range": "0.7-1.2 mg/dL", "unit": "mg/dL",
         "reference_range_min": 0.7, "reference_range_max": 1.2},
        {"code": "LAB_BUN",        "name": "Blood Urea Nitrogen",
         "body_system_code": "KD", "loinc_code": "3094-0",  "normal_range": "7-20 mg/dL", "unit": "mg/dL"},
        {"code": "LAB_ACR",        "name": "Urine Albumin-to-Creatinine Ratio",
         "body_system_code": "KD", "loinc_code": "14958-4", "normal_range": "<30 mg/g", "unit": "mg/g"},
        {"code": "LAB_URINALYSIS", "name": "Urinalysis",
         "body_system_code": "KD", "loinc_code": "24357-6", "normal_range": "Normal", "unit": "N/A"},
        {"code": "LAB_HBA1C",      "name": "Hemoglobin A1c",
         "body_system_code": "EN", "loinc_code": "4548-4",  "normal_range": "<5.7%", "unit": "%"},
        {"code": "LAB_TSH",        "name": "Thyroid Stimulating Hormone",
         "body_system_code": "EN", "loinc_code": "3016-3",  "normal_range": "0.4-4.0 mIU/L", "unit": "mIU/L"},
        {"code": "LAB_BNP",        "name": "B-Type Natriuretic Peptide (BNP)",
         "body_system_code": "CV", "loinc_code": "42637-8", "normal_range": "<100 pg/mL", "unit": "pg/mL"},
        {"code": "LAB_TROPONIN",   "name": "High-Sensitivity Troponin I",
         "body_system_code": "CV", "loinc_code": "6597-5",  "normal_range": "<99th percentile", "unit": "ng/L"},
        {"code": "LAB_CRP",        "name": "C-Reactive Protein (hs-CRP)",
         "body_system_code": "IM", "loinc_code": "30522-7", "normal_range": "<1.0 mg/L (low risk)", "unit": "mg/L"},
        {"code": "LAB_ECG",        "name": "12-Lead Electrocardiogram",
         "body_system_code": "CV", "loinc_code": None,       "normal_range": "Normal sinus rhythm", "unit": "N/A"},
    ]


# Condition -> Lab Test links
def _condition_lab_links() -> list[tuple[str, str]]:
    return [
        ("CV_CAD",  "LAB_LIPID"),
        ("CV_CAD",  "LAB_TROPONIN"),
        ("CV_CAD",  "LAB_ECG"),
        ("CV_CAD",  "LAB_CRP"),
        ("CV_HTN",  "LAB_BMP"),
        ("CV_HTN",  "LAB_CMP"),
        ("CV_HLD",  "LAB_LIPID"),
        ("CV_HF",   "LAB_BNP"),
        ("CV_HF",   "LAB_CMP"),
        ("CV_HF",   "LAB_ECG"),
        ("CV_ARR",  "LAB_ECG"),
        ("CV_ARR",  "LAB_CMP"),
        ("CV_AFIB", "LAB_ECG"),
        ("CV_AFIB", "LAB_CMP"),
        ("CV_AFIB", "LAB_TSH"),
        ("CV_ANGINA", "LAB_TROPONIN"),
        ("CV_ANGINA", "LAB_ECG"),
        ("CV_PAD",  "LAB_LIPID"),
        ("CV_PAD",  "LAB_HBA1C"),
        ("KD_CKD",  "LAB_CMP"),
        ("KD_CKD",  "LAB_EGFR"),
        ("KD_CKD",  "LAB_CREATININE"),
        ("KD_CKD",  "LAB_BUN"),
        ("KD_CKD",  "LAB_ACR"),
        ("KD_CKD",  "LAB_URINALYSIS"),
        ("KD_CKD",  "LAB_CBC"),
        ("KD_DN",   "LAB_HBA1C"),
        ("KD_DN",   "LAB_ACR"),
        ("KD_DN",   "LAB_EGFR"),
        ("KD_GN",   "LAB_URINALYSIS"),
        ("KD_GN",   "LAB_CMP"),
        ("KD_GN",   "LAB_ACR"),
        ("KD_AKI",  "LAB_CMP"),
        ("KD_AKI",  "LAB_CREATININE"),
        ("KD_AKI",  "LAB_BUN"),
        ("KD_AKI",  "LAB_URINALYSIS"),
        ("KD_NS",   "LAB_CMP"),
        ("KD_NS",   "LAB_ACR"),
        ("KD_NS",   "LAB_CREATININE"),
        ("KD_PKD",  "LAB_CMP"),
        ("KD_PKD",  "LAB_CREATININE"),
        ("KD_KS",   "LAB_URINALYSIS"),
        ("KD_KS",   "LAB_CMP"),
        ("KD_KS",   "LAB_CREATININE"),
        ("KD_UTI",  "LAB_URINALYSIS"),
        ("KD_UTI",  "LAB_CMP"),
        ("KD_ANEMIA", "LAB_CBC"),
        ("KD_BCA",  "LAB_URINALYSIS"),
        ("KD_BCA",  "LAB_CMP"),
    ]


# Condition -> Recommendation links (beyond the default per-condition recommendation mapping)
def _condition_rec_links() -> list[tuple[str, str]]:
    return [
        ("CV_CAD",   "REC_CAD_ASPIRIN"),
        ("CV_CAD",   "REC_CAD_STATIN"),
        ("CV_CAD",   "REC_CAD_CARDIOLOGY"),
        ("CV_HTN",   "REC_HTN_BP_MONITOR"),
        ("CV_HTN",   "REC_HTN_ANTIHYPERTENSIVE"),
        ("CV_HTN",   "REC_HTN_LIFESTYLE"),
        ("CV_HLD",   "REC_HLD_LIPID_PANEL"),
        ("CV_HLD",   "REC_HLD_DIET"),
        ("CV_HF",    "REC_HF_ECHO"),
        ("CV_HF",    "REC_HF_CARDIOLOGY"),
        ("CV_HF",    "REC_HF_SODIUM_RESTRICT"),
        ("CV_AFIB",  "REC_AFIB_CARDIOLOGY"),
        ("CV_AFIB",  "REC_AFIB_ANTICOAG"),
        ("CV_ANGINA","REC_ANGINA_NITRATE"),
        ("CV_ANGINA","REC_ANGINA_CARDIOLOGY"),
        ("CV_ARR",   "REC_ARR_ECG"),
        ("KD_CKD",   "REC_CKD_NEPHROLOGY"),
        ("KD_CKD",   "REC_CKD_MONITORING"),
        ("KD_CKD",   "REC_CKD_ACEI"),
        ("KD_CKD",   "REC_CKD_DIET"),
        ("KD_DN",    "REC_DN_SGLT2"),
        ("KD_DN",    "REC_DN_ENDOCRINE"),
        ("KD_KS",    "REC_KS_HYDRATION"),
        ("KD_KS",    "REC_KS_UROLOGY"),
        ("KD_UTI",   "REC_UTI_CULTURE"),
        ("KD_UTI",   "REC_UTI_ANTIBIOTIC"),
        ("KD_ANEMIA","REC_ANEMIA_CBC"),
        ("KD_AKI",   "REC_AKI_HOSPITAL"),
    ]


# Indicator -> Evidence links
def _indicator_evidence_links() -> list[tuple[str, int]]:
    """(indicator_key, evidence_index) where index into _evidence_references()"""
    return [
        ("CV_CHEST_PAIN",     0),
        ("CV_HYPERTENSION",   3),
        ("CV_HIGH_CHOL",      0),
        ("CV_DIABETES",       0),
        ("CV_TOBACCO",        0),
        ("KD_PROTEINURIA",    1),
        ("KD_LOW_EGFR",       1),
        ("KD_HIGH_CREAT",     1),
        ("KD_HTN_KIDNEY",     4),
        ("KD_DM_KIDNEY",      1),
        ("KD_NSAID",          4),
        ("CV_PALPITATIONS",   2),
        ("CV_SEDENTARY",      0),
        ("CV_POOR_DIET",      0),
        ("KD_FAMILY_CKD", 4),
    ]


# =========================================================================
# Seed function
# =========================================================================
async def seed_medical(session: AsyncSession, body_system_map: dict[str, str]) -> None:
    """Seed all medical knowledge: indicators, conditions, recommendations, lab tests, evidence, links."""
    # Check if already seeded
    stmt = select(ClinicalIndicatorModel).limit(1)
    existing = await session.execute(stmt)
    if existing.scalars().first() is not None:
        return

    indicator_repo = SQLClinicalIndicatorRepository(session)
    rec_repo = SQLRecommendationRepository(session)
    lab_repo = SQLLaboratoryTestRepository(session)

    # 1. Create conditions
    condition_map: dict[str, str] = {}  # code -> id
    for c in _conditions():
        cid = uuid.uuid4().hex
        bs_id = body_system_map.get(c["body_system_code"])
        model = PossibleConditionModel(
            id=cid,
            code=c["code"],
            name=c["name"],
            description=f"Possible condition: {c['name']}",
            body_system_id=bs_id,
            severity=c["severity"],
            icd10=c["icd10"],
            status="active",
        )
        session.add(model)
        condition_map[c["code"]] = cid
    await session.flush()

    # 2. Create clinical indicators
    indicator_map: dict[str, str] = {}  # key -> id
    for ind_data in _indicators():
        bs_id = body_system_map.get(ind_data["body_system_code"])
        ind = ClinicalIndicator.create(
            body_system_id=bs_id,
            key=ind_data["key"],
            name=ind_data["name"],
            description=f"Clinical indicator: {ind_data['name']}",
            severity=ind_data["severity"],
            evidence_strength=ind_data["evidence_strength"],
            confidence=ind_data["confidence"],
        )
        created = await indicator_repo.create(ind)
        indicator_map[ind_data["key"]] = created.id
    await session.flush()

    # 3. Create evidence references
    evidence_rows = _evidence_references()
    for ev in evidence_rows:
        session.add(EvidenceReferenceModel(**ev))
    await session.flush()
    evidence_ids = [ev["id"] for ev in evidence_rows]

    # 4. Create recommendations
    rec_map: dict[str, str] = {}  # key -> id
    for rec_data in _recommendations():
        bs_id = body_system_map.get(rec_data["body_system_code"])
        rec = Recommendation.create(
            body_system_id=bs_id,
            category=rec_data["category"],
            title=rec_data["title"],
            text=rec_data["text"],
            priority=rec_data["priority"],
            urgency=rec_data["urgency"],
            evidence_level=rec_data["evidence_level"],
        )
        created = await rec_repo.create(rec)
        rec_map[rec_data["key"]] = created.id
    await session.flush()

    # 5. Create lab tests
    lab_map: dict[str, str] = {}  # code -> id
    for lab_data in _lab_tests():
        bs_id = body_system_map.get(lab_data["body_system_code"])
        lab = LaboratoryTest.create(
            code=lab_data["code"],
            name=lab_data["name"],
            body_system_id=bs_id,
            description=f"Laboratory test: {lab_data['name']}",
            loinc_code=lab_data["loinc_code"],
            normal_range=lab_data.get("normal_range"),
            unit=lab_data.get("unit"),
            reference_range_min=lab_data.get("reference_range_min"),
            reference_range_max=lab_data.get("reference_range_max"),
        )
        created = await lab_repo.create(lab)
        lab_map[lab_data["code"]] = created.id
    await session.flush()

    # 6. Create question -> indicator links (by question code -> indicator key)
    # We need to find question IDs by code. The seed.py creates questions with codes.
    # Let's query the questions table.
    from app.infrastructure.persistence.models.question import QuestionModel

    q_rows = await session.execute(select(QuestionModel))
    questions = {q.code: q.id for q in q_rows.scalars().all()}

    for qcode, ind_key in _question_indicator_links():
        qid = questions.get(qcode)
        iid = indicator_map.get(ind_key)
        if qid and iid:
            link = QuestionIndicatorLinkModel(question_id=qid, indicator_id=iid)
            session.add(link)

    # 7. Create option -> indicator links
    from app.infrastructure.persistence.models.question_option import QuestionOptionModel

    opt_rows = await session.execute(select(QuestionOptionModel))
    options_by_code_question: dict[str, dict[str, str]] = {}
    for opt in opt_rows.scalars().all():
        options_by_code_question.setdefault(opt.code, {})[opt.question_id] = opt.id

    for qcode, opt_code, ind_key in _option_indicator_links():
        qid = questions.get(qcode)
        iid = indicator_map.get(ind_key)
        if qid and iid:
            opt_id = options_by_code_question.get(opt_code, {}).get(qid)
            if opt_id:
                link = QuestionOptionIndicatorLinkModel(
                    question_option_id=opt_id, indicator_id=iid
                )
                session.add(link)

    # 8. Create indicator -> condition links
    for ind_key, cond_code in _indicator_condition_links():
        iid = indicator_map.get(ind_key)
        cid = condition_map.get(cond_code)
        if iid and cid:
            link = IndicatorConditionLinkModel(indicator_id=iid, condition_id=cid)
            session.add(link)

    # 9. Create indicator -> evidence links
    for ind_key, ev_idx in _indicator_evidence_links():
        iid = indicator_map.get(ind_key)
        if iid and ev_idx < len(evidence_ids):
            link = IndicatorEvidenceLinkModel(
                indicator_id=iid, evidence_id=evidence_ids[ev_idx]
            )
            session.add(link)

    # 10. Create condition -> recommendation links
    for cond_code, rec_key in _condition_rec_links():
        cid = condition_map.get(cond_code)
        rid = rec_map.get(rec_key)
        if cid and rid:
            link = ConditionRecommendationLinkModel(condition_id=cid, recommendation_id=rid)
            session.add(link)

    # 11. Create condition -> lab test links
    for cond_code, lab_code in _condition_lab_links():
        cid = condition_map.get(cond_code)
        lid = lab_map.get(lab_code)
        if cid and lid:
            link = ConditionLaboratoryTestLinkModel(condition_id=cid, laboratory_test_id=lid)
            session.add(link)

    await session.commit()
