import csv
import math
from collections import defaultdict
DATA_DIR = 'round1data'
PRODUCTS = ['ASH_COATED_OSMIUM', 'INTARIAN_PEPPER_ROOT']

def load_prices(filepath):
    rows = []
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            rows.append(row)
    return rows

def load_trades(filepath):
    rows = []
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            rows.append(row)
    return rows

def parse_price_rows(all_rows):
    series = defaultdict(list)
    for row in all_rows:
        product = row.get('product', '')
        if product not in PRODUCTS:
            continue
        mid = row.get('mid_price', '')
        if not mid or mid == '0.0':
            continue
        mid = float(mid)
        ts = int(row['timestamp'])
        day = int(row['day'])
        bp1 = float(row['bid_price_1']) if row.get('bid_price_1') else None
        bv1 = int(row['bid_volume_1']) if row.get('bid_volume_1') else 0
        bp2 = float(row['bid_price_2']) if row.get('bid_price_2') else None
        bv2 = int(row['bid_volume_2']) if row.get('bid_volume_2') else 0
        bp3 = float(row['bid_price_3']) if row.get('bid_price_3') else None
        bv3 = int(row['bid_volume_3']) if row.get('bid_volume_3') else 0
        ap1 = float(row['ask_price_1']) if row.get('ask_price_1') else None
        av1 = int(row['ask_volume_1']) if row.get('ask_volume_1') else 0
        ap2 = float(row['ask_price_2']) if row.get('ask_price_2') else None
        av2 = int(row['ask_volume_2']) if row.get('ask_volume_2') else 0
        ap3 = float(row['ask_price_3']) if row.get('ask_price_3') else None
        av3 = int(row['ask_volume_3']) if row.get('ask_volume_3') else 0
        spread = None
        if bp1 and ap1:
            spread = ap1 - bp1
        series[product].append({'day': day, 'ts': ts, 'mid': mid, 'spread': spread, 'bp1': bp1, 'bv1': bv1, 'bp2': bp2, 'bv2': bv2, 'bp3': bp3, 'bv3': bv3, 'ap1': ap1, 'av1': av1, 'ap2': ap2, 'av2': av2, 'ap3': ap3, 'av3': av3})
    return series

