#!/usr/bin/env python3
"""
AI Resume Agent — Agentic Resume Tailor
────────────────────────────────────────
A true agentic workflow:
  1. RESEARCH  — Tavily searches company tech stack + culture
  2. TAILOR    — LLM tailors resume using JD + research
  3. EVALUATE  — LLM scores the resume 0-100, identifies weak sections
  4. ITERATE   — Rewrites weak sections if score < 85 (max 3 loops)
  5. DELIVER   — Uploads to Google Drive, returns link + score

Usage:
    python scripts/tailor_resume.py --company "Zapier" --role "AI Automation Engineer"
    python scripts/tailor_resume.py --role "AI Engineer"          # no research
    python scripts/tailor_resume.py --no-tailor                   # base resume only
"""

import os
import sys
import re
import json
import argparse
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv

# ─── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent
RESUME_PATH = BASE_DIR / "resume.md"
ENV_PATH = BASE_DIR / ".env"

# ─── Config ───────────────────────────────────────────────────────────────────
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-pro-exp-03-25")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive.file"]
MAX_ITERATIONS = 10
SCORE_THRESHOLD = 85

# ─── Required sections — used to validate completeness of output ──────────────
REQUIRED_SECTIONS = [
    "## Professional Summary",
    "## Technical Skills",
    "## Professional Experience",
    "## Education",
    "## Certifications",
]

