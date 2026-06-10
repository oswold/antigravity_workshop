import React, { useState, useEffect, useRef, useCallback } from 'react';
import { marked } from 'marked';

const API = '/api/pipeline';

const STEPS = [
  { key: 'fetch_notes', icon: '💬', label: 'WhatsApp MCP', desc: 'Fetch self-messages' },
  { key: 'link_review', icon: '🔗', label: 'Link Review', desc: 'Select links to research' },
  { key: 'research', icon: '🔍', label: 'Research Agent', desc: 'YouTube + Web Fetch MCP' },
  { key: 'write', icon: '✍️', label: 'Writer Agent', desc: 'Generate newsletter' },
  { key: 'review', icon: '👤', label: 'Human Review', desc: 'HITL approval gate' },
  { key: 'publish', icon: '🚀', label: 'Publish', desc: 'GitHub Pages + Gmail' },
];

const CRON_PRESETS = [
  { label: 'Every Monday 8am', value: '0 8 * * 1' },
  { label: 'Daily 7am', value: '0 7 * * *' },
  { label: 'Every 30 min', value: '*/30 * * * *' },
  { label: 'Every 5 min (test)', value: '*/5 * * * *' },
];

const LOG_ICONS = {
  step: '⚡', mcp_call: '🔌', newsletter_ready: '📄', whatsapp_note: '💬',
  started: '▶️', complete: '✅', rejected: '🚫', error: '❌', warn: '⚠️',
};

