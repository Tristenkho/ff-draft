#!/usr/bin/env python3
"""Pull league settings and rosters from the ESPN fantasy API.

Credentials live in .espn.json (gitignored):
    {"league_id": 1238596447, "season": 2026,
     "espn_s2": "...", "swid": "{...}"}

Usage: python3 scripts/espn_fetch.py
Writes raw JSON to out/espn_league.json and prints a settings summary.
"""
import json
import pathlib
import sys
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
CREDS = ROOT / ".espn.json"
OUT = ROOT / "out" / "espn_league.json"

BASE = ("https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl"
        "/seasons/{season}/segments/0/leagues/{league_id}")
VIEWS = ["mSettings", "mTeam", "mRoster"]

SLOTS = {
    0: "QB", 2: "RB", 4: "WR", 6: "TE", 16: "D/ST", 17: "K",
    20: "Bench", 21: "IR", 23: "FLEX", 3: "RB/WR", 5: "WR/TE", 7: "OP",
}


def load_creds():
    if not CREDS.exists():
        sys.exit(f"missing {CREDS.name} — see docstring for the expected shape")
    c = json.loads(CREDS.read_text())
    missing = [k for k in ("league_id", "espn_s2", "swid") if not c.get(k)]
    if missing:
        sys.exit(f"{CREDS.name} is missing: {', '.join(missing)}")
    c.setdefault("season", 2026)
    return c


def fetch(creds):
    url = BASE.format(season=creds["season"], league_id=creds["league_id"])
    url += "?" + "&".join(f"view={v}" for v in VIEWS)
    req = urllib.request.Request(url, headers={
        "Cookie": f"espn_s2={creds['espn_s2']}; SWID={creds['swid']}",
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            sys.exit(f"HTTP {e.code}: cookies rejected or expired. "
                     "Re-copy espn_s2 and SWID from a logged-in browser.")
        if e.code == 404:
            sys.exit(f"HTTP 404: no league {creds['league_id']} "
                     f"for season {creds['season']}.")
        sys.exit(f"HTTP {e.code}: {e.reason}")
    except urllib.error.URLError as e:
        sys.exit(f"network error: {e.reason}")


def summarize(data):
    s = data.get("settings", {})
    print(f"league:  {s.get('name', '?')}")
    print(f"size:    {s.get('size', '?')} teams")

    roster = s.get("rosterSettings", {}).get("lineupSlotCounts", {})
    active = {SLOTS.get(int(k), f"slot{k}"): v
              for k, v in roster.items() if v}
    if active:
        print("roster: ", ", ".join(f"{k} {v}" for k, v in active.items()))

    sched = s.get("scheduleSettings", {})
    print(f"playoff: {sched.get('playoffTeamCount', '?')} teams, "
          f"matchup length {sched.get('playoffMatchupPeriodLength', '?')}")

    scoring = s.get("scoringSettings", {}).get("scoringItems", [])
    print(f"scoring: {len(scoring)} configured stat items")

    teams = data.get("teams", [])
    print(f"teams:   {len(teams)}")
    for t in teams:
        name = t.get("name") or f"{t.get('location','')} {t.get('nickname','')}".strip()
        n = len((t.get("roster") or {}).get("entries", []))
        print(f"  [{t.get('id')}] {name or '?'} — {n} rostered")


def main():
    creds = load_creds()
    print(f"fetching league {creds['league_id']}, season {creds['season']}...\n")
    data = fetch(creds)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, indent=1))
    summarize(data)
    print(f"\nraw -> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
