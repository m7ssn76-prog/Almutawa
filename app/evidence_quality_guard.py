from __future__ import annotations

from collections.abc import Iterable
from typing import Any


_DEFAULT_CRITICAL_FIELDS = {"severity"}


def apply_degraded_evidence_guard(
    result: dict[str, Any],
    *,
    insufficient_ratio: float = 0.50,
    critical_fields: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Apply an evidence-quality guard without downgrading an existing risk state.

    The guard separates two questions:
    1. What do the accepted readings say about risk?
    2. Is the available evidence complete enough to trust a normal-looking result?

    It never lowers a non-normal risk state because inputs were rejected. Instead, it
    adds an evidence-quality warning. A normal-looking result may be escalated to a
    degraded or insufficient-evidence state when rejected inputs reduce confidence.
    """

    if not isinstance(result, dict):
        raise TypeError("result must be a dict")

    if not 0 <= insufficient_ratio <= 1:
        raise ValueError("insufficient_ratio must be between 0 and 1")

    critical = set(critical_fields or _DEFAULT_CRITICAL_FIELDS)

    original_state = result.get("state", "UNKNOWN")
    original_decision = result.get("decision")

    details = result.get("details", {})
    if not isinstance(details, dict):
        details = {}

    rejected = details.get("rejected", {})
    if not isinstance(rejected, dict):
        rejected = {}

    accepted = details.get("accepted", {})
    if not isinstance(accepted, dict):
        accepted = {}

    accepted_count = len(accepted)
    rejected_count = len(rejected)
    total_count = accepted_count + rejected_count

    rejected_ratio = (rejected_count / total_count) if total_count else 0.0
    coverage_ratio = (accepted_count / total_count) if total_count else 0.0
    critical_rejected_fields = sorted(set(rejected).intersection(critical))

    result["evidence_metrics"] = {
        "accepted_count": accepted_count,
        "rejected_count": rejected_count,
        "total_count": total_count,
        "coverage_ratio": coverage_ratio,
        "rejected_ratio": rejected_ratio,
        "critical_rejected_count": len(critical_rejected_fields),
        "critical_rejected_fields": critical_rejected_fields,
    }
    result["original_state"] = original_state
    result["original_decision"] = original_decision

    # No usable evidence exists. Preserve an already elevated risk state, but never
    # allow a normal-looking state to remain normal without accepted evidence.
    if total_count == 0 or accepted_count == 0:
        result["evidence_quality"] = "INSUFFICIENT"
        result["degraded_evidence"] = True

        if original_state == "NORMAL" or original_state in {None, "", "UNKNOWN"}:
            result["state"] = "INSUFFICIENT_EVIDENCE"
            result["decision"] = "VERIFY_INPUTS"
            result["reason"] = (
                "لا توجد أدلة صالحة كافية لاتخاذ حكم موثوق؛ "
                "لا يجوز اعتبار الحالة طبيعية قبل التحقق من المدخلات."
            )
        else:
            result["evidence_quality_warning"] = (
                "الأدلة المقبولة غير كافية؛ حالة الخطر الحالية محفوظة ولم يتم خفضها."
            )
        return result

    if not rejected:
        result["evidence_quality"] = "GOOD"
        result["degraded_evidence"] = False
        return result

    result["degraded_evidence"] = True

    # A rejected critical field is more serious than an ordinary quality reduction.
    if critical_rejected_fields:
        result["evidence_quality"] = "CRITICAL_DEGRADED"
        if original_state == "NORMAL":
            result["state"] = "CRITICAL_DEGRADED"
            result["decision"] = "VERIFY_CRITICAL_INPUTS / OBSERVE"
            result["reason"] = (
                "بعض المدخلات الحرجة رُفضت؛ لا تُعامل الحالة كطبيعية "
                "قبل التحقق من الحقول الحرجة."
            )
        else:
            result["evidence_quality_warning"] = (
                "بعض المدخلات الحرجة رُفضت؛ القرار الحالي قائم على الأدلة الصالحة فقط."
            )
        return result

    # Too much evidence was rejected. Preserve elevated risk states; normal states
    # become explicitly insufficient rather than merely degraded.
    if rejected_ratio >= insufficient_ratio:
        result["evidence_quality"] = "INSUFFICIENT"
        if original_state == "NORMAL":
            result["state"] = "INSUFFICIENT_EVIDENCE"
            result["decision"] = "VERIFY_INPUTS"
            result["reason"] = (
                "نسبة المدخلات المرفوضة مرتفعة؛ لا توجد تغطية كافية "
                "لاعتبار الحالة طبيعية."
            )
        else:
            result["evidence_quality_warning"] = (
                "نسبة كبيرة من المدخلات رُفضت؛ حالة الخطر محفوظة وتحتاج تحققًا إضافيًا."
            )
        return result

    result["evidence_quality"] = "DEGRADED"

    if original_state == "NORMAL":
        result["state"] = "DEGRADED_NORMAL"
        result["decision"] = "VERIFY_INPUTS / OBSERVE"
        result["reason"] = (
            "القراءات المقبولة تبدو طبيعية، لكن بعض المدخلات رُفضت؛ "
            "لا تُعامل الحالة كطبيعية كاملة قبل التحقق من جودة البيانات."
        )
    else:
        result["evidence_quality_warning"] = (
            "بعض المدخلات رُفضت؛ القرار الحالي قائم على الأدلة الصالحة فقط."
        )

    return result
