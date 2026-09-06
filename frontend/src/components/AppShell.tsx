"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/useAuth";
import {
  IconHome,
  IconFolder,
  IconSearch,
  IconSparkles,
  IconClipboardList,
  IconShield,
  IconLogOut,
  IconMenu,
  LogoBlock,
} from "./icons";

/**
 * Navigation is grouped and contains ONLY real routes:
 * /, /cases, /search, /ai, /audit. No placeholder pages.
 */
const navGroups = [
  {
    label: "Overview",
    items: [{ href: "/", label: "Dashboard", icon: IconHome }],
  },
  {
    label: "Investigation",
    items: [
      { href: "/cases", label: "Cases", icon: IconFolder },
      { href: "/search", label: "Search", icon: IconSearch },
    ],
  },
  {
    label: "Intelligence",
    items: [{ href: "/ai", label: "AI Assistant", icon: IconSparkles }],
  },
  {
    label: "Oversight",
    items: [{ href: "/audit", label: "Audit Logs", icon: IconClipboardList }],
  },
];

function isActive(pathname: string, href: string): boolean {
  return pathname === href || (href !== "/" && pathname.startsWith(href));
}

export default function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // The login page renders standalone — no shell chrome while logged out.
  if (pathname === "/login") {
    return <>{children}</>;
  }

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-slate-900/50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar: Deep Navy → Slate gradient */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 flex w-64 flex-col bg-gradient-to-b from-[#0f172a] to-[#1e293b] transition-transform lg:static lg:translate-x-0 ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        {/* Brand */}
        <div className="flex h-16 items-center border-b border-white/10 px-5">
          <LogoBlock />
        </div>

        {/* Grouped navigation */}
        <nav className="flex-1 space-y-5 overflow-y-auto px-3 py-4 slim-scrollbar">
          {navGroups.map((group) => (
            <div key={group.label}>
              <p className="mb-1.5 px-3 text-[10px] font-semibold uppercase tracking-widest text-slate-500">
                {group.label}
              </p>
              <div className="space-y-0.5">
                {group.items.map((item) => {
                  const active = isActive(pathname, item.href);
                  const Icon = item.icon;
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      onClick={() => setSidebarOpen(false)}
                      aria-current={active ? "page" : undefined}
                      className={`flex items-center gap-3 rounded-lg border-l-2 px-3 py-2 text-sm font-medium transition-colors ${
                        active
                          ? "border-blue-500 bg-blue-500/15 text-white"
                          : "border-transparent text-slate-400 hover:bg-white/5 hover:text-white"
                      }`}
                    >
                      <Icon className="h-[18px] w-[18px]" />
                      {item.label}
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>

        {/* User profile + sign out */}
        <div className="border-t border-white/10 p-4">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-blue-500/20 text-sm font-semibold text-white">
              {user?.full_name?.charAt(0) || user?.username?.charAt(0) || "U"}
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium text-white">
                {user?.full_name || user?.username || "Not signed in"}
              </p>
              <p className="truncate text-[11px] text-slate-400">
                {user?.role?.name?.replace(/_/g, " ") || "User"}
              </p>
            </div>
          </div>
          <button
            onClick={logout}
            className="mt-3 flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-slate-400 transition-colors hover:bg-white/5 hover:text-white"
          >
            <IconLogOut className="h-4 w-4" />
            Sign out
          </button>
        </div>
      </aside>

      {/* Main column */}
      <div className="flex min-w-0 flex-1 flex-col overflow-hidden">
        {/* Mobile top bar */}
        <header className="flex h-16 shrink-0 items-center gap-3 border-b border-slate-200 bg-white px-4 lg:px-6">
          <button
            onClick={() => setSidebarOpen(true)}
            className="rounded-lg p-2 text-slate-500 transition hover:bg-slate-100 lg:hidden"
            aria-label="Open navigation"
          >
            <IconMenu className="h-5 w-5" />
          </button>
          <div className="flex-1" />
          <span className="badge badge-success">
            <IconShield className="h-3 w-3" />
            Secure Session
          </span>
        </header>
        <main className="flex-1 overflow-y-auto p-6 lg:p-8">{children}</main>
      </div>
    </div>
  );
}
