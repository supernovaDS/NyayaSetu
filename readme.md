# NyayaSetu

NyayaSetu is an AI-assisted court judgment processing system for government departments. It converts long, unstructured judgment PDFs into verified action plans, source-backed evidence, deadline risk views, draft file notes, precedent hints, and a compliance dashboard.

The core idea is simple: AI can help read and structure a judgment, but only human-verified records should move into government decision workflows.

## What Problem It Solves

Government departments often receive court orders and final judgments as PDFs. These documents can be long, scanned, inconsistent, and legally dense. Officials must manually identify:

- case details
- date of order
- parties and government role
- final directions
- compliance requirements
- appeal or review urgency
- responsible department
- important deadlines

Manual reading can delay compliance and increase the risk of missed deadlines or contempt proceedings. NyayaSetu reduces that risk by turning judgments into a verified, trackable workflow.

## What The Application Does

NyayaSetu provides an end-to-end workflow:

1. Upload a court judgment PDF.
2. AI identifies the most important pages instead of processing every page heavily.
3. AI extracts structured legal data and an action plan.
4. The backend calculates deadline and risk metadata.
5. The system attaches source quotes and PDF-page evidence.
6. A human reviewer edits and approves the extracted data.
7. Only approved records appear in the dashboard.
8. Decision makers track the case through a Kanban compliance workflow.
9. The system exports a compliance packet containing verified data, source evidence, draft file note, review flags, and audit trail.

## Key Features

### Two-Pass Judgment Extraction

NyayaSetu uses a two-pass extraction pipeline:

- Pass 1: PyMuPDF extracts text from all pages. Gemini identifies pages likely to contain metadata, final orders, directions, and timelines.
- Pass 2: only those critical pages are rendered as images and sent to Gemini vision for structured extraction.

This keeps the demo fast and makes long PDFs easier to handle.

### Human Verification

The review screen is intentionally not a blind AI output screen. The reviewer can edit:

- case title
- case number
- order date
- state role
- parties
- directives
- timelines
- action type
- deadline
- responsible office
- reasoning
- file note

The approved version, not the raw AI version, is stored.

### Source Evidence Viewer

Each important field is paired with source evidence:

- source page
- source quote
- confidence
- bounding-box highlight when the quote can be located by PyMuPDF

The review UI renders the PDF page and highlights the supporting area when available.

### Decision Readiness Score

NyayaSetu computes a readiness score for every extracted judgment. It flags missing fields, low confidence, missing evidence, missing deadlines, and urgent deadlines. This gives judges and reviewers an immediate trust signal.

### Deadline Assist

The system applies deterministic demo rules:

- appeal: 30 days
- review: 90 days
- compliance: 60 days

The reviewer can recalculate the deadline with override days and record an override reason.

### Department Routing

The backend suggests a responsible department using deterministic keyword rules. Example categories include service matters, land acquisition, pension, environment, education, public works, and home/police.

### Precedent Intelligence

NyayaSetu searches a curated local precedent set using Gemini embeddings and cosine similarity. It shows similar cases, similarity score, previous outcome, and action taken.

### Persistent Dashboard

Approved records are stored in SQLite and shown in a Kanban board:

- Pending Verification
- Drafting Note
- Awaiting Approval
- Compliance Done

The dashboard includes risk filters, readiness metadata, audit trail, packet export, and printable packet view.

## Tech Stack

### Frontend

- React
- Vite
- Tailwind CSS
- Custom CSS design system

### Backend

- FastAPI
- Pydantic
- SQLite
- PyMuPDF
- Google Gemini API

### AI

- Gemini model for page finding and multimodal extraction
- Gemini `text-embedding-004` for precedent search embeddings

### Storage

- Uploaded PDFs: `backend/uploads/`
- Approved cases and audit events: `backend/nyayasetu.db`

## Project Structure

```text
NyayaSetu/
  backend/
    main.py
    models/
      schemas.py
    routes/
      admin.py
      dashboard.py
      deadline.py
      pdf.py
      precedents.py
      upload.py
    services/
      deadline_service.py
      department_service.py
      extraction_service.py
      llm_service.py
      pdf_service.py
      precedent_service.py
      quality_service.py
      settings_service.py
      storage_service.py
      vision_service.py
    requirements.txt
  frontend/
    src/
      App.jsx
      main.jsx
      index.css
      pages/
        AdminPage.jsx
        DashboardPage.jsx
        ReviewPage.jsx
        UploadPage.jsx
    package.json
  problem_statement.md
  features.md
  implementation.md
  working.md
  developer_plan.md
  demo.md
  future_roadmap.md
```

## Setup

### Prerequisites

- Python 3.10+
- Node.js 18+
- Google Gemini API key

### Backend

```bash
cd backend
pip install -r requirements.txt
```

Create `backend/.env`:

```env
GEMINI_API_KEY=your_api_key_here
```

Run the backend:

```bash
python -m uvicorn main:app --reload --port 8000
```

Health check:

```bash
http://127.0.0.1:8000/health
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open:

```text
http://127.0.0.1:5173
```

## How To Use

1. Open the app at `http://127.0.0.1:5173`.
2. Upload a court judgment PDF from the upload page.
3. Wait while the two-pass extraction pipeline runs.
4. On the review page, inspect the PDF evidence on the left.
5. Click source evidence cards to jump to the relevant PDF page and highlight.
6. Edit extracted case data if required.
7. Review the action plan, deadline rule, department routing, and risk level.
8. Check the decision readiness score and review flags.
9. Edit the file note draft.
10. Enter reviewer name and role.
11. Approve the verified record.
12. Open the dashboard.
13. Filter cases by urgency, criticality, readiness, or missing deadline.
14. Move cases through workflow columns.
15. Open the audit trail or export the compliance packet.

## Verification Commands

```bash
python -m compileall backend
cd frontend
npm run lint
npm run build
```

## Current Limitations

- Deadline rules are demo defaults and should not be treated as legal advice.
- Authentication and role-based access control are not implemented yet.
- Source highlighting depends on selectable text; scanned PDFs may fall back to page-level evidence.
- SQLite is suitable for the hackathon demo, but production should use PostgreSQL/Supabase or another managed database.

## Why This Is Hackathon-Relevant

NyayaSetu directly matches the problem statement: it reads judgment PDFs, extracts key information, generates action plans, requires human verification, and displays only approved records in a dashboard. The differentiator is trust: every important output is editable, source-backed, scored, audited, and exportable.
