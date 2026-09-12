"use client";

import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { LoadingState, ErrorState } from "../components/DataState";

const STAGES = [
  { key: "new", label: "New", color: "bg-blue-50 text-blue-900 border-blue-200" },
  { key: "review_queue", label: "Review Queue", color: "bg-orange-50 text-orange-900 border-orange-200" },
  { key: "contacted", label: "Contacted / In Progress", color: "bg-indigo-50 text-indigo-900 border-indigo-200" },
  { key: "qualified", label: "Qualified", color: "bg-teal-50 text-teal-900 border-teal-200" },
  { key: "appointment_offered", label: "Appointment Offered", color: "bg-purple-50 text-purple-900 border-purple-200" },
  { key: "appointment_booked", label: "Appointment Booked", color: "bg-green-50 text-green-900 border-green-200" },
  { key: "nurture", label: "Nurture", color: "bg-amber-50 text-amber-900 border-amber-200" },
  { key: "escalated", label: "Escalated (Human Takeover)", color: "bg-red-50 text-red-900 border-red-200" },
  { key: "opted_out", label: "Opted Out", color: "bg-slate-100 text-slate-700 border-slate-200" },
  { key: "dead", label: "Dead", color: "bg-slate-100 text-slate-500 border-slate-200" },
  { key: "merged", label: "Merged / Duplicate", color: "bg-slate-100 text-slate-600 border-slate-200" },
];

export default function ExecutiveFunnelPage() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  const load = () => {
    setError(null);
    setData(null);
    api.get("/metrics/funnel").then(setData).catch(setError);
  };

  useEffect(load, []);

  if (error) return <ErrorState error={error} onRetry={load} />;
  if (!data) return <LoadingState />;

  return (
    <div>
      <h1 className="text-xl font-semibold text-slate-900 mb-1">Executive Funnel</h1>
      <p className="text-sm text-slate-500 mb-6">
        {data.total} lead{data.total === 1 ? "" : "s"} total across the pipeline.
      </p>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {STAGES.map((stage) => (
          <div key={stage.key} className={`rounded-lg border p-4 ${stage.color}`}>
            <div className="text-2xl font-semibold">{data[stage.key] ?? 0}</div>
            <div className="text-xs font-medium mt-1">{stage.label}</div>
          </div>
        ))}
        {data.other > 0 && (
          <div className="rounded-lg border p-4 bg-slate-50 text-slate-600 border-slate-200">
            <div className="text-2xl font-semibold">{data.other}</div>
            <div className="text-xs font-medium mt-1">Other</div>
          </div>
        )}
      </div>
    </div>
  );
}