export default function App() {
  const [topic, setTopic] = useState('AI Agents');
  const [days, setDays] = useState(7);
  const [model, setModel] = useState('gemini');
  const [emails, setEmails] = useState('');
  const [cronExpr, setCronExpr] = useState('0 8 * * 1');
  const [cronActive, setCronActive] = useState(false);
  const [cronEmails, setCronEmails] = useState('');

  const [runId, setRunId] = useState(null);
  const [running, setRunning] = useState(false);
  const [stepStatus, setStepStatus] = useState({});
  const [stepDetail, setStepDetail] = useState({});
  const [logs, setLogs] = useState([]);
  const [newsletter, setNewsletter] = useState('');
  const [awaitingApproval, setAwaitingApproval] = useState(false);
  const [completed, setCompleted] = useState(false);
  const [feedbackText, setFeedbackText] = useState('');
  // Link-review state
  const [awaitingLinks, setAwaitingLinks] = useState(false);
  const [allLinks, setAllLinks] = useState([]);
  const [checkedLinks, setCheckedLinks] = useState({});
  const [includeUncrawlable, setIncludeUncrawlable] = useState(true);

  const logsEndRef = useRef(null);
  const eventSourceRef = useRef(null);

  // Auto-scroll logs
  useEffect(() => { logsEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [logs]);

  const addLog = useCallback((event) => {
    setLogs(prev => [...prev.slice(-200), { id: Date.now() + Math.random(), ...event }]);
  }, []);

  // Connect to SSE
  const connectSSE = useCallback((id) => {
    if (eventSourceRef.current) eventSourceRef.current.close();
    const es = new EventSource(`${API}/events/${id}`);
    eventSourceRef.current = es;

    es.onmessage = (e) => {
      const event = JSON.parse(e.data);
      addLog(event);

      if (event.type === 'step') {
        setStepStatus(prev => ({ ...prev, [event.step]: event.status }));
        if (event.detail) setStepDetail(prev => ({ ...prev, [event.step]: event.detail }));
      }
      if (event.type === 'newsletter_ready') {
        setNewsletter(event.content);
      }
      if (event.type === 'step' && event.step === 'review' && event.status === 'awaiting') {
        setAwaitingApproval(true);
      }
      // Link-review HITL gate
      if (event.type === 'step' && event.step === 'link_review' && event.status === 'awaiting') {
        const links = event.links || [];
        setAllLinks(links);
        const init = {};
        links.forEach(l => { init[l.url] = l.crawlable !== false; });
        setCheckedLinks(init);
        setAwaitingLinks(true);
      }
      if (event.type === 'complete' || event.type === 'rejected' || event.type === 'error') {
        setRunning(false);
        setAwaitingApproval(false);
        setAwaitingLinks(false);
        setCompleted(true);
        es.close();
      }
    };
    es.onerror = () => { setRunning(false); };
  }, [addLog]);

  // Start pipeline
  const handleRun = async () => {
    setLogs([]); setStepStatus({}); setStepDetail({});
    setNewsletter(''); setAwaitingApproval(false); setCompleted(false);
    setAwaitingLinks(false); setAllLinks([]); setCheckedLinks({}); setIncludeUncrawlable(true);
    setRunning(true);

    const res = await fetch(`${API}/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ topic, days: Number(days), model, emails }),
    });
    const { runId: id } = await res.json();
    setRunId(id);
    connectSSE(id);
  };

  const handleCancel = async () => {
    if (!runId) return;
    await fetch(`${API}/cancel/${runId}`, { method: 'POST' });
    setRunning(false);
    setCompleted(true);
  };

  // Approve / reject
  const handleApprove = async (approved) => {
    setAwaitingApproval(false);
    await fetch(`${API}/approve/${runId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ approved }),
    });
  };

  const handleRevise = async () => {
    if (!feedbackText.trim()) return;
    setAwaitingApproval(false);
    const fb = feedbackText;
    setFeedbackText('');
    await fetch(`${API}/approve/${runId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ feedback: fb }),
    });
  };

  // Send selected links to backend
  const handleSelectLinks = async () => {
    setAwaitingLinks(false);
    const selected = Object.entries(checkedLinks)
      .filter(([, v]) => v).map(([k]) => k);
    await fetch(`${API}/select-links/${runId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ links: selected, include_uncrawlable: includeUncrawlable }),
    });
  };

  // Set cron
  const handleCron = async () => {
    if (cronActive) {
      await fetch(`${API}/cron`, { method: 'DELETE' });
      setCronActive(false);
    } else {
      const res = await fetch(`${API}/cron`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ expression: cronExpr, topic, model, days: Number(days), emails: cronEmails }),
      });
      if (res.ok) setCronActive(true);
    }
  };

  const getStepBadge = (key) => {
    const s = stepStatus[key];
    if (!s || s === 'idle') return <span className="step-badge badge-idle">Waiting</span>;
    if (s === 'in_progress') return <span className="step-badge badge-active">Running</span>;
    if (s === 'done') return <span className="step-badge badge-done">Done ✓</span>;
    if (s === 'awaiting') return <span className="step-badge badge-waiting">⏳ Awaiting</span>;
    if (s === 'rejected') return <span className="step-badge badge-rejected">Rejected</span>;
    return null;
  };

  return (
    <div className="app">
      {/* ── Topbar ── */}
      <header className="topbar">
        <div className="topbar-logo">
          <h1>⚡ Sakthi's Corner</h1>
          <span className="topbar-badge">WIBD Workshop</span>
        </div>
        <div className="topbar-status">
          <span className={`status-dot ${running ? '' : 'idle'}`} />
          {running ? `Running · ${runId?.slice(0, 8)}...` : completed ? 'Complete' : 'Idle — ready to run'}
        </div>
        <div style={{ fontSize: 12, color: 'var(--text-dim)' }}>
          Python API: <code style={{ color: 'var(--cyan)' }}>localhost:8000</code>
          &nbsp;|&nbsp; Dashboard: <code style={{ color: 'var(--cyan)' }}>localhost:5173</code>
        </div>
      </header>

      {/* ── Sidebar ── */}
      <aside className="sidebar">
        {/* Run config */}
        <div className="card">
          <div className="card-title">Pipeline Config</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div className="field">
              <label htmlFor="researchTopic">Research Topic</label>
              <input id="researchTopic" value={topic} onChange={e => setTopic(e.target.value)} placeholder="e.g. AI Agents" />
            </div>
            <div className="field">
              <label htmlFor="fetchDays">Days of notes to fetch</label>
              <input id="fetchDays" type="number" min={1} max={30} value={days} onChange={e => setDays(e.target.value)} />
            </div>
            <div className="field">
              <label htmlFor="writerModel">Writer Agent Model</label>
              <select id="writerModel" value={model} onChange={e => setModel(e.target.value)}>
                <option value="gemini">✨ Gemini (cloud)</option>
                <option value="ollama">🦙 Local Gemma (Ollama)</option>
              </select>
            </div>
            <div className="field">
              <label htmlFor="subscribedEmails">Subscribed Emails (comma-separated)</label>
              <input id="subscribedEmails" value={emails} onChange={e => setEmails(e.target.value)} placeholder="e.g. user@example.com" />
            </div>
            <div style={{ display: 'flex', gap: '8px' }}>
              <button className="btn btn-primary" style={{ flex: 1 }} onClick={handleRun} disabled={running}>
                {running ? '⏳ Running...' : '▶ Run'}
              </button>
              {running && (
                <button className="btn btn-danger" onClick={handleCancel}>
                  Stop
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Cron scheduler */}
        <div className="card">
          <div className="card-title">⏰ Cron Scheduler</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            <div className="field">
              <label htmlFor="cronExpression">Cron Expression</label>
              <input id="cronExpression" value={cronExpr} onChange={e => setCronExpr(e.target.value)} style={{ fontFamily: 'var(--mono)', fontSize: 13 }} />
            </div>
            <div className="cron-presets">
              {CRON_PRESETS.map(p => (
                <button key={p.value} className={`cron-preset ${cronExpr === p.value ? 'active' : ''}`}
                  onClick={() => setCronExpr(p.value)}>{p.label}</button>
              ))}
            </div>
            <div className="field">
              <label htmlFor="subscribedCronEmails">Subscribed Emails for Cron</label>
              <input id="subscribedCronEmails" value={cronEmails} onChange={e => setCronEmails(e.target.value)} placeholder="e.g. user@example.com" />
            </div>
            <button className={`btn ${cronActive ? 'btn-danger' : 'btn-outline'} btn-sm`} onClick={handleCron}>
              {cronActive ? '⏹ Stop Cron' : '▶ Schedule Cron'}
            </button>
            {cronActive && <div className="cron-active-badge">● Cron active: {cronExpr}</div>}
          </div>
        </div>

        {/* MCP legend */}
        <div className="card">
          <div className="card-title">🔌 Active MCPs</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8, fontSize: 12 }}>
            {[
              { icon: '💬', name: 'WhatsApp MCP', auth: 'QR auth (once)', color: 'var(--cyan)' },
              { icon: '📺', name: 'YouTube Transcript', auth: 'no auth ✓', color: 'var(--green)' },
              { icon: '🌐', name: 'Fetch MCP', auth: 'no auth ✓', color: 'var(--green)' },
              { icon: '🐙', name: 'GitHub (IDE)', auth: 'OAuth / no PAT ✓', color: 'var(--green)' },
              { icon: '🐙', name: 'GitHub (pipeline)', auth: 'PAT env var', color: 'var(--amber)' },
            ].map(m => (
              <div key={m.name} style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                <span>{m.icon}</span>
                <span style={{ flex: 1, color: 'var(--text)' }}>{m.name}</span>
                <span style={{ color: m.color, fontSize: 11 }}>{m.auth}</span>
              </div>
            ))}
          </div>
        </div>
      </aside>

      {/* ── Main — Pipeline Steps + Event Log ── */}
      <main className="main">
        {/* Steps */}
        <div className="steps">
          {STEPS.map(step => {
            const s = stepStatus[step.key] || 'idle';
            return (
              <div key={step.key} className={`step ${s}`}>
                <div className="step-icon">{step.icon}</div>
                <div className="step-info">
                  <div className="step-name">{step.label}</div>
                  <div className="step-detail">{stepDetail[step.key] || step.desc}</div>
                </div>
                {getStepBadge(step.key)}
              </div>
            );
          })}
        </div>

        {/* Event log */}
        <div className="log-header">📡 Live Event Log</div>
        <div className="event-log">
          {logs.length === 0 && (
            <div style={{ color: 'var(--text-dim)', fontSize: 12, padding: '8px 0' }}>
              Start the pipeline to see real-time MCP calls and agent events...
            </div>
          )}
          {logs.map(log => (
            <div key={log.id} className={`log-entry ${log.type}`}>
              <span className="log-icon">{LOG_ICONS[log.status] || LOG_ICONS[log.type] || '•'}</span>
              <div className="log-content">
                {log.tool && <div className="log-tool">{log.tool}</div>}
                {log.message && <div className="log-msg">{log.message}</div>}
                {log.detail && <div className="log-detail">{log.detail}</div>}
                {/* WhatsApp notes rendered with links */}
                {log.type === 'whatsapp_note' && (
                  <div>
                    <div className="log-msg">💬 {log.text}</div>
                    {log.links?.map(lnk => (
                      <div key={lnk} className="log-detail">
                        🔗 <a href={lnk} target="_blank" rel="noreferrer"
                          style={{ color: 'var(--cyan)', wordBreak: 'break-all' }}>{lnk}</a>
                      </div>
                    ))}
                  </div>
                )}
                {!log.tool && !log.message && log.type !== 'whatsapp_note' &&
                  <div className="log-msg">{JSON.stringify(log)}</div>}
              </div>
              {log.status && log.type === 'mcp_call' && (
                <span className={`log-status-${log.status === 'success' ? 'ok' : 'warn'}`}>
                  {log.status === 'success' ? '✓' : '⚠'}
                </span>
              )}
            </div>
          ))}
          <div ref={logsEndRef} />
        </div>
      </main>

      {/* ── Right Panel — Newsletter Preview + Approval ── */}
      <aside className="panel">
        <div className="newsletter-panel">
          <div className="newsletter-header">
            <h3>📄 Newsletter Preview</h3>
            {newsletter && (
              <button className="btn btn-outline btn-sm" onClick={() => navigator.clipboard.writeText(newsletter)}>
                Copy MD
              </button>
            )}
          </div>

          <div className="newsletter-content">
            {newsletter ? (
              <div className="newsletter-markdown"
                dangerouslySetInnerHTML={{ __html: marked.parse(newsletter) }} />
            ) : (
              <div className="newsletter-empty">
                <span>📭</span>
                <p>Newsletter will appear here after the Writer Agent completes</p>
              </div>
            )}
          </div>

          {/* HITL Gate #1 — Link Selection */}
          {awaitingLinks && (
            <div className="approval-gate">
              <div className="approval-label">🔗 Select Links to Research</div>
              <p style={{ fontSize: 12, color: 'var(--text-dim)', marginBottom: 10 }}>
                These links were found in your WhatsApp self-messages.
                Uncheck any you want to skip before the Research Agent runs.
              </p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginBottom: 12 }}>
                {allLinks.map(link => (
                  <div key={link.url} style={{ display: 'flex', gap: 8, alignItems: 'flex-start', fontSize: 12 }}>
                    <input type="checkbox" id={link.url}
                      checked={!!checkedLinks[link.url]}
                      disabled={link.crawlable === false}
                      onChange={e => setCheckedLinks(p => ({ ...p, [link.url]: e.target.checked }))}
                      style={{ marginTop: 2, flexShrink: 0, cursor: link.crawlable === false ? 'not-allowed' : 'pointer' }} />
                    <label htmlFor={link.url} style={{ color: link.crawlable === false ? 'var(--text-dim)' : 'var(--text)', cursor: link.crawlable === false ? 'not-allowed' : 'pointer' }}>
                      <a href={link.url} target="_blank" rel="noreferrer"
                        style={{ color: link.crawlable === false ? 'var(--text-dim)' : 'var(--cyan)', textDecoration: link.crawlable === false ? 'line-through' : 'none', wordBreak: 'break-all' }}>{link.url}</a>
                      {link.crawlable === false && (
                        <span style={{ color: 'var(--amber)', fontSize: 11, marginLeft: 8 }} title={link.error_message}>
                          ⚠️ Uncrawlable ({link.error_message || 'Fetch failed'})
                        </span>
                      )}
                      <div style={{ color: 'var(--text-dim)', fontSize: 11, marginTop: 2 }}>
                        {link.source_text} · {link.date}
                      </div>
                    </label>
                  </div>
                ))}
              </div>

              {/* Checkbox for including uncrawlable links */}
              {allLinks.some(link => link.crawlable === false) && (
                <div style={{ display: 'flex', gap: 8, alignItems: 'center', fontSize: 12, marginTop: 12, marginBottom: 12, padding: '8px', background: '#1c1c28', borderRadius: '6px', border: '1px solid var(--border)' }}>
                  <input type="checkbox" id="include-uncrawlable"
                    checked={includeUncrawlable}
                    onChange={e => setIncludeUncrawlable(e.target.checked)}
                    style={{ cursor: 'pointer' }} />
                  <label htmlFor="include-uncrawlable" style={{ color: 'var(--text)', cursor: 'pointer' }}>
                    📖 Include failed/uncrawlable links in References section
                  </label>
                </div>
              )}

              <button
                className="btn btn-primary"
                onClick={handleSelectLinks}
                disabled={Object.values(checkedLinks).filter(Boolean).length === 0 || allLinks.every(link => link.crawlable === false)}
              >
                ▶ Research {Object.values(checkedLinks).filter(Boolean).length} selected link(s)
              </button>
            </div>
          )}

          {/* HITL Gate #2 — Publish Approval */}
          {awaitingApproval && (
            <div className="approval-gate">
              <div className="approval-label">GUARDRAIL — Human Approval Required</div>
              <p style={{ fontSize: 12, color: 'var(--text-dim)', marginBottom: 10 }}>
                Review the newsletter above. Approve to publish to GitHub Pages, or reject to stop.
                To request modifications, type your feedback below and click "Request Revision".
              </p>

              {/* Revision feedback area */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginBottom: 12 }}>
                <textarea
                  style={{
                    width: '100%',
                    minHeight: '60px',
                    background: '#1a1a24',
                    border: '1px solid var(--border)',
                    borderRadius: '6px',
                    padding: '8px 12px',
                    color: 'var(--text)',
                    fontSize: '12px',
                    fontFamily: 'inherit',
                    resize: 'vertical',
                    boxSizing: 'border-box'
                  }}
                  placeholder="e.g., Make the third pick sound more conversational, add key emojis, or shorten the summary..."
                  value={feedbackText}
                  onChange={e => setFeedbackText(e.target.value)}
                />
                <button
                  className="btn btn-outline"
                  onClick={handleRevise}
                  disabled={!feedbackText.trim()}
                  style={{
                    width: '100%',
                    borderColor: 'var(--amber)',
                    color: 'var(--amber)',
                    opacity: feedbackText.trim() ? 1 : 0.5,
                    cursor: feedbackText.trim() ? 'pointer' : 'not-allowed'
                  }}
                >
                  🔄 Request Revision
                </button>
              </div>

              <div className="approval-btns">
                <button className="btn btn-success" onClick={() => handleApprove(true)} style={{ flex: 1 }}>
                  ✅ Approve & Publish
                </button>
                <button className="btn btn-danger" onClick={() => handleApprove(false)} style={{ flex: 1 }}>
                  ❌ Reject
                </button>
              </div>
            </div>
          )}
        </div>
      </aside>
    </div>
  );
}
