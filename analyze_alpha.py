import csv
import statistics
from collections import defaultdict
DATA_DIR = '/Users/cyclops/Downloads/TUTORIAL_ROUND_1'

def load_prices(day):
    rows = []
    with open(f'{DATA_DIR}/prices_round_0_day_{day}.csv') as f:
        reader = csv.DictReader(f, delimiter=';')
        for r in reader:
            rows.append(r)
    return rows

def load_trades(day):
    rows = []
    with open(f'{DATA_DIR}/trades_round_0_day_{day}.csv') as f:
        reader = csv.DictReader(f, delimiter=';')
        for r in reader:
            rows.append(r)
    return rows

def analyze_prices(product, rows):
    ts_data = []
    for r in rows:
        if r['product'] != product:
            continue
        ts = int(r['timestamp'])
        mid = float(r['mid_price'])
        bid1 = float(r['bid_price_1']) if r['bid_price_1'] else None
        ask1 = float(r['ask_price_1']) if r['ask_price_1'] else None
        bvol1 = int(r['bid_volume_1']) if r['bid_volume_1'] else 0
        avol1 = int(r['ask_volume_1']) if r['ask_volume_1'] else 0
        bid2 = float(r['bid_price_2']) if r['bid_price_2'] else None
        ask2 = float(r['ask_price_2']) if r['ask_price_2'] else None
        bvol2 = int(r['bid_volume_2']) if r['bid_volume_2'] else 0
        avol2 = int(r['ask_volume_2']) if r['ask_volume_2'] else 0
        bid3 = float(r['bid_price_3']) if r['bid_price_3'] else None
        ask3 = float(r['ask_price_3']) if r['ask_price_3'] else None
        bvol3 = int(r['bid_volume_3']) if r['bid_volume_3'] else 0
        avol3 = int(r['ask_volume_3']) if r['ask_volume_3'] else 0
        spread = ask1 - bid1 if ask1 and bid1 else None
        ts_data.append({'ts': ts, 'mid': mid, 'bid1': bid1, 'ask1': ask1, 'bvol1': bvol1, 'avol1': avol1, 'spread': spread, 'bid2': bid2, 'ask2': ask2, 'bvol2': bvol2, 'avol2': avol2, 'bid3': bid3, 'ask3': ask3, 'bvol3': bvol3, 'avol3': avol3})
    return ts_data

def print_header(title):
    print(f"\n{'=' * 70}")
    print(f'  {title}')
    print(f"{'=' * 70}")
print_header('EMERALDS ANALYSIS')
for day in ['-2', '-1']:
    prices = load_prices(day)
    trades = load_trades(day)
    em_data = analyze_prices('EMERALDS', prices)
    mids = [d['mid'] for d in em_data]
    spreads = [d['spread'] for d in em_data if d['spread']]
    print(f'\n--- Day {day} ---')
    print(f'  Observations: {len(em_data)}')
    print(f'  Mid-price: mean={statistics.mean(mids):.2f}, stdev={statistics.stdev(mids):.2f}, min={min(mids)}, max={max(mids)}')
    print(f'  Spread: mean={statistics.mean(spreads):.2f}, min={min(spreads)}, max={max(spreads)}')
    unusual_mids = [(d['ts'], d['mid'], d['bid1'], d['ask1'], d['bid2'], d['ask2'], d['bid3'], d['ask3']) for d in em_data if d['mid'] != 10000.0]
    print(f'  Times with mid != 10000: {len(unusual_mids)}')
    if unusual_mids[:10]:
        for u in unusual_mids[:10]:
            print(f'    ts={u[0]}: mid={u[1]}, bid1={u[2]}, ask1={u[3]}, bid2={u[4]}, ask2={u[5]}, bid3={u[6]}, ask3={u[7]}')
    imbalances = []
    for d in em_data:
        total_bid = d['bvol1'] + d['bvol2'] + d['bvol3']
        total_ask = d['avol1'] + d['avol2'] + d['avol3']
        imb = total_bid / total_ask if total_ask > 0 else float('inf')
        imbalances.append(imb)
    print(f'  Order imbalance (bid/ask vol ratio): mean={statistics.mean(imbalances):.3f}, stdev={statistics.stdev(imbalances):.3f}')
    em_trades = [t for t in trades if t['symbol'] == 'EMERALDS']
    trade_prices = [float(t['price']) for t in em_trades]
    trade_qtys = [int(t['quantity']) for t in em_trades]
    if trade_prices:
        print(f'  Trades: {len(em_trades)}, avg_price={statistics.mean(trade_prices):.2f}, avg_qty={statistics.mean(trade_qtys):.1f}')
        print(f'  Trade price distribution: {dict(sorted(defaultdict(int, {p: trade_prices.count(p) for p in set(trade_prices)}).items()))}')