# ─── Prompts ──────────────────────────────────────────────────────────────────
TAILOR_PROMPT = """\
You are an expert ATS-optimized resume writer. Tailor the resume to score 95+/100 against the job description.

⛔ ABSOLUTE BAN — NEVER USE THESE UNDER ANY CIRCUMSTANCES:
CAS, Central Authentication Service, College of Arts and Sciences, HHSC, Health and Human Services, Okta, Keycloak, LDAP, OAuth, SAML, SSO, OpenID, .NET, Figma, Sketch, Adobe Photoshop, Adobe Illustrator, Adobe XD
These words must NEVER appear anywhere in the output — not in bullets, not in environment lines, not anywhere.
Also NEVER reference any external client names, government agencies, universities, or organizations (e.g., HHSC, CAS, NHS, DMV, etc.) — the candidate worked at Vyusoft, Capgemini, and Deloitte only.

CRITICAL OUTPUT RULES:
- Output the ENTIRE resume from start to finish — every section, every bullet, every line
- MUST include all 5 sections: Professional Summary, Technical Skills,
  Professional Experience (all 3 companies), Education, Certifications
- Never write "[rest unchanged]" or similar — always write everything in full
- Return ONLY raw markdown — no commentary, no preamble, no code fences, no ```markdown wrapper
- Max 2 pages worth of content — keep it concise

══════════════════════════════════════════════════
STEP 1 — SCAN THE JD BEFORE WRITING ANYTHING:
══════════════════════════════════════════════════
Read the JD and identify:
  A) MANDATORY skills/tools (required, must-have, listed first, or most emphasized)
  B) PREFERRED skills/tools
  C) EXACT keyword phrases used by the employer
  D) The job title in the JD

══════════════════════════════════════════════════
STEP 2 — MAP JD REQUIREMENTS TO COMPANIES:
══════════════════════════════════════════════════
Before writing any bullet, create this mental mapping:
  - List every JD requirement (tool, responsibility, skill)
  - Assign each one to Vyusoft OR Capgemini (cover ALL of them between these two companies)
  - Vyusoft gets ALL mandatory requirements + most preferred ones
  - Capgemini gets remaining mandatory requirements + other preferred ones
  - Every bullet in Vyusoft and Capgemini must trace back to a specific JD requirement
  - Deloitte gets only foundational/core skills (Java, SQL, REST APIs) — no niche JD tools

══════════════════════════════════════════════════
STEP 3 — APPLY RULES SECTION BY SECTION:
══════════════════════════════════════════════════

JOB TITLE:
- Adjust each company's job title to closely match the JD job title where reasonable
- Keep company names and dates exactly as-is

PROFESSIONAL SUMMARY — exactly 6-8 bullet points:
- Bold (**word**) every tool, technology, and JD keyword — Summary is a keyword showcase
- Each bullet: max 15 words, one tight, specific sentence
- Bullet 1: years of experience + JD job title keyword
- Every bullet directly addresses a JD mandatory or preferred requirement

TECHNICAL SKILLS:
- ONLY include skills explicitly mentioned in the JD — remove everything not in the JD
- Reorder categories so most JD-relevant appear first
- Every mandatory JD tool must appear here
- PRESERVE this exact format for every line: - **Category Name |** skill1, skill2, skill3
  The pipe | MUST stay inside the bold markers: **Category Name |**
  Never use a colon separator, never bold the skill values after the pipe

PROFESSIONAL EXPERIENCE — bullet count per company:
- Vyusoft: EXACTLY 6-8 bullets
- Capgemini: EXACTLY 6-8 bullets
- Deloitte: EXACTLY 5 bullets (first job, 2 years, junior scope but technically strong)
- BOLD (**word**) every JD keyword, tool, and technology — critical for ATS
- Strong action verb → **bold tool/tech** → specific outcome with real metric (%, ms, $, count, users)
- EVERY SINGLE BULLET must contain a quantified result — no exceptions
  Examples of GOOD bullets:
    ✓ "Optimized **WordPress** page load time by restructuring plugin calls, reducing average load by 35%."
    ✓ "Built **REST API** endpoints using **Spring Boot**, cutting data retrieval time by 28%."
    ✓ "Refactored **MySQL** queries with indexed joins, improving dashboard response time by 40%."
  Examples of BAD bullets (NEVER write these):
    ✗ "Participated in Agile Scrum meetings, providing input for project planning." (no metric, vague)
    ✗ "Assisted with website maintenance tasks." (no tool, no metric)
    ✗ "Worked with the team to implement features." (no tool, no metric)
- A bullet without a number is FORBIDDEN — rewrite it until it has one
- NEVER write process bullets like "participated in meetings", "assisted with", "attended" — every bullet must describe a SPECIFIC technical deliverable
- 1-2 sentences per bullet — second sentence only when it adds a concrete metric or technical detail
- Keep the Environment line exactly as-is after each role
- NEVER use: led, architected, spearheaded, oversaw (5 years experience)

CAREER PROGRESSION + JD ALIGNMENT — THIS IS THE MOST IMPORTANT RULE:

◆ Vyusoft (2024–Present) — ALMOST 100% JD MATCH:
  * Go through EVERY requirement in the JD one by one — write a bullet for each one
  * Use the JD's exact words, tools, and phrases in every bullet
  * Every mandatory AND preferred JD skill must appear in this company
  * The reader should feel Vyusoft IS the job being applied for
  * Verbs: designed, optimized, improved, delivered, managed, built, coordinated, enhanced, configured

◆ Capgemini (2021–2023) — ALMOST 100% JD MATCH (different project angle):
  * Same rule as Vyusoft — go through EVERY JD requirement and cover it here too
  * SAME JD tools and keywords are ALLOWED and REQUIRED in both companies
  * The difference is the PROJECT CONTEXT — different system, different domain, different outcome
  * Example: if Vyusoft used WordPress for an e-commerce platform, Capgemini used it for a CMS portal
  * Every mandatory JD skill must appear here as well
  * Verbs: developed, built, refactored, improved, implemented, delivered, integrated, configured

◆ Deloitte (2020–2021) — JUNIOR BUT TECHNICALLY STRONG (EXACTLY 5 bullets):
  * EXACTLY 5 bullets — first job, 2 years, smaller scope but real technical contributions
  * Each bullet must be SPECIFIC and TECHNICAL — name the actual tool, describe the actual output
  * Cover ~50% of JD foundational skills (Java, REST APIs, SQL, HTML/CSS and other common JD tools)
  * Metrics: realistic junior numbers (15–25% range) — EVERY bullet must have one quantified result
  * Good Deloitte bullet examples:
    ✓ "Developed **REST API** endpoints in **Java** to handle user authentication, reducing login errors by 18%."
    ✓ "Built **HTML5/CSS3** responsive pages for internal dashboard, improving mobile usability by 22%."
    ✓ "Wrote **SQL** queries to automate weekly reporting, saving 3 hours of manual work per week."
  * Verbs ONLY: implemented, developed, wrote, created, built, tested, configured, resolved, integrated
  * NEVER use: led, managed, directed, spearheaded, architected, oversaw, participated in, assisted

SELF-CHECK BEFORE OUTPUTTING:
- Read every JD requirement — is it in Vyusoft? Is it in Capgemini? If not, add it
- Count JD keywords in Vyusoft bullets — should match 90%+ of JD requirements
- Count JD keywords in Capgemini bullets — should match 90%+ of JD requirements

OUTPUT IS RESUME ONLY — no cover letter, no preamble, no sign-off
NO em dashes (—) in Experience or Summary bullets — use commas instead
EDUCATION & CERTIFICATIONS: copy these sections VERBATIM from the base resume — do NOT reword, reformat, or change any punctuation including em dashes

ACTION VERB VARIETY — STRICTLY ENFORCED:
  - No verb repeated more than ONCE across ALL bullets in the entire resume
  - Never repeat the same opening verb in consecutive bullets
  - No phrase or clause repeated across bullets (e.g. "responsive front-end layouts using HTML, CSS" must appear at most once)
  - Use a wide mix: Developed, Built, Implemented, Integrated, Optimized, Delivered,
    Improved, Refactored, Created, Configured, Deployed, Automated, Maintained, Resolved,
    Collaborated, Supported, Contributed, Wrote, Streamlined, Migrated, Enhanced, Tested,
    Coordinated, Managed, Reduced, Increased, Accelerated, Established, Transformed, Launched

NO BUZZWORDS OR CLICHÉS — never use: leveraged, utilized, spearheaded, synergized,
  best-in-class, cutting-edge, dynamic, robust, seamless, scalable solution, passionate,
  proven track record, results-driven, detail-oriented, team player, go-to, thought leader,
  innovative, transformative, game-changing, world-class, visionary, holistic, strategic
TECHNICAL SKILLS format — every line MUST follow this pattern exactly:
  - **Category Name |** skill1, skill2, skill3
  Use ONLY these category names (pick whichever are JD-relevant):
  Programming Languages | Backend Frameworks & Architecture | Frontend Technologies |
  CMS & Web Platforms | Databases & Data Stores | Messaging & Integration |
  Cloud & DevOps | Testing & Quality | Development Practices |
NEVER invent companies, degrees, certifications, or dates

TECHNOLOGY RESTRICTION — STRICTLY ENFORCED:
You may ONLY use technologies from this approved list (base resume) PLUS any tool explicitly named in the JD.
Approved base technologies:
  Java, JavaScript, SQL, Spring Boot, Spring MVC, REST APIs, Microservices, Hibernate, JPA, JDBC,
  React.js, Vue.js, HTML5, CSS3, SASS, WordPress, WordPress REST API, WooCommerce,
  PostgreSQL, MySQL, MongoDB, Apache Kafka, RabbitMQ,
  AWS (EC2, ECS, EKS, S3, RDS, Lambda, IAM, CloudWatch), Azure, Docker, GitLab CI, Git, CI/CD,
  JUnit, Mockito, Agile Scrum
DO NOT mention: CAS, College of Arts and Sciences, Okta, Keycloak, LDAP, OAuth, SAML, or ANY other tool not in the above list or the JD.
If a tool is not in the approved list AND not in the JD — do not use it, period.

COMPANY RESEARCH:
{research}

BASE RESUME:
{resume}

JOB DESCRIPTION:
{jd}
"""

