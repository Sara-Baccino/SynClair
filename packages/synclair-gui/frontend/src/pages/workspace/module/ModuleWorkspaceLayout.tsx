import { Outlet } from "react-router-dom";
import { AnalysisSidebar } from "../../../components/workspace/AnalysisSidebar";

export function ModuleWorkspaceLayout() {
  return (
    <div className="flex min-h-screen bg-slate-50">
      <AnalysisSidebar />
      <main className="flex-1 p-8">
        <Outlet />
      </main>
    </div>
  );
}