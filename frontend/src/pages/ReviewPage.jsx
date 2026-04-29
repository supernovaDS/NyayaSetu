import { useEffect, useMemo, useState } from 'react';

const ROLES = [
  { id: 'legal_reviewer', label: 'Legal Reviewer' },
  { id: 'department_officer', label: 'Department Officer' },
  { id: 'approving_authority', label: 'Approving Authority' },
  { id: 'admin', label: 'Admin' },
];

function Badge({ level }) {
  const colors = {
    critical: 'bg-red-100 text-red-700 border-red-200',
    high: 'bg-orange-100 text-orange-700 border-orange-200',
    medium: 'bg-amber-100 text-amber-800 border-amber-200',
    low: 'bg-emerald-100 text-emerald-700 border-emerald-200',
  };
  return (
    <span className={`rounded-full border px-2.5 py-1 text-xs font-semibold uppercase ${colors[level] || colors.low}`}>
      {level || 'low'}
    </span>
  );
}

function PdfEvidenceViewer({ jobId, selectedEvidence }) {
  const page = selectedEvidence?.page || 1;
  const bbox = selectedEvidence?.bbox || [];
  const hasBox = bbox.length === 4;

  return (
    <div className="flex h-full flex-col bg-slate-100">
      <div className="flex h-12 items-center justify-between border-b border-[var(--border)] bg-white px-4">
        <div>
          <p className="text-sm font-semibold">Source Page {page}</p>
          <p className="text-xs text-[var(--text-muted)]">Evidence highlight is shown when text coordinates are available.</p>
        </div>
        {selectedEvidence?.confidence !== undefined && (
          <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs text-[var(--text-secondary)]">
            {Math.round((selectedEvidence.confidence || 0) * 100)}% evidence
          </span>
        )}
      </div>
      <div className="flex-1 overflow-auto p-5">
        <div className="relative mx-auto w-full max-w-[860px] shadow-sm">
          <img
            src={`/api/pdf/${jobId}/page/${page}`}
            alt={`Judgment page ${page}`}
            className="block w-full rounded-lg border border-[var(--border)] bg-white"
          />
          {hasBox && (
            <div
              className="absolute rounded-sm border-2 border-blue-600 bg-blue-500/20 ring-4 ring-blue-500/10"
              style={{
                left: `${bbox[0] * 100}%`,
                top: `${bbox[1] * 100}%`,
                width: `${(bbox[2] - bbox[0]) * 100}%`,
                height: `${Math.max((bbox[3] - bbox[1]) * 100, 1.2)}%`,
              }}
            />
          )}
        </div>
      </div>
    </div>
  );
}

function Evidence({ item, onSelect }) {
  if (!item?.quote) return null;
  return (
    <button
      type="button"
      onClick={() => onSelect(item)}
      className="mt-2 block w-full rounded-lg border border-blue-100 bg-blue-50 p-3 text-left transition hover:border-blue-300"
    >
      <div className="mb-1 flex items-center justify-between gap-3">
        <span className="text-[10px] font-semibold uppercase text-blue-700">Source evidence</span>
        {item.page > 0 && <span className="text-xs text-blue-700">Page {item.page}</span>}
      </div>
      <p className="text-xs leading-relaxed text-slate-700">{item.quote}</p>
    </button>
  );
}

function TextInput({ label, value, onChange, evidence, onSelectEvidence }) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs font-semibold uppercase text-[var(--text-muted)]">{label}</span>
      <input
        value={value || ''}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-lg border border-[var(--border)] bg-white px-3 py-2 text-sm outline-none transition focus:border-[var(--accent)] focus:ring-4 focus:ring-blue-100"
      />
      <Evidence item={evidence} onSelect={onSelectEvidence} />
    </label>
  );
}

