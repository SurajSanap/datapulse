import { useEffect, useState } from 'react';

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/+$/, '');
const PAGE_SIZE = 10;

function formatDate(value) {
  if (!value) return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '—';
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date);
}

function StatusBadge({ status }) {
  const normalized = (status || 'unknown').toLowerCase();
  return <span className={`status-badge status-${normalized}`}>{normalized}</span>;
}

export default function App() {
  const [pipelineName, setPipelineName] = useState('');
  const [status, setStatus] = useState('');
  const [page, setPage] = useState(0);
  const [runs, setRuns] = useState([]);
  const [hasNext, setHasNext] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    const controller = new AbortController();

    async function loadRuns() {
      setLoading(true);
      setError('');

      const params = new URLSearchParams({
        limit: String(PAGE_SIZE + 1),
        offset: String(page * PAGE_SIZE),
      });
      if (pipelineName.trim()) params.set('pipeline_name', pipelineName.trim());
      if (status) params.set('status', status);

      try {
        const response = await fetch(`${API_BASE_URL}/pipeline-runs?${params}`, {
          signal: controller.signal,
        });
        if (!response.ok) {
          throw new Error(`The API returned HTTP ${response.status}.`);
        }

        const data = await response.json();
        if (!Array.isArray(data)) {
          throw new Error('The API returned an unexpected response.');
        }
        setRuns(data.slice(0, PAGE_SIZE));
        setHasNext(data.length > PAGE_SIZE);
      } catch (requestError) {
        if (requestError.name !== 'AbortError') {
          setError(requestError.message || 'Could not load pipeline runs.');
          setRuns([]);
          setHasNext(false);
        }
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }

    loadRuns();
    return () => controller.abort();
  }, [pipelineName, status, page, reloadToken]);

  function updatePipelineName(event) {
    setPipelineName(event.target.value);
    setPage(0);
  }

  function updateStatus(event) {
    setStatus(event.target.value);
    setPage(0);
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <a className="brand" href="/" aria-label="DataPulse home">
          <span className="brand-mark" aria-hidden="true">D</span>
          <span>DataPulse</span>
        </a>
        <span className="topbar-label">Pipeline operations</span>
      </header>

      <section className="content">
        <div className="page-heading">
          <div>
            <p className="eyebrow">OBSERVABILITY</p>
            <h1>Pipeline runs</h1>
            <p className="subtitle">Review recent executions and spot failures quickly.</p>
          </div>
          <div className="live-indicator"><span /> Run history</div>
        </div>

        <section className="history-card" aria-labelledby="history-title">
          <div className="card-heading">
            <div>
              <h2 id="history-title">Execution history</h2>
              <p>Filter runs by pipeline or current status.</p>
            </div>
          </div>

          <div className="filters">
            <label className="filter-field pipeline-filter">
              <span>Pipeline</span>
              <input
                type="search"
                value={pipelineName}
                onChange={updatePipelineName}
                placeholder="Filter by pipeline name"
                aria-label="Filter by pipeline name"
              />
            </label>
            <label className="filter-field status-filter">
              <span>Status</span>
              <select value={status} onChange={updateStatus} aria-label="Filter by status">
                <option value="">All statuses</option>
                <option value="running">Running</option>
                <option value="success">Success</option>
                <option value="failed">Failed</option>
              </select>
            </label>
          </div>

          {error ? (
            <div className="state-panel error-panel" role="alert">
              <span className="state-icon" aria-hidden="true">!</span>
              <div>
                <strong>Couldn’t load run history</strong>
                <p>{error} Check that the API is running and the frontend origin is allowed by CORS.</p>
              </div>
              <button className="button secondary" onClick={() => setReloadToken((value) => value + 1)}>
                Try again
              </button>
            </div>
          ) : (
            <>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th scope="col">Pipeline</th>
                      <th scope="col">Status</th>
                      <th scope="col">Started</th>
                      <th scope="col">Completed</th>
                      <th scope="col" className="numeric">Records</th>
                      <th scope="col">Result</th>
                    </tr>
                  </thead>
                  <tbody>
                    {loading ? (
                      <tr><td colSpan="6"><div className="table-state">Loading pipeline runs…</div></td></tr>
                    ) : runs.length === 0 ? (
                      <tr>
                        <td colSpan="6">
                          <div className="table-state empty-state">
                            <strong>No pipeline runs found</strong>
                            <span>Runs matching these filters will appear here.</span>
                          </div>
                        </td>
                      </tr>
                    ) : runs.map((run) => (
                      <tr key={run.id}>
                        <td>
                          <span className="pipeline-name">{run.pipeline_name}</span>
                          <span className="run-id">Run #{run.id}</span>
                        </td>
                        <td><StatusBadge status={run.status} /></td>
                        <td className="date-cell">{formatDate(run.started_at)}</td>
                        <td className="date-cell">{formatDate(run.completed_at)}</td>
                        <td className="numeric records-cell">{Number(run.records_processed || 0).toLocaleString()}</td>
                        <td>
                          {run.status === 'failed' ? (
                            <span className="failure-result" title={run.error_message || 'Pipeline failed'}>
                              <span aria-hidden="true">!</span>
                              {run.error_message || 'Failed'}
                            </span>
                          ) : run.status === 'running' ? (
                            <span className="muted-result">In progress</span>
                          ) : (
                            <span className="success-result"><span aria-hidden="true">✓</span> Completed</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <footer className="table-footer">
                <span className="page-caption">
                  {runs.length > 0 ? `Showing ${page * PAGE_SIZE + 1}–${page * PAGE_SIZE + runs.length}` : 'No results'}
                </span>
                <div className="pagination">
                  <button
                    className="button secondary"
                    onClick={() => setPage((current) => Math.max(0, current - 1))}
                    disabled={page === 0 || loading}
                  >
                    Previous
                  </button>
                  <span>Page {page + 1}</span>
                  <button
                    className="button secondary"
                    onClick={() => setPage((current) => current + 1)}
                    disabled={!hasNext || loading}
                  >
                    Next
                  </button>
                </div>
              </footer>
            </>
          )}
        </section>
        <p className="api-note">Connected to <code>{API_BASE_URL}</code></p>
      </section>
    </main>
  );
}
