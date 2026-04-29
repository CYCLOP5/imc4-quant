from __future__ import annotations

import csv
import math
from collections import defaultdict
from pathlib import Path
from statistics import mean, median, pstdev
from typing import Dict, Iterable, List, Sequence, Tuple


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "prosperity_rust_backtester" / "datasets" / "round5"
REPORT = ROOT / "analysis" / "round5_research.md"
DAYS = (2, 3, 4)

FAMILIES: Dict[str, List[str]] = {
    "GALAXY_SOUNDS": [
        "GALAXY_SOUNDS_DARK_MATTER",
        "GALAXY_SOUNDS_BLACK_HOLES",
        "GALAXY_SOUNDS_PLANETARY_RINGS",
        "GALAXY_SOUNDS_SOLAR_WINDS",
        "GALAXY_SOUNDS_SOLAR_FLAMES",
    ],
    "SLEEP_POD": [
        "SLEEP_POD_SUEDE",
        "SLEEP_POD_LAMB_WOOL",
        "SLEEP_POD_POLYESTER",
        "SLEEP_POD_NYLON",
        "SLEEP_POD_COTTON",
    ],
    "MICROCHIP": [
        "MICROCHIP_CIRCLE",
        "MICROCHIP_OVAL",
        "MICROCHIP_SQUARE",
        "MICROCHIP_RECTANGLE",
        "MICROCHIP_TRIANGLE",
    ],
    "PEBBLES": [
        "PEBBLES_XS",
        "PEBBLES_S",
        "PEBBLES_M",
        "PEBBLES_L",
        "PEBBLES_XL",
    ],
    "ROBOT": [
        "ROBOT_VACUUMING",
        "ROBOT_MOPPING",
        "ROBOT_DISHES",
        "ROBOT_LAUNDRY",
        "ROBOT_IRONING",
    ],
    "UV_VISOR": [
        "UV_VISOR_YELLOW",
        "UV_VISOR_AMBER",
        "UV_VISOR_ORANGE",
        "UV_VISOR_RED",
        "UV_VISOR_MAGENTA",
    ],
    "TRANSLATOR": [
        "TRANSLATOR_SPACE_GRAY",
        "TRANSLATOR_ASTRO_BLACK",
        "TRANSLATOR_ECLIPSE_CHARCOAL",
        "TRANSLATOR_GRAPHITE_MIST",
        "TRANSLATOR_VOID_BLUE",
    ],
    "PANEL": [
        "PANEL_1X2",
        "PANEL_2X2",
        "PANEL_1X4",
        "PANEL_2X4",
        "PANEL_4X4",
    ],
    "OXYGEN_SHAKE": [
        "OXYGEN_SHAKE_MORNING_BREATH",
        "OXYGEN_SHAKE_EVENING_BREATH",
        "OXYGEN_SHAKE_MINT",
        "OXYGEN_SHAKE_CHOCOLATE",
        "OXYGEN_SHAKE_GARLIC",
    ],
    "SNACKPACK": [
        "SNACKPACK_CHOCOLATE",
        "SNACKPACK_VANILLA",
        "SNACKPACK_PISTACHIO",
        "SNACKPACK_STRAWBERRY",
        "SNACKPACK_RASPBERRY",
    ],
}

PRODUCT_TO_FAMILY = {
    product: family for family, products in FAMILIES.items() for product in products
}

ReturnCache = Dict[int, Dict[str, List[float]]]


def fnum(value: str) -> float | None:
    return float(value) if value not in ("", None) else None


def corr(xs: Sequence[float], ys: Sequence[float]) -> float:
    n = min(len(xs), len(ys))
    if n < 3:
        return 0.0
    x = xs[:n]
    y = ys[:n]
    mx = sum(x) / n
    my = sum(y) / n
    num = sum((a - mx) * (b - my) for a, b in zip(x, y))
    vx = sum((a - mx) ** 2 for a in x)
    vy = sum((b - my) ** 2 for b in y)
    den = math.sqrt(vx * vy)
    return num / den if den else 0.0


def returns(series: Sequence[float]) -> List[float]:
    return [series[i] - series[i - 1] for i in range(1, len(series))]


