#!/usr/bin/env python3
"""Refresh the complete draft-day pool from ESPN and FantasyPros.

ESPN supplies the league-scored projection, room ADP/rank, current NFL team,
and availability status. FantasyPros supplies half-PPR ECR, tiers, and a
second bye-week check. Sleeper supplies an independent availability read that
corroborates ESPN rather than overriding it. CBS/FFToday/Sleeper projections
are then applied by the ensemble updater.
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
FFC_URL = "https://fantasyfootballcalculator.com/api/v1/adp/half-ppr?teams=12&year=2026"
SLEEPER_PLAYERS_URL = "https://api.sleeper.app/v1/players/nfl"

# ESPN and Sleeper describe the same facts with different vocabularies, so
# compare the availability class each implies. "IR" against "INJURY_RESERVE" is
# agreement; only a real severity gap is worth a human's attention on draft day.
# Anything that maps to "unknown" is withheld rather than counted either way.
ESPN_AVAILABILITY_CLASS = {
    "ACTIVE": "available", "QUESTIONABLE": "in doubt", "DOUBTFUL": "in doubt",
    "OUT": "out", "SUSPENSION": "out", "INJURY_RESERVE": "out",
    "COMMISSIONER_EXEMPT": "out", "NON_FOOTBALL_INJURY": "out", "PUP": "out",
}
SLEEPER_AVAILABILITY_CLASS = {
    None: "available", "": "available", "Active": "available",
    "Questionable": "in doubt", "Doubtful": "in doubt",
    "Out": "out", "IR": "out", "PUP": "out", "NFI": "out", "Sus": "out",
    "COV": "out", "DNR": "out", "NA": "unknown",
}

POSITION_ID = {1: "QB", 2: "RB", 3: "WR", 4: "TE", 5: "K", 16: "DST"}
QUOTAS = {"QB": 30, "RB": 70, "WR": 90, "TE": 26}
BASELINE_POOL_SIZE = 205
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

# ESPN can lag official league transactions. These narrow, dated overrides
# keep confirmed availability facts authoritative without guessing a return
# date or changing the player's projection. Remove/update an entry as soon as
# the cited league status changes.
AUTHORITATIVE_AVAILABILITY = {
    4047365: {
        "status": "COMMISSIONER_EXEMPT",
        "availability_note": "Commissioner's Exempt List — cannot practice or play; no return timetable",
        "availability_updated": "2026-09-05",
        "availability_source": "NFL",
        "availability_url": "https://www.nfl.com/news/nfl-places-packers-rb-josh-jacobs-commissioner-exempt-list",
    },
}
AUTHORITATIVE_TEAM = {
    # Acquired by Green Bay on 2026-08-30; ESPN's player team can lag trades.
    4819231: "GB",  # Kaleb Johnson
}
REQUIRED_SKILL_PLAYERS = {"Kaleb Johnson", "Chris Brooks"}


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


def fantasypros(refresh: bool) -> tuple[dict[str, dict], dict]:
    text = fetch(FP_URL, CACHE / "fantasypros_half_ppr.html", refresh)
    marker = "var ecrData = "
    start = text.find(marker)
    if start < 0:
        raise RuntimeError("FantasyPros ECR payload not found")
    payload, _ = json.JSONDecoder().raw_decode(text[start + len(marker):])
    players = payload.get("players") or []
    if (payload.get("type") != "Draft Half PPR" or payload.get("year") != "2026"
            or payload.get("scoring") != "HALF" or len(players) < 200):
        raise RuntimeError("FantasyPros returned an unexpected half-PPR ECR payload")
    try:
        month, day = map(int, payload["last_updated"].split("/"))
        updated = dt.date(dt.date.today().year, month, day)
    except (KeyError, TypeError, ValueError) as exc:
        raise RuntimeError("FantasyPros did not provide a valid ECR update date") from exc
    if not 0 <= (dt.date.today() - updated).days <= 3:
        raise RuntimeError(f"FantasyPros ECR is stale ({updated.isoformat()})")

    groups_marker = "var expertGroupsData = "
    groups_start = text.find(groups_marker)
    if groups_start < 0:
        raise RuntimeError("FantasyPros expert-recency payload not found")
    groups, _ = json.JSONDecoder().raw_decode(text[groups_start + len(groups_marker):])
    default_ids = set(groups["expert_groups"]["default"]["options"][0]["experts"])
    recency_options = groups["recency_groups"]["recency"]["options"]
    if recency_options and isinstance(recency_options[0], list):
        recency_options = recency_options[0]
    recency = {str(option["id"]): set(option["experts"]) for option in recency_options}
    if len(default_ids) < 20 or default_ids != recency.get("7", set()):
        raise RuntimeError("FantasyPros Latest ECR is not the expected seven-day expert panel")
    metadata = {
        "source": "FantasyPros Latest ECR, half-PPR",
        "updated": updated.isoformat(),
        "experts": len(default_ids),
        "updated_1d": len(default_ids & recency.get("1", set())),
        "updated_3d": len(default_ids & recency.get("3", set())),
        "updated_7d": len(default_ids & recency.get("7", set())),
    }
    return {ensemble.normalize(player["player_name"]): player for player in players}, metadata


def fantasyfootballcalculator(refresh: bool) -> tuple[dict[tuple[str, str], dict], dict]:
    """Return current 12-team half-PPR market ADP with observed draft dispersion."""
    payload = json.loads(fetch(FFC_URL, CACHE / "ffc_half_ppr_adp.json", refresh))
    meta = payload.get("meta") or {}
    rows = payload.get("players") or []
    if payload.get("status") != "Success" or meta.get("type") != "Half-PPR" or meta.get("teams") != 12:
        raise RuntimeError("Fantasy Football Calculator returned an unexpected ADP payload")
    if len(rows) < 150:
        raise RuntimeError(f"Fantasy Football Calculator ADP pool is incomplete ({len(rows)} rows)")
    try:
        market_date = dt.date.fromisoformat(meta["end_date"])
    except (KeyError, TypeError, ValueError) as exc:
        raise RuntimeError("Fantasy Football Calculator did not provide a valid market end date") from exc
    if not 0 <= (dt.date.today() - market_date).days <= 3 or int(meta.get("total_drafts") or 0) < 10:
        raise RuntimeError(f"Fantasy Football Calculator market is stale or undersampled ({meta})")
    positions = {"DEF": "DST", "D/ST": "DST"}
    by_player = {}
    for row in rows:
        pos = positions.get(row.get("position"), row.get("position"))
        if pos not in (*ensemble.POSITIONS, "K", "DST"):
            continue
        by_player[(ensemble.normalize(row.get("name", "")), pos)] = row
    return by_player, meta


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


def sleeper_players(refresh: bool) -> dict[tuple[str, str], dict]:
    """Sleeper's full player file, indexed by normalized name and position.

    Sleeper asks callers to pull this ~14MB file at most once a day, so a copy
    already retrieved today is reused even under --refresh.
    """
    path = CACHE / "sleeper_players.json"
    pulled_today = (path.exists() and path.stat().st_size > 1_000_000
                    and ensemble.cache_date(path) == dt.date.today().isoformat())
    payload = json.loads(fetch(SLEEPER_PLAYERS_URL, path, refresh and not pulled_today))
    if not isinstance(payload, dict) or len(payload) < 5000:
        raise RuntimeError(f"Sleeper player file is incomplete ({len(payload)} entries)")
    index: dict[tuple[str, str], dict] = {}
    for row in payload.values():
        name, position = row.get("full_name"), row.get("position")
        if not name or position not in (*ensemble.POSITIONS, "K"):
            continue
        key = (ensemble.normalize(name), position)
        # A name can collide between a rostered player and a free agent; the
        # rostered one is the player this draft is about.
        if key not in index or (row.get("team") and not index[key].get("team")):
            index[key] = row
    return index


def add_sleeper_availability(players: list[dict], sleeper: dict[tuple[str, str], dict]) -> dict:
    """Attach Sleeper's availability read as corroboration, never as an override.

    ESPN remains the status of record and a dated authoritative override still
    outranks both. Sleeper adds an injured body part, its own news recency, and
    a second opinion whose disagreements are surfaced for judgment.
    """
    matched, conflicts = 0, []
    for player in players:
        if player["pos"] == "DST":
            continue
        row = sleeper.get((ensemble.normalize(player["name"]), player["pos"]))
        if not row:
            continue
        matched += 1
        injury = row.get("injury_status") or None
        player["sleeper_status"] = injury or row.get("status") or "Active"
        if row.get("injury_body_part"):
            player["sleeper_body_part"] = row["injury_body_part"]
        if row.get("news_updated"):
            player["sleeper_news"] = dt.datetime.fromtimestamp(
                int(row["news_updated"]) / 1000).date().isoformat()
        espn_class = ESPN_AVAILABILITY_CLASS.get(player.get("status") or "ACTIVE", "unknown")
        sleeper_class = SLEEPER_AVAILABILITY_CLASS.get(injury, "unknown")
        agrees = espn_class == sleeper_class or "unknown" in (espn_class, sleeper_class)
        player["sleeper_agrees"] = agrees
        # A dated human-verified override is already known to contradict ESPN;
        # re-reporting it as a source conflict would be noise.
        if not agrees and not player.get("availability_source"):
            conflicts.append({"name": player["name"], "pos": player["pos"], "team": player["team"],
                              "espn": player.get("status") or "ACTIVE", "espn_class": espn_class,
                              "sleeper": injury, "sleeper_class": sleeper_class,
                              "body_part": row.get("injury_body_part")})
    return {"matched": matched, "eligible": sum(p["pos"] != "DST" for p in players),
            "conflicts": conflicts}


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


def room_rank(adp: float, rank: float) -> float:
    adp = min(adp if 0 < adp < 500 else 400, 400)
    rank = min(rank if 0 < rank < 1000 else 400, 400)
    # Keep player quality (ECR) out of the ESPN room forecast. ECR belongs in
    # Model; including it here also lets consensus alter VONA through survival.
    return .70 * adp + .30 * rank


def candidate(row: dict, fp_by_name: dict[str, dict], ffc_by_player: dict[tuple[str, str], dict],
              ffc_meta: dict, old_by_id: dict[int, dict]) -> dict | None:
    p = row["player"]
    position = POSITION_ID.get(p.get("defaultPositionId"))
    team = AUTHORITATIVE_TEAM.get(p["id"], TEAM_BY_ID.get(p.get("proTeamId")))
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
    room = room_rank(espn_adp, espn_rank)
    market_row = ffc_by_player.get((ensemble.normalize(p["fullName"]), position))
    if position == "DST" and not market_row:
        market_row = next((item for (name, pos), item in ffc_by_player.items()
                           if pos == "DST" and item.get("team") == team), None)
    market_adp = float((market_row or {}).get("adp") or room)
    market_sd = float((market_row or {}).get("stdev") or 0)
    if market_sd <= 0:
        market_sd = float(old.get("adp_sd") or max(6, min(35, 5.8 + .055 * room)))
    same_day = old.get("adp_updated") == dt.date.today().isoformat()
    old_adp = float(old.get("adp_prev" if same_day else "espn_adp", old.get("adp", espn_adp)))
    old_adp_delta = espn_adp - old_adp
    sd = projection * ensemble.CEILING_RATE[position]
    result = {
        "id": p["id"], "name": p["fullName"], "pos": position, "team": team,
        "bye": BYE_BY_TEAM[team], "status": p.get("injuryStatus") or "ACTIVE",
        "injured": bool(p.get("injured")), "last_news": p.get("lastNewsDate"),
        "proj": round(projection, 1), "proj_espn": round(projection, 1), "sd": round(sd, 1),
        "sd_source": "position-rate proxy",
        "adp": round(espn_adp, 1), "espn_adp": round(espn_adp, 1),
        "adp_prev": round(old_adp, 1), "adp_delta": round(old_adp_delta, 1),
        "adp_prev_date": old.get("adp_prev_date" if same_day else "adp_updated", "prior refresh"),
        "adp_updated": dt.date.today().isoformat(),
        "espn_rank": round(espn_rank, 1), "room_rank": round(room, 1),
        "market_adp": round(market_adp, 1), "market_adp_sd": round(market_sd, 1),
        "market_adp_n": int((market_row or {}).get("times_drafted") or 0),
        "market_adp_updated": ffc_meta.get("end_date") if market_row else old.get("market_adp_updated"),
        "adp_sd": round(market_sd, 1), "adp_sd_source": "FFC observed" if market_row else "fallback",
        "ecr": int(ecr),
        "ecr_mean": round(float((fp or {}).get("rank_ave") or old.get("ecr_mean") or ecr), 2),
        "ecr_sd": round(float((fp or {}).get("rank_std") or old.get("ecr_sd") or 0), 2),
        "ecr_min": int(float((fp or {}).get("rank_min") or old.get("ecr_min") or ecr)),
        "ecr_max": int(float((fp or {}).get("rank_max") or old.get("ecr_max") or ecr)),
        "tier": int((fp or {}).get("tier") or old.get("tier") or 99),
        "ecr_pos": position_rank(fp, position), "fp_ranked": bool(fp),
        "percent_owned": round(float(ownership.get("percentOwned") or 0), 1),
    }
    result.update(AUTHORITATIVE_AVAILABILITY.get(p["id"], {}))
    return result


def choose_pool(candidates: list[dict]) -> list[dict]:
    output = []
    for position, quota in QUOTAS.items():
        group = [p for p in candidates if p["pos"] == position]
        useful = [p for p in group if p["fp_ranked"] or p["proj"] > 0 or p["percent_owned"] >= 1]
        useful.sort(key=lambda p: (min(p["ecr"], p["room_rank"]), p["room_rank"], -p["percent_owned"], -p["proj"], p["name"]))
        group = useful + [p for p in group if p not in useful]
        output.extend(group[:quota])

    # Keep newly relevant depth-chart players searchable even before their
    # projection/ownership rises enough to clear the fixed positional quota.
    chosen = {p["id"] for p in output}
    output.extend(p for p in candidates if p["name"] in REQUIRED_SKILL_PLAYERS and p["id"] not in chosen)

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


def render_report(players: list[dict], before: list[dict], source_date: str, ecr_meta: dict,
                  availability: dict) -> str:
    counts = {pos: sum(p["pos"] == pos for p in players) for pos in (*ensemble.POSITIONS, "K", "DST")}
    statuses = defaultdict(int)
    for player in players:
        statuses[player["status"]] += 1
    zero = [p for p in players if p["pos"] in ensemble.POSITIONS and p["proj"] <= 0]
    lines = "\n".join(f"- {key}: {value}" for key, value in sorted(statuses.items()))
    conflicts = availability["conflicts"]
    availability_lines = "\n".join(
        f"- {c['name']} ({c['pos']}, {c['team']}): ESPN {c['espn']} ({c['espn_class']}) vs "
        f"Sleeper {c['sleeper'] or 'no designation'} ({c['sleeper_class']})"
        + (f" — {c['body_part']}" if c["body_part"] else "")
        for c in sorted(conflicts, key=lambda c: c["name"])
    ) or "- No disagreements: ESPN and Sleeper agree on every matched player."
    return f"""# Draft data hardening analysis

