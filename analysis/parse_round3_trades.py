import json
import os
from collections import defaultdict
LOG_PATH = os.path.join('LOGS', '486260', '486260.log')
JSON_PATH = os.path.join('LOGS', '486260', '486260.json')
with open(LOG_PATH, 'r') as f:
    log = json.load(f)
with open(JSON_PATH, 'r') as f:
    js = json.load(f)
print(f"profit (official): {js['profit']:,.0f}")
print(f"submissionId: {log['submissionId']}")
trades = log['tradeHistory']
print(f'\ntradeHistory entries (SUBMISSION participating): {len(trades):,}')
per_prod = defaultdict(lambda: {'buys': 0, 'sells': 0, 'buy_vol': 0, 'sell_vol': 0, 'buy_notional': 0.0, 'sell_notional': 0.0, 'last_pos': 0, 'peak_long': 0, 'peak_short': 0, 'first_ts': None, 'last_ts': None, 'positions_over_time': []})
trades_sorted = sorted(trades, key=lambda t: t['timestamp'])
for tr in trades_sorted:
    sym = tr['symbol']
    ts = tr['timestamp']
    qty = int(tr['quantity'])
    price = float(tr['price'])
    p = per_prod[sym]
    if tr['buyer'] == 'SUBMISSION':
        p['buys'] += 1
        p['buy_vol'] += qty
        p['buy_notional'] += qty * price
        p['last_pos'] += qty
    elif tr['seller'] == 'SUBMISSION':
        p['sells'] += 1
        p['sell_vol'] += qty
        p['sell_notional'] += qty * price
        p['last_pos'] -= qty
    p['peak_long'] = max(p['peak_long'], p['last_pos'])
    p['peak_short'] = min(p['peak_short'], p['last_pos'])
    if p['first_ts'] is None:
        p['first_ts'] = ts
    p['last_ts'] = ts
    p['positions_over_time'].append((ts, p['last_pos']))
LIMITS = {'HYDROGEL_PACK': 200, 'VELVETFRUIT_EXTRACT': 200, 'VEV_4000': 300, 'VEV_4500': 300, 'VEV_5000': 300, 'VEV_5100': 300, 'VEV_5200': 300, 'VEV_5300': 300, 'VEV_5400': 300, 'VEV_5500': 300, 'VEV_6000': 300, 'VEV_6500': 300}
order = ['HYDROGEL_PACK', 'VELVETFRUIT_EXTRACT', 'VEV_4000', 'VEV_4500', 'VEV_5000', 'VEV_5100', 'VEV_5200', 'VEV_5300', 'VEV_5400', 'VEV_5500', 'VEV_6000', 'VEV_6500']
print(f"\n{'product':22s} {'lim':>4s} {'buys':>5s} {'sells':>5s} {'buyV':>6s} {'sellV':>6s} {'pkLong':>7s} {'pkShort':>7s} {'pk%':>6s} {'gross_buy':>11s} {'gross_sell':>11s} {'net':>10s}")
for sym in order:
    if sym not in per_prod:
        print(f'{sym:22s}  --- no trades ---')
        continue
    p = per_prod[sym]
    lim = LIMITS.get(sym, 0)
    pk_pct = max(p['peak_long'], -p['peak_short']) / lim * 100 if lim else 0
    net_cash = p['sell_notional'] - p['buy_notional']
    print(f"{sym:22s} {lim:>4d} {p['buys']:>5d} {p['sells']:>5d} {p['buy_vol']:>6d} {p['sell_vol']:>6d} {p['peak_long']:>+7d} {p['peak_short']:>+7d} {pk_pct:>5.0f}%  {p['buy_notional']:>11,.0f} {p['sell_notional']:>11,.0f} {net_cash:>+10,.0f}")
acts = js['activitiesLog'].strip().split('\n')[1:]
ix_keys = ['day', 'timestamp', 'product', 'bid_price_1', 'bid_volume_1', 'bid_price_2', 'bid_volume_2', 'bid_price_3', 'bid_volume_3', 'ask_price_1', 'ask_volume_1', 'ask_price_2', 'ask_volume_2', 'ask_price_3', 'ask_volume_3', 'mid_price', 'profit_and_loss']
mids = defaultdict(list)
last_pnl = {}
for line in acts:
    parts = line.split(';')
    if len(parts) < len(ix_keys):
        continue
    sym = parts[2]
    ts = int(parts[1])
    mid_str = parts[15]
    pnl_str = parts[16]
    if mid_str:
        mids[sym].append((ts, float(mid_str)))
    if pnl_str:
        last_pnl[sym] = float(pnl_str)
print('\n=== pnl alignment with directional risk ===')
print(f"{'product':22s} {'pnl':>9s} {'first_mid':>10s} {'last_mid':>10s} {'drift':>8s} {'pk_long':>7s} {'pk_short':>7s} {'dir_bet':>10s}")
for sym in order:
    if sym not in mids:
        continue
    seq = sorted(mids[sym])
    first_m = seq[0][1]
    last_m = seq[-1][1]
    drift = last_m - first_m
    p = per_prod.get(sym, {'peak_long': 0, 'peak_short': 0})
    bet = ''
    if p['peak_long'] > -p['peak_short']:
        bet = 'long-bias'
    elif -p['peak_short'] > p['peak_long']:
        bet = 'short-bias'
    pn = last_pnl.get(sym, 0)
    print(f"{sym:22s} {pn:>+9,.0f} {first_m:>10.1f} {last_m:>10.1f} {drift:>+8.1f} {p['peak_long']:>+7d} {p['peak_short']:>+7d}  {bet:>9s}")
print('\n=== TOTAL PnL drawdown trajectory (from graphLog) ===')
gl = js['graphLog'].strip().split('\n')[1:]
pts = []
for line in gl:
    a, b = line.split(';')
    pts.append((int(a), float(b)))
pts.sort()
ts_arr = [p[0] for p in pts]
pnl_arr = [p[1] for p in pts]
peak = 0.0
trough = 0.0
peak_t = 0
trough_t = 0
final = pnl_arr[-1]
for ts, p in pts:
    if p > peak:
        peak, peak_t = (p, ts)
    if p < trough:
        trough, trough_t = (p, ts)
print(f'  final: {final:+,.0f} @ ts={ts_arr[-1]:,}')
print(f'  peak:  {peak:+,.0f} @ ts={peak_t:,}')
print(f'  trough:{trough:+,.0f} @ ts={trough_t:,}')
print(f'  drawdown from peak: {peak - trough:+,.0f}')
print('\n  checkpoints (every 100k ticks):')
for chk in range(0, 1000001, 100000):
    near = min(pts, key=lambda x: abs(x[0] - chk))
    print(f'    ts={chk:>7,}  pnl≈{near[1]:>+10,.0f}  (sample @ ts={near[0]})')
print('\n=== ticks AT or NEAR position limit (>= 95% |pos|/lim) ===')
for sym in order:
    if sym not in per_prod:
        continue
    p = per_prod[sym]
    lim = LIMITS.get(sym, 0)
    if lim == 0:
        continue
    near_lim = sum((1 for _, pos in p['positions_over_time'] if abs(pos) >= 0.95 * lim))
    total_t = len(p['positions_over_time'])
    if total_t > 0:
        print(f'  {sym:22s}: {near_lim:5d} / {total_t:5d} trades happened with |pos| >= 95% of {lim}')
