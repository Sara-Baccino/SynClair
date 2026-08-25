import { useParams, useNavigate } from "react-router-dom";

export function ModuleDetailPage() {
  const { moduleId } = useParams<{ moduleId: string }>();
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-slate-900 text-white p-8 max-w-5xl mx-auto">
      <button 
        onClick={() => navigate("/")}
        className="mb-8 text-sm text-cyan-400 hover:underline flex items-center gap-2"
      >
        ← Torna alla Landing Page
      </button>

      <h1 className="text-4xl font-bold mb-4 capitalize">{moduleId?.replace("-", " ")}</h1>
      <p className="text-slate-300 mb-8">Scheda tecnica dettagliata degli algoritmi e parametri configurabili.</p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-12">
        {/* Sezione Parametri & Algoritmi */}
        <div className="bg-slate-800 p-6 rounded-xl border border-slate-700">
          <h2 className="text-xl font-bold text-cyan-400 mb-4">Algoritmi Supportati</h2>
          <ul className="list-disc list-inside space-y-2 text-slate-300 text-sm">
            <li><strong>PCA / UMAP:</strong> Riduzione della dimensionalità</li>
            <li><strong>k-Means / Leiden:</strong> Clustering di sottopopolazioni</li>
            <li><strong>Z-Score Normalization:</strong> Standardizzazione dei parametri</li>
          </ul>
        </div>

        {/* Sezione Video / Immagine Dimostrativa */}
        <div className="bg-slate-800 p-6 rounded-xl border border-slate-700 flex flex-col justify-center items-center">
          <div className="w-full h-48 bg-slate-900 rounded-lg flex items-center justify-center text-slate-500 border border-slate-700">
            [ Immagine / Mini Video del Modulo ]
          </div>
        </div>
      </div>
    </div>
  );
}