EVALUATE_PROMPT = """\
You are a strict ATS and recruiter resume evaluator. Score 0-100.

SCORING CRITERIA:

1. MANDATORY KEYWORD COVERAGE (40 pts):
   - Identify every mandatory/required skill in the JD
   - Each mandatory skill present in the resume = full points for that item
   - Missing mandatory skills = heavy deduction (10 pts per missing mandatory skill)

2. SUMMARY QUALITY (20 pts):
   - 6-8 bullet points present?
   - Each bullet directly tied to a JD requirement with bold keywords?
   - Mentions years of experience and JD job title?

3. EXPERIENCE DEPTH (25 pts):
   - Each of the 3 companies has 6-8 bullets?
   - Every bullet has a quantified metric?
   - Bold keywords used throughout?
   - Mandatory JD tools appear in experience bullets?

4. OVERALL JD MATCH (15 pts):
   - Does the resume feel written specifically for THIS job?
   - Are the job titles aligned with the JD?
   - Are preferred skills included?

Return ONLY valid JSON:
{{"score": <0-100>, "weak": ["specific issue 1", "specific issue 2"], "suggestions": ["exact fix 1", "exact fix 2"]}}

TAILORED RESUME:
{resume}

JOB DESCRIPTION:
{jd}
"""

IMPROVE_PROMPT = """\
You are an expert resume writer. Your goal is to fix the resume until it scores 95+/100.

⛔ ABSOLUTE BAN — NEVER USE THESE UNDER ANY CIRCUMSTANCES:
CAS, Central Authentication Service, College of Arts and Sciences, HHSC, Health and Human Services, Okta, Keycloak, LDAP, OAuth, SAML, SSO, OpenID, .NET, Figma, Sketch, Adobe Photoshop, Adobe Illustrator, Adobe XD
These words must NEVER appear anywhere in the output — not in bullets, not in environment lines, not anywhere.
Also NEVER reference any external client names, government agencies, universities, or organizations (e.g., HHSC, CAS, NHS, DMV, etc.) — the candidate worked at Vyusoft, Capgemini, and Deloitte only.

CRITICAL OUTPUT RULES:
- Output the ENTIRE resume from start to finish — every section, every line
- MUST include all 5 sections: Professional Summary, Technical Skills,
  Professional Experience (all 3 companies), Education, Certifications
- Return ONLY raw markdown — no commentary, no code fences, no ```markdown wrapper

WHAT TO FIX — address every weak area and suggestion from the evaluation:
{weak}
{suggestions}

MANDATORY RULES (apply to everything you rewrite):
- Write bullets like a REAL professional — specific, technical, natural language, not AI-sounding
- BOLD (**word**) every JD keyword, tool, and technology in Summary and Experience bullets
- Vyusoft/Capgemini: EXACTLY 6-8 bullets each — EVERY bullet must have a number/metric
- Deloitte: EXACTLY 5 bullets — EVERY bullet must have a number/metric (15–25% range, realistic for junior). Each bullet must name a specific tool and describe a real technical deliverable. NEVER write "participated in meetings", "assisted with", or vague process bullets.
- A bullet with NO number is forbidden — rewrite it with a metric before outputting
- NEVER write process bullets ("participated in", "assisted with", "attended", "helped") — every bullet must describe a SPECIFIC technical action with a measurable outcome
- Summary: 6-8 bullets, max 15 words each, bold all keywords
- Technical Skills: only JD skills, exact format: **Category Name |** skill1, skill2 (pipe inside bold, never colon)
- Job titles: align to JD job title where appropriate
- JD ALIGNMENT — MOST IMPORTANT:
    Vyusoft (current): 90%+ JD match — go through every JD requirement, write a bullet for each, use exact JD phrases
    Capgemini (mid): 90%+ JD match — SAME JD tools allowed, different project context/domain, also cover every JD requirement
    Deloitte (first/junior): EXACTLY 5 bullets — junior scope but technically strong. Each bullet specific and quantified (15–25% metrics), foundational JD skills (Java, SQL, REST APIs, HTML/CSS), junior verbs (implemented/contributed/developed/wrote/built/tested), no senior verbs
- SELF-CHECK: scan every JD requirement — if missing from Vyusoft or Capgemini, add it immediately
- Each company has DISTINCT responsibilities — no repeating the same story across companies
- NEVER use: led, architected, spearheaded, oversaw
- Niche JD tools: appear in 1-2 companies only — NOT forced into all three
- No em dashes in Experience/Summary — use commas instead
- Education & Certifications: copy VERBATIM from base resume — do not change any punctuation
- Technical Skills: every line must be - **Category Name |** skill1, skill2 (pipe inside bold, no colon, no bold on skills)
- Keep Environment lines and company names/dates exactly as-is
- ACTION VERB VARIETY: no verb repeated more than twice, never repeat opening verb in consecutive bullets
- NO BUZZWORDS: never use leveraged, utilized, spearheaded, synergized, robust, seamless, cutting-edge, passionate, results-driven, detail-oriented, thought leader
- NEVER invent technologies. Only allowed tools: Java, JavaScript, SQL, Spring Boot, Spring MVC, REST APIs, Microservices, Hibernate, JPA, JDBC, React.js, Vue.js, HTML5, CSS3, SASS, WordPress, WooCommerce, PostgreSQL, MySQL, MongoDB, Kafka, RabbitMQ, AWS, Azure, Docker, GitLab CI, Git, CI/CD, JUnit, Mockito, Agile Scrum — PLUS any tool explicitly named in the JD. Never mention CAS, College of Arts and Sciences, Okta, Keycloak, LDAP, or anything else not in this list or the JD
- OUTPUT IS RESUME ONLY — no cover letter, no preamble, no sign-off

CURRENT RESUME:
{resume}

EVALUATION SCORE: {score}/100

JOB DESCRIPTION:
{jd}
"""

