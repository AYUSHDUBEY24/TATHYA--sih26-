import Link from 'next/link';
import { AuditLogEntry, CaseListItem } from '@/lib/api-types';

export function KpiCard({ label, value, tone }: { label: string; value: number; tone: 'sky' | 'amber' | 'emerald' | 'violet' }) {
  const tones = {
    sky: 'border-sky-900 bg-sky-950/30 text-sky-400',
    amber: 'border-amber-900 bg-amber-950/30 text-amber-400',
    emerald: 'border-emerald-900 bg-emerald-950/30 text-emerald-400',
    violet: 'border-violet-900 bg-violet-950/30 text-violet-400',
  };
  return (
    <div className={`rounded-xl border p-5 ${tones[tone]}`}>
      <p className='text-xs font-medium uppercase tracking-wide opacity-80'>{label}</p>
      <p className='mt-2 text-3xl font-bold'>{value}</p>
    </div>
  );
}

export function CasesTable({ cases }: { cases: CaseListItem[] }) {
  return (
    <section>
      <div className='mb-4 flex items-center justify-between'>
        <h2 className='text-lg font-semibold'>Recent Cases</h2>
        <Link href='/cases' className='text-sm font-medium text-sky-400 hover:text-sky-300'>
          View all →
        </Link>
      </div>
      {cases.length === 0 ? (
        <div className='rounded-xl border border-dashed border-slate-700 p-8 text-center text-slate-500'>
          No cases yet. <Link href='/cases/new' className='text-sky-400 hover:underline'>Create your first case</Link>.
        </div>
      ) : (
        <div className='overflow-hidden rounded-xl border border-slate-800'>
          <table className='w-full text-left text-sm'>
            <thead className='bg-slate-900 text-xs uppercase tracking-wide text-slate-400'>
              <tr>
                <th className='px-4 py-3'>Case</th>
                <th className='px-4 py-3'>Status</th>
                <th className='px-4 py-3'>Assigned IO</th>
                <th className='px-4 py-3'>Updated</th>
              </tr>
            </thead>
            <tbody className='divide-y divide-slate-800'>
              {cases.map((c) => (
                <tr key={c.id} className='hover:bg-slate-900/50'>
                  <td className='px-4 py-3'>
                    <Link href={`/cases/${c.id}`} className='font-medium hover:text-sky-400'>
                      {c.title}
                    </Link>
                    <p className='text-xs text-slate-500'>{c.case_number}</p>
                  </td>
                  <td className='px-4 py-3'>
                    <span className={statusBadgeClass(c.status)}>{c.status.replace(/_/g, ' ')}</span>
                  </td>
                  <td className='px-4 py-3 text-slate-400'>
                    {c.assigned_io?.full_name ?? c.assigned_io?.username ?? '—'}
                  </td>
                  <td className='px-4 py-3 text-slate-500'>{new Date(c.updated_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

export function ActivityList({ activity }: { activity: AuditLogEntry[] }) {
  return (
    <section>
      <div className='mb-4 flex items-center justify-between'>
        <h2 className='text-lg font-semibold'>Recent Activity</h2>
        <Link href='/audit' className='text-sm font-medium text-sky-400 hover:text-sky-300'>
          View audit log →
        </Link>
      </div>
      {activity.length === 0 ? (
        <div className='rounded-xl border border-dashed border-slate-700 p-8 text-center text-slate-500'>
          No recent activity.
        </div>
      ) : (
        <div className='space-y-2'>
          {activity.map((log) => (
            <div key={log.id} className='flex items-center gap-4 rounded-lg border border-slate-800 bg-slate-900/50 px-4 py-3 text-sm'>
              <span className='rounded-md bg-slate-800 px-2 py-0.5 text-xs font-semibold text-slate-300'>
                {log.action}
              </span>
              <span className='text-slate-400'>{log.actor_username ?? 'system'}</span>
              <span className='ml-auto text-xs text-slate-500'>
                {new Date(log.created_at).toLocaleString()}
              </span>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

export function statusBadgeClass(status: string): string {
  const map: Record<string, string> = {
    OPEN: 'rounded-md bg-sky-900/80 px-2 py-0.5 text-xs font-semibold text-sky-300',
    UNDER_INVESTIGATION: 'rounded-md bg-amber-900/80 px-2 py-0.5 text-xs font-semibold text-amber-300',
    UNDER_REVIEW: 'rounded-md bg-violet-900/80 px-2 py-0.5 text-xs font-semibold text-violet-300',
    CHARGESHEET_FILED: 'rounded-md bg-orange-900/80 px-2 py-0.5 text-xs font-semibold text-orange-300',
    COURT_STAGE: 'rounded-md bg-fuchsia-900/80 px-2 py-0.5 text-xs font-semibold text-fuchsia-300',
    CLOSED: 'rounded-md bg-slate-800 px-2 py-0.5 text-xs font-semibold text-slate-300',
    ARCHIVED: 'rounded-md bg-slate-800/60 px-2 py-0.5 text-xs font-semibold text-slate-400',
  };
  return map[status] ?? 'rounded-md bg-slate-800 px-2 py-0.5 text-xs font-semibold text-slate-300';
}
