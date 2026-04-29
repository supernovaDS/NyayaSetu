import { useEffect, useState } from 'react';

function AppHeader({ onBack }) {
  return (
    <header className="app-header">
      <div className="app-header-inner">
        <button onClick={onBack} className="btn btn-secondary">Back to app</button>
        <div className="brand" style={{ justifyContent: 'center' }}>
          <div>
            <p className="brand-title">Admin</p>
            <p className="brand-subtitle">Model configuration</p>
          </div>
        </div>
        <div style={{ width: 104 }} />
      </div>
    </header>
  );
}

export default function AdminPage({ onBack }) {
  const [loading, setLoading] = useState(true);
  const [config, setConfig] = useState({ current_model: '', available_models: [] });
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      const response = await fetch('/api/config');
      const data = await response.json();
      if (!cancelled) {
        setConfig(data);
        setLoading(false);
      }
    }
    load();
    return () => { cancelled = true; };
  }, []);

  const handleSave = async (modelId) => {
    setSaving(true);
    try {
      const res = await fetch('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model_id: modelId }),
      });
      const data = await res.json();
      setConfig((prev) => ({ ...prev, current_model: data.current_model }));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="app-page">
      <AppHeader onBack={onBack} />
      <main className="container admin-main">
        <section className="panel admin-card">
          <h1 className="panel-title">AI model configuration</h1>
          <p className="panel-copy">Select the model used by the page finder and vision extraction pipeline.</p>

          {loading ? (
            <p className="panel-copy" style={{ marginTop: 24 }}>Loading settings...</p>
          ) : (
            <div className="model-list">
              {config.available_models.map((m) => {
                const isActive = config.current_model === m.id;
                return (
                  <button
                    key={m.id}
                    onClick={() => !isActive && handleSave(m.id)}
                    className={`model-option ${isActive ? 'active' : ''}`}
                  >
                    <div>
                      <p className="model-name">{m.name}</p>
                      <p className="model-id">{m.id}</p>
                    </div>
                    {isActive && <span className="active-pill">Active</span>}
                  </button>
                );
              })}
            </div>
          )}

          {saving && <p className="panel-copy" style={{ color: 'var(--brand)', marginTop: 16 }}>Saving configuration...</p>}
        </section>
      </main>
    </div>
  );
}
