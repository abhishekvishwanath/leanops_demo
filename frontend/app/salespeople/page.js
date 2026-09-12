"use client";

import { useEffect, useState } from "react";
import { api } from "../../lib/api";
import { LoadingState, ErrorState } from "../../components/DataState";

export default function SalespeoplePage() {
  const [salespeople, setSalespeople] = useState(null);
  const [error, setError] = useState(null);

  const load = () => {
    setError(null);
    api.get("/salespeople").then(setSalespeople).catch(setError);
  };

  useEffect(load, []);

  if (error) return <ErrorState error={error} onRetry={load} />;
  if (!salespeople) return <LoadingState />;

  return (
    <div>
      <h1 className="text-xl font-semibold text-slate-900 mb-1">Salesperson Board</h1>
      <p className="text-sm text-slate-500 mb-4">
        Active lead count excludes Dead/Nurture leads, matching how the assignment engine balances workload.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {salespeople.map((s) => (
          <div key={s.salesperson_id} className="bg-white rounded-lg border border-slate-200 p-4">
            <div className="flex items-center justify-between mb-2">
              <div>
                <div className="font-semibold text-slate-900">{s.name}</div>
                <div className="text-xs text-slate-400">{s.salesperson_id} · {s.role === "floating_specialist" ? "Floating language specialist" : "Project owner"}</div>
              </div>
              <span className={`text-xs rounded-full px-2 py-0.5 font-medium ${s.active ? "bg-green-100 text-green-800" : "bg-slate-200 text-slate-600"}`}>
                {s.active ? "Active" : "Inactive"}
              </span>
            </div>
            <div className="text-sm text-slate-600 mb-2">{s.territory}</div>
            <div className="flex flex-wrap gap-1 mb-3">
              {s.languages.map((lang) => (
                <span key={lang} className="text-xs bg-slate-100 text-slate-600 rounded px-1.5 py-0.5">{lang}</span>
              ))}
            </div>
            <div className="flex justify-between items-center text-sm">
              <div>
                {s.projects.length > 0 ? (
                  <span className="text-slate-600">{s.projects.join(", ")}</span>
                ) : (
                  <span className="text-slate-400">No exclusive project ownership</span>
                )}
              </div>
              <div className="text-right">
                <div className="font-semibold text-slate-900">{s.active_lead_count}</div>
                <div className="text-xs text-slate-400">active leads</div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
