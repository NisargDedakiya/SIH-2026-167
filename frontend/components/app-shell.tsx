"use client";

import React, { useEffect, useState, useRef } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Satellite,
  Layers,
  GitCompare,
  Radio,
  BarChart2,
  History as HistoryIcon,
  FileText,
  Database,
  ChevronDown,
  Zap,
  Search,
  Bell,
  Settings,
  Menu,
  X,
  Sparkles,
  PlusCircle,
} from "lucide-react";

// ── Navigation items ──────────────────────────────────────────
const PRIMARY_NAV = [
  { href: "/",         label: "Home",       icon: Satellite },
  { href: "/analyze",  label: "Analyze",    icon: Sparkles,  highlight: true },
  { href: "/images",   label: "Images",     icon: Database },
  { href: "/history",  label: "History",    icon: HistoryIcon },
  { href: "/reports",  label: "Reports",    icon: FileText },
  { href: "/evaluation", label: "Eval",     icon: BarChart2 },
];

const WORKSPACE_NAV = [
  { href: "/temporal",    label: "Temporal",    icon: GitCompare },
  { href: "/cross-modal", label: "Optical+SAR", icon: Radio },
];

// ── Health Status Pill ────────────────────────────────────────
function HealthPill({ status }: { status: string }) {
  const map: Record<string, { color: string; label: string; dotClass: string }> = {
    CONNECTING: { color: "text-slate-400", label: "Connecting", dotClass: "bg-slate-500 animate-pulse" },
    ONLINE:     { color: "text-emerald-400", label: "Online",   dotClass: "bg-emerald-400 shadow-[0_0_6px_rgba(52,211,153,0.7)]" },
    DEGRADED:   { color: "text-amber-400",  label: "Degraded",  dotClass: "bg-amber-400 shadow-[0_0_6px_rgba(251,191,36,0.7)]" },
    OFFLINE:    { color: "text-rose-400",   label: "Offline",   dotClass: "bg-rose-500 shadow-[0_0_6px_rgba(239,68,68,0.7)]" },
  };
  const s = map[status] ?? map.CONNECTING;
  return (
    <div className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-md bg-[#0D1320] border border-[#1C2535] text-[10px] font-mono">
      <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${s.dotClass}`} />
      <span className={`hidden sm:inline ${s.color}`}>{s.label}</span>
    </div>
  );
}

// ── Logo ──────────────────────────────────────────────────────
function Logo() {
  return (
    <Link href="/" className="flex items-center gap-3 group flex-shrink-0" aria-label="SatQuery AI — Home">
      {/* Icon */}
      <div className="relative w-8 h-8 flex-shrink-0">
        <div className="absolute inset-0 rounded-lg bg-gradient-to-br from-cyan-500/20 to-teal-500/10 border border-cyan-700/40 group-hover:border-cyan-500/60 transition-colors" />
        <div className="absolute inset-0 flex items-center justify-center">
          <Satellite className="w-4 h-4 text-cyan-400" />
        </div>
      </div>
      {/* Wordmark */}
      <div className="flex flex-col leading-none">
        <span className="font-mono font-bold text-sm tracking-wider text-white">
          SAT<span className="text-cyan-400">QUERY</span>
          <span className="text-cyan-500 ml-1">AI</span>
        </span>
        <span className="text-[9px] text-[#687381] tracking-widest uppercase font-mono">
          Remote Sensing Intelligence
        </span>
      </div>
    </Link>
  );
}

// ── Nav Item ──────────────────────────────────────────────────
function NavItem({
  href,
  label,
  icon: Icon,
  highlight,
  isActive,
  onClick,
}: {
  href: string;
  label: string;
  icon: React.ElementType;
  highlight?: boolean;
  isActive: boolean;
  onClick?: () => void;
}) {
  if (highlight) {
    return (
      <Link
        href={href}
        onClick={onClick}
        className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-[11px] font-semibold bg-cyan-500/10 border border-cyan-600/30 text-cyan-400 hover:bg-cyan-500/15 hover:border-cyan-500/50 hover:text-cyan-300 transition-all"
      >
        <Icon className="w-3.5 h-3.5" />
        {label}
      </Link>
    );
  }

  return (
    <Link
      href={href}
      onClick={onClick}
      className={`
        relative flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-[11px] font-medium transition-all
        ${isActive
          ? "text-white bg-[#1C2535]"
          : "text-[#A7B0BD] hover:text-white hover:bg-[#151C26]"
        }
      `}
    >
      <Icon className={`w-3.5 h-3.5 ${isActive ? "text-cyan-400" : ""}`} />
      {label}
      {isActive && (
        <span className="absolute bottom-0 left-1/2 -translate-x-1/2 w-4 h-0.5 bg-cyan-500 rounded-full" />
      )}
    </Link>
  );
}

// ── Main App Shell ────────────────────────────────────────────
export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [healthStatus, setHealthStatus] = useState<"CONNECTING" | "ONLINE" | "DEGRADED" | "OFFLINE">("CONNECTING");
  const [mobileOpen, setMobileOpen] = useState(false);
  const mobileRef = useRef<HTMLDivElement>(null);

  // Health check
  useEffect(() => {
    let isMounted = true;
    async function evaluateHealth() {
      try {
        const healthRes = await fetch("/health");
        if (!healthRes.ok) { if (isMounted) setHealthStatus("OFFLINE"); return; }
        try {
          const readyRes = await fetch("/ready");
          if (isMounted) setHealthStatus(readyRes.ok ? "ONLINE" : "DEGRADED");
        } catch { if (isMounted) setHealthStatus("DEGRADED"); }
      } catch { if (isMounted) setHealthStatus("OFFLINE"); }
    }
    evaluateHealth();
    const iv = setInterval(evaluateHealth, 15000);
    return () => { isMounted = false; clearInterval(iv); };
  }, []);

  // Close mobile menu on route change
  useEffect(() => { setMobileOpen(false); }, [pathname]);

  // Close on outside click
  useEffect(() => {
    if (!mobileOpen) return;
    function handler(e: MouseEvent) {
      if (mobileRef.current && !mobileRef.current.contains(e.target as Node)) {
        setMobileOpen(false);
      }
    }
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [mobileOpen]);

  return (
    <div className="flex flex-col min-h-screen">
      {/* ── Header ── */}
      <header
        className="
          sticky top-0 z-50
          h-12
          bg-[rgba(11,15,22,0.90)]
          backdrop-blur-md
          border-b border-[#1C2535]
          flex items-center
        "
        role="banner"
      >
        <div className="max-w-[1400px] w-full mx-auto px-4 sm:px-6 flex items-center gap-4 h-full">

          {/* Logo */}
          <Logo />

          {/* Center nav — desktop */}
          <nav
            className="hidden lg:flex items-center gap-0.5 mx-auto"
            role="navigation"
            aria-label="Primary navigation"
          >
            {PRIMARY_NAV.map((item) => (
              <NavItem
                key={item.href}
                {...item}
                isActive={
                  item.href === "/"
                    ? pathname === "/"
                    : pathname.startsWith(item.href)
                }
              />
            ))}

            {/* Separator */}
            <span className="w-px h-4 bg-[#25303D] mx-1" />

            {/* Workspace shortcuts */}
            {WORKSPACE_NAV.map((item) => (
              <NavItem
                key={item.href}
                {...item}
                isActive={pathname.startsWith(item.href)}
              />
            ))}
          </nav>

          {/* Right side controls */}
          <div className="flex items-center gap-2 ml-auto lg:ml-0">
            <HealthPill status={healthStatus} />

            {/* Mobile menu toggle */}
            <button
              type="button"
              onClick={() => setMobileOpen(!mobileOpen)}
              className="lg:hidden w-8 h-8 flex items-center justify-center rounded-md text-[#A7B0BD] hover:text-white hover:bg-[#151C26] transition"
              aria-label={mobileOpen ? "Close navigation" : "Open navigation"}
              aria-expanded={mobileOpen}
              aria-controls="mobile-nav"
            >
              {mobileOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
            </button>
          </div>
        </div>
      </header>

      {/* ── Mobile Nav Drawer ── */}
      {mobileOpen && (
        <div
          id="mobile-nav"
          ref={mobileRef}
          className="
            lg:hidden fixed top-12 left-0 right-0 z-40
            bg-[#0B0F16] border-b border-[#1C2535]
            px-4 py-4
            sq-animate-in
          "
          role="navigation"
          aria-label="Mobile navigation"
        >
          <div className="grid grid-cols-3 gap-2">
            {[...PRIMARY_NAV, ...WORKSPACE_NAV].map((item) => {
              const Icon = item.icon;
              const isActive = item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`
                    flex flex-col items-center gap-1.5 py-3 px-2 rounded-lg text-center
                    text-[10px] font-medium transition
                    ${isActive
                      ? "bg-[#151C26] text-cyan-400 border border-[#25303D]"
                      : "text-[#A7B0BD] hover:bg-[#111821] hover:text-white border border-transparent"
                    }
                  `}
                >
                  <Icon className="w-4 h-4" />
                  {item.label}
                </Link>
              );
            })}
          </div>
        </div>
      )}

      {/* ── Main Content ── */}
      <main
        className="flex-1 max-w-[1400px] w-full mx-auto px-4 sm:px-6 py-6"
        role="main"
      >
        {children}
      </main>

      {/* ── Footer ── */}
      <footer
        className="border-t border-[#1C2535] py-4 text-[11px] text-[#49576A]"
        role="contentinfo"
      >
        <div className="max-w-[1400px] mx-auto px-4 sm:px-6 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span className="font-mono">
            SatQuery AI · ISRO SIH Problem Statement 26167 · Department of Space
          </span>
          <div className="flex items-center gap-4 font-mono">
            <a
              href="/docs"
              target="_blank"
              rel="noreferrer"
              className="hover:text-[#A7B0BD] transition"
            >
              API Docs
            </a>
            <span className="text-[#1C2535]">·</span>
            <span>Geospatial Intelligence Platform</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
