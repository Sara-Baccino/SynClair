/**
 * synclair-gui frontend router
 * ----------------------------------
 *
 * Route table: public Landing/Login, protected Workspace (Step 1/2/3).
 * Workspace routes are wrapped individually in <ProtectedRoute> rather
 * than wrapping a single parent route, so each step's auth check is
 * explicit and self-contained -- consistent with how each backend
 * Workspace endpoint (datasets.py/structure.py) independently declares
 * Depends(get_current_user) rather than relying on a single shared gate.
 */

import { createBrowserRouter, Navigate, Outlet } from "react-router-dom";

import { ProtectedRoute } from "./components/ProtectedRoute";
import { LoginPage } from "./pages/LoginPage";
import { ModuleDetailPage } from "./pages/modules/ModuleDetailPage"; // Nuova pagina
import { Step1UploadPage } from "./pages/workspace/Step1UploadPage";
import { Step2ConfigurePage } from "./pages/workspace/Step2ConfigurePage";
import { Step3ResultsPage } from "./pages/workspace/Step3ResultsPage";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <LoginPage />,
  },
  {
    path: "/login",
    element: <LoginPage />,
  },
  // Rotta per la scheda tecnica dettagliata dei singoli moduli
  {
    path: "/modules/:moduleId",
    element: <ModuleDetailPage />,
  },
  {
    path: "/workspace",
    element: (
      <ProtectedRoute>
        <Outlet />
      </ProtectedRoute>
    ),
    children: [
      {
        path: "",
        element: <Navigate to="/workspace/upload" replace />,
      },
      {
        path: "upload",
        element: <Step1UploadPage />,
      },
      {
        path: "configure",
        element: <Step2ConfigurePage />,
      },
      {
        path: "results/:jobId",
        element: <Step3ResultsPage />,
      },
    ],
  },
  {
    path: "*",
    element: <Navigate to="/" replace />,
  },
]);