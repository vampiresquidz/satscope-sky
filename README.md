# satscope-sky

A daily summary of the modern sky for the Satscope app, built from CelesTrak's public satellite catalogue
(https://celestrak.org/pub/satcat.csv). A GitHub Action runs `sky_summary.py` once a day and commits `sky.json`:

- `reentries`: payloads and rocket stages whose catalogued decay date is in the last 7 days. `notable` marks rocket
  stages, objects up 5+ years, and famous names (never routine Starlink disposals).
- `debris`: catalogued debris totals per day and the new pieces per week.

The app reads https://raw.githubusercontent.com/vampiresquidz/satscope-sky/main/sky.json.