print_header('TOMATOES ANALYSIS')
for day in ['-2', '-1']:
    prices = load_prices(day)
    trades = load_trades(day)
    tom_data = analyze_prices('TOMATOES', prices)
    mids = [d['mid'] for d in tom_data]
    spreads = [d['spread'] for d in tom_data if d['spread']]
    print(f'\n--- Day {day} ---')
    print(f'  Observations: {len(tom_data)}')
    print(f'  Mid-price: mean={statistics.mean(mids):.2f}, stdev={statistics.stdev(mids):.2f}, min={min(mids)}, max={max(mids)}')
    print(f'  Spread: mean={statistics.mean(spreads):.2f}, min={min(spreads)}, max={max(spreads)}')
    returns = [mids[i] - mids[i - 1] for i in range(1, len(mids))]
    print(f'  Price changes (1-step): mean={statistics.mean(returns):.4f}, stdev={statistics.stdev(returns):.4f}')
    if len(returns) > 1:
        mean_r = statistics.mean(returns)
        var_r = statistics.variance(returns)
        if var_r > 0:
            lag1_corr = sum(((returns[i] - mean_r) * (returns[i - 1] - mean_r) for i in range(1, len(returns)))) / ((len(returns) - 1) * var_r)
            print(f'  Return autocorrelation (lag1): {lag1_corr:.4f}')
    up_then_down = 0
    up_then_up = 0
    down_then_up = 0
    down_then_down = 0
    for i in range(1, len(returns)):
        if returns[i - 1] > 0:
            if returns[i] < 0:
                up_then_down += 1
            elif returns[i] > 0:
                up_then_up += 1
        elif returns[i - 1] < 0:
            if returns[i] > 0:
                down_then_up += 1
            elif returns[i] < 0:
                down_then_down += 1
    print(f'  Mean reversion signals:')
    print(f'    Up->Down: {up_then_down}, Up->Up: {up_then_up}')
    print(f'    Down->Up: {down_then_up}, Down->Down: {down_then_down}')
    avg_bvol = statistics.mean([d['bvol1'] for d in tom_data])
    avg_avol = statistics.mean([d['avol1'] for d in tom_data])
    future_returns = {}
    for i in range(len(tom_data) - 1):
        total_bid = tom_data[i]['bvol1'] + tom_data[i]['bvol2'] + tom_data[i]['bvol3']
        total_ask = tom_data[i]['avol1'] + tom_data[i]['avol2'] + tom_data[i]['avol3']
        imb = (total_bid - total_ask) / (total_bid + total_ask) if total_bid + total_ask > 0 else 0
        j = min(i + 5, len(tom_data) - 1)
        fut_ret = tom_data[j]['mid'] - tom_data[i]['mid']
        bucket = round(imb, 1)
        if bucket not in future_returns:
            future_returns[bucket] = []
        future_returns[bucket].append(fut_ret)
    print(f'\n  Order imbalance -> Future return (5-step):')
    for bucket in sorted(future_returns.keys()):
        rets = future_returns[bucket]
        if len(rets) > 5:
            print(f'    Imbalance={bucket:+.1f}: avg_ret={statistics.mean(rets):+.3f}, count={len(rets)}')
    tom_trades = [t for t in trades if t['symbol'] == 'TOMATOES']
    trade_prices = [float(t['price']) for t in tom_trades]
    trade_qtys = [int(t['quantity']) for t in tom_trades]
    trade_ts = [int(t['timestamp']) for t in tom_trades]
    if trade_prices:
        print(f'\n  Trades: {len(tom_trades)}, avg_price={statistics.mean(trade_prices):.2f}, avg_qty={statistics.mean(trade_qtys):.1f}')
        trade_signals = []
        for t in tom_trades:
            t_ts = int(t['timestamp'])
            t_price = float(t['price'])
            mid_at_trade = None
            mid_future = None
            for d in tom_data:
                if d['ts'] == t_ts:
                    mid_at_trade = d['mid']
                if d['ts'] == t_ts + 500:
                    mid_future = d['mid']
            if mid_at_trade and mid_future:
                trade_vs_mid = t_price - mid_at_trade
                future_move = mid_future - mid_at_trade
                trade_signals.append((t_ts, t_price, mid_at_trade, trade_vs_mid, future_move))
        if trade_signals:
            above_mid = [s for s in trade_signals if s[3] > 0]
            below_mid = [s for s in trade_signals if s[3] < 0]
            if above_mid:
                avg_future_after_buy = statistics.mean([s[4] for s in above_mid])
                print(f'  Trade above mid (buy signal) -> avg future move: {avg_future_after_buy:+.3f} (n={len(above_mid)})')
            if below_mid:
                avg_future_after_sell = statistics.mean([s[4] for s in below_mid])
                print(f'  Trade below mid (sell signal) -> avg future move: {avg_future_after_sell:+.3f} (n={len(below_mid)})')
