"""Daily modern-sky summary for Satscope, from CelesTrak's public SATCAT (no account needed).

Writes sky.json:
  reentries: objects whose DECAY_DATE falls in the last 7 days (confirmed re-entries, newest first)
  debris:    debris pieces newly catalogued this week, measured from a daily count history kept in the same file
Usage: python sky_summary.py [out_path]   (reads the previous out_path, if present, for the history)
"""
import csv, io, json, re, sys, urllib.request
from datetime import date, datetime, timedelta, timezone

SATCAT = "https://celestrak.org/pub/satcat.csv"
OUT = sys.argv[1] if len(sys.argv) > 1 else "sky.json"
UA = "Satscope-sky-summary/1.0 (daily, once)"
KEEP_DAYS = 45
FAMOUS = ("ISS", "TIANGONG", "HUBBLE", "CREW DRAGON", "DRAGON", "SOYUZ", "PROGRESS", "SHENZHOU", "TIANZHOU", "CYGNUS", "STARLINER", "ORION")


def fetch_rows():
    req = urllib.request.Request(SATCAT, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=120) as r:
        text = r.read().decode("utf-8")
    return list(csv.DictReader(io.StringIO(text)))


def parse_day(s):
    try:
        return date.fromisoformat(s[:10])
    except (TypeError, ValueError):
        return None


def main():
    today = datetime.now(timezone.utc).date()
    rows = fetch_rows()
    if len(rows) < 50_000:
        raise SystemExit(f"SATCAT looks truncated ({len(rows)} rows); keeping yesterday's file")

    try:
        prev = json.load(open(OUT, encoding="utf-8"))
    except (OSError, ValueError):
        prev = {}

    # Confirmed re-entries in the last 7 days. Skip unnamed debris fragments: a reading names its object.
    recent = []
    for r in rows:
        d = parse_day(r.get("DECAY_DATE", ""))
        if d is None or not (today - timedelta(days=7) <= d <= today):
            continue
        kind = r.get("OBJECT_TYPE", "")
        if kind not in ("PAY", "R/B"):
            continue
        name = r["OBJECT_NAME"].strip()
        launched = parse_day(r.get("LAUNCH_DATE", ""))
        years_up = (d - launched).days / 365.25 if launched else 0
        # Notable: rocket stages, anything up 5+ years, or a famous name. Never Starlink's routine disposals.
        notable = not name.upper().startswith("STARLINK") and (
            kind == "R/B" or years_up >= 5 or any(re.search(rf"\b{re.escape(f)}\b", name.upper()) for f in FAMOUS))
        recent.append({
            "date": d.isoformat(),
            "name": name,
            "notable": notable,
            "yearsUp": round(years_up, 1),
            "norad": int(r["NORAD_CAT_ID"]),
            "type": kind,
            "owner": r.get("OWNER", ""),
            "launch": r.get("LAUNCH_DATE", ""),
            "intldes": r.get("OBJECT_ID", ""),
        })
    recent.sort(key=lambda x: (x["date"], x["notable"]), reverse=True)

    # Debris: total catalogued DEB objects today, compared with the count about a week ago.
    deb_total = sum(1 for r in rows if r.get("OBJECT_TYPE") == "DEB")
    deb_up = sum(1 for r in rows if r.get("OBJECT_TYPE") == "DEB" and not r.get("DECAY_DATE"))
    history = [h for h in prev.get("debris", {}).get("history", []) if h["date"] != today.isoformat()]
    history.append({"date": today.isoformat(), "total": deb_total, "up": deb_up})
    history = [h for h in history if parse_day(h["date"]) >= today - timedelta(days=KEEP_DAYS)]
    history.sort(key=lambda h: h["date"])
    week_ago = [h for h in history if parse_day(h["date"]) <= today - timedelta(days=7)]
    if week_ago:
        base = week_ago[-1]
        days = max(7, (today - parse_day(base["date"])).days)
        new_week = round((deb_total - base["total"]) * 7 / days)
    else:
        new_week = None

    out = {
        "generated": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "source": "CelesTrak SATCAT (celestrak.org)",
        "reentries": recent[:20],
        "debris": {"newThisWeek": new_week, "total": deb_total, "up": deb_up, "history": history},
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    print(f"{len(recent)} re-entries in 7 days; debris total {deb_total}, new this week {new_week}")


if __name__ == "__main__":
    main()
