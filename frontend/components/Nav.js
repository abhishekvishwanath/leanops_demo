"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/", label: "Executive Funnel" },
  { href: "/leads", label: "Lead Queue" },
  { href: "/inventory", label: "ERP Inventory" },
  { href: "/salespeople", label: "Salesperson Board" },
  { href: "/slots", label: "Slots & Bookings" },
  { href: "/followups", label: "Follow-up Centre" },
  { href: "/escalations", label: "Escalation Centre" },
  { href: "/quality", label: "Quality & Ops" },
];

export default function Nav() {
  const pathname = usePathname();

  return (
    <nav className="w-56 shrink-0 border-r border-slate-200 bg-white min-h-screen px-3 py-5">
      <div className="px-2 mb-6">
        <div className="text-sm font-semibold text-slate-900">XYZ Properties</div>
        <div className="text-xs text-slate-500">Dealer Dashboard (Demo)</div>
      </div>
      <ul className="space-y-0.5">
        {LINKS.map((link) => {
          const active = pathname === link.href;
          return (
            <li key={link.href}>
              <Link
                href={link.href}
                className={`block rounded-md px-3 py-2 text-sm ${
                  active
                    ? "bg-slate-900 text-white font-medium"
                    : "text-slate-600 hover:bg-slate-100"
                }`}
              >
                {link.label}
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
