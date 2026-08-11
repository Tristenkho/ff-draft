#!/usr/bin/env python3
"""Refresh the 2026 ESPN/CBS/FFToday projection ensemble in the HTML app."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import math
import re
import ssl
import statistics
import unicodedata
import urllib.request
from pathlib import Path

import certifi
from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "out" / "draft_terminal.html"
CACHE = ROOT / ".cache" / "projection-ensemble-2026"
RAW = ROOT / "out" / "projection_ensemble_raw.json"
REPORT = ROOT / "out" / "projection_ensemble_analysis.md"
NFLVERSE_URL = "https://github.com/nflverse/nflverse-data/releases/download/player_stats/player_stats.csv"
POSITIONS = ("QB", "RB", "WR", "TE")
CBS_URL = "https://www.cbssports.com/fantasy/football/stats/{pos}/2026/season/projections/ppr/"
FFTODAY_URL = "https://www.fftoday.com/rankings/playerproj.php?Season=2026&PosID={pos_id}&LeagueID=1&cur_page={page}"
FFTODAY_POS = {"QB": 10, "RB": 20, "WR": 30, "TE": 40}
PASS_FD_PER_COMPLETION = .518
REC_FD = {"RB": .325, "WR": .597, "TE": .511}
RUSH_FD = {"QB": .344, "RB": .224, "WR": .291, "TE": .224}
# Half the robust 2018-23 preseason residual scale. This represents shared
# outcome/role uncertainty; source disagreement is added separately below.
HISTORICAL_UNCERTAINTY = {"QB": .156, "RB": .260, "WR": .212, "TE": .229}
RATE_PRIOR = {"pass": 300, "rush": 120, "rec": 80}


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode().lower()
    value = re.sub(r"\b(jr|sr|ii|iii|iv)\b", "", value)
    value = re.sub(r"[^a-z0-9]", "", value)
    aliases = {
        "hollywoodbrown": "marquisebrown", "kennygainwell": "kennethgainwell",
        "joshuapalmer": "joshpalmer", "gabedavis": "gabrieldavis",
        "ajbarner": "a.j.barner", "djmoore": "d.j.moore",
    }
    return aliases.get(value, value).replace(".", "")


def number(value: str) -> float:
    value = re.sub(r"[^0-9.\-]", "", value or "")
    return float(value) if value not in ("", "-", ".") else 0.0


def download(url: str, path: Path, refresh: bool) -> str:
    if refresh or not path.exists() or path.stat().st_size < 1000:
        path.parent.mkdir(parents=True, exist_ok=True)
        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 ff-draft-projection-refresh"})
        context = ssl.create_default_context(cafile=certifi.where())
        with urllib.request.urlopen(request, timeout=120, context=context) as response:
            path.write_bytes(response.read())
    return path.read_text(errors="replace")


def current_players() -> tuple[str, list[dict], int, int]:
    text = HTML.read_text()
    marker = "const PLAYERS="
    start = text.index(marker) + len(marker)
    end = text.index(";\n\n// ── extended constants", start)
    return text, json.loads(text[start:end]), start, end


def player_name_and_team(cell) -> tuple[str, str]:
    long_name = cell.select_one(".CellPlayerName--long a")
    if not long_name:
        return "", ""
    team = cell.select_one(".CellPlayerName--long .CellPlayerName-team")
    return long_name.get_text(" ", strip=True), team.get_text(" ", strip=True) if team else ""


def parse_cbs(position: str, html: str) -> dict[str, dict]:
    soup = BeautifulSoup(html, "html.parser")
    output = {}
    for row in soup.select("tr.TableBase-bodyTr"):
        cells = row.find_all("td", recursive=False)
        if not cells:
            continue
        name, team = player_name_and_team(cells[0])
        values = [number(cell.get_text(" ", strip=True)) for cell in cells[1:]]
        if not name:
            continue
        stats = {"source": "CBS", "name": name, "team": team, "pos": position}
        try:
            if position == "QB":
                stats.update(pass_att=values[1], completions=values[2], pass_yds=values[3], pass_td=values[5], interceptions=values[6],
                             rush_att=values[8], rush_yds=values[9], rush_td=values[11], fumbles=values[12])
            elif position == "RB":
                stats.update(rush_att=values[1], rush_yds=values[2], rush_td=values[4], receptions=values[6],
                             rec_yds=values[7], rec_td=values[10], fumbles=values[11])
            elif position == "WR":
                stats.update(receptions=values[2], rec_yds=values[3], rec_td=values[6], rush_att=values[7],
                             rush_yds=values[8], rush_td=values[10], fumbles=values[11])
            else:
                stats.update(receptions=values[2], rec_yds=values[3], rec_td=values[6], fumbles=values[7])
        except IndexError:
            continue
        output[normalize(name)] = stats
    return output


def parse_fftoday(position: str, pages: list[str]) -> dict[str, dict]:
    output = {}
    for html in pages:
        soup = BeautifulSoup(html, "html.parser")
        for row in soup.find_all("tr"):
            link = row.find("a", href=lambda href: href and "/stats/players/" in href)
            if not link:
                continue
            cells = row.find_all("td", recursive=False)
            values = [cell.get_text(" ", strip=True) for cell in cells]
            try:
                index = next(i for i, cell in enumerate(cells) if cell.find("a", href=lambda href: href and "/stats/players/" in href))
            except StopIteration:
                continue
            name = link.get_text(" ", strip=True)
            trailing = values[index + 1:]
            if len(trailing) < 4:
                continue
            team = trailing[0]
            nums = [number(value) for value in trailing[2:]]  # skip team and bye
            stats = {"source": "FFToday", "name": name, "team": team, "pos": position}
            try:
                if position == "QB":
                    stats.update(completions=nums[0], pass_att=nums[1], pass_yds=nums[2], pass_td=nums[3], interceptions=nums[4],
                                 rush_att=nums[5], rush_yds=nums[6], rush_td=nums[7], fumbles=0)
                elif position == "RB":
                    stats.update(rush_att=nums[0], rush_yds=nums[1], rush_td=nums[2], receptions=nums[3],
                                 rec_yds=nums[4], rec_td=nums[5], fumbles=0)
                elif position == "WR":
                    stats.update(receptions=nums[0], rec_yds=nums[1], rec_td=nums[2], rush_att=nums[3],
                                 rush_yds=nums[4], rush_td=nums[5], fumbles=0)
                else:
                    stats.update(receptions=nums[0], rec_yds=nums[1], rec_td=nums[2], fumbles=0)
            except IndexError:
                continue
            output[normalize(name)] = stats
    return output


def player_first_down_rates(refresh: bool) -> dict[tuple[str, str], dict]:
    """Return 2023-24 player rates shrunk toward the empirical position mean."""
    text = download(NFLVERSE_URL, CACHE / "nflverse_player_stats.csv", refresh)
    totals: dict[tuple[str, str], dict[str, float]] = {}
    for row in csv.DictReader(text.splitlines()):
        if row.get("season") not in ("2023", "2024") or row.get("season_type") != "REG":
            continue
        pos = row.get("position", "")
        if pos not in POSITIONS:
            continue
        key = (normalize(row.get("player_display_name") or row.get("player_name") or ""), pos)
        item = totals.setdefault(key, {"pass_n": 0, "pass_fd": 0, "rush_n": 0, "rush_fd": 0,
                                       "rec_n": 0, "rec_fd": 0})
        for field in item:
            source = {"pass_n": "completions", "pass_fd": "passing_first_downs",
                      "rush_n": "carries", "rush_fd": "rushing_first_downs",
                      "rec_n": "receptions", "rec_fd": "receiving_first_downs"}[field]
            item[field] += number(row.get(source, "0"))

    output = {}
    for (name, pos), item in totals.items():
        rates = dict(item)
        if pos == "QB":
            rates["pass_rate"] = (item["pass_fd"] + RATE_PRIOR["pass"] * PASS_FD_PER_COMPLETION) / (item["pass_n"] + RATE_PRIOR["pass"])
        if pos in RUSH_FD:
            rates["rush_rate"] = (item["rush_fd"] + RATE_PRIOR["rush"] * RUSH_FD[pos]) / (item["rush_n"] + RATE_PRIOR["rush"])
        if pos in REC_FD:
            rates["rec_rate"] = (item["rec_fd"] + RATE_PRIOR["rec"] * REC_FD[pos]) / (item["rec_n"] + RATE_PRIOR["rec"])
        output[(name, pos)] = rates
    return output


def custom_score(stats: dict, rates: dict | None = None) -> float:
    pos = stats["pos"]
    rates = rates or {}
    score = 0.0
    if pos == "QB":
        score += .04 * stats.get("pass_yds", 0) + 4 * stats.get("pass_td", 0) - 2 * stats.get("interceptions", 0)
        score += .1 * rates.get("pass_rate", PASS_FD_PER_COMPLETION) * stats.get("completions", 0)
    score += .1 * stats.get("rush_yds", 0) + 6 * stats.get("rush_td", 0)
    score += .25 * rates.get("rush_rate", RUSH_FD[pos]) * stats.get("rush_att", 0)
    if pos != "QB":
        score += .5 * stats.get("receptions", 0) + .1 * stats.get("rec_yds", 0) + 6 * stats.get("rec_td", 0)
        score += .5 * rates.get("rec_rate", REC_FD[pos]) * stats.get("receptions", 0)
    score -= 2 * stats.get("fumbles", 0)
    return score


def source_data(refresh: bool) -> tuple[dict, dict, dict]:
    cbs, fftoday, metadata = {}, {}, {"season": 2026, "fetched": dt.date.today().isoformat(), "sources": {}}
    for pos in POSITIONS:
        cbs_html = download(CBS_URL.format(pos=pos), CACHE / f"cbs_{pos.lower()}.html", refresh)
        cbs[pos] = parse_cbs(pos, cbs_html)
        pages = [download(FFTODAY_URL.format(pos_id=FFTODAY_POS[pos], page=page), CACHE / f"fftoday_{pos.lower()}_{page}.html", refresh) for page in (0, 1)]
        fftoday[pos] = parse_fftoday(pos, pages)
    metadata["sources"] = {
        "ESPN": {"date": "2026-08-07", "role": "existing custom projection"},
        "CBS": {"date": dt.date.today().isoformat(), "role": "raw stat projection rescored locally"},
        "FFToday": {"date": "2026-08-06", "role": "raw stat projection rescored locally"},
    }
    return cbs, fftoday, metadata


def rank_map(players: list[dict], field: str) -> dict[int, int]:
    skill = [player for player in players if player["pos"] in POSITIONS]
    ordered = sorted(skill, key=lambda player: player[field], reverse=True)
    return {player["id"]: index + 1 for index, player in enumerate(ordered)}


def build_ensemble(players: list[dict], cbs: dict, fftoday: dict, metadata: dict,
                   fd_rates: dict[tuple[str, str], dict] | None = None) -> tuple[list[dict], dict]:
    espn_players = [{**player, "proj": player.get("proj_espn", player["proj"])} for player in players]
    original_rank = rank_map(espn_players, "proj")
    rows, updated = [], []
    for player in players:
        espn = float(player.get("proj_espn", player["proj"]))
        old = espn
        sources = {"ESPN": espn} if espn > 0 or player["pos"] not in POSITIONS else {}
        if player["pos"] in POSITIONS:
            key = normalize(player["name"])
            rates = (fd_rates or {}).get((key, player["pos"]), {})
            if key in cbs[player["pos"]]:
                sources["CBS"] = custom_score(cbs[player["pos"]][key], rates)
            if key in fftoday[player["pos"]]:
                sources["FFToday"] = custom_score(fftoday[player["pos"]][key], rates)
        else:
            rates = {}
        values = list(sources.values())
        if not values:
            values = [espn]
        projection = statistics.median(values) if values else espn
        disagreement = statistics.pstdev(values) if len(values) >= 2 else 0
        if player["pos"] in HISTORICAL_UNCERTAINTY and len(values) >= 2:
            floor = HISTORICAL_UNCERTAINTY[player["pos"]] * projection
            uncertainty = math.sqrt(floor * floor + disagreement * disagreement)
        else:
            uncertainty = 0.0
        changed = dict(player)
        # `sd` is the app's upside/ceiling input. Projection disagreement is a
        # confidence measure, not player upside, so keep those concepts separate.
        spread_ratio = (max(values) - min(values)) / projection if projection > 0 else 1
        reliability = "low" if len(sources) <= 1 or projection <= 0 else "medium" if len(sources) == 2 or spread_ratio > .25 else "high"
        changed.update(proj=round(projection, 1), proj_espn=round(espn, 1), proj_unc=round(uncertainty, 1), proj_n=len(sources),
                       proj_low=round(min(values), 1), proj_high=round(max(values), 1), proj_reliability=reliability,
                       fd_rec_rate=round(rates.get("rec_rate", REC_FD.get(player["pos"], 0)), 3),
                       fd_rush_rate=round(rates.get("rush_rate", RUSH_FD.get(player["pos"], 0)), 3),
                       fd_pass_rate=round(rates.get("pass_rate", PASS_FD_PER_COMPLETION if player["pos"] == "QB" else 0), 3),
                       fd_rate_n=int(rates.get("rec_n", 0) + rates.get("rush_n", 0) + rates.get("pass_n", 0)))
        updated.append(changed)
        rows.append({"id": player["id"], "name": player["name"], "pos": player["pos"], "team": player["team"],
                     "old_proj": old, "new_proj": changed["proj"], "ceiling_sd": changed["sd"], "proj_unc": changed["proj_unc"],
                     "sources": {name: round(value, 2) for name, value in sources.items()}})
    new_rank = rank_map(updated, "proj")
    for row in rows:
        if row["pos"] in POSITIONS:
            row["old_rank"] = original_rank[row["id"]]
            row["new_rank"] = new_rank[row["id"]]
            row["rank_change"] = row["old_rank"] - row["new_rank"]
    skill_rows = [row for row in rows if row["pos"] in POSITIONS]
    coverage = {pos: {
        "players": sum(row["pos"] == pos for row in skill_rows),
        "three_sources": sum(row["pos"] == pos and len(row["sources"]) == 3 for row in skill_rows),
        "two_plus_sources": sum(row["pos"] == pos and len(row["sources"]) >= 2 for row in skill_rows),
    } for pos in POSITIONS}
    analysis = {"metadata": metadata, "coverage": coverage,
                "fd_player_matches": sum(p["pos"] in POSITIONS and p.get("fd_rate_n", 0) > 0 for p in updated),
                "players": rows}
    return updated, analysis


def render_report(analysis: dict) -> str:
    skill = [row for row in analysis["players"] if row["pos"] in POSITIONS]
    covered = [row for row in skill if len(row["sources"]) >= 2]
    three = [row for row in skill if len(row["sources"]) == 3]
    movers = sorted(covered, key=lambda row: abs(row.get("rank_change", 0)), reverse=True)[:20]
    disagreements = sorted(three, key=lambda row: max(row["sources"].values()) - min(row["sources"].values()), reverse=True)[:20]
    coverage_rows = "\n".join(
        f"| {pos} | {value['three_sources']}/{value['players']} | {value['two_plus_sources']}/{value['players']} |"
        for pos, value in analysis["coverage"].items()
    )
    mover_rows = "\n".join(
        f"| {row['name']} | {row['pos']} | {row['old_proj']:.1f} | {row['new_proj']:.1f} | {row['old_rank']} | {row['new_rank']} | {row['rank_change']:+d} |"
        for row in movers
    )
    disagreement_rows = "\n".join(
        f"| {row['name']} | {row['pos']} | {row['sources'].get('ESPN', float('nan')):.1f} | {row['sources']['CBS']:.1f} | {row['sources']['FFToday']:.1f} | "
        f"{row['new_proj']:.1f} | {row['proj_unc']:.1f} |"
        for row in disagreements
    )
    mean_change = statistics.mean(abs(row["new_proj"] - row["old_proj"]) for row in covered)
    return f"""# 2026 projection ensemble analysis