def build_return_cache(prices: Dict[int, Dict[str, List[dict]]]) -> ReturnCache:
    return {
        day: {
            product: returns([record["mid"] for record in records])
            for product, records in products.items()
        }
        for day, products in prices.items()
    }


def read_prices() -> Dict[int, Dict[str, List[dict]]]:
    by_day: Dict[int, Dict[str, List[dict]]] = {}
    for day in DAYS:
        path = DATASET / f"prices_round_5_day_{day}.csv"
        products: Dict[str, List[dict]] = defaultdict(list)
        with path.open(newline="") as fh:
            reader = csv.DictReader(fh, delimiter=";")
            for row in reader:
                product = row["product"]
                bid = fnum(row["bid_price_1"])
                ask = fnum(row["ask_price_1"])
                spread = (ask - bid) if bid is not None and ask is not None else None
                products[product].append(
                    {
                        "timestamp": int(row["timestamp"]),
                        "mid": float(row["mid_price"]),
                        "spread": spread,
                        "bid_vol": abs(int(row["bid_volume_1"] or 0)),
                        "ask_vol": abs(int(row["ask_volume_1"] or 0)),
                    }
                )
        by_day[day] = dict(products)
    return by_day


def read_trades() -> Dict[str, dict]:
    by_day = read_trades_by_day()
    stats: Dict[str, dict] = defaultdict(lambda: {"count": 0, "volume": 0, "notional": 0.0})
    for products in by_day.values():
        for product, row in products.items():
            stats[product]["count"] += row["count"]
            stats[product]["volume"] += row["volume"]
            stats[product]["notional"] += row["notional"]
    return dict(stats)


def read_trades_by_day() -> Dict[int, Dict[str, dict]]:
    by_day: Dict[int, Dict[str, dict]] = {}
    for day in DAYS:
        by_day[day] = defaultdict(lambda: {"count": 0, "volume": 0, "notional": 0.0})
        path = DATASET / f"trades_round_5_day_{day}.csv"
        with path.open(newline="") as fh:
            reader = csv.DictReader(fh, delimiter=";")
            for row in reader:
                product = row["symbol"]
                qty = int(float(row["quantity"]))
                price = float(row["price"])
                by_day[day][product]["count"] += 1
                by_day[day][product]["volume"] += qty
                by_day[day][product]["notional"] += price * qty
        by_day[day] = dict(by_day[day])
    return by_day


def product_metrics(prices: Dict[int, Dict[str, List[dict]]], trades: Dict[str, dict]):
    rows = []
    for product, family in PRODUCT_TO_FAMILY.items():
        mids_by_day = []
        spreads = []
        depths = []
        drifts = []
        ret_all = []
        acfs = []
        for day in DAYS:
            records = prices[day][product]
            mids = [r["mid"] for r in records]
            rets = returns(mids)
            mids_by_day.append(mids)
            ret_all.extend(rets)
            drifts.append(mids[-1] - mids[0])
            spreads.extend(r["spread"] for r in records if r["spread"] is not None)
            depths.extend((r["bid_vol"] + r["ask_vol"]) / 2 for r in records)
            if len(rets) > 2:
                acfs.append(corr(rets[:-1], rets[1:]))
        tr = trades.get(product, {"count": 0, "volume": 0, "notional": 0.0})
        vol = pstdev(ret_all) if len(ret_all) > 1 else 0.0
        rows.append(
            {
                "product": product,
                "family": family,
                "avg_spread": mean(spreads),
                "med_spread": median(spreads),
                "avg_l1_depth": mean(depths),
                "trade_count": tr["count"],
                "trade_volume": tr["volume"],
                "avg_abs_drift": mean(abs(x) for x in drifts),
                "drifts": drifts,
                "ret_vol": vol,
                "acf1": mean(acfs) if acfs else 0.0,
                "mm_score": mean(spreads) * math.sqrt(max(tr["volume"], 1)) / (1 + vol),
            }
        )
    return rows


