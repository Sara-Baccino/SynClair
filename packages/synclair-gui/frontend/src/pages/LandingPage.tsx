import { useState, type FormEvent, useEffect } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";
import { ApiError } from "../api/client";
import { useAuth } from "../context/AuthContext";
import { GradientLogo } from "../components/branding/GradientLogo";
import { AppBackground } from "../components/branding/AppBackground";
//import { GRADIENT_BUTTON } from "../constants/brandStyles";

interface LocationState {
  from?: { pathname: string };
}

export function LandingPage() {
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
    return <div className="min-h-screen bg-slate-50" />;
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
    <div className="relative min-h-screen w-full text-slate-800 font-['Manrope',sans-serif] selection:bg-pink-200 selection:text-blue-700">
      {/* Import dei font e stili per l'animazione della Data Wave */}
      <link
        rel="stylesheet"
        href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap"
      />
      <style>{`
        @keyframes waveMotionSlow {
          0% { transform: translateY(0px) scaleY(1); }
          50% { transform: translateY(-15px) scaleY(1.03); }
          100% { transform: translateY(0px) scaleY(1); }
        }
        @keyframes pulseNode {
          0%, 100% { opacity: 0.5; transform: scale(1); }
          50% { opacity: 1; transform: scale(1.4); }
        }
        .animate-wave-slow {
          animation: waveMotionSlow 18s ease-in-out infinite;
        }
        .animate-pulse-slow {
          animation: pulseNode 4s ease-in-out infinite;
          transform-origin: center;
        }
      `}</style>

      {/* BACKGROUND FISSO: Gradiente Blu -> Rosa e Data Wave SVG */}
      <AppBackground />

      {/* CONTENUTI DELLA PAGINA (In primo piano rispetto allo sfondo) */}
      <div className="relative z-10 flex flex-col items-center w-full">
        {/* 1. NAVBAR (Effetto Vetro) */}
        <nav className="fixed top-0 left-0 right-0 z-50 bg-white/60 backdrop-blur-md border-b border-white/40 px-6 sm:px-10 py-4 flex items-center justify-between shadow-sm">
          <div className="flex items-center gap-8">
            <GradientLogo onClick={() => scrollToSection("hero")} />

            <div className="hidden md:flex items-center gap-6 text-sm font-medium text-slate-600">
              <button onClick={() => scrollToSection("overview")} className="hover:text-slate-900 transition">Overview</button>
              <button onClick={() => scrollToSection("modules")} className="hover:text-slate-900 transition">Modules</button>
              <button onClick={() => scrollToSection("demo")} className="hover:text-slate-900 transition">Demo</button>
              <button onClick={() => scrollToSection("workspace")} className="hover:text-slate-900 transition">Workspace</button>
            </div>
          </div>

          <div>
            <button
              onClick={() => navigate("/login")}
              className="text-xs font-semibold px-4 py-2.5 rounded-lg bg-gradient-to-r from-purple-600 via-pink-600 to-amber-400 text-white shadow-md hover:opacity-90 hover:shadow-lg transition duration-200"
            >
              Access Workspace
            </button>
          </div>
        </nav>

        {/* 2. HERO SECTION */}
        <section id="hero" className="pt-36 pb-24 px-6 text-center max-w-6xl mx-auto flex flex-col items-center justify-center min-h-[90vh]">
          <div className="max-w-4xl mx-auto flex flex-col items-center">
            <h1 className="text-6xl sm:text-7xl lg:text-8xl font-extrabold tracking-tight mb-6 select-none bg-gradient-to-r from-purple-600 via-pink-600 to-amber-400 bg-clip-text text-transparent">
              SynClair
            </h1>

            <h3 className="text-xl sm:text-4xl font-semibold text-slate-800 mb-8 leading-tight">
              Transform complex data into clear decisions.<br />

            </h3>
            <p className="text-base sm:text-lg text-slate-600 font-normal max-w-2xl leading-relaxed mb-10">
              Analyze the structure, quality, and relationships of your data in a single platform. <br/>
              No coding, no complex configurations.
            </p>

            <div className="flex flex-col sm:flex-row items-center gap-4 mb-16">
              <button
                onClick={() => scrollToSection("overview")}
                className="bg-white/80 backdrop-blur-sm border border-white/60 hover:bg-white text-slate-800 font-semibold px-8 py-3.5 rounded-xl transition duration-200 shadow-sm hover:shadow"
              >
                Learn How It Works ↓
              </button>
              <button
                onClick={() => scrollToSection("demo")}
                className="bg-gradient-to-r from-purple-600 via-pink-600 to-amber-400 hover:opacity-90 text-white font-semibold px-8 py-3.5 rounded-xl shadow-md transition duration-200 hover:shadow-lg hover:scale-[1.02]">
                Try the Free Demo
              </button>
            </div>

            <div className="flex flex-wrap items-center justify-center gap-3 text-xs font-semibold text-slate-600 uppercase tracking-wider">
              <span className="px-3 py-1 rounded-full bg-white/70 backdrop-blur-sm text-blue-600 border border-white/50">Analyze</span>
              <span>·</span>
              <span className="px-3 py-1 rounded-full bg-white/70 backdrop-blur-sm text-purple-600 border border-white/50">Compare</span>
              <span>·</span>
              <span className="px-3 py-1 rounded-full bg-white/70 backdrop-blur-sm text-pink-600 border border-white/50">Validate</span>
              <span>·</span>
              <span className="px-3 py-1 rounded-full bg-white/70 backdrop-blur-sm text-yellow-600 border border-white/50">Understand</span>
            </div>
          </div>
        </section>

        {/* 3. OVERVIEW SECTION */}
        <section id="overview" className="w-full py-24 px-6 border-t border-white/40 bg-white/40 backdrop-blur-md">
          <div className="max-w-5xl mx-auto">
            <div className="text-center max-w-3xl mx-auto mb-16">
              <h2 className="text-xs font-semibold uppercase tracking-widest bg-gradient-to-r from-purple-600 to-amber-400 bg-clip-text text-transparent mb-6">
                Overview
              </h2>

              <h3 className="text-3xl sm:text-4xl font-semibold text-slate-800 mb-6">
                What is SynClair?
              </h3>

              <p className="text-lg sm:text-xl text-slate-800 font-semibold leading-relaxed mb-8">
                <span className="bg-gradient-to-r from-purple-600 to-amber-500 bg-clip-text text-transparent">
                  A modular environment for interactive data analysis.
                </span>
              </p>

              <p className="text-base sm:text-lg text-slate-600 font-normal leading-relaxed mb-10">
                
                SynClair brings datasets, analytical tools, and results into a single unified workspace. <br/>
                Chain outputs into new modules, compare results side-by-side, and iterate seamlessly without ever starting from scratch.
                
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 mb-24">
                {[
                  { title: "Explore and Clean", desc: "Inspect distributions, detect missingness, and analyze dataset structure." },
                  { title: "Connect and Group", desc: "Discover hidden clusters, match datasets, and map complex network relationships." },
                  { title: "Synthesize & Report", desc: "Consolidate analytical results into clear metrics, visual summaries, and reports." },
                ].map((cat) => (
                  <div key={cat.title} className="bg-white/70 backdrop-blur-md border border-white/50 p-6 rounded-xl shadow-sm">
                    <h5 className="text-2xl font-semibold bg-gradient-to-r from-purple-600 to-pink-400 bg-clip-text text-transparent mb-2">
                      {cat.title}
                    </h5>
                    <p className="text-xs text-slate-600 leading-relaxed">
                      {cat.desc}
                    </p>
                  </div>
                ))}
              </div>

            <div className="text-center max-w-3xl mx-auto mb-12">
            
            <h4 className="text-xs font-semibold uppercase tracking-widest bg-gradient-to-r from-purple-600 to-amber-400 bg-clip-text text-transparent mb-6">
                Workflow
            </h4>

            <h3 className="text-3xl sm:text-4xl font-semibold text-slate-800 mb-6">
                How SynClair works
            </h3>

              <p className="text-base sm:text-lg text-slate-600 font-semibold leading-relaxed mb-4">
                Combine specialized modules across three core dimensions: <br/>
                <strong className="text-purple-600 font-semibold">Data Quality</strong>, <strong className="text-pink-600 font-semibold">Structure</strong> and <strong className="text-amber-500 font-semibold">Relationships</strong>.
              </p>

              <p className="text-base sm:text-lg text-slate-600 font-normal leading-relaxed mb-6">
                Connect tools in any order, refine parameters on the fly, and make complex datasets{" "}
                <span className="bg-gradient-to-r from-purple-600 to-amber-400 bg-clip-text text-transparent font-semibold">visible</span>,{" "}
                <span className="bg-gradient-to-r from-purple-600 to-amber-400 bg-clip-text text-transparent font-semibold">measurable</span> and{" "}
                <span className="bg-gradient-to-r from-purple-600 to-amber-400 bg-clip-text text-transparent font-semibold">interpretable</span>.
              </p>

            </div>

            <div className="my-16 p-8 bg-grey/70 backdrop-blur-md border border-white/50 rounded-2xl shadow-sm">
              <h4 className="text-xs font-semibold uppercase tracking-widest text-slate-500 text-center mb-8">
                A Modular Approach to Data Understanding
              </h4>
              <div className="flex flex-col items-center">
                <span className="bg-gradient-to-r from-purple-600 via-pink-600 to-amber-400 bg-clip-text text-transparent font-extrabold text-sm">
                  SynClair
                </span>
                <div className="w-0.5 h-8 bg-slate-300 my-1"></div>

                

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full max-w-4xl">
                  <div className="flex flex-col items-center bg-white/80 border border-white/60 p-5 rounded-xl shadow-xs">
                    <span className="text-xs font-semibold text-purple-600 tracking-wider mb-2">QUALITY</span>
                    <div className="w-full border-t border-slate-200 my-2"></div>
                    <ul className="text-xs text-slate-600 space-y-1 text-center font-normal">
                      <li>Missingness</li>
                      <li>Cleaning</li>
                      <li>Constraints</li>
                    </ul>
                  </div>
                  <div className="flex flex-col items-center bg-white/80 border border-white/60 p-5 rounded-xl shadow-xs">
                    <span className="text-xs font-semibold text-pink-600 tracking-wider mb-2">STRUCTURE</span>
                    <div className="w-full border-t border-slate-200 my-2"></div>
                    <ul className="text-xs text-slate-600 space-y-1 text-center font-normal">
                      <li>Patterns</li>
                      <li>Formats</li>
                      <li>Clusters</li>
                    </ul>
                  </div>
                  <div className="flex flex-col items-center bg-white/80 border border-white/60 p-5 rounded-xl shadow-xs">
                    <span className="text-xs font-semibold text-yellow-600 tracking-wider mb-2">RELATIONSHIPS</span>
                    <div className="w-full border-t border-slate-200 my-2"></div>
                    <ul className="text-xs text-slate-600 space-y-1 text-center font-normal">
                      <li>Networks</li>
                      <li>Matching</li>
                      <li>Comparison</li>
                    </ul>
                  </div>
                </div>

                <div className="w-0.5 h-8 bg-slate-300 my-1"></div>
                <div className="px-6 py-2 rounded-lg bg-white border border-white/60 text-slate-800 font-semibold text-xs tracking-wider shadow-xs">
                  UNDERSTANDING
                </div>
                <div className="w-0.5 h-6 bg-slate-300 my-1"></div>
                <div className="px-5 py-1.5 rounded-lg bg-white/80 border border-white/60 text-blue-600 text-xs font-medium shadow-xs">
                  Reporting & Insights
                </div>
              </div>
            </div>
            </div>
          </div>
        </section>

        {/* 4. ANALYTICAL MODULES */}
        <section id="modules" className="w-full py-24 px-6 border-t border-white/40 bg-white/30 backdrop-blur-sm">
          <div className="max-w-6xl mx-auto">
            <div className="text-center mb-16">
              <h4 className="text-xs font-semibold uppercase tracking-widest bg-gradient-to-r from-purple-600 to-amber-400 bg-clip-text text-transparent mb-6">
                Modules
              </h4>
              <h3 className="text-3xl sm:text-4xl font-semibold text-slate-800 mb-10">
                Explore Your Data from Every Perspective
              </h3>
              <p className="text-lg sm:text-xl text-slate-800 font-semibold leading-relaxed mb-6">
                <span className="bg-gradient-to-r from-purple-600 to-amber-500 bg-clip-text text-transparent">
                  One workspace. Many analytical paths.
                </span>
              </p>
              <p className="text-base sm:text-lg text-slate-600 font-normal leading-relaxed mb-10">
                Modular and composable analytical tools for deep dataset understanding. <br/> 
                Select a module below to inspect its functionalities.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {[
                {
                  id: "structure", title: "Data Structure", subtitle: "Understand how your dataset is built.", tags: ["data types", "formats", "cardinality", "distributions", "dimensionality"], path: "/modules/data-structure"
                },
                {
                  id: "missingness", title: "Missingness & Quality", subtitle: "Understand missing data patterns, quality indicators and structural inconsistencies.", tags: ["missingness patterns", "correlations", "cleaning", "consistency checks"], path: "/modules/missingness"
                },
                {
                  id: "patterns", title: "Pattern Discovery", subtitle: "Reveal hidden structures in your data.", tags: ["K-Means", "HDBSCAN", "GMM", "PCA", "UMAP", "anomaly detection"], path: "/modules/clustering-analytics"
                },
                {
                  id: "networks", title: "Network Analysis", subtitle: "Explore relationships between entities.", tags: ["graph construction", "centrality", "communities", "network metrics"], path: "/modules/network-analysis"
                },
                {
                  id: "constraints", title: "Constraint Discovery", subtitle: "Find rules your data appears to follow.", tags: ["structural constraints", "dependencies", "consistency rules"], path: "/modules/constraint-discovery"
                },
                {
                  id: "matching", title: "Dataset Matching", subtitle: "Identify corresponding records across datasets.", tags: ["record linkage", "entity resolution", "similarity", "matching confidence"], path: "/modules/dataset-matching"
                },
                {
                  id: "comparison", title: "Dataset Comparison", subtitle: "Understand how two datasets differ.", tags: ["schema comparison", "distribution comparison", "missingness"], path: "/modules/dataset-comparison"
                },
                {
                  id: "reporting", title: "Reporting", subtitle: "Turn analysis into reproducible outputs.", tags: ["PDF", "CSV", "tables", "metrics", "visualizations"], path: "/modules/reporting"
                }
              ].map((mod) => (
                <div
                  key={mod.id}
                  onClick={() => navigateToModule(mod.path)}
                  className="group bg-white/70 backdrop-blur-md border border-white/50 hover:border-purple-400 p-6 rounded-xl flex flex-col justify-between cursor-pointer transition duration-200 shadow-sm hover:shadow-md hover:scale-[1.01]"
                >
                  <div>
                    <h4 className="text-lg font-semibold text-slate-800 mb-2 group-hover:text-amber-600 transition">
                      {mod.title}
                    </h4>
                    <p className="text-xs text-slate-600 mb-4 leading-relaxed font-normal">
                      {mod.subtitle}
                    </p>
                    <div className="flex flex-wrap gap-1.5 mb-6">
                      {mod.tags.map((t) => (
                        <span key={t} className="text-[10px] bg-white/80 text-slate-600 px-2 py-0.5 rounded border border-white/60 font-medium">
                          {t}
                        </span>
                      ))}
                    </div>
                  </div>
                  <div className="text-xs font-semibold bg-gradient-to-r from-purple-600 via-pink-500 to-amber-500 bg-clip-text text-transparent flex items-center gap-1 group-hover:translate-x-1 transition">
                    Explore module →
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* 5. DEMO SECTION */}
        <section id="demo" className="w-full min-h-screen flex flex-col items-center justify-center px-6 border-t border-white/40 bg-white/40 backdrop-blur-md py-20">
          <div className="max-w-4xl w-full bg-white/60 backdrop-blur-xl border border-white/80 shadow-[0_8px_32px_rgba(37,99,235,0.05)] p-12 sm:p-16 rounded-3xl text-center">
            <span className="text-xs font-bold uppercase tracking-widest bg-gradient-to-r from-purple-600 to-amber-400 bg-clip-text text-transparent mb-3 inline-block mb-8">
              Interactive Playground
            </span>
            <h2 className="text-3xl sm:text-5xl font-semibold text-slate-800 mb-8">
              Try SynClair in 2 Minutes
            </h2>
            <p className="text-base sm:text-lg text-slate-600 max-w-2xl mx-auto mb-10 leading-relaxed font-normal">
              Explore the platform with a preconfigured demo dataset. Test algorithms, missingness inspections, and interactive outputs without uploading your own data.
            </p>
            <button
              onClick={() => {
                sessionStorage.setItem("landing_last_section", "demo");
                navigate("/demo");
              }}
              className="bg-gradient-to-r from-purple-600 via-pink-600 to-amber-400 hover:opacity-90 text-white font-semibold text-base px-10 py-4 rounded-xl transition duration-200 shadow-md hover:shadow-lg hover:scale-[1.02]"
            >
              Start Demo
            </button>
          </div>
        </section>

        {/* 6. WORKSPACE SECTION WITH LOGIN */}
        <section id="workspace" className="w-full py-24 px-6 border-t border-white/40 bg-white/30 backdrop-blur-sm scroll-mt-16">
          <div className="max-w-4xl mx-auto">
            <div className="text-center mb-10">
              <h2 className="text-xs font-semibold uppercase tracking-widest bg-gradient-to-r from-purple-600 to-amber-400 bg-clip-text text-transparent mb-6">
                Private Workspace
              </h2>
              <h3 className="text-3xl sm:text-4xl font-semibold text-slate-800">
                Ready to Analyze Your Own Data?
              </h3>
            </div>

            <div className="mb-12 bg-white/70 backdrop-blur-md border border-white/50 p-8 sm:p-10 rounded-2xl shadow-sm text-left">
              <h4 className="text-xl font-semibold text-slate-800 mb-4">
                Analyze datasets, save, export and reuse your workflows with one click.
              </h4>
              <p className="text-sm sm:text-base text-slate-600 leading-relaxed mb-4 font-normal">
                The <strong className="text-slate-800 font-semibold">SynClair Workspace</strong> provides a workspace designed to transform raw and heterogenous datasets into actionable structural intelligence. 
                From initial ingestion to final report export, every step is built for reproducibility and statistical clarity. <br/> <br/>
                Don't have an account? Register here: link.
              </p>
            </div>

            {/* LOGIN FORM */}
            <div id="workspace-login" className="max-w-md mx-auto bg-white/80 backdrop-blur-lg border border-white/60 p-8 sm:p-10 rounded-2xl shadow-md">
              <h4 className="text-xl font-bold bg-gradient-to-r from-purple-600 via-pink-600 to-amber-400 bg-clip-text text-transparent mb-6 text-center">
                Sign in to Workspace
              </h4>
              
              <form onSubmit={handleSubmit} className="space-y-4">
                {error && (
                  <div className="p-3 text-xs text-red-600 bg-red-50/80 border border-red-200 rounded-lg">
                    {error}
                  </div>
                )}
                
                <div>
                  <label className="block text-xs font-semibold mb-1 text-slate-600">Username</label>
                  <input
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    className="w-full bg-white/90 border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500"
                    required
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold mb-1 text-slate-600">Password</label>
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full bg-white/90 border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500"
                    required
                  />
                </div>

                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="w-full bg-gradient-to-r from-purple-600 via-pink-600 to-amber-400 hover:opacity-90 text-white font-semibold py-2.5 rounded-lg transition disabled:opacity-50 mt-2 shadow-md hover:shadow-lg"
                >
                  {isSubmitting ? "Authenticating..." : "Open Workspace"}
                </button>
              </form>
            </div>
          </div>
        </section>

        {/* 7. FOOTER */}
        <footer className="w-full bg-white/70 backdrop-blur-md border-t border-white/40 py-8 px-6 text-center text-xs text-slate-600">
          <div className="mb-2 font-extrabold text-sm bg-gradient-to-r from-purple-600 to-amber-400 bg-clip-text text-transparent">
            SynClair
          </div>
          <p>&copy; {new Date().getFullYear()} SynClair Analytics Environment. All rights reserved.</p>
        </footer>
      </div>
    </div>
  );
}