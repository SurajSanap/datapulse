import assert from 'node:assert/strict';
import test from 'node:test';

import { fetchPipelineHealth, getPipelineHealthMetrics } from '../src/healthSummary.js';

const populatedSummaries = [
  {
    pipeline_name: 'alpha_pipeline',
    total_runs: 5,
    successful_runs: 3,
    failed_runs: 1,
    running_runs: 1,
    latest_run_at: '2026-11-02T10:00:00Z',
    latest_status: 'running',
  },
  {
    pipeline_name: 'weather_pipeline',
    total_runs: 2,
    successful_runs: 1,
    failed_runs: 1,
    running_runs: 0,
    latest_run_at: '2026-11-02T09:30:00Z',
    latest_status: 'failed',
  },
];

test('loads populated per-pipeline health summaries and totals', async () => {
  let requestedUrl;
  const summaries = await fetchPipelineHealth('http://localhost:8000/', {
    fetchImpl: async (url) => {
      requestedUrl = url;
      return { ok: true, status: 200, json: async () => populatedSummaries };
    },
  });

  assert.equal(requestedUrl, 'http://localhost:8000/pipeline-health');
  assert.deepEqual(summaries, populatedSummaries);
  assert.deepEqual(getPipelineHealthMetrics(summaries), {
    pipelineCount: 2,
    failedRuns: 2,
    runningRuns: 1,
  });
});

test('handles an empty pipeline health summary', async () => {
  const summaries = await fetchPipelineHealth('http://localhost:8000', {
    fetchImpl: async () => ({ ok: true, status: 200, json: async () => [] }),
  });

  assert.deepEqual(summaries, []);
  assert.deepEqual(getPipelineHealthMetrics(summaries), {
    pipelineCount: 0,
    failedRuns: 0,
    runningRuns: 0,
  });
});

test('surfaces API failures when loading health summaries', async () => {
  await assert.rejects(
    fetchPipelineHealth('http://localhost:8000', {
      fetchImpl: async () => ({ ok: false, status: 503 }),
    }),
    /HTTP 503 while loading pipeline health/,
  );
});
