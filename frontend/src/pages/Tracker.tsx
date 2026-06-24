import { useState, useEffect } from 'react'
import { ExternalLink, Trash2, ChevronDown, ClipboardList } from 'lucide-react'
import { listApplications, updateStatus, updateNotes, deleteApplication } from '../api/client'
import type { Application, ApplicationStatus } from '../types'

const STATUSES: { value: ApplicationStatus; label: string; color: string }[] = [
  { value: 'saved',        label: 'Saved',        color: 'bg-slate-600 text-slate-200' },
  { value: 'applied',      label: 'Applied',      color: 'bg-blue-600 text-white' },
  { value: 'interviewing', label: 'Interviewing', color: 'bg-yellow-500 text-black' },
  { value: 'offer',        label: 'Offer',        color: 'bg-green-500 text-white' },
  { value: 'rejected',     label: 'Rejected',     color: 'bg-red-600 text-white' },
]

const SCORE_COLORS: Record<string, string> = {
  apply: 'text-green-400',
  maybe: 'text-yellow-400',
  skip:  'text-slate-500',
}

function statusConfig(status: ApplicationStatus) {
  return STATUSES.find(s => s.value === status) ?? STATUSES[0]
}

function ScoreRing({ score }: { score: number | null }) {
  if (score === null) return <span className="text-slate-600 text-sm">—</span>
  const r = 16
  const circ = 2 * Math.PI * r
  const offset = circ - (score / 100) * circ
  const color = score >= 70 ? '#22c55e' : score >= 45 ? '#eab308' : '#ef4444'
  return (
    <div className="relative w-11 h-11 flex-shrink-0">
      <svg className="w-full h-full -rotate-90" viewBox="0 0 40 40">
        <circle cx="20" cy="20" r={r} fill="none" stroke="#1e293b" strokeWidth="4" />
        <circle cx="20" cy="20" r={r} fill="none" stroke={color} strokeWidth="4"
          strokeDasharray={circ} strokeDashoffset={offset} strokeLinecap="round" />
      </svg>
      <span className="absolute inset-0 flex items-center justify-center text-xs font-bold text-white">
        {score}
      </span>
    </div>
  )
}

