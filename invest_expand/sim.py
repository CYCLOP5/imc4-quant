import math
import random
from typing import List, Tuple
BUDGET = 50000
COST_PER_PCT = BUDGET / 100.0
LOG101 = math.log(101)

def research(x: int) -> float:
    return 200000.0 * math.log(1 + x) / LOG101

def scale(x: int) -> float:
    return 7.0 * x / 100.0

def speed_mult_from_rank(rank: int, n: int) -> float:
    if n <= 1:
        return 0.9
    return 0.9 - 0.8 * (rank - 1) / (n - 1)

def speed_mult(sp: int, field: List[int]) -> float:
    above = sum((1 for x in field if x > sp))
    rank = above + 1
    return speed_mult_from_rank(rank, len(field) + 1)

def gross(r: int, s: int, sp_mult: float) -> float:
    return research(r) * scale(s) * sp_mult

def pnl(r: int, s: int, sp: int, sp_mult: float) -> float:
    return gross(r, s, sp_mult) - COST_PER_PCT * (r + s + sp)

def gen_field(n_others: int, scenario: str, rng: random.Random) -> List[int]:
    if scenario == 'low':
        return [rng.randint(0, 30) for _ in range(n_others)]
    if scenario == 'mid':
        return [rng.randint(0, 60) for _ in range(n_others)]
    if scenario == 'high':
        return [rng.randint(20, 80) for _ in range(n_others)]
    if scenario == 'bimodal':
        return [rng.choice([0, 5, 10, 40, 60, 80]) for _ in range(n_others)]
    if scenario == 'uniform':
        return [rng.randint(0, 100) for _ in range(n_others)]
    if scenario == 'thirds':
        return [rng.choices([33, 30, 25, 40, 50, 20, 10, 60], weights=[30, 15, 12, 12, 10, 8, 8, 5])[0] for _ in range(n_others)]
    if scenario == 'skewed_low':
        out = []
        for _ in range(n_others):
            if rng.random() < 0.65:
                out.append(rng.randint(0, 25))
            else:
                out.append(rng.randint(40, 80))
        return out
    if scenario == 'beta':
        out = []
        for _ in range(n_others):
            v = rng.betavariate(2.0, 4.0)
            out.append(int(round(v * 100)))
        return out
    if scenario == 'soft_low':
        out = []
        for _ in range(n_others):
            roll = rng.random()
            if roll < 0.3:
                out.append(rng.randint(0, 15))
            elif roll < 0.7:
                out.append(rng.randint(25, 40))
            elif roll < 0.95:
                out.append(rng.randint(45, 55))
            else:
                out.append(rng.randint(60, 80))
        return out
    if scenario == 'soft_skewed':
        out = []
        for _ in range(n_others):
            roll = rng.random()
            if roll < 0.5:
                out.append(rng.randint(0, 20))
            elif roll < 0.9:
                out.append(rng.randint(25, 40))
            else:
                out.append(rng.randint(45, 70))
        return out
    if scenario == 'llm_cluster':
        out = []
        for _ in range(n_others):
            roll = rng.random()
            if roll < 0.15:
                out.append(rng.randint(0, 15))
            elif roll < 0.35:
                out.append(rng.randint(28, 38))
            elif roll < 0.85:
                out.append(rng.randint(35, 50))
            else:
                out.append(rng.randint(50, 80))
        return out
    if scenario == 'competitive_half':
        out = []
        for _ in range(n_others):
            roll = rng.random()
            if roll < 0.4:
                out.append(rng.randint(0, 25))
            elif roll < 0.65:
                out.append(rng.randint(30, 40))
            elif roll < 0.95:
                out.append(rng.randint(35, 55))
            else:
                out.append(rng.randint(60, 90))
        return out
    raise ValueError(scenario)

def exp_speed_mult_table(scenario: str, trials: int, n_others: int, seed: int) -> List[float]:
    rng = random.Random(seed)
    table = [0.0] * 101
    for _ in range(trials):
        field = gen_field(n_others, scenario, rng)
        for sp in range(101):
            table[sp] += speed_mult(sp, field)
    return [v / trials for v in table]

def search(sp_table: List[float]) -> Tuple[float, int, int, int]:
    best = (-1e+18, 0, 0, 0)
    for r in range(0, 101):
        rs_left = 100 - r
        for s in range(0, rs_left + 1):
            sp_left = rs_left - s
            for sp in range(0, sp_left + 1):
                p = pnl(r, s, sp, sp_table[sp])
                if p > best[0]:
                    best = (p, r, s, sp)
    return best

