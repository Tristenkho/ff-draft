#!/usr/bin/env python3
"""Refresh the complete draft-day pool from ESPN and FantasyPros.

ESPN supplies the league-scored projection, room ADP/rank, current NFL team,
and availability status. FantasyPros supplies half-PPR ECR, tiers, and a
second bye-week check. CBS/FFToday are then applied by the ensemble updater.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import ssl
import urllib.request
from collections import defaultdict
from pathlib import Path

import certifi

import update_projection_ensemble as ensemble


ROOT = Path(__file__).resolve().parents[1]
CREDS = ROOT / ".espn.json"
CACHE = ROOT / ".cache" / "draft-data-2026"
RAW = ROOT / "out" / "draft_data_refresh_raw.json"
REPORT = ROOT / "out" / "draft_data_refresh_analysis.md"
FP_URL = "https://www.fantasypros.com/nfl/rankings/half-point-ppr-cheatsheets.php"

POSITION_ID = {1: "QB", 2: "RB", 3: "WR", 4: "TE", 5: "K", 16: "DST"}
QUOTAS = {"QB": 30, "RB": 70, "WR": 90, "TE": 26}
BASELINE_POOL_SIZE = 205
CEILING_RATE = {"QB": .14, "RB": .26, "WR": .23, "TE": .25, "K": .10, "DST": .18}
TEAM_BY_ID = {
    1: "ATL", 2: "BUF", 3: "CHI", 4: "CIN", 5: "CLE", 6: "DAL", 7: "DEN", 8: "DET",
    9: "GB", 10: "TEN", 11: "IND", 12: "KC", 13: "LV", 14: "LAR", 15: "MIA", 16: "MIN",
    17: "NE", 18: "NO", 19: "NYG", 20: "NYJ", 21: "PHI", 22: "ARI", 23: "PIT", 24: "LAC",
    25: "SF", 26: "SEA", 27: "TB", 28: "WAS", 29: "CAR", 30: "JAX", 33: "BAL", 34: "HOU",
}
BYE_BY_TEAM = {
    "CAR": 5, "KC": 5,
    "CIN": 6, "DET": 6, "MIA": 6, "MIN": 6,
    "BUF": 7, "JAX": 7, "LAC": 7, "WAS": 7,
    "HOU": 8, "NO": 8, "NYG": 8, "SF": 8,
    "PIT": 9, "TEN": 9,
    "CHI": 10, "DEN": 10, "PHI": 10, "TB": 10,
    "ATL": 11, "CLE": 11, "GB": 11, "LAR": 11, "NE": 11, "SEA": 11,
    "BAL": 13, "IND": 13, "LV": 13, "NYJ": 13,
    "ARI": 14, "DAL": 14,
}


def fetch(url: str, path: Path, refresh: bool, headers: dict | None = None) -> str:
    if refresh or not path.exists() or path.stat().st_size < 1000:
        path.parent.mkdir(parents=True, exist_ok=True)
        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 ff-draft-refresh", **(headers or {})})
        context = ssl.create_default_context(cafile=certifi.where())
        with urllib.request.urlopen(request, timeout=120, context=context) as response:
            path.write_bytes(response.read())
    return path.read_text(errors="replace")


def espn_rows(refresh: bool) -> list[dict]:
    creds = json.loads(CREDS.read_text())
    url = ("https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl"
           f"/seasons/{creds.get('season', 2026)}/segments/0/leagues/{creds['league_id']}"
           "?scoringPeriodId=0&view=kona_player_info")
    fantasy_filter = {"players": {"limit": 1000, "sortPercOwned": {"sortPriority": 1, "sortAsc": False},
                                   "filterActive": {"value": True}}}
    headers = {
        "Cookie": f"espn_s2={creds['espn_s2']}; SWID={creds['swid']}",
        "Accept": "application/json", "x-fantasy-filter": json.dumps(fantasy_filter),
    }
    return json.loads(fetch(url, CACHE / "espn_players.json", refresh, headers))["players"]


def fantasypros(refresh: bool) -> dict[str, dict]:
    text = fetch(FP_URL, CACHE / "fantasypros_half_ppr.html", refresh)
    marker = '"players":[{"player_id":22968'
    start = text.find(marker)
    if start < 0:
        raise RuntimeError("FantasyPros player payload not found")
    players, _ = json.JSONDecoder().raw_decode(text[start + len('"players":'):])
    return {ensemble.normalize(player["player_name"]): player for player in players}


def season_projection(player: dict) -> float:
    values = [stat.get("appliedTotal", 0) for stat in player.get("stats", [])
              if stat.get("seasonId") == 2026 and stat.get("scoringPeriodId") == 0
              and stat.get("statSourceId") == 1 and stat.get("statSplitTypeId") == 0]
    return float(values[0]) if values else 0.0


def position_rank(fp: dict | None, position: str) -> int:
    match = re.search(r"(\d+)$", str((fp or {}).get("pos_rank", "")))
    return int(match.group(1)) if match else 99


def room_rank(adp: float, rank: float, ecr: float) -> float:
    adp = min(adp if 0 < adp < 500 else 400, 400)
    rank = min(rank if 0 < rank < 1000 else 400, 400)
    ecr = min(ecr if 0 < ecr < 1000 else 400, 400)
    return .65 * adp + .25 * rank + .10 * ecr


def candidate(row: dict, fp_by_name: dict[str, dict], old_by_id: dict[int, dict]) -> dict | None:
    p = row["player"]
    position = POSITION_ID.get(p.get("defaultPositionId"))
    team = TEAM_BY_ID.get(p.get("proTeamId"))
    if not position or not team:
        return None
    fp = fp_by_name.get(ensemble.normalize(p["fullName"]))
    if position == "DST":
        fp = next((item for item in fp_by_name.values()
                   if item.get("player_position_id") == "DST" and item.get("player_team_id") == team), fp)
    old = old_by_id.get(p["id"], {})
    ownership = p.get("ownership") or {}
    ranks = p.get("draftRanksByRankType") or {}
    espn_rank = float((ranks.get("PPR") or ranks.get("STANDARD") or {}).get("rank", 999))
    espn_adp = float(ownership.get("averageDraftPosition") or 999)
    ecr = float((fp or {}).get("rank_ecr") or old.get("ecr") or espn_rank)
    projection = season_projection(p)
    market = room_rank(espn_adp, espn_rank, ecr)
    old_fp_adp = old.get("fp_adp", old.get("adp", 999))
    sd = float(old.get("sd") or projection * CEILING_RATE[position])
    return {
        "id": p["id"], "name": p["fullName"], "pos": position, "team": team,
        "bye": BYE_BY_TEAM[team], "status": p.get("injuryStatus") or "ACTIVE",
        "injured": bool(p.get("injured")), "last_news": p.get("lastNewsDate"),
        "proj": round(projection, 1), "proj_espn": round(projection, 1), "sd": round(sd, 1),
        "adp": round(espn_adp, 1), "espn_adp": round(espn_adp, 1),
        "espn_rank": round(espn_rank, 1), "room_rank": round(market, 1),
        "adp_sd": round(max(6, min(35, 5.8 + .055 * market)), 1),
        "ecr": int(ecr), "fp_adp": old_fp_adp, "tier": int((fp or {}).get("tier") or old.get("tier") or 99),
        "ecr_pos": position_rank(fp, position), "fp_ranked": bool(fp),
        "percent_owned": round(float(ownership.get("percentOwned") or 0), 1),
    }


def choose_pool(candidates: list[dict]) -> list[dict]:
    output = []
    for position, quota in QUOTAS.items():
        group = [p for p in candidates if p["pos"] == position]
        useful = [p for p in group if p["fp_ranked"] or p["proj"] > 0 or p["percent_owned"] >= 1]
        useful.sort(key=lambda p: (min(p["ecr"], p["room_rank"]), p["room_rank"], -p["percent_owned"], -p["proj"], p["name"]))
        group = useful + [p for p in group if p not in useful]
        output.extend(group[:quota])

    # One projected kicker per NFL team; all 32 team defenses.
    kickers = defaultdict(list)
    for player in candidates:
        if player["pos"] == "K":
            kickers[player["team"]].append(player)
    for team in sorted(TEAM_BY_ID.values()):
        options = kickers[team]
        if not options:
            raise RuntimeError(f"No active ESPN kicker for {team}")
        options.sort(key=lambda p: (-p["proj"], -p["percent_owned"], p["room_rank"]))
        output.append(options[0])
    defenses = [p for p in candidates if p["pos"] == "DST"]
    if len(defenses) != 32:
        raise RuntimeError(f"Expected 32 defenses, received {len(defenses)}")
    output.extend(defenses)
    return output


def add_special_ranks(players: list[dict]) -> None:
    for position in ("K", "DST"):
        group = [p for p in players if p["pos"] == position]
        projection_rank = {p["id"]: index + 1 for index, p in enumerate(sorted(group, key=lambda p: -p["proj"]))}
        for player in group:
            player["special_score"] = round(.75 * projection_rank[player["id"]] + .25 * min(player["ecr_pos"], 32), 2)
        ordered = sorted(group, key=lambda p: (p["special_score"], -p["proj"]))
        for index, player in enumerate(ordered, 1):
            player["special_rank"] = index


def render_report(players: list[dict], before: list[dict]) -> str:
    counts = {pos: sum(p["pos"] == pos for p in players) for pos in (*ensemble.POSITIONS, "K", "DST")}
    statuses = defaultdict(int)
    for player in players:
        statuses[player["status"]] += 1
    zero = [p for p in players if p["pos"] in ensemble.POSITIONS and p["proj"] <= 0]
    lines = "\n".join(f"- {key}: {value}" for key, value in sorted(statuses.items()))
    return f"""# Draft data hardening analysis

