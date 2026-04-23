import { useState, useEffect } from 'react'
import { Save, Plus, X, CheckCircle } from 'lucide-react'
import type { UserProfile } from '../types'

const DEFAULT_PROFILE: UserProfile = {
  targetRoles: [],
  skills: [],
  experienceYears: 0,
  location: '',
  remotePreference: 'any',
  summary: '',
  salaryMin: 0,
  salaryMax: 0,
}

function TagInput({ label, values, onChange, placeholder }: {
  label: string
  values: string[]
  onChange: (v: string[]) => void
  placeholder: string
}) {
  const [input, setInput] = useState('')

  function add() {
    const val = input.trim()
    if (val && !values.includes(val)) onChange([...values, val])
    setInput('')
  }

  function remove(v: string) {
    onChange(values.filter(x => x !== v))
  }

  return (
    <div>
      <label className="block text-sm font-medium text-slate-300 mb-2">{label}</label>
      <div className="flex flex-wrap gap-2 mb-2">
        {values.map(v => (
          <span key={v} className="flex items-center gap-1 bg-blue-600/20 text-blue-400 border border-blue-500/30 px-2 py-1 rounded-lg text-sm">
            {v}
            <button onClick={() => remove(v)} className="hover:text-white transition-colors">
              <X size={12} />
            </button>
          </span>
        ))}
      </div>
      <div className="flex gap-2">
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); add() } }}
          placeholder={placeholder}
          className="flex-1 bg-slate-800 border border-slate-700 text-slate-200 placeholder-slate-500 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500 transition-colors"
        />
        <button onClick={add} className="bg-slate-700 hover:bg-slate-600 text-slate-300 rounded-lg px-3 py-2 transition-colors">
          <Plus size={16} />
        </button>
      </div>
    </div>
  )
}

export default function Profile() {
  const [profile, setProfile] = useState<UserProfile>(DEFAULT_PROFILE)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    const raw = localStorage.getItem('lazyapply_profile')
    if (raw) setProfile(JSON.parse(raw))
  }, [])

  function save() {
    localStorage.setItem('lazyapply_profile', JSON.stringify(profile))
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  function set<K extends keyof UserProfile>(key: K, value: UserProfile[K]) {
    setProfile(prev => ({ ...prev, [key]: value }))
  }

  return (
    <div className="flex-1 flex flex-col h-full">
      <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
        <div>
          <h1 className="text-white font-semibold">Your Profile</h1>
          <p className="text-slate-500 text-xs">Used to score jobs against your background</p>
        </div>
        <button
          onClick={save}
          className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white text-sm px-4 py-2 rounded-lg transition-colors"
        >
          {saved ? <CheckCircle size={16} /> : <Save size={16} />}
          {saved ? 'Saved!' : 'Save'}
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-6 py-6 space-y-6 max-w-2xl">
        <TagInput
          label="Target Roles"
          values={profile.targetRoles}
          onChange={v => set('targetRoles', v)}
          placeholder="e.g. Software Engineer"
        />

        <TagInput
          label="Skills"
          values={profile.skills}
          onChange={v => set('skills', v)}
          placeholder="e.g. Python, FastAPI, React"
        />

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">Experience (years)</label>
            <input
              type="number"
              min={0}
              value={profile.experienceYears}
              onChange={e => set('experienceYears', Number(e.target.value))}
              className="w-full bg-slate-800 border border-slate-700 text-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500 transition-colors"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">Location</label>
            <input
              value={profile.location}
              onChange={e => set('location', e.target.value)}
              placeholder="e.g. Bangalore"
              className="w-full bg-slate-800 border border-slate-700 text-slate-200 placeholder-slate-500 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500 transition-colors"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-300 mb-2">Remote Preference</label>
          <div className="flex gap-2">
            {(['any', 'remote', 'hybrid', 'onsite'] as const).map(opt => (
              <button
                key={opt}
                onClick={() => set('remotePreference', opt)}
                className={`px-4 py-2 rounded-lg text-sm font-medium capitalize transition-colors
                  ${profile.remotePreference === opt
                    ? 'bg-blue-600 text-white'
                    : 'bg-slate-800 text-slate-400 hover:text-slate-200 border border-slate-700'}`}
              >
                {opt}
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">Min Salary (₹ LPA)</label>
            <input
              type="number"
              min={0}
              value={profile.salaryMin || ''}
              onChange={e => set('salaryMin', Number(e.target.value))}
              placeholder="0"
              className="w-full bg-slate-800 border border-slate-700 text-slate-200 placeholder-slate-500 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500 transition-colors"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">Max Salary (₹ LPA)</label>
            <input
              type="number"
              min={0}
              value={profile.salaryMax || ''}
              onChange={e => set('salaryMax', Number(e.target.value))}
              placeholder="0"
              className="w-full bg-slate-800 border border-slate-700 text-slate-200 placeholder-slate-500 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500 transition-colors"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-300 mb-2">Summary <span className="text-slate-500 font-normal">(optional)</span></label>
          <textarea
            value={profile.summary}
            onChange={e => set('summary', e.target.value)}
            placeholder="Brief description of your background and what you're looking for..."
            rows={3}
            className="w-full bg-slate-800 border border-slate-700 text-slate-200 placeholder-slate-500 rounded-lg px-3 py-2 text-sm resize-none focus:outline-none focus:border-blue-500 transition-colors"
          />
        </div>
      </div>
    </div>
  )
}
