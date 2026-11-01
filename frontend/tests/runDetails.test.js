import assert from 'node:assert/strict';
import test from 'node:test';

import { fetchPipelineRun, getFailureDiagnostic } from '../src/runDetails.js';

test('loads a successful run and exposes its detail fields', async () => {
  const successfulRun = {
    id: 42,
    pipeline_name: 'open_meteo_weather',
    status: 'success',
    started_at: '2026-11-02T10:00:00Z',
    completed_at: '2026-11-02T10:01:00Z',
    records_processed: 24,
    error_message: null,
  };
  let requestedUrl;

  const run = await fetchPipelineRun('http://localhost:8000/', 42, {
    fetchImpl: async (url) => {
      requestedUrl = url;
      return { ok: true, status: 200, json: async () => successfulRun };
    },
  });

  assert.equal(requestedUrl, 'http://localhost:8000/pipeline-runs/42');
  assert.deepEqual(run, successfulRun);
  assert.equal(getFailureDiagnostic(run), null);
});

test('loads a failed run and returns its error message for diagnostics', async () => {
  const failedRun = {
    id: 43,
    pipeline_name: 'open_meteo_weather',
    status: 'failed',
    started_at: '2026-11-02T10:00:00Z',
    completed_at: '2026-11-02T10:00:04Z',
    records_processed: 0,
    error_message: 'upstream unavailable',
  };

  const run = await fetchPipelineRun('http://localhost:8000', 43, {
    fetchImpl: async () => ({
      ok: true,
      status: 200,
      json: async () => failedRun,
    }),
  });

  assert.equal(run.status, 'failed');
  assert.equal(getFailureDiagnostic(run), 'upstream unavailable');
});

test('reports a missing run clearly', async () => {
  await assert.rejects(
    fetchPipelineRun('http://localhost:8000', 404, {
      fetchImpl: async () => ({ ok: false, status: 404 }),
    }),
    /Pipeline run 404 was not found/,
  );
});
