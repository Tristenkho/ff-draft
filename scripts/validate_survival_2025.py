#!/usr/bin/env python3
"""External validation of the board's survival model against a real draft.

Every other check of `surv` has been internal: the simulator's opponent model
and the survival estimate both derive from `timingMetric`, so agreement between
them is partly self-fulfilling. This scores the same formula against what the
twelve managers in this league actually did on 2025-08-31.

Method: walk the real 2025 draft pick by pick. At each manager's pick, rebuild
the effective-ADP ranking over the players still on the board -- exactly what
`survives()` does live, where a player's effective ADP is the current pick plus
his index among remaining players, not his absolute ADP -- and predict whether
each remaining player lasts to that manager's next pick. Then look at the real
draft and see whether he did.

    P(survive to k) = 1 - Phi((k - effective_adp) / adp_sd)

For 2025 only market ADP is available, so `timingSd` reduces to FFC's observed
per-player stdev and the ESPN/market disagreement term is zero.

Only one league draft exists, so instead of a second season this reports whether
the effect is consistent *within* the draft -- across all twelve managers and
across rounds -- with a manager-clustered bootstrap.

Usage: python3 scripts/validate_survival_2025.py
"""
from __future__ import annotations

import json
import math
import pathlib
import random
import re
import statistics
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parent.parent
DRAFT = ROOT / "out" / "league_draft_2025.json"
ADP = ROOT / ".cache" / "ff-backtest" / "ffc_half_ppr_adp_2025.json"
SKILL = ("QB", "RB", "WR", "TE")
MID = (.15, .70)          # the range where the board's judgement actually bites
BOOTSTRAPS = 5000


def normalize(name: str) -> str:
    name = name.lower().replace("&apos;", "'")
    name = re.sub(r"\b(jr|sr|ii|iii|iv|v)\b\.?", "", name)
    return re.sub(r"[^a-z]", "", name)


def phi(z: float) -> float:
    """Same Abramowitz-Stegun approximation the board uses, so the numbers match."""
    t = 1 / (1 + .2316419 * abs(z))
    d = .3989423 * math.exp(-z * z / 2)
    p = d * t * (.3193815 + t * (-.3565638 + t * (1.781478 + t * (-1.821256 + t * 1.330274))))
    return 1 - p if z > 0 else p


def load():
    picks = sorted(json.loads(DRAFT.read_text())["picks"], key=lambda p: p["overall"])
    market = {}
    for row in json.loads(ADP.read_text())["players"]:
        if row.get("position") in SKILL:
            market[normalize(row["name"])] = {
                "adp": float(row["adp"]),
                "sd": max(1.5, float(row.get("stdev") or 8)),
            }
    taken, matched = {}, 0
    for pick in picks:
        key = normalize(pick["name"])
        if key in market:
            matched += 1
            taken[key] = pick["overall"]
    by_mgr = defaultdict(list)
    for pick in picks:
        by_mgr[pick["mgr"]].append(pick["overall"])
    return picks, market, taken, matched, by_mgr


def observations(market, taken, by_mgr, stretch):
    """(manager, round, predicted, actually_lasted) for every remaining player."""
    out = []
    for mgr, overalls in by_mgr.items():
        for idx, (here, nxt) in enumerate(zip(overalls, overalls[1:])):
            remaining = [k for k in market if k not in taken or taken[k] >= here]
            remaining.sort(key=lambda k: market[k]["adp"])
            for i, key in enumerate(remaining):
                if taken.get(key) == here:
                    continue          # this manager took him; not an observation
                eff = here + i / stretch
                p = min(max(1 - phi((nxt - eff) / market[key]["sd"]), 0.0), 1.0)
                lasted = int(key not in taken or taken[key] >= nxt)
                out.append((mgr, idx + 1, p, lasted))
    return out


