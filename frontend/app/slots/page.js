"use client";

import { useEffect, useMemo, useState } from "react";
import { api } from "../../lib/api";
import { LoadingState, ErrorState, EmptyState } from "../../components/DataState";
import StatusBadge from "../../components/StatusBadge";

const STATUS_OPTIONS = ["Available", "Held", "Booked", "Cancelled", "Completed", "No-show"];

export default function SlotsPage() {
  const [projects, setProjects] = useState([]);
  const [leads, setLeads] = useState([]);
  const [projectFilter, setProjectFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [slots, setSlots] = useState(null);
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(null);
  const [pickedLead, setPickedLead] = useState({});

  useEffect(() => {
    api.get("/projects").then((ps) => {
      setProjects(ps);
      if (!projectFilter && ps.length) setProjectFilter(ps[0].project_id);
    }).catch(setError);
    api.get("/leads").then(setLeads).catch(() => {});
  }, []);

  const load = () => {
    if (!projectFilter) return;
    setError(null);
    const params = new URLSearchParams();
    if (statusFilter) params.set("status", statusFilter);
    api.get(`/projects/${projectFilter}/slots?${params.toString()}`).then(setSlots).catch(setError);
  };

  useEffect(load, [projectFilter, statusFilter]);

  async function run(action) {
    setBusy(true);
    try {
      await action();
      load();
    } catch (e) {
      alert(e.message);
    } finally {
      setBusy(false);
    }
  }

  const leadOptions = useMemo(() => leads.filter((l) => !l.duplicate_of), [leads]);

  return (
    <div>
      <h1 className="text-xl font-semibold text-slate-900 mb-1">Slots & Bookings</h1>
      <p className="text-sm text-slate-500 mb-4">
        Hold offers a slot to a lead; Confirm books it only if still held for that same lead (spec: recheck before booking).
      </p>

      <div className="flex gap-3 mb-4">
        <select value={projectFilter} onChange={(e) => setProjectFilter(e.target.value)} className="rounded border border-slate-300 text-sm px-2 py-1.5">
          {projects.map((p) => (
            <option key={p.project_id} value={p.project_id}>{p.project_id} — {p.project_name}</option>
          ))}
        </select>
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className="rounded border border-slate-300 text-sm px-2 py-1.5">
          <option value="">All statuses</option>
          {STATUS_OPTIONS.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
      </div>

      {error && <ErrorState error={error} onRetry={load} />}
      {!error && !slots && <LoadingState />}
      {!error && slots && slots.length === 0 && <EmptyState label="No slots match this filter." />}

      {!error && slots && slots.length > 0 && (
        <div className="overflow-x-auto bg-white rounded-lg border border-slate-200">
          <table>
            <thead>
              <tr>
                <th>Slot</th>
                <th>Date</th>
                <th>Time</th>
                <th>Salesperson</th>
                <th>Status</th>
                <th>Lead</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {slots.map((s) => (
                <tr key={s.slot_id}>
                  <td className="font-mono text-xs">{s.slot_id}</td>
                  <td>{s.slot_date}</td>
                  <td>{s.slot_time}</td>
                  <td>{s.salesperson_id}</td>
                  <td><StatusBadge value={s.status} /></td>
                  <td className="text-xs">{s.lead_id || "—"}</td>
                  <td>
                    {s.status === "Available" && (
                      <div className="flex gap-1 items-center">
                        <select
                          value={pickedLead[s.slot_id] || ""}
                          onChange={(e) => setPickedLead({ ...pickedLead, [s.slot_id]: e.target.value })}
                          className="rounded border border-slate-300 text-xs px-1 py-1"
                        >
                          <option value="">Pick lead...</option>
                          {leadOptions.map((l) => (
                            <option key={l.lead_id} value={l.lead_id}>{l.lead_id} — {l.name}</option>
                          ))}
                        </select>
                        <button
                          disabled={busy || !pickedLead[s.slot_id]}
                          onClick={() => run(() => api.post(`/slots/${s.slot_id}/hold`, { lead_id: pickedLead[s.slot_id] }))}
                          className="text-xs bg-slate-900 text-white rounded px-2 py-1 hover:bg-slate-700 disabled:opacity-50"
                        >
                          Hold
                        </button>
                      </div>
                    )}
                    {s.status === "Held" && (
                      <div className="flex gap-2">
                        <button
                          disabled={busy}
                          onClick={() => run(() => api.post(`/slots/${s.slot_id}/confirm`, { lead_id: s.lead_id }))}
                          className="text-xs bg-green-600 text-white rounded px-2 py-1 hover:bg-green-700 disabled:opacity-50"
                        >
                          Confirm
                        </button>
                        <button
                          disabled={busy}
                          onClick={() => run(() => api.post(`/slots/${s.slot_id}/cancel`, { reason: "Cancelled from dashboard" }))}
                          className="text-xs border border-slate-300 rounded px-2 py-1 hover:bg-slate-50 disabled:opacity-50"
                        >
                          Cancel
                        </button>
                      </div>
                    )}
                    {s.status === "Booked" && (
                      <button
                        disabled={busy}
                        onClick={() => run(() => api.post(`/slots/${s.slot_id}/cancel`, { reason: "Cancelled from dashboard" }))}
                        className="text-xs border border-slate-300 rounded px-2 py-1 hover:bg-slate-50 disabled:opacity-50"
                      >
                        Cancel
                      </button>
                    )}
                    {["Cancelled", "Completed", "No-show"].includes(s.status) && (
                      <span className="text-xs text-slate-300">—</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
