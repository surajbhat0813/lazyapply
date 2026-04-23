import { useState, useEffect } from 'react'
import { CheckCircle, AlertCircle, Loader2, Trash2 } from 'lucide-react'
import { getSessionStatus, startSession, completeSession } from '../api/client'

const PLATFORMS = ['linkedin', 'naukri', 'indeed'] as const
type Platform = typeof PLATFORMS[number]

const PLATFORM_INFO: Record<Platform, { label: string; color: string; loginUrl: string }> = {
  linkedin: { label: 'LinkedIn', color: 'bg-blue-600', loginUrl: 'https://linkedin.com/login' },
  naukri: { label: 'Naukri', color: 'bg-orange-500', loginUrl: 'https://naukri.com/login' },
  indeed: { label: 'Indeed', color: 'bg-purple-600', loginUrl: 'https://in.indeed.com' },
}

type Status = { saved: boolean; login_in_progress: boolean } | null

export default function Settings() {
  const [statuses, setStatuses] = useState<Record<Platform, Status>>({
    linkedin: null,
    naukri: null,
    indeed: null,
  })
  const [pendingPlatform, setPendingPlatform] = useState<Platform | null>(null)
  const [loading, setLoading] = useState<Platform | null>(null)

  useEffect(() => {
    PLATFORMS.forEach(fetchStatus)
  }, [])

  async function fetchStatus(platform: Platform) {
    try {
      const status = await getSessionStatus(platform)
      setStatuses(prev => ({ ...prev, [platform]: status }))
    } catch {
      setStatuses(prev => ({ ...prev, [platform]: { saved: false, login_in_progress: false } }))
    }
  }

  async function handleStart(platform: Platform) {
    setLoading(platform)
    try {
      await startSession(platform)
      setPendingPlatform(platform)
      await fetchStatus(platform)
    } catch (e: any) {
      alert(`Failed to start login: ${e.message}`)
    } finally {
      setLoading(null)
    }
  }

  async function handleComplete(platform: Platform) {
    setLoading(platform)
    try {
      await completeSession(platform)
      setPendingPlatform(null)
      await fetchStatus(platform)
    } catch (e: any) {
      alert(`Failed to complete login: ${e.message}`)
    } finally {
      setLoading(null)
    }
  }

  return (
    <div className="flex-1 flex flex-col h-full">
      <div className="px-6 py-4 border-b border-slate-800">
        <h1 className="text-white font-semibold">Settings</h1>
        <p className="text-slate-500 text-xs">Manage your platform sessions</p>
      </div>

      <div className="flex-1 overflow-y-auto px-6 py-6 space-y-4 max-w-2xl">
        <p className="text-slate-400 text-sm">
          Connect your accounts so the scraper can search on your behalf. Your login is saved locally — nothing is sent to any server.
        </p>

        {PLATFORMS.map(platform => {
          const info = PLATFORM_INFO[platform]
          const status = statuses[platform]
          const isPending = pendingPlatform === platform
          const isLoading = loading === platform

          return (
            <div key={platform} className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-5">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className={`w-8 h-8 ${info.color} rounded-lg flex items-center justify-center text-white text-xs font-bold`}>
                    {info.label[0]}
                  </div>
                  <div>
                    <p className="text-white font-medium">{info.label}</p>
                    <div className="flex items-center gap-1 mt-0.5">
                      {status === null ? (
                        <span className="text-slate-500 text-xs">Checking...</span>
                      ) : status.saved ? (
                        <>
                          <CheckCircle size={12} className="text-green-400" />
                          <span className="text-green-400 text-xs">Session saved</span>
                        </>
                      ) : (
                        <>
                          <AlertCircle size={12} className="text-slate-500" />
                          <span className="text-slate-500 text-xs">Not connected</span>
                        </>
                      )}
                    </div>
                  </div>
                </div>

                {/* Naukri and Indeed don't require login */}
                {platform !== 'linkedin' && (
                  <span className="text-xs text-slate-500 bg-slate-700 px-2 py-1 rounded-lg">
                    Login optional
                  </span>
                )}
              </div>

              {!isPending ? (
                <button
                  onClick={() => handleStart(platform)}
                  disabled={isLoading}
                  className="w-full bg-slate-700 hover:bg-slate-600 disabled:opacity-50 text-slate-200 text-sm py-2 rounded-lg transition-colors flex items-center justify-center gap-2"
                >
                  {isLoading ? <Loader2 size={14} className="animate-spin" /> : null}
                  {status?.saved ? 'Re-connect' : 'Connect'} {info.label}
                </button>
              ) : (
                <div className="space-y-2">
                  <div className="bg-blue-600/10 border border-blue-500/20 rounded-lg px-4 py-3 text-sm text-blue-300">
                    A browser window has opened. Log in to {info.label}, then click <strong>Complete</strong> below.
                  </div>
                  <button
                    onClick={() => handleComplete(platform)}
                    disabled={isLoading}
                    className="w-full bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-sm py-2 rounded-lg transition-colors flex items-center justify-center gap-2"
                  >
                    {isLoading ? <Loader2 size={14} className="animate-spin" /> : <CheckCircle size={14} />}
                    Complete Login
                  </button>
                </div>
              )}
            </div>
          )
        })}

        <div className="border-t border-slate-800 pt-4">
          <h2 className="text-slate-300 font-medium text-sm mb-3">Danger Zone</h2>
          <button
            onClick={() => {
              if (confirm('Clear your saved profile?')) {
                localStorage.removeItem('lazyapply_profile')
              }
            }}
            className="flex items-center gap-2 text-red-400 hover:text-red-300 text-sm border border-red-400/20 hover:border-red-400/40 px-4 py-2 rounded-lg transition-colors"
          >
            <Trash2 size={14} />
            Clear saved profile
          </button>
        </div>
      </div>
    </div>
  )
}