# ─── Prereq check ─────────────────────────────────────────────────────────────
def check_prerequisites():
    errors = []
    if not RESUME_PATH.exists():
        errors.append(f"resume.md not found at {RESUME_PATH}")
    if not os.getenv("OPENROUTER_API_KEY"):
        errors.append("OPENROUTER_API_KEY not set in .env")
    if not os.getenv("GOOGLE_REFRESH_TOKEN"):
        errors.append("Google not authenticated. Run: python scripts/auth_google.py")
    if not os.getenv("TAVILY_API_KEY"):
        print("⚠️   TAVILY_API_KEY not set — skipping company research\n")
    if errors:
        print("\n❌  Setup issues:\n")
        for e in errors:
            print(f"  • {e}\n")
        sys.exit(1)

# ─── Input ────────────────────────────────────────────────────────────────────
def get_job_description(args) -> str:
    if args.jd_file:
        return Path(args.jd_file).read_text().strip()
    print("Paste the job description below.")
    print("Press Enter then Ctrl+D when done:\n")
    return sys.stdin.read().strip()

# ─── Phase 1: Research ────────────────────────────────────────────────────────
def research_company(company: str, role: str) -> str:
    tavily_key = os.getenv("TAVILY_API_KEY", "")
    if not tavily_key or not company:
        return "No company research available."

    from tavily import TavilyClient
    client = TavilyClient(api_key=tavily_key)

    print(f"🔍  Researching {company}...")

    results = []
    queries = [
        f"{company} tech stack automation tools AI engineering",
        f"{company} {role} culture values engineering team",
    ]

    for q in queries:
        try:
            resp = client.search(query=q, max_results=3, search_depth="basic")
            for r in resp.get("results", []):
                results.append(r.get("content", "")[:400])
        except Exception:
            pass

    if not results:
        print(f"    No results found for {company}\n")
        return "No company research available."

    combined = "\n\n".join(results[:4])

    # Extract key signals with a quick LLM call
    from openai import OpenAI
    client_llm = OpenAI(
        base_url=OPENROUTER_BASE_URL,
        api_key=os.getenv("OPENROUTER_API_KEY"),
    )
    resp = client_llm.chat.completions.create(
        model=OPENROUTER_MODEL,
        max_tokens=300,
        messages=[{
            "role": "user",
            "content": f"From this research about {company}, extract in 3-4 bullet points: "
                       f"key technologies used, automation tools mentioned, culture/values, pain points.\n\n{combined}"
        }],
        extra_headers={"HTTP-Referer": "https://replixlab.com", "X-Title": "Resume Agent"}
    )
    summary = resp.choices[0].message.content.strip()

    # Print research summary
    for line in summary.split("\n")[:4]:
        if line.strip():
            print(f"    {line.strip()}")
    print()

    return summary

