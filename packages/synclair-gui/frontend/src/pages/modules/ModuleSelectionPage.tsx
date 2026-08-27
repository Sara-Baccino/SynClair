import { useNavigate } from "react-router-dom";
import { AVAILABLE_MODULES } from "../../constants/modules";
import { useWorkspace } from "../../context/WorkspaceContext";

export function ModuleSelectionPage() {
  const navigate = useNavigate();
  const { setSelectedModule } = useWorkspace();

  return (
    <div className="min-h-screen bg-slate-50 p-10">
      <h1 className="text-2xl font-semibold text-slate-800">Select a module</h1>
      <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2">
        {AVAILABLE_MODULES.map((mod) => (
          <button
            key={mod.id}
            disabled={!mod.enabled}
            onClick={() => {
              setSelectedModule(mod.id);
              navigate(`/workspace/modules/${mod.id}/config`);
            }}
            className="rounded-lg border border-slate-200 bg-white p-6 text-left shadow-sm disabled:cursor-not-allowed disabled:opacity-40"
          >
            <h2 className="font-medium text-slate-800">{mod.title}</h2>
            <p className="mt-1 text-xs text-slate-400">{mod.subtitle}</p>
            {!mod.enabled && <p className="mt-1 text-xs text-slate-400">Coming soon</p>}
          </button>
        ))}
      </div>
    </div>
  );
}