def analyze_product(name, data):
    print(f"\n{'=' * 70}")
    print(f'  {name}')
    print(f"{'=' * 70}")
    mids = [d['mid'] for d in data]
    spreads = [d['spread'] for d in data if d['spread'] is not None]
    print(f'\n--- BASIC STATS ---')
    print(f'  Ticks: {len(data)}')
    print(f'  Mid range: {min(mids):.1f} - {max(mids):.1f}')
    print(f'  Mid mean: {sum(mids) / len(mids):.2f}')
    print(f'  Mid stdev: {stdev(mids):.2f}')
    if spreads:
        print(f'  Spread mean: {sum(spreads) / len(spreads):.2f}')
        print(f'  Spread min/max: {min(spreads):.0f} / {max(spreads):.0f}')
    print(f'\n--- PRICE TREND ---')
    first_chunk = mids[:100]
    last_chunk = mids[-100:]
    print(f'  First 100 avg: {sum(first_chunk) / len(first_chunk):.2f}')
    print(f'  Last 100 avg: {sum(last_chunk) / len(last_chunk):.2f}')
    print(f'  Total drift: {sum(last_chunk) / len(last_chunk) - sum(first_chunk) / len(first_chunk):.2f}')
    print(f'\n--- PER-DAY ANALYSIS ---')
    by_day = defaultdict(list)
    for d in data:
        by_day[d['day']].append(d['mid'])
    for day in sorted(by_day):
        dm = by_day[day]
        print(f'  Day {day}: start={dm[0]:.1f}, end={dm[-1]:.1f}, mean={sum(dm) / len(dm):.2f}, drift={dm[-1] - dm[0]:.1f}')
    print(f'\n--- RETURN AUTOCORRELATION (mean reversion signal) ---')
    returns = [mids[i + 1] - mids[i] for i in range(len(mids) - 1)]
    for lag in [1, 2, 5, 10]:
        if len(returns) > lag:
            ac = autocorrelation(returns, lag)
            signal = 'MEAN REVERSION' if ac < -0.1 else 'MOMENTUM' if ac > 0.1 else 'NOISE'
            print(f'  Lag {lag}: {ac:.4f} ({signal})')
    print(f'\n--- FAIR VALUE ANALYSIS ---')
    from collections import Counter
    mid_counter = Counter([round(m, 1) for m in mids])
    top5 = mid_counter.most_common(5)
    total = len(mids)
    print(f'  Top 5 mid values:')
    for val, cnt in top5:
        print(f'    {val}: {cnt} times ({cnt / total * 100:.1f}%)')
    round_val = round(sum(mids) / len(mids) / 1000) * 1000
    within_10 = sum((1 for m in mids if abs(m - round_val) <= 10))
    within_20 = sum((1 for m in mids if abs(m - round_val) <= 20))
    print(f'  Within ±10 of {round_val}: {within_10 / total * 100:.1f}%')
    print(f'  Within ±20 of {round_val}: {within_20 / total * 100:.1f}%')
    print(f'\n--- ORDER BOOK IMBALANCE ---')
    imb_returns = []
    for i in range(len(data) - 5):
        d = data[i]
        bid_vol = d['bv1'] + d['bv2'] + d['bv3']
        ask_vol = d['av1'] + d['av2'] + d['av3']
        total_vol = bid_vol + ask_vol
        if total_vol == 0:
            continue
        imbalance = (bid_vol - ask_vol) / total_vol
        future_ret = data[i + 5]['mid'] - data[i]['mid']
        imb_returns.append((round(imbalance, 1), future_ret))
    imb_buckets = defaultdict(list)
    for imb, ret in imb_returns:
        imb_buckets[imb].append(ret)
    print(f'  Imbalance -> Avg 5-step return:')
    for imb in sorted(imb_buckets):
        rets = imb_buckets[imb]
        if len(rets) >= 10:
            avg_ret = sum(rets) / len(rets)
            direction = 'CONTRARIAN' if imb > 0 and avg_ret < 0 or (imb < 0 and avg_ret > 0) else 'MOMENTUM'
            print(f'    {imb:+.1f}: avg_ret={avg_ret:+.2f} (n={len(rets)}) [{direction}]')
    print(f'\n--- SPREAD ANALYSIS ---')
    spread_counter = Counter([int(s) for s in spreads])
    print(f'  Spread distribution:')
    for sp in sorted(spread_counter):
        cnt = spread_counter[sp]
        print(f'    spread={sp}: {cnt} ({cnt / len(spreads) * 100:.1f}%)')
    print(f'\n--- WALL ANALYSIS ---')
    wall_bid_offsets = []
    wall_ask_offsets = []
    for d in data:
        if d['bp1'] is None or d['ap1'] is None:
            continue
        mid = d['mid']
        bids = [(d['bp1'], d['bv1']), (d['bp2'], d['bv2']), (d['bp3'], d['bv3'])]
        bids = [(p, v) for p, v in bids if p is not None and v > 0]
        if bids:
            wall_bid = max(bids, key=lambda x: x[1])[0]
            wall_bid_offsets.append(wall_bid - mid)
        asks = [(d['ap1'], d['av1']), (d['ap2'], d['av2']), (d['ap3'], d['av3'])]
        asks = [(p, v) for p, v in asks if p is not None and v > 0]
        if asks:
            wall_ask = min(asks, key=lambda x: -x[1])[0]
            wall_ask_offsets.append(wall_ask - mid)
    if wall_bid_offsets:
        print(f'  Avg wall_bid offset from mid: {sum(wall_bid_offsets) / len(wall_bid_offsets):.2f}')
    if wall_ask_offsets:
        print(f'  Avg wall_ask offset from mid: {sum(wall_ask_offsets) / len(wall_ask_offsets):.2f}')
    print(f'\n--- EMA MEAN REVERSION SIMULATION ---')
    for ema_len in [10, 20, 50]:
        ema = mids[0]
        alpha = 2.0 / (ema_len + 1)
        pnl = 0
        pos = 0
        for i in range(1, len(mids)):
            ema = alpha * mids[i] + (1 - alpha) * ema
            deviation = mids[i] - ema
            target_pos = -1 if deviation > 2 else 1 if deviation < -2 else 0
            if target_pos != pos:
                pnl += (target_pos - pos) * -mids[i]
                pos = target_pos
        pnl += pos * mids[-1]
        print(f'  EMA({ema_len}), threshold=2: simulated pnl = {pnl:.0f}')
    print(f'\n--- MARKET MAKING SIMULATION (simple at mid) ---')
    for edge in [1, 2, 3, 4, 5, 8]:
        mm_pnl = 0
        mm_pos = 0
        limit = 50
        for d in data:
            if d['bp1'] is None or d['ap1'] is None:
                continue
            mid = d['mid']
            our_bid = mid - edge
            our_ask = mid + edge
            if d['ap1'] is not None and d['ap1'] <= our_bid + 0.5 and (mm_pos < limit):
                mm_pos += 1
                mm_pnl -= d['ap1']
            if d['bp1'] is not None and d['bp1'] >= our_ask - 0.5 and (mm_pos > -limit):
                mm_pos -= 1
                mm_pnl += d['bp1']
        mm_pnl += mm_pos * mids[-1]
        print(f'  Edge={edge}: pnl={mm_pnl:.0f}, final_pos={mm_pos}')