## Outcome

- ESPN, CBS, and FFToday are combined with a robust median when available.
- CBS and FFToday raw stat lines are rescored under the league's passing, rushing, receiving, first-down, and fumble rules.
- ADP and ECR are not projection inputs.
- Player-specific 2023-24 first-down rates are regressed toward position averages before CBS/FFToday are rescored; matched players: {analysis['fd_player_matches']}/{len(skill)}.
- Mean absolute projection change among matched players: {mean_change:.1f} points.
- Three-source coverage: {len(three)}/{len(skill)} skill players ({100*len(three)/len(skill):.1f}%).
- Two-or-more-source coverage: {len(covered)}/{len(skill)} skill players ({100*len(covered)/len(skill):.1f}%).

## Coverage

| Position | Three sources | At least two sources |
| --- | ---: | ---: |
{coverage_rows}

## Largest overall projection-rank changes

Positive means the ensemble moves the player up.

| Player | Pos | ESPN/custom | Ensemble | Old rank | New rank | Change |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
{mover_rows}

## Largest source disagreements

| Player | Pos | ESPN | CBS | FFToday | Median | Uncertainty |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
{disagreement_rows}

## Uncertainty

The separate player `proj_unc` field combines a position-specific historical residual floor with current source disagreement in quadrature. The residual floors are half of the robust 2018–2023 preseason error scale: QB 15.6%, RB 26.0%, WR 21.2%, and TE 22.9%. This prevents three similar projections from implying false certainty while increasing uncertainty when sources materially disagree. It deliberately does not replace `sd`, which remains the app's ceiling/upside input; treating forecast error as upside created a position bias in validation.

