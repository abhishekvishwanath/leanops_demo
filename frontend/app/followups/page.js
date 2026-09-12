"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "../../lib/api";
import { LoadingState, ErrorState, EmptyState } from "../../components/DataState";

export default function FollowupsPage() {
  const [due, setDue] = useState(null);
  const [leads, setLeads] = useState([]);
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);
  const [manualLead, setManualLead] = useState("");
  const [manualDay, setManualDay] = useState(3);

  const load = () => {
    setError(null);
    api.get("/follow-ups/due").then(setDue).catch(setError);
    api.get("/leads").then(setLeads).catch(() => {});
  };

  useEffect(load, []);

  async function send(leadId, day) {
    setBusy(true);
    try {
      await api.post(`/leads/${leadId}/follow-up`, { day });
      load();
    } catch (e) {
      alert(e.message);
    } finally {
      setBusy(false);
    }
  }

  if (error) return <ErrorState error={error} onRetry={load} />;
  if (!due) return <LoadingState />;

  return (
    <div>
      <h1 className="text-xl font-semibold text-slate-900 mb-1">Follow-up Centre</h1>
      <p className="text-sm text-slate-500 mb-4">
        Day 3/7/10 sequence, stopping on reply, opt-out, booking, or human takeover. In production a scheduler
        (Celery beat / Trigger.dev) calls this same endpoint on a timer — here you trigger it manually.
      </p>

      <div className="bg-white rounded-lg border border-slate-200 p-4 mb-4">
        <h2 className="text-sm font-semibold text-slate-900 mb-2">Due right now</h2>
        {due.length === 0 && (
          <EmptyState label="Nothing due — all seed leads were created today, so day 3/7/10 hasn't elapsed yet. Use the manual trigger below to demo it." />
        )}
        {due.length > 0 && (
          <ul className="space-y-2">
            {due.map((d) => (
              <li key={`${d.lead_id}-${d.day}`} className="flex items-center justify-between text-sm">
                <span>
                  <Link href={`/leads/${d.lead_id}`} className="font-medium hover:underline">{d.lead_id}</Link>{" "}
                  — day {d.day} due ({d.days_since_created} days since creation)
                </span>
                <button
                  disabled={busy}
                  onClick={() => send(d.lead_id, d.day)}
                  className="text-xs bg-slate-900 text-white rounded px-2 py-1 hover:bg-slate-700 disabled:opacity-50"
                >
                  Send now
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="bg-white rounded-lg border border-slate-200 p-4">
        <h2 className="text-sm font-semibold text-slate-900 mb-2">Manual trigger (demo)</h2>
        <p className="text-xs text-slate-500 mb-3">
          Force-send a specific day's follow-up regardless of elapsed time — useful for demoing the stop conditions
          without waiting days. Still respects them: already-sent days, replies, opt-outs, bookings, and dead leads
          are all rejected.
        </p>
        <div className="flex gap-2 items-center">
          <select value={manualLead} onChange={(e) => setManualLead(e.target.value)} className="rounded border border-slate-300 text-sm px-2 py-1.5">
            <option value="">Pick a lead...</option>
            {leads.map((l) => <option key={l.lead_id} value={l.lead_id}>{l.lead_id} — {l.name} ({l.status})</option>)}
          </select>
          <select value={manualDay} onChange={(e) => setManualDay(Number(e.target.value))} className="rounded border border-slate-300 text-sm px-2 py-1.5">
            <option value={3}>Day 3</option>
            <option value={7}>Day 7</option>
            <option value={10}>Day 10</option>
          </select>
          <button
            disabled={busy || !manualLead}
            onClick={() => send(manualLead, manualDay)}
            className="text-xs bg-slate-900 text-white rounded px-2 py-1.5 hover:bg-slate-700 disabled:opacity-50"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
