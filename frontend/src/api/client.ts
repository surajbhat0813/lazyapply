import type { UserProfile, SearchResponse, Platform, DatePosted, RemoteType } from '../types'

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
