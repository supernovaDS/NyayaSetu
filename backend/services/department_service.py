"""Deterministic department routing hints for the review workflow."""

ROUTING_RULES = [
    (
        ("land acquisition", "compensation", "revenue", "acquired land"),
        "Revenue Department / Land Acquisition Officer",
    ),
    (
        ("appointment", "promotion", "seniority", "service", "reinstatement", "salary", "pay scale"),
        "Department of Personnel and Administrative Reforms",
    ),
    (
        ("pension", "retirement", "gratuity"),
        "Finance Department / Pension Sanctioning Authority",
    ),
    (
        ("school", "teacher", "education", "student"),
        "Education Department",
    ),
    (
        ("police", "fir", "law and order"),
        "Home Department",
    ),
    (
        ("municipal", "urban", "building", "town planning"),
        "Urban Development Department / Municipal Commissioner",
    ),
    (
        ("forest", "environment", "pollution", "clearance"),
        "Environment, Forest and Climate Change Department",
    ),
    (
        ("road", "highway", "bridge", "contractor", "tender", "works"),
        "Public Works Department",
    ),
]


def route_department(directives: list[str], parties: list[str]) -> dict:
    text = " ".join([*directives, *parties]).lower()
    for keywords, department in ROUTING_RULES:
        if any(keyword in text for keyword in keywords):
            matched = [keyword for keyword in keywords if keyword in text]
            return {
                "department": department,
                "reason": f"Matched court directive keywords: {', '.join(matched[:3])}.",
            }

    return {
        "department": "Administrative Department concerned / Legal Cell",
        "reason": "No domain-specific keyword matched; route to the department's legal cell for assignment.",
    }
