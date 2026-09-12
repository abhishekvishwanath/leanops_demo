"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import { api } from "../../../lib/api";
import { LoadingState, ErrorState } from "../../../components/DataState";
import StatusBadge from "../../../components/StatusBadge";

function formatMoney(v) {
  if (v === null || v === undefined) return "—";
  return `₹${(v / 100000).toFixed(1)}L`;
}

function Field({ label, value }) {
  return (
    <div>
      <div className="text-xs text-slate-400">{label}</div>
      <div className="text-sm text-slate-800">{value ?? "—"}</div>
    </div>
  );
}

function Section({ title, children }) {
  return (
    <div className="bg-white rounded-lg border border-slate-200 p-4 mb-4">
      <h2 className="text-sm font-semibold text-slate-900 mb-3">{title}</h2>
      {children}
    </div>
  );
}

export default function LeadDetailPage({ params }) {
  const { id } = use(params);
  const [detail, setDetail] = useState(null);
  const [salespeople, setSalespeople] = useState([]);
  const [slots, setSlots] = useState([]);
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);
  const [notes, setNotes] = useState("");
  const [question, setQuestion] = useState("");
  const [questionResult, setQuestionResult] = useState(null);
  const [replyText, setReplyText] = useState("");
  const [followupDay, setFollowupDay] = useState(3);

  const load = () => {
    setError(null);
    api.get(`/leads/${id}`)
      .then((d) => {
        setDetail(d);
        setNotes(d.lead.last_intent || "");
        if (d.lead.project_interest) {
          api.get(`/projects/${d.lead.project_interest}/slots?status=Available`).then(setSlots).catch(() => setSlots([]));
        }
      })
      .catch(setError);
    api.get("/salespeople").then(setSalespeople).catch(() => {});
  };

  useEffect(load, [id]);

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

  if (error) return <ErrorState error={error} onRetry={load} />;
  if (!detail) return <LoadingState />;

  const { lead, events } = detail;

  return (
    <div>
      <Link href="/leads" className="text-xs text-slate-500 hover:underline">&larr; Back to Lead Queue</Link>

      <div className="flex items-center justify-between mt-2 mb-4">
        <div>
          <h1 className="text-xl font-semibold text-slate-900">{lead.name}</h1>
          <div className="text-xs text-slate-400">{lead.lead_id} · {lead.phone} · {lead.email || "no email"}</div>
        </div>
        <StatusBadge value={lead.status} />
      </div>

      {lead.duplicate_of && (
        <div className="rounded-md border border-orange-200 bg-orange-50 text-orange-800 text-sm p-3 mb-4">
          Duplicate of <Link href={`/leads/${lead.duplicate_of}`} className="underline">{lead.duplicate_of}</Link>
          {lead.canonical_lead_id ? " (auto-merged)" : " — pending review"}
          {lead.claim_status && <> · Broker claim: <strong>{lead.claim_status}</strong></>}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2">
          <Section title="Lead Profile">
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              <Field label="Source" value={lead.source} />
              <Field label="Project" value={lead.project_interest} />
              <Field label="BHK" value={lead.bhk} />
              <Field label="Budget" value={`${formatMoney(lead.budget_min_inr)}–${formatMoney(lead.budget_max_inr)}`} />
              <Field label="Language" value={lead.language} />
              <Field label="Timeline" value={lead.timeline} />
              <Field label="Grade / Score" value={lead.lead_grade ? `${lead.lead_grade} (${lead.lead_score})` : null} />
              <Field label="Created" value={new Date(lead.created_at).toLocaleString()} />
              <Field label="Assigned to" value={lead.assigned_salesperson_id} />
            </div>
          </Section>

          <Section title="Event Timeline">
            <ol className="space-y-2 max-h-96 overflow-y-auto">
              {events.map((e, i) => (
                <li key={i} className="text-xs border-l-2 border-slate-200 pl-3">
                  <div className="flex justify-between text-slate-800">
                    <span className="font-medium">{e.event_type}</span>
                    <span className="text-slate-400">{new Date(e.created_at).toLocaleString()}</span>
                  </div>
                  <pre className="text-slate-500 whitespace-pre-wrap break-words">{JSON.stringify(e.payload, null, 0)}</pre>
                </li>
              ))}
            </ol>
          </Section>

          <Section title="Available slots for this project">
            {!lead.project_interest && <div className="text-sm text-slate-400">No project associated with this lead.</div>}
            {lead.project_interest && slots.length === 0 && (
              <div className="text-sm text-slate-400">No available slots right now.</div>
            )}
            {slots.length > 0 && (
              <ul className="space-y-1">
                {slots.map((s) => (
                  <li key={s.slot_id} className="flex items-center justify-between text-sm">
                    <span>{s.slot_date} at {s.slot_time} — {s.salesperson_id}</span>
                    <button
                      disabled={busy}
                      onClick={() => run(() => api.post(`/slots/${s.slot_id}/hold`, { lead_id: lead.lead_id }))}
                      className="text-xs bg-slate-900 text-white rounded px-2 py-1 hover:bg-slate-700 disabled:opacity-50"
                    >
                      Offer this slot
                    </button>
                  </li>
                ))}
              </ul>
            )}
            <p className="text-xs text-slate-400 mt-2">
              Offering a slot holds it (WF008). Confirm the hold from the Slots &amp; Bookings page once the lead agrees.
            </p>
          </Section>
        </div>

        <div>
          <Section title="Actions">
            <div className="space-y-4">
              <div>
                <label className="text-xs text-slate-500 block mb-1">Reassign salesperson</label>
                <select
                  value={lead.assigned_salesperson_id || ""}
                  onChange={(e) => run(() => api.patch(`/leads/${id}`, { assigned_salesperson_id: e.target.value || null }))}
                  className="w-full rounded border border-slate-300 text-sm px-2 py-1.5"
                >
                  <option value="">Unassigned</option>
                  {salespeople.map((s) => (
                    <option key={s.salesperson_id} value={s.salesperson_id}>{s.name}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-xs text-slate-500 block mb-1">Notes / next action</label>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  rows={2}
                  className="w-full rounded border border-slate-300 text-sm px-2 py-1.5"
                />
                <button
                  disabled={busy}
                  onClick={() => run(() => api.patch(`/leads/${id}`, { last_intent: notes }))}
                  className="mt-1 text-xs bg-slate-900 text-white rounded px-2 py-1 hover:bg-slate-700 disabled:opacity-50"
                >
                  Save notes
                </button>
              </div>

              <div className="flex gap-2">
                <button
                  disabled={busy}
                  onClick={() => run(() => api.post(`/leads/${id}/contact-outcome`, { outcome: "answered", channel: "voice" }))}
                  className="flex-1 text-xs border border-slate-300 rounded px-2 py-1.5 hover:bg-slate-50"
                >
                  Mark answered
                </button>
                <button
                  disabled={busy}
                  onClick={() => run(() => api.post(`/leads/${id}/contact-outcome`, { outcome: "no_answer", channel: "voice" }))}
                  className="flex-1 text-xs border border-slate-300 rounded px-2 py-1.5 hover:bg-slate-50"
                >
                  Mark no answer
                </button>
              </div>

              <div>
                <label className="text-xs text-slate-500 block mb-1">Send follow-up</label>
                <div className="flex gap-2">
                  <select
                    value={followupDay}
                    onChange={(e) => setFollowupDay(Number(e.target.value))}
                    className="rounded border border-slate-300 text-sm px-2 py-1.5"
                  >
                    <option value={3}>Day 3</option>
                    <option value={7}>Day 7</option>
                    <option value={10}>Day 10</option>
                  </select>
                  <button
                    disabled={busy}
                    onClick={() => run(() => api.post(`/leads/${id}/follow-up`, { day: followupDay }))}
                    className="text-xs bg-slate-900 text-white rounded px-2 py-1 hover:bg-slate-700 disabled:opacity-50"
                  >
                    Send
                  </button>
                </div>
              </div>

              <div>
                <label className="text-xs text-slate-500 block mb-1">Reply from lead (simulate inbound)</label>
                <textarea
                  value={replyText}
                  onChange={(e) => setReplyText(e.target.value)}
                  rows={2}
                  placeholder="e.g. Yes still interested"
                  className="w-full rounded border border-slate-300 text-sm px-2 py-1.5"
                />
                <button
                  disabled={busy || !replyText}
                  onClick={() => run(() => api.post(`/leads/${id}/reply`, { message: replyText }).then(() => setReplyText("")))}
                  className="mt-1 text-xs bg-slate-900 text-white rounded px-2 py-1 hover:bg-slate-700 disabled:opacity-50"
                >
                  Record reply (stops follow-ups)
                </button>
              </div>

              <div className="pt-2 border-t border-slate-100 flex justify-between">
                <button
                  disabled={busy || lead.status === "Opted Out"}
                  onClick={() => run(() => api.post(`/leads/${id}/opt-out`))}
                  className="text-xs text-slate-600 hover:underline disabled:text-slate-300"
                >
                  Opt out
                </button>
                <button
                  disabled={busy || lead.status === "Dead"}
                  onClick={() => run(() => api.patch(`/leads/${id}`, { status: "Dead" }))}
                  className="text-xs text-red-600 hover:underline disabled:text-slate-300"
                >
                  Disqualify
                </button>
              </div>
            </div>
          </Section>

          <Section title="Ask a question (escalation classifier)">
            <textarea
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              rows={3}
              placeholder="e.g. Can I get a discount on this unit?"
              className="w-full rounded border border-slate-300 text-sm px-2 py-1.5"
            />
            <button
              disabled={busy || !question}
              onClick={() =>
                run(async () => {
                  const result = await api.post(`/leads/${id}/questions`, { message: question });
                  setQuestionResult(result);
                  setQuestion("");
                })
              }
              className="mt-2 text-xs bg-slate-900 text-white rounded px-2 py-1 hover:bg-slate-700 disabled:opacity-50"
            >
              Classify &amp; route
            </button>
            {questionResult && (
              <div className="mt-3 text-xs rounded border border-slate-200 p-2 bg-slate-50">
                <div className="mb-1">
                  Classified as <strong>{questionResult.escalation_class}</strong> ({questionResult.source}, confidence {questionResult.confidence.toFixed(2)})
                </div>
                {questionResult.ai_answer && <div className="text-slate-700">AI answer: {questionResult.ai_answer}</div>}
                {questionResult.escalation_ticket_id && (
                  <div className="text-slate-700">
                    Escalation ticket #{questionResult.escalation_ticket_id} created —{" "}
                    <Link href="/escalations" className="underline">view in Escalation Centre</Link>
                  </div>
                )}
              </div>
            )}
          </Section>
        </div>
      </div>
    </div>
  );
}
