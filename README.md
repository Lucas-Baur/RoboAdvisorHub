# RoboAdvisorHub

## SHAB Scraper

This project includes a Python script to collect daily notices from the Schweizerisches Handelsamtsblatt (SHAB), analyse them using the OpenAI API and store information about neue medizinische Einrichtungen in einer SQLite-Datenbank. Neben dem Text werden auch der Unternehmensname, die Kontaktmöglichkeit, die Adresse und die genaue Einordnung (z.B. Arztpraxis, Krankenhaus, Klinik, Zahnarzt, Reha) gespeichert.

### Usage

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Set your OpenAI API key using the `OPENAI_API_KEY` environment variable or by editing `shab_scraper.py`.
3. Run the scraper:
   ```bash
   python shab_scraper.py
   ```

The script prüft einmal täglich das SHAB, analysiert alle neuen Meldungen und speichert gefundene medizinische Einrichtungen in `medical_registrations.db`.
