# AI Resume Builder — Claude Code Instructions

## What This Project Does
An agentic AI workflow that:
1. Researches the company you're applying to via web search (Tavily)
2. Tailors your resume to the job description using AI (Gemini via OpenRouter)
3. Self-evaluates and scores the resume 0-100
4. Rewrites weak sections until score reaches 85+
5. Uploads the final resume directly to Google Docs and gives you a shareable link

---

## CRITICAL: How to Generate a Resume

**When the user asks to generate, tailor, or create a resume for a job:**

ALWAYS run the script — never manually create or save a .md file:

```bash
source .venv/bin/activate
python scripts/tailor_resume.py --company "CompanyName" --role "Role Title"
```

Then paste the job description and press Ctrl+D.

The script handles everything: research -> tailor -> evaluate -> iterate -> Google Docs upload.
It will print the Google Docs link directly. That is the final deliverable — not a .md file.

**If the user does not specify a company, omit --company:**
```bash
python scripts/tailor_resume.py --role "AI Engineer"
```

**To upload the base resume to Google Docs without tailoring:**
```bash
python scripts/tailor_resume.py --no-tailor
```

---

## Project Files
```
resume-builder/
├── CLAUDE.md                  <- This file (Claude Code instructions)
├── resume.md                  <- Your base resume (edit with YOUR info)
├── .env.example               <- Environment variable template
├── .env                       <- Your secrets (never commit this)
├── google-client-secret.json  <- Google OAuth credentials (never commit)
└── scripts/
    ├── tailor_resume.py       <- Main agentic script
    ├── auth_google.py         <- One-time Google login setup
    ├── requirements.txt       <- Python dependencies
    └── setup.sh               <- One-command setup
```

---

## Setup (First Time Only)

### Step 1 — Run setup script
```bash
bash scripts/setup.sh
```
This creates a .venv, installs all Python dependencies, and copies .env.example to .env.

### Step 2 — Fill in your .env file
Open .env and add your API keys:
```
TAVILY_API_KEY=       # from tavily.com (free tier: 1000 searches/month)
OPENROUTER_API_KEY=   # from openrouter.ai/keys
```

### Step 3 — Enable Google Drive API
Go to this URL and click Enable:
```
https://console.cloud.google.com/apis/library/drive.googleapis.com
```

### Step 4 — Create Google OAuth credentials
1. Go to: https://console.cloud.google.com/apis/credentials
2. Click Create Credentials -> OAuth client ID -> Desktop app
3. Download the JSON file -> rename it to google-client-secret.json
4. Place it in the project root folder

### Step 5 — Authenticate Google (one time only)
```bash
source .venv/bin/activate
python scripts/auth_google.py
```
A browser window opens -> log in with your Google account -> done.
Your refresh token is saved to .env automatically.

---

## Editing Your Resume
Open resume.md and replace all [PLACEHOLDER] values with your real information.
Every placeholder is clearly labeled inside the file.

Key rules for resume content:
- Every bullet: action verb -> tool name -> outcome/metric
- Every project needs at least one number (%, time saved, volume processed)
- No em dashes use commas instead
- Your target role keyword must appear in the summary

---

## Daily Usage

```bash
source .venv/bin/activate

# Full agentic mode (researches company + tailors + self-evaluates -> Google Docs):
python scripts/tailor_resume.py --company "Zapier" --role "AI Automation Engineer"

# JD only, no company research:
python scripts/tailor_resume.py --role "AI Engineer"

# Convert base resume to Google Doc without tailoring:
python scripts/tailor_resume.py --no-tailor
```

Paste the job description when prompted -> press Ctrl+D -> get your Google Docs link.

---

## Cost Per Run
- Gemini Flash 2.0 via OpenRouter: ~$0.001-0.002 per tailoring run
- Tavily searches: free for first 1,000/month
- Google Drive: free

Total: less than $0.002 per resume.

---

## Troubleshooting
- **Missing sections in output** — the script auto-recovers from base resume
- **Google auth expired** — re-run python scripts/auth_google.py
- **Model not found error** — check OPENROUTER_MODEL in .env, use google/gemini-2.0-flash-001
- **Score stuck below 85** — max 3 iterations, uses best version achieved
- **google-client-secret.json not found** — follow Step 4 above
- **ModuleNotFoundError** — make sure you ran bash scripts/setup.sh and activated .venv
