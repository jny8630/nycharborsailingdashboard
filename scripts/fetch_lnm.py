#!/usr/bin/env python3
"""
fetch_lnm.py — Download current USCG D1 LNM PDF, extract NYC Harbor notices via
GitHub Models (GPT-4o-mini), write lnm_current.json to project root.

Usage:
  export GITHUB_TOKEN=$(gh auth token)   # or automatic in GitHub Actions
  python3 scripts/fetch_lnm.py

Requirements: openai, requests, pdfplumber  (see scripts/requirements.txt)
"""

import json
import os
import re
import sys
import io
from datetime import datetime, timezone, date, timedelta

import requests
import pdfplumber
from openai import OpenAI

# ── Config ─────────────────────────────────────────────────────────────────────

GITHUB_MODELS_URL = "https://models.inference.ai.azure.com"
PRIMARY_MODEL     = "gpt-4o-mini"
FALLBACK_MODEL    = "Meta-Llama-3.1-8B-Instruct"
OUTPUT_FILE       = os.path.join(os.path.dirname(__file__), "..", "lnm_current.json")
LNM_BASE          = "https://www.navcen.uscg.gov/sites/default/files/pdf/lnms/"
MAX_WEEKS_BACK    = 4   # how many weeks to search back for a text-based PDF
MAX_SECTION_CHARS = 1500  # chars to keep per relevant section
MAX_TOTAL_CHARS   = 25000 # safety limit for total prompt content

# Geographic terms matched against each section's header line.
# Specific enough to avoid false positives (e.g. "Hudson" matches Hudson, NH).
NYC_SECTION_TERMS = [
    "ambrose",
    "kill van kull", "kill van",
    "arthur kill",
    "raritan bay", "raritan river",
    "great kills",
    "sheepshead",
    "shooters island",
    "east river",
    "main channel - hudson",
    "sector new york",
    "beach channel",
    "jamaica bay",
    "gravesend",
    "upper bay", "lower bay",
    "upper new york bay", "lower new york bay",
    "new york harbor", "new york bay",
    "buttermilk",
    "governors island",
    "verrazzano", "verrazano",
    "newark bay",
    "sandy hook",
    "naval weapon station earle",
    "staten island",
]

# Boilerplate lines to strip from each PDF page
BOILERPLATE_RE = re.compile(
    r"^\d+/\d+/\d+,.*?Navigation Center\s*$|^Local Notice to Mariners.*$",
    re.MULTILINE | re.IGNORECASE,
)

PROMPT = """You are reviewing an extract from a USCG District 1 Local Notice to Mariners,
pre-filtered for the NYC Harbor area. Extract notices relevant to small keelboat sailing in:
- Upper/Lower New York Bay, The Narrows, Ambrose Channel
- Governors Island, Buttermilk Channel, Anchorage/Flats
- Hudson River (Battery to ~W 60th St)
- East River south of Brooklyn Bridge
- Kill Van Kull, Arthur Kill, Raritan Bay, Sandy Hook
- Great Kills, Sheepshead Bay, Gravesend Bay

EXCLUDE notices clearly north of Brooklyn Bridge on East River, north of W 60th on Hudson,
or in Long Island Sound / New England.

Return ONLY this JSON, no other text:
{"notices": [
  {"location": "...", "chart": "12327 or null", "summary": "one sentence for a sailor",
   "status": "ACTIVE|TEMPORARY|CANCELLED", "since": "date or ongoing"}
]}
If nothing is relevant: {"notices": []}

NYC HARBOR LNM EXTRACT:
"""

# ── Helpers ────────────────────────────────────────────────────────────────────

def lnm_url(week, year):
    return f"{LNM_BASE}lnm01{week:02d}{year}.pdf"

def week_year_for_offset(days_back=0):
    d = date.today() - timedelta(days=days_back)
    iso = d.isocalendar()
    return iso[1], iso[0]

def download_pdf(url):
    headers = {"User-Agent": "Mozilla/5.0 (compatible; LNM-fetcher/1.0)"}
    r = requests.get(url, headers=headers, timeout=60)
    if r.status_code == 404:
        return None
    r.raise_for_status()
    return r.content

def extract_pages(pdf_bytes):
    """Return list of page text strings. Empty list if scanned/image-based."""
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        return [p.extract_text() or "" for p in pdf.pages]

