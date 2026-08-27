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

export interface LastRunConfig {
  algorithm: string;
  primaryParam: number;
  includeProjection: boolean;
}

interface WorkspaceContextValue {
  datasetId: string | null;
  filename: string | null;
  dataConfig: DataConfigDTO | null;
  selectedModuleId: string | null;
  jobId: string | null;
  lastRunConfig: LastRunConfig | null;
  setDataset: (datasetId: string, filename: string) => void;
  setDataConfig: (dataConfig: DataConfigDTO) => void;
  setSelectedModule: (moduleId: string) => void;
  setJobId: (jobId: string) => void;
  setLastRunConfig: (config: LastRunConfig) => void;
  reset: () => void;
}

const WorkspaceContext = createContext<WorkspaceContextValue | undefined>(undefined);

export function WorkspaceProvider({ children }: { children: ReactNode }) {
  const [datasetId, setDatasetId] = useState<string | null>(null);
  const [filename, setFilename] = useState<string | null>(null);
  const [dataConfig, setDataConfigState] = useState<DataConfigDTO | null>(null);
  const [jobId, setJobIdState] = useState<string | null>(null);
  const [lastRunConfig, setLastRunConfigState] = useState<LastRunConfig | null>(null);
  const [selectedModuleId, setSelectedModuleIdState] = useState<string | null>(null);

  function setLastRunConfig(config: LastRunConfig): void {
    setLastRunConfigState(config);
  }

  function setDataset(newDatasetId: string, newFilename: string): void {
    setDatasetId(newDatasetId);
    setFilename(newFilename);
    setDataConfigState(null);
    setJobIdState(null);
  }

  function setDataConfig(newDataConfig: DataConfigDTO): void {
    setDataConfigState(newDataConfig);
  }

  function setJobId(newJobId: string): void {
    setJobIdState(newJobId);
  }

  function setSelectedModule(moduleId: string): void {
    setSelectedModuleIdState(moduleId);
    setJobIdState(null);
  }

  function reset(): void {
    setDatasetId(null);
    setFilename(null);
    setDataConfigState(null);
    setJobIdState(null);
    setLastRunConfigState(null);
    setSelectedModuleIdState(null);
  }

  const value: WorkspaceContextValue = {
    datasetId,
    filename,
    dataConfig,
    selectedModuleId,
    jobId,
    lastRunConfig,
    setDataset,
    setDataConfig,
    setSelectedModule,
    setJobId,
    setLastRunConfig,
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