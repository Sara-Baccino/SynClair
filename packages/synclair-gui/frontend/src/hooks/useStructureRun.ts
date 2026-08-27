/**
 * synclair-gui frontend useStructureRun
 * ---------------------------------------------
 *
 * Shared polling logic for a structure job: polls GET /structure/jobs/:id
 * until status is 'completed' or 'failed', and only then fetches
 * GET /structure/jobs/:id/result. Fixes a bug where Results/Artifacts/
 * Export sections queried /result immediately after launching a run,
 * got a transient 409 (job still running), and surfaced it as a
 * permanent "Failed to load results" instead of waiting -- even though
 * the job was genuinely still in progress and completed moments later.
 */

import { useQuery } from "@tanstack/react-query";

import { getStructureJobResult, getStructureJobStatus } from "../api/client";

export function useStructureRun(jobId: string | null) {
  const statusQuery = useQuery({
    queryKey: ["structure-job-status", jobId],
    queryFn: ({ signal }) => getStructureJobStatus(jobId!, signal),
    enabled: Boolean(jobId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === "completed" || status === "failed" ? false : 1000;
    },
  });

  const isFinished =
    statusQuery.data?.status === "completed" || statusQuery.data?.status === "failed";

  const resultQuery = useQuery({
    queryKey: ["structure-job-result", jobId],
    queryFn: ({ signal }) => getStructureJobResult(jobId!, signal),
    enabled: Boolean(jobId) && isFinished,
    retry: false, // a 409 here would mean isFinished was wrong; don't mask it by retrying blindly
  });

  return { statusQuery, resultQuery, isFinished };
}