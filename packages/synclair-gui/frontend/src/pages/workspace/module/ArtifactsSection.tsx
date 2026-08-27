import { CartesianGrid, Scatter, ScatterChart, Tooltip, XAxis, YAxis } from "recharts";
import { useWorkspace } from "../../../context/WorkspaceContext";
import { useStructureRun } from "../../../hooks/useStructureRun";
import { buildDownloadUrl, downloadAuthenticatedFile } from "../../../api/client";
import type { DataFramePreviewDTO } from "../../../types/api";

function formatCellValue(value: unknown): string {
  if (typeof value === "number") {
    if (Number.isInteger(value)) {
      return value.toString();
    }
    return Number(value.toFixed(3)).toString();
  }
  return String(value ?? "");
}

function TablePreview({ table }: { table: DataFramePreviewDTO }) {
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

export function ArtifactsSection() {
  const { jobId } = useWorkspace();
  const { statusQuery, resultQuery, isFinished } = useStructureRun(jobId);

  if (!jobId) {
    return <div className="text-slate-600">No job selected.</div>;
  }

  if (!isFinished) {
    return (
      <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <p className="text-slate-700">{statusQuery.data?.progress.message ?? "Analysis in progress..."}</p>
        {statusQuery.data?.progress.percentage != null && (
          <div className="mt-3 h-2 w-full rounded bg-slate-100">
            <div
              className="h-2 rounded bg-blue-600 transition-all"
              style={{ width: `${statusQuery.data.progress.percentage}%` }}
            />
          </div>
        )}
      </div>
    );
  }

  if (resultQuery.isError || !resultQuery.data) {
    return <div className="text-red-600">Failed to load artifacts.</div>;
  }

  const { success, tables, datasets } = resultQuery.data;

  if (!success) {
    return null;
  }

  const clusteredDataset = datasets.find((d: DataFramePreviewDTO) => d.name === "clustered_dataset");
  const embeddingDataset = datasets.find((d: DataFramePreviewDTO) => d.name === "projection_embedding");
  const scatterPoints =
    embeddingDataset && clusteredDataset
      ? embeddingDataset.preview.map((row: Record<string, unknown>, i: number) => ({
          x: Number(row["dim_0"] ?? 0),
          y: Number(row["dim_1"] ?? 0),
          cluster: (clusteredDataset.preview[i]?.["cluster_label"] as string | number | null) ?? null,
        }))
      : [];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-slate-800">Artifacts</h1>

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

      {[...tables, ...datasets].map((table) => (
        <div key={table.name} className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-medium text-slate-800">{table.name}</h2>
            <button
              onClick={() =>
                downloadAuthenticatedFile(
                  buildDownloadUrl(
                    jobId,
                    tables.includes(table) ? "tables" : "datasets",
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
    </div>
  );
}