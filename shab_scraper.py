"""Simple scraper that fetches SHAB notices and stores medical ones."""

import datetime
import json
import os
import time
import sqlite3
from typing import List, Dict, Optional

import requests
import openai

DB_PATH = "medical_registrations.db"
SHAB_API_URL = "https://www.shab.ch/api/v1/notice"  # Placeholder URL
CHECK_INTERVAL = 24 * 60 * 60  # seconds

# Configure OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY", "")
if not openai.api_key:
    print("Warning: OPENAI_API_KEY environment variable not set. API requests will fail.")


def fetch_shab_entries(date: datetime.date) -> List[Dict]:
    """Fetch SHAB entries for the given date.

    This function should call the SHAB API or scrape the website to
    retrieve notices published on the specified date. The implementation
    here is a placeholder and returns an empty list.
    """
    # Example request (the real parameters depend on the SHAB API)
    params = {
        "published_after": date.strftime("%Y-%m-%d"),
        "published_before": (date + datetime.timedelta(days=1)).strftime("%Y-%m-%d"),
    }
    try:
        response = requests.get(SHAB_API_URL, params=params)
        response.raise_for_status()
        return response.json().get("results", [])
    except Exception as exc:
        print(f"Failed to fetch SHAB data: {exc}")
        return []


def analyze_entry(text: str) -> Optional[Dict[str, str]]:
    """Return parsed details if the entry describes a medical establishment."""

    prompt = (
        "Extrahiere aus dem folgenden SHAB-Eintrag die Daten eines medizinischen\n"
        "Unternehmens. Gib nur ein JSON mit den Feldern 'company', 'category',\n"
        "'contact' und 'address' zur\u00fcck. Falls es sich nicht um eine medizinische\n"
        "Einrichtung handelt, gib das Wort 'null' zur\u00fcck.\n\n"
        f"Text: {text}"
    )

    try:
        resp = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        content = resp.choices[0].message.content.strip()
        if content.lower().startswith("null"):
            return None
        data = json.loads(content)
        return {
            "company": data.get("company", ""),
            "category": data.get("category", ""),
            "contact": data.get("contact", ""),
            "address": data.get("address", ""),
        }
    except Exception as exc:
        print(f"Analysis failed: {exc}")
        return None


def save_entry(conn: sqlite3.Connection, entry: Dict, details: Dict[str, str]) -> None:
    """Save the relevant entry to the database along with extracted details."""
    conn.execute(
        """
        INSERT INTO medical_entries (date, title, text, company, category, contact, address)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            entry.get("date"),
            entry.get("title"),
            entry.get("text"),
            details.get("company"),
            details.get("category"),
            details.get("contact"),
            details.get("address"),
        ),
    )
    conn.commit()


def ensure_db(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS medical_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            title TEXT,
            text TEXT,
            company TEXT,
            category TEXT,
            contact TEXT,
            address TEXT
        )
        """
    )
    conn.commit()


def run_daily() -> None:
    conn = sqlite3.connect(DB_PATH)
    ensure_db(conn)

    while True:
        yesterday = datetime.date.today() - datetime.timedelta(days=1)
        entries = fetch_shab_entries(yesterday)
        for entry in entries:
            details = analyze_entry(entry.get("text", ""))
            if details:
                save_entry(conn, entry, details)
        conn.commit()
        # Sleep until the next run
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    run_daily()
