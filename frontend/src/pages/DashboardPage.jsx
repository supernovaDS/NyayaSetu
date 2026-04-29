import { useEffect, useMemo, useState } from 'react';

const COLUMNS = [
  { id: 'pending_verification', label: 'Pending Verification' },
  { id: 'drafting_note', label: 'Drafting Note' },
  { id: 'awaiting_approval', label: 'Awaiting Approval' },
  { id: 'compliance_submitted', label: 'Compliance Done' },
];

const RISK_FILTERS = [
  { id: 'all', label: 'All' },
  { id: 'urgent', label: '0-7 days' },
  { id: 'critical', label: 'Critical' },
  { id: 'needs_review', label: 'Needs review' },
  { id: 'unverified_deadline', label: 'No deadline' },
];

function AppHeader({ onUpload, onAdmin }) {
  return (
    <header className="app-header">
      <div className="app-header-inner">
        <div className="brand">
          <div className="brand-mark">N</div>
          <div>
            <p className="brand-title">NyayaSetu</p>
            <p className="brand-subtitle">Verified dashboard</p>
          </div>
        </div>
        <nav className="nav-actions">
          <button onClick={onAdmin} className="btn btn-secondary">Admin</button>
          <button onClick={onUpload} className="btn btn-primary">Upload New</button>
        </nav>
      </div>
    </header>
  );
}

function Badge({ level }) {
  return <span className={`badge ${level || 'low'}`}>{level || 'unknown'}</span>;
}

