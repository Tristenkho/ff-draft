#!/usr/bin/env python3
"""Historical draft-policy backtest using preseason ADP and actual NFL weeks.

Inputs are cached outside version control.  Draft policy is selected on 2018-22,
screened on 2023, and reported once on the sealed 2024 holdout.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import re
import ssl
import statistics
import unicodedata
import urllib.request
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, replace
from pathlib import Path

import pandas as pd
import certifi


ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / ".cache" / "ff-backtest"
OUT_JSON = ROOT / "out" / "draft_historical_backtest_raw.json"
OUT_MD = ROOT / "out" / "draft_historical_backtest.md"
VERIFY_JSON = ROOT / "out" / "draft_historical_robustness_raw.json"
VERIFY_MD = ROOT / "out" / "draft_historical_robustness.md"
SEASONS = tuple(range(2018, 2025))
TRAIN, VALIDATION, HOLDOUT = tuple(range(2018, 2023)), (2023,), (2024,)
POSITIONS = ("QB", "RB", "WR", "TE")
CAPS = {"QB": 4, "RB": 8, "WR": 8, "TE": 3}


@dataclass(frozen=True)
class Policy:
    id: str
    label: str
    ceiling: float = 0.40
    core_early: int = 3
    core_deadline: int = 4
    starter_deadline: int = 8
    core_total: int = 10
    min_core_each: int = 4
    luxury_start: int = 9
    te2_edge: float = 5.0
    qb2_edge: float = 5.0
    # Which per-player uncertainty the ceiling premium multiplies. "volatility"
    # is prior-season weekly variance (what this harness has always used);
    # "proxy" reproduces the live board's position-rate proxy; "dispersion"
    # uses draft-market disagreement; "blend" averages volatility and dispersion.
    sd_mode: str = "volatility"
    # How the pick is chosen from the eligible set. "vona" is the live board's
    # wait-band gain logic; "consensus" takes the best available by contemporaneous
    # market rank, the historical stand-in for "just draft off ECR". Roster
    # eligibility is identical either way, so this isolates the ranker.
    select: str = "vona"


BASELINE = Policy("baseline", "Current tuned build")
POLICIES = (
    BASELINE,
    replace(BASELINE, id="ceiling_0", label="No ceiling premium", ceiling=0.0),
    replace(BASELINE, id="ceiling_20", label="Ceiling weight 0.20", ceiling=0.20),
    replace(BASELINE, id="ceiling_60", label="Ceiling weight 0.60", ceiling=0.60),
    replace(BASELINE, id="core_2", label="Two RB/WR through R4", core_early=2),
    replace(BASELINE, id="core_4", label="Four RB/WR through R4", core_early=4),
    replace(BASELINE, id="starters_7", label="Finish starters by R7", starter_deadline=7),
    replace(BASELINE, id="starters_9", label="Finish starters by R9", starter_deadline=9, luxury_start=10),
    replace(BASELINE, id="core_9", label="Nine total RB/WR", core_total=9),
    replace(BASELINE, id="loose_balance", label="Allow 7/3 RB-WR", min_core_each=3),
    replace(BASELINE, id="sd_proxy", label="Live position-rate sd (ships today)", sd_mode="proxy"),
    replace(BASELINE, id="sd_dispersion", label="ADP-dispersion sd", sd_mode="dispersion"),
    replace(BASELINE, id="sd_blend", label="Volatility+dispersion sd", sd_mode="blend"),
    replace(BASELINE, id="sd_proxy_ceiling_60", label="Live proxy sd, ceiling 0.60", sd_mode="proxy", ceiling=.60),
    replace(BASELINE, id="consensus", label="Consensus rank, model roster rules", select="consensus"),
    replace(BASELINE, id="no_luxury", label="No QB2/TE2", luxury_start=13, te2_edge=99, qb2_edge=99),
    replace(BASELINE, id="easy_te2", label="Any superior late TE2", te2_edge=0),
)


def stable_seed(*parts: object) -> int:
    data = "|".join(map(str, parts)).encode()
    return int.from_bytes(hashlib.blake2b(data, digest_size=8).digest(), "big")


def normalize_name(value: str) -> str:
    value = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode().lower()
    value = re.sub(r"\b(jr|sr|ii|iii|iv)\b", "", value)
    value = re.sub(r"[^a-z0-9]", "", value)
    aliases = {
        "hollywoodbrown": "marquisebrown",
        "kennygainwell": "kennethgainwell",
        "joshuapalmer": "joshpalmer",
        "gabedavis": "gabrieldavis",
    }
    return aliases.get(value, value)


def download(url: str, path: Path) -> None:
    if path.exists() and path.stat().st_size > 100:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": "ff-draft-historical-backtest"})
    context = ssl.create_default_context(cafile=certifi.where())
    with urllib.request.urlopen(request, timeout=120, context=context) as response, path.open("wb") as target:
        target.write(response.read())


def fetch_inputs() -> tuple[Path, dict[int, tuple[Path, ...]]]:
    stats = CACHE / "nflverse_player_stats.csv"
    download("https://github.com/nflverse/nflverse-data/releases/download/player_stats/player_stats.csv", stats)
    adp = {}
    for season in SEASONS:
        paths = []
        for scoring in ("half-ppr", "ppr", "standard"):
            path = CACHE / f"ffc_{scoring.replace('-', '_')}_adp_{season}.json"
            download(f"https://fantasyfootballcalculator.com/api/v1/adp/{scoring}?teams=12&year={season}", path)
            paths.append(path)
        adp[season] = tuple(paths)
    return stats, adp


def custom_points(frame: pd.DataFrame) -> pd.Series:
    def col(name: str) -> pd.Series:
        return pd.to_numeric(frame.get(name, 0), errors="coerce").fillna(0)

    return (
        .04 * col("passing_yards") + 4 * col("passing_tds") - 2 * col("interceptions")
        + .1 * col("passing_first_downs") + 2 * col("passing_2pt_conversions")
        + .1 * col("rushing_yards") + 6 * col("rushing_tds") + .25 * col("rushing_first_downs")
        + 2 * col("rushing_2pt_conversions") + .1 * col("receiving_yards")
        + .5 * col("receptions") + 6 * col("receiving_tds") + .5 * col("receiving_first_downs")
        + 2 * col("receiving_2pt_conversions") + 6 * col("special_teams_tds")
        - 2 * (col("sack_fumbles_lost") + col("rushing_fumbles_lost") + col("receiving_fumbles_lost"))
    )


def load_weekly(stats_path: Path) -> tuple[dict, dict]:
    usecols = [
        "player_display_name", "position", "season", "week", "season_type",
        "passing_yards", "passing_tds", "interceptions", "passing_first_downs", "passing_2pt_conversions",
        "rushing_yards", "rushing_tds", "rushing_first_downs", "rushing_2pt_conversions",
        "receiving_yards", "receptions", "receiving_tds", "receiving_first_downs", "receiving_2pt_conversions",
        "special_teams_tds", "sack_fumbles_lost", "rushing_fumbles_lost", "receiving_fumbles_lost",
    ]
    frame = pd.read_csv(stats_path, usecols=usecols)
    frame = frame[(frame.season.between(min(SEASONS) - 2, max(SEASONS))) & (frame.season_type == "REG")]
    frame = frame[frame.position.isin(POSITIONS)].copy()
    frame["key"] = frame.player_display_name.map(normalize_name)
    frame["points"] = custom_points(frame)
    weekly = {}
    totals = defaultdict(dict)
    for row in frame[["season", "week", "key", "position", "points"]].itertuples(index=False):
        weekly[(int(row.season), row.key, row.position, int(row.week))] = float(row.points)
        totals[(int(row.season), row.key, row.position)][int(row.week)] = float(row.points)
    return weekly, totals


def load_adp(paths: dict[int, tuple[Path, ...]]) -> dict[int, list[dict]]:
    result = {}
    for season, season_paths in paths.items():
        players = []
        seen = set()
        for source_index, path in enumerate(season_paths):
            payload = json.loads(path.read_text())
            for raw in payload.get("players", []):
                pos = raw.get("position")
                player_id = f"{normalize_name(raw['name'])}:{pos}"
                if pos not in POSITIONS or player_id in seen:
                    continue
                seen.add(player_id)
                # Preserve the half-PPR board; alternate scoring only supplies
                # enough late players to complete all twelve skill rounds.
                players.append({
                    "id": player_id, "name": raw["name"], "key": normalize_name(raw["name"]),
                    "pos": pos, "team": raw.get("team", ""), "adp": float(raw["adp"]) + 18 * source_index,
                    "adp_sd": max(1.5, float(raw.get("stdev") or 8)), "bye": raw.get("bye"),
                    "adp_source": ("half-ppr", "ppr-tail", "standard-tail")[source_index],
                })
                if len(players) >= 190:
                    break
            if len(players) >= 190:
                break
        result[season] = sorted(players, key=lambda p: p["adp"])
    return result


# Mirrors ensemble.CEILING_RATE in the live pipeline, so "proxy" reproduces
# exactly what out/draft_terminal.html ships today.
CEILING_RATE = {"QB": .14, "RB": .26, "WR": .23, "TE": .25}
SD_FIELD = {"volatility": "sd", "proxy": "sd_proxy", "dispersion": "sd_disp", "blend": "sd_blend"}


def season_points(totals: dict, season: int, key: str, pos: str) -> float:
    return sum(totals.get((season, key, pos), {}).values())


def make_pools(adp: dict[int, list[dict]], totals: dict) -> dict[int, list[dict]]:
    pools = {}
    for season, source in adp.items():
        prior_distributions = {}
        for pos in POSITIONS:
            values = []
            for prior in (season - 1, season - 2):
                candidates = [sum(weeks.values()) for (yr, _, p), weeks in totals.items() if yr == prior and p == pos]
                values.append(sorted(candidates, reverse=True))
            prior_distributions[pos] = values
        pos_rank = Counter()
        pool = []
        for raw in source:
            pos = raw["pos"]
            rank = pos_rank[pos]
            pos_rank[pos] += 1
            distributions = prior_distributions[pos]
            comparable = [dist[min(rank, len(dist) - 1)] for dist in distributions if dist]
            market = statistics.mean(comparable) if comparable else 0
            last = season_points(totals, season - 1, raw["key"], pos)
            older = season_points(totals, season - 2, raw["key"], pos)
            history = .72 * last + .28 * older if last or older else market
            has_history = bool(last or older)
            projection = (.58 * history + .42 * market) if has_history else market
            # Annual uncertainty proxy derived only from prior weekly volatility.
            history_weeks = list(totals.get((season - 1, raw["key"], pos), {}).values())
            weekly_sd = statistics.pstdev(history_weeks) if len(history_weeks) > 1 else projection / 17 * .55
            annual_sd = max(projection * .10, weekly_sd * math.sqrt(17) * .65)
            pool.append({**raw, "proj": projection, "sd": annual_sd, "actual": season_points(totals, season, raw["key"], pos)})
        add_alternate_uncertainty(pool)
        pools[season] = pool
    return pools


def add_alternate_uncertainty(pool: list[dict]) -> None:
    """Attach the uncertainty variants the sd_mode policies select between.

    "dispersion" converts ADP disagreement (in picks) into points using the
    local slope of projection against draft position within each position
    group, so a player the market cannot place is treated as more uncertain.
    """
    slope = {}
    for pos in POSITIONS:
        group = sorted((p for p in pool if p["pos"] == pos), key=lambda p: p["adp"])
        if len(group) > 2:
            span_adp = group[-1]["adp"] - group[0]["adp"]
            span_proj = group[0]["proj"] - group[-1]["proj"]
            slope[pos] = abs(span_proj / span_adp) if span_adp else 0.0
        else:
            slope[pos] = 0.0
    for player in pool:
        pos = player["pos"]
        player["sd_proxy"] = player["proj"] * CEILING_RATE[pos]
        player["sd_disp"] = max(player["proj"] * .10, player["adp_sd"] * slope[pos])
        player["sd_blend"] = .5 * player["sd"] + .5 * player["sd_disp"]


def make_weekly_forecasts(pools: dict[int, list[dict]], weekly: dict) -> dict:
    forecasts = {}
    for season, pool in pools.items():
        for player in pool:
            prior = []
            preseason_week = player["proj"] / 17
            for week in range(1, 18):
                key = (season, player["key"], player["pos"], week)
                if key in weekly:
                    recent = statistics.mean(prior[-4:]) if prior else preseason_week
                    forecasts[(season, player["id"], week)] = (.60 * recent + .40 * preseason_week, weekly[key])
                    prior.append(weekly[key])
    return forecasts


def replacement(pool: list[dict], ceiling: float, sd_key: str = "sd") -> dict[str, float]:
    value = lambda p: p["proj"] + ceiling * p[sd_key]
    groups = {pos: sorted((p for p in pool if p["pos"] == pos), key=value, reverse=True) for pos in POSITIONS}
    need = {"QB": 12, "RB": 24, "WR": 24, "TE": 12}
    for _ in range(12):
        options = [(value(groups[pos][need[pos]]), pos) for pos in ("RB", "WR", "TE") if len(groups[pos]) > need[pos]]
        if options:
            need[max(options)[1]] += 1
    return {pos: value(groups[pos][min(need[pos], len(groups[pos]) - 1)]) if groups[pos] else 0 for pos in POSITIONS}


def model_meta(pool: list[dict], ceiling: float, sd_key: str = "sd") -> tuple[dict[str, int], dict[str, float]]:
    rep = replacement(pool, ceiling, sd_key)
    values = {p["id"]: p["proj"] + ceiling * p[sd_key] for p in pool}
    core = sorted(pool, key=lambda p: values[p["id"]] - rep[p["pos"]], reverse=True)
    core_rank = {p["id"]: i + 1 for i, p in enumerate(core)}
    model = sorted(pool, key=lambda p: .8 * core_rank[p["id"]] + .2 * p["adp"])
    return {p["id"]: i + 1 for i, p in enumerate(model)}, values


def counts(roster: list[dict]) -> Counter:
    return Counter(p["pos"] for p in roster)


def opponent_need(pos: str, roster: list[dict], round_no: int) -> float:
    have = counts(roster)
    rb, wr, te = have["RB"], have["WR"], have["TE"]
    flex = max(0, rb - 2) + max(0, wr - 2) + max(0, te - 1)
    if pos == "QB":
        if not have["QB"]:
            return 30 if round_no <= 5 else 20 if round_no == 6 else 5 if round_no == 7 else -8 if round_no == 8 else -25
        return 35 if round_no >= 11 else 80
    if pos == "TE":
        if not te:
            return 20 if round_no <= 4 else 8 if round_no <= 6 else 0 if round_no == 7 else -8 if round_no == 8 else -14
        return 18 if round_no >= 10 else 45
    have_pos = rb if pos == "RB" else wr
    return -18 if have_pos < 2 else -10 if not flex else -4 if round_no <= 10 else 10


def opponent_eligible(player: dict, roster: list[dict], round_no: int) -> bool:
    have = counts(roster)
    pos = player["pos"]
    onesies = have["QB"] + have["TE"]
    if have[pos] >= CAPS[pos]:
        return False
    if pos == "QB" and have[pos] and (round_no < 11 or have[pos] >= 2 or onesies >= 3):
        return False
    if pos == "TE" and have[pos] and (round_no < 10 or have[pos] >= 2 or onesies >= 3):
        return False
    return True


def recommendation_eligible(player: dict, roster: list[dict], round_no: int, policy: Policy) -> tuple[bool, bool]:
    have = counts(roster)
    pos = player["pos"]
    if have[pos] >= CAPS[pos]:
        return False, False
    luxury = False
    if pos == "QB" and have["QB"] >= 1:
        if have["QB"] >= 2 or round_no < policy.luxury_start or have["QB"] + have["TE"] >= 3:
            return False, False
        luxury = True
    if pos == "TE" and have["TE"] >= 1:
        if have["TE"] >= 2 or round_no < policy.luxury_start or have["QB"] + have["TE"] >= 3:
            return False, False
        luxury = True
    after = have.copy()
    after[pos] += 1
    core_after = after["RB"] + after["WR"]
    if round_no <= policy.core_deadline and core_after + policy.core_deadline - round_no < policy.core_early:
        return False, False
    if round_no <= policy.starter_deadline:
        future = policy.starter_deadline - round_no
        qb_need, te_need = max(0, 1 - after["QB"]), max(0, 1 - after["TE"])
        rb_need, wr_need = max(0, 2 - after["RB"]), max(0, 2 - after["WR"])
        core_starter = max(rb_need + wr_need, 5 - core_after)
        if qb_need + te_need + core_starter > future:
            return False, False
    future = max(0, 12 - round_no)
    extras = max(0, after["QB"] - 1) + max(0, after["TE"] - 1)
    target = max(8, policy.core_total - extras)
    minimum = min(policy.min_core_each, target // 2)
    rb_need, wr_need = max(0, minimum - after["RB"]), max(0, minimum - after["WR"])
    core_need = max(rb_need + wr_need, target - core_after)
    if max(0, 1 - after["QB"]) + max(0, 1 - after["TE"]) + core_need > future:
        return False, False
    return True, luxury


def need_factor(pos: str, roster: list[dict]) -> float:
    have = counts(roster)
    if have[pos] >= CAPS[pos]:
        return 0
    base = {"QB": 1, "RB": 2, "WR": 2, "TE": 1}[pos]
    if have[pos] < base:
        return 1
    if pos in ("RB", "WR") and have[pos] < base + 1:
        return .85
    bench = max(0, len(roster) - min(have["QB"], 1) - min(have["RB"], 2) - min(have["WR"], 2) - min(have["TE"], 1))
    if bench >= 5:
        return .20
    if pos in ("RB", "WR"):
        return .65
    if pos == "TE":
        return .40 if bench >= 3 else .18
    return .30 if bench >= 3 else .12


def phi(value: float) -> float:
    return .5 * (1 + math.erf(value / math.sqrt(2)))


def choose_user(available: list[dict], roster: list[dict], overall_pick: int, round_no: int, policy: Policy) -> dict:
    sd_key = SD_FIELD[policy.sd_mode]
    model_rank, values = model_meta(available, policy.ceiling, sd_key)
    rep = replacement(available, policy.ceiling, sd_key)
    next_pick = (round_no * 12 + (10 if (round_no + 1) % 2 == 0 else 3)) if round_no < 12 else None
    ranked = {p["id"]: overall_pick + i for i, p in enumerate(sorted(available, key=lambda x: x["adp"]))}

    def survives(player: dict) -> float:
        if next_pick is None:
            return 0
        return 1 - phi((next_pick - ranked[player["id"]]) / max(player["adp_sd"], 1.5))

    def expected_best(pos: str) -> float:
        carry = 1.0
        expected = 0.0
        for player in sorted((p for p in available if p["pos"] == pos), key=lambda p: values[p["id"]], reverse=True)[:40]:
            chance = survives(player)
            expected += values[player["id"]] * chance * carry
            carry *= 1 - chance
            if carry < 1e-4:
                break
        return expected

    next_value = {pos: expected_best(pos) for pos in POSITIONS}
    rows = []
    for player in available:
        okay, luxury = recommendation_eligible(player, roster, round_no, policy)
        value = values[player["id"]]
        gain = ((value - next_value[player["pos"]]) if next_pick else value - rep[player["pos"]]) * need_factor(player["pos"], roster)
        rows.append({"p": player, "ok": okay, "luxury": luxury, "value": value, "gain": gain, "rank": model_rank[player["id"]]})
    best_core_gain = max((r["gain"] for r in rows if r["ok"] and r["p"]["pos"] in ("RB", "WR")), default=-1e9)
    best_core_value = max((r["value"] for r in rows if r["ok"] and r["p"]["pos"] in ("RB", "WR")), default=-1e9)
    for row in rows:
        if row["ok"] and row["luxury"]:
            edge = policy.te2_edge if row["p"]["pos"] == "TE" else policy.qb2_edge
            clears = row["value"] >= best_core_value + edge if row["p"]["pos"] == "TE" else row["gain"] >= best_core_gain + edge
            row["ok"] = clears and row["value"] - rep[row["p"]["pos"]] > 0
    eligible = [r for r in rows if r["ok"]]
    if not eligible:
        raise RuntimeError(f"No eligible user pick in round {round_no}")
    if policy.select == "consensus":
        return min(eligible, key=lambda r: (r["p"]["adp"], -r["gain"]))["p"]
    eligible.sort(key=lambda r: (-r["gain"], r["rank"]))
    top_gain = eligible[0]["gain"]
    tier = [r for r in eligible if top_gain - r["gain"] < 7.5]
    return min(tier, key=lambda r: (r["rank"], -r["gain"]))["p"]


@dataclass(frozen=True)
class Opponent:
    model_weight: float
    need_weight: float
    noise_scale: float


def draft_room(pool: list[dict], policy: Policy, opponent: Opponent, seed: int, user_team: bool = True) -> list[list[dict]]:
    rng = random.Random(seed)
    model_rank, _ = model_meta(pool, policy.ceiling, SD_FIELD[policy.sd_mode])
    available = {p["id"]: p for p in pool}
    rosters = [[] for _ in range(12)]
    for overall in range(1, 145):
        round_no = (overall - 1) // 12 + 1
        in_round = (overall - 1) % 12
        team = in_round if round_no % 2 else 11 - in_round
        if user_team and team == 2:
            pick = choose_user(list(available.values()), rosters[team], overall, round_no, policy)
        else:
            candidates = [p for p in available.values() if opponent_eligible(p, rosters[team], round_no)]
            if not candidates:
                candidates = list(available.values())
            def score(player: dict) -> float:
                market = player["adp"]
                model = model_rank[player["id"]]
                need = opponent_need(player["pos"], rosters[team], round_no)
                noise_sd = abs(opponent.noise_scale) if opponent.noise_scale < 0 else player["adp_sd"] * opponent.noise_scale
                noise = rng.gauss(0, noise_sd)
                return market + opponent.model_weight * (model - market) + opponent.need_weight * need + noise
            pick = min(candidates, key=lambda p: (score(p), p["adp"]))
        rosters[team].append(pick)
        del available[pick["id"]]
    return rosters


def opponent_fit(pools: dict[int, list[dict]], candidates: list[Opponent], seasons: tuple[int, ...], drafts: int, tag: str) -> list[dict]:
    rows = []
    for config in candidates:
        squared, bias, dispersion, count = 0.0, 0.0, 0.0, 0
        for season in seasons:
            observed = defaultdict(list)
            for index in range(drafts):
                rosters = draft_room(pools[season], BASELINE, config, stable_seed("cal", tag, season, index), user_team=False)
                for team, roster in enumerate(rosters):
                    for round_index, pick in enumerate(roster, 1):
                        overall = (round_index - 1) * 12 + (team + 1 if round_index % 2 else 12 - team)
                        observed[pick["id"]].append(overall)
            by_id = {p["id"]: p for p in pools[season]}
            for player_id, picks in observed.items():
                player = by_id[player_id]
                if player["adp"] > 130 or len(picks) < drafts // 2:
                    continue
                delta = statistics.mean(picks) - player["adp"]
                scale = max(4, player["adp_sd"])
                squared += (delta / scale) ** 2
                simulated_sd = statistics.pstdev(picks) if len(picks) > 1 else 0
                dispersion += simulated_sd / player["adp_sd"]
                squared += .35 * ((simulated_sd - player["adp_sd"]) / scale) ** 2
                bias += delta
                count += 1
        rows.append({**asdict(config), "rmse_sd": math.sqrt(squared / max(count, 1)), "mean_pick_bias": bias / max(count, 1),
                     "dispersion_ratio": dispersion / max(count, 1), "players": count})
    rows.sort(key=lambda row: (row["rmse_sd"], abs(row["mean_pick_bias"])))
    return rows


def calibrate_opponents(pools: dict[int, list[dict]], drafts: int) -> tuple[Opponent, list[dict], list[dict]]:
    candidates = [Opponent(m, n, z) for m in (0, .15, .30, .45, .70, 1.0) for n in (.20, .40, .60, 1.0) for z in (.65, .90, 1.15)]
    current_like = Opponent(1.0, 1.0, -4.0)
    coarse = opponent_fit(pools, candidates + [current_like], TRAIN, min(5, max(2, drafts // 4)), "coarse")
    finalist_configs = [Opponent(row["model_weight"], row["need_weight"], row["noise_scale"]) for row in coarse[:8]]
    if current_like not in finalist_configs:
        finalist_configs.append(current_like)
    final = opponent_fit(pools, finalist_configs, TRAIN, drafts, "final")
    best_row = next(row for row in final if row["noise_scale"] >= 0)
    best = Opponent(best_row["model_weight"], best_row["need_weight"], best_row["noise_scale"])
    validation = opponent_fit(pools, [best, current_like], VALIDATION + HOLDOUT, max(20, drafts), "opponent-validation")
    return best, final, validation


def weekly_lineup(roster: list[dict], season: int, week: int, forecasts: dict) -> float:
    candidates = []
    for player in roster:
        result = forecasts.get((season, player["id"], week))
        if result is None:
            continue
        forecast, actual = result
        candidates.append((player, forecast, actual))
    used = set()
    total = 0.0
    def take(pos: str, amount: int) -> None:
        nonlocal total
        options = sorted((x for x in candidates if x[0]["pos"] == pos and x[0]["id"] not in used), key=lambda x: x[1], reverse=True)
        for item in options[:amount]:
            used.add(item[0]["id"])
            total += item[2]
    take("QB", 1); take("RB", 2); take("WR", 2); take("TE", 1)
    flex = sorted((x for x in candidates if x[0]["pos"] in ("RB", "WR", "TE") and x[0]["id"] not in used), key=lambda x: x[1], reverse=True)
    if flex:
        total += flex[0][2]
    return total


_ENVIRONMENTS = {}


def season_environment(season: int, seed: int) -> tuple[list[list[float]], list[list[int]]]:
    cache_key = (season, seed)
    if cache_key in _ENVIRONMENTS:
        return _ENVIRONMENTS[cache_key]
    special = [[0.0] * 18 for _ in range(12)]
    for team in range(12):
        rng = random.Random(stable_seed("kdst", season, seed, team))
        for week in range(1, 18):
            special[team][week] = max(2, 15 + rng.gauss(0, 3.5))
    schedules = []
    for week in range(1, 15):
        order = list(range(12))
        random.Random(stable_seed("schedule", season, seed, week)).shuffle(order)
        schedules.append(order)
    _ENVIRONMENTS[cache_key] = (special, schedules)
    return special, schedules


def season_result(rosters: list[list[dict]], season: int, forecasts: dict, seed: int) -> dict:
    special, schedules = season_environment(season, seed)
    scores = [[0.0] * 18 for _ in range(12)]
    for team in range(12):
        for week in range(1, 18):
            scores[team][week] = weekly_lineup(rosters[team], season, week, forecasts) + special[team][week]
    wins, points = [0] * 12, [0.0] * 12
    for week in range(1, 15):
        order = schedules[week - 1]
        for index in range(0, 12, 2):
            a, b = order[index:index + 2]
            points[a] += scores[a][week]; points[b] += scores[b][week]
            wins[a if scores[a][week] >= scores[b][week] else b] += 1
    seeds = sorted(range(12), key=lambda t: (-wins[t], -points[t]))[:8]
    def winner(a: int, b: int, week: int) -> int:
        return a if scores[a][week] >= scores[b][week] else b
    quarters = [winner(seeds[0], seeds[7], 15), winner(seeds[3], seeds[4], 15), winner(seeds[1], seeds[6], 15), winner(seeds[2], seeds[5], 15)]
    semis = [winner(quarters[0], quarters[1], 16), winner(quarters[2], quarters[3], 16)]
    champion = winner(semis[0], semis[1], 17)
    return {"playoff": int(2 in seeds), "champion": int(champion == 2), "points": points[2], "seed": seeds.index(2) + 1 if 2 in seeds else 9}


def evaluate(policy: Policy, seasons: tuple[int, ...], pools: dict, forecasts: dict, opponent: Opponent, drafts: int, tag: str) -> dict:
    outcomes, constructions = [], Counter()
    for season in seasons:
        for index in range(drafts):
            seed = stable_seed("draft", tag, season, index)
            rosters = draft_room(pools[season], policy, opponent, seed)
            mine = rosters[2]
            have = counts(mine)
            construction = " ".join(f"{pos}{have[pos]}" for pos in POSITIONS)
            constructions[construction] += 1
            outcome = season_result(rosters, season, forecasts, stable_seed("season", tag, index))
            outcome["season"] = season
            outcomes.append(outcome)
    def mean(key: str) -> float:
        return statistics.mean(row[key] for row in outcomes)
    return {
        "policy": asdict(policy), "trials": len(outcomes), "playoff": mean("playoff"), "champion": mean("champion"),
        "points": mean("points"), "seed": mean("seed"), "constructions": dict(constructions.most_common(8)),
        "by_season": {str(season): {
            "trials": sum(row["season"] == season for row in outcomes),
            "playoff": statistics.mean(row["playoff"] for row in outcomes if row["season"] == season),
            "champion": statistics.mean(row["champion"] for row in outcomes if row["season"] == season),
            "points": statistics.mean(row["points"] for row in outcomes if row["season"] == season),
        } for season in seasons},
        "raw": outcomes,
    }


def paired_interval(challenger: dict, baseline: dict, key: str) -> dict:
    differences = [a[key] - b[key] for a, b in zip(challenger["raw"], baseline["raw"])]
    mean = statistics.mean(differences)
    sd = statistics.stdev(differences) if len(differences) > 1 else 0
    error = 1.96 * sd / math.sqrt(max(1, len(differences)))
    return {"delta": mean, "lo": mean - error, "hi": mean + error}


def paired_rows(challenger: list[dict], baseline: list[dict], key: str) -> dict:
    differences = [a[key] - b[key] for a, b in zip(challenger, baseline)]
    mean = statistics.mean(differences)
    sd = statistics.stdev(differences) if len(differences) > 1 else 0
    error = 1.96 * sd / math.sqrt(max(1, len(differences)))
    return {"delta": mean, "lo": mean - error, "hi": mean + error}


def strip_raw(result: dict) -> dict:
    return {key: value for key, value in result.items() if key != "raw"}


def run(args: argparse.Namespace) -> dict:
    stats_path, adp_paths = fetch_inputs()
    weekly, totals = load_weekly(stats_path)
    adp = load_adp(adp_paths)
    pools = make_pools(adp, totals)
    forecasts = make_weekly_forecasts(pools, weekly)
    match = {season: sum(bool(totals.get((season, p["key"], p["pos"]))) for p in pools[season]) / len(pools[season]) for season in SEASONS}
    opponent, calibration, opponent_validation = calibrate_opponents(pools, args.calibration_drafts)

    training = [evaluate(policy, TRAIN, pools, forecasts, opponent, args.train_drafts, "train") for policy in POLICIES]
    train_ranked = sorted(training, key=lambda row: (row["champion"], row["playoff"], row["points"]), reverse=True)
    finalists = {BASELINE.id, *(row["policy"]["id"] for row in train_ranked[:4])}
    validation = [evaluate(policy, VALIDATION, pools, forecasts, opponent, args.validation_drafts, "validation") for policy in POLICIES if policy.id in finalists]
    validation_ranked = sorted(validation, key=lambda row: (row["champion"], row["playoff"], row["points"]), reverse=True)
    holdout_ids = {BASELINE.id, *(row["policy"]["id"] for row in validation_ranked[:3])}
    holdout = [evaluate(policy, HOLDOUT, pools, forecasts, opponent, args.holdout_drafts, "holdout") for policy in POLICIES if policy.id in holdout_ids]
    holdout_base = next(row for row in holdout if row["policy"]["id"] == BASELINE.id)
    for row in holdout:
        row["champion_vs_baseline"] = paired_interval(row, holdout_base, "champion")
        row["playoff_vs_baseline"] = paired_interval(row, holdout_base, "playoff")
        row["points_vs_baseline"] = paired_interval(row, holdout_base, "points")
    return {
        "method": {"seasons": list(SEASONS), "train": list(TRAIN), "validation": list(VALIDATION), "holdout": list(HOLDOUT),
                   "calibration_drafts_per_season": args.calibration_drafts, "train_drafts_per_season": args.train_drafts,
                   "validation_drafts": args.validation_drafts, "holdout_drafts": args.holdout_drafts,
                   "weekly_source": "nflverse player_stats", "market_source": "Fantasy Football Calculator half-PPR ADP"},
        "match_rate": match, "opponent": asdict(opponent), "opponent_calibration": calibration,
        "opponent_validation": opponent_validation,
        "training": [strip_raw(row) for row in training], "validation": [strip_raw(row) for row in validation],
        "holdout": [strip_raw(row) for row in holdout],
    }


def percent(value: float) -> str:
    return f"{100 * value:.2f}%"


def render(result: dict) -> str:
    holdout = sorted(result["holdout"], key=lambda row: (row["champion"], row["playoff"]), reverse=True)
    baseline = next(row for row in holdout if row["policy"]["id"] == "baseline")
    winner = holdout[0]
    interval = winner["champion_vs_baseline"]
    stable = winner["policy"]["id"] != "baseline" and interval["lo"] > 0
    verdict = (f"Holdout candidate: **{winner['policy']['label']}**. It improved the sealed holdout, but must pass the separate fresh-seed, all-season robustness gate before any live change."
               if stable else "**Retain the current live policy.** No challenger demonstrated a reliable championship improvement on the sealed holdout.")
    rows = []
    for row in holdout:
        ci = row["champion_vs_baseline"]
        rows.append(f"| {row['policy']['label']} | {percent(row['champion'])} | {percent(row['playoff'])} | {row['points']:.1f} | {percent(ci['delta'])} [{percent(ci['lo'])}, {percent(ci['hi'])}] |")
    training = sorted(result["training"], key=lambda row: (row["champion"], row["playoff"]), reverse=True)
    train_rows = [f"| {row['policy']['label']} | {percent(row['champion'])} | {percent(row['playoff'])} | {row['points']:.1f} |" for row in training]
    match = " · ".join(f"{season}: {percent(rate)}" for season, rate in result["match_rate"].items())
    config = result["opponent"]
    opponent_rows = []
    for row in sorted(result["opponent_validation"], key=lambda item: item["rmse_sd"]):
        label = "Current fixed-noise logic" if row["noise_scale"] < 0 else "Calibrated market blend"
        opponent_rows.append(f"| {label} | {row['rmse_sd']:.3f} | {row['mean_pick_bias']:+.2f} | {row['dispersion_ratio']:.2f}× |")
    return f"""# Historical draft-policy backtest