## Limitations

- ESPN is the current authenticated league-scored projection embedded by `refresh_draft_data.py`.
- CBS and FFToday do not project first downs, so player-specific 2023–24 reception/carry/completion rates are regressed toward the position baseline; rookies and unmatched players use that baseline.
- FFToday does not expose projected fumbles in its public table; its source score therefore omits that small component. CBS and ESPN retain their fumble assumptions.
- K and D/ST use ESPN's league-scored season and Weeks 1–3 projections because equivalent raw multi-source scoring was not available under this league's distance and defense-tier rules. D/ST is ranked primarily for early streaming; kicker retains more season-long and consensus signal.
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh", action="store_true", help="redownload source pages")
    parser.add_argument("--write", action="store_true", help="replace the embedded player array")
    args = parser.parse_args()
    text, players, start, end = current_players()
    cbs, fftoday, metadata = source_data(args.refresh)
    fd_rates = player_first_down_rates(args.refresh)
    updated, analysis = build_ensemble(players, cbs, fftoday, metadata, fd_rates)
    RAW.write_text(json.dumps(analysis, indent=2))
    report = render_report(analysis)
    REPORT.write_text(report)
    if args.write:
        replacement = json.dumps(updated, indent=2, ensure_ascii=False)
        HTML.write_text(text[:start] + replacement + text[end:])
    print(report)


if __name__ == "__main__":
    main()
