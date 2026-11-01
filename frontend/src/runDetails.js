/** Data helpers for loading and presenting individual pipeline runs. */

export async function fetchPipelineRun(apiBaseUrl, runId, { signal, fetchImpl = fetch } = {}) {
  const baseUrl = apiBaseUrl.replace(/\/+$/, '');
  const response = await fetchImpl(
    `${baseUrl}/pipeline-runs/${encodeURIComponent(runId)}`,
    { signal },
  );

  if (response.status === 404) {
    throw new Error(`Pipeline run ${runId} was not found. It may have been removed.`);
  }
  if (!response.ok) {
    throw new Error(`The API returned HTTP ${response.status} while loading run ${runId}.`);
  }

  return response.json();
}

export function getFailureDiagnostic(run) {
  if (run?.status !== 'failed') return null;
  return run.error_message?.trim() || 'The run failed without an error message.';
}
