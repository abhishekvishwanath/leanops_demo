const COLORS = {
  New: "bg-blue-100 text-blue-800",
  Assigned: "bg-indigo-100 text-indigo-800",
  Qualified: "bg-teal-100 text-teal-800",
  Nurture: "bg-amber-100 text-amber-800",
  "Sales callback": "bg-indigo-100 text-indigo-800",
  "Follow-up due": "bg-amber-100 text-amber-800",
  "WhatsApp follow-up": "bg-amber-100 text-amber-800",
  "Appointment proposed": "bg-purple-100 text-purple-800",
  "Appointment Booked": "bg-green-100 text-green-800",
  "Review Queue": "bg-orange-100 text-orange-800",
  "Escalated - Human Takeover": "bg-red-100 text-red-800",
  "Opted Out": "bg-slate-200 text-slate-700",
  Dead: "bg-slate-200 text-slate-500",
  "Merged - Duplicate": "bg-slate-200 text-slate-600",
  "Merged - Broker Claim Under Review": "bg-orange-100 text-orange-800",
  Available: "bg-green-100 text-green-800",
  Held: "bg-amber-100 text-amber-800",
  Booked: "bg-indigo-100 text-indigo-800",
  Cancelled: "bg-slate-200 text-slate-600",
  Completed: "bg-slate-200 text-slate-600",
  "No-show": "bg-red-100 text-red-800",
  Open: "bg-orange-100 text-orange-800",
  "In Progress": "bg-amber-100 text-amber-800",
  Resolved: "bg-green-100 text-green-800",
  Reopened: "bg-red-100 text-red-800",
};

const ESCALATION_COLORS = {
  E0: "bg-slate-100 text-slate-700",
  E1: "bg-blue-100 text-blue-800",
  E2: "bg-indigo-100 text-indigo-800",
  E3: "bg-amber-100 text-amber-800",
  E4: "bg-orange-100 text-orange-800",
  E5: "bg-red-100 text-red-800",
};

export default function StatusBadge({ value, variant }) {
  const colorMap = variant === "escalation" ? ESCALATION_COLORS : COLORS;
  const cls = colorMap[value] || "bg-slate-100 text-slate-700";
  return (
    <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium whitespace-nowrap ${cls}`}>
      {value}
    </span>
  );
}