def family_metrics(rows: List[dict], prices: Dict[int, Dict[str, List[dict]]]):
    result = []
    for family, products in FAMILIES.items():
        family_rows = [r for r in rows if r["family"] == family]
        intra_corrs = []
        for day in DAYS:
            for i, a in enumerate(products):
                for b in products[i + 1 :]:
                    ra = returns([r["mid"] for r in prices[day][a]])
                    rb = returns([r["mid"] for r in prices[day][b]])
                    intra_corrs.append(corr(ra, rb))
        result.append(
            {
                "family": family,
                "avg_spread": mean(r["avg_spread"] for r in family_rows),
                "trade_volume": sum(r["trade_volume"] for r in family_rows),
                "avg_abs_drift": mean(r["avg_abs_drift"] for r in family_rows),
                "ret_vol": mean(r["ret_vol"] for r in family_rows),
                "acf1": mean(r["acf1"] for r in family_rows),
                "intra_corr": mean(intra_corrs),
                "mm_score": sum(r["mm_score"] for r in family_rows),
            }
        )
    return result


def family_day_metrics(
    prices: Dict[int, Dict[str, List[dict]]], trades_by_day: Dict[int, Dict[str, dict]]
) -> List[dict]:
    rows = []
    for family, products in FAMILIES.items():
        for day in DAYS:
            spreads = []
            signed_drifts = []
            abs_drifts = []
            trade_volume = 0
            for product in products:
                records = prices[day][product]
                mids = [r["mid"] for r in records]
                drift = mids[-1] - mids[0]
                signed_drifts.append(drift)
                abs_drifts.append(abs(drift))
                spreads.extend(r["spread"] for r in records if r["spread"] is not None)
                trade_volume += trades_by_day[day].get(product, {}).get("volume", 0)
            rows.append(
                {
                    "family": family,
                    "day": day,
                    "avg_spread": mean(spreads),
                    "trade_volume": trade_volume,
                    "avg_signed_drift": mean(signed_drifts),
                    "avg_abs_drift": mean(abs_drifts),
                    "drift_dispersion": pstdev(signed_drifts),
                }
            )
    return rows


def family_return(prices: Dict[int, Dict[str, List[dict]]], day: int, family: str) -> List[float]:
    product_returns = [
        returns([r["mid"] for r in prices[day][product]]) for product in FAMILIES[family]
    ]
    n = min(len(r) for r in product_returns)
    return [mean(r[i] for r in product_returns) for i in range(n)]


def cached_family_return(return_cache: ReturnCache, day: int, family: str) -> List[float]:
    product_returns = [return_cache[day][product] for product in FAMILIES[family]]
    n = min(len(r) for r in product_returns)
    return [mean(r[i] for r in product_returns) for i in range(n)]


def lag_scan_family(prices: Dict[int, Dict[str, List[dict]]], max_lag: int = 20):
    candidates = []
    fams = list(FAMILIES)
    return_cache = build_return_cache(prices)
    family_returns = {
        (day, family): cached_family_return(return_cache, day, family)
        for day in DAYS
        for family in fams
    }
    for leader in fams:
        for follower in fams:
            if leader == follower:
                continue
            same_day_lead = []
            best = {"lag": 0, "corr": 0.0, "lift": 0.0}
            for day in DAYS:
                lr = family_returns[(day, leader)]
                fr = family_returns[(day, follower)]
                same_day_lead.append(corr(lr, fr))
            base = mean(same_day_lead)
            for lag in range(1, max_lag + 1):
                vals = []
                for day in DAYS:
                    lr = family_returns[(day, leader)]
                    fr = family_returns[(day, follower)]
                    vals.append(corr(lr[:-lag], fr[lag:]))
                value = mean(vals)
                lift = value - base
                if abs(value) > abs(best["corr"]):
                    best = {"lag": lag, "corr": value, "lift": lift}
            if abs(best["corr"]) > 0.08 and abs(best["lift"]) > 0.03:
                candidates.append((leader, follower, base, best["lag"], best["corr"], best["lift"]))
    return sorted(candidates, key=lambda x: (abs(x[4]), abs(x[5])), reverse=True)


