/**
 * synclair-gui frontend WorkspaceContext
 * -------------------------------------------
 *
 * Holds state that must flow across the Workspace's three route-based
 * steps (upload -> configure -> results): the current dataset_id, the
 * last DataConfig built/validated for it, and the current structure job
 * id. Deliberately NOT persisted to localStorage (unlike AuthContext's
 * token): this state mirrors server-side in-memory state
 * (dataset_store/job_manager), which itself doesn't survive a backend
 * restart, so surviving a frontend refresh would be misleading anyway.
 * A page refresh mid-flow is expected to restart the Workspace from
 * Step 1.
 */

import { createContext, useContext, useState, type ReactNode } from "react";

import type { DataConfigDTO } from "../types/api";

interface WorkspaceContextValue {
  datasetId: string | null;
  filename: string | null;
  dataConfig: DataConfigDTO | null;
  jobId: string | null;
  setDataset: (datasetId: string, filename: string) => void;
  setDataConfig: (dataConfig: DataConfigDTO) => void;
  setJobId: (jobId: string) => void;
  reset: () => void;
}

const WorkspaceContext = createContext<WorkspaceContextValue | undefined>(undefined);

export function WorkspaceProvider({ children }: { children: ReactNode }) {
  const [datasetId, setDatasetId] = useState<string | null>(null);
  const [filename, setFilename] = useState<string | null>(null);
  const [dataConfig, setDataConfigState] = useState<DataConfigDTO | null>(null);
  const [jobId, setJobIdState] = useState<string | null>(null);

  function setDataset(newDatasetId: string, newFilename: string): void {
    setDatasetId(newDatasetId);
    setFilename(newFilename);
    // A new dataset invalidates any previously built config/job.
    setDataConfigState(null);
    setJobIdState(null);
  }

  function setDataConfig(newDataConfig: DataConfigDTO): void {
    setDataConfigState(newDataConfig);
  }

  function setJobId(newJobId: string): void {
    setJobIdState(newJobId);
  }

  function reset(): void {
    setDatasetId(null);
    setFilename(null);
    setDataConfigState(null);
    setJobIdState(null);
  }

  const value: WorkspaceContextValue = {
    datasetId,
    filename,
    dataConfig,
    jobId,
    setDataset,
    setDataConfig,
    setJobId,
    reset,
  };

  return <WorkspaceContext.Provider value={value}>{children}</WorkspaceContext.Provider>;
}

export function useWorkspace(): WorkspaceContextValue {
  const context = useContext(WorkspaceContext);
  if (context === undefined) {
    throw new Error("useWorkspace() must be used within a <WorkspaceProvider>.");
  }
  return context;
}