function StatusDropdown({ app, onChange }: { app: Application; onChange: (updated: Application) => void }) {
  const [open, setOpen] = useState(false)
  const cfg = statusConfig(app.status)

  async function pick(status: ApplicationStatus) {
    setOpen(false)
    const updated = await updateStatus(app.id, status)
    onChange(updated)
  }

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(o => !o)}
        className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${cfg.color} whitespace-nowrap`}
      >
        {cfg.label}
        <ChevronDown size={11} />
      </button>
      {open && (
        <div className="absolute z-20 left-0 top-full mt-1 bg-slate-800 border border-slate-700 rounded-lg shadow-xl min-w-[140px] overflow-hidden">
          {STATUSES.map(s => (
            <button
              key={s.value}
              onClick={() => pick(s.value)}
              className={`w-full text-left px-3 py-2 text-xs hover:bg-slate-700 transition-colors
                ${app.status === s.value ? 'font-semibold text-white' : 'text-slate-300'}`}
            >
              {s.label}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

function NotesCell({ app }: { app: Application }) {
  const [editing, setEditing] = useState(false)
  const [value, setValue] = useState(app.notes ?? '')

  async function save() {
    setEditing(false)
    await updateNotes(app.id, value)
  }

  if (editing) {
    return (
      <input
        autoFocus
        value={value}
        onChange={e => setValue(e.target.value)}
        onBlur={save}
        onKeyDown={e => e.key === 'Enter' && save()}
        className="w-full bg-slate-700 border border-slate-600 text-slate-200 text-xs rounded px-2 py-1 focus:outline-none focus:border-blue-500"
      />
    )
  }
  return (
    <span
      onClick={() => setEditing(true)}
      className="text-xs text-slate-400 hover:text-slate-200 cursor-text truncate max-w-[160px] block"
      title={value || 'Click to add notes'}
    >
      {value || <span className="text-slate-600 italic">Add notes…</span>}
    </span>
  )
}

const FILTER_OPTIONS: { label: string; value: string | undefined }[] = [
  { label: 'All', value: undefined },
  ...STATUSES.map(s => ({ label: s.label, value: s.value })),
]

export default function Tracker() {
  const [apps, setApps] = useState<Application[]>([])
  const [filter, setFilter] = useState<string | undefined>(undefined)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    listApplications(filter)
      .then(setApps)
      .finally(() => setLoading(false))
  }, [filter])

  function handleStatusChange(updated: Application) {
    setApps(prev => prev.map(a => a.id === updated.id ? updated : a))
  }

  async function handleDelete(id: number) {
    await deleteApplication(id)
    setApps(prev => prev.filter(a => a.id !== id))
  }

  return (
    <div className="flex-1 flex flex-col h-full">
      {/* Header */}
      <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <ClipboardList size={20} className="text-blue-400" />
          <div>
            <h1 className="text-white font-semibold">Application Tracker</h1>
            <p className="text-slate-500 text-xs">{apps.length} application{apps.length !== 1 ? 's' : ''}</p>
          </div>
        </div>
        {/* Filter pills */}
        <div className="flex gap-1 bg-slate-800 rounded-lg p-1">
          {FILTER_OPTIONS.map(opt => (
            <button
              key={opt.label}
              onClick={() => setFilter(opt.value)}
              className={`px-3 py-1 rounded-md text-xs font-medium transition-colors
                ${filter === opt.value ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-slate-200'}`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      <div className="flex-1 overflow-auto px-6 py-4">
        {loading ? (
          <div className="flex items-center justify-center h-40 text-slate-500 text-sm">Loading…</div>
        ) : apps.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-40 gap-2 text-slate-600">
            <ClipboardList size={36} />
            <p className="text-sm">No applications yet — save jobs from the Chat tab</p>
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-slate-500 text-xs border-b border-slate-800">
                <th className="text-left pb-3 pr-4 font-medium w-8">Score</th>
                <th className="text-left pb-3 pr-4 font-medium">Job</th>
                <th className="text-left pb-3 pr-4 font-medium hidden md:table-cell">Platform</th>
                <th className="text-left pb-3 pr-4 font-medium">Status</th>
                <th className="text-left pb-3 pr-4 font-medium hidden lg:table-cell">Notes</th>
                <th className="text-left pb-3 pr-4 font-medium hidden md:table-cell">Saved</th>
                <th className="pb-3 w-8" />
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {apps.map(app => (
                <tr key={app.id} className="group hover:bg-slate-800/30 transition-colors">
                  <td className="py-3 pr-4">
                    <ScoreRing score={app.score} />
                  </td>
                  <td className="py-3 pr-4">
                    <a
                      href={app.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="font-medium text-white hover:text-blue-400 transition-colors flex items-center gap-1.5 group/link"
                    >
                      {app.title}
                      <ExternalLink size={11} className="opacity-0 group-hover/link:opacity-100 transition-opacity" />
                    </a>
                    <span className="text-slate-500 text-xs">{app.company}{app.location ? ` · ${app.location}` : ''}</span>
                    {app.recommendation && (
                      <span className={`ml-2 text-xs font-medium ${SCORE_COLORS[app.recommendation] ?? ''}`}>
                        {app.recommendation}
                      </span>
                    )}
                  </td>
                  <td className="py-3 pr-4 hidden md:table-cell">
                    <span className="capitalize text-slate-400 text-xs">{app.platform || '—'}</span>
                  </td>
                  <td className="py-3 pr-4">
                    <StatusDropdown app={app} onChange={handleStatusChange} />
                  </td>
                  <td className="py-3 pr-4 hidden lg:table-cell">
                    <NotesCell app={app} />
                  </td>
                  <td className="py-3 pr-4 hidden md:table-cell">
                    <span className="text-slate-500 text-xs whitespace-nowrap">
                      {new Date(app.saved_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })}
                    </span>
                  </td>
                  <td className="py-3">
                    <button
                      onClick={() => handleDelete(app.id)}
                      className="opacity-0 group-hover:opacity-100 text-slate-600 hover:text-red-400 transition-all"
                    >
                      <Trash2 size={14} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
