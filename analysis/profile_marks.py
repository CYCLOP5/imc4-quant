import csv
import os
from collections import defaultdict
DATA = os.path.join('prosperity_rust_backtester', 'datasets', 'round4')
PRODUCTS_TRACKED = {'HYDROGEL_PACK', 'VELVETFRUIT_EXTRACT', 'VEV_4000', 'VEV_4500', 'VEV_5000', 'VEV_5100', 'VEV_5200', 'VEV_5300', 'VEV_5400', 'VEV_5500', 'VEV_6000', 'VEV_6500'}

def load_trades():
    rows = []
    for d in (1, 2, 3):
        with open(os.path.join(DATA, f'trades_round_4_day_{d}.csv')) as f:
            r = csv.DictReader(f, delimiter=';')
            for row in r:
                row['day'] = d
                row['timestamp'] = int(row['timestamp'])
                row['price'] = float(row['price'])
                row['quantity'] = int(row['quantity'])
                rows.append(row)
    return rows

def load_mids():
    mids = defaultdict(list)
    for d in (1, 2, 3):
        with open(os.path.join(DATA, f'prices_round_4_day_{d}.csv')) as f:
            r = csv.DictReader(f, delimiter=';')
            for row in r:
                prod = row['product']
                if prod not in PRODUCTS_TRACKED:
                    continue
                ts = int(row['timestamp'])
                mid_str = row['mid_price']
                if not mid_str:
                    continue
                mids[d, prod].append((ts, float(mid_str)))
    for k in mids:
        mids[k].sort()
    return mids

def mid_at(mids_for_prod, ts):
    if not mids_for_prod:
        return None
    lo, hi = (0, len(mids_for_prod) - 1)
    if ts <= mids_for_prod[0][0]:
        return mids_for_prod[0][1]
    if ts >= mids_for_prod[-1][0]:
        return mids_for_prod[-1][1]
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if mids_for_prod[mid][0] <= ts:
            lo = mid
        else:
            hi = mid - 1
    return mids_for_prod[lo][1]

