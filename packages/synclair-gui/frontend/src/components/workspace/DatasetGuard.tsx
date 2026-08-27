/**
 * Blocks access to any Workspace module section that requires an active
 * dataset. Verifies the dataset against the real backend state
 * (GET /datasets/{id}) rather than trusting only WorkspaceContext, so a
 * stale/local datasetId (e.g. after a backend restart, or a context that
 * was never rehydrated after a refresh) cannot produce a false "dataset
 * ready" state.
 */

import type { ReactNode } from "react";
import { useQuery } from "@tanstack/react-query";
import { Navigate } from "react-router-dom";

import { getDataset } from "../../api/client";
import { useWorkspace } from "../../context/WorkspaceContext";

export function DatasetGuard({ children }: { children: ReactNode }) {
  const { datasetId } = useWorkspace();

  const query = useQuery({
    queryKey: ["dataset-check", datasetId],
    queryFn: ({ signal }) => getDataset(datasetId!, signal),
    enabled: Boolean(datasetId),
    retry: false,
  });

  if (!datasetId) {
    return <Navigate to="/workspace/dataset" replace />;
  }

  if (query.isLoading) {
    return <div className="min-h-screen bg-slate-50" />;
  }

  if (query.isError) {
    // Dataset no longer exists server-side (e.g. backend restarted, or a
    // stale reference survived a refresh) -- send the user back to
    // upload a dataset instead of rendering a section with no real data.
    return <Navigate to="/workspace/dataset" replace />;
  }

  return <>{children}</>;
}