def lag_scan_within_family(prices: Dict[int, Dict[str, List[dict]]], max_lag: int = 20):
    candidates = []
    return_cache = build_return_cache(prices)
    for family, products in FAMILIES.items():
        for leader in products:
            for follower in products:
                if leader == follower:
                    continue
                base_vals = []
                best = {"lag": 0, "corr": 0.0, "lift": 0.0}
                for day in DAYS:
                    lr = return_cache[day][leader]
                    fr = return_cache[day][follower]
                    base_vals.append(corr(lr, fr))
                base = mean(base_vals)
                for lag in range(1, max_lag + 1):
                    vals = []
                    for day in DAYS:
                        lr = return_cache[day][leader]
                        fr = return_cache[day][follower]
                        vals.append(corr(lr[:-lag], fr[lag:]))
                    value = mean(vals)
                    lift = value - base
                    if abs(value) > abs(best["corr"]):
                        best = {"lag": lag, "corr": value, "lift": lift}
                if abs(best["corr"]) > 0.08 and abs(best["lift"]) > 0.04:
                    candidates.append((family, leader, follower, base, best["lag"], best["corr"], best["lift"]))
    return sorted(candidates, key=lambda x: (abs(x[5]), abs(x[6])), reverse=True)


def pair_residual_series(
    a_mids: Sequence[float], b_mids: Sequence[float], return_corr: float
) -> Tuple[str, List[float]]:
    if return_corr >= 0:
        return "spread", [a - b for a, b in zip(a_mids, b_mids)]
    return "basket", [a + b for a, b in zip(a_mids, b_mids)]


def pair_spreads(prices: Dict[int, Dict[str, List[dict]]]):
    rows = []
    for family, products in FAMILIES.items():
        for i, a in enumerate(products):
            for b in products[i + 1 :]:
                all_a_returns = []
                all_b_returns = []
                all_a_mids = []
                all_b_mids = []
                for day in DAYS:
                    ma = [r["mid"] for r in prices[day][a]]
                    mb = [r["mid"] for r in prices[day][b]]
                    all_a_mids.extend(ma)
                    all_b_mids.extend(mb)
                    all_a_returns.extend(returns(ma))
                    all_b_returns.extend(returns(mb))
                return_corr = corr(all_a_returns, all_b_returns)
                relation, residuals = pair_residual_series(all_a_mids, all_b_mids, return_corr)
                day_means = []
                for day in DAYS:
                    ma = [r["mid"] for r in prices[day][a]]
                    mb = [r["mid"] for r in prices[day][b]]
                    _, residual_day = pair_residual_series(ma, mb, return_corr)
                    day_means.append(mean(residual_day))
                spread_std = pstdev(residuals) if len(residuals) > 1 else 0.0
                day_mean_range = max(day_means) - min(day_means)
                stability = abs(return_corr) / (1 + day_mean_range / max(spread_std, 1.0))
                rows.append(
                    {
                        "family": family,
                        "a": a,
                        "b": b,
                        "relation": relation,
                        "corr": return_corr,
                        "spread_std": spread_std,
                        "spread_range": max(residuals) - min(residuals),
                        "day_mean_range": day_mean_range,
                        "stability": stability,
                    }
                )
    return sorted(rows, key=lambda r: (-abs(r["corr"]), r["day_mean_range"], r["spread_std"]))


def md_table(headers: Sequence[str], rows: Iterable[Sequence[object]]) -> List[str]:
    lines = ["| " + " | ".join(headers) + " |"]
    lines.append("|" + "|".join("---" for _ in headers) + "|")
    for row in rows:
        lines.append("| " + " | ".join(str(x) for x in row) + " |")
    return lines


def fmt(value: float, digits: int = 2) -> str:
    return f"{value:.{digits}f}"


