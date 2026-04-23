import type { UserProfile, SearchResponse, Platform, DatePosted, RemoteType, Application } from '../types'

const BASE = 'http://localhost:8000'

export async function searchJobs(params: {
  query: string
  location: string
  platform: Platform
  remote?: RemoteType
  datePosted?: DatePosted
  maxResults?: number
  profile: UserProfile
}): Promise<SearchResponse> {
  const res = await fetch(`${BASE}/jobs/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      platform: params.platform,
      query: params.query,
      location: params.location,
      remote: params.remote ?? null,
      date_posted: params.datePosted ?? null,
      max_results: params.maxResults ?? 10,
      fetch_descriptions: true,
      profile: {
        target_roles: params.profile.targetRoles,
        skills: params.profile.skills,
        experience_years: params.profile.experienceYears,
        location: params.profile.location,
        remote_preference: params.profile.remotePreference,
        summary: params.profile.summary,
        salary_min: params.profile.salaryMin,
        salary_max: params.profile.salaryMax,
      },
    }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail ?? `Request failed: ${res.status}`)
  }
  const data = await res.json()
  // Map snake_case response to camelCase
  return {
    total: data.total,
    results: data.results.map((j: any) => ({
      title: j.title,
      company: j.company,
      location: j.location,
      url: j.url,
      platform: j.platform,
      description: j.description,
      postedDate: j.posted_date,
      employmentType: j.employment_type,
      seniorityLevel: j.seniority_level,
      scrapedAt: j.scraped_at,
      score: j.score,
      reasoning: j.reasoning,
      matchingSkills: j.matching_skills,
      missingSkills: j.missing_skills,
      recommendation: j.recommendation,
    })),
  }
}

export async function getSessionStatus(platform: string): Promise<{ saved: boolean; login_in_progress: boolean }> {
  const res = await fetch(`${BASE}/sessions/${platform}/status`)
  return res.json()
}

export async function startSession(platform: string): Promise<void> {
  await fetch(`${BASE}/sessions/${platform}/save/start`, { method: 'POST' })
}

export async function completeSession(platform: string): Promise<{ cookie_count: number }> {
  const res = await fetch(`${BASE}/sessions/${platform}/save/complete`, { method: 'POST' })
  return res.json()
}

export async function saveJob(job: {
  title: string
  company: string
  location: string
  url: string
  platform: string
  score?: number
  recommendation?: string
  description?: string
}): Promise<{ id: number; already_saved: boolean }> {
  const res = await fetch(`${BASE}/tracker/save`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(job),
  })
  if (!res.ok) throw new Error('Failed to save job')
  return res.json()
}

export async function listApplications(status?: string): Promise<Application[]> {
  const url = status ? `${BASE}/tracker?status=${status}` : `${BASE}/tracker`
  const res = await fetch(url)
  if (!res.ok) throw new Error('Failed to load applications')
  return res.json()
}

export async function updateStatus(id: number, status: string, notes?: string): Promise<Application> {
  const res = await fetch(`${BASE}/tracker/${id}/status`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status, notes }),
  })
  if (!res.ok) throw new Error('Failed to update status')
  return res.json()
}

export async function updateNotes(id: number, notes: string): Promise<void> {
  await fetch(`${BASE}/tracker/${id}/notes`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ notes }),
  })
}

export async function deleteApplication(id: number): Promise<void> {
  await fetch(`${BASE}/tracker/${id}`, { method: 'DELETE' })
}

export async function sendChatMessage(params: {
  message: string
  platform: string
  datePosted?: string
  maxResults?: number
  profile: UserProfile
  lastJobs?: import('../types').ScoredJob[]
}): Promise<import('../types').ChatApiResponse> {
  const res = await fetch(`${BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message: params.message,
      platform: params.platform,
      date_posted: params.datePosted ?? null,
      max_results: params.maxResults ?? 10,
      profile: {
        target_roles: params.profile.targetRoles,
        skills: params.profile.skills,
        experience_years: params.profile.experienceYears,
        location: params.profile.location,
        remote_preference: params.profile.remotePreference,
        summary: params.profile.summary,
        salary_min: params.profile.salaryMin,
        salary_max: params.profile.salaryMax,
      },
      last_jobs: (params.lastJobs ?? []).map(j => ({
        title: j.title,
        company: j.company,
        location: j.location,
        url: j.url,
        platform: j.platform,
        score: j.score,
        recommendation: j.recommendation,
        description: j.description,
      })),
    }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail ?? `Request failed: ${res.status}`)
  }
  const data = await res.json()
  return {
    type: data.type,
    content: data.content,
    savedCount: data.saved_count ?? 0,
    applications: data.applications ?? [],
    jobs: (data.jobs ?? []).map((j: any) => ({
      title: j.title,
      company: j.company,
      location: j.location,
      url: j.url,
      platform: j.platform,
      description: j.description,
      postedDate: j.posted_date,
      employmentType: j.employment_type,
      seniorityLevel: j.seniority_level,
      scrapedAt: j.scraped_at,
      score: j.score,
      reasoning: j.reasoning,
      matchingSkills: j.matching_skills,
      missingSkills: j.missing_skills,
      recommendation: j.recommendation,
    })),
  }
}