# ─── Strip markdown code fences from LLM output ──────────────────────────────
def strip_fences(text: str) -> str:
    text = re.sub(r'^```[a-zA-Z]*\n?', '', text.strip())
    text = re.sub(r'\n?```$', '', text.strip())
    return text.strip()

# ─── Ban list: remove any mention of these technologies post-LLM ──────────────
_BANNED_TECH = [
    r'\bCAS\b',
    r'Central Authentication Service',
    r'College of Arts and Sciences',
    r'\bHHSC\b',
    r'Health and Human Services',
    r'\bOkta\b',
    r'\bKeycloak\b',
    r'\bLDAP\b',
    r'\bSAML\b',
    r'\bOAuth\b',
    r'\bOAuth2\b',
    r'\bOpenID\b',
    r'\bSSO\b',
    r'\b\.NET\b',
    r'\bFigma\b',
    r'\bSketch\b',
    r'Adobe Photoshop',
    r'Adobe Illustrator',
    r'Adobe XD',
    r'Web Illustration Design',
    r'Experience Design',
    r'Mobile Design',
    r'UI/UX Principles',
    r'Web Layout Design',
    r'Web Accessibility Principles',
]

def sanitize_output(resume: str) -> str:
    """Remove any banned technology names that the LLM may have hallucinated."""
    lines = resume.split('\n')
    cleaned = []
    for line in lines:
        original = line
        for pattern in _BANNED_TECH:
            line = re.sub(pattern, '', line, flags=re.IGNORECASE)
        # Clean up leftover artifacts like ", , " or "( )" or double spaces
        line = re.sub(r',\s*,', ',', line)
        line = re.sub(r'\(\s*\)', '', line)
        line = re.sub(r',\s*$', '', line.rstrip())
        line = re.sub(r'^\s*,\s*', '', line)
        line = re.sub(r'  +', ' ', line)
        line = line.strip()
        # If the line was a bullet and is now basically empty after removal, skip it
        if original.startswith('- ') and len(line) < 5:
            continue
        cleaned.append(line)
    return '\n'.join(cleaned)

# ─── Completeness validator ───────────────────────────────────────────────────
def is_complete(resume: str) -> bool:
    """Check that all required sections are present in the output."""
    return all(section in resume for section in REQUIRED_SECTIONS)

def ensure_complete(tailored: str, base: str) -> str:
    """If output is missing sections, fall back to base resume for those sections."""
    if is_complete(tailored):
        return tailored
    missing = [s for s in REQUIRED_SECTIONS if s not in tailored]
    print(f"    ⚠️  Missing sections detected: {missing} — recovering from base...")
    # Append missing sections from base resume
    for section in missing:
        start = base.find(section)
        if start == -1:
            continue
        # Find the next section or end of file
        next_section_start = len(base)
        for other in REQUIRED_SECTIONS:
            pos = base.find(other, start + 1)
            if pos != -1 and pos < next_section_start:
                next_section_start = pos
        tailored += "\n\n" + base[start:next_section_start].strip()
    return tailored

# ─── Phase 2: Tailor ──────────────────────────────────────────────────────────
def tailor_resume(base_resume: str, jd: str, research: str) -> str:
    from openai import OpenAI
    client = OpenAI(
        base_url=OPENROUTER_BASE_URL,
        api_key=os.getenv("OPENROUTER_API_KEY"),
    )
    resp = client.chat.completions.create(
        model=OPENROUTER_MODEL,
        max_tokens=16000,
        messages=[{
            "role": "user",
            "content": TAILOR_PROMPT.format(resume=base_resume, jd=jd, research=research)
        }],
        extra_headers={"HTTP-Referer": "https://replixlab.com", "X-Title": "Resume Agent"}
    )
    result = sanitize_output(strip_fences(resp.choices[0].message.content))
    return ensure_complete(result, base_resume)

