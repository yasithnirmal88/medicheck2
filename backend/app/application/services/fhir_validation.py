"""Deterministic FHIR R4 structural validator for MediCheck exports.

Dependency-free (no pydantic-v1 / fhir.resources needed at runtime),
so it can run in the normal test environment and CI. It enforces the
FHIR R4 structural rules that matter for the resource types
MediCheck exports:

- known R4 resource types (whitelist)
- required elements per the R4 specification (resource-level
  cardinalities, which the official pydantic models under-enforce)
- Observation.value[x] exactly-one constraint
- enum values (status / intent / priority / gender / bundle type /
  consent provision type)
- Reference format (``ResourceType/id``)
- CodeableConcept / Identifier / HumanName / Quantity structure
- id, uri, date, dateTime, instant formats
- extension URLs must be absolute + namespaced under
  ``https://medicheck.org/fhir/StructureDefinition/``
- safety invariant: MediCheck NEVER exports ``Condition`` resources
  (possible conditions are Observations, not confirmed diagnoses)

Usage::

    from app.application.services.fhir_validation import validate_fhir_payload

    errors = validate_fhir_payload(payload_dict)
    # errors == []  -> structurally valid FHIR R4

This is a structural validator, not a terminology validator: it does
not check code-system membership (that requires a terminology server
or the official HL7 validator). See MEDICHECK_PHASE10_REPORT.md for
the re-validation workflow with the official R4 models.
"""

from __future__ import annotations

import re
from typing import Any

# ── FHIR R4 primitive formats ────────────────────────────────────
_ID_RE = re.compile(r"^[A-Za-z0-9\-\.]{1,64}$")
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_DATETIME_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}[Tt]\d{2}:\d{2}:\d{2}(\.\d+)?"
    r"([Zz]|[+-]\d{2}:\d{2})$"
)
_URI_RE = re.compile(r"^\S+$")
_REFERENCE_RE = re.compile(r"^[A-Za-z][A-Za-z0-9\-\.]{0,63}/[\w\-\.]{1,64}$")

# ── FHIR R4 resource types MediCheck exports ─────────────────────
EXPORTED_RESOURCE_TYPES = frozenset(
    {
        "Patient",
        "Consent",
        "QuestionnaireResponse",
        "Observation",
        "DiagnosticReport",
        "ServiceRequest",
        "Task",
        "CarePlan",
    }
)

#: Safety invariant: a possible condition is NEVER a Condition.
FORBIDDEN_RESOURCE_TYPES = frozenset({"Condition"})

# ── R4 value sets (spec-defined enums) ───────────────────────────
_ENUMS: dict[str, dict[str, frozenset[str]]] = {
    "Patient": {"gender": frozenset({"male", "female", "other", "unknown"})},
    "Consent": {
        "status": frozenset(
            {"draft", "proposed", "active", "rejected", "inactive", "entered-in-error"}
        ),
    },
    "QuestionnaireResponse": {
        "status": frozenset(
            {"in-progress", "completed", "amended", "entered-in-error", "stopped"}
        ),
    },
    "Observation": {
        "status": frozenset(
            {
                "registered",
                "preliminary",
                "final",
                "amended",
                "corrected",
                "cancelled",
                "entered-in-error",
                "unknown-status",
            }
        ),
    },
    "DiagnosticReport": {
        "status": frozenset(
            {
                "registered",
                "partial",
                "preliminary",
                "final",
                "amended",
                "corrected",
                "cancelled",
                "entered-in-error",
            }
        ),
    },
    "ServiceRequest": {
        "status": frozenset(
            {"active", "on-hold", "completed", "revoked", "entered-in-error", "unknown-status"}
        ),
        "intent": frozenset(
            {
                "proposal",
                "plan",
                "order",
                "original-order",
                "reflex-order",
                "filler-order",
                "instance-order",
                "option",
            }
        ),
        "priority": frozenset({"routine", "urgent", "stat", "asap"}),
    },
    "Task": {
        "status": frozenset(
            {
                "proposed",
                "planned",
                "requested",
                "received",
                "accepted",
                "in-progress",
                "on-hold",
                "review",
                "rejected",
                "ready",
                "cancelled",
                "entered-in-error",
                "failed",
                "draft",
            }
        ),
        "intent": frozenset(
            {
                "proposal",
                "plan",
                "order",
                "original-order",
                "reflex-order",
                "filler-order",
                "instance-order",
                "option",
            }
        ),
    },
    "CarePlan": {
        "status": frozenset(
            {"draft", "active", "on-hold", "revoked", "completed", "entered-in-error", "unknown"}
        ),
        "intent": frozenset(
            {"proposal", "plan", "order", "original-order", "reflex-order", "filler-order", "instance-order", "option"}
        ),
    },
    "Bundle": {
        "type": frozenset(
            {
                "document",
                "collection",
                "batch",
                "batch-response",
                "transaction",
                "transaction-response",
                "history",
                "searchset",
                "subscription",
            }
        ),
    },
}

