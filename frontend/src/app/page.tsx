'use client';

import { useEffect, useState } from 'react';
import { ApiError, apiFetch } from '@/lib/auth';
import { AuditLogEntry, CaseListItem } from '@/lib/api-types';
import { CasesTable, KpiCard, ActivityList } from '@/components/dashboard';

interface DashboardStats {
  total_cases: number;
  active_cases: number;
  total_documents: number;
  recent_activity: AuditLogEntry[];
}

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [cases, setCases] = useState<CaseListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const [statsData, casesData] = await Promise.all([
          apiFetch<DashboardStats>('/api/dashboard'),
          apiFetch<CaseListItem[]>('/api/cases?limit=10'),
        ]);
        if (!cancelled) {
          setStats(statsData);
          setCases(casesData);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : 'Failed to load dashboard');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => { cancelled = true; };
  }, []);

  if (loading) {
    return (
      <div className='grid gap-6 lg:grid-cols-3'>
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className='h-32 animate-pulse rounded-xl border border-slate-800 bg-slate-900/50' />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className='rounded-xl border border-amber-800 bg-amber-950/30 p-6 text-amber-300'>
        <p className='font-semibold'>Could not load dashboard</p>
        <p className='mt-1 text-sm text-amber-400'>{error}</p>
      </div>
    );
  }

  return (
    <div className='space-y-8'>
      <div className='grid gap-4 sm:grid-cols-2 lg:grid-cols-4'>
        <KpiCard label='Total Cases' value={stats?.total_cases ?? 0} tone='sky' />
        <KpiCard label='Active Cases' value={stats?.active_cases ?? 0} tone='amber' />
        <KpiCard label='Documents' value={stats?.total_documents ?? 0} tone='emerald' />
        <KpiCard label='Recent Events' value={stats?.recent_activity?.length ?? 0} tone='violet' />
      </div>
      <CasesTable cases={cases} />
      <ActivityList activity={stats?.recent_activity ?? []} />
    </div>
  );
}