# ─── Phase 3: Evaluate ────────────────────────────────────────────────────────
def evaluate_resume(resume: str, jd: str) -> dict:
    from openai import OpenAI
    client = OpenAI(
        base_url=OPENROUTER_BASE_URL,
        api_key=os.getenv("OPENROUTER_API_KEY"),
    )
    resp = client.chat.completions.create(
        model=OPENROUTER_MODEL,
        max_tokens=512,
        messages=[{
            "role": "user",
            "content": EVALUATE_PROMPT.format(resume=resume, jd=jd)
        }],
        extra_headers={"HTTP-Referer": "https://replixlab.com", "X-Title": "Resume Agent"}
    )
    raw = resp.choices[0].message.content.strip()

    # Parse JSON safely
    try:
        # Strip markdown code fences if present
        raw = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()
        return json.loads(raw)
    except Exception:
        return {"score": 70, "weak": ["Could not parse evaluation"], "suggestions": []}

# ─── Phase 4: Improve ────────────────────────────────────────────────────────
def improve_resume(resume: str, evaluation: dict, jd: str) -> str:
    from openai import OpenAI
    client = OpenAI(
        base_url=OPENROUTER_BASE_URL,
        api_key=os.getenv("OPENROUTER_API_KEY"),
    )
    resp = client.chat.completions.create(
        model=OPENROUTER_MODEL,
        max_tokens=16000,
        messages=[{
            "role": "user",
            "content": IMPROVE_PROMPT.format(
                resume=resume,
                jd=jd,
                score=evaluation.get("score", "?"),
                weak="\n".join(f"  - {w}" for w in evaluation.get("weak", [])),
                suggestions="\n".join(f"  - {s}" for s in evaluation.get("suggestions", []))
            )
        }],
        extra_headers={"HTTP-Referer": "https://replixlab.com", "X-Title": "Resume Agent"}
    )
    result = sanitize_output(strip_fences(resp.choices[0].message.content))
    return ensure_complete(result, resume)

# ─── Markdown → HTML ──────────────────────────────────────────────────────────
# All styles are INLINE — Google Docs ignores <style> blocks on HTML import.

def inline_bold(text: str) -> str:
    return re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)

def strip_bold(text: str) -> str:
    """Remove **markers** entirely — used where bold is not wanted."""
    return re.sub(r'\*\*(.*?)\*\*', r'\1', text)

def _is_bold_pipe(s: str) -> bool:
    """True if line is a paragraph-level **bold** | text pattern (not a list item)."""
    return bool(re.match(r'^\*\*.+?\*\*\s*\|', s)) and not s.startswith('- ')

# ── Inline style constants ────────────────────────────────────────────────────
_FONT   = "font-family:Arial,sans-serif;"
_NAME   = "font-family:'Times New Roman',serif;font-size:15pt;font-weight:bold;text-decoration:none;margin:0;padding:0;line-height:1.0;"
_TITLE  = f"{_FONT}font-size:11pt;font-weight:bold;text-decoration:none;margin:0;padding:0;line-height:1.0;"
_CONTACT= f"{_FONT}font-size:11pt;font-weight:bold;margin:0;padding:0;line-height:1.0;"
_HR     = "border:none;border-top:1.5px solid #000;margin:0;padding:0;"
_H2     = (f"{_FONT}font-size:11pt;font-weight:bold;text-decoration:underline;"
           "padding:12pt 0 12pt 0;margin:0;line-height:1.0;")
_BODY_P = f"{_FONT}font-size:11pt;margin:0;padding:0;line-height:1.0;"
_CO     = f"{_FONT}font-size:11pt;font-weight:bold;margin:0;padding:0;line-height:1.0;"
_TD     = f"font-family:Arial,sans-serif;font-size:11pt;font-weight:bold;padding:0;border:none;vertical-align:top;line-height:1.0;"
_TD_R   = f"{_TD}text-align:right;white-space:nowrap;width:28%;"
_ROLES  = f"{_FONT}font-size:11pt;font-weight:bold;margin:0;padding:0;line-height:1.0;"
_ENV    = f"{_FONT}font-size:11pt;margin:0;padding:0;line-height:1.0;"
_SPACER = f"{_FONT}font-size:11pt;height:11pt;margin:0;padding:0;line-height:1.0;"
_LI     = f"{_FONT}font-size:11pt;margin:0;padding:0;line-height:1.0;margin-left:36pt;text-indent:-18pt;"
_LI_TS  = f"{_FONT}font-size:11pt;margin:0;padding:0;line-height:1.15;margin-left:36pt;text-indent:-18pt;"