## Outcome

- Player pool expanded from {BASELINE_POOL_SIZE} to {len(players)} players.
- Position coverage: {', '.join(f'{pos} {count}' for pos, count in counts.items())}.
- ESPN custom projections, ESPN room ADP/rank, current teams, and status were retrieved {source_date}.
- FantasyPros half-PPR ECR was updated {ecr_meta['updated']} from {ecr_meta['experts']} experts: {ecr_meta['updated_1d']} updated within one day, {ecr_meta['updated_3d']} within three days, and all {ecr_meta['updated_7d']} within seven days.
- All 32 NFL bye weeks are populated from the official schedule.
- D/ST is a streaming board: 55% Week 1, 25% Week 2, 10% Week 3, 7.5% season projection, and 2.5% positional ECR.
- K balances immediate and season-long value: 40% Week 1, 20% Week 2, 10% Week 3, 22.5% season projection, and 7.5% positional ECR.
- {len(players) - BASELINE_POOL_SIZE} net players were added. Skill players without a current projection: {len(zero)}; each remains searchable and status-flagged.
- Sleeper corroborated availability for {availability['matched']}/{availability['eligible']} non-D/ST players; {len(availability['conflicts'])} disagree with ESPN.

## Status coverage

{lines}

## Availability cross-check

ESPN remains the status of record. Sleeper is a second independent read: where
the two disagree, neither is applied automatically — the conflict is listed here
so it can be resolved against the actual league transaction before the draft.