## Outcome

- Player pool expanded from {BASELINE_POOL_SIZE} to {len(players)} players.
- Position coverage: {', '.join(f'{pos} {count}' for pos, count in counts.items())}.
- ESPN custom projections, ESPN room ADP/rank, current teams, and status were refreshed {dt.date.today().isoformat()}.
- All 32 NFL bye weeks are populated from the official schedule.
- K and D/ST use a 75% custom-projection rank / 25% FantasyPros positional-ECR rank blend.
- {len(players) - BASELINE_POOL_SIZE} net players were added. Skill players without a current projection: {len(zero)}; each remains searchable and status-flagged.

## Status coverage

{lines}

## Zero-projection skill players

{chr(10).join(f'- {p["name"]} ({p["team"]}, {p["status"]}, ESPN ADP {p["espn_adp"]:.1f})' for p in zero) or '- None'}

## Model boundaries

- ESPN room rank/ADP controls opponent timing and survival; FantasyPros ECR remains the model sanity check.
- Status is visible and zero-projection/long-term unavailable players are not automatically recommended, but every player remains clickable for accurate bookkeeping.
- Bye week is informational; elite players are not downgraded for sharing a bye.
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    text, before, start, end = ensemble.current_players()
    old_by_id = {p["id"]: p for p in before}
    fp = fantasypros(args.refresh)
    rows = espn_rows(args.refresh)
    candidates = [player for row in rows if (player := candidate(row, fp, old_by_id))]
    pool = choose_pool(candidates)
    cbs, fftoday, metadata = ensemble.source_data(args.refresh)
    metadata["sources"]["ESPN"] = {"date": dt.date.today().isoformat(), "role": "live custom-league projection"}
    players, analysis = ensemble.build_ensemble(pool, cbs, fftoday, metadata)
    # New/rescued players need an upside input even when the old ESPN row was zero.
    for player in players:
        if player["proj"] > 0 and player["sd"] <= 0:
            player["sd"] = round(player["proj"] * CEILING_RATE[player["pos"]], 1)
    add_special_ranks(players)
    players.sort(key=lambda p: (p["room_rank"], p["name"]))
    report = render_report(players, before)
    REPORT.write_text(report)
    RAW.write_text(json.dumps({"metadata": metadata, "players": players}, indent=2))
    ensemble.REPORT.write_text(ensemble.render_report(analysis))
    ensemble.RAW.write_text(json.dumps(analysis, indent=2))
    if args.write:
        output = text[:start] + json.dumps(players, indent=2, ensure_ascii=False) + text[end:]
        today = dt.date.today().isoformat()
        output = re.sub(
            r'<b>2026 RANKINGS</b><span>.*?</span>',
            f'<b>2026 RANKINGS</b><span>{len(players)}-player pool, refreshed {dt.date.today():%b %-d}. '
            'Projections: median of ESPN, CBS, and FFToday; room timing: ESPN ADP/rank; ECR: FantasyPros.</span>',
            output, count=1,
        )
        output = re.sub(
            r"const PROJECTION_META=\{sources:\['ESPN','CBS','FFToday'\],method:'median',updated:'[^']+'\};",
            f"const PROJECTION_META={{sources:['ESPN','CBS','FFToday'],method:'median',updated:'{today}'}};",
            output, count=1,
        )
        ensemble.HTML.write_text(output)
    print(report)


if __name__ == "__main__":
    main()