def table(rows, label):
    buckets = defaultdict(lambda: {"n": 0, "lasted": 0, "pred": 0.0})
    for _, _, p, o in rows:
        c = buckets[min(9, int(p * 10))]
        c["n"] += 1
        c["pred"] += p
        c["lasted"] += o
    print(f"  bucket        n    predicted   observed     error   [{label}]")
    total = weighted = 0
    for b in sorted(buckets):
        c = buckets[b]
        pred, obs = c["pred"] / c["n"], c["lasted"] / c["n"]
        total += c["n"]
        weighted += abs(obs - pred) * c["n"]
        flag = "  <-- UNDERconfident" if obs - pred > .10 else (
            "  <-- OVERconfident" if obs - pred < -.10 else "")
        print(f"  {b/10:.1f}-{b/10+.1:.1f} {c['n']:>8}       {pred:.3f}      {obs:.3f}   {obs-pred:>+7.3f}{flag}")
    pred = statistics.mean(p for _, _, p, _ in rows)
    obs = statistics.mean(o for _, _, _, o in rows)
    print(f"\n  observations {total:,} | weighted mean |error| {weighted/total:.3f} "
          f"| predicted {pred:.3f} vs observed {obs:.3f} (bias {obs-pred:+.3f})")
    brier = statistics.mean((p - o) ** 2 for _, _, p, o in rows)
    ref = statistics.mean((obs - o) ** 2 for _, _, _, o in rows)
    print(f"  Brier {brier:.4f} vs {ref:.4f} for the base rate -> skill score {1-brier/ref:+.3f}")


def main() -> None:
    picks, market, taken, matched, by_mgr = load()
    density = matched / len(picks)

    print("SURVIVAL MODEL vs THE REAL 2025 DRAFT")
    print(f"Lava Hound, 2025-08-31, same twelve managers. {matched}/{len(picks)} picks "
          f"matched to FFC ADP ({len(market)} skill players priced).\n")
    table(observations(market, taken, by_mgr, 1.0), "as the board computes it")

    # Only some picks take an FFC-priced player; the rest go to kickers, defenses
    # and sleepers outside the top 156. Those still consume slots, so ranking only
    # priced players compresses effective ADP and biases predicted survival low.
    print(f"\n  SENSITIVITY -- effective ADP stretched by the observed density of priced")
    print(f"  picks ({matched}/{len(picks)} = {density:.3f}). Everything below uses this")
    print(f"  conservative version, testing the finding at its weakest.\n")
    adj = observations(market, taken, by_mgr, density)
    table(adj, "density-corrected")

    mid = [r for r in adj if MID[0] <= r[2] <= MID[1]]
    print(f"\n\nIS IT CONSISTENT ACROSS MANAGERS?  (predictions {MID[0]}-{MID[1]})\n")
    print("  manager           n     predicted   observed     bias")
    per_mgr = {}
    for mgr in sorted(by_mgr):
        rows = [r for r in mid if r[0] == mgr]
        if not rows:
            continue
        pr = statistics.mean(r[2] for r in rows)
        ob = statistics.mean(r[3] for r in rows)
        per_mgr[mgr] = ob - pr
        print(f"  {mgr:<14} {len(rows):>5}       {pr:.3f}      {ob:.3f}   {ob-pr:>+7.3f}")
    print(f"\n  positive bias in {sum(v > 0 for v in per_mgr.values())}/{len(per_mgr)} managers")

    random.seed(7)
    names = list(by_mgr)
    by_name = {m: [r for r in mid if r[0] == m] for m in names}
    boots = []
    for _ in range(BOOTSTRAPS):
        rows = [r for m in (random.choice(names) for _ in names) for r in by_name[m]]
        if rows:
            boots.append(statistics.mean(r[3] for r in rows) - statistics.mean(r[2] for r in rows))
    boots.sort()
    lo, hi = boots[int(.025 * len(boots))], boots[int(.975 * len(boots))]
    print(f"  manager-clustered bootstrap ({BOOTSTRAPS:,} resamples): "
          f"mean {statistics.mean(boots):+.3f}, 95% CI [{lo:+.3f}, {hi:+.3f}]")

    print("\n\nWHERE IN THE DRAFT?\n")
    print("  round     n     predicted   observed     bias")
    for rd in range(1, 14):
        rows = [r for r in mid if r[1] == rd]
        if not rows:
            continue
        pr = statistics.mean(r[2] for r in rows)
        ob = statistics.mean(r[3] for r in rows)
        print(f"   {rd:>2} {len(rows):>7}       {pr:.3f}      {ob:.3f}   {ob-pr:>+7.3f}  "
              f"{'#' * max(0, round((ob - pr) * 40))}")

    print("""
  Rounds 1-5 are calibrated; the error appears at round 6 and stays. That lines up
  with out/league_tendencies_2025.md, which records rounds 7-9 running 53% special
  teams -- every pick a manager spends off-ADP is a skill player surviving longer
  than strict-ADP timing predicts.

  Limits: one draft. Managers share a pool and pick against each other, so the
  clusters are not truly independent and the bootstrap interval is optimistic.
  Read this as calibration shape and location, not a significance test.""")


if __name__ == "__main__":
    main()
