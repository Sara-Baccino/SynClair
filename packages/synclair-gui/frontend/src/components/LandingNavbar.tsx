import { useState } from "react";

export function LandingNavbar({ onLoginClick }: { onLoginClick: () => void }) {
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const modules = [
    { name: "Structure", desc: "Clustering, PCA, Embedding & Profiling", status: "Available" },
    { name: "Matching", desc: "Record Linkage & Entity Alignment", status: "In Dev" },
    { name: "Validation", desc: "Cluster Quality & Hypothesis Testing", status: "In Dev" },
    { name: "Discovery", desc: "Subgroup & Pattern Discovery", status: "In Dev" },
    { name: "Reporting", desc: "Automated Synthetic Reports (PDF)", status: "Available" },
  ];

  return (
    <nav className="sticky top-0 z-50 border-b border-amber-200/40 bg-amber-50/80 backdrop-blur-md">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
        {/* Logo SynClair */}
        <a href="#" className="flex items-center gap-2 text-xl font-black tracking-tight text-slate-900">
          <span className="h-3 w-3 rounded-full bg-fuchsia-500 shadow-sm shadow-fuchsia-500/50" />
          SynClair
        </a>

        {/* Desktop Links */}
        <div className="hidden items-center gap-8 md:flex text-sm font-medium text-slate-700">
          <a href="#overview" className="hover:text-fuchsia-600 transition-colors">Overview</a>
          
          {/* Modules Dropdown */}
          <div 
            className="relative"
            onMouseEnter={() => setIsDropdownOpen(true)}
            onMouseLeave={() => setIsDropdownOpen(false)}
          >
            <button className="flex items-center gap-1 hover:text-fuchsia-600 transition-colors py-1">
              Modules
              <svg className="h-4 w-4 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>

            {isDropdownOpen && (
              <div className="absolute left-0 top-full w-72 rounded-xl border border-amber-200/60 bg-white/95 p-2 shadow-xl backdrop-blur-lg">
                {modules.map((m) => (
                  <div key={m.name} className="flex items-start justify-between rounded-lg p-2.5 hover:bg-rose-50/50 transition-colors">
                    <div>
                      <div className="font-semibold text-slate-900 text-xs">{m.name}</div>
                      <div className="text-[11px] text-slate-500">{m.desc}</div>
                    </div>
                    <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded ${
                      m.status === "Available" 
                        ? "bg-indigo-50 text-indigo-600 border border-indigo-200" 
                        : "bg-slate-100 text-slate-400"
                    }`}>
                      {m.status}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

          <a href="#workflow" className="hover:text-fuchsia-600 transition-colors">Workflow</a>
          <a href="#demo" className="hover:text-fuchsia-600 transition-colors">Demo</a>
        </div>

        {/* CTA Login Button */}
        <div className="hidden md:block">
          <button
            onClick={onLoginClick}
            className="rounded-full bg-slate-900 px-5 py-2 text-xs font-semibold text-white shadow-md hover:bg-slate-800 transition-all"
          >
            Enter Workspace
          </button>
        </div>

        {/* Mobile Hamburger Toggle */}
        <button 
          onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
          className="md:hidden text-slate-800"
        >
          <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
      </div>

      {/* Mobile Menu */}
      {isMobileMenuOpen && (
        <div className="border-t border-amber-200/40 bg-amber-50 px-6 py-4 md:hidden space-y-3 text-sm">
          <a href="#overview" onClick={() => setIsMobileMenuOpen(false)} className="block font-medium text-slate-700">Overview</a>
          <a href="#workflow" onClick={() => setIsMobileMenuOpen(false)} className="block font-medium text-slate-700">Workflow</a>
          <a href="#demo" onClick={() => setIsMobileMenuOpen(false)} className="block font-medium text-slate-700">Demo</a>
          <button
            onClick={() => { setIsMobileMenuOpen(false); onLoginClick(); }}
            className="w-full rounded-lg bg-slate-900 py-2.5 text-center text-xs font-semibold text-white"
          >
            Enter Workspace
          </button>
        </div>
      )}
    </nav>
  );
}