def md_to_html(md: str) -> str:
    lines = md.strip().split('\n')
    out = ['<html><head><meta charset="UTF-8"></head>'
           f'<body style="{_FONT}font-size:11pt;color:#000;margin:36pt 31.5pt;padding:0;">']
    i = 0
    header_done = False
    current_section = None
    pending_title = None  # holds subtitle until contact line combines them

    while i < len(lines):
        s = lines[i].strip()
        i += 1

        if not s or s == '---':
            continue

        # ── Name (H1) ─────────────────────────────────────────────────────────
        if s.startswith('# '):
            out.append(f'<p style="{_NAME}">{s[2:]}</p>')
            continue

        # ── Section headers (H2) ──────────────────────────────────────────────
        if s.startswith('## '):
            current_section = s[3:].strip().upper().rstrip(':')
            # Reference: all headers have colon EXCEPT CERTIFICATIONS
            section = current_section if 'CERTIFICATION' in current_section else current_section + ':'
            if 'PROFESSIONAL SUMMARY' in current_section:
                out.append(f'<hr style="{_HR}">')
            out.append(f'<p style="{_H2}">{section}</p>')
            continue

        # ── Job title subtitle — buffer until contact line to combine into one <p> ──
        if not header_done and s.startswith('**') and s.endswith('**') and '|' not in s:
            pending_title = s[2:-2]
            continue

        # ── Contact line — combine with pending subtitle into one paragraph ───
        if not header_done and '|' in s and ('@' in s or s.startswith('+') or 'linkedin' in s.lower()):
            contact_html = re.sub(
                r'([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})',
                r'<a href="mailto:\1" style="color:#1155cc;text-decoration:underline;">\1</a>',
                s
            )
            if pending_title:
                # Single bold paragraph: subtitle <br> contact  (matches reference exactly)
                out.append(f'<p style="{_CONTACT}">{pending_title}<br>{contact_html}</p>')
                pending_title = None
            else:
                out.append(f'<p style="{_CONTACT}">{contact_html}</p>')
            header_done = True
            continue

        # ── Bullet list — use <p> not <li> to avoid Google Docs double-bullets ──
        if s.startswith('- '):
            while s.startswith('- '):
                # Technical Skills: bold "Category |" label, plain skills after pipe
                # Works regardless of where the AI puts ** markers
                if current_section and 'TECHNICAL SKILLS' in current_section:
                    raw = strip_bold(s[2:])
                    if '|' in raw:
                        before, after = raw.split('|', 1)
                        text = f'<strong>{before.strip()} |</strong>&nbsp;{after.strip()}'
                    else:
                        text = raw
                # Education & Certifications: fully plain text
                elif current_section and any(x in current_section for x in ('EDUCATION', 'CERTIFICATIONS')):
                    text = strip_bold(s[2:])
                else:
                    text = inline_bold(s[2:])
                li_style = _LI_TS if (current_section and 'TECHNICAL SKILLS' in current_section) else _LI
                bullet = '<span style="font-size:11pt;line-height:1.0;">&#9679;</span>&nbsp;&nbsp;'
                out.append(f'<p style="{li_style}">{bullet}{text}</p>')
                s = lines[i].strip() if i < len(lines) else ''
                i += 1
            if s and not s.startswith('- '):
                i -= 1
            continue

        # ── Experience: two consecutive **bold** | text lines ─────────────────
        if _is_bold_pipe(s):
            j = i
            while j < len(lines) and not lines[j].strip():
                j += 1
            next_s = lines[j].strip() if j < len(lines) else ''

            if _is_bold_pipe(next_s):
                # Line 1: Company | Location
                m = re.match(r'^\*\*(.+?)\*\*\s*\|\s*(.+)', s)
                co = f'{m.group(1)} | {m.group(2)}' if m else inline_bold(s)
                out.append(f'<p style="{_CO}">{co}</p>')

                # Line 2: Title | Dates (right-aligned via table)
                i = j + 1
                m2 = re.match(r'^\*\*(.+?)\*\*\s*\|\s*(.+)', next_s)
                if m2:
                    title, dates = m2.group(1), m2.group(2)
                    out.append(
                        f'<table style="width:100%;border-collapse:collapse;margin:0;">'
                        f'<tr>'
                        f'<td style="{_TD}">{title}</td>'
                        f'<td style="{_TD_R}">{dates}</td>'
                        f'</tr></table>'
                    )
                else:
                    out.append(f'<p style="{_CO}">{inline_bold(next_s)}</p>')

                out.append(f'<p style="{_ROLES}">Roles &amp; Responsibilities</p>')
                continue
            else:
                # Single entry line (Content section etc.)
                m = re.match(r'^\*\*(.+?)\*\*\s*\|\s*(.+)', s)
                if m:
                    out.append(f'<p style="{_CO}">{m.group(1)}</p>')
                    out.append(f'<p style="{_ENV}">{m.group(2)}</p>')
                else:
                    out.append(f'<p style="{_BODY_P}">{inline_bold(s)}</p>')
                continue

        # ── **Key:** Value (Environment lines) ────────────────────────────────
        m = re.match(r'^\*\*(.+?):\*\*\s*(.*)', s)
        if m:
            key, val = m.group(1), strip_bold(m.group(2))
            # Spacer before + after Environment line (matches reference 11pt gap)
            out.append(f'<p style="{_SPACER}"></p>')
            out.append(f'<p style="{_ENV}"><strong>{key}:</strong> {val}</p>')
            out.append(f'<p style="{_SPACER}"></p>')
            continue

        # ── Standalone **bold** (project names etc.) ──────────────────────────
        if s.startswith('**') and s.endswith('**'):
            out.append(f'<p style="{_CO}margin-top:6px;">{s[2:-2]}</p>')
            continue

        # ── Plain paragraph ───────────────────────────────────────────────────
        if s:
            out.append(f'<p style="{_BODY_P}">{inline_bold(s)}</p>')

    out.append('</body></html>')
    return '\n'.join(out)

