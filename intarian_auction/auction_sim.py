import json

def run_auction(bids, asks, our_order=None):
    all_bids = []
    all_asks = []
    for b in bids:
        all_bids.append({'price': b['price'], 'vol': b['vol'], 'is_us': False})
    for a in asks:
        all_asks.append({'price': a['price'], 'vol': a['vol'], 'is_us': False})
    if our_order:
        if our_order['side'] == 'BUY':
            all_bids.append({'price': our_order['price'], 'vol': our_order['vol'], 'is_us': True})
        else:
            all_asks.append({'price': our_order['price'], 'vol': our_order['vol'], 'is_us': True})
    prices = set()
    for b in all_bids:
        prices.add(b['price'])
    for a in all_asks:
        prices.add(a['price'])
    prices = sorted(list(prices))
    best_p = None
    max_vol = -1
    for p in prices:
        demand = sum((b['vol'] for b in all_bids if b['price'] >= p))
        supply = sum((a['vol'] for a in all_asks if a['price'] <= p))
        vol_matched = min(demand, supply)
        if vol_matched > max_vol:
            max_vol = vol_matched
            best_p = p
        elif vol_matched == max_vol:
            if best_p is None or p > best_p:
                best_p = p
    clearing_price = best_p
    our_filled = 0
    if our_order and our_order['side'] == 'BUY':
        if our_order['price'] > clearing_price:
            our_filled = our_order['vol']
        elif our_order['price'] == clearing_price:
            ahead_demand = sum((b['vol'] for b in all_bids if b['price'] > clearing_price))
            ahead_demand += sum((b['vol'] for b in all_bids if b['price'] == clearing_price and (not b['is_us'])))
            total_supply = sum((a['vol'] for a in all_asks if a['price'] <= clearing_price))
            remaining_supply = max(0, total_supply - ahead_demand)
            our_filled = min(our_order['vol'], remaining_supply)
    elif our_order and our_order['side'] == 'SELL':
        if our_order['price'] < clearing_price:
            our_filled = our_order['vol']
        elif our_order['price'] == clearing_price:
            ahead_supply = sum((a['vol'] for a in all_asks if a['price'] < clearing_price))
            ahead_supply += sum((a['vol'] for a in all_asks if a['price'] == clearing_price and (not a['is_us'])))
            total_demand = sum((b['vol'] for b in all_bids if b['price'] >= clearing_price))
            remaining_demand = max(0, total_demand - ahead_supply)
            our_filled = min(our_order['vol'], remaining_demand)
    return (clearing_price, our_filled)

def search_optimal(asset, fv, fee, max_vol, bids, asks):
    best_profit = -float('inf')
    best_order = None
    best_cp = None
    best_our_fill = None
    target_vols = set([max_vol])
    for i in range(1, 1000):
        target_vols.add(i)
    for i in range(1, max_vol // 1000 + 1):
        target_vols.add(i * 1000)
    for i in range(1, max_vol // 1000 + 1):
        target_vols.add(i * 1000 - 1)
    for i in range(1, max_vol // 1000 + 1):
        target_vols.add(i * 1000 + 1)
    for p in range(0, 50):
        for v in sorted(list(target_vols)):
            if v > max_vol:
                continue
            cp, filled = run_auction(bids, asks, {'side': 'BUY', 'price': p, 'vol': v})
            profit = filled * (fv - cp - fee)
            if profit > best_profit:
                best_profit = profit
                best_order = f'BUY {v} @ {p}'
                best_cp = cp
                best_our_fill = filled
            cp, filled = run_auction(bids, asks, {'side': 'SELL', 'price': p, 'vol': v})
            profit = filled * (cp - fv - fee)
            if profit > best_profit:
                best_profit = profit
                best_order = f'SELL {v} @ {p}'
                best_cp = cp
                best_our_fill = filled
    print(f'Optimal for {asset}:')
    print(f'Order: {best_order}')
    print(f'Clearing Price: {best_cp}')
    print(f'Filled Vol: {best_our_fill}')
    print(f'Profit: {best_profit}')
    print()
flax_bids = [{'price': 30, 'vol': 30000}, {'price': 29, 'vol': 5000}, {'price': 28, 'vol': 12000}, {'price': 27, 'vol': 28000}]
flax_asks = [{'price': 28, 'vol': 40000}, {'price': 31, 'vol': 20000}, {'price': 32, 'vol': 20000}, {'price': 33, 'vol': 30000}]
search_optimal('DRYLAND FLAX', 30, 0, 50000, flax_bids, flax_asks)
mush_bids = [{'price': 20, 'vol': 43000}, {'price': 19, 'vol': 17000}, {'price': 18, 'vol': 6000}, {'price': 17, 'vol': 5000}, {'price': 16, 'vol': 10000}, {'price': 15, 'vol': 5000}, {'price': 14, 'vol': 10000}, {'price': 13, 'vol': 7000}]
mush_asks = [{'price': 12, 'vol': 20000}, {'price': 13, 'vol': 25000}, {'price': 14, 'vol': 35000}, {'price': 15, 'vol': 6000}, {'price': 16, 'vol': 5000}, {'price': 18, 'vol': 10000}, {'price': 19, 'vol': 12000}]
search_optimal('EMBER MUSHROOM', 20, 0.1, 75000, mush_bids, mush_asks)
