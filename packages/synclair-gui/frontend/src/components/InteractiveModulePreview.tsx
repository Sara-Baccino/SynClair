import { useMutation } from "@tanstack/react-query";
import { runDemoStructure } from "../api/client";

export function InteractiveModulePreview() {
  const mutation = useMutation({
    mutationFn: () => runDemoStructure({ dataset_name: "iris", n_clusters: 3, include_projection: true }),
  });

  return (
    <div className="bg-white p-6 rounded-xl border border-[#E2E8F0] shadow-sm">
      <h2 className="text-xl font-bold text-[#0284C7] mb-4">See it in action</h2>
      <p className="text-sm text-[#64748B] mb-4">
        Run a read-only example on the Iris dataset. This is a preview, not a real analysis session.
      </p>
      <button
        onClick={() => mutation.mutate()}
        disabled={mutation.isPending}
        className="rounded bg-[#0284C7] px-4 py-2 text-sm text-white disabled:opacity-50"
      >
        {mutation.isPending ? "Running..." : "Run example on Iris"}
      </button>

      {mutation.data?.success && (
        <div className="mt-4 text-sm text-[#1E293B]">
          <p>Clusters found: {String(mutation.data.metrics.n_clusters)}</p>
          <p>Silhouette: {typeof mutation.data.metrics.silhouette === "number" ? mutation.data.metrics.silhouette.toFixed(3) : "-"}</p>
        </div>
      )}
    </div>
  );
}