## Decision

{verdict}

## Sealed 2024 holdout

| Policy | Champion | Playoffs | Regular-season points | Championship delta vs baseline (95% CI) |
| --- | ---: | ---: | ---: | ---: |
{chr(10).join(rows)}

## Training screen (2018–2022)

| Policy | Champion | Playoffs | Regular-season points |
| --- | ---: | ---: | ---: |
{chr(10).join(train_rows)}

## Opponent selection validation (2023–2024)

| Selector | Pick-error RMSE (ADP SD) | Mean pick bias | Simulated/observed dispersion |
| --- | ---: | ---: | ---: |
{chr(10).join(opponent_rows)}

## Method

- Preseason market: Fantasy Football Calculator half-PPR ADP snapshots from real 12-team drafts.
- Outcomes: nflverse regular-season weekly player statistics scored with this league's passing, rushing, receiving, first-down, two-point, fumble, and return-TD rules.
- Split: 2018–2022 training, 2023 policy validation, and one sealed 2024 holdout read after finalists were chosen.
- Opponent calibration: model-deviation weight `{config['model_weight']:.2f}`, need weight `{config['need_weight']:.2f}`, ADP-SD randomness multiplier `{config['noise_scale']:.2f}` selected only on training years. Lower pick-error RMSE is better.
- ADP-to-outcome player match: {match}.
- Weekly lineups use only preseason value and results from earlier weeks; actual current-week points never choose the lineup.
- The same draft rooms, weekly results, special-team noise, and schedules are paired across policies.

