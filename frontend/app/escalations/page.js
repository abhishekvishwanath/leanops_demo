"use client";

import { Fragment, useEffect, useState } from "react";
import Link from "next/link";
import { api } from "../../lib/api";
import { LoadingState, ErrorState, EmptyState } from "../../components/DataState";
import StatusBadge from "../../components/StatusBadge";

const CLASS_OPTIONS = ["E0", "E1", "E2", "E3", "E4", "E5"];
const STATUS_OPTIONS = ["Open", "In Progress", "Resolved", "Reopened"];
const PRIORITY_OPTIONS = ["Low", "Medium", "High", "Critical"];

function EditRow({ ticket, onSaved }) {
  const [owner, setOwner] = useState(ticket.owner || "");
  const [priority, setPriority] = useState(ticket.priority || "");
  const [status, setStatus] = useState(ticket.status);
  const [resolution, setResolution] = useState(ticket.resolution || "");
  const [busy, setBusy] = useState(false);

  async function save() {
    setBusy(true);
    try {
      await api.patch(`/escalations/${ticket.ticket_id}`, { owner, priority, status, resolution });
      onSaved();
    } catch (e) {
      alert(e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <tr className="bg-slate-50">
      <td colSpan={7}>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2 items-end p-2">
          <div>
            <label className="text-xs text-slate-500 block mb-1">Owner</label>
            <input value={owner} onChange={(e) => setOwner(e.target.value)} className="w-full rounded border border-slate-300 text-sm px-2 py-1" />
          </div>
          <div>
            <label className="text-xs text-slate-500 block mb-1">Priority</label>
            <select value={priority} onChange={(e) => setPriority(e.target.value)} className="w-full rounded border border-slate-300 text-sm px-2 py-1">
              <option value="">—</option>
              {PRIORITY_OPTIONS.map((p) => <option key={p} value={p}>{p}</option>)}
            </select>
          </div>
          <div>
            <label className="text-xs text-slate-500 block mb-1">Status</label>
            <select value={status} onChange={(e) => setStatus(e.target.value)} className="w-full rounded border border-slate-300 text-sm px-2 py-1">
              {STATUS_OPTIONS.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
          <div className="col-span-2 md:col-span-1">
            <label className="text-xs text-slate-500 block mb-1">Resolution notes</label>
            <input value={resolution} onChange={(e) => setResolution(e.target.value)} className="w-full rounded border border-slate-300 text-sm px-2 py-1" />
          </div>
          <button disabled={busy} onClick={save} className="text-xs bg-slate-900 text-white rounded px-2 py-1.5 hover:bg-slate-700 disabled:opacity-50 h-fit">
            Save
          </button>
        </div>
      </td>
    </tr>
  );
}

export default function EscalationsPage() {
  const [tickets, setTickets] = useState(null);
  const [error, setError] = useState(null);
  const [classFilter, setClassFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [expanded, setExpanded] = useState(null);

  const load = () => {
    setError(null);
    const params = new URLSearchParams();
    if (classFilter) params.set("escalation_class", classFilter);
    if (statusFilter) params.set("status", statusFilter);
    api.get(`/escalations?${params.toString()}`).then(setTickets).catch(setError);
  };

  useEffect(load, [classFilter, statusFilter]);

  if (error) return <ErrorState error={error} onRetry={load} />;
  if (!tickets) return <LoadingState />;

  return (
    <div>
      <h1 className="text-xl font-semibold text-slate-900 mb-1">Escalation Centre</h1>
      <p className="text-sm text-slate-500 mb-4">
        E0 is answered directly by the AI and never reaches here. E1–E5 route by severity — assign an expert, set
        priority, then resolve or reopen.
      </p>

      <div className="flex gap-3 mb-4">
        <select value={classFilter} onChange={(e) => setClassFilter(e.target.value)} className="rounded border border-slate-300 text-sm px-2 py-1.5">
          <option value="">All classes</option>
          {CLASS_OPTIONS.map((c) => <option key={c} value={c}>{c}</option>)}
        </select>
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className="rounded border border-slate-300 text-sm px-2 py-1.5">
          <option value="">All statuses</option>
          {STATUS_OPTIONS.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
      </div>

      {tickets.length === 0 && <EmptyState label="No escalation tickets match this filter." />}

      {tickets.length > 0 && (
        <div className="overflow-x-auto bg-white rounded-lg border border-slate-200">
          <table>
            <thead>
              <tr>
                <th>Class</th>
                <th>Lead</th>
                <th>Reason</th>
                <th>Expert / Owner</th>
                <th>Priority</th>
                <th>SLA due</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {tickets.map((t) => (
                <Fragment key={t.ticket_id}>
                  <tr
                    className="cursor-pointer"
                    onClick={() => setExpanded(expanded === t.ticket_id ? null : t.ticket_id)}
                  >
                    <td><StatusBadge value={t.escalation_class} variant="escalation" /></td>
                    <td>
                      <Link href={`/leads/${t.lead_id}`} onClick={(e) => e.stopPropagation()} className="hover:underline">
                        {t.lead_id}
                      </Link>
                    </td>
                    <td className="max-w-xs truncate" title={t.reason}>{t.reason}</td>
                    <td className="text-xs">{t.expert_type}{t.owner ? ` · ${t.owner}` : " · unassigned"}</td>
                    <td className="text-xs">{t.priority || "—"}</td>
                    <td className="text-xs">{t.sla_due_at ? new Date(t.sla_due_at).toLocaleString() : "—"}</td>
                    <td><StatusBadge value={t.status} /></td>
                  </tr>
                  {expanded === t.ticket_id && (
                    <EditRow ticket={t} onSaved={() => { setExpanded(null); load(); }} />
                  )}
                </Fragment>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