def write_report():
    prices = read_prices()
    trades = read_trades()
    trades_by_day = read_trades_by_day()
    products = product_metrics(prices, trades)
    families = family_metrics(products, prices)
    family_days = family_day_metrics(prices, trades_by_day)
    fam_lags = lag_scan_family(prices)
    prod_lags = lag_scan_within_family(prices)
    pairs = pair_spreads(prices)

    lines = [
        "# r5 research pass 1",
        "",
        "source: `prosperity_rust_backtester/datasets/round5/` days d+2 d+3 d+4. generator: `analysis/round5_research.py`.",
        "",
        "## family snapshot",
        "",
    ]
    families_sorted = sorted(families, key=lambda r: r["mm_score"], reverse=True)
    lines += md_table(
        ["family", "mm_score", "spread", "trade_vol", "abs_drift", "ret_vol", "acf1", "intra_corr"],
        [
            [
                r["family"],
                fmt(r["mm_score"]),
                fmt(r["avg_spread"]),
                r["trade_volume"],
                fmt(r["avg_abs_drift"]),
                fmt(r["ret_vol"]),
                fmt(r["acf1"], 3),
                fmt(r["intra_corr"], 3),
            ]
            for r in families_sorted
        ],
    )

    lines += [
        "",
        "## family day stability",
        "",
        "signed drift: avg of (close-open) over the 5 names in the family. `drift_dispersion`: stdev of those 5 signed drifts — did they move together.",
        "",
    ]
    lines += md_table(
        ["family", "day", "spread", "trade_vol", "signed_drift", "abs_drift", "drift_dispersion"],
        [
            [
                r["family"],
                f"D+{r['day']}",
                fmt(r["avg_spread"]),
                r["trade_volume"],
                fmt(r["avg_signed_drift"]),
                fmt(r["avg_abs_drift"]),
                fmt(r["drift_dispersion"]),
            ]
            for r in sorted(family_days, key=lambda row: (row["family"], row["day"]))
        ],
    )

    lines += [
        "",
        "## product passive-mm shortlist",
        "",
        "`mm_score = avg_spread * sqrt(trade_volume) / (1 + return_vol)` — triage only.",
        "",
    ]
    product_sorted = sorted(products, key=lambda r: r["mm_score"], reverse=True)
    lines += md_table(
        ["product", "family", "score", "spread", "trade_vol", "abs_drift", "acf1", "drifts d2/d3/d4"],
        [
            [
                r["product"],
                r["family"],
                fmt(r["mm_score"]),
                fmt(r["avg_spread"]),
                r["trade_volume"],
                fmt(r["avg_abs_drift"]),
                fmt(r["acf1"], 3),
                "/".join(fmt(x, 0) for x in r["drifts"]),
            ]
            for r in product_sorted[:15]
        ],
    )

    lines += [
        "",
        "## family lead/lag candidates",
        "",
        "lag in 100-tick bars. filter: meaningful |lag_corr|, not just lift off a weak same-time baseline.",
        "",
    ]
    lines += md_table(
        ["leader", "follower", "same_time", "lag", "lag_corr", "lift"],
        [
            [leader, follower, fmt(base, 3), lag, fmt(value, 3), fmt(lift, 3)]
            for leader, follower, base, lag, value, lift in fam_lags[:15]
        ],
    )

    lines += [
        "",
        "## same-family product lead/lag candidates",
        "",
        "stricter bar on |lag_corr| so the table is not fake signal from -0.9 same-time corr washing out at lag.",
        "",
    ]
    lines += md_table(
        ["family", "leader", "follower", "same_time", "lag", "lag_corr", "lift"],
        [
            [family, leader, follower, fmt(base, 3), lag, fmt(value, 3), fmt(lift, 3)]
            for family, leader, follower, base, lag, value, lift in prod_lags[:20]
        ],
    )

    lines += [
        "",
        "## same-family pair candidates",
        "",
        "`spread`: corr ≥ 0, residual `a-b`. `basket`: corr < 0, residual `a+b`.",
        "",
    ]
    lines += md_table(
        ["family", "relation", "a", "b", "corr", "resid_std", "resid_range", "day_mean_range"],
        [
            [
                r["family"],
                r["relation"],
                r["a"],
                r["b"],
                fmt(r["corr"], 3),
                fmt(r["spread_std"]),
                fmt(r["spread_range"]),
                fmt(r["day_mean_range"]),
            ]
            for r in pairs[:20]
        ],
    )

    lines += [
        "",
        "## what i took from this",
        "",
        "- cross-family lead/lag table was empty under the strict filter — i did not build the live trader on cross-family lag.",
        "- `SNACKPACK` looked best on mm_score + internal pairs (berry/choc-vanilla neg corr). still needs causal replay before trusting.",
        "- neg corr pairs → basket/residual framing more honest than pretending they move together.",
        "- i promoted nothing from this file into `trader.py` without rust replay; the skip-list came from per-product replay pnl not from this notebook.",
        "",
    ]

    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {REPORT}")


if __name__ == "__main__":
    write_report()