print_header('CROSS-ASSET SIGNAL')
for day in ['-2', '-1']:
    prices = load_prices(day)
    em_data = analyze_prices('EMERALDS', prices)
    tom_data = analyze_prices('TOMATOES', prices)
    em_by_ts = {d['ts']: d for d in em_data}
    tom_by_ts = {d['ts']: d for d in tom_data}
    common_ts = sorted(set(em_by_ts.keys()) & set(tom_by_ts.keys()))
    signals = []
    for i, ts in enumerate(common_ts[:-5]):
        em_mid = em_by_ts[ts]['mid']
        em_dev = em_mid - 10000
        future_ts = common_ts[min(i + 5, len(common_ts) - 1)]
        tom_ret = tom_by_ts[future_ts]['mid'] - tom_by_ts[ts]['mid']
        signals.append((em_dev, tom_ret))
    em_devs_nonzero = [(s[0], s[1]) for s in signals if s[0] != 0]
    print(f'\n--- Day {day} ---')
    print(f'  EMERALDS non-zero deviations: {len(em_devs_nonzero)}')
    if em_devs_nonzero:
        pos_dev = [s for s in em_devs_nonzero if s[0] > 0]
        neg_dev = [s for s in em_devs_nonzero if s[0] < 0]
        if pos_dev:
            print(f'    EMERALDS above 10000 -> TOMATOES avg future ret: {statistics.mean([s[1] for s in pos_dev]):+.3f} (n={len(pos_dev)})')
        if neg_dev:
            print(f'    EMERALDS below 10000 -> TOMATOES avg future ret: {statistics.mean([s[1] for s in neg_dev]):+.3f} (n={len(neg_dev)})')
