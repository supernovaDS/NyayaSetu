from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse
from pydantic import BaseModel, Field
from html import escape
from services.storage_service import (
    get_audit_events,
    get_case,
    list_cases,
    save_approved_case,
    update_case_status,
)

router = APIRouter()

KANBAN_ORDER = ["pending_verification", "drafting_note", "awaiting_approval", "compliance_submitted"]


class ApproveRequest(BaseModel):
    job_id: str
    extracted_data: dict
    action_plan: dict
    source_evidence: dict = Field(default_factory=dict)
    review_meta: dict = Field(default_factory=dict)
    verified_by: str = "Demo Reviewer"
    verified_role: str = "legal_reviewer"
    edits: dict = Field(default_factory=dict)


class StatusUpdate(BaseModel):
    kanban_status: str
    actor: str = "Demo Reviewer"


@router.post("/approve")
async def approve_case(req: ApproveRequest):
    save_approved_case(
        req.job_id,
        req.extracted_data,
        req.action_plan,
        req.source_evidence,
        req.review_meta,
        req.verified_by,
        req.verified_role,
        req.edits,
    )
    return {"job_id": req.job_id, "status": "approved"}


@router.get("/dashboard")
async def get_dashboard():
    return {"cases": list_cases()}


@router.patch("/dashboard/{job_id}/status")
async def update_status(job_id: str, body: StatusUpdate):
    if body.kanban_status not in KANBAN_ORDER:
        raise HTTPException(status_code=400, detail="Invalid status")
    if not update_case_status(job_id, body.kanban_status, body.actor):
        raise HTTPException(status_code=404, detail="Case not found")
    return {"status": "updated"}


@router.get("/dashboard/{job_id}/audit")
async def get_audit(job_id: str):
    if get_case(job_id) is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return {"events": get_audit_events(job_id)}


