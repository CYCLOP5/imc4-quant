from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


BUDGET = 1_000_000

GOODS = [
    "obsidian_cutlery",
    "pyroflex_cells",
    "thermalite_core",
    "lava_cake",
    "magma_ink",
    "scoria_paste",
    "ashes_of_the_phoenix",
    "volcanic_incense",
    "sulfur_reactor",
]

DEFAULT_MAX_ALLOCATION = 0.40

PLACEHOLDER_RETURNS: Dict[str, float] = {
    "obsidian_cutlery": 0.25,
    "pyroflex_cells": 0.30,
    "thermalite_core": 0.20,
    "lava_cake": 0.30,
    "magma_ink": 0.15,
    "scoria_paste": 0.0,
    "ashes_of_the_phoenix": 0.0,
    "volcanic_incense": 0.0,
    "sulfur_reactor": 0.20,
}

PLACEHOLDER_DIRECTIONS: Dict[str, str] = {
    "obsidian_cutlery": "buy",
    "pyroflex_cells": "sell",
    "thermalite_core": "buy",
    "lava_cake": "sell",
    "magma_ink": "buy",
    "scoria_paste": "skip",
    "ashes_of_the_phoenix": "skip",
    "volcanic_incense": "skip",
    "sulfur_reactor": "buy",
}


@dataclass
class Leg:
    good: str
    direction: str
    allocation: float
    expected_return: float
    investment: float
    fee: float
    expected_pnl: float

    def as_row(self) -> List[str]:
        pct = self.allocation * 100
        if abs(pct - round(pct)) < 1e-9:
            alloc_s = f"{int(round(pct))}%"
        else:
            alloc_s = f"{pct:.2f}%"
        return [
            self.good,
            self.direction,
            alloc_s,
            f"{self.investment:,.0f}",
            f"{self.fee:,.0f}",
            f"{self.expected_pnl:,.0f}",
        ]


def optimal_allocations(
    expected_returns: Dict[str, float],
    max_allocation: float = DEFAULT_MAX_ALLOCATION,
    sum_allocation_cap: float = 1.0,
) -> Dict[str, float]:
    active = {g: r for g, r in expected_returns.items() if r > 0}
    if not active:
        return {g: 0.0 for g in expected_returns}

    while True:
        unconstrained = {g: r / 2 for g, r in active.items()}
        if sum(unconstrained.values()) <= sum_allocation_cap:
            allocations = unconstrained
            break

        n = len(active)
        lam = (sum(active.values()) - 2 * sum_allocation_cap) / n
        new_active = {g: r for g, r in active.items() if r > lam}
        if len(new_active) == len(active):
            allocations = {g: max(0.0, (r - lam) / 2) for g, r in new_active.items()}
            break
        active = new_active

    capped = {g: min(allocations.get(g, 0.0), max_allocation) for g in expected_returns}
    return capped


def _ev_int_pct(pct: int, r: float, budget: int = BUDGET) -> float:
    if pct <= 0 or r <= 0:
        return 0.0
    a = pct / 100.0
    return budget * (a * r - a * a)


def integer_percent_allocations(
    continuous: Dict[str, float],
    expected_returns: Dict[str, float],
    max_allocation: float = DEFAULT_MAX_ALLOCATION,
    sum_cap_pct: int = 100,
    budget: int = BUDGET,
) -> Dict[str, int]:
    """Whole-number percentages for UI that rejects fractional % (e.g. no 12.5)."""
    max_pct = int(round(max_allocation * 100))
    target = min(
        sum_cap_pct,
        int(round(sum(continuous.get(g, 0.0) * 100 for g in GOODS))),
    )
    p: Dict[str, int] = {}
    for g in GOODS:
        a = continuous.get(g, 0.0)
        pi = int(round(a * 100))
        if expected_returns.get(g, 0.0) <= 0:
            pi = 0
        p[g] = max(0, min(max_pct, pi))

    def marg_down(g: str) -> float:
        if p[g] <= 0:
            return float("-inf")
        r = expected_returns.get(g, 0.0)
        return _ev_int_pct(p[g], r, budget) - _ev_int_pct(p[g] - 1, r, budget)

    def marg_up(g: str) -> float:
        if p[g] >= max_pct:
            return float("-inf")
        r = expected_returns.get(g, 0.0)
        if r <= 0:
            return float("-inf")
        return _ev_int_pct(p[g] + 1, r, budget) - _ev_int_pct(p[g], r, budget)

    while sum(p.values()) > target:
        candidates = [g for g in GOODS if p[g] > 0]
        g_drop = min(candidates, key=lambda g: (marg_down(g), g))
        p[g_drop] -= 1

    while sum(p.values()) < target:
        candidates = [g for g in GOODS if p[g] < max_pct and expected_returns.get(g, 0.0) > 0]
        if not candidates:
            break
        g_add = max(candidates, key=lambda g: (marg_up(g), g))
        p[g_add] += 1

    for g in GOODS:
        if expected_returns.get(g, 0.0) <= 0:
            p[g] = 0
    if sum(p.values()) > sum_cap_pct:
        while sum(p.values()) > sum_cap_pct:
            candidates = [x for x in GOODS if p[x] > 0]
            if not candidates:
                break
            g_drop = min(candidates, key=lambda x: (marg_down(x), x))
            p[g_drop] -= 1

    return p


