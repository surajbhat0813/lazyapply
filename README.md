# JobAgent — Your Personal AI Job Hunting Assistant

> Configure once. Let it hunt. You just show up to the interview.

[![Status](https://img.shields.io/badge/status-in%20development-yellow)](https://github.com)
[![Stack](https://img.shields.io/badge/stack-React%20%7C%20Python%20%7C%20FastAPI-blue)](https://github.com)
[![AI](https://img.shields.io/badge/AI-Groq%20%7C%20Llama%203.3%2070b-purple)](https://github.com)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Free](https://img.shields.io/badge/free-forever-brightgreen)](https://github.com)

---

## What is this?

JobAgent is a free, open-source AI-powered job hunting automation tool. You fill in your details once — your skills, target roles, location, salary range — and the agent does the rest.

It searches LinkedIn, Naukri.com, and Indeed on your behalf, scores each job 0–100 against your profile with AI reasoning, and presents results in a clean chatbot interface. No cloud, no subscription, no data leaving your machine.

---

## Features

### Working now
- **Multi-platform job scraping** — LinkedIn, Naukri.com, Indeed
- **AI job scoring** — each posting scored 0–100 against your profile with reasoning, matching/missing skills, and an apply/maybe/skip recommendation (powered by Groq — free tier, Llama 3.3 70b, no credit card)
- **Chatbot interface** — type what you're looking for in plain language; results appear inline with scores
- **Profile-driven matching** — set your target roles, skills, experience, location, and salary range once; every search uses it
- **Platform selector + date filter** — switch between LinkedIn/Naukri/Indeed and filter by today/this week/this month
- **Session manager** — connect LinkedIn from the Settings tab using your real browser; profile is saved locally so you stay logged in
- **Guest mode fallback** — Naukri and Indeed work without login; LinkedIn requires a session for full results
- **Session warning banner** — chat warns you when a platform session isn't connected, with a direct link to Settings

### Coming soon
- HR email extraction — AI parses job descriptions to find or infer recruiter contact details
- Tailored outreach — generates a unique cold email or cover letter per job
- Auto email dispatch — optionally send emails automatically after you review
- Application tracker — dashboard showing every application, its status, and follow-up reminders
- Runs on a schedule — set it to run daily or weekly, fully hands-off

---

## How it works

```
Fill in your profile (one time)
        ↓
Type what you're looking for in the chat
        ↓
Scraper fetches jobs → LinkedIn / Naukri / Indeed
        ↓
AI scores each posting against your profile
   → Match score 0–100
   → Matching skills (green) / Missing skills (gray)
   → Apply / Maybe / Skip recommendation
   → Reasoning summary
        ↓
Results appear in chat, ranked by score
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, TypeScript, Tailwind CSS, Vite |
| Backend | Python 3.10+, FastAPI, Uvicorn |
| Scraping | Playwright (persistent browser profiles) |
| AI Scoring | Groq API — Llama 3.3 70b (free tier) |
| Session storage | Persistent Playwright browser profiles (local) |
| Routing | react-router-dom |

---

## Project Structure

```
personal/
├── frontend/                  # React + TypeScript dashboard
│   └── src/
│       ├── pages/
│       │   ├── Chat.tsx       # Chatbot job search interface
│       │   ├── Profile.tsx    # User profile setup
│       │   └── Settings.tsx   # Platform session manager
│       ├── components/
│       │   ├── JobCard.tsx    # Score ring, skills, recommendation
│       │   └── Sidebar.tsx    # Navigation
│       ├── api/client.ts      # API calls to FastAPI backend
│       └── types/index.ts     # Shared TypeScript types
│
├── backend/                   # Python + FastAPI
│   ├── main.py                # App entry point + CORS config
│   ├── api/
│   │   ├── jobs.py            # POST /jobs/search
│   │   └── sessions.py        # Session status + connect endpoints
│   ├── scrapers/
│   │   ├── models.py          # Shared Job dataclass
│   │   ├── linkedin.py        # LinkedIn scraper (headless=False)
│   │   ├── naukri.py          # Naukri scraper (headless=True)
│   │   └── indeed.py          # Indeed scraper (headless=True)
│   ├── ai/
│   │   └── scorer.py          # Groq-powered job scoring
│   ├── sessions/
│   │   └── session_manager.py # Playwright persistent profile manager
│   └── requirements.txt
│
└── data/
    └── sessions/
        └── profiles/          # Persistent browser profiles (git-ignored)
            ├── linkedin/
            ├── naukri/
            └── indeed/
```

---

## Getting Started

### Prerequisites

- **Node.js 18+**
- **Python 3.10+**
- **Playwright** — `pip install playwright && playwright install chromium`
- **Groq API key** (free) — sign up at [console.groq.com](https://console.groq.com), create a key, it's free with generous limits (14,400 requests/day)

### 1. Clone the repo

```bash
git clone https://github.com/surajbhat0813/lazyapply.git
cd lazyapply
```

### 2. Backend setup

```bash
# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt

# Install Playwright browser
playwright install chromium

# Set your Groq API key
export GROQ_API_KEY=your_key_here
# To persist it, add the line above to your ~/.zshrc or ~/.bashrc

# Start the backend
uvicorn backend.main:app --reload
# Runs on http://localhost:8000
```

### 3. Frontend setup

```bash
cd frontend
npm install
npm run dev
# Runs on http://localhost:5173
```

### 4. Set up your profile

Open [http://localhost:5173](http://localhost:5173) and go to the **Profile** tab. Fill in:
- Target roles (e.g. "Software Engineer", "Frontend Developer")
- Your skills
- Years of experience, location, remote preference, salary range

This is saved to your browser's `localStorage` — nothing leaves your machine.

### 5. Connect LinkedIn (optional but recommended)

Go to the **Settings** tab and click **Connect** next to LinkedIn. A browser window will open — log in to your LinkedIn account normally. Once you're in, click **Done** in the Settings tab. Your session is saved locally as a persistent browser profile.

> Naukri and Indeed work in guest mode without login. LinkedIn requires a session for full search results.

### 6. Search for jobs

Go to the **Chat** tab, select a platform, optionally set a date filter, and type what you're looking for. Results are ranked by AI score.

---

## Configuration

| Variable | Where to set | Description |
|---|---|---|
| `GROQ_API_KEY` | Shell environment (`~/.zshrc`) | Required for AI scoring. Get a free key at console.groq.com |

> The frontend API base URL defaults to `http://localhost:8000`. To change it, edit `frontend/src/api/client.ts`.

---

## Roadmap

- [x] Project architecture & planning
- [x] Session manager (Playwright persistent browser profiles)
- [x] LinkedIn scraper
- [x] Naukri.com scraper
- [x] Indeed scraper
- [x] AI job scoring layer (Groq — Llama 3.3 70b, free tier)
- [x] FastAPI backend with jobs + sessions endpoints
- [x] React frontend — chatbot, profile, settings, job cards
- [ ] HR email extraction
- [ ] Tailored message generation
- [ ] Email dispatch (Gmail API)
- [ ] Application tracker
- [ ] Scheduler (daily/weekly runs)
- [ ] Chrome extension (stretch goal)

---

## Privacy & Security

- **Sessions are stored locally** as persistent Playwright browser profiles — nothing is sent to any server
- **Your Groq API key** is only used for scoring and stays on your machine
- **No telemetry, no analytics, no cloud sync**
- You own your data entirely

---

## Why I built this

Job hunting is repetitive, time-consuming, and demoralising at scale. Sending 50 applications manually — each needing a tailored message — takes days. This tool removes all the mechanical work so you can focus on what actually matters: preparing well and showing up.

---

## Contributing

Contributions are welcome. If you find a bug, have a feature idea, or want to add support for a new job platform, feel free to open an issue or a PR.

---

## License

MIT — free to use, modify, and distribute.

---

<p align="center">Built with curiosity by <a href="https://github.com/surajbhat0813">@surajbhat0813</a> · Star it if it helps you ⭐</p>