def main():
    trades = load_trades()
    mids = load_mids()
    print(f'loaded {len(trades):,} trades across 3 days, {len(mids)} (day,product) mid-series.')
    all_marks = set()
    for tr in trades:
        all_marks.add(tr['buyer'])
        all_marks.add(tr['seller'])
    print(f'unique counterparty IDs: {len(all_marks)}')
    print(f'  -> {sorted(all_marks)}')
    mp = defaultdict(lambda: defaultdict(lambda: {'n_buy': 0, 'n_sell': 0, 'q_buy': 0, 'q_sell': 0, 'first_ts_d': {}, 'last_ts_d': {}, 'taker_premium_sum': 0.0, 'taker_premium_n': 0, 'sizes': [], 'days_active': set()}))
    for tr in trades:
        d = tr['day']
        ts = tr['timestamp']
        sym = tr['symbol']
        if sym not in PRODUCTS_TRACKED:
            continue
        q = tr['quantity']
        px = tr['price']
        mids_p = mids.get((d, sym))
        m = mid_at(mids_p, ts) if mids_p else None
        for side, mark in (('buy', tr['buyer']), ('sell', tr['seller'])):
            stat = mp[mark][sym]
            stat['days_active'].add(d)
            if side == 'buy':
                stat['n_buy'] += 1
                stat['q_buy'] += q
            else:
                stat['n_sell'] += 1
                stat['q_sell'] += q
            stat['sizes'].append(q)
            if m is not None:
                tp = px - m if side == 'buy' else m - px
                stat['taker_premium_sum'] += tp
                stat['taker_premium_n'] += 1
            if d not in stat['first_ts_d']:
                stat['first_ts_d'][d] = ts
            stat['last_ts_d'][d] = ts
    print('\n=== per-Mark TOTAL profile (all products combined) ===')
    print(f"{'Mark':10s} {'trades':>7s} {'buys':>6s} {'sells':>6s} {'buyQ':>7s} {'sellQ':>7s} {'imb%':>6s} {'avgSz':>6s} {'taker_p':>9s} {'days':>5s} {'topProds':s}")
    mark_totals = []
    for mark in sorted(all_marks):
        n_buy = sum((s['n_buy'] for s in mp[mark].values()))
        n_sell = sum((s['n_sell'] for s in mp[mark].values()))
        q_buy = sum((s['q_buy'] for s in mp[mark].values()))
        q_sell = sum((s['q_sell'] for s in mp[mark].values()))
        sz = []
        for s in mp[mark].values():
            sz += s['sizes']
        tp_sum = sum((s['taker_premium_sum'] for s in mp[mark].values()))
        tp_n = sum((s['taker_premium_n'] for s in mp[mark].values()))
        days = set()
        for s in mp[mark].values():
            days |= s['days_active']
        ntot = n_buy + n_sell
        if ntot == 0:
            continue
        imb = (q_buy - q_sell) / max(1, q_buy + q_sell) * 100
        avg_sz = sum(sz) / len(sz) if sz else 0
        avg_tp = tp_sum / tp_n if tp_n else 0
        per_prod_n = sorted(((sym, s['n_buy'] + s['n_sell']) for sym, s in mp[mark].items()), key=lambda x: -x[1])
        top_prods = ','.join((f'{p}({n})' for p, n in per_prod_n[:3]))
        mark_totals.append((mark, ntot, n_buy, n_sell, q_buy, q_sell, imb, avg_sz, avg_tp, len(days), top_prods))
    mark_totals.sort(key=lambda x: -x[1])
    for row in mark_totals:
        mark, ntot, nb, ns, qb, qs, imb, avgsz, avgtp, days, topp = row
        print(f'{mark:10s} {ntot:>7d} {nb:>6d} {ns:>6d} {qb:>7d} {qs:>7d} {imb:>+5.0f}% {avgsz:>6.1f} {avgtp:>+9.2f} {days:>5d}  {topp}')
    print('\n=== per-PRODUCT: top 5 most-active Marks (with role hints) ===')
    by_prod = defaultdict(list)
    for mark in all_marks:
        for sym, s in mp[mark].items():
            n = s['n_buy'] + s['n_sell']
            if n == 0:
                continue
            imb = (s['q_buy'] - s['q_sell']) / max(1, s['q_buy'] + s['q_sell'])
            avgsz = sum(s['sizes']) / len(s['sizes'])
            tp = s['taker_premium_sum'] / s['taker_premium_n'] if s['taker_premium_n'] else 0
            by_prod[sym].append((mark, n, s['n_buy'], s['n_sell'], imb, avgsz, tp))
    for sym in sorted(by_prod):
        rows = sorted(by_prod[sym], key=lambda x: -x[1])
        print(f'\n  {sym}:')
        print(f"    {'Mark':10s} {'n':>4s} {'buy':>4s} {'sell':>4s} {'imb':>6s} {'avgSz':>6s} {'taker_p':>8s}  role-hint")
        for row in rows[:8]:
            mark, n, nb, ns, imb, avgsz, tp = row
            if abs(imb) < 0.15 and abs(tp) < 0.1:
                role = 'MM-ish (balanced, near-mid)'
            elif tp > 0.3:
                role = f'TAKER (pays {tp:+.2f} avg)'
            elif tp < -0.3:
                role = f'MAKER (collects {-tp:+.2f} avg)'
            elif imb > 0.5:
                role = 'BUY-bias (one-sided long)'
            elif imb < -0.5:
                role = 'SELL-bias (one-sided short)'
            else:
                role = 'mixed'
            print(f'    {mark:10s} {n:>4d} {nb:>4d} {ns:>4d} {imb:>+6.0%} {avgsz:>6.1f} {tp:>+8.2f}  {role}')
if __name__ == '__main__':
    main()
