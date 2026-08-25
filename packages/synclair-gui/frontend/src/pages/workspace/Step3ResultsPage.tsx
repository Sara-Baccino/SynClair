/**
 * synclair-gui frontend Step3ResultsPage
 * -----------------------------------------------
 *
 * Workspace Step 3: polls job status (GET /structure/jobs/:id) until
 * completion, then fetches and renders the result preview (metrics,
 * tables, datasets, embedding scatter plot), with buttons to download
 * full tables/datasets as CSV and the PDF report -- all via the
 * synclair-reporting-backed endpoints added alongside this page.
 */

import { useQuery } from "@tanstack/react-query";
import { useParams, useNavigate } from "react-router-dom";
import {
  CartesianGrid,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import {
  buildDownloadUrl,
  buildReportUrl,
  downloadAuthenticatedFile,
  getStructureJobResult,
  getStructureJobStatus,
} from "../../api/client";
import type { DataFramePreviewDTO } from "../../types/api";

function formatCellValue(value: unknown): string {
  if (typeof value === "number") {
    if (Number.isInteger(value)) {
      return value.toString();
    }
    // Arrotonda a un massimo di 3 cifre decimali ed elimina zeri finali non necessari
    return Number(value.toFixed(3)).toString();
  }
  return String(value ?? "");
}

export function TablePreview({ table }: { table: DataFramePreviewDTO }) {
  return (
    <div className="mt-4 overflow-x-auto rounded-lg border border-slate-200 shadow-sm">
      <table className="min-w-full text-left text-sm">
        <thead>
          <tr className="border-b border-slate-200 bg-slate-50/80 text-slate-600">
            {table.columns.map((col) => (
              <th key={col} className="whitespace-nowrap px-3 py-2.5 font-medium">
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 bg-white">
          {table.preview.map((row, i) => (
            <tr key={i} className="hover:bg-slate-50/50 transition-colors">
              {table.columns.map((col) => (
                <td key={col} className="whitespace-nowrap px-3 py-2 font-mono text-xs text-slate-700">
                  {formatCellValue(row[col])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      <div className="bg-slate-50/50 px-3 py-2 text-xs text-slate-400 border-t border-slate-100">
        Showing {table.preview.length} of {table.n_rows} rows.
      </div>
    </div>
  );
}

export function Step3ResultsPage() {
  const { jobId } = useParams<{ jobId: string }>();
  const navigate = useNavigate();

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
  });

  if (!jobId) {
    return <div className="min-h-screen bg-slate-50 p-10 text-slate-600">No job selected.</div>;
  }

  const clusteredDataset = resultQuery.data?.datasets.find(
    (d: DataFramePreviewDTO) => d.name === "clustered_dataset"
  );
  const embeddingDataset = resultQuery.data?.datasets.find(
    (d: DataFramePreviewDTO) => d.name === "projection_embedding"
  );
  const scatterPoints =
    embeddingDataset && clusteredDataset
      ? embeddingDataset.preview.map((row: Record<string, unknown>, i: number) => ({
          x: Number(row["dim_0"] ?? 0),
          y: Number(row["dim_1"] ?? 0),
          cluster: (clusteredDataset.preview[i]?.["cluster_label"] as string | number | null) ?? null,
        }))
      : [];

  return (
    <div className="min-h-screen bg-slate-50 p-10">
      <h1 className="text-2xl font-semibold text-slate-800">Step 3 · Results</h1>

      {!isFinished && (
        <div className="mt-6 rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <p className="text-slate-700">{statusQuery.data?.progress.message ?? "Starting..."}</p>
          {statusQuery.data?.progress.percentage !== null && (
            <div className="mt-3 h-2 w-full rounded bg-slate-100">
              <div
                className="h-2 rounded bg-blue-600 transition-all"
                style={{ width: `${statusQuery.data?.progress.percentage ?? 0}%` }}
              />
            </div>
          )}
        </div>
      )}

      {resultQuery.data && (
        <div className="mt-6 space-y-6">
          {!resultQuery.data.success && (
            <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-red-700">
              Analysis failed: {resultQuery.data.error}
            </div>
          )}

          {resultQuery.data.success && (
            <>
              <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
                <h2 className="text-lg font-medium text-slate-800">Metrics</h2>
                <dl className="mt-3 grid grid-cols-2 gap-x-6 gap-y-1 text-sm text-slate-600 sm:grid-cols-4">
                  {Object.entries(resultQuery.data.metrics).map(([key, value]) => (
                    <div key={key}>
                      <dt className="text-slate-400">{key}</dt>
                      <dd className="font-medium text-slate-800">
                        {typeof value === "number" 
                          ? Number.isInteger(value) ? value.toString() : value.toFixed(3)
                          : String(value)
                        }
                      </dd>
                    </div>
                  ))}
                </dl>

                <div className="mt-4 flex gap-3">
                  <button
                    onClick={() =>
                      downloadAuthenticatedFile(buildReportUrl(jobId), `synclair-report-${jobId}.pdf`)
                    }
                    className="rounded bg-slate-800 px-3 py-1.5 text-sm text-white hover:bg-slate-700 transition"
                  >
                    Download PDF report
                  </button>
                </div>
              </div>

              {scatterPoints.length > 0 && (
                <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
                  <h2 className="text-lg font-medium text-slate-800">Embedding</h2>
                  <ScatterChart width={400} height={300} className="mt-3">
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis type="number" dataKey="x" hide />
                    <YAxis type="number" dataKey="y" hide />
                    <Tooltip cursor={{ strokeDasharray: "3 3" }} />
                    <Scatter data={scatterPoints} fill="#2563eb" />
                  </ScatterChart>
                </div>
              )}

              {[...resultQuery.data.tables, ...resultQuery.data.datasets].map((table) => (
                <div key={table.name} className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
                  <div className="flex items-center justify-between">
                    <h2 className="text-lg font-medium text-slate-800">{table.name}</h2>
                    <button
                      onClick={() =>
                        downloadAuthenticatedFile(
                          buildDownloadUrl(
                            jobId,
                            resultQuery.data!.tables.includes(table) ? "tables" : "datasets",
                            table.name
                          ),
                          `${table.name}.csv`
                        )
                      }
                      className="rounded border border-slate-300 px-3 py-1 text-sm text-slate-700 hover:bg-slate-50 transition"
                    >
                      Download CSV
                    </button>
                  </div>
                  <TablePreview table={table} />
                </div>
              ))}
            </>
          )}
        </div>
      )}

      {/* Pulsanti di navigazione inseriti correttamente dentro il container div radice */}
      <div className="mt-10 pt-6 border-t border-slate-200 flex items-center justify-between">
        <button
          onClick={() => navigate("/", { replace: true })}
          className="rounded border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 transition"
        >
          ← Torna alla Landing Page
        </button>

        <button
          onClick={() => navigate("/workspace/upload", { replace: true })}
          className="rounded bg-cyan-600 px-4 py-2 text-sm font-medium text-white hover:bg-cyan-500 transition"
        >
          Avvia Nuova Analisi
        </button>
      </div>
    </div>
  );
}