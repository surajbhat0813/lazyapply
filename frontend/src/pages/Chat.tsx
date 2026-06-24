import { useState, useRef, useEffect } from 'react'
import { Send, Loader2, BriefcaseIcon, AlertTriangle, Settings, BookmarkCheck } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { sendChatMessage, getSessionStatus } from '../api/client'
import JobCard from '../components/JobCard'
import type { ChatMessage, Platform, UserProfile, ScoredJob } from '../types'

const PLATFORMS: Platform[] = ['linkedin', 'naukri', 'indeed']
const DATE_OPTIONS = [
  { label: 'Any time', value: undefined },
  { label: 'Today', value: 'day' },
  { label: 'This week', value: 'week' },
  { label: 'This month', value: 'month' },
] as const

function loadProfile(): UserProfile | null {
  try {
    const raw = localStorage.getItem('lazyapply_profile')
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

function TypingDots() {
  return (
    <div className="flex gap-1 items-center px-4 py-3">
      {[0, 1, 2].map(i => (
        <span
          key={i}
          className="w-2 h-2 bg-slate-500 rounded-full animate-bounce"
          style={{ animationDelay: `${i * 0.15}s` }}
        />
      ))}
    </div>
  )
}

function renderContent(content: string) {
  return content.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
}

export default function Chat() {
  const navigate = useNavigate()
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '0',
      role: 'assistant',
      content: "Hi! I'm your job hunting assistant. Tell me what kind of job you're looking for, ask me to save results, check your tracker, or anything else.",
      timestamp: new Date(),
    },
  ])
  const [input, setInput] = useState('')
  const [platform, setPlatform] = useState<Platform>('naukri')
  const [datePosted, setDatePosted] = useState<string | undefined>(undefined)
  const [loading, setLoading] = useState(false)
  const [sessionSaved, setSessionSaved] = useState<boolean | null>(null)
  const [lastJobs, setLastJobs] = useState<ScoredJob[]>([])
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    getSessionStatus(platform)
      .then(s => setSessionSaved(s.saved))
      .catch(() => setSessionSaved(false))
  }, [platform])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function send() {
    const query = input.trim()
    if (!query || loading) return

    const profile = loadProfile()
    if (!profile) {
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        role: 'assistant',
        content: 'No profile found. Please go to the Profile tab and fill in your details first.',
        timestamp: new Date(),
      }])
      return
    }

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: query,
      timestamp: new Date(),
    }
    const loadingMsg: ChatMessage = {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: '',
      loading: true,
      timestamp: new Date(),
    }

    setMessages(prev => [...prev, userMsg, loadingMsg])
    setInput('')
    setLoading(true)

    try {
      const result = await sendChatMessage({
        message: query,
        platform,
        datePosted: datePosted as any,
        maxResults: 10,
        profile,
        lastJobs,
      })

      if (result.type === 'search' && result.jobs.length > 0) {
        setLastJobs(result.jobs)
      }

      setMessages(prev => prev.map(m =>
        m.loading
          ? {
              ...m,
              loading: false,
              content: result.content,
              jobs: result.type === 'search' ? result.jobs : undefined,
              responseType: result.type,
            }
          : m
      ))
    } catch (err: any) {
      setMessages(prev => prev.map(m =>
        m.loading ? { ...m, loading: false, content: `Error: ${err.message}` } : m
      ))
    } finally {
      setLoading(false)
    }
  }

  function handleKey(e: React.KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      send()
    }
  }

  return (
    <div className="flex-1 flex flex-col h-full">
      {/* Header */}
      <div className="px-6 py-4 border-b border-slate-800 flex items-center gap-3">
        <BriefcaseIcon size={20} className="text-blue-400" />
        <div>
          <h1 className="text-white font-semibold">Job Search</h1>
          <p className="text-slate-500 text-xs">Search jobs, save results, or check your tracker</p>
        </div>
      </div>

      {/* Session warning */}
      {sessionSaved === false && (
        <div className="mx-6 mt-3 flex items-center justify-between gap-3 bg-yellow-500/10 border border-yellow-500/20 rounded-lg px-4 py-2.5">
          <div className="flex items-center gap-2 text-yellow-400 text-sm">
            <AlertTriangle size={15} />
            <span>No session for <strong className="capitalize">{platform}</strong> — results will be limited (guest mode)</span>
          </div>
          <button
            onClick={() => navigate('/settings')}
            className="flex items-center gap-1.5 text-xs bg-yellow-500/20 hover:bg-yellow-500/30 text-yellow-300 px-3 py-1.5 rounded-lg transition-colors whitespace-nowrap"
          >
            <Settings size={12} />
            Connect
          </button>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {messages.map(msg => (
          <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            {msg.role === 'assistant' ? (
              <div className="max-w-3xl w-full space-y-3">
                {msg.loading ? (
                  <div className="bg-slate-800 rounded-2xl rounded-tl-sm w-fit">
                    <TypingDots />
                  </div>
                ) : (
                  <>
                    {msg.content && (
                      <div className={`rounded-2xl rounded-tl-sm px-4 py-3 text-sm leading-relaxed
                        ${msg.responseType === 'saved'
                          ? 'bg-blue-600/20 border border-blue-500/30 text-blue-200'
                          : 'bg-slate-800 text-slate-200'}`}
                      >
                        {msg.responseType === 'saved' && (
                          <BookmarkCheck size={14} className="inline mr-1.5 text-blue-400" />
                        )}
                        <span dangerouslySetInnerHTML={{ __html: renderContent(msg.content) }} />
                        {msg.responseType === 'tracker_summary' && (
                          <button
                            onClick={() => navigate('/tracker')}
                            className="ml-2 text-xs text-blue-400 hover:text-blue-300 underline"
                          >
                            Open Tracker →
                          </button>
                        )}
                      </div>
                    )}
                    {msg.jobs && msg.jobs.length > 0 && (
                      <div className="space-y-2">
                        {msg.jobs.map((job, i) => <JobCard key={i} job={job} />)}
                      </div>
                    )}
                  </>
                )}
              </div>
            ) : (
              <div className="bg-blue-600 text-white rounded-2xl rounded-tr-sm px-4 py-3 text-sm max-w-lg">
                {msg.content}
              </div>
            )}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Input area */}
      <div className="px-6 py-4 border-t border-slate-800 space-y-3">
        <div className="flex gap-2 flex-wrap">
          <div className="flex gap-1 bg-slate-800 rounded-lg p-1">
            {PLATFORMS.map(p => (
              <button
                key={p}
                onClick={() => setPlatform(p)}
                className={`px-3 py-1 rounded-md text-xs font-medium transition-colors capitalize
                  ${platform === p ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-slate-200'}`}
              >
                {p}
              </button>
            ))}
          </div>
          <div className="flex gap-1 bg-slate-800 rounded-lg p-1">
            {DATE_OPTIONS.map(opt => (
              <button
                key={opt.label}
                onClick={() => setDatePosted(opt.value)}
                className={`px-3 py-1 rounded-md text-xs font-medium transition-colors
                  ${datePosted === opt.value ? 'bg-slate-600 text-white' : 'text-slate-400 hover:text-slate-200'}`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        <div className="flex gap-3">
          <textarea
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKey}
            placeholder='Search for jobs, or say "save the first one", "show my tracker"…'
            rows={2}
            className="flex-1 bg-slate-800 border border-slate-700 text-slate-200 placeholder-slate-500 rounded-xl px-4 py-3 text-sm resize-none focus:outline-none focus:border-blue-500 transition-colors"
          />
          <button
            onClick={send}
            disabled={loading || !input.trim()}
            className="w-12 bg-blue-600 hover:bg-blue-500 disabled:opacity-40 disabled:cursor-not-allowed rounded-xl flex items-center justify-center transition-colors flex-shrink-0"
          >
            {loading ? <Loader2 size={18} className="animate-spin text-white" /> : <Send size={18} className="text-white" />}
          </button>
        </div>
      </div>
    </div>
  )
}
