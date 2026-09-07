#!/usr/bin/env python3
"""Pull the completed draft (picks, teams, rosters) from the ESPN fantasy API.

Credentials come from .espn.json, the same file scripts/espn_fetch.py uses.

Usage: python3 scripts/espn_draft_recap.py [season]
Writes out/espn_draft_<season>.json and prints the draft board.
"""
import json
import pathlib
import ssl
import sys
import urllib.error
import urllib.request

import certifi

ROOT = pathlib.Path(__file__).resolve().parent.parent
CREDS = ROOT / ".espn.json"

BASE = ("https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl"
        "/seasons/{season}/segments/0/leagues/{league_id}")
VIEWS = ["mDraftDetail", "mTeam", "mRoster", "mSettings"]
POS = {1: "QB", 2: "RB", 3: "WR", 4: "TE", 5: "K", 16: "DST"}


def load_creds(season=None):
    if not CREDS.exists():
        sys.exit(f"missing {CREDS.name}")
    c = json.loads(CREDS.read_text())
    c.setdefault("season", 2026)
    if season:
        c["season"] = int(season)
    return c


def fetch(creds):
    url = BASE.format(season=creds["season"], league_id=creds["league_id"])
    url += "?" + "&".join(f"view={v}" for v in VIEWS)
    req = urllib.request.Request(url, headers={
        "Cookie": f"espn_s2={creds['espn_s2']}; SWID={creds['swid']}",
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
    })
    ctx = ssl.create_default_context(cafile=certifi.where())
    try:
        with urllib.request.urlopen(req, timeout=40, context=ctx) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        sys.exit(f"HTTP {e.code}: {e.reason}")


def main():
    season = sys.argv[1] if len(sys.argv) > 1 else None
    creds = load_creds(season)
    data = fetch(creds)

    teams = {}
    for t in data.get("teams", []):
        name = t.get("name") or f"{t.get('location','')} {t.get('nickname','')}".strip()
        teams[t["id"]] = name

    names = {}
    for t in data.get("teams", []):
        for e in (t.get("roster") or {}).get("entries", []):
            p = e.get("playerPoolEntry", {}).get("player", {})
            if p.get("id"):
                names[p["id"]] = {
                    "name": p.get("fullName"),
                    "pos": POS.get(p.get("defaultPositionId"), "?"),
                    "team_id": t["id"],
                }

    picks = []
    for p in (data.get("draftDetail") or {}).get("picks", []):
        info = names.get(p["playerId"], {})
        picks.append({
            "overall": p["overallPickNumber"],
            "round": p["roundId"],
            "pick_in_round": p["roundPickNumber"],
            "player_id": p["playerId"],
            "name": info.get("name"),
            "pos": info.get("pos"),
            "team_id": p["teamId"],
            "team": teams.get(p["teamId"]),
            "keeper": p.get("keeper"),
        })
    picks.sort(key=lambda x: x["overall"])

    out = {
        "league": data.get("settings", {}).get("name"),
        "season": creds["season"],
        "league_id": creds["league_id"],
        "teams": teams,
        "drafted": (data.get("draftDetail") or {}).get("drafted"),
        "picks": picks,
        "rosters": {teams[t["id"]]: [
            {"name": e.get("playerPoolEntry", {}).get("player", {}).get("fullName"),
             "pos": POS.get(e.get("playerPoolEntry", {}).get("player", {}).get("defaultPositionId"), "?")}
            for e in (t.get("roster") or {}).get("entries", [])
        ] for t in data.get("teams", [])},
    }
    dest = ROOT / "out" / f"espn_draft_{creds['season']}.json"
    dest.write_text(json.dumps(out, indent=1))
    print(f"wrote {dest}  drafted={out['drafted']}  picks={len(picks)}")
    for p in picks:
        print(f"{p['overall']:>4} R{p['round']:<2} {p['team'][:22]:<22} "
              f"{(p['name'] or '?'):<26} {p['pos']}")


main()
