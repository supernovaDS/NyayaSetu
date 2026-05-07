"""Deterministic workflow intelligence for verified judgment action plans."""

from datetime import datetime, timedelta

from models.schemas import ActionPlan, ExtractedData, HandoffTask, StakeholderStep
from services.quality_service import classify_case


def _relative_due(days: int) -> str:
    return (datetime.now().date() + timedelta(days=days)).isoformat()


def _service_level(action: ActionPlan) -> tuple[str, str]:
    if action.contempt_risk_level == "critical" or 0 <= action.days_remaining <= 5:
        return (
            "red_lane",
            "Immediate escalation to the department secretary/legal head is recommended because the verified deadline is very close or already critical.",
        )
    if action.contempt_risk_level == "high" or 0 <= action.days_remaining <= 15:
        return (
            "amber_lane",
            "Fast-track review is recommended; legal and department officers should settle the response note within 48 hours.",
        )
    return (
        "green_lane",
        "Standard monitored workflow is sufficient, with dashboard tracking until compliance or appeal decision is closed.",
    )


def enrich_action_plan(extracted: ExtractedData, action: ActionPlan) -> ActionPlan:
    """Add practical handoff details that do not depend on another AI call."""

    category = classify_case(extracted)
    service_level, escalation_note = _service_level(action)
    deadline = action.calculated_deadline or "manual deadline verification"
    action.service_level = service_level
    action.escalation_note = escalation_note
    action.priority_summary = (
        f"{category} case requiring {action.action_type.value} by {deadline}. "
        f"Responsible office: {action.assigned_designation or 'department legal cell'}."
    )

    action.first_48_hours = [
        "Confirm case number, order date, parties, and final operative directions against the highlighted source pages.",
        "Send verified action plan to the responsible office and request comments on feasibility, compliance status, or appeal grounds.",
        "Prepare the file note for approving authority with deadline, risk lane, and evidence-backed directives.",
        "Record the final decision path: comply, file appeal/review, or seek legal clarification.",
    ]

    legal_owner = "Department Legal Cell"
    department_owner = action.assigned_designation or "Administrative Department concerned"
    action.stakeholders = [
        StakeholderStep(
            designation=legal_owner,
            responsibility="Verify legal interpretation, limitation period, and appeal/review maintainability.",
            handoff="Receives source evidence, extracted directives, precedent hints, and draft file note.",
        ),
        StakeholderStep(
            designation=department_owner,
            responsibility="Confirm facts, collect records, and execute compliance or supply grounds for appeal.",
            handoff="Receives the verified action plan and 48-hour task list.",
        ),
        StakeholderStep(
            designation="Approving Authority",
            responsibility="Approve compliance, appeal, review, or speaking order decision before deadline.",
            handoff="Receives printable compliance packet with audit trail.",
        ),
    ]

    action.handoff_checklist = [
        HandoffTask(title="Evidence verification completed", owner=legal_owner, due=_relative_due(1)),
        HandoffTask(title="Department factual comments received", owner=department_owner, due=_relative_due(2)),
        HandoffTask(title="Decision note placed before approving authority", owner=legal_owner, due=_relative_due(3)),
        HandoffTask(title="Compliance/appeal action initiated", owner=department_owner, due=deadline),
    ]

    if not action.draft_file_note:
        action.draft_file_note = (
            f"Reference is made to the judgment dated {extracted.date_of_order or '[date]'} "
            f"in {extracted.case_title or '[case title]'}. The matter requires {action.action_type.value} "
            f"by {deadline}. The responsible office may examine the enclosed source evidence and submit "
            "a time-bound proposal for approval."
        )

    return action
