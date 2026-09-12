"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { api } from "../../lib/api";
import { LoadingState, ErrorState, EmptyState } from "../../components/DataState";
import StatusBadge from "../../components/StatusBadge";

const STATUS_OPTIONS = [
  "New", "Assigned", "Qualified", "Nurture", "Sales callback", "Follow-up due",
  "WhatsApp follow-up", "Appointment proposed", "Appointment Booked", "Review Queue",
  "Escalated - Human Takeover", "Opted Out", "Dead",
];

function formatMoney(v) {
  if (v === null || v === undefined) return "—";
  return `₹${(v / 100000).toFixed(1)}L`;
}

export default function LeadsPage() {
  const [leads, setLeads] = useState(null);
  const [salespeople, setSalespeople] = useState([]);
  const [projects, setProjects] = useState([]);
  const [error, setError] = useState(null);
  const [statusFilter, setStatusFilter] = useState("");
  const [projectFilter, setProjectFilter] = useState("");
  const [busyId, setBusyId] = useState(null);

  const load = () => {
    setError(null);
    const params = new URLSearchParams();
    if (statusFilter) params.set("status", statusFilter);
    if (projectFilter) params.set("project_id", projectFilter);
    Promise.all([
      api.get(`/leads?${params.toString()}`),
      api.get("/salespeople"),
      api.get("/projects"),
    ])
      .then(([l, s, p]) => {
        setLeads(l);
        setSalespeople(s);
        setProjects(p);
      })
      .catch(setError);
  };

  useEffect(load, [statusFilter, projectFilter]);

  const spName = useMemo(() => {
    const map = {};
    salespeople.forEach((s) => (map[s.salesperson_id] = s.name));
    return map;
  }, [salespeople]);

  async function reassign(leadId, salespersonId) {
    setBusyId(leadId);
    try {
      await api.patch(`/leads/${leadId}`, { assigned_salesperson_id: salespersonId || null });
      load();
    } catch (e) {
      alert(`Reassign failed: ${e.message}`);
    } finally {
      setBusyId(null);
    }
  }

  async function disqualify(leadId) {
    if (!confirm(`Mark ${leadId} as Dead?`)) return;
    setBusyId(leadId);
    try {
      await api.patch(`/leads/${leadId}`, { status: "Dead" });
      load();
    } catch (e) {
      alert(`Disqualify failed: ${e.message}`);
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div>
      <h1 className="text-xl font-semibold text-slate-900 mb-1">Live Lead Queue</h1>
      <p className="text-sm text-slate-500 mb-4">
        Assign/reassign, disqualify, or open a lead for the full profile, transcript, and next actions.
      </p>

      <div className="flex gap-3 mb-4">
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="rounded border border-slate-300 text-sm px-2 py-1.5"
        >
          <option value="">All statuses</option>
          {STATUS_OPTIONS.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
        <select
          value={projectFilter}
          onChange={(e) => setProjectFilter(e.target.value)}
          className="rounded border border-slate-300 text-sm px-2 py-1.5"
        >
          <option value="">All projects</option>
          {projects.map((p) => (
            <option key={p.project_id} value={p.project_id}>{p.project_id} — {p.project_name}</option>
          ))}
        </select>
      </div>

      {error && <ErrorState error={error} onRetry={load} />}
      {!error && !leads && <LoadingState />}
      {!error && leads && leads.length === 0 && <EmptyState label="No leads match this filter." />}

      {!error && leads && leads.length > 0 && (
        <div className="overflow-x-auto bg-white rounded-lg border border-slate-200">
          <table>
            <thead>
              <tr>
                <th>Lead</th>
                <th>Source</th>
                <th>Project</th>
                <th>Budget</th>
                <th>Language</th>
                <th>Grade</th>
                <th>Status</th>
                <th>Assigned to</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {leads.map((l) => (
                <tr key={l.lead_id}>
                  <td>
                    <Link href={`/leads/${l.lead_id}`} className="font-medium text-slate-900 hover:underline">
                      {l.name}
                    </Link>
                    <div className="text-xs text-slate-400">{l.lead_id} · {l.phone}</div>
                  </td>
                  <td>{l.source}</td>
                  <td>{l.project_interest || "—"}{l.bhk ? ` · ${l.bhk}` : ""}</td>
                  <td>{formatMoney(l.budget_min_inr)}–{formatMoney(l.budget_max_inr)}</td>
                  <td>{l.language || "—"}</td>
                  <td>{l.lead_grade ? `${l.lead_grade} (${l.lead_score})` : "—"}</td>
                  <td><StatusBadge value={l.status} /></td>
                  <td>
                    <select
                      value={l.assigned_salesperson_id || ""}
                      disabled={busyId === l.lead_id}
                      onChange={(e) => reassign(l.lead_id, e.target.value)}
                      className="rounded border border-slate-300 text-xs px-1.5 py-1"
                    >
                      <option value="">Unassigned</option>
                      {salespeople.map((s) => (
                        <option key={s.salesperson_id} value={s.salesperson_id}>{s.name}</option>
                      ))}
                    </select>
                  </td>
                  <td>
                    <button
                      onClick={() => disqualify(l.lead_id)}
                      disabled={busyId === l.lead_id || l.status === "Dead"}
                      className="text-xs text-red-600 hover:underline disabled:text-slate-300"
                    >
                      Disqualify
                    </button>
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