def stdev(arr):
    n = len(arr)
    mean = sum(arr) / n
    return math.sqrt(sum(((x - mean) ** 2 for x in arr)) / n)

def autocorrelation(arr, lag=1):
    n = len(arr)
    if n <= lag:
        return 0
    mean = sum(arr) / n
    var = sum(((x - mean) ** 2 for x in arr)) / n
    if var == 0:
        return 0
    cov = sum(((arr[i] - mean) * (arr[i + lag] - mean) for i in range(n - lag))) / (n - lag)
    return cov / var

def analyze_trades(product, trades):
    print(f'\n--- TRADE ANALYSIS: {product} ---')
    prices = [float(t['price']) for t in trades if t.get('symbol') == product]
    qtys = [int(t['quantity']) for t in trades if t.get('symbol') == product]
    if not prices:
        print('  No trades found')
        return
    print(f'  Trade count: {len(prices)}')
    print(f'  Price range: {min(prices):.0f} - {max(prices):.0f}')
    print(f'  Avg price: {sum(prices) / len(prices):.2f}')
    print(f'  Avg qty: {sum(qtys) / len(qtys):.1f}')
    print(f'  Total volume: {sum(qtys)}')

def main():
    print('=' * 70)
    print('  ROUND 1 DATA ANALYSIS - ACO & IPR')
    print('=' * 70)
    all_price_rows = []
    all_trade_rows = []
    for day_suffix in ['-2', '-1', '0']:
        pf = f'{DATA_DIR}/prices_round_1_day_{day_suffix}.csv'
        tf = f'{DATA_DIR}/trades_round_1_day_{day_suffix}.csv'
        try:
            all_price_rows.extend(load_prices(pf))
            print(f'Loaded prices: {pf}')
        except FileNotFoundError:
            print(f'Not found: {pf}')
        try:
            all_trade_rows.extend(load_trades(tf))
            print(f'Loaded trades: {tf}')
        except FileNotFoundError:
            print(f'Not found: {tf}')
    series = parse_price_rows(all_price_rows)
    for product in PRODUCTS:
        if product in series:
            analyze_product(product, series[product])
    for product in PRODUCTS:
        analyze_trades(product, all_trade_rows)
    print(f"\n{'=' * 70}")
    print('  CROSS-ASSET ANALYSIS')
    print(f"{'=' * 70}")
    if 'ASH_COATED_OSMIUM' in series and 'INTARIAN_PEPPER_ROOT' in series:
        aco_by_ts = {}
        ipr_by_ts = {}
        for d in series['ASH_COATED_OSMIUM']:
            key = (d['day'], d['ts'])
            aco_by_ts[key] = d['mid']
        for d in series['INTARIAN_PEPPER_ROOT']:
            key = (d['day'], d['ts'])
            ipr_by_ts[key] = d['mid']
        common = sorted(set(aco_by_ts.keys()) & set(ipr_by_ts.keys()))
        if len(common) > 10:
            aco_rets = []
            ipr_rets = []
            for i in range(1, len(common)):
                aco_rets.append(aco_by_ts[common[i]] - aco_by_ts[common[i - 1]])
                ipr_rets.append(ipr_by_ts[common[i]] - ipr_by_ts[common[i - 1]])
            n = len(aco_rets)
            ma = sum(aco_rets) / n
            mi = sum(ipr_rets) / n
            va = sum(((x - ma) ** 2 for x in aco_rets))
            vi = sum(((x - mi) ** 2 for x in ipr_rets))
            cov = sum(((aco_rets[i] - ma) * (ipr_rets[i] - mi) for i in range(n)))
            if va > 0 and vi > 0:
                corr = cov / math.sqrt(va * vi)
                print(f'  Return correlation ACO/IPR: {corr:.4f}')
            for lag in [1, 2, 5]:
                if len(aco_rets) > lag and len(ipr_rets) > lag:
                    cov_lead = sum((aco_rets[i] * ipr_rets[i + lag] for i in range(n - lag))) / (n - lag)
                    print(f'  ACO return -> IPR return (lag {lag}): {cov_lead:.4f}')
                    cov_lead2 = sum((ipr_rets[i] * aco_rets[i + lag] for i in range(n - lag))) / (n - lag)
                    print(f'  IPR return -> ACO return (lag {lag}): {cov_lead2:.4f}')
if __name__ == '__main__':
    main()