print_header('SPREAD / VOLUME ANOMALY ANALYSIS')
for day in ['-2', '-1']:
    prices = load_prices(day)
    tom_data = analyze_prices('TOMATOES', prices)
    future_returns_by_spread = defaultdict(list)
    for i in range(len(tom_data) - 10):
        sp = tom_data[i]['spread']
        if sp is None:
            continue
        fut_ret = tom_data[i + 10]['mid'] - tom_data[i]['mid']
        sp_bucket = round(sp)
        future_returns_by_spread[sp_bucket].append(fut_ret)
    print(f'\n--- Day {day}: TOMATOES Spread -> Future return (10-step) ---')
    for sp in sorted(future_returns_by_spread.keys()):
        rets = future_returns_by_spread[sp]
        if len(rets) > 5:
            print(f'    Spread={sp}: avg_ret={statistics.mean(rets):+.3f}, stdev={statistics.stdev(rets):.3f}, count={len(rets)}')
    vols = [d['bvol1'] + d['avol1'] for d in tom_data]
    avg_vol = statistics.mean(vols)
    std_vol = statistics.stdev(vols)
    print(f'\n  L1 Volume: avg={avg_vol:.1f}, stdev={std_vol:.1f}')
    spikes = [(d['ts'], d['bvol1'] + d['avol1'], d['mid']) for d in tom_data if d['bvol1'] + d['avol1'] > avg_vol + 2 * std_vol]
    print(f'  Volume spikes (>2σ): {len(spikes)}')
    for s in spikes[:5]:
        print(f'    ts={s[0]}, vol={s[1]}, mid={s[2]}')
print_header('TRADE PRESSURE ANALYSIS')
for day in ['-2', '-1']:
    prices = load_prices(day)
    trades = load_trades(day)
    tom_data = analyze_prices('TOMATOES', prices)
    tom_trades = [t for t in trades if t['symbol'] == 'TOMATOES']
    print(f'\n--- Day {day}: TOMATOES trades buyer/seller info ---')
    has_buyer = sum((1 for t in tom_trades if t.get('buyer', '')))
    has_seller = sum((1 for t in tom_trades if t.get('seller', '')))
    print(f'  Trades with buyer: {has_buyer}/{len(tom_trades)}')
    print(f'  Trades with seller: {has_seller}/{len(tom_trades)}')
    tom_by_ts = {d['ts']: d for d in tom_data}
    buy_trades = []
    sell_trades = []
    for t in tom_trades:
        t_ts = int(t['timestamp'])
        t_price = float(t['price'])
        if t_ts in tom_by_ts:
            d = tom_by_ts[t_ts]
            if d['bid1'] and d['ask1']:
                mid = (d['bid1'] + d['ask1']) / 2
                if t_price >= mid:
                    buy_trades.append(t)
                else:
                    sell_trades.append(t)
    print(f'  Classified: buys={len(buy_trades)}, sells={len(sell_trades)}')
    window = 1000
    trade_pressure = defaultdict(lambda: {'buy_vol': 0, 'sell_vol': 0})
    for t in tom_trades:
        t_ts = int(t['timestamp'])
        t_price = float(t['price'])
        t_qty = int(t['quantity'])
        w = t_ts // window * window
        if t_ts in tom_by_ts:
            d = tom_by_ts[t_ts]
            if d['bid1'] and d['ask1']:
                mid = (d['bid1'] + d['ask1']) / 2
                if t_price >= mid:
                    trade_pressure[w]['buy_vol'] += t_qty
                else:
                    trade_pressure[w]['sell_vol'] += t_qty
    pressure_signals = []
    for w_ts, p in sorted(trade_pressure.items()):
        net = p['buy_vol'] - p['sell_vol']
        future_ts = w_ts + 5000
        if w_ts in tom_by_ts and future_ts in tom_by_ts:
            fut_ret = tom_by_ts[future_ts]['mid'] - tom_by_ts[w_ts]['mid']
            pressure_signals.append((w_ts, net, fut_ret))
    if pressure_signals:
        net_pos = [s for s in pressure_signals if s[1] > 0]
        net_neg = [s for s in pressure_signals if s[1] < 0]
        if net_pos:
            print(f'  Net buy pressure -> avg future return (5000 ticks): {statistics.mean([s[2] for s in net_pos]):+.3f} (n={len(net_pos)})')
        if net_neg:
            print(f'  Net sell pressure -> avg future return (5000 ticks): {statistics.mean([s[2] for s in net_neg]):+.3f} (n={len(net_neg)})')
