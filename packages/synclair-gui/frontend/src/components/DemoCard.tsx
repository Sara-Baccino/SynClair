/**
 * synclair-gui frontend DemoCard
 * -------------------------------------
 *
 * Self-contained interactive card: runs a single public demo
 * (POST /demo/structure/run) for a given dataset, and renders the
 * resulting metrics + a colored scatter plot of the PCA embedding (if
 * present). Fully public/stateless -- no auth, no dataset_store/job
 * polling involved (the endpoint itself is synchronous).
 */

import { useMutation } from "@tanstack/react-query";
import {
  CartesianGrid,
  Legend,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { runDemoStructure } from "../api/client";
import type { DemoDatasetDTO, DemoStructureRunResponse } from "../types/api";

const CLUSTER_COLORS = ["#2563eb", "#dc2626", "#16a34a", "#d97706", "#7c3aed", "#0891b2"];

function buildScatterSeries(response: DemoStructureRunResponse) {
  if (!response.embedding) return [];

  const uniqueLabels = Array.from(new Set(response.labels)).sort((a, b) => a - b);

  return uniqueLabels.map((label) => ({
    label,
    color: CLUSTER_COLORS[label % CLUSTER_COLORS.length],
    points: response.embedding!.filter((_, index) => response.labels[index] === label),
  }));
}

export function DemoCard({ dataset }: { dataset: DemoDatasetDTO }) {
  const mutation = useMutation({
    mutationFn: () =>
      runDemoStructure({
        dataset_name: dataset.name as DemoStructureRunResponse["dataset_name"] extends string
          ? "blobs_2d" | "elongated_clusters" | "clinical_like"
          : never,
        n_clusters: 3,
        include_projection: true,
      }),
  });

  const result = mutation.data;
  const series = result ? buildScatterSeries(result) : [];

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <h3 className="text-lg font-semibold text-slate-800">{dataset.title}</h3>
      <p className="mt-1 text-sm text-slate-500">{dataset.description}</p>

      <button
        onClick={() => mutation.mutate()}
        disabled={mutation.isPending}
        className="mt-4 rounded bg-blue-600 px-3 py-1.5 text-sm text-white disabled:opacity-50"
      >
        {mutation.isPending ? "Running..." : "Run demo"}
      </button>

      {mutation.isError && (
        <p className="mt-3 text-sm text-red-600">
          Demo run failed. Please try again.
        </p>
      )}

      {result && !result.success && (
        <p className="mt-3 text-sm text-red-600">{result.error}</p>
      )}

      {result && result.success && (
        <div className="mt-4">
          <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm text-slate-600">
            <dt>Observations</dt>
            <dd>{result.n_observations}</dd>
            <dt>Features</dt>
            <dd>{result.n_features}</dd>
            <dt>Clusters</dt>
            <dd>{String(result.metrics.n_clusters ?? "-")}</dd>
            <dt>Silhouette</dt>
            <dd>{typeof result.metrics.silhouette === "number" ? result.metrics.silhouette.toFixed(3) : "-"}</dd>
          </dl>

          {series.length > 0 && (
            <ScatterChart width={280} height={220} className="mt-3">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" dataKey="x" name="dim_0" hide />
              <YAxis type="number" dataKey="y" name="dim_1" hide />
              <Tooltip cursor={{ strokeDasharray: "3 3" }} />
              <Legend />
              {series.map((s) => (
                <Scatter
                  key={s.label}
                  name={`Cluster ${s.label}`}
                  data={s.points}
                  fill={s.color}
                />
              ))}
            </ScatterChart>
          )}
        </div>
      )}
    </div>
  );
}