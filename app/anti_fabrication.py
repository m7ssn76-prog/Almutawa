from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Iterable


_EXECUTION_RE = re.compile(
    r"(?:\b(?:implemented|executed|merged|deployed|connected|passed|succeeded|successful|running|production)\b|"
    r"(?:تم|نُفذ|نفذ|اشتغل|شغّال|نجح|دُمج|دمج|نشر|متصل|تشغيل|إنتاجي))",
    re.IGNORECASE,
)
_SHA40_RE = re.compile(r"\b[a-f0-9]{40}\b", re.IGNORECASE)
_SUCCESS_RE = re.compile(
    r"\b(?:success|successful|passed|completed|merged|ok)\b|(?:نجح|ناجح|تم الدمج|مكتمل)",
    re.IGNORECASE,
)
_TOKEN_RE = re.compile(r"[A-Za-z0-9_\-]+|[\u0600-\u06FF]+", re.UNICODE)

_STOPWORDS = {
    "the", "and", "for", "with", "from", "this", "that", "was", "were", "is", "are",
    "has", "have", "had", "into", "only", "على", "من", "إلى", "الى", "في", "عن", "هذا",
    "هذه", "هو", "هي", "تم", "مع", "كان", "كانت", "يكون", "تكون", "وقد", "لكن",
}

_EXECUTION_KEYS = {
    "run_id",
    "run_number",
    "workflow_run",
    "workflow",
    "artifact_id",
    "commit_sha",
    "head_sha",
    "merge_commit_sha",
    "repository_id",
}
_OUTCOME_KEYS = {"conclusion", "status", "merged", "result", "outcome"}


@dataclass(frozen=True)
class GateResult:
    allowed: bool
    reason: str
    evidence_ids: tuple[int, ...]


def _value(item: Any, name: str, default: Any = None) -> Any:
    if isinstance(item, dict):
        return item.get(name, default)
    return getattr(item, name, default)


def _evidence_text(item: Any) -> str:
    return "\n".join(
        str(_value(item, field, "") or "")
        for field in ("title", "content", "purpose", "provenance_hash")
    )


def _tokens(text: str) -> set[str]:
    return {
        token.casefold()
        for token in _TOKEN_RE.findall(text)
        if len(token) >= 2 and token.casefold() not in _STOPWORDS
    }


def _mostly_arabic(text: str) -> bool:
    letters = [char for char in text if char.isalpha()]
    if not letters:
        return False
    arabic = sum("\u0600" <= char <= "\u06ff" for char in letters)
    return arabic / len(letters) >= 0.35


def _same_language_support(claim: str, evidence_text: str) -> bool:
    """Fail closed on unrelated same-language claims.

    Cross-language evidence is not rejected solely for lexical mismatch because a
    legitimate Arabic answer may cite an English source. Execution claims still
    require structural proof independently of language.
    """
    if _mostly_arabic(claim) != _mostly_arabic(evidence_text):
        return True

    claim_tokens = _tokens(claim)
    if not claim_tokens:
        return False
    evidence_tokens = _tokens(evidence_text)
    overlap = claim_tokens & evidence_tokens
    required = 1 if len(claim_tokens) <= 3 else max(2, round(len(claim_tokens) * 0.15))
    return len(overlap) >= required


def _walk_json(value: Any, keys: set[str], values: list[str]) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            keys.add(str(key).casefold())
            _walk_json(item, keys, values)
    elif isinstance(value, list):
        for item in value:
            _walk_json(item, keys, values)
    elif value is not None:
        values.append(str(value))


def _execution_proof(item: Any) -> bool:
    text = _evidence_text(item)
    keys: set[str] = set()
    values: list[str] = []

    content = str(_value(item, "content", "") or "")
    try:
        parsed = json.loads(content)
    except (TypeError, ValueError, json.JSONDecodeError):
        parsed = None
    if parsed is not None:
        _walk_json(parsed, keys, values)

    combined_values = " ".join(values)
    has_identity = bool(keys & _EXECUTION_KEYS) or bool(_SHA40_RE.search(text))
    has_outcome_key = bool(keys & _OUTCOME_KEYS)
    has_success = bool(_SUCCESS_RE.search(text + " " + combined_values))
    return has_identity and has_outcome_key and has_success


def validate_claims(claims: Iterable[Any], allowed_evidence: dict[int, Any]) -> GateResult:
    """Validate model claims before an answer can be returned as evidence-backed.

    Rules:
    - every claim must be explicitly classified;
    - verified/inference claims require evidence IDs from the supplied packet;
    - unverified/conflict claims fail the answered path closed;
    - same-language claims need minimal lexical support from their cited evidence;
    - execution/state claims require structural execution proof (run/commit + outcome).
    """
    claim_list = list(claims)
    if not claim_list:
        return GateResult(False, "answered output contained no claim-level evidence map", ())

    used: list[int] = []
    for claim in claim_list:
        text = str(_value(claim, "text", "") or "").strip()
        status = str(_value(claim, "status", "") or "").strip().casefold()
        evidence_ids = list(dict.fromkeys(_value(claim, "evidence_ids", []) or []))

        if not text:
            return GateResult(False, "empty claim", ())
        if status not in {"verified", "inference", "unverified", "conflict"}:
            return GateResult(False, "invalid claim status", ())
        if status in {"unverified", "conflict"}:
            return GateResult(False, f"claim status is {status}", ())
        if not evidence_ids:
            return GateResult(False, "supported claim has no evidence IDs", ())
        if any(item_id not in allowed_evidence for item_id in evidence_ids):
            return GateResult(False, "claim references evidence outside the supplied packet", ())

        cited_items = [allowed_evidence[item_id] for item_id in evidence_ids]
        cited_text = "\n".join(_evidence_text(item) for item in cited_items)
        if not _same_language_support(text, cited_text):
            return GateResult(False, "claim is not sufficiently grounded in cited evidence", ())

        if _EXECUTION_RE.search(text):
            if status != "verified":
                return GateResult(False, "execution claim cannot be inference", ())
            if not any(_execution_proof(item) for item in cited_items):
                return GateResult(False, "execution claim lacks run/commit outcome proof", ())

        used.extend(evidence_ids)

    return GateResult(True, "claim-level evidence gate passed", tuple(dict.fromkeys(used)))


def render_claims(claims: Iterable[Any]) -> str:
    """Render only validated claim text, preventing uncited wrapper prose."""
    lines: list[str] = []
    for claim in claims:
        status = str(_value(claim, "status", "") or "").strip().casefold()
        text = str(_value(claim, "text", "") or "").strip()
        lines.append(f"[{status}] {text}")
    return "\n".join(lines)