print_header('PERIODICITY / TIME-OF-DAY EFFECTS')
for day in ['-2', '-1']:
    prices = load_prices(day)
    tom_data = analyze_prices('TOMATOES', prices)
    max_ts = max((d['ts'] for d in tom_data))
    segment_size = max_ts // 10 + 1
    segments = defaultdict(list)
    for d in tom_data:
        seg = d['ts'] // segment_size
        segments[seg].append(d['mid'])
    print(f'\n--- Day {day}: TOMATOES price by segment ---')
    for seg in sorted(segments.keys()):
        mids = segments[seg]
        movement = mids[-1] - mids[0] if len(mids) > 1 else 0
        print(f'    Segment {seg} (ts {seg * segment_size}-{(seg + 1) * segment_size}): mean={statistics.mean(mids):.1f}, move={movement:+.1f}, count={len(mids)}')
print_header('DIRECTIONAL ALPHA: Moving Average Crossover Analysis')
for day in ['-2', '-1']:
    prices = load_prices(day)
    tom_data = analyze_prices('TOMATOES', prices)
    mids = [d['mid'] for d in tom_data]

    def ema(data, period):
        result = [data[0]]
        alpha = 2 / (period + 1)
        for x in data[1:]:
            result.append(alpha * x + (1 - alpha) * result[-1])
        return result
    fast = ema(mids, 10)
    slow = ema(mids, 50)
    pnl = 0
    for i in range(1, len(mids)):
        if fast[i - 1] > slow[i - 1]:
            pnl += mids[i] - mids[i - 1]
        else:
            pnl -= mids[i] - mids[i - 1]
    print(f'\n--- Day {day}: EMA(10)/EMA(50) crossover P&L ---')
    print(f'    P&L = {pnl:.2f}')
    best_pnl = -float('inf')
    best_params = None
    for f_period in [3, 5, 8, 10, 15, 20]:
        for s_period in [20, 30, 50, 75, 100, 200]:
            if f_period >= s_period:
                continue
            f = ema(mids, f_period)
            s = ema(mids, s_period)
            pnl = 0
            for i in range(1, len(mids)):
                if f[i - 1] > s[i - 1]:
                    pnl += mids[i] - mids[i - 1]
                else:
                    pnl -= mids[i] - mids[i - 1]
            if pnl > best_pnl:
                best_pnl = pnl
                best_params = (f_period, s_period)
    print(f'    Best EMA crossover: fast={best_params[0]}, slow={best_params[1]}, P&L={best_pnl:.2f}')
print_header('MOMENTUM ANALYSIS')
for day in ['-2', '-1']:
    prices = load_prices(day)
    tom_data = analyze_prices('TOMATOES', prices)
    mids = [d['mid'] for d in tom_data]
    for lookback in [5, 10, 20, 50]:
        profits = 0
        trades_count = 0
        for i in range(lookback, len(mids) - 1):
            momentum = mids[i] - mids[i - lookback]
            next_ret = mids[i + 1] - mids[i]
            if momentum > 0:
                profits += next_ret
                trades_count += 1
            elif momentum < 0:
                profits -= next_ret
                trades_count += 1
        print(f'  Day {day}, Lookback={lookback}: Momentum P&L={profits:.2f} ({trades_count} trades)')
print_header('MEAN REVERSION ANALYSIS')
for day in ['-2', '-1']:
    prices = load_prices(day)
    tom_data = analyze_prices('TOMATOES', prices)
    mids = [d['mid'] for d in tom_data]
    for lookback in [10, 20, 50, 100]:
        profits = 0
        trades_count = 0
        for i in range(lookback, len(mids) - 1):
            ma = statistics.mean(mids[i - lookback:i])
            dev = mids[i] - ma
            next_ret = mids[i + 1] - mids[i]
            if dev > 0:
                profits -= next_ret
                trades_count += 1
            elif dev < 0:
                profits += next_ret
                trades_count += 1
        print(f'  Day {day}, Lookback={lookback}: Mean Reversion P&L={profits:.2f} ({trades_count} trades)')
print(f"\n{'=' * 70}")
print('DONE')
print(f"{'=' * 70}")