def build_ticket(
    expected_returns: Dict[str, float],
    directions: Dict[str, str],
    max_allocation: float = DEFAULT_MAX_ALLOCATION,
    budget: int = BUDGET,
    integer_ui: bool = False,
) -> List[Leg]:
    continuous = optimal_allocations(expected_returns, max_allocation)
    if integer_ui:
        p_int = integer_percent_allocations(
            continuous, expected_returns, max_allocation, sum_cap_pct=100, budget=budget
        )
        allocations = {g: p_int[g] / 100.0 for g in GOODS}
    else:
        allocations = continuous
    legs: List[Leg] = []
    for good in GOODS:
        a = allocations.get(good, 0.0)
        r = expected_returns.get(good, 0.0)
        direction = directions.get(good, "skip")
        if a <= 0 or r <= 0:
            direction = "skip"
        investment = a * budget
        fee = (a ** 2) * budget
        expected_pnl = investment * r - fee
        legs.append(
            Leg(
                good=good,
                direction=direction,
                allocation=a,
                expected_return=r,
                investment=investment,
                fee=fee,
                expected_pnl=expected_pnl,
            )
        )
    return legs


def render(legs: List[Leg]) -> str:
    headers = ["good", "direction", "alloc", "investment", "fee", "exp PnL"]
    rows = [leg.as_row() for leg in legs]
    widths = [max(len(h), max((len(r[i]) for r in rows), default=0)) for i, h in enumerate(headers)]
    line = lambda cells: "  ".join(c.ljust(widths[i]) for i, c in enumerate(cells))
    out = [line(headers), line(["-" * w for w in widths])]
    out.extend(line(r) for r in rows)
    total_inv = sum(leg.investment for leg in legs)
    total_fee = sum(leg.fee for leg in legs)
    total_pnl = sum(leg.expected_pnl for leg in legs)
    out.append(line(["-" * w for w in widths]))
    tot_pct = total_inv / BUDGET * 100
    tot_alloc_s = f"{int(round(tot_pct))}%" if abs(tot_pct - round(tot_pct)) < 1e-9 else f"{tot_pct:.2f}%"
    out.append(
        line(
            [
                "TOTAL",
                "",
                tot_alloc_s,
                f"{total_inv:,.0f}",
                f"{total_fee:,.0f}",
                f"{total_pnl:,.0f}",
            ]
        )
    )
    return "\n".join(out)


def sensitivity(
    expected_returns: Dict[str, float],
    deltas: Optional[List[float]] = None,
) -> str:
    if deltas is None:
        deltas = [-0.05, -0.02, 0.0, 0.02, 0.05]

    base_legs = build_ticket(expected_returns, PLACEHOLDER_DIRECTIONS)
    base_pnl = sum(leg.expected_pnl for leg in base_legs)

    rows = [["good", "base r", *(f"+{d:+.2f}r ⇒ ΔEV" for d in deltas)]]
    for good in GOODS:
        base_r = expected_returns.get(good, 0.0)
        row = [good, f"{base_r:.3f}"]
        for d in deltas:
            bumped = dict(expected_returns)
            bumped[good] = max(0.0, base_r + d)
            new_legs = build_ticket(bumped, PLACEHOLDER_DIRECTIONS)
            new_pnl = sum(leg.expected_pnl for leg in new_legs)
            row.append(f"{new_pnl - base_pnl:+,.0f}")
        rows.append(row)
    widths = [max(len(r[i]) for r in rows) for i in range(len(rows[0]))]
    return "\n".join("  ".join(c.ljust(widths[i]) for i, c in enumerate(r)) for r in rows)


def main():
    print("IGNITH UI: TYPE THE alloc COLUMN (whole %, see table) NOT r×100 (25, 30, …).")
    print("25% in UI = r by mistake → 140% budget + fee blowup. cap is 100%.")
    print("this game rejects fractional % (12.5 / 7.5) — ticket below uses integer %.")
    print()
    legs = build_ticket(PLACEHOLDER_RETURNS, PLACEHOLDER_DIRECTIONS, integer_ui=True)
    print(render(legs))
    print()
    print(sensitivity(PLACEHOLDER_RETURNS))


if __name__ == "__main__":
    main()
