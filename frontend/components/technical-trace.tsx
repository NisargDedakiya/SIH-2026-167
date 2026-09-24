"use client";

import React, { useState } from "react";
import { Terminal, ChevronDown, ChevronUp } from "lucide-react";

interface TraceEvent {
  sequence?: number;
  step?: number;
  event_type?: string;
  action?: string;
  status?: string;
  tool_name?: string | null;
  description?: string;
  duration_ms?: number | null;
  timestamp?: string | null;
}

interface TechnicalTraceProps {
  traceEvents?: TraceEvent[];
  traces?: TraceEvent[];
  agentRunId?: string | null;
}

export function TechnicalTrace({ traceEvents = [], traces = [], agentRunId }: TechnicalTraceProps) {
  const [open, setOpen] = useState(false);
  const activeEvents = traces.length > 0 ? traces : traceEvents;

  if (!activeEvents || activeEvents.length === 0) return null;

  return (
    <div className="rounded-xl bg-slate-900/60 border border-slate-800 overflow-hidden text-xs">
      <button
        onClick={() => setOpen(!open)}
        className="w-full p-3.5 flex items-center justify-between hover:bg-slate-800/40 transition text-left"
      >
        <div className="flex items-center space-x-2 text-slate-400 font-mono text-[11px]">
          <Terminal className="h-3.5 w-3.5 text-cyan-400" />
          <span>Observable Technical Trace ({traceEvents.length} events)</span>
          {agentRunId && <span className="text-slate-600 truncate max-w-xs">· ID: {agentRunId}</span>}
        </div>
        <div className="text-slate-500">
          {open ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </div>
      </button>

      {open && (
        <div className="p-3.5 pt-0 border-t border-slate-800/60 font-mono text-[11px] space-y-1.5 bg-slate-950/60">
          {traceEvents.map((t, idx) => (
            <div key={idx} className="flex items-center justify-between text-slate-400 py-0.5">
              <div className="flex items-center space-x-2 truncate pr-4">
                <span className="text-cyan-500">[{t.sequence}]</span>
                <span className="text-slate-200">{t.event_type}</span>
                {t.tool_name && <span className="text-teal-400">→ {t.tool_name}</span>}
              </div>
              <div className="flex items-center space-x-2 shrink-0">
                <span className="text-emerald-400">{t.status}</span>
                {t.duration_ms !== null && t.duration_ms !== undefined && (
                  <span className="text-slate-600">{t.duration_ms}ms</span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
