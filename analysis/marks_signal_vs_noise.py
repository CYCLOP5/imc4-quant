import csv
import os
from collections import defaultdict
DATA = os.path.join('prosperity_rust_backtester', 'datasets', 'round4')
PRODUCTS = ['HYDROGEL_PACK', 'VELVETFRUIT_EXTRACT', 'VEV_4000']
WINDOWS = (500, 2000, 5000)

def load_mids():
    mids = defaultdict(list)
    for d in (1, 2, 3):
        with open(os.path.join(DATA, f'prices_round_4_day_{d}.csv')) as f:
            r = csv.DictReader(f, delimiter=';')
            for row in r:
                if row['product'] not in PRODUCTS:
                    continue
                if not row['mid_price']:
                    continue
                mids[d, row['product']].append((int(row['timestamp']), float(row['mid_price'])))
    for k in mids:
        mids[k].sort()
    return mids

def mid_at(seq, ts):
    if not seq or ts < seq[0][0]:
        return None
    if ts >= seq[-1][0]:
        return seq[-1][1]
    lo, hi = (0, len(seq) - 1)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if seq[mid][0] <= ts:
            lo = mid
        else:
            hi = mid - 1
    return seq[lo][1]

def main():
    mids = load_mids()
    trades = []
    for d in (1, 2, 3):
        with open(os.path.join(DATA, f'trades_round_4_day_{d}.csv')) as f:
            r = csv.DictReader(f, delimiter=';')
            for row in r:
                if row['symbol'] not in PRODUCTS:
                    continue
                trades.append((d, int(row['timestamp']), row['symbol'], row['buyer'], row['seller'], float(row['price']), int(row['quantity'])))
    agg = defaultdict(lambda: defaultdict(list))
    for d, ts, sym, b, s, px, q in trades:
        seq = mids[d, sym]
        m_now = mid_at(seq, ts)
        if m_now is None:
            continue
        for win in WINDOWS:
            m_fut = mid_at(seq, ts + win)
            if m_fut is None:
                continue
            drift = m_fut - m_now
            agg[b, sym, 'buy'][win].append(drift)
            agg[s, sym, 'sell'][win].append(drift)
    print(f"{'Mark':10s} {'product':22s} {'side':4s} " + ''.join((f'  drift_{w}'.rjust(14) for w in WINDOWS)) + f"  {'n':>6s}")
    print('-' * 100)
    rows = []
    for key, by_w in agg.items():
        mark, sym, side = key
        n = len(by_w[WINDOWS[0]])
        if n < 30:
            continue
        line_vals = [sum(by_w[w]) / len(by_w[w]) for w in WINDOWS]
        rows.append((mark, sym, side, n, line_vals))
    rows.sort(key=lambda x: (x[1], x[0], x[2]))
    for mark, sym, side, n, vals in rows:
        v_str = ''.join((f'  {v:>+12.2f}' for v in vals))
        print(f'{mark:10s} {sym:22s} {side:4s}{v_str}  {n:>6d}')
    print('\n=== role classification (using drift_2000) ===')
    print(f"{'Mark':10s} {'product':22s} {'side':4s} {'drift':>8s}  classification")
    for mark, sym, side, n, vals in rows:
        d = vals[1]
        if side == 'buy':
            cls = 'INFORMED buyer' if d > 1.0 else 'NOISE buyer' if d < -1.0 else 'neutral buyer'
        else:
            cls = 'INFORMED seller' if d < -1.0 else 'NOISE seller' if d > 1.0 else 'neutral seller'
        print(f'{mark:10s} {sym:22s} {side:4s} {d:>+8.2f}  {cls}')
if __name__ == '__main__':
    main()