## Limits

- Public nflverse player stats currently end at 2024, so 2025 was not invented or silently imputed.
- Only one untouched holdout season is available. Thousands of rooms reduce draft-room Monte Carlo error but do not turn one NFL season into thousands of independent seasons.
- Historical source projections were not available consistently across all years. The backtest constructs preseason values only from prior-season results plus contemporaneous ADP, without using that season's outcomes.
- K/DST contribute paired generic weekly scoring because nflverse player stats do not contain defense-level fantasy scoring. Policy comparisons still reserve the same final two picks for them.
- Waiver execution and historical injury designations are not reconstructed; missing weeks are reflected in actual player availability and roster depth.
"""


def verify_finalist(args: argparse.Namespace) -> None:
    if not OUT_JSON.exists():
        raise RuntimeError("Run the full historical backtest before finalist verification")
    prior = json.loads(OUT_JSON.read_text())
    config = Opponent(**prior["opponent"])
    stats_path, adp_paths = fetch_inputs()
    weekly, totals = load_weekly(stats_path)
    pools = make_pools(load_adp(adp_paths), totals)
    forecasts = make_weekly_forecasts(pools, weekly)
    challenger_policy = next(policy for policy in POLICIES if policy.id == args.verify_policy)
    tag = f"verification-{challenger_policy.id}-{args.seed_offset}"
    baseline = evaluate(BASELINE, SEASONS, pools, forecasts, config, args.verification_drafts, tag)
    challenger = evaluate(challenger_policy, SEASONS, pools, forecasts, config, args.verification_drafts, tag)
    by_season = []
    for season in SEASONS:
        base_rows = [row for row in baseline["raw"] if row["season"] == season]
        challenge_rows = [row for row in challenger["raw"] if row["season"] == season]
        by_season.append({
            "season": season,
            "baseline_champion": statistics.mean(row["champion"] for row in base_rows),
            "challenger_champion": statistics.mean(row["champion"] for row in challenge_rows),
            "champion_delta": paired_rows(challenge_rows, base_rows, "champion"),
            "playoff_delta": paired_rows(challenge_rows, base_rows, "playoff"),
            "points_delta": paired_rows(challenge_rows, base_rows, "points"),
        })
    result = {
        "method": {"drafts_per_season": args.verification_drafts, "seed_offset": args.seed_offset, "seasons": list(SEASONS)},
        "opponent": asdict(config), "baseline": strip_raw(baseline), "challenger": strip_raw(challenger),
        "overall": {key: paired_interval(challenger, baseline, key) for key in ("champion", "playoff", "points")},
        "by_season": by_season,
    }
    positive = sum(row["champion_delta"]["delta"] > 0 for row in by_season)
    overall = result["overall"]["champion"]
    stable = overall["lo"] > 0 and positive >= 5
    rows = "\n".join(
        f"| {row['season']} | {percent(row['baseline_champion'])} | {percent(row['challenger_champion'])} | "
        f"{percent(row['champion_delta']['delta'])} | {percent(row['playoff_delta']['delta'])} | {row['points_delta']['delta']:+.1f} |"
        for row in by_season
    )
    report = f"""# Historical policy robustness check: {challenger_policy.label}

