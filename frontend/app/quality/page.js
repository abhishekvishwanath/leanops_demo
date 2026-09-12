"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "../../lib/api";
import { LoadingState, ErrorState, EmptyState } from "../../components/DataState";

const DIMENSIONS = [
  ["disclosure_pass", "Disclosure"],
  ["language_pass", "Language"],
  ["qualification_pass", "Qualification"],
  ["accuracy_pass", "Accuracy"],
  ["conversation_pass", "Conversation"],
  ["escalation_pass", "Escalation"],
  ["crm_pass", "CRM"],
  ["booking_pass", "Booking"],
  ["compliance_pass", "Compliance"],
];

function Pill({ pass, label }) {
  return (
    <span className={`text-xs rounded px-1.5 py-0.5 ${pass ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"}`}>
      {label}
    </span>
  );
}

export default function QualityPage() {
  const [reviews, setReviews] = useState(null);
  const [error, setError] = useState(null);
  const [expanded, setExpanded] = useState(null);

  const load = () => {
    setError(null);
    api.get("/quality-reviews").then(setReviews).catch(setError);
  };

  useEffect(load, []);

  if (error) return <ErrorState error={error} onRetry={load} />;
  if (!reviews) return <LoadingState />;

  return (
    <div>
      <h1 className="text-xl font-semibold text-slate-900 mb-1">Quality &amp; Operations</h1>
      <p className="text-sm text-slate-500 mb-4">
        Call-quality review against the spec section 9 rubric. A hallucination flag means the AI answered from
        outside approved ERP/FAQ data — always a training/process signal, never something to leave unactioned.
      </p>

      {reviews.length === 0 && <EmptyState label="No call reviews yet." />}

      <div className="space-y-3">
        {reviews.map((r) => (
          <div key={r.review_id} className={`bg-white rounded-lg border p-4 ${r.hallucination_flag ? "border-red-300" : "border-slate-200"}`}>
            <div className="flex items-center justify-between mb-2">
              <div>
                <Link href={`/leads/${r.call.lead_id}`} className="font-medium text-slate-900 hover:underline">
                  {r.call.lead_id}
                </Link>
                <span className="text-xs text-slate-400 ml-2">
                  {r.call.channel} · {r.call.language} · {new Date(r.created_at).toLocaleString()} · reviewed by {r.reviewer}
                </span>
              </div>
              {r.hallucination_flag && (
                <span className="text-xs bg-red-100 text-red-800 rounded-full px-2 py-0.5 font-medium">Hallucination flagged</span>
              )}
            </div>
            <div className="flex flex-wrap gap-1 mb-2">
              {DIMENSIONS.map(([key, label]) => (
                <Pill key={key} pass={r[key]} label={label} />
              ))}
            </div>
            <div className="text-sm text-slate-700 mb-2">
              <span className="text-xs text-slate-400">Disposition: </span>{r.call.disposition}
            </div>
            {r.notes && <div className="text-sm text-slate-600 mb-2">{r.notes}</div>}
            <button
              onClick={() => setExpanded(expanded === r.review_id ? null : r.review_id)}
              className="text-xs text-slate-500 hover:underline"
            >
              {expanded === r.review_id ? "Hide transcript" : "Show transcript"}
            </button>
            {expanded === r.review_id && (
              <pre className="mt-2 text-xs text-slate-600 whitespace-pre-wrap bg-slate-50 rounded p-3 border border-slate-100">
                {r.call.transcript}
              </pre>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
