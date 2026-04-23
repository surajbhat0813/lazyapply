import { ExternalLink, CheckCircle, Clock, XCircle, Zap, AlertCircle } from 'lucide-react'
import type { ScoredJob } from '../types'

const PLATFORM_COLORS: Record<string, string> = {
  linkedin: 'bg-blue-600',
  naukri: 'bg-orange-500',
  indeed: 'bg-purple-600',
}

const REC_CONFIG = {
  apply: { icon: CheckCircle, color: 'text-green-400', bg: 'bg-green-400/10 border-green-400/20', label: 'Apply' },
  maybe: { icon: AlertCircle, color: 'text-yellow-400', bg: 'bg-yellow-400/10 border-yellow-400/20', label: 'Maybe' },
  skip: { icon: XCircle, color: 'text-red-400', bg: 'bg-red-400/10 border-red-400/20', label: 'Skip' },
}

function ScoreRing({ score }: { score: number }) {
  const color = score >= 80 ? '#4ade80' : score >= 50 ? '#facc15' : '#f87171'
  return (
    <div className="relative w-14 h-14 flex-shrink-0">
      <svg className="w-14 h-14 -rotate-90" viewBox="0 0 56 56">
        <circle cx="28" cy="28" r="22" fill="none" stroke="#1e293b" strokeWidth="6" />
        <circle
          cx="28" cy="28" r="22" fill="none"
          stroke={color} strokeWidth="6"
          strokeDasharray={`${(score / 100) * 138} 138`}
          strokeLinecap="round"
        />
      </svg>
      <span className="absolute inset-0 flex items-center justify-center text-sm font-bold text-white">
        {score}
      </span>
    </div>
  )
}

export default function JobCard({ job }: { job: ScoredJob }) {
  const rec = REC_CONFIG[job.recommendation] ?? REC_CONFIG.maybe
  const RecIcon = rec.icon

  return (
    <div className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-4 flex gap-4 hover:border-slate-600 transition-colors">
      <ScoreRing score={job.score} />

      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-2 mb-1">
          <div>
            <a
              href={job.url}
              target="_blank"
              rel="noreferrer"
              className="font-semibold text-white hover:text-blue-400 transition-colors flex items-center gap-1"
            >
              {job.title}
              <ExternalLink size={13} className="opacity-60" />
            </a>
            <p className="text-slate-400 text-sm">{job.company} · {job.location}</p>
          </div>
          <div className="flex items-center gap-2 flex-shrink-0">
            <span className={`text-xs px-2 py-0.5 rounded-full text-white ${PLATFORM_COLORS[job.platform] ?? 'bg-slate-600'}`}>
              {job.platform}
            </span>
            <span className={`flex items-center gap-1 text-xs px-2 py-0.5 rounded-full border ${rec.bg} ${rec.color}`}>
              <RecIcon size={11} />
              {rec.label}
            </span>
          </div>
        </div>

        <p className="text-slate-400 text-xs mb-2 leading-relaxed">{job.reasoning}</p>

        <div className="flex flex-wrap gap-3 text-xs">
          {job.matchingSkills.length > 0 && (
            <div className="flex items-center gap-1 flex-wrap">
              <Zap size={11} className="text-green-400" />
              {job.matchingSkills.map(s => (
                <span key={s} className="bg-green-400/10 text-green-400 border border-green-400/20 px-1.5 py-0.5 rounded">
                  {s}
                </span>
              ))}
            </div>
          )}
          {job.missingSkills.length > 0 && (
            <div className="flex items-center gap-1 flex-wrap">
              <Clock size={11} className="text-slate-500" />
              {job.missingSkills.slice(0, 3).map(s => (
                <span key={s} className="bg-slate-700 text-slate-400 border border-slate-600 px-1.5 py-0.5 rounded">
                  {s}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
