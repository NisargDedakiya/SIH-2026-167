"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  Satellite,
  Layers,
  ExternalLink,
  GitCompare,
  Radio,
  BarChart2,
  Sparkles,
  History as HistoryIcon,
  FileText,
  PlusCircle,
  Database,
} from "lucide-react";

export function AppShell({ children }: { children: React.ReactNode }) {
  const [healthStatus, setHealthStatus] = useState<
    "CONNECTING" | "ONLINE" | "DEGRADED" | "OFFLINE"
  >("CONNECTING");

  useEffect(() => {
    let isMounted = true;

    async function evaluateHealth() {
      try {
        const healthRes = await fetch("/health");
        if (!healthRes.ok) {
          if (isMounted) setHealthStatus("OFFLINE");
          return;
        }

        // Liveness succeeded (200). Now probe deep readiness.
        try {
          const readyRes = await fetch("/ready");
          if (isMounted) {
            if (readyRes.ok) {
              setHealthStatus("ONLINE");
            } else {
              setHealthStatus("DEGRADED");
            }
          }
        } catch (_) {
          if (isMounted) setHealthStatus("DEGRADED");
        }
      } catch (_) {
        if (isMounted) setHealthStatus("OFFLINE");
      }
    }

    evaluateHealth();
    const interval = setInterval(evaluateHealth, 15000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  return (
    <div className="flex flex-col min-h-screen">
      {/* Top Banner */}
      <header className="border-b border-slate-800/80 bg-surface/80 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Link href="/" className="flex items-center space-x-3 group">
              <div className="h-10 w-10 rounded-lg bg-gradient-to-tr from-cyan-600 to-teal-400 p-0.5 shadow-lg shadow-cyan-500/20 group-hover:scale-105 transition-transform">
                <div className="h-full w-full bg-slate-950 rounded-[7px] flex items-center justify-center">
                  <Satellite className="h-5 w-5 text-cyan-400" />
                </div>
              </div>
              <div>
                <div className="flex items-center space-x-2">
                  <span className="font-bold tracking-wider text-base sm:text-lg text-white font-mono">
                    SATQUERY <span className="text-cyan-400">AI</span>
                  </span>
                  <span className="hidden sm:inline-block px-2 py-0.5 text-[10px] font-semibold tracking-wider uppercase rounded bg-cyan-950/80 text-cyan-300 border border-cyan-700/50">
                    SIH Hardened · Production
                  </span>
                </div>
                <p className="text-[11px] text-slate-400 tracking-tight">
                  Multimodal Remote-Sensing Intelligence Platform
                </p>
              </div>
            </Link>
          </div>

          <nav className="flex items-center space-x-1 sm:space-x-2">
            <Link
              href="/"
              className="px-2.5 py-1.5 rounded-md text-xs font-medium text-slate-300 hover:text-white hover:bg-slate-800/60 transition"
            >
              Dashboard
            </Link>
            <Link
              href="/demo"
              className="px-2.5 py-1.5 rounded-md text-xs font-bold text-amber-300 hover:text-amber-200 bg-amber-950/40 border border-amber-500/40 hover:bg-amber-900/50 transition flex items-center space-x-1 shadow-sm shadow-amber-950"
            >
              <Sparkles className="h-3.5 w-3.5 text-amber-400" />
              <span>Demo Hub</span>
            </Link>
            <Link
              href="/analyze"
              className="px-2.5 py-1.5 rounded-md text-xs font-medium text-cyan-400 hover:text-cyan-300 hover:bg-cyan-950/50 border border-cyan-800/50 transition flex items-center space-x-1 shadow-sm shadow-cyan-950"
            >
              <PlusCircle className="h-3.5 w-3.5" />
              <span>New Analysis</span>
            </Link>
            <Link
              href="/history"
              className="px-2.5 py-1.5 rounded-md text-xs font-medium text-slate-300 hover:text-white hover:bg-slate-800/60 transition flex items-center space-x-1"
            >
              <HistoryIcon className="h-3.5 w-3.5" />
              <span>History</span>
            </Link>
            <Link
              href="/images"
              className="px-2.5 py-1.5 rounded-md text-xs font-medium text-slate-300 hover:text-white hover:bg-slate-800/60 transition flex items-center space-x-1"
            >
              <Database className="h-3.5 w-3.5" />
              <span>Images</span>
            </Link>
            <Link
              href="/reports"
              className="px-2.5 py-1.5 rounded-md text-xs font-medium text-slate-300 hover:text-white hover:bg-slate-800/60 transition flex items-center space-x-1"
            >
              <FileText className="h-3.5 w-3.5" />
              <span>Reports</span>
            </Link>
            <Link
              href="/evaluation"
              className="px-2.5 py-1.5 rounded-md text-xs font-medium text-slate-300 hover:text-white hover:bg-slate-800/60 transition flex items-center space-x-1"
            >
              <BarChart2 className="h-3.5 w-3.5" />
              <span>Evaluation</span>
            </Link>

            {/* Health pill */}
            <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-slate-900 border border-slate-800 text-[11px] text-slate-400">
              <span
                className={`h-2 w-2 rounded-full ${
                  healthStatus === "CONNECTING"
                    ? "bg-slate-500 animate-pulse"
                    : healthStatus === "ONLINE"
                    ? "bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.6)]"
                    : healthStatus === "DEGRADED"
                    ? "bg-amber-400 shadow-[0_0_8px_rgba(251,191,36,0.6)]"
                    : "bg-rose-500"
                }`}
              />
              <span className="hidden md:inline font-mono text-[10px]">
                {healthStatus === "CONNECTING"
                  ? "Connecting"
                  : healthStatus === "ONLINE"
                  ? "Online"
                  : healthStatus === "DEGRADED"
                  ? "Degraded"
                  : "Offline"}
              </span>
            </div>
          </nav>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/60 bg-slate-950/40 py-6 text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row justify-between items-center space-y-2 sm:space-y-0">
          <div>
            ISRO Smart India Hackathon Problem Statement 26167 · Department of Space
          </div>
          <div className="flex items-center space-x-4">
            <a
              href="/docs"
              target="_blank"
              rel="noreferrer"
              className="hover:text-cyan-400 transition flex items-center space-x-1"
            >
              <span>API Docs</span>
              <ExternalLink className="h-3 w-3" />
            </a>
            <span>Foundation & Ingestion Layer</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