# ─── Phase 5: Upload to Google Drive ─────────────────────────────────────────
def upload_to_drive(html: str, doc_name: str) -> str:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaInMemoryUpload

    creds = Credentials(
        token=None,
        refresh_token=os.getenv("GOOGLE_REFRESH_TOKEN"),
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
        token_uri="https://oauth2.googleapis.com/token",
        scopes=DRIVE_SCOPES
    )
    creds.refresh(Request())
    drive = build('drive', 'v3', credentials=creds)

    metadata = {'name': doc_name, 'mimeType': 'application/vnd.google-apps.document'}
    folder_id = os.getenv('GOOGLE_DRIVE_FOLDER_ID', '').strip()
    if folder_id:
        metadata['parents'] = [folder_id]

    media = MediaInMemoryUpload(html.encode('utf-8'), mimetype='text/html', resumable=False)
    file = drive.files().create(body=metadata, media_body=media, fields='id, webViewLink').execute()
    drive.permissions().create(fileId=file['id'], body={'type': 'anyone', 'role': 'reader'}).execute()
    return file['webViewLink']

# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    load_dotenv(ENV_PATH) if ENV_PATH.exists() else load_dotenv()

    parser = argparse.ArgumentParser(description='AI Resume Agent — agentic resume tailor')
    parser.add_argument('--jd-file', help='Path to .txt file with job description')
    parser.add_argument('--company', default='', help='Company name for research')
    parser.add_argument('--role', default='', help='Role title')
    parser.add_argument('--no-tailor', action='store_true', help='Skip AI — convert base resume only')
    args = parser.parse_args()

    check_prerequisites()

    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("  AI Resume Agent")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

    base_resume = RESUME_PATH.read_text()

    if args.no_tailor:
        print("📄  Using base resume as-is...\n")
        final_resume = base_resume
        final_score = None
    else:
        job_description = get_job_description(args)
        if not job_description:
            print("No job description provided. Exiting.")
            sys.exit(1)

        # Phase 1: Research
        research = research_company(args.company, args.role)

        # Phase 2: Tailor
        label = f"{args.company} · {args.role}".strip(" ·") or "role"
        print(f"🧠  Tailoring for {label}...\n")
        current_resume = tailor_resume(base_resume, job_description, research)

        # Phases 3+4: Evaluate + Iterate
        final_resume = current_resume
        final_score = None

        for attempt in range(1, MAX_ITERATIONS + 1):
            print(f"📊  Evaluating quality...")
            evaluation = evaluate_resume(current_resume, job_description)
            score = evaluation.get("score", 0)
            weak = evaluation.get("weak", [])
            final_score = score

            if score >= SCORE_THRESHOLD:
                print(f"    Score: {score}/100 ✅\n")
                final_resume = current_resume
                break

            print(f"    Score: {score}/100")
            for w in weak[:2]:
                print(f"    ✗ {w}")

            if attempt < MAX_ITERATIONS:
                print(f"\n🔄  Improving (attempt {attempt + 1}/{MAX_ITERATIONS})...\n")
                current_resume = improve_resume(current_resume, evaluation, job_description)
                final_resume = current_resume
            else:
                print(f"\n    Max attempts reached. Using best version.\n")
                final_resume = current_resume

    # Phase 5: Deliver
    print("📝  Converting to Google Doc format...")
    html = md_to_html(final_resume)

    timestamp = datetime.now().strftime('%Y-%m-%d')
    parts = [p for p in [args.company, args.role] if p]
    label = ' — '.join(parts) if parts else 'Base'
    doc_name = f"SSK Resume — {label} — {timestamp}"

    print("📤  Uploading to Google Drive...\n")
    url = upload_to_drive(html, doc_name)

    score_str = f" · Final score: {final_score}/100" if final_score else ""
    print(f"✅  Done!{score_str}")
    print(f"\n🔗  {url}")
    print("\n    Open → File → Download → PDF Document")
    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

if __name__ == '__main__':
    main()
