import json
import sys
from collections import Counter, defaultdict

def load(path):
    with open(path) as f:
        return json.load(f)

def parse_activities(raw):
    lines = raw.strip().split('\n')
    header = lines[0].split(';')
    rows = []
    for l in lines[1:]:
        parts = l.split(';')
        if len(parts) < 17:
            continue
        rows.append({'day': int(parts[0]), 'ts': int(parts[1]), 'product': parts[2], 'bp1': float(parts[3]) if parts[3] else None, 'bv1': int(parts[4]) if parts[4] else 0, 'bp2': float(parts[5]) if parts[5] else None, 'bv2': int(parts[6]) if parts[6] else 0, 'bp3': float(parts[7]) if parts[7] else None, 'bv3': int(parts[8]) if parts[8] else 0, 'ap1': float(parts[9]) if parts[9] else None, 'av1': int(parts[10]) if parts[10] else 0, 'ap2': float(parts[11]) if parts[11] else None, 'av2': int(parts[12]) if parts[12] else 0, 'ap3': float(parts[13]) if parts[13] else None, 'av3': int(parts[14]) if parts[14] else 0, 'mid': float(parts[15]) if parts[15] else None, 'pnl': float(parts[16]) if parts[16] else 0.0})
    return rows

def header(title):
    print(f"\n{'=' * 60}")
    print(f'  {title}')
    print(f"{'=' * 60}")

def run(path):
    data = load(path)
    tr = data.get('tradeHistory', [])
    al_raw = data.get('activitiesLog', '')
    header('TRADE SUMMARY')
    products = set((t['symbol'] for t in tr))
    for sym in sorted(products):
        sym_tr = [t for t in tr if t['symbol'] == sym]
        buys = [t for t in sym_tr if t['buyer'] == 'SUBMISSION']
        sells = [t for t in sym_tr if t['seller'] == 'SUBMISSION']
        buy_qty = sum((t['quantity'] for t in buys))
        sell_qty = sum((t['quantity'] for t in sells))
        buy_val = sum((t['price'] * t['quantity'] for t in buys))
        sell_val = sum((t['price'] * t['quantity'] for t in sells))
        avg_buy = buy_val / buy_qty if buy_qty else 0
        avg_sell = sell_val / sell_qty if sell_qty else 0
        net_pos = buy_qty - sell_qty
        raw_pnl = sell_val - buy_val
        print(f'\n  [{sym}]')
        print(f'  trades: {len(buys)}b + {len(sells)}s = {len(buys) + len(sells)}')
        print(f'  volume: {buy_qty}b + {sell_qty}s = {buy_qty + sell_qty} total')
        print(f'  avg buy: {avg_buy:.2f}  avg sell: {avg_sell:.2f}')
        print(f'  realized spread: {avg_sell - avg_buy:.2f}')
        print(f'  raw pnl (no m2m): {raw_pnl:.0f}')
        print(f'  ending position: {net_pos}')
    header('ZERO-EDGE WASTE (trades at exact fv)')
    aco_fv = 10000
    zero_takes = [t for t in tr if t['symbol'] == 'ASH_COATED_OSMIUM' and t['price'] == aco_fv and (t['buyer'] == 'SUBMISSION' or t['seller'] == 'SUBMISSION')]
    zero_qty = sum((t['quantity'] for t in zero_takes))
    print(f'  ACO trades at exactly {aco_fv}: {len(zero_takes)} trades, {zero_qty} units')
    print(f'  => wasted position capacity for 0 profit')
    header('INVENTORY TIMELINE')
    for sym in sorted(products):
        sym_tr = sorted([t for t in tr if t['symbol'] == sym], key=lambda x: x['timestamp'])
        pos = 0
        max_pos = 0
        time_at_high = 0
        prev_ts = sym_tr[0]['timestamp'] if sym_tr else 0
        high_thresh = 60
        for t in sym_tr:
            dt = t['timestamp'] - prev_ts
            if abs(pos) >= high_thresh:
                time_at_high += dt
            if t['buyer'] == 'SUBMISSION':
                pos += t['quantity']
            elif t['seller'] == 'SUBMISSION':
                pos -= t['quantity']
            max_pos = max(max_pos, abs(pos))
            prev_ts = t['timestamp']
        total_span = sym_tr[-1]['timestamp'] - sym_tr[0]['timestamp'] if len(sym_tr) > 1 else 1
        pct = time_at_high / total_span * 100 if total_span else 0
        print(f'\n  [{sym}]')
        print(f'  peak |pos|: {max_pos}')
        print(f'  time at |pos|>={high_thresh}: {pct:.0f}% of session')
        print(f'  final pos: {pos}')
        if abs(pos) >= 60:
            print(f'  !! POSITION STUCK - bot capped out, cannot trade freely')
    header('SPREAD DISTRIBUTION')
    if al_raw:
        activities = parse_activities(al_raw)
        for sym in sorted(products):
            sym_acts = [a for a in activities if a['product'] == sym]
            spreads = []
            for a in sym_acts:
                if a['bp1'] is not None and a['ap1'] is not None:
                    spreads.append(int(a['ap1'] - a['bp1']))
            if not spreads:
                continue
            sc = Counter(spreads)
            avg_sp = sum(spreads) / len(spreads)
            print(f'\n  [{sym}] avg={avg_sp:.1f}')
            for s in sorted(sc):
                bar = '#' * int(sc[s] / len(spreads) * 50)
                print(f'    sp={s:2d}: {sc[s]:4d} ({sc[s] / len(spreads) * 100:5.1f}%) {bar}')
    header('PNL TRAJECTORY (server reported)')
    if al_raw:
        activities = parse_activities(al_raw)
        for sym in sorted(products):
            sym_acts = [a for a in activities if a['product'] == sym]
            print(f'\n  [{sym}]')
            buckets = range(0, 100001, 10000)
            for b in buckets:
                chunk = [a['pnl'] for a in sym_acts if a['ts'] <= b]
                if chunk:
                    print(f'    ts<={b:6d}: {chunk[-1]:8.1f}')
    header('EDGE ANALYSIS PER TRADE')
    for sym in sorted(products):
        sym_tr = [t for t in tr if t['symbol'] == sym and (t['buyer'] == 'SUBMISSION' or t['seller'] == 'SUBMISSION')]
        if not sym_tr:
            continue
        edges = []
        for t in sym_tr:
            if sym == 'ASH_COATED_OSMIUM':
                fv = 10000
                if t['buyer'] == 'SUBMISSION':
                    edge = fv - t['price']
                else:
                    edge = t['price'] - fv
                edges.append(edge)
        if not edges:
            continue
        print(f'\n  [{sym}]')
        edge_counter = Counter([int(e) for e in edges])
        for e in sorted(edge_counter):
            cnt = edge_counter[e]
            print(f'    edge={e:+d}: {cnt} trades')
        avg_edge = sum(edges) / len(edges)
        print(f'    avg edge per trade: {avg_edge:.2f}')
    header('DONE')
if __name__ == '__main__':
    path = sys.argv[1] if len(sys.argv) > 1 else 'LOGS/122614/122614.log'
    run(path)