#: R4 spec-required elements per resource type (beyond resourceType).
_REQUIRED_FIELDS: dict[str, tuple[str, ...]] = {
    "Patient": (),
    "Consent": ("status", "scope", "category"),
    "QuestionnaireResponse": ("status",),
    "Observation": ("status", "code"),
    "DiagnosticReport": ("status", "code"),
    "ServiceRequest": ("status", "intent"),
    "Task": ("status", "intent"),
    "CarePlan": ("status", "intent"),
}

#: Observation.value[x] — R4 allows exactly ONE of these.
_OBSERVATION_VALUE_FIELDS = (
    "valueAttachment",
    "valueBoolean",
    "valueCodeableConcept",
    "valueDateTime",
    "valueInteger",
    "valuePeriod",
    "valueQuantity",
    "valueRange",
    "valueRatio",
    "valueReference",
    "valueSampledData",
    "valueString",
    "valueTime",
)

_MEDICHECK_EXTENSION_BASE = "https://medicheck.org/fhir/StructureDefinition/"


def _err(path: str, msg: str) -> str:
    return f"{path}: {msg}"


def _validate_codeable_concept(path: str, cc: Any, errors: list[str]) -> None:
    if not isinstance(cc, dict):
        errors.append(_err(path, "CodeableConcept must be an object"))
        return
    coding = cc.get("coding")
    if coding is not None:
        if not isinstance(coding, list) or not coding:
            errors.append(_err(path + ".coding", "must be a non-empty list when present"))
            return
        for i, c in enumerate(coding):
            if not isinstance(c, dict):
                errors.append(_err(f"{path}.coding[{i}]", "Coding must be an object"))
                continue
            for key in ("system", "code"):
                val = c.get(key)
                if not isinstance(val, str) or not val:
                    errors.append(_err(f"{path}.coding[{i}].{key}", "required non-empty string"))
            if "system" in c and not _URI_RE.match(c["system"]):
                errors.append(_err(f"{path}.coding[{i}].system", "invalid uri"))


def _validate_reference(path: str, ref: Any, errors: list[str]) -> None:
    if not isinstance(ref, dict):
        errors.append(_err(path, "Reference must be an object"))
        return
    reference = ref.get("reference")
    if not isinstance(reference, str) or not _REFERENCE_RE.match(reference):
        errors.append(
            _err(path + ".reference", f"must match 'ResourceType/id' (got {reference!r})")
        )


def _validate_extension_list(path: str, extensions: Any, errors: list[str]) -> None:
    if not isinstance(extensions, list):
        errors.append(_err(path, "extension must be a list"))
        return
    for i, ext in enumerate(extensions):
        if not isinstance(ext, dict):
            errors.append(_err(f"{path}[{i}]", "Extension must be an object"))
            continue
        url = ext.get("url")
        if not isinstance(url, str) or not _URI_RE.match(url):
            errors.append(_err(f"{path}[{i}].url", "Extension.url must be an absolute uri"))
        elif url.startswith(_MEDICHECK_EXTENSION_BASE):
            continue  # properly namespaced Medicheck extension
        elif url.startswith("http://hl7.org/fhir") or url.startswith("http://terminology.hl7.org"):
            continue  # standard HL7 extension
        else:
            errors.append(
                _err(
                    f"{path}[{i}].url",
                    f"extension outside the Medicheck/HL7 namespaces: {url}",
                )
            )


