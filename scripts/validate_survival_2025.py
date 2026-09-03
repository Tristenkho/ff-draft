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

Usage: python3 scripts/validate_survival_2025.py
"""
from __future__ import annotations

import json
import math
import pathlib
import re
import statistics
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parent.parent
DRAFT = ROOT / "out" / "league_draft_2025.json"
ADP = ROOT / ".cache" / "ff-backtest" / "ffc_half_ppr_adp_2025.json"
SKILL = ("QB", "RB", "WR", "TE")


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


def main() -> None:
    picks = json.loads(DRAFT.read_text())["picks"]
    adp_rows = json.loads(ADP.read_text())["players"]
    market = {}
    for row in adp_rows:
        if row.get("position") not in SKILL:
            continue
        market[normalize(row["name"])] = {
            "adp": float(row["adp"]),
            "sd": max(1.5, float(row.get("stdev") or 8)),
        }

    picks = sorted(picks, key=lambda p: p["overall"])
    taken_by = {}          # normalized name -> overall pick it went at
    matched = 0
    for pick in picks:
        key = normalize(pick["name"])
        if key in market:
            matched += 1
            taken_by[key] = pick["overall"]

    # Every manager's pick numbers, in order.
    by_mgr = defaultdict(list)
    for pick in picks:
        by_mgr[pick["mgr"]].append(pick["overall"])

    # Sensitivity control. Only some picks take a player FFC priced; the rest go
    # to kickers, defenses and sleepers outside the top 156. Those still consume
    # slots, so ranking only priced players compresses effective ADP and biases
    # predicted survival low. Stretching the index by the observed density of
    # priced picks corrects for that.
    density = matched / len(picks)

    def run(stretch: float):
        buckets = defaultdict(lambda: {"n": 0, "lasted": 0, "pred": 0.0})
        pairs = []
        for mgr, overalls in by_mgr.items():
            for here, nxt in zip(overalls, overalls[1:]):
                remaining = [k for k, v in market.items()
                             if k not in taken_by or taken_by[k] >= here]
                remaining.sort(key=lambda k: market[k]["adp"])
                for i, key in enumerate(remaining):
                    if taken_by.get(key) == here:
                        continue
                    eff = here + i / stretch
                    p = min(max(1 - phi((nxt - eff) / market[key]["sd"]), 0.0), 1.0)
                    lasted = key not in taken_by or taken_by[key] >= nxt
                    b = min(9, int(p * 10))
                    cell = buckets[b]
                    cell["n"] += 1
                    cell["pred"] += p
                    cell["lasted"] += int(lasted)
                    pairs.append((p, int(lasted)))
        return buckets, pairs

    buckets, pairs = run(1.0)

    print("SURVIVAL MODEL vs THE REAL 2025 DRAFT")
    print(f"Lava Hound, 2025-08-31, same twelve managers. "
          f"{matched}/{len(picks)} picks matched to FFC ADP ({len(market)} skill players priced).\n")
    print("  bucket        n    predicted   observed     error")
    total = weighted = 0
    for b in sorted(buckets):
        c = buckets[b]
        pred, obs = c["pred"] / c["n"], c["lasted"] / c["n"]
        err = obs - pred
        total += c["n"]
        weighted += abs(err) * c["n"]
        flag = "  <-- OVERconfident" if err < -.10 else ("  <-- UNDERconfident" if err > .10 else "")
        print(f"  {b/10:.1f}-{b/10+.1:.1f} {c['n']:>8}       {pred:.3f}      {obs:.3f}   {err:>+7.3f}{flag}")

    pred_all = sum(c["pred"] for c in buckets.values()) / total
    obs_all = sum(c["lasted"] for c in buckets.values()) / total
    brier = statistics.mean((p - o) ** 2 for p, o in pairs)
    base = statistics.mean(o for _, o in pairs)
    ref = statistics.mean((base - o) ** 2 for _, o in pairs)
    print(f"\n  observations: {total:,} over {len(by_mgr)} managers x 13 pick gaps")
    print(f"  weighted mean |error|: {weighted/total:.3f}")
    print(f"  overall predicted {pred_all:.3f} vs observed {obs_all:.3f}  (bias {obs_all-pred_all:+.3f})")
    print(f"  Brier {brier:.4f} vs {ref:.4f} for always guessing the base rate "
          f"-> skill score {1-brier/ref:+.3f}")
    b2, pairs2 = run(density)
    t2 = sum(c["n"] for c in b2.values())
    pred2 = sum(c["pred"] for c in b2.values()) / t2
    obs2 = sum(c["lasted"] for c in b2.values()) / t2
    w2 = sum(abs(c["lasted"]/c["n"] - c["pred"]/c["n"]) * c["n"] for c in b2.values()) / t2
    print(f"\n  SENSITIVITY -- stretching effective ADP by the observed density of priced")
    print(f"  picks ({matched}/{len(picks)} = {density:.3f}) to account for the slots spent on")
    print(f"  kickers, defenses and unpriced sleepers:")
    print(f"    predicted {pred2:.3f} vs observed {obs2:.3f}  (bias {obs2-pred2:+.3f}), "
          f"weighted mean |error| {w2:.3f}")
    print(f"    mid-range check: ", end="")
    for b in (3, 5, 6):
        if b in b2:
            c = b2[b]
            print(f"[{b/10:.1f}] pred {c['pred']/c['n']:.2f} obs {c['lasted']/c['n']:.2f}  ", end="")
    print()

    print("\n  One real draft. Observations share players and picks, so they are not "
          "\n  independent; read this as calibration shape, not a significance test.")


if __name__ == "__main__":
    main()
