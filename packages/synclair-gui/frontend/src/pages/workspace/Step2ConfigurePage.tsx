/**
 * synclair-gui frontend Step2ConfigurePage
 * -----------------------------------------------
 *
 * Workspace Step 2: build/validate the DataConfig for the dataset
 * uploaded in Step 1 (POST /datasets/parse-config), let the user adjust
 * per-column settings and re-validate, then pick a clustering algorithm
 * and launch the analysis (POST /structure/run), storing the resulting
 * job_id in WorkspaceContext before navigating to Step 3.
 *
 * Column renaming (new_name) is intentionally not editable here: since
 * DataConfig requires the dict key to equal ColumnInfo.new_name (Phase
 * 1), supporting renames would require re-keying the whole config on
 * edit -- left as a future extension rather than silently omitted.
 */

import { useEffect, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";

import { parseConfig, runStructure } from "../../api/client";
import { useWorkspace } from "../../context/WorkspaceContext";
import type {
  ClusteringAlgorithmName,
  ClusteringConfig,
  ColumnInfoDTO,
  ConfigValidationDTO,
  EncoderType,
  MissingStrategy,
  ProjectionConfig,
  ScalerType,
  StructureModuleConfig,
} from "../../types/api";

// ---------------------------------------------------------------------- //
// Default configs -- mirror the exact Python defaults from
// clustering_configs.py / projection_configs.py (Phase 6). Only the
// "primary" parameter of each is exposed for editing in this step.
// ---------------------------------------------------------------------- //
const DEFAULT_CLUSTERING_CONFIGS: Record<ClusteringAlgorithmName, ClusteringConfig> = {
  hdbscan: {
    min_cluster_size: 15,
    min_samples: null,
    metric: "euclidean",
    cluster_selection_method: "eom",
    extra_params: {},
  },
  kmeans: {
    n_clusters: 5,
    init: "k-means++",
    n_init: 10,
    random_state: 42,
    extra_params: {},
  },
  agglomerative: {
    n_clusters: 5,
    metric: "euclidean",
    linkage: "ward",
    extra_params: {},
  },
  gmm: {
    n_components: 5,
    covariance_type: "full",
    random_state: 42,
    extra_params: {},
  },
  fuzzy_cmeans: {
    n_clusters: 5,
    m: 2.0,
    error: 0.005,
    maxiter: 1000,
    init: null,
    random_state: 42,
    extra_params: {},
  },
};

const DEFAULT_PCA_CONFIG: ProjectionConfig = {
  n_components: 2,
  target_variance: null,
  random_state: 42,
  extra_params: {},
};

const CLUSTERING_ALGORITHMS: ClusteringAlgorithmName[] = [
  "kmeans",
  "hdbscan",
  "agglomerative",
  "gmm",
  "fuzzy_cmeans",
];

const MISSING_STRATEGIES: MissingStrategy[] = ["maintain", "drop", "impute", "replace"];
const SCALER_METHODS: Exclude<ScalerType, "none">[] = ["standard", "minmax", "robust"];
const ENCODER_METHODS: Exclude<EncoderType, "none">[] = ["one_hot", "ordinal"];

// ---------------------------------------------------------------------- //
// DTO <-> raw core payload conversion
// ---------------------------------------------------------------------- //
function toRawDataConfig(columns: ColumnInfoDTO[]): Record<string, unknown> {
  const rawColumns: Record<string, unknown> = {};
  for (const column of columns) {
    rawColumns[column.name] = {
      new_name: column.new_name,
      active: column.active,
      categorical: column.categorical,
      numerical: column.numerical,
      id: column.id,
      semantic_roles: column.semantic_roles,
      multiplier: column.multiplier,
      mappings: column.mappings,
      missing_data_management: column.missing_data_management,
      scaling: column.scaling,
      encoding: column.encoding,
      type: column.type,
    };
  }
  return { columns: rawColumns };
}

function updateColumn(
  columns: ColumnInfoDTO[],
  name: string,
  updater: (column: ColumnInfoDTO) => ColumnInfoDTO
): ColumnInfoDTO[] {
  return columns.map((column) => (column.name === name ? updater(column) : column));
}

function buildClusteringConfig(
  algorithm: ClusteringAlgorithmName,
  primaryParam: number
): ClusteringConfig {
  switch (algorithm) {
    case "hdbscan":
      return { ...DEFAULT_CLUSTERING_CONFIGS.hdbscan, min_cluster_size: primaryParam };
    case "kmeans":
      return { ...DEFAULT_CLUSTERING_CONFIGS.kmeans, n_clusters: primaryParam };
    case "agglomerative":
      return { ...DEFAULT_CLUSTERING_CONFIGS.agglomerative, n_clusters: primaryParam };
    case "gmm":
      return { ...DEFAULT_CLUSTERING_CONFIGS.gmm, n_components: primaryParam };
    case "fuzzy_cmeans":
      return { ...DEFAULT_CLUSTERING_CONFIGS.fuzzy_cmeans, n_clusters: primaryParam };
  }
}

export function Step2ConfigurePage() {
  const navigate = useNavigate();
  const { datasetId, filename, setDataConfig, setJobId } = useWorkspace();

  const [columns, setColumns] = useState<ColumnInfoDTO[] | null>(null);
  const [validation, setValidation] = useState<ConfigValidationDTO | null>(null);
  const [clusteringAlgorithm, setClusteringAlgorithm] = useState<ClusteringAlgorithmName>("kmeans");
  const [primaryParam, setPrimaryParam] = useState<number>(5);
  const [includeProjection, setIncludeProjection] = useState(true);

  const buildMutation = useMutation({
    mutationFn: () => parseConfig({ dataset_id: datasetId! }),
    onSuccess: (response) => {
      setColumns(response.data_config.columns);
      setValidation(response.validation);
    },
  });

  const revalidateMutation = useMutation({
    mutationFn: (currentColumns: ColumnInfoDTO[]) =>
      parseConfig({
        dataset_id: datasetId!,
        existing_config: toRawDataConfig(currentColumns),
      }),
    onSuccess: (response) => {
      setColumns(response.data_config.columns);
      setValidation(response.validation);
    },
  });

  const runMutation = useMutation({
    mutationFn: () => {
      const clusteringConfig = buildClusteringConfig(clusteringAlgorithm, primaryParam);

      const moduleConfig: StructureModuleConfig = {
        apply_imputation: false,
        clustering_algorithm: clusteringAlgorithm,
        clustering_config: clusteringConfig,
        projection_algorithm: includeProjection ? "pca" : "none",
        projection_config: includeProjection ? DEFAULT_PCA_CONFIG : null,
        run_stability: false,
        stability_config: { n_iterations: 50, sample_fraction: 0.8, seed: 42 },
        run_feature_importance: false,
        rf_importance_config: { n_estimators: 100, max_depth: 6, random_state: 42, extra_params: {} },
        run_shap: false,
        shap_config: { n_estimators: 100, max_depth: 5, random_state: 42, extra_params: {} },
        run_cluster_profile: false,
      };

      return runStructure({
        dataset_id: datasetId!,
        module_config: moduleConfig as unknown as Record<string, unknown>,
      });
    },
    onSuccess: (response) => {
      setJobId(response.job_id);
      navigate(`/workspace/results/${response.job_id}`);
    },
  });

  useEffect(() => {
    if (datasetId && columns === null && !buildMutation.isPending) {
      buildMutation.mutate();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [datasetId]);

  if (!datasetId) {
    return (
      <div className="min-h-screen bg-slate-50 p-10">
        <p className="text-slate-600">
          No dataset selected. Please go back to{" "}
          <button onClick={() => navigate("/workspace/upload")} className="text-blue-600 underline">
            Step 1
          </button>
          .
        </p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 p-10">
      <h1 className="text-2xl font-semibold text-slate-800">Step 2 · Configure columns</h1>
      <p className="mt-2 text-slate-500">
        Dataset: <span className="font-medium">{filename}</span>
      </p>

      {buildMutation.isPending && <p className="mt-6 text-slate-500">Building configuration...</p>}
      {buildMutation.isError && (
        <p className="mt-6 text-red-600">Failed to build configuration for this dataset.</p>
      )}

      {columns && (
        <>
          <div className="mt-6 overflow-x-auto rounded-lg border border-slate-200 bg-white shadow-sm">
            <table className="min-w-full text-left text-sm">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50 text-slate-500">
                  <th className="px-3 py-2 font-medium">Column</th>
                  <th className="px-3 py-2 font-medium">Active</th>
                  <th className="px-3 py-2 font-medium">Numerical</th>
                  <th className="px-3 py-2 font-medium">Categorical</th>
                  <th className="px-3 py-2 font-medium">ID</th>
                  <th className="px-3 py-2 font-medium">Missing strategy</th>
                  <th className="px-3 py-2 font-medium">Scaling</th>
                  <th className="px-3 py-2 font-medium">Encoding</th>
                </tr>
              </thead>
              <tbody>
                {columns.map((column) => (
                  <tr key={column.name} className="border-b border-slate-100">
                    <td className="whitespace-nowrap px-3 py-2 font-medium text-slate-700">
                      {column.name}
                    </td>
                    <td className="px-3 py-2">
                      <input
                        type="checkbox"
                        checked={column.active}
                        onChange={(e) =>
                          setColumns((cols) =>
                            updateColumn(cols!, column.name, (c) => ({ ...c, active: e.target.checked }))
                          )
                        }
                      />
                    </td>
                    <td className="px-3 py-2">
                      <input
                        type="checkbox"
                        checked={column.numerical}
                        onChange={(e) =>
                          setColumns((cols) =>
                            updateColumn(cols!, column.name, (c) => ({
                              ...c,
                              numerical: e.target.checked,
                              categorical: e.target.checked ? false : c.categorical,
                            }))
                          )
                        }
                      />
                    </td>
                    <td className="px-3 py-2">
                      <input
                        type="checkbox"
                        checked={column.categorical}
                        onChange={(e) =>
                          setColumns((cols) =>
                            updateColumn(cols!, column.name, (c) => ({
                              ...c,
                              categorical: e.target.checked,
                              numerical: e.target.checked ? false : c.numerical,
                            }))
                          )
                        }
                      />
                    </td>
                    <td className="px-3 py-2">
                      <input
                        type="checkbox"
                        checked={column.id}
                        onChange={(e) =>
                          setColumns((cols) =>
                            updateColumn(cols!, column.name, (c) => ({ ...c, id: e.target.checked }))
                          )
                        }
                      />
                    </td>
                    <td className="px-3 py-2">
                      <select
                        value={column.missing_data_management.strategy}
                        onChange={(e) =>
                          setColumns((cols) =>
                            updateColumn(cols!, column.name, (c) => ({
                              ...c,
                              missing_data_management: {
                                ...c.missing_data_management,
                                strategy: e.target.value as MissingStrategy,
                              },
                            }))
                          )
                        }
                        className="rounded border border-slate-300 px-2 py-1"
                      >
                        {MISSING_STRATEGIES.map((strategy) => (
                          <option key={strategy} value={strategy}>
                            {strategy}
                          </option>
                        ))}
                      </select>
                    </td>
                    <td className="px-3 py-2">
                      <div className="flex items-center gap-1">
                        <input
                          type="checkbox"
                          checked={column.scaling.enabled}
                          disabled={!column.numerical}
                          onChange={(e) =>
                            setColumns((cols) =>
                              updateColumn(cols!, column.name, (c) => ({
                                ...c,
                                scaling: {
                                  enabled: e.target.checked,
                                  method: e.target.checked ? "standard" : "none",
                                },
                              }))
                            )
                          }
                        />
                        <select
                          value={column.scaling.method === "none" ? "standard" : column.scaling.method}
                          disabled={!column.scaling.enabled}
                          onChange={(e) =>
                            setColumns((cols) =>
                              updateColumn(cols!, column.name, (c) => ({
                                ...c,
                                scaling: { ...c.scaling, method: e.target.value as ScalerType },
                              }))
                            )
                          }
                          className="rounded border border-slate-300 px-2 py-1 disabled:opacity-40"
                        >
                          {SCALER_METHODS.map((method) => (
                            <option key={method} value={method}>
                              {method}
                            </option>
                          ))}
                        </select>
                      </div>
                    </td>
                    <td className="px-3 py-2">
                      <div className="flex items-center gap-1">
                        <input
                          type="checkbox"
                          checked={column.encoding.enabled}
                          disabled={!column.categorical}
                          onChange={(e) =>
                            setColumns((cols) =>
                              updateColumn(cols!, column.name, (c) => ({
                                ...c,
                                encoding: {
                                  enabled: e.target.checked,
                                  method: e.target.checked ? "one_hot" : "none",
                                  order: null,
                                },
                              }))
                            )
                          }
                        />
                        <select
                          value={column.encoding.method === "none" ? "one_hot" : column.encoding.method}
                          disabled={!column.encoding.enabled}
                          onChange={(e) =>
                            setColumns((cols) =>
                              updateColumn(cols!, column.name, (c) => ({
                                ...c,
                                encoding: { ...c.encoding, method: e.target.value as EncoderType },
                              }))
                            )
                          }
                          className="rounded border border-slate-300 px-2 py-1 disabled:opacity-40"
                        >
                          {ENCODER_METHODS.map((method) => (
                            <option key={method} value={method}>
                              {method}
                            </option>
                          ))}
                        </select>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="mt-4 flex items-center gap-4">
            <button
              onClick={() => revalidateMutation.mutate(columns)}
              disabled={revalidateMutation.isPending}
              className="rounded bg-slate-700 px-4 py-2 text-sm text-white disabled:opacity-50"
            >
              {revalidateMutation.isPending ? "Validating..." : "Re-validate configuration"}
            </button>

            {validation && (
              <span className={validation.is_valid ? "text-sm text-green-600" : "text-sm text-red-600"}>
                {validation.is_valid ? "Configuration is valid." : validation.errors.join("; ")}
              </span>
            )}
          </div>

          {validation?.is_valid && (
            <div className="mt-8 rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
              <h2 className="text-lg font-medium text-slate-800">Run structure analysis</h2>

              <div className="mt-4 flex flex-wrap items-end gap-4">
                <label className="block">
                  <span className="text-sm text-slate-600">Clustering algorithm</span>
                  <select
                    value={clusteringAlgorithm}
                    onChange={(e) => setClusteringAlgorithm(e.target.value as ClusteringAlgorithmName)}
                    className="mt-1 block rounded border border-slate-300 px-3 py-2"
                  >
                    {CLUSTERING_ALGORITHMS.map((algorithm) => (
                      <option key={algorithm} value={algorithm}>
                        {algorithm}
                      </option>
                    ))}
                  </select>
                </label>

                <label className="block">
                  <span className="text-sm text-slate-600">
                    {clusteringAlgorithm === "hdbscan" ? "Min cluster size" : "Number of clusters"}
                  </span>
                  <input
                    type="number"
                    min={2}
                    value={primaryParam}
                    onChange={(e) => setPrimaryParam(Number(e.target.value))}
                    className="mt-1 block w-32 rounded border border-slate-300 px-3 py-2"
                  />
                </label>

                <label className="flex items-center gap-2 pb-2">
                  <input
                    type="checkbox"
                    checked={includeProjection}
                    onChange={(e) => setIncludeProjection(e.target.checked)}
                  />
                  <span className="text-sm text-slate-600">Include 2D PCA projection</span>
                </label>
              </div>

              {runMutation.isError && (
                <p className="mt-4 text-sm text-red-600">
                  Failed to start the analysis. Please check your configuration.
                </p>
              )}

              <button
                onClick={() => {
                  const rawConfig = toRawDataConfig(columns);
                  setDataConfig({ columns } as never);
                  void rawConfig; // kept for clarity: server already holds this config from the last revalidate
                  runMutation.mutate();
                }}
                disabled={runMutation.isPending}
                className="mt-6 rounded bg-blue-600 px-4 py-2 text-sm text-white disabled:opacity-50"
              >
                {runMutation.isPending ? "Starting..." : "Run analysis →"}
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}