def main():
    scenarios = ['mid', 'high', 'bimodal', 'uniform', 'thirds', 'skewed_low', 'beta', 'soft_low', 'soft_skewed', 'llm_cluster', 'competitive_half']
    print('=' * 86)
    print('invest & expand: per-scenario grid search (integer pcts, n_others=200)')
    print('=' * 86)
    print(f"{'scenario':<12} {'r':>4} {'s':>4} {'sp':>4} {'used':>6} {'pnl':>12} {'gross':>12}")
    sp_tables = {}
    for sc in scenarios:
        tbl = exp_speed_mult_table(sc, trials=400, n_others=200, seed=42)
        sp_tables[sc] = tbl
        p, r, s, sp = search(tbl)
        used = COST_PER_PCT * (r + s + sp)
        g = gross(r, s, tbl[sp])
        print(f'{sc:<12} {r:>4} {s:>4} {sp:>4} {used:>6.0f} {p:>12.1f} {g:>12.1f}')
    print()
    print('=' * 86)
    print('robust selection: max-min pnl across all scenarios')
    print('=' * 86)
    print(f"{'r':>4} {'s':>4} {'sp':>4} {'used':>6} " + ' '.join((f'{sc:>10}' for sc in scenarios)) + f" {'min':>10}")
    candidates = []
    for r in range(0, 101):
        rs_left = 100 - r
        for s in range(0, rs_left + 1):
            sp_left = rs_left - s
            for sp in range(0, sp_left + 1):
                vals = [pnl(r, s, sp, sp_tables[sc][sp]) for sc in scenarios]
                candidates.append((min(vals), vals, r, s, sp))
    candidates.sort(key=lambda x: -x[0])
    for mn, vals, r, s, sp in candidates[:10]:
        used = COST_PER_PCT * (r + s + sp)
        row = f'{r:>4} {s:>4} {sp:>4} {used:>6.0f} ' + ' '.join((f'{v:>10.1f}' for v in vals)) + f' {mn:>10.1f}'
        print(row)
    print()
    print('=' * 86)
    print("robust selection v2: max-min excluding 'low' (savvy field assumption)")
    print('=' * 86)
    sub = ['mid', 'bimodal', 'uniform', 'thirds', 'skewed_low', 'beta', 'soft_low', 'soft_skewed', 'llm_cluster', 'competitive_half']
    print(f"{'r':>4} {'s':>4} {'sp':>4} {'used':>6} " + ' '.join((f'{sc:>10}' for sc in sub)) + f" {'min':>10}")
    cands2 = []
    for r in range(0, 101):
        rs_left = 100 - r
        for s in range(0, rs_left + 1):
            sp_left = rs_left - s
            for sp in range(0, sp_left + 1):
                vals = [pnl(r, s, sp, sp_tables[sc][sp]) for sc in sub]
                cands2.append((min(vals), vals, r, s, sp))
    cands2.sort(key=lambda x: -x[0])
    for mn, vals, r, s, sp in cands2[:10]:
        used = COST_PER_PCT * (r + s + sp)
        row = f'{r:>4} {s:>4} {sp:>4} {used:>6.0f} ' + ' '.join((f'{v:>10.1f}' for v in vals)) + f' {mn:>10.1f}'
        print(row)
    print()
    print('=' * 86)
    print('robust selection v3: max-EXPECTED pnl (uniform avg over scenarios)')
    print('=' * 86)
    print(f"{'r':>4} {'s':>4} {'sp':>4} {'used':>6} " + ' '.join((f'{sc:>10}' for sc in scenarios)) + f" {'avg':>10}")
    cands3 = []
    for r in range(0, 101):
        rs_left = 100 - r
        for s in range(0, rs_left + 1):
            sp_left = rs_left - s
            for sp in range(0, sp_left + 1):
                vals = [pnl(r, s, sp, sp_tables[sc][sp]) for sc in scenarios]
                cands3.append((sum(vals) / len(vals), vals, r, s, sp))
    cands3.sort(key=lambda x: -x[0])
    for avg, vals, r, s, sp in cands3[:10]:
        used = COST_PER_PCT * (r + s + sp)
        row = f'{r:>4} {s:>4} {sp:>4} {used:>6.0f} ' + ' '.join((f'{v:>10.1f}' for v in vals)) + f' {avg:>10.1f}'
        print(row)
    print()
    print('=' * 86)
    print('speed multiplier curves (expected mult vs sp invest)')
    print('=' * 86)
    print(f"{'sp':>4} " + ' '.join((f'{sc:>10}' for sc in scenarios)))
    for sp in (0, 5, 10, 15, 20, 25, 30, 33, 40, 48, 50, 60, 70, 80, 100):
        row = f'{sp:>4} ' + ' '.join((f'{sp_tables[sc][sp]:>10.3f}' for sc in scenarios))
        print(row)
if __name__ == '__main__':
    main()
