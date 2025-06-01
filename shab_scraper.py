import datetime
import time
import sqlite3
from typing import List, Dict, Optional

import json

import requests
import openai
import os

DB_PATH = "medical_registrations.db"
SHAB_API_URL = "https://www.shab.ch/api/v1/notice"  # Placeholder URL

# Configure OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY", "YOUR_OPENAI_API_KEY")


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
    """Return extracted info if the entry describes a medical establishment."""
    prompt = (
        "Extrahiere aus dem folgenden SHAB-Eintrag den Unternehmensnamen, die Kontaktinformationen "
        "(falls vorhanden) und klassifiziere den genauen Bereich im Gesundheitswesen (Arztpraxis, "
        "Krankenhaus, Klinik, Zahnarzt, Reha, etc.). Antworte ausschließlich mit einem JSON im Format:\n"
        "{\n"
        " \"is_medical\": true|false,\n"
        " \"company_name\": \"\",\n"
        " \"category\": \"\",\n"
        " \"contact\": \"\",\n"
        " \"address\": \"\"\n"
        "}\n\n"
        f"Eintrag: {text}"
    )
    try:
        resp = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        content = resp.choices[0].message.content.strip()
        data = json.loads(content)
        if not isinstance(data, dict) or not data.get("is_medical"):
            return None
        return data
    except Exception as exc:
        print(f"Analysis failed: {exc}")
        return None


def save_entry(conn: sqlite3.Connection, entry: Dict) -> None:
    """Save the relevant entry to the database."""
    conn.execute(
        """
        INSERT INTO medical_entries (
            date,
            company_name,
            category,
            contact,
            address,
            text
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            entry.get("date"),
            entry.get("company_name"),
            entry.get("category"),
            entry.get("contact"),
            entry.get("address"),
            entry.get("text"),
        ),
    )
    conn.commit()


def ensure_db(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS medical_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            company_name TEXT,
            category TEXT,
            contact TEXT,
            address TEXT,
            text TEXT
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
            text = entry.get("text", "")
            result = analyze_entry(text)
            if result:
                record = {
                    "date": entry.get("date"),
                    "company_name": result.get("company_name"),
                    "category": result.get("category"),
                    "contact": result.get("contact"),
                    "address": result.get("address"),
                    "text": text,
                }
                save_entry(conn, record)
        conn.commit()
        # Sleep for 24 hours
        time.sleep(24 * 60 * 60)


if __name__ == "__main__":
    run_daily()
