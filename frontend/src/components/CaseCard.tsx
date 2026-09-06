"use client";

import Link from "next/link";
import { CaseListItem } from "@/lib/api-types";
import { StatusBadge } from "./ui";
import { timeAgo } from "@/lib/format";

/**
 * Reusable case card used on the Cases page (grid view) and the Dashboard.
 * Purely presentational — one case, all fields come from the API payload.
 */
export function CaseCard({ item }: { item: CaseListItem }) {
  return (
    <Link
      href={`/cases/${item.id}`}
      className="group card block p-5 transition hover:border-blue-300 hover:shadow-card-hover"
    >
      <div className="flex items-start justify-between gap-3">
        <span className="font-mono text-xs font-semibold text-blue-600">
          {item.case_number}
        </span>
        <StatusBadge status={item.status} />
      </div>
      <h3 className="mt-2 text-sm font-semibold text-slate-900 group-hover:text-blue-700">
        {item.title}
      </h3>
      {item.description && (
        <p className="mt-1 line-clamp-2 text-xs text-slate-600">
          {item.description}
        </p>
      )}
      <div className="mt-4 flex flex-wrap items-center gap-x-3 gap-y-1 border-t border-slate-100 pt-3 text-xs text-slate-500">
        <span className="font-medium text-slate-600">{item.crime_type}</span>
        <span aria-hidden="true">·</span>
        <span className="truncate">{item.police_station}</span>
        <span className="ml-auto whitespace-nowrap">
          Updated {timeAgo(item.updated_at)}
        </span>
      </div>
      <p className="mt-1 truncate text-xs text-slate-500">
        IO:{" "}
        {item.assigned_io
          ? (item.assigned_io.full_name ?? item.assigned_io.username)
          : "Unassigned"}
      </p>
    </Link>
  );
}
