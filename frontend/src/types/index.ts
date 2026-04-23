export interface UserProfile {
  targetRoles: string[]
  skills: string[]
  experienceYears: number
  location: string
  remotePreference: 'remote' | 'hybrid' | 'onsite' | 'any'
  summary: string
  salaryMin: number
  salaryMax: number
}

export interface ScoredJob {
  title: string
  company: string
  location: string
  url: string
  platform: string
  description: string
  postedDate: string
  employmentType: string
  seniorityLevel: string
  scrapedAt: string
  score: number
  reasoning: string
  matchingSkills: string[]
  missingSkills: string[]
  recommendation: 'apply' | 'maybe' | 'skip'
}

export interface SearchResponse {
  total: number
  results: ScoredJob[]
}

export type Platform = 'linkedin' | 'naukri' | 'indeed'
export type DatePosted = 'day' | 'week' | 'month'
export type RemoteType = 'remote' | 'hybrid' | 'onsite'

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  jobs?: ScoredJob[]
  loading?: boolean
  timestamp: Date
}
