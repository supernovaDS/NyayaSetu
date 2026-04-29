import { useCallback, useState } from 'react';

const STEPS = [
  'Uploading PDF',
  'Reading page text',
  'Finding critical pages',
  'Extracting with vision',
  'Preparing verified review',
];

function AppHeader({ onDashboard, onAdmin }) {
  return (
    <header className="app-header">
      <div className="app-header-inner">
        <div className="brand">
          <div className="brand-mark">N</div>
          <div>
            <p className="brand-title">NyayaSetu</p>
            <p className="brand-subtitle">Judgment to action plan</p>
          </div>
        </div>
        <nav className="nav-actions">
          <button onClick={onDashboard} className="btn btn-secondary">Dashboard</button>
          <button onClick={onAdmin} className="btn btn-secondary">Admin</button>
        </nav>
      </div>
    </header>
  );
}

export default function UploadPage({ onResult, onDashboard, onAdmin }) {
  const [dragging, setDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState(0);
  const [error, setError] = useState(null);

  const handleFile = useCallback(async (file) => {
    if (!file || !file.name.toLowerCase().endsWith('.pdf')) {
      setError('Upload a PDF judgment to continue.');
      return;
    }

    setLoading(true);
    setError(null);
    setStep(0);

    const interval = setInterval(() => {
      setStep((s) => (s < STEPS.length - 1 ? s + 1 : s));
    }, 3500);

    try {
      const formData = new FormData();
      formData.append('file', file);
      const res = await fetch('/api/upload', { method: 'POST', body: formData });
      clearInterval(interval);
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || `Server error: ${res.status}`);
      }
      onResult(await res.json());
    } catch (err) {
      clearInterval(interval);
      setError(err.message || 'Upload failed. Please try again.');
      setLoading(false);
    }
  }, [onResult]);

  const onDrop = useCallback((e) => {
    e.preventDefault();
    setDragging(false);
    handleFile(e.dataTransfer.files?.[0]);
  }, [handleFile]);

  const onFileSelect = useCallback((e) => {
    handleFile(e.target.files?.[0]);
  }, [handleFile]);

  return (
    <div className="app-page">
      <AppHeader onDashboard={onDashboard} onAdmin={onAdmin} />
      <main className="container upload-main">
        <section>
          <p className="eyebrow">Verified court compliance</p>
          <h1 className="hero-title">Court judgments, converted into verified action plans.</h1>
          <p className="hero-copy">
            Extract directives, calculate deadlines, route departments, verify evidence, and move approved cases into a focused compliance dashboard.
          </p>
          <div className="feature-row">
            <span className="feature-pill">Source evidence</span>
            <span className="feature-pill">Human approval</span>
            <span className="feature-pill">Audit trail</span>
          </div>
        </section>

        <section className="upload-card">
          {!loading ? (
            <div
              onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
              onDragLeave={() => setDragging(false)}
              onDrop={onDrop}
              onClick={() => document.getElementById('file-input').click()}
              className={`drop-zone ${dragging ? 'dragging' : ''}`}
            >
              <input id="file-input" type="file" accept=".pdf" hidden onChange={onFileSelect} />
              <div className="upload-icon">
                <svg width="28" height="28" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M12 16V4m0 0 4 4m-4-4-4 4M4 16v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2" />
                </svg>
              </div>
              <p className="drop-title">Upload judgment PDF</p>
              <p className="drop-copy">Drag and drop a scanned or digital court judgment, or click to browse.</p>
            </div>
          ) : (
            <div className="progress-card">
              <h2 className="panel-title">Processing judgment</h2>
              <p className="panel-copy">Keep this tab open while NyayaSetu prepares the review workspace.</p>
              <div className="step-list">
                {STEPS.map((label, i) => (
                  <div key={label} className={`step-item ${i < step ? 'done' : ''} ${i === step ? 'active' : ''}`}>
                    <span className="step-dot">{i < step ? '✓' : i + 1}</span>
                    <span>{label}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
          {error && <div className="error-box">{error}</div>}
        </section>
      </main>
    </div>
  );
}
