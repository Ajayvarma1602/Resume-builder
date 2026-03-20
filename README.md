# AI Resume Builder

An agentic AI workflow that researches companies, tailors your resume to any job description, self-scores the output, and delivers a polished Google Doc — all in under 60 seconds.

Built with Python, OpenRouter (Gemini), Tavily, and Google Drive API.

---

## How It Works

```
You paste a job description
        ↓
[1] RESEARCH   — Tavily searches the company's tech stack + culture
        ↓
[2] TAILOR     — AI rewrites your resume to match the JD
        ↓
[3] EVALUATE   — AI scores the result 0–100 across 4 dimensions
        ↓
[4] ITERATE    — If score < 85, AI rewrites weak sections (max 3 attempts)
        ↓
[5] DELIVER    — Final resume uploaded to Google Docs, link returned
```

Cost per run: less than $0.002. Practically free.

---

## What You Need

| Service | Purpose | Cost |
|---|---|---|
| OpenRouter | AI model (Gemini Flash) | ~$0.001/run, free credits on sign-up |
| Tavily | Company web research | Free: 1,000 searches/month |
| Google Drive API | Output as Google Doc | Free |

---

## Setup (One Time)

### Prerequisites
- Python 3.10+ installed
- A Google account
- Terminal / command line access

---

### Step 1 — Download and open the project

Unzip the project folder. Open your terminal and navigate to it:

```bash
cd path/to/resume-builder
```

---

### Step 2 — Run the setup script

```bash
bash scripts/setup.sh
```

This will:
- Create a Python virtual environment at `.venv/`
- Install all required packages
- Copy `.env.example` to `.env`

---

### Step 3 — Get your API keys

**OpenRouter** (required — powers the AI):
1. Go to https://openrouter.ai/keys
2. Sign up (free credits included)
3. Create a new API key
4. Copy it into `.env` next to `OPENROUTER_API_KEY=`

**Tavily** (optional — enables company research):
1. Go to https://tavily.com
2. Sign up for the free plan (1,000 searches/month)
3. Copy your API key into `.env` next to `TAVILY_API_KEY=`

If you skip Tavily, the script still works — it just tailors from the job description alone without company context.

---

### Step 4 — Set up Google Drive (for Google Docs output)

**4a. Enable the Google Drive API:**
1. Go to https://console.cloud.google.com
2. Create a new project (or use an existing one)
3. Search for "Google Drive API" and click Enable

**4b. Create OAuth credentials:**
1. Go to https://console.cloud.google.com/apis/credentials
2. Click **Create Credentials** → **OAuth client ID**
3. Application type: **Desktop app**
4. Give it any name (e.g. "Resume Builder")
5. Click **Create**
6. Click **Download JSON**
7. Rename the downloaded file to `google-client-secret.json`
8. Move it into the project root folder (same folder as CLAUDE.md)

**4c. Configure the OAuth consent screen (if prompted):**
1. Go to https://console.cloud.google.com/apis/auth/consent
2. Select **External** user type
3. Fill in App name (anything) and your email
4. Add your email under "Test users"
5. Save and continue through the rest

**4d. Authenticate (one time only):**
```bash
source .venv/bin/activate
python scripts/auth_google.py
```

A browser window will open. Log in with your Google account. When you see "Authentication successful", close the browser. Your refresh token is saved to `.env` automatically — you never need to do this again.

---

### Step 5 — Add your resume

Open `resume.md` and replace every `[PLACEHOLDER]` with your real information.

Tips:
- Every bullet should follow the format: **action verb → tool → outcome with metric**
- Include at least one number in every project (%, hours saved, volume, speed)
- Keep the section structure intact — the AI depends on it
- Do not use em dashes (—) — use commas instead

---

## Using It

Activate your virtual environment first (every session):

```bash
source .venv/bin/activate
```

**Full agentic mode** (researches company + tailors + evaluates → Google Docs):
```bash
python scripts/tailor_resume.py --company "Zapier" --role "AI Automation Engineer"
```

**JD-only mode** (no company research):
```bash
python scripts/tailor_resume.py --role "AI Engineer"
```

