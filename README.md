# 🤖 JobAgent — Your Personal AI Job Hunting Assistant

> Configure once. Let it hunt. You just show up to the interview.

[![Status](https://img.shields.io/badge/status-in%20development-yellow)](https://github.com)
[![Stack](https://img.shields.io/badge/stack-React%20%7C%20Python%20%7C%20FastAPI-blue)](https://github.com)
[![AI](https://img.shields.io/badge/AI-Groq%20%7C%20Ollama-purple)](https://github.com)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Free](https://img.shields.io/badge/free-forever-brightgreen)](https://github.com)

---

## What is this?

JobAgent is a free, open-source AI-powered job hunting automation tool. You fill in your details once — your skills, target roles, location, salary range, and resume — and the agent does the rest.

It searches LinkedIn, Naukri.com, and Indeed on your behalf, scores each job against your profile, finds HR contact emails where possible, generates a tailored cold email or cover letter for each application, and tracks everything in a clean dashboard.

The only things left for you to do are the things only you can do — the call, the interview, the handshake.

---

## Features

- **Multi-platform job scraping** — LinkedIn, Naukri.com, Indeed (more coming)
- **Session-based login** — logs in once using your real account, saves session locally. Your credentials never leave your device.
- **AI job scoring** — each posting is scored against your profile so you only see relevant matches
- **HR email extraction** — AI parses job descriptions to find or infer recruiter contact details
- **Tailored outreach** — generates a unique cold email or cover letter per job, referencing the company and role specifically
- **Auto email dispatch** — optionally send emails automatically once you review and approve (opt-in only)
- **Application tracker** — dashboard showing every application, its status, dates, and follow-up reminders
- **Runs on a schedule** — set it to run daily or weekly, completely hands-off
- **Free AI scoring** — uses Groq's free tier (Llama 3.3 70b) for job scoring. No credit card required. Ollama supported for fully offline use.
- **Fully local** — no cloud, no subscription, no data leaving your machine

---

## How it works

```
User setup (one time)
        ↓
Scrape jobs → LinkedIn + Naukri + Indeed
        ↓
AI agent analyzes each posting
   → Match score vs your profile
   → Extract HR email if present
   → Parse key requirements
        ↓
Filter & shortlist based on your thresholds
        ↓
Generate tailored message per job
        ↓
Review → (optional) auto-dispatch email
        ↓
Track in dashboard → follow-up reminders
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React, Tailwind CSS |
| Backend | Python, FastAPI |
| Scraping | Playwright (browser automation) |
| Database | SQLite (local, no setup needed) |
| AI | Groq (free tier, Llama 3.3 70b) / Ollama (local, offline) |
| Email | Gmail API / SendGrid |
| Scheduler | APScheduler |

---

## Project Structure

```
job-agent/
├── frontend/          # React dashboard
│   └── src/
│       ├── pages/     # Onboarding, Dashboard, Tracker
│       └── components/
│
├── backend/           # Python + FastAPI
│   ├── scrapers/      # LinkedIn, Naukri, Indeed
│   ├── sessions/      # Playwright session manager
│   ├── ai/            # Scoring, email gen, HR extraction
│   ├── email/         # Gmail API / SendGrid
│   └── scheduler/     # Automated run config
│
├── data/              # Local SQLite DB + encrypted sessions
└── docs/              # Setup guides, architecture
```

---

## Getting Started

> ⚠️ Project is currently in active development. Setup instructions will be added as modules are completed.

### Prerequisites

- Node.js 18+
- Python 3.10+
- Playwright (`pip install playwright && playwright install`)
- Ollama (optional, for local AI) — [ollama.com](https://ollama.com)

### Setup (coming soon)

```bash
git clone https://github.com/yourusername/job-agent.git
cd job-agent

# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend
cd ../frontend
npm install
npm run dev
```

---

## Roadmap

- [x] Project architecture & planning
- [x] Session manager (Playwright login + cookie storage)
- [x] LinkedIn scraper
- [ ] Naukri.com scraper
- [ ] Indeed scraper
- [x] AI job scoring layer (Groq — Llama 3.3 70b, free tier)
- [ ] HR email extraction
- [ ] Tailored message generation
- [ ] Email dispatch (Gmail API)
- [ ] React dashboard
- [ ] Application tracker
- [ ] Scheduler (daily/weekly runs)
- [ ] Chrome extension (stretch goal)

---

## Privacy & Security

This tool is designed with privacy as a core principle:

- **Sessions are stored locally** on your machine, encrypted
- **No credentials are ever sent** to any server
- **No telemetry, no analytics, no cloud sync**
- You own your data entirely

---

## Why I built this

Job hunting is repetitive, time-consuming, and demoralising at scale. Sending 50 applications manually — each needing a tailored message — takes days. This tool removes all the mechanical work so you can focus on what actually matters: preparing well and showing up.

I built this as a personal project while transitioning from frontend to full-stack development. If it helps even a few people land jobs faster, that's more than enough.

---

## Contributing

Contributions are welcome. If you find a bug, have a feature idea, or want to add support for a new job platform, feel free to open an issue or a PR.

---

## License

MIT — free to use, modify, and distribute.

---

<p align="center">Built with curiosity by <a href="https://github.com/surajbhat0813">@surajbhat0813</a> · Star it if it helps you ⭐</p>
