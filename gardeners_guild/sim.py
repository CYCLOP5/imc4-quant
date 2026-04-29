from __future__ import annotations
import itertools
from dataclasses import dataclass
from typing import Dict, List, Tuple
import numpy as np
RESERVE_GRID: List[int] = list(range(670, 925, 5))
LIQ: int = 920
GRID_N: int = len(RESERVE_GRID)
FIELD_SCENARIOS: List[int] = list(range(860, 916, 1))
MAIN_SCENARIO: int = 900
BID_LO = 670
BID_HI = 920
BID_STEP = 1

def penalty(b2: int, avg_b2: float) -> float:
    if b2 >= avg_b2:
        return 1.0
    if b2 >= LIQ:
        return 1.0
    return ((LIQ - avg_b2) / (LIQ - b2)) ** 3

def p_reserve_le(b: int) -> float:
    return sum((1 for r in RESERVE_GRID if r <= b)) / GRID_N

def p_reserve_between(lo: int, hi: int) -> float:
    return sum((1 for r in RESERVE_GRID if lo < r <= hi)) / GRID_N

def ev(b1: int, b2: int, avg_b2: float) -> float:
    if b2 < b1:
        return -1000000000.0
    p1 = p_reserve_le(b1)
    p2 = p_reserve_between(b1, b2)
    pr1 = max(0, LIQ - b1)
    pr2 = max(0, LIQ - b2) * penalty(b2, avg_b2)
    return p1 * pr1 + p2 * pr2

@dataclass
class BidPair:
    b1: int
    b2: int
    ev_per_scenario: Dict[int, float]

    @property
    def min_ev(self) -> float:
        return min(self.ev_per_scenario.values())

    @property
    def mean_ev(self) -> float:
        return float(np.mean(list(self.ev_per_scenario.values())))

    @property
    def max_ev(self) -> float:
        return max(self.ev_per_scenario.values())

def full_grid_sweep() -> List[BidPair]:
    pairs: List[BidPair] = []
    for b1 in range(BID_LO, BID_HI + 1, BID_STEP):
        for b2 in range(b1, BID_HI + 1, BID_STEP):
            ev_map = {s: ev(b1, b2, s) for s in FIELD_SCENARIOS}
            pairs.append(BidPair(b1, b2, ev_map))
    return pairs

def best_per_scenario(pairs: List[BidPair]) -> Dict[int, BidPair]:
    out: Dict[int, BidPair] = {}
    for s in FIELD_SCENARIOS:
        out[s] = max(pairs, key=lambda p: p.ev_per_scenario[s])
    return out

def robust_max_min(pairs: List[BidPair]) -> BidPair:
    return max(pairs, key=lambda p: p.min_ev)

def robust_max_mean(pairs: List[BidPair]) -> BidPair:
    return max(pairs, key=lambda p: p.mean_ev)

def top_k_by(pairs: List[BidPair], key_fn, k: int=10) -> List[BidPair]:
    return sorted(pairs, key=lambda p: -key_fn(p))[:k]

def fmt_row(p: BidPair, main_scenario: int=MAIN_SCENARIO) -> str:
    return f'({p.b1:3d},{p.b2:3d})  main={p.ev_per_scenario[main_scenario]:7.3f}  min={p.min_ev:7.3f}  mean={p.mean_ev:7.3f}  max={p.max_ev:7.3f}'

def main() -> None:
    print('reserve grid:', RESERVE_GRID[:4], '...', RESERVE_GRID[-4:])
    print(f'grid size: {GRID_N}, liquidation: {LIQ}')
    print(f'field scenarios: avg_b2 in {FIELD_SCENARIOS[0]}..{FIELD_SCENARIOS[-1]}')
    pairs = full_grid_sweep()
    print(f'evaluated {len(pairs):,} bid pairs')
    print('\n==== single-scenario optima ====')
    for s in [870, 880, 890, 895, 900, 905, 910, 915]:
        best = max(pairs, key=lambda p: p.ev_per_scenario[s])
        print(f'  avg_b2={s}: opt=({best.b1:3d},{best.b2:3d})  ev={best.ev_per_scenario[s]:7.3f}')
    print('\n==== top 10 by max-min (robust) ====')
    for p in top_k_by(pairs, lambda x: x.min_ev, k=10):
        print('  ' + fmt_row(p))
    print('\n==== top 10 by mean across scenarios ====')
    for p in top_k_by(pairs, lambda x: x.mean_ev, k=10):
        print('  ' + fmt_row(p))
    print(f'\n==== top 10 at central scenario avg_b2={MAIN_SCENARIO} ====')
    for p in top_k_by(pairs, lambda x: x.ev_per_scenario[MAIN_SCENARIO], k=10):
        print('  ' + fmt_row(p))
    print('\n==== chosen picks ====')
    mm = robust_max_min(pairs)
    mn = robust_max_mean(pairs)
    cp = max(pairs, key=lambda p: p.ev_per_scenario[MAIN_SCENARIO])
    print('  max-min     : ' + fmt_row(mm))
    print('  max-mean    : ' + fmt_row(mn))
    print('  central prior: ' + fmt_row(cp))
    print('\n==== scenario-by-scenario EV for chosen max-min pair ====')
    for s in FIELD_SCENARIOS[::5]:
        print(f'  avg_b2={s}: ev={mm.ev_per_scenario[s]:7.3f}')
if __name__ == '__main__':
    main()
