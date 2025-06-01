# RoboAdvisorHub

## SHAB Scraper

This project includes a Python script that collects daily notices from the Schweizerisches Handelsamtsblatt (SHAB), analyses them with the OpenAI API and stores medical related entries in a SQLite database.  For each relevant entry the database keeps company name, category, address and contact information when available.

### Usage

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Set your OpenAI API key using the `OPENAI_API_KEY` environment variable.
3. Run the scraper:
   ```bash
   python shab_scraper.py
   ```

The script will check the SHAB once per day, analyse new entries and store relevant ones in `medical_registrations.db`.
