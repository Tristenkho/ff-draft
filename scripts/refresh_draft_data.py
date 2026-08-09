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
SPECIAL_REPORT = ROOT / "out" / "special_teams_streaming_analysis.md"
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


def espn_rows(refresh: bool, scoring_period: int = 0) -> list[dict]:
    creds = json.loads(CREDS.read_text())
    url = ("https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl"
           f"/seasons/{creds.get('season', 2026)}/segments/0/leagues/{creds['league_id']}"
           f"?scoringPeriodId={scoring_period}&view=kona_player_info")
    fantasy_filter = {"players": {"limit": 1000, "sortPercOwned": {"sortPriority": 1, "sortAsc": False},
                                   "filterActive": {"value": True}}}
    headers = {
        "Cookie": f"espn_s2={creds['espn_s2']}; SWID={creds['swid']}",
        "Accept": "application/json", "x-fantasy-filter": json.dumps(fantasy_filter),
    }
    cache_name = "espn_players.json" if scoring_period == 0 else f"espn_players_week_{scoring_period}.json"
    return json.loads(fetch(url, CACHE / cache_name, refresh, headers))["players"]


def fantasypros(refresh: bool) -> dict[str, dict]:
    text = fetch(FP_URL, CACHE / "fantasypros_half_ppr.html", refresh)
    marker = '"players":[{"player_id":22968'
    start = text.find(marker)
    if start < 0:
        raise RuntimeError("FantasyPros player payload not found")
    players, _ = json.JSONDecoder().raw_decode(text[start + len('"players":'):])
    return {ensemble.normalize(player["player_name"]): player for player in players}


def espn_schedule(refresh: bool) -> dict[int, dict[str, str]]:
    aliases = {"JAC": "JAX", "WSH": "WAS"}
    result = {}
    for week in (1, 2, 3):
        url = ("https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
               f"?dates=2026&seasontype=2&week={week}&limit=100")
        payload = json.loads(fetch(url, CACHE / f"espn_schedule_week_{week}.json", refresh,
                                   {"User-Agent": "Python-urllib/3.14"}))
        matchups = {}
        for event in payload.get("events", []):
            competitors = event["competitions"][0]["competitors"]
            if len(competitors) != 2:
                continue
            for team, opponent in ((competitors[0], competitors[1]), (competitors[1], competitors[0])):
                abbreviation = aliases.get(team["team"]["abbreviation"], team["team"]["abbreviation"])
                other = aliases.get(opponent["team"]["abbreviation"], opponent["team"]["abbreviation"])
                matchups[abbreviation] = ("vs " if team["homeAway"] == "home" else "@ ") + other
        result[week] = matchups
    return result


def season_projection(player: dict) -> float:
    values = [stat.get("appliedTotal", 0) for stat in player.get("stats", [])
              if stat.get("seasonId") == 2026 and stat.get("scoringPeriodId") == 0
              and stat.get("statSourceId") == 1 and stat.get("statSplitTypeId") == 0]
    return float(values[0]) if values else 0.0