@router.get("/dashboard/{job_id}/packet")
async def get_compliance_packet(job_id: str):
    case = get_case(job_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found")

    data = case["extracted_data"]
    plan = case["action_plan"]
    evidence = case.get("source_evidence", {})
    review_meta = case.get("review_meta", {})
    events = get_audit_events(job_id)

    lines = [
        "NYAYASETU VERIFIED COMPLIANCE PACKET",
        "=" * 43,
        "",
        f"Case title: {data.get('case_title', '')}",
        f"Case number: {data.get('case_number', '')}",
        f"Date of order: {data.get('date_of_order', '')}",
        f"State role: {data.get('state_role', '')}",
        f"Verified by: {case.get('verified_by', '')}",
        f"Reviewer role: {case.get('verified_role', '')}",
        f"Case category: {review_meta.get('case_category', '')}",
        f"Triage lane: {review_meta.get('triage_lane', '')}",
        f"Decision readiness score: {review_meta.get('readiness_score', '')}/100",
        f"Source coverage: {review_meta.get('source_coverage', '')}%",
        f"Confidence label: {review_meta.get('confidence_label', '')}",
        f"Estimated minutes saved: {review_meta.get('estimated_minutes_saved', '')}",
        f"Approved at: {case.get('approved_at', '')}",
        "",
        "IMPACT BRIEF",
        "-" * 12,
        review_meta.get("impact_summary", ""),
        "",
        "ACTION PLAN",
        "-" * 11,
        f"Action type: {plan.get('action_type', '')}",
        f"Responsible office: {plan.get('assigned_designation', '')}",
        f"Deadline: {plan.get('calculated_deadline', '')}",
        f"Days remaining: {plan.get('days_remaining', '')}",
        f"Risk level: {plan.get('contempt_risk_level', '')}",
        f"Service level: {plan.get('service_level', '')}",
        f"Priority summary: {plan.get('priority_summary', '')}",
        f"Escalation note: {plan.get('escalation_note', '')}",
        "",
        "DIRECTIVES",
        "-" * 10,
    ]
    for idx, directive in enumerate(data.get("directives", []), start=1):
        lines.append(f"{idx}. {directive}")

    lines.extend(["", "DRAFT FILE NOTE", "-" * 15, plan.get("draft_file_note", "")])

    lines.extend(["", "FIRST 48 HOURS", "-" * 14])
    for idx, task in enumerate(plan.get("first_48_hours", []), start=1):
        lines.append(f"{idx}. {task}")

    lines.extend(["", "STAKEHOLDER HANDOFF", "-" * 19])
    for item in plan.get("stakeholders", []):
        lines.append(f"{item.get('designation', '')}: {item.get('responsibility', '')}")
        lines.append(f"  Handoff: {item.get('handoff', '')}")

    lines.extend(["", "CHECKLIST", "-" * 9])
    for item in plan.get("handoff_checklist", []):
        lines.append(f"- {item.get('title', '')} | {item.get('owner', '')} | Due {item.get('due', '')} | {item.get('status', '')}")

    lines.extend(["", "SOURCE EVIDENCE", "-" * 15])
    for key, item in evidence.items():
        try:
            confidence = float(item.get("confidence", 0))
        except (TypeError, ValueError):
            confidence = 0.0
        lines.append(f"{key} (page {item.get('page', '-')}, confidence {confidence:.0%})")
        lines.append(f"  {item.get('quote', '')}")

    lines.extend(["", "REVIEW FLAGS", "-" * 12])
    for flag in review_meta.get("flags", []):
        lines.append(f"{flag.get('severity', 'info').upper()}: {flag.get('title', '')} - {flag.get('detail', '')}")

    lines.extend(["", "AUDIT TRAIL", "-" * 11])
    for event in events:
        lines.append(f"{event['created_at']} | {event['actor']} | {event['event_type']} | {event['details']}")

    content = "\n".join(lines)
    return PlainTextResponse(
        content,
        media_type="text/plain",
        headers={"Content-Disposition": f'attachment; filename="nyayasetu-{job_id}-packet.txt"'},
    )


@router.get("/dashboard/{job_id}/packet.html")
async def get_compliance_packet_html(job_id: str):
    case = get_case(job_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found")

    data = case["extracted_data"]
    plan = case["action_plan"]
    evidence = case.get("source_evidence", {})
    review_meta = case.get("review_meta", {})
    events = get_audit_events(job_id)

    directives = "".join(f"<li>{escape(str(directive))}</li>" for directive in data.get("directives", []))
    first_48 = "".join(f"<li>{escape(str(task))}</li>" for task in plan.get("first_48_hours", []))
    stakeholders = "".join(
        f"<tr><td>{escape(str(item.get('designation', '')))}</td>"
        f"<td>{escape(str(item.get('responsibility', '')))}</td>"
        f"<td>{escape(str(item.get('handoff', '')))}</td></tr>"
        for item in plan.get("stakeholders", [])
    )
    checklist = "".join(
        f"<tr><td>{escape(str(item.get('title', '')))}</td>"
        f"<td>{escape(str(item.get('owner', '')))}</td>"
        f"<td>{escape(str(item.get('due', '')))}</td>"
        f"<td>{escape(str(item.get('status', '')))}</td></tr>"
        for item in plan.get("handoff_checklist", [])
    )
    evidence_rows = ""
    for key, item in evidence.items():
        try:
            confidence = float(item.get("confidence", 0))
        except (TypeError, ValueError):
            confidence = 0.0
        evidence_rows += (
            f"<tr><td>{escape(str(key))}</td><td>{escape(str(item.get('page', '-')))}</td>"
            f"<td>{confidence:.0%}</td><td>{escape(str(item.get('quote', '')))}</td></tr>"
        )
    audit_rows = "".join(
        f"<tr><td>{escape(str(event['created_at']))}</td><td>{escape(str(event['actor']))}</td><td>{escape(str(event['event_type']))}</td><td>{escape(str(event['details']))}</td></tr>"
        for event in events
    )
    flag_rows = "".join(
        f"<tr><td>{escape(str(flag.get('severity', 'info')))}</td><td>{escape(str(flag.get('title', '')))}</td><td>{escape(str(flag.get('detail', '')))}</td></tr>"
        for flag in review_meta.get("flags", [])
    )

    html = f"""
    <!doctype html>
    <html>
    <head>
      <meta charset="utf-8" />
      <title>NyayaSetu Compliance Packet</title>
      <style>
        body {{ font-family: Arial, sans-serif; color: #111827; margin: 40px; line-height: 1.45; }}
        h1 {{ font-size: 24px; margin: 0 0 4px; }}
        h2 {{ font-size: 15px; margin-top: 28px; border-bottom: 1px solid #d1d5db; padding-bottom: 6px; }}
        .muted {{ color: #6b7280; font-size: 12px; }}
        .grid {{ display: grid; grid-template-columns: 180px 1fr; gap: 8px 16px; font-size: 13px; }}
        table {{ border-collapse: collapse; width: 100%; font-size: 12px; }}
        th, td {{ border: 1px solid #d1d5db; padding: 8px; vertical-align: top; }}
        th {{ background: #f3f4f6; text-align: left; }}
        .note {{ white-space: pre-wrap; background: #f9fafb; border: 1px solid #e5e7eb; padding: 14px; }}
        @media print {{ body {{ margin: 20mm; }} .no-print {{ display: none; }} }}
      </style>
    </head>
    <body>
      <button class="no-print" onclick="window.print()">Print / Save as PDF</button>
      <h1>NyayaSetu Verified Compliance Packet</h1>
      <p class="muted">Generated from human-verified action plan.</p>

      <h2>Case</h2>
      <div class="grid">
        <strong>Case title</strong><span>{escape(str(data.get('case_title', '')))}</span>
        <strong>Case number</strong><span>{escape(str(data.get('case_number', '')))}</span>
        <strong>Date of order</strong><span>{escape(str(data.get('date_of_order', '')))}</span>
        <strong>State role</strong><span>{escape(str(data.get('state_role', '')))}</span>
        <strong>Verified by</strong><span>{escape(str(case.get('verified_by', '')))} ({escape(str(case.get('verified_role', '')))})</span>
        <strong>Case category</strong><span>{escape(str(review_meta.get('case_category', '')))}</span>
        <strong>Triage lane</strong><span>{escape(str(review_meta.get('triage_lane', '')))}</span>
        <strong>Readiness score</strong><span>{escape(str(review_meta.get('readiness_score', '')))}/100</span>
        <strong>Source coverage</strong><span>{escape(str(review_meta.get('source_coverage', '')))}%</span>
        <strong>Estimated time saved</strong><span>{escape(str(review_meta.get('estimated_minutes_saved', '')))} minutes</span>
      </div>

      <h2>Impact Brief</h2>
      <div class="note">{escape(str(review_meta.get('impact_summary', '')))}</div>

      <h2>Action Plan</h2>
      <div class="grid">
        <strong>Action type</strong><span>{escape(str(plan.get('action_type', '')))}</span>
        <strong>Responsible office</strong><span>{escape(str(plan.get('assigned_designation', '')))}</span>
        <strong>Deadline</strong><span>{escape(str(plan.get('calculated_deadline', '')))}</span>
        <strong>Rule applied</strong><span>{escape(str(plan.get('deadline_rule_id', '')))}</span>
        <strong>Risk level</strong><span>{escape(str(plan.get('contempt_risk_level', '')))}</span>
        <strong>Service level</strong><span>{escape(str(plan.get('service_level', '')))}</span>
        <strong>Priority summary</strong><span>{escape(str(plan.get('priority_summary', '')))}</span>
      </div>

      <h2>Directives</h2>
      <ol>{directives}</ol>

      <h2>Draft File Note</h2>
      <div class="note">{escape(str(plan.get('draft_file_note', '')))}</div>

      <h2>First 48 Hours</h2>
      <ol>{first_48}</ol>

      <h2>Stakeholder Handoff</h2>
      <table><thead><tr><th>Designation</th><th>Responsibility</th><th>Handoff</th></tr></thead><tbody>{stakeholders}</tbody></table>

      <h2>Checklist</h2>
      <table><thead><tr><th>Task</th><th>Owner</th><th>Due</th><th>Status</th></tr></thead><tbody>{checklist}</tbody></table>

      <h2>Source Evidence</h2>
      <table><thead><tr><th>Field</th><th>Page</th><th>Confidence</th><th>Quote</th></tr></thead><tbody>{evidence_rows}</tbody></table>

      <h2>Review Flags</h2>
      <table><thead><tr><th>Severity</th><th>Flag</th><th>Detail</th></tr></thead><tbody>{flag_rows}</tbody></table>

      <h2>Audit Trail</h2>
      <table><thead><tr><th>Time</th><th>Actor</th><th>Event</th><th>Details</th></tr></thead><tbody>{audit_rows}</tbody></table>
    </body>
    </html>
    """
    return HTMLResponse(html)
