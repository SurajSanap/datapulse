/** Helpers for retrieving and interpreting pipeline health summaries. */

export async function fetchPipelineHealth(apiBaseUrl, { signal, fetchImpl = fetch } = {}) {
  const baseUrl = apiBaseUrl.replace(/\/+$/, '');
  const response = await fetchImpl(`${baseUrl}/pipeline-health`, { signal });

  if (!response.ok) {
    throw new Error(`The API returned HTTP ${response.status} while loading pipeline health.`);
  }

  const summaries = await response.json();
  if (!Array.isArray(summaries)) {
    throw new Error('The API returned an unexpected pipeline health response.');
  }
  return summaries;
}

export function getPipelineHealthMetrics(summaries) {
  return summaries.reduce(
    (metrics, pipeline) => ({
      pipelineCount: metrics.pipelineCount + 1,
      failedRuns: metrics.failedRuns + pipeline.failed_runs,
      runningRuns: metrics.runningRuns + pipeline.running_runs,
    }),
    { pipelineCount: 0, failedRuns: 0, runningRuns: 0 },
  );
}