def weekly_projection(player: dict, scoring_period: int) -> float:
    values = [stat.get("appliedTotal", 0) for stat in player.get("stats", [])
              if stat.get("seasonId") == 2026 and stat.get("scoringPeriodId") == scoring_period
              and stat.get("statSourceId") == 1 and stat.get("statSplitTypeId") == 1]
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
    same_day = old.get("adp_updated") == dt.date.today().isoformat()
    old_adp = float(old.get("adp_prev" if same_day else "espn_adp", old.get("adp", espn_adp)))
    old_adp_delta = float(old.get("adp_delta", espn_adp - old_adp)) if same_day else espn_adp - old_adp
    sd = float(old.get("sd") or projection * CEILING_RATE[position])
    return {
        "id": p["id"], "name": p["fullName"], "pos": position, "team": team,
        "bye": BYE_BY_TEAM[team], "status": p.get("injuryStatus") or "ACTIVE",
        "injured": bool(p.get("injured")), "last_news": p.get("lastNewsDate"),
        "proj": round(projection, 1), "proj_espn": round(projection, 1), "sd": round(sd, 1),
        "adp": round(espn_adp, 1), "espn_adp": round(espn_adp, 1),
        "adp_prev": round(old_adp, 1), "adp_delta": round(old_adp_delta, 1),
        "adp_prev_date": old.get("adp_prev_date" if same_day else "adp_updated", "prior refresh"),
        "adp_updated": dt.date.today().isoformat(),
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


def add_weekly_projections(players: list[dict], weekly_rows: dict[int, list[dict]], schedule: dict[int, dict[str, str]]) -> None:
    weekly_by_period = {
        period: {row["player"]["id"]: row["player"] for row in rows}
        for period, rows in weekly_rows.items()
    }
    for player in players:
        if player["pos"] not in ("K", "DST"):
            continue
        for period in (1, 2, 3):
            weekly = weekly_by_period[period].get(player["id"], {})
            player[f"week{period}_proj"] = round(weekly_projection(weekly, period), 1)
            player[f"week{period}_opp"] = schedule[period].get(player["team"], "TBD")


def add_special_ranks(players: list[dict]) -> None:
    for position in ("K", "DST"):
        group = [p for p in players if p["pos"] == position]
        ranks = {
            field: {p["id"]: index + 1 for index, p in enumerate(
                sorted(group, key=lambda p: (-p[field], -p["proj"], p["name"])))}
            for field in ("week1_proj", "week2_proj", "week3_proj", "proj")
        }
        weights = ({"week1_proj": .40, "week2_proj": .20, "week3_proj": .10, "proj": .225, "ecr": .075}
                   if position == "K" else
                   {"week1_proj": .55, "week2_proj": .25, "week3_proj": .10, "proj": .075, "ecr": .025})
        for player in group:
            score = sum(weight * ranks[field][player["id"]] for field, weight in weights.items() if field != "ecr")
            score += weights["ecr"] * min(player["ecr_pos"], 32)
            player["special_score"] = round(score, 2)
            player["special_mode"] = "weekly fallback" if position == "K" else "early stream"
        ordered = sorted(group, key=lambda p: (p["special_score"], -p["week1_proj"], -p["proj"]))
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
- D/ST is a streaming board: 55% Week 1, 25% Week 2, 10% Week 3, 7.5% season projection, and 2.5% positional ECR.
- K balances immediate and season-long value: 40% Week 1, 20% Week 2, 10% Week 3, 22.5% season projection, and 7.5% positional ECR.
- {len(players) - BASELINE_POOL_SIZE} net players were added. Skill players without a current projection: {len(zero)}; each remains searchable and status-flagged.

## Status coverage

{lines}

## Zero-projection skill players

{chr(10).join(f'- {p["name"]} ({p["team"]}, {p["status"]}, ESPN ADP {p["espn_adp"]:.1f})' for p in zero) or '- None'}

## Model boundaries

- Opponent timing and survival blend 60% ESPN room rank/ADP with 40% FantasyPros half-PPR ADP; FantasyPros ECR remains the model sanity check.
- Status is visible and zero-projection/long-term unavailable players are not automatically recommended, but every player remains clickable for accurate bookkeeping.
- Bye week is informational; elite players are not downgraded for sharing a bye.
"""


def render_special_report(players: list[dict]) -> str:
    def table(position: str) -> str:
        group = sorted((p for p in players if p["pos"] == position), key=lambda p: p["special_rank"])
        return "\n".join(
            f'| {p["special_rank"]} | {p["name"]} | {p["team"]} | {p["week1_opp"]} | {p["week1_proj"]:.1f} | '
            f'{p["week2_opp"]} | {p["week2_proj"]:.1f} | {p["week3_opp"]} | {p["week3_proj"]:.1f} | '
            f'{p["proj"]:.1f} | {p["ecr_pos"]} |'
            for p in group[:16]
        )

    return f"""# Early-season special-teams streaming board

Generated {dt.date.today().isoformat()} from ESPN's authenticated weekly projections scored under this league's custom settings.

## Draft policy

- Keep K and D/ST out of VONA and wait until Rounds 13–14.
- D/ST is treated as a stream, not a season-long hold: Week 1 carries 55% of its rank, Week 2 25%, Week 3 10%, season projection 7.5%, and positional ECR 2.5%.
- K keeps more season-long signal because elite kickers can be worth holding: Week 1 carries 40%, Week 2 20%, Week 3 10%, season projection 22.5%, and positional ECR 7.5%. If the preferred options are gone, the remaining order naturally becomes an early-week streaming list.
- Weekly projections are volatile and should be refreshed near the draft and again before setting the Week 1 lineup. Opponent, injuries, depth-chart changes, weather, and betting markets can materially change this order.

## D/ST early-stream board

| Rank | Defense | Team | W1 opp | W1 pts | W2 opp | W2 pts | W3 opp | W3 pts | Season | ECR pos |
| ---: | --- | --- | --- | ---: | --- | ---: | --- | ---: | ---: | ---: |
{table("DST")}

## Kicker draft/fallback board

| Rank | Kicker | Team | W1 opp | W1 pts | W2 opp | W2 pts | W3 opp | W3 pts | Season | ECR pos |
| ---: | --- | --- | --- | ---: | --- | ---: | --- | ---: | ---: | ---: |
{table("K")}

## Interpretation

This ranking is a draft-day acquisition list, not a promise to hold the player. For D/ST, prioritize the best Week 1 option still available and reassess weekly. For K, hold a top option while usage and offense remain strong; otherwise stream based on the next matchup rather than protecting draft capital.
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
    weekly_rows = {period: espn_rows(args.refresh, period) for period in (1, 2, 3)}
    schedule = espn_schedule(args.refresh)
    candidates = [player for row in rows if (player := candidate(row, fp, old_by_id))]
    pool = choose_pool(candidates)
    cbs, fftoday, metadata = ensemble.source_data(args.refresh)
    metadata["sources"]["ESPN"] = {"date": dt.date.today().isoformat(), "role": "live custom-league projection"}
    fd_rates = ensemble.player_first_down_rates(args.refresh)
    players, analysis = ensemble.build_ensemble(pool, cbs, fftoday, metadata, fd_rates)
    add_weekly_projections(players, weekly_rows, schedule)
    # New/rescued players need an upside input even when the old ESPN row was zero.
    for player in players:
        if player["proj"] > 0 and player["sd"] <= 0:
            player["sd"] = round(player["proj"] * CEILING_RATE[player["pos"]], 1)
    add_special_ranks(players)
    players.sort(key=lambda p: (p["room_rank"], p["name"]))
    report = render_report(players, before)
    REPORT.write_text(report)
    SPECIAL_REPORT.write_text(render_special_report(players))
    RAW.write_text(json.dumps({"metadata": metadata, "players": players}, indent=2))
    ensemble.REPORT.write_text(ensemble.render_report(analysis))
    ensemble.RAW.write_text(json.dumps(analysis, indent=2))
    if args.write:
        output = text[:start] + json.dumps(players, indent=2, ensure_ascii=False) + text[end:]
        today = dt.date.today().isoformat()
        output = re.sub(
            r'<b>2026 RANKINGS</b><span>.*?</span>',
            f'<b>2026 RANKINGS</b><span>{len(players)}-player pool, refreshed {dt.date.today():%b %-d}. '
            'Projections: median of ESPN, CBS, and FFToday; timing: 60% ESPN room + 40% FantasyPros ADP.</span>',
            output, count=1,
        )
        output = re.sub(
            r"const PROJECTION_META=\{sources:\['ESPN','CBS','FFToday'\],method:'median',updated:'[^']+'\};",
            f"const PROJECTION_META={{sources:['ESPN','CBS','FFToday'],method:'median',updated:'{today}'}};",
            output, count=1,
        )
        output = re.sub(
            r"player-specific 2024–25 first-down rates regressed toward position averages;(?: rookies and unmatched players use the position rate\.)?",
            "player-specific 2023–24 first-down rates regressed toward position averages; rookies and unmatched players use the position rate.",
            output,
        )
        ensemble.HTML.write_text(output)
    print(report)


if __name__ == "__main__":
    main()