{availability_lines}

## Zero-projection skill players

{chr(10).join(f'- {p["name"]} ({p["team"]}, {p["status"]}, ESPN ADP {p["espn_adp"]:.1f})' for p in zero) or '- None'}

## Model boundaries

- Opponent timing and survival are market-first: RB/WR/TE blend 80% current Fantasy Football Calculator 12-team half-PPR ADP with 20% ESPN-only room rank/ADP, QB blends 50/50, K/DST are unchanged. Its observed draft standard deviation drives availability uncertainty when matched, widened when ESPN and market disagree; FantasyPros ECR remains separate as the Model sanity check.
- FantasyPros supplies not only ECR but each player's expert mean, standard deviation, and range. Those disagreement fields are exported for judgment and are not silently converted into another ranking weight.
- Status is visible and zero-projection/long-term unavailable players are not automatically recommended, but every player remains clickable for accurate bookkeeping.
- Bye week is informational; elite players are not downgraded for sharing a bye.
"""


def render_special_report(players: list[dict], source_date: str) -> str:
    def table(position: str) -> str:
        group = sorted((p for p in players if p["pos"] == position), key=lambda p: p["special_rank"])
        return "\n".join(
            f'| {p["special_rank"]} | {p["name"]} | {p["team"]} | {p["week1_opp"]} | {p["week1_proj"]:.1f} | '
            f'{p["week2_opp"]} | {p["week2_proj"]:.1f} | {p["week3_opp"]} | {p["week3_proj"]:.1f} | '
            f'{p["proj"]:.1f} | {p["ecr_pos"]} |'
            for p in group[:16]
        )

    return f"""# Early-season special-teams streaming board