function TextArea({ label, value, onChange, evidence, onSelectEvidence, rows = 5 }) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs font-semibold uppercase text-[var(--text-muted)]">{label}</span>
      <textarea
        value={value || ''}
        rows={rows}
        onChange={(e) => onChange(e.target.value)}
        className="w-full resize-y rounded-lg border border-[var(--border)] bg-white px-3 py-2 text-sm leading-relaxed outline-none transition focus:border-[var(--accent)] focus:ring-4 focus:ring-blue-100"
      />
      <Evidence item={evidence} onSelect={onSelectEvidence} />
    </label>
  );
}

function SelectInput({ label, value, onChange, children }) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs font-semibold uppercase text-[var(--text-muted)]">{label}</span>
      <select
        value={value || ''}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-lg border border-[var(--border)] bg-white px-3 py-2 text-sm outline-none transition focus:border-[var(--accent)] focus:ring-4 focus:ring-blue-100"
      >
        {children}
      </select>
    </label>
  );
}

function ReviewReadiness({ meta }) {
  const score = meta?.readiness_score ?? 0;
  const flags = meta?.flags || [];
  return (
    <div className="rounded-xl border border-[var(--border)] bg-white p-4">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase text-[var(--text-muted)]">Decision readiness</p>
          <p className="mt-1 text-2xl font-bold">{score}/100</p>
          <p className="mt-1 text-sm text-[var(--text-muted)]">{meta?.case_category || 'General'} matter</p>
        </div>
        <div className="text-right">
          <p className="text-xs font-semibold uppercase text-[var(--text-muted)]">Time saved</p>
          <p className="mt-1 text-lg font-bold">{meta?.estimated_minutes_saved || 0} min</p>
          <p className="mt-1 text-xs text-[var(--text-muted)]">{meta?.pages_reduced || 0} pages skipped</p>
        </div>
      </div>
      {flags.length > 0 && (
        <div className="mt-4 grid gap-2">
          {flags.map((flag, index) => (
            <div key={`${flag.title}-${index}`} className="rounded-lg bg-slate-50 p-3">
              <p className="text-xs font-bold uppercase text-[var(--text-primary)]">{flag.severity}: {flag.title}</p>
              <p className="mt-1 text-xs text-[var(--text-muted)]">{flag.detail}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function toLines(value) {
  return Array.isArray(value) ? value.join('\n') : '';
}

function fromLines(value) {
  return value.split('\n').map((line) => line.trim()).filter(Boolean);
}

function changedFields(original, current, prefix) {
  const changes = {};
  Object.keys(current).forEach((key) => {
    const before = JSON.stringify(original?.[key] ?? '');
    const after = JSON.stringify(current[key] ?? '');
    if (before !== after) changes[`${prefix}.${key}`] = { before: original?.[key] ?? '', after: current[key] ?? '' };
  });
  return changes;
}

export default function ReviewPage({ result, onBack, onApproved }) {
  const { extracted_data: originalData, action_plan: originalPlan, source_evidence: evidence = {}, review_meta: reviewMeta = {}, job_id } = result;
  const [activeTab, setActiveTab] = useState('extraction');
  const [precedents, setPrecedents] = useState([]);
  const [approving, setApproving] = useState(false);
  const [verifiedBy, setVerifiedBy] = useState('Demo Reviewer');
  const [verifiedRole, setVerifiedRole] = useState('legal_reviewer');
  const [data, setData] = useState(originalData);
  const [plan, setPlan] = useState(originalPlan);
  const [directivesText, setDirectivesText] = useState(toLines(originalData.directives));
  const [timelinesText, setTimelinesText] = useState(toLines(originalData.timelines));
  const [selectedEvidence, setSelectedEvidence] = useState(evidence.directives || evidence.case_number || Object.values(evidence)[0]);
  const [deadlineDays, setDeadlineDays] = useState('');

  const tabs = ['extraction', 'action_plan', 'file_note', 'precedents'];
  const tabLabels = { extraction: 'Verify', action_plan: 'Action', file_note: 'File Note', precedents: 'Precedents' };

  const edits = useMemo(() => ({
    ...changedFields(originalData, data, 'extracted_data'),
    ...changedFields(originalPlan, plan, 'action_plan'),
  }), [originalData, originalPlan, data, plan]);

  useEffect(() => {
    const query = (data.directives || []).join('. ') || data.case_title || '';
    if (!query) return undefined;
    let cancelled = false;
    async function loadPrecedents() {
      try {
        const response = await fetch(`/api/precedents?query=${encodeURIComponent(query)}`);
        const payload = await response.json();
        if (!cancelled) setPrecedents(payload.precedents || []);
      } catch {
        if (!cancelled) setPrecedents([]);
      }
    }
    loadPrecedents();
    return () => { cancelled = true; };
  }, [data.case_title, data.directives]);

  const updateData = (key, value) => setData((prev) => ({ ...prev, [key]: value }));
  const updatePlan = (key, value) => setPlan((prev) => ({ ...prev, [key]: value }));

  const recalculateDeadline = async () => {
    const override = deadlineDays ? Number(deadlineDays) : null;
    const response = await fetch('/api/deadline-rules/calculate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ date_of_order: data.date_of_order, action_type: plan.action_type, override_days: override }),
    });
    const payload = await response.json();
    setPlan((prev) => ({
      ...prev,
      calculated_deadline: payload.calculated_deadline,
      days_remaining: payload.days_remaining,
      contempt_risk_level: payload.contempt_risk_level,
      deadline_rule_id: payload.deadline_rule_id,
      deadline_basis: payload.deadline_basis,
    }));
  };

  const handleApprove = async () => {
    setApproving(true);
    try {
      const response = await fetch('/api/approve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          job_id,
          extracted_data: data,
          action_plan: plan,
          source_evidence: evidence,
          review_meta: reviewMeta,
          verified_by: verifiedBy || 'Demo Reviewer',
          verified_role: verifiedRole,
          edits,
        }),
      });
      if (!response.ok) throw new Error('Approval failed');
      onApproved();
    } catch {
      setApproving(false);
    }
  };

  return (
    <div className="flex h-screen flex-col bg-[var(--bg-primary)]">
      <header className="flex h-14 shrink-0 items-center border-b border-[var(--border)] bg-white px-5">
        <button onClick={onBack} className="rounded-lg px-3 py-1.5 text-sm text-[var(--text-secondary)] transition hover:bg-slate-100">
          Back
        </button>
        <div className="min-w-0 flex-1 px-6">
          <p className="truncate text-center text-sm font-semibold">{data.case_title || 'Untitled Case'}</p>
          <p className="truncate text-center text-xs text-[var(--text-muted)]">{data.case_number}</p>
        </div>
        <div className="flex items-center gap-3">
          {plan.days_remaining >= 0 && <span className="text-xs font-semibold text-[var(--text-secondary)]">{plan.days_remaining} days left</span>}
          <Badge level={plan.contempt_risk_level} />
        </div>
      </header>

      <main className="grid min-h-0 flex-1 grid-cols-[minmax(420px,52%)_minmax(420px,48%)] overflow-hidden">
        <PdfEvidenceViewer jobId={job_id} selectedEvidence={selectedEvidence} />

        <section className="flex min-w-0 flex-col border-l border-[var(--border)] bg-white">
          <div className="flex shrink-0 border-b border-[var(--border)] px-4">
            {tabs.map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`border-b-2 px-4 py-3 text-sm font-semibold transition ${
                  activeTab === tab
                    ? 'border-[var(--accent)] text-[var(--accent)]'
                    : 'border-transparent text-[var(--text-muted)] hover:text-[var(--text-primary)]'
                }`}
              >
                {tabLabels[tab]}
              </button>
            ))}
          </div>

          <div className="flex-1 overflow-y-auto p-5">
            {activeTab === 'extraction' && (
              <div className="space-y-5">
                <div>
                  <h2 className="text-lg font-semibold">Human verification</h2>
                  <p className="mt-1 text-sm text-[var(--text-muted)]">Edit extracted values and click source cards to inspect highlighted PDF evidence.</p>
                </div>
                <ReviewReadiness meta={reviewMeta} />
                <div className="grid gap-4 rounded-xl border border-[var(--border)] bg-slate-50 p-4">
                  <TextInput label="Case Title" value={data.case_title} onChange={(v) => updateData('case_title', v)} evidence={evidence.case_title} onSelectEvidence={setSelectedEvidence} />
                  <TextInput label="Case Number" value={data.case_number} onChange={(v) => updateData('case_number', v)} evidence={evidence.case_number} onSelectEvidence={setSelectedEvidence} />
                  <div className="grid grid-cols-2 gap-4">
                    <TextInput label="Date of Order" value={data.date_of_order} onChange={(v) => updateData('date_of_order', v)} evidence={evidence.date_of_order} onSelectEvidence={setSelectedEvidence} />
                    <TextInput label="State Role" value={data.state_role} onChange={(v) => updateData('state_role', v)} evidence={evidence.case_title} onSelectEvidence={setSelectedEvidence} />
                  </div>
                  <TextArea label="Parties" value={toLines(data.parties)} onChange={(v) => updateData('parties', fromLines(v))} rows={4} evidence={evidence.case_title} onSelectEvidence={setSelectedEvidence} />
                  <TextArea label="Directives" value={directivesText} onChange={(v) => { setDirectivesText(v); updateData('directives', fromLines(v)); }} rows={6} evidence={evidence.directives} onSelectEvidence={setSelectedEvidence} />
                  <TextArea label="Timelines" value={timelinesText} onChange={(v) => { setTimelinesText(v); updateData('timelines', fromLines(v)); }} rows={4} evidence={evidence.timelines} onSelectEvidence={setSelectedEvidence} />
                </div>
              </div>
            )}

            {activeTab === 'action_plan' && (
              <div className="space-y-5">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <h2 className="text-lg font-semibold">Action plan</h2>
                    <p className="mt-1 text-sm text-[var(--text-muted)]">Review the rule applied, deadline, routing, and risk before approval.</p>
                  </div>
                  <Badge level={plan.contempt_risk_level} />
                </div>
                <div className="grid gap-4 rounded-xl border border-[var(--border)] bg-slate-50 p-4">
                  <div className="grid grid-cols-2 gap-4">
                    <SelectInput label="Action Type" value={plan.action_type} onChange={(v) => updatePlan('action_type', v)}>
                      <option value="compliance">Compliance</option>
                      <option value="appeal">Appeal</option>
                      <option value="review">Review</option>
                    </SelectInput>
                    <SelectInput label="Risk Level" value={plan.contempt_risk_level} onChange={(v) => updatePlan('contempt_risk_level', v)}>
                      <option value="critical">Critical</option>
                      <option value="high">High</option>
                      <option value="medium">Medium</option>
                      <option value="low">Low</option>
                    </SelectInput>
                  </div>
                  <div className="grid grid-cols-[1fr_150px_auto] items-end gap-3">
                    <TextInput label="Deadline" value={plan.calculated_deadline} onChange={(v) => updatePlan('calculated_deadline', v)} evidence={evidence.timelines} onSelectEvidence={setSelectedEvidence} />
                    <TextInput label="Override Days" value={deadlineDays} onChange={setDeadlineDays} />
                    <button onClick={recalculateDeadline} className="rounded-lg bg-[var(--accent)] px-4 py-2 text-sm font-semibold text-white transition hover:bg-blue-700">
                      Recalculate
                    </button>
                  </div>
                  <div className="rounded-lg border border-[var(--border)] bg-white p-3">
                    <p className="text-xs font-semibold uppercase text-[var(--text-muted)]">Rule Applied</p>
                    <p className="mt-1 text-sm font-medium">{plan.deadline_rule_id || 'Manual review required'}</p>
                    <p className="mt-1 text-xs text-[var(--text-muted)]">{plan.deadline_basis || 'No deadline basis recorded.'}</p>
                  </div>
                  <TextInput label="Responsible Office" value={plan.assigned_designation} onChange={(v) => updatePlan('assigned_designation', v)} evidence={evidence.action_plan} onSelectEvidence={setSelectedEvidence} />
                  <TextArea label="Reasoning" value={plan.reasoning} onChange={(v) => updatePlan('reasoning', v)} rows={5} evidence={evidence.action_plan} onSelectEvidence={setSelectedEvidence} />
                  <TextArea label="Deadline Override Reason" value={plan.deadline_override_reason} onChange={(v) => updatePlan('deadline_override_reason', v)} rows={3} />
                </div>
              </div>
            )}

            {activeTab === 'file_note' && (
              <div className="space-y-5">
                <div>
                  <h2 className="text-lg font-semibold">File note</h2>
                  <p className="mt-1 text-sm text-[var(--text-muted)]">This reviewed draft is included in the compliance packet.</p>
                </div>
                <TextArea label="Draft File Note" value={plan.draft_file_note} onChange={(v) => updatePlan('draft_file_note', v)} rows={18} evidence={evidence.action_plan} onSelectEvidence={setSelectedEvidence} />
              </div>
            )}

            {activeTab === 'precedents' && (
              <div className="space-y-4">
                <div>
                  <h2 className="text-lg font-semibold">Precedents</h2>
                  <p className="mt-1 text-sm text-[var(--text-muted)]">Curated similar cases for decision support.</p>
                </div>
                {precedents.length === 0 ? (
                  <p className="rounded-xl border border-[var(--border)] bg-slate-50 p-4 text-sm text-[var(--text-muted)]">No similar cases returned yet.</p>
                ) : (
                  precedents.map((p) => (
                    <div key={p.id} className="rounded-xl border border-[var(--border)] bg-white p-4">
                      <div className="flex items-start justify-between gap-3">
                        <h3 className="text-sm font-semibold">{p.case_name}</h3>
                        <span className="rounded-full bg-blue-50 px-2.5 py-1 text-xs font-semibold text-blue-700">{Math.round(p.similarity * 100)}% match</span>
                      </div>
                      <p className="mt-1 text-xs text-[var(--text-muted)]">{p.category}</p>
                      <p className="mt-3 text-sm text-[var(--text-secondary)]">{p.summary}</p>
                      <p className="mt-3 text-xs font-medium text-[var(--text-primary)]">Outcome: {p.outcome}</p>
                      <p className="mt-1 text-xs text-[var(--text-muted)]">{p.action_taken}</p>
                    </div>
                  ))
                )}
              </div>
            )}
          </div>

          <footer className="shrink-0 border-t border-[var(--border)] bg-white p-4">
            <div className="grid grid-cols-[1fr_190px_auto_auto] items-end gap-3">
              <TextInput label="Reviewer" value={verifiedBy} onChange={setVerifiedBy} />
              <SelectInput label="Role" value={verifiedRole} onChange={setVerifiedRole}>
                {ROLES.map((role) => <option key={role.id} value={role.id}>{role.label}</option>)}
              </SelectInput>
              <button onClick={onBack} className="rounded-lg border border-[var(--border)] px-4 py-2 text-sm font-semibold text-[var(--text-secondary)] transition hover:bg-slate-100">
                Reject
              </button>
              <button onClick={handleApprove} disabled={approving} className="rounded-lg bg-[var(--success)] px-5 py-2 text-sm font-semibold text-white transition hover:bg-emerald-700 disabled:opacity-50">
                {approving ? 'Approving...' : `Approve (${Object.keys(edits).length} edits)`}
              </button>
            </div>
          </footer>
        </section>
      </main>
    </div>
  );
}
