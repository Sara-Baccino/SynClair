import { useParams } from "react-router-dom";
import { Link } from "react-router-dom";
import { CartesianGrid, Scatter, ScatterChart, Tooltip, XAxis, YAxis } from "recharts";
import { useWorkspace } from "../../../context/WorkspaceContext";
import { useStructureRun } from "../../../hooks/useStructureRun";
import { getModuleTitle } from "../../../constants/modules";

export function ResultsSection() {
  const { moduleId } = useParams<{ moduleId: string }>();
  const { jobId, lastRunConfig } = useWorkspace();
  const { statusQuery, resultQuery, isFinished } = useStructureRun(jobId);

  const clusteredDataset = resultQuery.data?.datasets.find((d) => d.name === "clustered_dataset");
  const embeddingDataset = resultQuery.data?.datasets.find((d) => d.name === "projection_embedding");
  const scatterPoints =
    embeddingDataset && clusteredDataset
      ? embeddingDataset.preview.map((row, i) => ({
          x: Number(row["dim_0"] ?? 0),
          y: Number(row["dim_1"] ?? 0),
          cluster: clusteredDataset.preview[i]?.["cluster_label"] ?? null,
        }))
      : [];

  return (
    <div>
      <h1 className="mb-2 text-2xl font-semibold text-slate-800">{getModuleTitle(moduleId)} Results</h1>

      {lastRunConfig && (
        <p className="mb-4 text-sm text-slate-500">
          Algorithm: <span className="font-medium text-slate-700">{lastRunConfig.algorithm}</span>
          {" · "}{lastRunConfig.algorithm === "hdbscan" ? "Min cluster size" : "Clusters"}:{" "}
          <span className="font-medium text-slate-700">{lastRunConfig.primaryParam}</span>
          {lastRunConfig.includeProjection && " · with 2D PCA projection"}
        </p>
      )}

      {!isFinished && (
        <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <p className="text-slate-700">{statusQuery.data?.progress.message ?? "Starting..."}</p>
          {statusQuery.data?.progress.percentage != null && (
            <div className="mt-3 h-2 w-full rounded bg-slate-100">
              <div className="h-2 rounded bg-blue-600 transition-all" style={{ width: `${statusQuery.data.progress.percentage}%` }} />
            </div>
          )}
        </div>
      )}

      {isFinished && (resultQuery.isError || (resultQuery.data && !resultQuery.data.success)) && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-red-700">
          Analysis failed{resultQuery.data?.error ? `: ${resultQuery.data.error}` : "."}
        </div>
      )}

      {isFinished && resultQuery.data?.success && (
        <>
          <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="text-lg font-medium text-slate-800">Metrics</h2>
            <dl className="mt-3 grid grid-cols-2 gap-x-6 gap-y-1 text-sm text-slate-600 sm:grid-cols-4">
              {Object.entries(resultQuery.data.metrics).map(([key, value]) => (
                <div key={key}><dt className="text-slate-400">{key}</dt><dd className="font-medium text-slate-800">{typeof value === "number" ? value.toFixed(3) : String(value)}</dd></div>
              ))}
            </dl>
          </div>

          <div className="mt-6 rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="text-lg font-medium text-slate-800 mb-3">Artifacts</h2>

            {scatterPoints.length > 0 && (
              <ScatterChart width={400} height={280} className="mb-4">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" dataKey="x" hide />
                <YAxis type="number" dataKey="y" hide />
                <Tooltip cursor={{ strokeDasharray: "3 3" }} />
                <Scatter data={scatterPoints} fill="#2563eb" />
              </ScatterChart>
            )}

            {[...resultQuery.data.tables, ...resultQuery.data.datasets].map((table) => (
              <div key={table.name} className="mb-4 last:mb-0">
                <p className="text-sm font-medium text-slate-700">{table.name} · {table.n_rows} rows · {table.n_columns} columns</p>
                <div className="mt-1 overflow-x-auto max-h-56">
                  <table className="min-w-full text-left text-xs">
                    <thead>
                      <tr className="border-b border-slate-200 text-slate-400">
                        {table.columns.map((c) => <th key={c} className="px-2 py-1">{c}</th>)}
                      </tr>
                    </thead>
                    <tbody>
                      {table.preview.map((row, i) => (
                        <tr key={i} className="border-b border-slate-100">
                          {table.columns.map((c) => <td key={c} className="px-2 py-1 text-slate-600">{String(row[c] ?? "")}</td>)}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-8 flex items-center gap-3">
            <button
              disabled
              title="Use this result as input for a new pipeline step (coming soon — requires registering the artifact as a new dataset)"
              className="rounded bg-slate-200 px-4 py-2 text-sm text-slate-400 cursor-not-allowed"
            >
              Continue composing pipeline
            </button>
            <Link to="/" className="ml-auto rounded border border-slate-300 px-4 py-2 text-sm text-slate-600 hover:bg-slate-50">
              ← Back to Home
            </Link>
          </div>
        </>
      )}
    </div>
  );
}