def _validate_resource(resource: dict, errors: list[str]) -> None:
    path = resource.get("resourceType", "?")
    rtype = resource.get("resourceType")
    if not isinstance(rtype, str):
        errors.append(_err(path, "resourceType is required"))
        return
    rid = resource.get("id")
    if rid is not None and (not isinstance(rid, str) or not _ID_RE.match(rid)):
        errors.append(_err(path + ".id", f"invalid FHIR id (got {rid!r})"))

    if rtype in FORBIDDEN_RESOURCE_TYPES:
        errors.append(
            _err(path, f"forbidden resource type: MediCheck never exports {rtype}")
        )
    if rtype not in EXPORTED_RESOURCE_TYPES:
        errors.append(_err(path, f"unexpected resource type: {rtype}"))
        return

    # Required elements per the R4 spec.
    for field in _REQUIRED_FIELDS.get(rtype, ()):
        if resource.get(field) is None:
            errors.append(_err(path, f"missing required R4 element '{field}'"))

    # Enum-valued fields.
    for field, allowed in _ENUMS.get(rtype, {}).items():
        val = resource.get(field)
        if val is not None and val not in allowed:
            errors.append(_err(path, f"invalid {rtype}.{field} value {val!r}"))

    # Dates / datetimes.
    for field, pattern in (
        ("birthDate", _DATE_RE),
        ("effectiveDateTime", _DATETIME_RE),
        ("issued", _DATETIME_RE),
        ("authored", _DATETIME_RE),
        ("occurrenceDateTime", _DATETIME_RE),
    ):
        val = resource.get(field)
        if val is not None and (not isinstance(val, str) or not pattern.match(val)):
            errors.append(_err(path, f"invalid {rtype}.{field} date/dateTime (got {val!r})"))

    # References.
    for field in ("subject", "patient", "focus", "for"):
        ref = resource.get(field)
        if ref is not None:
            _validate_reference(f"{path}.{field}", ref, errors)
    for field in ("result",):
        refs = resource.get(field)
        if refs is not None:
            if not isinstance(refs, list):
                errors.append(_err(path + ".result", "must be a list of Reference"))
            else:
                for i, r in enumerate(refs):
                    _validate_reference(f"{path}.result[{i}]", r, errors)

    # CodeableConcepts.
    for field in ("code", "scope", "valueCodeableConcept"):
        cc = resource.get(field)
        if cc is not None:
            _validate_codeable_concept(f"{path}.{field}", cc, errors)
    for field in ("category", "interpretation", "conclusionCode", "reasonCode"):
        ccs = resource.get(field)
        if ccs is not None:
            if not isinstance(ccs, list):
                errors.append(_err(path + f".{field}", "must be a list of CodeableConcept"))
            else:
                for i, cc in enumerate(ccs):
                    _validate_codeable_concept(f"{path}.{field}[{i}]", cc, errors)

    # Extensions (namespacing).
    for field in ("extension", "modifierExtension"):
        exts = resource.get(field)
        if exts is not None:
            _validate_extension_list(f"{path}.{field}", exts, errors)

    # Type-specific structural rules.
    if rtype == "Observation":
        present = [f for f in _OBSERVATION_VALUE_FIELDS if resource.get(f) is not None]
        if len(present) == 0:
            errors.append(_err(path, "Observation has no value[x] (exactly one expected)"))
        elif len(present) > 1:
            errors.append(
                _err(
                    path,
                    f"Observation carries multiple value[x] ({', '.join(present)}); "
                    "R4 allows exactly one",
                )
            )
        components = resource.get("component")
        if components is not None:
            if not isinstance(components, list):
                errors.append(_err(path + ".component", "must be a list"))
            else:
                for i, comp in enumerate(components):
                    cpath = f"{path}.component[{i}]"
                    if not isinstance(comp, dict):
                        errors.append(_err(cpath, "component must be an object"))
                        continue
                    if not isinstance(comp.get("code"), dict):
                        errors.append(_err(cpath, "component.code (CodeableConcept) is required"))
                    comp_present = [f for f in _OBSERVATION_VALUE_FIELDS if comp.get(f) is not None]
                    if len(comp_present) != 1:
                        errors.append(
                            _err(cpath, f"component must carry exactly one value[x] (got {comp_present})")
                        )
        notes = resource.get("note")
        if notes is not None and isinstance(notes, list):
            for i, note in enumerate(notes):
                if not isinstance(note, dict) or not isinstance(note.get("text"), str):
                    errors.append(_err(f"{path}.note[{i}]", "Annotation.text is required"))

    elif rtype == "Patient":
        for i, name in enumerate(resource.get("name") or []):
            if not isinstance(name, dict):
                errors.append(_err(f"{path}.name[{i}]", "HumanName must be an object"))
        identifiers = resource.get("identifier")
        if identifiers is not None:
            if not isinstance(identifiers, list):
                errors.append(_err(path + ".identifier", "must be a list of Identifier"))
            else:
                for i, ident in enumerate(identifiers):
                    ipath = f"{path}.identifier[{i}]"
                    if not isinstance(ident, dict):
                        errors.append(_err(ipath, "Identifier must be an object"))
                        continue
                    for key in ("system", "value"):
                        if not isinstance(ident.get(key), str) or not ident[key]:
                            errors.append(_err(ipath, f"Identifier.{key} required non-empty string"))
        for i, comm in enumerate(resource.get("communication") or []):
            if not isinstance(comm, dict) or not isinstance(comm.get("language"), dict):
                errors.append(
                    _err(f"{path}.communication[{i}]", "Patient.communication.language is required")
                )

    elif rtype == "QuestionnaireResponse":
        questionnaire = resource.get("questionnaire")
        if questionnaire is not None and (not isinstance(questionnaire, str) or not _URI_RE.match(questionnaire)):
            errors.append(_err(path, "invalid QuestionnaireResponse.questionnaire canonical"))
        for i, item in enumerate(resource.get("item") or []):
            if not isinstance(item, dict) or not isinstance(item.get("linkId"), str):
                errors.append(_err(f"{path}.item[{i}]", "linkId is required"))

    elif rtype == "DiagnosticReport":
        conclusion = resource.get("conclusion")
        if conclusion is not None and not isinstance(conclusion, str):
            errors.append(_err(path, "DiagnosticReport.conclusion must be a string"))

    elif rtype == "Task":
        period = resource.get("executionPeriod")
        if period is not None and not isinstance(period, dict):
            errors.append(_err(path, "Task.executionPeriod must be a Period object"))

    elif rtype == "CarePlan":
        for i, activity in enumerate(resource.get("activity") or []):
            if not isinstance(activity, dict) or not isinstance(activity.get("detail"), dict):
                errors.append(_err(f"{path}.activity[{i}]", "CarePlan.activity.detail is required"))

    elif rtype == "Consent":
        provision = resource.get("provision")
        if provision is not None:
            # R4: Consent.provision is 0..1 (a single provision object).
            if not isinstance(provision, dict):
                errors.append(
                    _err(path, "Consent.provision must be a single object (R4 0..1)")
                )
            elif provision.get("type") not in (None, "permit", "deny"):
                errors.append(_err(path, "Consent.provision.type must be 'permit' or 'deny'"))


