#!/usr/bin/env python3
"""Quantify what REFD/RFD/PFD do to this league's scoring.

`REC 0.5` makes the league look like half-PPR, but `REFD 0.5` pushes the real
value of a reception to ~0.80 for WR, ~0.77 for TE, ~0.66 for RB. This rescores
the cached CBS/FFToday/Sleeper stat lines two ways -- with the league's first-down
bonuses and without -- to measure the gap, and re-ranks the flex pool to show
which players the half-PPR market (FFC ADP, FantasyPros ECR) misprices.

Writes out/effective_ppr_raw.json. See out/effective_ppr.md for the writeup.

Requires a populated .cache/projection-ensemble-2026/ (run
scripts/update_projection_ensemble.py first, or pass --refresh).
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import update_projection_ensemble as ens  # noqa: E402

FLEX = ("RB", "WR", "TE")


def rescore(stats: dict, rates: dict, rec_pt: float, first_downs: bool) -> float:
    """Score a raw stat line. rec_pt = points/reception; first_downs = league FD bonuses."""
    pos = stats["pos"]
    score = 0.0
    if pos == "QB":
        score += .04 * stats.get("pass_yds", 0) + 4 * stats.get("pass_td", 0)
        score -= 2 * stats.get("interceptions", 0)
        if first_downs:
            score += .1 * rates.get("pass_rate", ens.PASS_FD_PER_COMPLETION) * stats.get("completions", 0)
    score += .1 * stats.get("rush_yds", 0) + 6 * stats.get("rush_td", 0)
    if first_downs:
        score += .25 * rates.get("rush_rate", ens.RUSH_FD[pos]) * stats.get("rush_att", 0)
    if pos != "QB":
        score += rec_pt * stats.get("receptions", 0) + .1 * stats.get("rec_yds", 0)
        score += 6 * stats.get("rec_td", 0)
        if first_downs:
            score += .5 * rates.get("rec_rate", ens.REC_FD[pos]) * stats.get("receptions", 0)
    score -= 2 * stats.get("fumbles", 0)
    return score


def load_pool() -> dict:
    """The PLAYERS array inlined in the terminal, keyed by (normalized name, pos)."""
    html = (ROOT / "out" / "draft_terminal.html").read_text(encoding="utf-8")
    start = html.index("const PLAYERS=[") + len("const PLAYERS=")
    end = html.index("\n];", start)
    return {(ens.normalize(p["name"]), p["pos"]): p
            for p in json.loads(html[start:end + 2])}


def build_rows(refresh: bool) -> list[dict]:
    cbs, fftoday, sleeper, _ = ens.source_data(refresh)
    fd_rates = ens.player_first_down_rates(refresh)
    pool = load_pool()

    rows = []
    for pos in ens.POSITIONS:
        for key in set(cbs[pos]) | set(fftoday[pos]) | set(sleeper[pos]):
            player = pool.get((key, pos))
            if not player:
                continue
            rates = fd_rates.get((key, pos), {})
            lines = [src[pos][key] for src in (cbs, fftoday, sleeper) if key in src[pos]]
            rec_rate = rates.get("rec_rate", ens.REC_FD.get(pos, 0.0))
            rows.append({
                "name": player["name"], "pos": pos,
                "adp": player.get("adp"), "ecr": player.get("ecr"),
                "league": statistics.median(rescore(s, rates, .5, True) for s in lines),
                "half": statistics.median(rescore(s, rates, .5, False) for s in lines),
                "full": statistics.median(rescore(s, rates, 1., False) for s in lines),
                "receptions": statistics.median(s.get("receptions", 0) for s in lines),
                "fd_rec_rate": round(rec_rate, 3),
                "eff_ppr": round(.5 + .5 * rec_rate, 3),
                "fd_rate_n": int(rates.get("rec_n", 0) + rates.get("rush_n", 0) + rates.get("pass_n", 0)),
            })
    for row in rows:
        row["fd_points"] = round(row["league"] - row["half"], 1)
    return rows


def rank_shift(rows: list[dict], floor: float = 80.0) -> list[dict]:
    """Rank the flex pool under league scoring vs half-PPR (what ADP/ECR price)."""
    flex = [r for r in rows if r["pos"] in FLEX and r["league"] > floor]
    for field, key in (("league", "rank_league"), ("half", "rank_half")):
        for i, row in enumerate(sorted(flex, key=lambda r: -r[field]), 1):
            row[key] = i
    for row in flex:
        row["move"] = row["rank_half"] - row["rank_league"]  # + = better here than market
    return flex


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true", help="re-download sources instead of using cache")
    ap.add_argument("--top", type=int, default=10, help="movers to print per direction")
    args = ap.parse_args()

    rows = build_rows(args.refresh)
    flex = rank_shift(rows)
    print(f"{len(rows)} players rescored, {len(flex)} in the flex pool\n")

    print("=== effective points per reception (league scoring) ===")
    for pos in ("WR", "TE", "RB"):
        sub = [r for r in rows if r["pos"] == pos and r["receptions"] >= 20]
        if sub:
            vals = [r["eff_ppr"] for r in sub]
            print(f"  {pos}: mean {statistics.mean(vals):.3f}  median {statistics.median(vals):.3f}"
                  f"  range {min(vals):.2f}-{max(vals):.2f}  (n={len(sub)})")

    print("\n=== first-down points as share of projection ===")
    for pos in ("QB", "RB", "WR", "TE"):
        sub = [r for r in rows if r["pos"] == pos and r["league"] > 50]
        if sub:
            print(f"  {pos}: +{statistics.mean(r['fd_points'] for r in sub):5.1f} pts"
                  f"  ({statistics.mean(r['fd_points'] / r['league'] for r in sub) * 100:4.1f}% of total)")

    print("\n=== mean rank movement vs half-PPR market ===")
    for pos in FLEX:
        sub = [r for r in flex if r["pos"] == pos]
        if sub:
            print(f"  {pos}: {statistics.mean(r['move'] for r in sub):+.1f} spots  (n={len(sub)})")

    for label, order in (("UNDERPRICED by half-PPR market", -1), ("OVERPRICED", 1)):
        print(f"\n=== {label} ===")
        for r in sorted(flex, key=lambda x: order * x["move"])[:args.top]:
            print(f"  {r['name']:<24}{r['pos']}  #{r['rank_half']:<4}-> #{r['rank_league']:<4}"
                  f"({r['move']:+d})  ADP {str(r['adp']):<6} +{r['fd_points']:.0f}pts"
                  f"  {r['receptions']:.0f}rec @ {r['eff_ppr']:.2f}")

    out = ROOT / "out" / "effective_ppr_raw.json"
    out.write_text(json.dumps({"players": rows, "flex": flex}, indent=1), encoding="utf-8")
    print(f"\nwrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