function AuditTrail({ jobId }) {
  const [events, setEvents] = useState(null);
  const [open, setOpen] = useState(false);

  const toggle = async () => {
    const nextOpen = !open;
    setOpen(nextOpen);
    if (!nextOpen || events) return;
    try {
      const response = await fetch(`/api/dashboard/${jobId}/audit`);
      const payload = await response.json();
      setEvents(payload.events || []);
    } catch {
      setEvents([]);
    }
  };

  return (
    <div className="audit-box">
      <button onClick={toggle} className="btn btn-secondary" style={{ padding: '6px 10px', fontSize: 12 }}>
        {open ? 'Hide audit' : 'Audit trail'}
      </button>
      {open && (
        <div style={{ display: 'grid', gap: 8, marginTop: 10 }}>
          {events === null ? (
            <p className="case-meta">Loading audit...</p>
          ) : events.length === 0 ? (
            <p className="case-meta">No audit events found.</p>
          ) : (
            events.map((event, idx) => (
              <div key={`${event.created_at}-${idx}`} className="metric">
                <p className="metric-value">{event.event_type.replaceAll('_', ' ')}</p>
                <p className="metric-label">{event.created_at} by {event.actor}</p>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}

function CaseCard({ c, onMove }) {
  const data = c.extracted_data;
  const plan = c.action_plan;
  const meta = c.review_meta || {};
  const colIdx = COLUMNS.findIndex((col) => col.id === c.kanban_status);
  const canMove = colIdx >= 0 && colIdx < COLUMNS.length - 1;

  return (
    <article className="case-card">
      <div className="case-card-header">
        <div>
          <h4 className="case-title">{data.case_title || 'Untitled Case'}</h4>
          <p className="case-meta">{data.case_number || 'No case number'}</p>
        </div>
        <Badge level={plan.contempt_risk_level} />
      </div>

      <div className="metric-grid">
        <div className="metric">
          <p className="metric-label">Action</p>
          <p className="metric-value">{plan.action_type}</p>
        </div>
        <div className="metric">
          <p className="metric-label">Readiness</p>
          <p className="metric-value" style={{ color: (meta.readiness_score || 0) < 70 ? 'var(--amber)' : 'var(--green)' }}>
            {meta.readiness_score ?? 0}/100
          </p>
        </div>
      </div>

      <p className="case-meta" style={{ marginTop: 12 }}>
        <strong style={{ color: 'var(--ink)' }}>Category:</strong> {meta.case_category || 'General'}
      </p>
      <p className="case-meta" style={{ marginTop: 12 }}>
        <strong style={{ color: 'var(--ink)' }}>Office:</strong> {plan.assigned_designation || 'Not assigned'}
      </p>
      <p className="case-meta">Deadline: {plan.calculated_deadline || 'Manual review required'} {plan.days_remaining >= 0 ? `(${plan.days_remaining} days left)` : ''}</p>
      {(meta.flags || []).slice(0, 2).map((flag, index) => (
        <p key={`${flag.title}-${index}`} className="case-meta" style={{ color: flag.severity === 'critical' ? 'var(--red)' : 'var(--amber)' }}>
          {flag.severity}: {flag.title}
        </p>
      ))}
      <p className="case-meta">Verified by {c.verified_by || 'Demo Reviewer'} ({c.verified_role || 'legal_reviewer'})</p>

      <div className="card-actions">
        {canMove && <button onClick={() => onMove(c.job_id, COLUMNS[colIdx + 1].id)} className="btn btn-primary">Move next</button>}
        <a href={`/api/dashboard/${c.job_id}/packet.html`} target="_blank" rel="noreferrer" className="btn btn-secondary">Print</a>
        <a href={`/api/dashboard/${c.job_id}/packet`} className="btn btn-secondary">TXT</a>
      </div>

      <AuditTrail jobId={c.job_id} />
    </article>
  );
}

function matchesRiskFilter(c, filter) {
  const plan = c.action_plan || {};
  if (filter === 'all') return true;
  if (filter === 'urgent') return Number.isFinite(plan.days_remaining) && plan.days_remaining >= 0 && plan.days_remaining <= 7;
  if (filter === 'critical') return plan.contempt_risk_level === 'critical';
  if (filter === 'needs_review') return (c.review_meta?.readiness_score ?? 100) < 75 || (c.review_meta?.flags || []).some((flag) => flag.severity === 'critical');
  if (filter === 'unverified_deadline') return !plan.calculated_deadline || plan.days_remaining < 0;
  return true;
}

export default function DashboardPage({ onUpload, onAdmin }) {
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [riskFilter, setRiskFilter] = useState('all');

  const fetchCases = async () => {
    try {
      const res = await fetch('/api/dashboard');
      const data = await res.json();
      setCases(data.cases || []);
    } catch {
      setCases([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let cancelled = false;
    async function loadCases() {
      try {
        const res = await fetch('/api/dashboard');
        const data = await res.json();
        if (!cancelled) setCases(data.cases || []);
      } catch {
        if (!cancelled) setCases([]);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    loadCases();
    return () => { cancelled = true; };
  }, []);

  const moveCase = async (jobId, newStatus) => {
    await fetch(`/api/dashboard/${jobId}/status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ kanban_status: newStatus, actor: 'Demo Reviewer' }),
    });
    fetchCases();
  };

  const filteredCases = useMemo(
    () => cases
      .filter((c) => matchesRiskFilter(c, riskFilter))
      .sort((a, b) => (a.action_plan.days_remaining ?? 9999) - (b.action_plan.days_remaining ?? 9999)),
    [cases, riskFilter],
  );

  const urgentCount = cases.filter((c) => matchesRiskFilter(c, 'urgent')).length;
  const criticalCount = cases.filter((c) => matchesRiskFilter(c, 'critical')).length;
  const missingDeadlineCount = cases.filter((c) => matchesRiskFilter(c, 'unverified_deadline')).length;
  const needsReviewCount = cases.filter((c) => matchesRiskFilter(c, 'needs_review')).length;
  const minutesSaved = cases.reduce((sum, c) => sum + (c.review_meta?.estimated_minutes_saved || 0), 0);
  const averageReadiness = cases.length
    ? Math.round(cases.reduce((sum, c) => sum + (c.review_meta?.readiness_score || 0), 0) / cases.length)
    : 0;

  return (
    <div className="app-page">
      <AppHeader onUpload={onUpload} onAdmin={onAdmin} />
      <main className="container dashboard-main">
        <section className="panel radar-panel">
          <div>
            <h1 className="panel-title">Contempt Risk Radar</h1>
            <p className="panel-copy">
              {urgentCount} urgent, {criticalCount} critical, {needsReviewCount} need review, {missingDeadlineCount} missing deadline
            </p>
            <p className="panel-copy">Average readiness {averageReadiness}/100 · Estimated review time saved {minutesSaved} minutes</p>
          </div>
          <div className="filter-row">
            {RISK_FILTERS.map((filter) => (
              <button
                key={filter.id}
                onClick={() => setRiskFilter(filter.id)}
                className={`filter-chip ${riskFilter === filter.id ? 'active' : ''}`}
              >
                {filter.label}
              </button>
            ))}
          </div>
        </section>

        {loading ? (
          <div className="empty-state">
            <div>
              <div className="empty-icon">...</div>
              <h2 className="panel-title">Loading cases</h2>
            </div>
          </div>
        ) : filteredCases.length === 0 ? (
          <div className="empty-state">
            <div>
              <div className="empty-icon">0</div>
              <h2 className="panel-title">No cases match this view</h2>
              <p className="panel-copy">Upload and approve a judgment, or change the risk filter.</p>
              <button onClick={onUpload} className="btn btn-primary" style={{ marginTop: 18 }}>Upload judgment</button>
            </div>
          </div>
        ) : (
          <div className="kanban-grid">
            {COLUMNS.map((col) => {
              const colCases = filteredCases.filter((c) => c.kanban_status === col.id);
              return (
                <section key={col.id}>
                  <div className="kanban-column-title">
                    <span>{col.label}</span>
                    <span className="count-pill">{colCases.length}</span>
                  </div>
                  <div className="case-stack">
                    {colCases.map((c) => <CaseCard key={c.job_id} c={c} onMove={moveCase} />)}
                  </div>
                </section>
              );
            })}
          </div>
        )}
      </main>
    </div>
  );
}