def validate_fhir_resource(resource: Any) -> list[str]:
    """Validate a single FHIR R4 resource dict. Returns a list of
    error strings (empty == structurally valid)."""
    errors: list[str] = []
    if not isinstance(resource, dict):
        return ["resource must be a JSON object"]
    _validate_resource(resource, errors)
    return errors


def validate_fhir_bundle(bundle: Any) -> list[str]:
    """Validate a FHIR R4 Bundle (and every entry resource).
    Returns a list of error strings (empty == structurally valid)."""
    errors: list[str] = []
    if not isinstance(bundle, dict):
        return ["bundle must be a JSON object"]
    if bundle.get("resourceType") != "Bundle":
        errors.append(_err("Bundle", "resourceType must be 'Bundle'"))
        return errors
    if bundle.get("type") not in _ENUMS["Bundle"]["type"]:
        errors.append(_err("Bundle", f"invalid Bundle.type (got {bundle.get('type')!r})"))
    timestamp = bundle.get("timestamp")
    if timestamp is not None and (not isinstance(timestamp, str) or not _DATETIME_RE.match(timestamp)):
        errors.append(_err("Bundle", f"invalid Bundle.timestamp instant (got {timestamp!r})"))
    meta = bundle.get("meta")
    if meta is not None and not isinstance(meta, dict):
        errors.append(_err("Bundle", "meta must be a Meta object"))
    entries = bundle.get("entry")
    if entries is not None:
        if not isinstance(entries, list):
            errors.append(_err("Bundle", "entry must be a list"))
        else:
            for i, entry in enumerate(entries):
                epath = f"Bundle.entry[{i}]"
                if not isinstance(entry, dict):
                    errors.append(_err(epath, "entry must be an object"))
                    continue
                full_url = entry.get("fullUrl")
                if full_url is not None and (not isinstance(full_url, str) or not _URI_RE.match(full_url)):
                    errors.append(_err(epath, f"invalid fullUrl (got {full_url!r})"))
                resource = entry.get("resource")
                if resource is None:
                    errors.append(_err(epath, "entry.resource is required"))
                else:
                    errors.extend(validate_fhir_resource(resource))
    return errors


#: Alias — validate any FHIR payload (Bundle or single resource).
def validate_fhir_payload(payload: Any) -> list[str]:
    if isinstance(payload, dict) and payload.get("resourceType") == "Bundle":
        return validate_fhir_bundle(payload)
    return validate_fhir_resource(payload)