Generated from ESPN's authenticated weekly projections retrieved {source_date} and scored under this league's custom settings.

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
    if args.write and not args.refresh:
        parser.error("--write requires --refresh so the live app cannot publish cached data with a fresh timestamp")
    text, before, start, end = ensemble.current_players()
    old_by_id = {p["id"]: p for p in before}
    fp, ecr_meta = fantasypros(args.refresh)
    ffc, ffc_meta = fantasyfootballcalculator(args.refresh)
    rows = espn_rows(args.refresh)
    weekly_rows = {period: espn_rows(args.refresh, period) for period in (1, 2, 3)}
    schedule = espn_schedule(args.refresh)
    candidates = [player for row in rows if (player := candidate(row, fp, ffc, ffc_meta, old_by_id))]
    pool = choose_pool(candidates)
    sleeper_pool = sleeper_players(args.refresh)
    cbs, fftoday, sleeper_proj, metadata = ensemble.source_data(args.refresh)
    metadata["sources"]["ESPN"] = {
        "date": ensemble.cache_date(CACHE / "espn_players.json"),
        "role": "live custom-league projection",
    }
    metadata["sources"]["Sleeper availability"] = {
        "date": ensemble.cache_date(CACHE / "sleeper_players.json"),
        "role": "independent status cross-check, never an override",
    }
    fd_rates = ensemble.player_first_down_rates(args.refresh)
    players, analysis = ensemble.build_ensemble(pool, cbs, fftoday, sleeper_proj, metadata, fd_rates)
    availability = add_sleeper_availability(players, sleeper_pool)
    analysis["availability_cross_check"] = availability
    add_weekly_projections(players, weekly_rows, schedule)
    add_special_ranks(players)
    players.sort(key=lambda p: (p["room_rank"], p["name"]))
    espn_source_date = ensemble.cache_date(CACHE / "espn_players.json")
    report = render_report(players, before, espn_source_date, ecr_meta, availability)
    REPORT.write_text(report)
    SPECIAL_REPORT.write_text(render_special_report(players, espn_source_date))
    RAW.write_text(json.dumps({"metadata": metadata, "players": players}, indent=2))
    ensemble.REPORT.write_text(ensemble.render_report(analysis))
    ensemble.RAW.write_text(json.dumps(analysis, indent=2))
    if args.write:
        output = text[:start] + json.dumps(players, indent=2, ensure_ascii=False) + text[end:]
        today = dt.date.today().isoformat()
        output = re.sub(
            r'<b>2026 RANKINGS</b><span>.*?</span>',
            f'<b>2026 RANKINGS</b><span>{len(players)}-player pool, refreshed {dt.date.today():%b %-d}. '
            'Projections: median of ESPN, CBS, FFToday, and Sleeper; timing: market-first blend, 80% current 12-team half-PPR market for RB/WR/TE and 50% for QB, ESPN room fills the rest (K/DST unchanged, rounds 13-14 only).</span>',
            output, count=1,
        )
        output = re.sub(
            r"const PROJECTION_META=\{sources:\[[^\]]*\],method:'median',updated:'[^']+'\};",
            f"const PROJECTION_META={{sources:['ESPN','CBS','FFToday','Sleeper'],method:'median',updated:'{today}'}};",
            output, count=1,
        )
        output = re.sub(
            r"// Projections: robust median of [^,]+(?:, [^,]+)*, refreshed \d{4}-\d{2}-\d{2}\.",
            f"// Projections: robust median of ESPN, CBS, FFToday, and Sleeper, refreshed {today}.",
            output, count=1,
        )
        output = re.sub(
            r"const MARKET_META=\{source:'[^']+',updated:'[^']+',drafts:\d+\};",
            f"const MARKET_META={{source:'Fantasy Football Calculator 12-team half-PPR',"
            f"updated:'{ffc_meta.get('end_date', today)}',drafts:{int(ffc_meta.get('total_drafts') or 0)}}};",
            output, count=1,
        )
        output = re.sub(
            r"const ECR_META=\{source:'[^']+',updated:'[^']+',experts:\d+,updated1d:\d+,updated3d:\d+,updated7d:\d+\};",
            f"const ECR_META={{source:'FantasyPros Latest ECR, half-PPR',updated:'{ecr_meta['updated']}',"
            f"experts:{ecr_meta['experts']},updated1d:{ecr_meta['updated_1d']},"
            f"updated3d:{ecr_meta['updated_3d']},updated7d:{ecr_meta['updated_7d']}}};",
            output, count=1,
        )
        output = re.sub(
            r"<b>Projection</b> is the median of [^.]+\.",
            "<b>Projection</b> is the median of ESPN, CBS, FFToday, and Sleeper (Rotowire) when available.",
            output, count=1,
        )
        output = re.sub(
            r"CBS and FFToday raw stat lines are rescored locally",
            "CBS, FFToday, and Sleeper raw stat lines are rescored locally",
            output,
        )
        output = re.sub(
            r"player-specific 2023–(?:24|25) first-down rates regressed toward position averages;(?: rookies and unmatched players use the position rate\.)?",
            "player-specific 2023–25 first-down rates regressed toward position averages; rookies and unmatched players use the position rate.",
            output,
        )
        ensemble.HTML.write_text(output)
    print(report)


if __name__ == "__main__":
    main()
