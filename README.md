# NyayaSetu

NyayaSetu converts court judgment PDFs into evidence-backed, human-verified government action plans. It is built for departments that receive disposed case judgments and need to quickly identify directives, deadlines, responsible offices, compliance risk, and next actions.

The application is not a generic PDF summarizer. It is a workflow system: AI assists extraction, deterministic services calculate risk and handoff details, and only human-approved records enter the trusted dashboard.

## Highlights

- Upload scanned or digital judgment PDFs.
- Two-pass pipeline finds critical pages before vision extraction.
- Extracts case title, case number, order date, parties, directives, timelines, and confidence.
- Generates action plan: compliance, appeal, or review.
- Calculates deadline and contempt risk using deterministic rules.
- Routes the case to a likely responsible department.
- Shows source evidence with page, quote, confidence, and optional PDF highlight.
- Requires human review and approval before dashboard entry.
- Adds operational intelligence: priority summary, service lane, escalation note, first-48-hour checklist, stakeholders, and handoff tasks.
- Tracks approved cases on a verified dashboard with risk filters, next deadlines, department load, audit trail, and packet export.

## Tech Stack

Backend:

- FastAPI
- Pydantic
- SQLite
- PyMuPDF
- Google Gemini API

Frontend:

- React
- Vite
- Tailwind CSS
- custom CSS

AI:

- Gemini model for critical page selection and multimodal extraction
- Gemini `text-embedding-004` for curated precedent search

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
      intelligence_service.py
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
      index.css
      pages/
        AdminPage.jsx
        DashboardPage.jsx
        ReviewPage.jsx
        UploadPage.jsx
    package.json
  description.md
  developer.md
  demo.md
  features.md
  implementation.md
  ppt.md
  problem_statement.md
```

## Setup

### Backend

```bash
cd backend
pip install -r requirements.txt
```

Create `backend/.env`:

```env
GEMINI_API_KEY=your_api_key_here
```

Run:

```bash
python -m uvicorn main:app --reload --port 8000
```

Health check:

```text
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

## Usage

1. Open the upload screen.
2. Upload a court judgment PDF.
3. Wait for critical page detection and extraction.
4. Review extracted fields beside PDF evidence.
5. Edit directives, deadlines, action type, responsible office, and file note if needed.
6. Check readiness score, evidence coverage, impact brief, service lane, and first-48-hour handoff.
7. Approve as a reviewer.
8. Use the dashboard to track risk, department load, next deadlines, audit trail, and compliance packet.

## Verification

```bash
python -m compileall backend
cd frontend
npm run lint
npm run build
```

## Demo Guide

Read `demo.md` for a full hackathon demo script and PDF selection strategy.

Read `developer.md` for a complete technical explanation, architecture, features, judge Q&A preparation, and implementation notes.
