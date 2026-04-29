"""Configurable deadline assist rules for demo and review workflows."""

from datetime import datetime, timedelta


DEADLINE_RULES = {
    "appeal": {
        "rule_id": "appeal_default_30",
        "label": "Appeal default",
        "days": 30,
        "basis": "Demo rule: appeal consideration within 30 days from date of order.",
    },
    "review": {
        "rule_id": "review_default_90",
        "label": "Review default",
        "days": 90,
        "basis": "Demo rule: review consideration within 90 days from date of order.",
    },
    "compliance": {
        "rule_id": "compliance_default_60",
        "label": "Compliance default",
        "days": 60,
        "basis": "Demo rule: compliance follow-up within 60 days unless the court specifies otherwise.",
    },
}


def list_deadline_rules() -> list[dict]:
    return [{"action_type": key, **value} for key, value in DEADLINE_RULES.items()]


def calculate_deadlines(date_of_order: str, action_type: str, override_days: int | None = None) -> dict:
    rule = DEADLINE_RULES.get(action_type, DEADLINE_RULES["compliance"])
    try:
        order_date = datetime.strptime(date_of_order, "%Y-%m-%d")
    except (ValueError, TypeError):
        return {
            "calculated_deadline": "",
            "days_remaining": -1,
            "contempt_risk_level": "low",
            "deadline_rule_id": rule["rule_id"],
            "deadline_basis": "Order date was not available in YYYY-MM-DD format; reviewer must verify deadline manually.",
        }

    days = override_days if override_days is not None else rule["days"]
    deadline = order_date + timedelta(days=days)
    remaining_raw = (deadline.date() - datetime.now().date()).days
    remaining = max(remaining_raw, 0)

    if remaining_raw <= 5:
        risk = "critical"
    elif remaining_raw <= 15:
        risk = "high"
    elif remaining_raw <= 30:
        risk = "medium"
    else:
        risk = "low"

    return {
        "calculated_deadline": deadline.strftime("%Y-%m-%d"),
        "days_remaining": remaining,
        "contempt_risk_level": risk,
        "deadline_rule_id": rule["rule_id"],
        "deadline_basis": rule["basis"],
    }