## Decision

{f'**Verified: {challenger_policy.label}.**' if stable else '**Not verified strongly enough to change the live policy.**'}

- {args.verification_drafts:,} fresh-seed paired draft rooms per season; {args.verification_drafts * len(SEASONS):,} rooms per policy.
- Overall championship delta: {percent(overall['delta'])} (95% CI {percent(overall['lo'])} to {percent(overall['hi'])}).
- Positive championship delta in {positive}/{len(SEASONS)} seasons.

| Season | Baseline champion | Challenger champion | Champion delta | Playoff delta | Points delta |
| ---: | ---: | ---: | ---: | ---: | ---: |
{rows}

This is a verification of an originally prespecified policy, not a new parameter search. NFL seasons remain the true independent units; room-level confidence intervals describe draft-room uncertainty only.
"""
    result["stable"] = stable
    result["challenger_policy"] = asdict(challenger_policy)
    json_path = VERIFY_JSON if challenger_policy.id == "starters_7" else ROOT / "out" / f"draft_historical_robustness_{challenger_policy.id}_raw.json"
    md_path = VERIFY_MD if challenger_policy.id == "starters_7" else ROOT / "out" / f"draft_historical_robustness_{challenger_policy.id}.md"
    json_path.write_text(json.dumps(result, indent=2))
    md_path.write_text(report)
    print(report)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--calibration-drafts", type=int, default=40)
    parser.add_argument("--train-drafts", type=int, default=80)
    parser.add_argument("--validation-drafts", type=int, default=500)
    parser.add_argument("--holdout-drafts", type=int, default=1200)
    parser.add_argument("--verify-finalist", action="store_true")
    parser.add_argument("--verify-policy", choices=[policy.id for policy in POLICIES], default="starters_7")
    parser.add_argument("--verification-drafts", type=int, default=250)
    parser.add_argument("--seed-offset", type=int, default=1)
    args = parser.parse_args()
    if args.verify_finalist:
        verify_finalist(args)
        return
    result = run(args)
    OUT_JSON.write_text(json.dumps(result, indent=2))
    report = render(result)
    OUT_MD.write_text(report)
    print(report)


if __name__ == "__main__":
    main()
