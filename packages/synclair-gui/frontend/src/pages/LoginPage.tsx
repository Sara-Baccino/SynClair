import { useState, type FormEvent, useEffect } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";
import { ApiError } from "../api/client";
import { useAuth } from "../context/AuthContext";

interface LocationState {
  from?: { pathname: string };
}

export function LoginPage() {
  const { isAuthenticated, isInitializing, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Gestione dello scroll intelligente al ritorno sulla pagina
  useEffect(() => {
    if (location.hash) {
      const targetId = location.hash.replace("#", "");
      const elem = document.getElementById(targetId);
      if (elem) {
        elem.scrollIntoView({ behavior: "smooth", block: "start" });
        return;
      }
    }

    const savedSection = sessionStorage.getItem("landing_last_section");
    if (savedSection) {
      const elem = document.getElementById(savedSection);
      if (elem) {
        setTimeout(() => {
          elem.scrollIntoView({ behavior: "auto", block: "start" });
        }, 50);
        return;
      }
    }

    window.scrollTo(0, 0);
  }, [location]);

  if (isInitializing) {
    return <div className="min-h-screen bg-[#FAF8F5]" />;
  }

  const state = location.state as LocationState | null;
  if (isAuthenticated && state?.from) {
    return <Navigate to={state.from.pathname} replace />;
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      await login(username, password);
      const state = location.state as LocationState | null;
      navigate(state?.from?.pathname ?? "/workspace", { replace: true });
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        setError("Incorrect username or password.");
      } else {
        setError("Login failed. Please try again.");
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  const scrollToSection = (id: string) => {
    sessionStorage.setItem("landing_last_section", id);
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  };

  const navigateToModule = (path: string, sectionId = "modules") => {
    sessionStorage.setItem("landing_last_section", sectionId);
    navigate(path);
  };

  return (
    <div className="min-h-screen w-full bg-[#FAF8F5] text-[#1E293B] font-['Manrope',sans-serif] selection:bg-[#FEF3C7] selection:text-[#0284C7]">
      {/* Import dei font e stili per l'animazione dell'onda e punti glowing */}
      <link
        rel="stylesheet"
        href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap"
      />
      <style>{`
        @keyframes waveMotion {
          0% { transform: translateY(0px) scaleY(1); }
          50% { transform: translateY(-12px) scaleY(1.05); }
          100% { transform: translateY(0px) scaleY(1); }
        }
        @keyframes pulseDot {
          0%, 100% { opacity: 0.3; transform: scale(1); }
          50% { opacity: 0.95; transform: scale(1.6); }
        }
        .animate-wave {
          animation: waveMotion 8s ease-in-out infinite;
        }
        .animate-[#dot-1] { animation: pulseDot 3s ease-in-out infinite; }
        .animate-[#dot-2] { animation: pulseDot 4.5s ease-in-out 1s infinite; }
        .animate-[#dot-3] { animation: pulseDot 3.5s ease-in-out 0.5s infinite; }
        .animate-[#dot-4] { animation: pulseDot 5s ease-in-out 1.5s infinite; }
      `}</style>

      {/* 1. NAVBAR */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-[#FAF8F5]/90 backdrop-blur-md border-b border-[#E2E8F0] px-6 sm:px-10 py-4 flex items-center justify-between">
        <div className="flex items-center gap-8">
          <span
            className="text-xl font-extrabold tracking-tight text-[#1E293B] cursor-pointer hover:text-[#0284C7] transition"
            onClick={() => scrollToSection("hero")}
          >
            SynClair
          </span>
          <div className="hidden md:flex items-center gap-6 text-sm font-medium text-[#64748B]">
            <button onClick={() => scrollToSection("overview")} className="hover:text-[#1E293B] transition">Overview</button>
            <button onClick={() => scrollToSection("modules")} className="hover:text-[#1E293B] transition">Modules</button>
            <button onClick={() => scrollToSection("demo")} className="hover:text-[#1E293B] transition">Demo</button>
            <button onClick={() => scrollToSection("workspace")} className="hover:text-[#1E293B] transition">Workspace</button>
          </div>
        </div>

        <div>
          <button
            onClick={() => scrollToSection("workspace")}
            className="text-xs font-semibold px-4 py-2 rounded-lg bg-[#f5d7f0] border border-[#f5d7f0]/30 text-[#2e0327] hover:bg-[#0EA5E9] hover:text-[#FFFFFF] transition duration-200"
          >
            Access Workspace
          </button>
        </div>
      </nav>

      {/* 2. HERO SECTION CON SFONDO AD ONDA ED ELEMENTI LUMINOSI */}
      <section id="hero" className="relative pt-36 pb-24 px-6 text-center max-w-6xl mx-auto flex flex-col items-center justify-center min-h-[90vh] overflow-hidden">
        
        {/* SFONDO ANIMATO: Onde Ambrate/Rosate e Punti Luminosi */}
        <div className="absolute inset-0 pointer-events-none -z-10 flex items-center justify-center overflow-hidden">
          {/* Bagliore di sfondo sfumato */}
          <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[350px] bg-gradient-to-tr from-[#FEF3C7] via-[#FFE4E6] to-[#E0F2FE] rounded-full filter blur-3xl opacity-70" />

          {/* Onde SVG animate */}
          <svg className="w-full h-full min-w-[800px] opacity-40 animate-wave" viewBox="0 0 1440 600" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path
              d="M0,160 C320,300 420,40 720,180 C1020,320 1120,80 1440,200 L1440,600 L0,600 Z"
              fill="url(#amber-pink-grad)"
            />
            <path
              d="M0,280 C240,180 480,320 720,220 C960,120 1200,280 1440,180"
              stroke="#0284C7"
              strokeWidth="1.5"
              strokeDasharray="4 4"
              opacity="0.5"
            />
            <path
              d="M0,200 C360,100 600,300 900,160 C1200,20 1320,240 1440,220"
              stroke="#0EA5E9"
              strokeWidth="2"
              opacity="0.6"
            />
            <defs>
              <linearGradient id="amber-pink-grad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#FEF3C7" stopOpacity="0.8" />
                <stop offset="50%" stopColor="#FFE4E6" stopOpacity="0.5" />
                <stop offset="100%" stopColor="#E0F2FE" stopOpacity="0.3" />
              </linearGradient>
            </defs>
          </svg>

          {/* Punti/Nodi Luminosi Animati (Glow Dots) */}
          <div className="absolute inset-0 max-w-4xl mx-auto">
            <div className="absolute top-[25%] left-[20%] w-3 h-3 bg-[#0EA5E9] rounded-full shadow-[0_0_12px_#0EA5E9] animate-[#dot-1]" />
            <div className="absolute top-[40%] right-[22%] w-3.5 h-3.5 bg-[#EC4899] rounded-full shadow-[0_0_14px_#EC4899] animate-[#dot-2]" />
            <div className="absolute top-[65%] left-[30%] w-2.5 h-2.5 bg-[#0284C7] rounded-full shadow-[0_0_10px_#0284C7] animate-[#dot-3]" />
            <div className="absolute top-[30%] right-[38%] w-2 h-2 bg-[#0EA5E9] rounded-full shadow-[0_0_8px_#0EA5E9] animate-[#dot-4]" />
          </div>
        </div>

        {/* CONTENUTO HERO */}
        <div className="relative z-10 max-w-4xl mx-auto flex flex-col items-center">
          <h1 className="text-6xl sm:text-7xl lg:text-8xl font-extrabold tracking-tight text-[#1E293B] mb-6 select-none">
            SynClair
          </h1>

          <h2 className="text-3xl sm:text-5xl font-semibold text-[#1E293B] mb-6 leading-tight">
            Explore the <span className="text-[#ded77a] font-semibold">structure</span>.<br />
            Discover the <span className="text-[#cf6dbe] font-semibold">insights</span>.
          </h2>

          <p className="text-base sm:text-lg text-[#64748B] font-normal max-w-2xl leading-relaxed mb-10">
            A modular analytical environment for understanding the patterns, relationships and constraints hidden within complex data.
          </p>

          <div className="flex flex-col sm:flex-row items-center gap-4 mb-16">
            <button
              onClick={() => scrollToSection("overview")}
              className="bg-[#0284C7] hover:bg-[#0EA5E9] text-[#FFFFFF] font-semibold px-8 py-3.5 rounded-xl shadow-md transition duration-200"
            >
              Explore SynClair ↓
            </button>
            <button
              onClick={() => scrollToSection("demo")}
              className="bg-[#FFFFFF] border border-[#E2E8F0] hover:border-[#64748B] text-[#1E293B] font-semibold px-8 py-3.5 rounded-xl transition duration-200 shadow-sm"
            >
              Try Demo
            </button>
          </div>

          <div className="flex flex-wrap items-center justify-center gap-3 text-xs font-semibold text-[#64748B] uppercase tracking-wider">
            <span className="px-3 py-1 rounded-full bg-[#f7daf7] text-[#4B174D]">Structure</span>
            <span>·</span>
            <span className="px-3 py-1 rounded-full bg-[#E0F2FE] text-[#0369A1]">Compare</span>
            <span>·</span>
            <span className="px-3 py-1 rounded-full bg-[#FFE4E6] text-[#BE123C]">Validate</span>
            <span>·</span>
            <span className="px-3 py-1 rounded-full bg-[#FEF3C7] border border-[#E2E8F0] text-[#B49209]">Understand</span>
          </div>
        </div>
      </section>

      {/* 3. OVERVIEW SECTION */}
      <section id="overview" className="py-24 px-6 border-t border-[#E2E8F0] bg-[#FFFFFF]">
        <div className="max-w-5xl mx-auto">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <h2 className="text-xs font-semibold uppercase tracking-widest text-[#0284C7] mb-2">
              Overview
            </h2>
            <h3 className="text-3xl sm:text-4xl font-semibold text-[#1E293B] mb-6">
              What is SynClair?
            </h3>
            <p className="text-base sm:text-lg text-[#64748B] font-normal leading-relaxed mb-6">
              Modern datasets are rarely difficult because of their size alone. Their complexity comes from missing values, inconsistent formats, hidden relationships, structural constraints, heterogeneous sources and patterns that are difficult to inspect manually.
            </p>
            <p className="text-base sm:text-lg text-[#1E293B] font-medium leading-relaxed">
              SynClair is a modular analytical environment designed to make these structures <span className="text-[#e09f43] font-semibold">visible</span>, <span className="text-[#0284C7] font-semibold">measurable</span> and <span className="text-[#E11D48] font-semibold">interpretable</span>.
            </p>
          </div>

          {/* DIAGRAMMA ARCHITETTURALE MODULARE */}
          <div className="my-16 p-8 bg-[#FAF8F5] border border-[#E2E8F0] rounded-2xl shadow-sm">
            <h4 className="text-xs font-semibold uppercase tracking-widest text-[#64748B] text-center mb-8">
              A Modular Approach to Data Understanding
            </h4>

            <div className="flex flex-col items-center">
              <div className="px-6 py-2.5 rounded-lg bg-[#e3fcfb] border border-[#0EA5E9]/40 text-[#167874] font-extrabold text-sm">
                SynClair
              </div>
              <div className="w-0.5 h-8 bg-[#E2E8F0] my-1"></div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full max-w-4xl">
                <div className="flex flex-col items-center bg-[#FFFFFF] border border-[#E2E8F0] p-5 rounded-xl">
                  <span className="text-xs font-semibold text-[#0284C7] tracking-wider mb-2">STRUCTURE</span>
                  <div className="w-full border-t border-[#E2E8F0] my-2"></div>
                  <ul className="text-xs text-[#64748B] space-y-1 text-center font-normal">
                    <li>Patterns</li>
                    <li>Formats</li>
                    <li>Clusters</li>
                  </ul>
                </div>

                <div className="flex flex-col items-center bg-[#FFFFFF] border border-[#E2E8F0] p-5 rounded-xl">
                  <span className="text-xs font-semibold text-[#E11D48] tracking-wider mb-2">RELATIONSHIPS</span>
                  <div className="w-full border-t border-[#E2E8F0] my-2"></div>
                  <ul className="text-xs text-[#64748B] space-y-1 text-center font-normal">
                    <li>Networks</li>
                    <li>Matching</li>
                    <li>Comparison</li>
                  </ul>
                </div>

                <div className="flex flex-col items-center bg-[#FFFFFF] border border-[#E2E8F0] p-5 rounded-xl">
                  <span className="text-xs font-semibold text-[#e09f43] tracking-wider mb-2">QUALITY</span>
                  <div className="w-full border-t border-[#E2E8F0] my-2"></div>
                  <ul className="text-xs text-[#64748B] space-y-1 text-center font-normal">
                    <li>Missingness</li>
                    <li>Cleaning</li>
                    <li>Constraints</li>
                  </ul>
                </div>
              </div>

              <div className="w-0.5 h-8 bg-[#E2E8F0] my-1"></div>
              <div className="px-6 py-2 rounded-lg bg-[#FFFFFF] border border-[#E2E8F0] text-[#1E293B] font-semibold text-xs tracking-wider">
                UNDERSTANDING
              </div>
              <div className="w-0.5 h-6 bg-[#E2E8F0] my-1"></div>
              <div className="px-5 py-1.5 rounded-lg bg-[#f5d7f0] border border-[#4B0F4D]/30 text-[#2B062B] text-xs font-medium">
                Reporting & Insights
              </div>
            </div>
          </div>

          {/* WHAT DOES SYNCLAIR LOOK FOR? */}
          <div className="pt-8">
            <h4 className="text-2xl font-semibold text-[#1E293B] text-center mb-10">
              What does SynClair look for?
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {[
                { title: "Data Structure", desc: "Data types, formats, cardinality, distributions, and dimensionality inspection." },
                { title: "Missingness", desc: "Missingness patterns, correlations, quality indicators, and systematic errors." },
                { title: "Relationships", desc: "Networks, associations, dependencies, and cross-record entity matching." },
                { title: "Patterns", desc: "Clusters, anomalies, subpopulations, and emergent structural traits." },
                { title: "Constraints", desc: "Structural rules, implicit dependencies, consistency rules, and violations." },
                { title: "Cross-dataset structure", desc: "Record linkage, schema comparison, distribution diffs, and alignment." },
              ].map((cat) => (
                <div key={cat.title} className="bg-[#FAF8F5] border border-[#E2E8F0] p-6 rounded-xl">
                  <h5 className="text-base font-semibold text-[#0284C7] mb-2">
                    {cat.title}
                  </h5>
                  <p className="text-xs text-[#64748B] leading-relaxed">
                    {cat.desc}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* 4. ANALYTICAL MODULES */}
      <section id="modules" className="py-24 px-6 border-t border-[#E2E8F0] bg-[#FAF8F5]">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-xs font-semibold uppercase tracking-widest text-[#0284C7] mb-2">
              Analytical Modules
            </h2>
            <h3 className="text-3xl sm:text-4xl font-semibold text-[#1E293B]">
              Explore your data from multiple perspectives
            </h3>
            <p className="text-sm text-[#64748B] mt-3 font-normal">
              Modular and composable analytical tools for deep dataset understanding.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              {
                id: "structure",
                title: "Data Structure",
                subtitle: "Understand how your dataset is built.",
                tags: ["data types", "formats", "cardinality", "distributions", "dimensionality"],
                path: "/modules/data-structure"
              },
              {
                id: "missingness",
                title: "Missingness & Quality",
                subtitle: "Understand missing data patterns, quality indicators and structural inconsistencies.",
                tags: ["missingness patterns", "correlations", "cleaning", "consistency checks"],
                path: "/modules/missingness"
              },
              {
                id: "patterns",
                title: "Pattern Discovery",
                subtitle: "Reveal hidden structures in your data.",
                tags: ["K-Means", "HDBSCAN", "GMM", "PCA", "UMAP", "anomaly detection"],
                path: "/modules/clustering-analytics"
              },
              {
                id: "networks",
                title: "Network Analysis",
                subtitle: "Explore relationships between entities.",
                tags: ["graph construction", "centrality", "communities", "network metrics"],
                path: "/modules/network-analysis"
              },
              {
                id: "constraints",
                title: "Constraint Discovery",
                subtitle: "Find rules your data appears to follow.",
                tags: ["structural constraints", "dependencies", "consistency rules"],
                path: "/modules/constraint-discovery"
              },
              {
                id: "matching",
                title: "Dataset Matching",
                subtitle: "Identify corresponding records across datasets.",
                tags: ["record linkage", "entity resolution", "similarity", "matching confidence"],
                path: "/modules/dataset-matching"
              },
              {
                id: "comparison",
                title: "Dataset Comparison",
                subtitle: "Understand how two datasets differ.",
                tags: ["schema comparison", "distribution comparison", "missingness"],
                path: "/modules/dataset-comparison"
              },
              {
                id: "reporting",
                title: "Reporting",
                subtitle: "Turn analysis into reproducible outputs.",
                tags: ["PDF", "CSV", "tables", "metrics", "visualizations"],
                path: "/modules/reporting"
              }
            ].map((mod) => (
              <div
                key={mod.id}
                onClick={() => navigateToModule(mod.path)}
                className="group bg-[#FFFFFF] border border-[#E2E8F0] hover:border-[#0284C7] p-6 rounded-xl flex flex-col justify-between cursor-pointer transition duration-200 hover:shadow-md"
              >
                <div>
                  <h4 className="text-lg font-semibold text-[#1E293B] mb-2 group-hover:text-[#0284C7] transition">
                    {mod.title}
                  </h4>
                  <p className="text-xs text-[#64748B] mb-4 leading-relaxed font-normal">
                    {mod.subtitle}
                  </p>
                  <div className="flex flex-wrap gap-1.5 mb-6">
                    {mod.tags.map((t) => (
                      <span key={t} className="text-[10px] bg-[#FAF8F5] text-[#64748B] px-2 py-0.5 rounded border border-[#E2E8F0] font-medium">
                        {t}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="text-xs font-semibold text-[#0284C7] flex items-center gap-1 group-hover:translate-x-1 transition">
                  Explore module →
                </div>
              </div>
            ))}
          </div>

          <div className="mt-12 text-center p-4 bg-[#FFFFFF] border border-[#E2E8F0] rounded-xl">
            <span className="text-xs text-[#64748B] font-medium">
              ⚡ More analytical modules coming: <span className="text-[#1E293B] font-semibold">Survival Analysis</span>, <span className="text-[#1E293B] font-semibold">Causal Inference</span>, and <span className="text-[#1E293B] font-semibold">Time Series Structures</span>.
            </span>
          </div>
        </div>
      </section>

      {/* 5. DEMO SECTION - Full Screen (min-h-screen) */}
      <section id="demo" className="min-h-screen flex flex-col items-center justify-center px-6 border-t border-[#E2E8F0] bg-[#FFFFFF] py-20">
        <div className="max-w-4xl w-full bg-gradient-to-br from-[#FEF3C7]/60 via-[#FFE4E6]/40 to-[#E0F2FE]/40 border border-[#0EA5E9]/30 p-12 sm:p-16 rounded-3xl text-center shadow-sm">
          <span className="text-xs font-bold uppercase tracking-widest text-[#0284C7] mb-3 inline-block">
            Interactive Playground
          </span>
          <h2 className="text-3xl sm:text-5xl font-semibold text-[#1E293B] mb-6">
            Try SynClair
          </h2>
          <p className="text-base sm:text-lg text-[#64748B] max-w-2xl mx-auto mb-10 leading-relaxed font-normal">
            Explore the platform with a preconfigured demo dataset. Test algorithms, missingness inspections, and interactive outputs without uploading your own data.
          </p>
          <button
            onClick={() => {
              sessionStorage.setItem("landing_last_section", "demo");
              navigate("/workspace/upload?mode=demo");
            }}
            className="bg-[#0284C7] hover:bg-[#0EA5E9] text-[#FFFFFF] font-semibold text-base px-10 py-4 rounded-xl transition duration-200 shadow-md"
          >
            Start Demo
          </button>
        </div>
      </section>

      {/* 6. WORKSPACE SECTION */}
      <section id="workspace" className="py-24 px-6 border-t border-[#E2E8F0] bg-[#FAF8F5] scroll-mt-16">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-10">
            <h2 className="text-xs font-semibold uppercase tracking-widest text-[#0284C7] mb-2">
              Private Workspace
            </h2>
            <h3 className="text-3xl sm:text-4xl font-semibold text-[#1E293B]">
              Analyze Your Own Data
            </h3>
          </div>

          {/* PARAGRAFO STRUTTURATO PER IL WORKSPACE */}
          <div className="mb-12 bg-[#FFFFFF] border border-[#E2E8F0] p-8 sm:p-10 rounded-2xl shadow-sm text-left">
            <h4 className="text-xl font-semibold text-[#1E293B] mb-4">
              An End-to-End Environment for Proprietary Datasets
            </h4>
            <p className="text-sm sm:text-base text-[#64748B] leading-relaxed mb-4 font-normal">
              The <strong className="text-[#1E293B] font-semibold">SynClair Workspace</strong> provides a secure, fully featured workspace designed to transform raw and heterogenous datasets into actionable structural intelligence. From initial ingestion to final report export, every step is built for reproducibility and statistical clarity.
            </p>
            <p className="text-sm sm:text-base text-[#64748B] leading-relaxed font-normal">
              Inside your workspace, you can upload complex relational files, configure tailored missingness diagnostics, discover implicit constraint rules, perform cross-dataset entity matching, and extract publishable analytics without leaving the browser environment.
            </p>
          </div>

          {/* LOGIN FORM */}
          <div id="workspace-login" className="max-w-md mx-auto bg-[#FFFFFF] border border-[#E2E8F0] p-8 sm:p-10 rounded-2xl shadow-sm">
            <h4 className="text-lg font-semibold text-[#1E293B] mb-6 text-center">
              Sign in to Workspace
            </h4>
            
            <form onSubmit={handleSubmit} className="space-y-4">
              {error && (
                <div className="p-3 text-xs text-red-600 bg-red-50 border border-red-200 rounded-lg">
                  {error}
                </div>
              )}
              
              <div>
                <label className="block text-xs font-semibold mb-1 text-[#64748B]">Username</label>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="w-full bg-[#FAF8F5] border border-[#E2E8F0] rounded-lg px-3 py-2 text-sm text-[#1E293B] focus:outline-none focus:border-[#0284C7]"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-semibold mb-1 text-[#64748B]">Password</label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full bg-[#FAF8F5] border border-[#E2E8F0] rounded-lg px-[#3] py-2 text-sm text-[#1E293B] focus:outline-none focus:border-[#0284C7]"
                  required
                />
              </div>

              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full bg-[#0284C7] hover:bg-[#0EA5E9] text-[#FFFFFF] font-semibold py-2.5 rounded-lg transition disabled:opacity-50 mt-2 shadow-sm"
              >
                {isSubmitting ? "Authenticating..." : "Open Workspace"}
              </button>
            </form>
          </div>
        </div>
      </section>

      {/* 7. FOOTER */}
      <footer className="bg-[#FFFFFF] border-t border-[#E2E8F0] py-8 px-6 text-center text-xs text-[#64748B]">
        <div className="mb-2 font-extrabold text-[#1E293B] text-sm">SynClair</div>
        <p>&copy; {new Date().getFullYear()} SynClair Analytics Environment. All rights reserved.</p>
      </footer>
    </div>
  );
}