**Base resume to Google Docs** (no tailoring):
```bash
python scripts/tailor_resume.py --no-tailor
```

In all cases: paste your job description when prompted, then press **Ctrl+D** (Mac/Linux) or **Ctrl+Z then Enter** (Windows).

The script will print a Google Docs link. Open it, then go to **File → Download → PDF Document** when you're ready to apply.

---

## Using With Claude Code

If you have Claude Code installed, you can drop this whole folder into it and just talk to it:

```
"Generate a resume for this job at [Company], role [Title]: [paste JD]"
```

Claude Code reads CLAUDE.md and knows to run the script and return a Google Docs link — not a markdown file.

To install Claude Code: https://claude.ai/code

---

## Customizing the AI Model

By default the script uses `google/gemini-2.0-flash-001` via OpenRouter — fast and extremely cheap.

To switch models, edit `OPENROUTER_MODEL` in your `.env`:

```
OPENROUTER_MODEL=anthropic/claude-haiku-4-5-20251001
OPENROUTER_MODEL=openai/gpt-4o-mini
OPENROUTER_MODEL=google/gemini-2.0-flash-001
```

Browse all available models at https://openrouter.ai/models

---

## Customizing the Prompts

The resume tailoring prompts are in `scripts/tailor_resume.py` starting at line 47.

- `TAILOR_PROMPT` — controls how the resume is rewritten for a JD
- `EVALUATE_PROMPT` — controls how the resume is scored 0–100
- `IMPROVE_PROMPT` — controls how weak sections are rewritten

Edit the "My context" section in `TAILOR_PROMPT` to add your personal pitch — who you are, why you're reaching out, what value you bring. This makes the tailoring much more specific.

---

## Troubleshooting

**`ModuleNotFoundError`**
You forgot to activate the venv. Run `source .venv/bin/activate` first.

**`google-client-secret.json not found`**
Follow Step 4b above — download your OAuth credentials JSON and rename it.

**`Google auth expired`**
Refresh tokens expire if unused for 6 months. Re-run `python scripts/auth_google.py`.

**`OPENROUTER_API_KEY not set`**
Open `.env` and make sure the key is on the same line: `OPENROUTER_API_KEY=sk-or-...`

**`Score stuck below 85`**
The script runs up to 3 improvement iterations and uses the best version reached. A score of 75-84 still produces a solid tailored resume.

**Missing sections in output**
The script automatically detects missing sections and recovers them from your base `resume.md`. If this happens frequently, try a more capable model.

**Windows users**
Replace `source .venv/bin/activate` with `.venv\Scripts\activate`
Replace `Ctrl+D` with `Ctrl+Z then Enter` when pasting the job description.

---

## File Structure

```
resume-builder/
├── README.md                  <- You are here
├── CLAUDE.md                  <- Instructions for Claude Code
├── resume.md                  <- Your base resume (edit this)
├── .env.example               <- Environment variable template
├── .env                       <- Your secrets (auto-created, never commit)
├── google-client-secret.json  <- Google OAuth credentials (never commit)
└── scripts/
    ├── tailor_resume.py       <- Main agentic script (research + tailor + evaluate + upload)
    ├── auth_google.py         <- One-time Google login
    ├── requirements.txt       <- Python dependencies
    └── setup.sh               <- One-command environment setup
```

---

## Security Notes

- Never commit `.env` or `google-client-secret.json` to git
- Both files are listed in `.gitignore` by default
- Your Google refresh token allows write access to your Drive — keep it private
- OpenRouter and Tavily keys should be treated like passwords

---

## Questions or Issues?

If something is not working, double-check:
1. Did you run `bash scripts/setup.sh`?
2. Did you activate `.venv` with `source .venv/bin/activate`?
3. Are all keys filled in `.env` (not `.env.example`)?
4. Did you run `python scripts/auth_google.py` and complete the browser login?
5. Is `google-client-secret.json` in the project root (not in a subfolder)?

All 5 boxes checked and still stuck? Re-read Step 4 carefully — Google OAuth setup is the most common point of confusion.
