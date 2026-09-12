"use client";

import { useEffect, useState } from "react";
import { api } from "../../lib/api";
import { LoadingState, ErrorState } from "../../components/DataState";

function formatMoney(v) {
  return `₹${(v / 100000).toFixed(1)}L`;
}

export default function InventoryPage() {
  const [projects, setProjects] = useState(null);
  const [error, setError] = useState(null);

  const load = () => {
    setError(null);
    api.get("/projects").then(setProjects).catch(setError);
  };

  useEffect(load, []);

  if (error) return <ErrorState error={error} onRetry={load} />;
  if (!projects) return <LoadingState />;

  return (
    <div>
      <h1 className="text-xl font-semibold text-slate-900 mb-1">ERP Inventory</h1>
      <p className="text-sm text-slate-500 mb-4">
        Only units with <span className="font-mono text-xs">approved_for_ai = true</span> are readable by the AI —
        greyed-out rows are blocked (spec section 6: stale/unapproved records must never be quoted).
      </p>

      <div className="space-y-4">
        {projects.map((p) => (
          <div key={p.project_id} className="bg-white rounded-lg border border-slate-200 p-4">
            <div className="flex items-center justify-between mb-2">
              <div>
                <div className="font-semibold text-slate-900">{p.project_name} <span className="text-xs text-slate-400 font-normal">({p.project_id})</span></div>
                <div className="text-xs text-slate-500">{p.locality}, {p.city} · {p.construction_status} · Possession: {p.possession} · RERA: {p.rera_number}</div>
              </div>
              <div className="text-xs text-slate-500 text-right">
                {p.total_floors} floors · {p.amenity_count} amenities · {p.view} view · {p.parking_included ? "Parking included" : "No parking"}
              </div>
            </div>
            <table>
              <thead>
                <tr>
                  <th>BHK</th>
                  <th>Carpet area</th>
                  <th>Price</th>
                  <th>AI status</th>
                  <th>Note</th>
                </tr>
              </thead>
              <tbody>
                {p.units.map((u) => (
                  <tr key={u.unit_id} className={!u.approved_for_ai ? "opacity-50" : ""}>
                    <td>{u.bhk}</td>
                    <td>{u.carpet_sqft} sqft</td>
                    <td>{formatMoney(u.base_price_inr)}</td>
                    <td>
                      {u.approved_for_ai ? (
                        <span className="text-green-700 text-xs font-medium">Approved</span>
                      ) : (
                        <span className="text-red-700 text-xs font-medium">Blocked — stale</span>
                      )}
                    </td>
                    <td className="text-xs text-slate-500">{u.stale_note || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ))}
      </div>
    </div>
  );
}