def get_section_header(page_text):
    """Return the first non-boilerplate, non-empty line of a page."""
    skip = {"4/29/26", "4/30/26", "maritime safety", "navigation center",
            "local notice to mariners", "name llnr status"}
    for line in page_text.split("\n"):
        line = line.strip()
        if line and not any(s in line.lower() for s in skip):
            return line
    return ""

def is_nyc_relevant(header):
    h = header.lower()
    return any(term in h for term in NYC_SECTION_TERMS)

def clean_page(page_text):
    """Strip boilerplate header lines from a page."""
    lines = page_text.split("\n")
    out = []
    for line in lines:
        stripped = line.strip()
        skip = any(s in stripped.lower() for s in [
            "maritime safety information", "navigation center",
            "local notice to mariners",
        ])
        if not skip and re.match(r"^\d+/\d+/\d+,\s*\d+:\d+", stripped):
            skip = True
        if not skip:
            out.append(line)
    return "\n".join(out).strip()

def prefilter(pages):
    """
    Return filtered text: only sections with NYC-relevant headers,
    each capped at MAX_SECTION_CHARS, total capped at MAX_TOTAL_CHARS.
    """
    sections = []
    total = 0
    for page in pages:
        header = get_section_header(page)
        if not is_nyc_relevant(header):
            continue
        content = clean_page(page)
        excerpt = content[:MAX_SECTION_CHARS]
        if total + len(excerpt) > MAX_TOTAL_CHARS:
            remaining = MAX_TOTAL_CHARS - total
            if remaining < 200:
                break
            excerpt = excerpt[:remaining]
        sections.append(excerpt)
        total += len(excerpt)

    return "\n\n---\n\n".join(sections)

def call_model(client, model, filtered_text):
    prompt = PROMPT + filtered_text
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        max_tokens=2048,
        temperature=0.1,
    )
    raw = response.choices[0].message.content
    data = json.loads(raw)
    return data.get("notices", [])

# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("ERROR: GITHUB_TOKEN not set.", file=sys.stderr)
        print("  Run: export GITHUB_TOKEN=$(gh auth token)", file=sys.stderr)
        sys.exit(1)

    client = OpenAI(base_url=GITHUB_MODELS_URL, api_key=token)

    # Find latest text-based LNM
    pdf_bytes = pages = week = year = url = None
    for weeks_back in range(0, MAX_WEEKS_BACK * 7 + 1, 7):
        w, y = week_year_for_offset(days_back=weeks_back)
        u = lnm_url(w, y)
        print(f"Trying week {w}/{y}: {u}")
        data = download_pdf(u)
        if data is None:
            print("  404 — skipping"); continue
        pg = extract_pages(data)
        text_pages = [p for p in pg if p.strip()]
        if not text_pages:
            print("  Scanned PDF — skipping"); continue
        print(f"  OK — {len(data):,} bytes, {len(text_pages)} text pages")
        pdf_bytes, pages, week, year, url = data, pg, w, y, u
        break

    if not pages:
        print("ERROR: No text-based LNM found in the last 4 weeks.", file=sys.stderr)
        sys.exit(1)

    filtered = prefilter(pages)
    print(f"Pre-filter: {len(filtered):,} chars from {sum(1 for p in pages if get_section_header(p) and is_nyc_relevant(get_section_header(p)))} relevant sections")

    # Call model with fallback
    notices = None
    used_model = None
    for model in (PRIMARY_MODEL, FALLBACK_MODEL):
        try:
            print(f"Calling {model}…")
            notices = call_model(client, model, filtered)
            used_model = model
            print(f"  {len(notices)} relevant notice(s) extracted.")
            break
        except Exception as e:
            print(f"  {model} failed: {e}", file=sys.stderr)

    if notices is None:
        print("ERROR: All models failed.", file=sys.stderr)
        sys.exit(1)

    output = {
        "week": week,
        "year": year,
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "pdf_url": url,
        "model": used_model,
        "notices": notices,
        "disclaimer": (
            "AI-extracted from USCG D1 LNM via GitHub Models. "
            "Verify against source PDF before underway."
        ),
    }

    out_path = os.path.abspath(OUTPUT_FILE)
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"Written: {out_path}")

if __name__ == "__main__":
    main()
