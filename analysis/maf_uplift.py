import os
import sys
import numpy as np
import pandas as pd
ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, ROOT)
import builtins
_orig_print = builtins.print

def _silent(*a, **k):
    if a and isinstance(a[0], str) and a[0].startswith('END_OF_ROUND'):
        return
    _orig_print(*a, **k)
from trader import Trader, lim
from datamodel import OrderDepth, TradingState
import trader as trader_mod
trader_mod.print = _silent
from loader import load_all_prices, split_product, R2_DAYS, R2_DIR

def hdr(s):
    print('\n' + '=' * 64)
    print('  ' + s)
    print('=' * 64)

def build_order_depth(row):
    od = OrderDepth()
    for k in ['bid_price_1', 'bid_price_2', 'bid_price_3']:
        i = k[-1]
        p = row[k]
        v = row['bid_volume_' + i]
        if pd.notna(p) and pd.notna(v) and (v > 0):
            od.buy_orders[int(p)] = int(v)
    for k in ['ask_price_1', 'ask_price_2', 'ask_price_3']:
        i = k[-1]
        p = row[k]
        v = row['ask_volume_' + i]
        if pd.notna(p) and pd.notna(v) and (v > 0):
            od.sell_orders[int(p)] = -int(v)
    return od

def scale_depth(od, factor, rng):
    new = OrderDepth()
    for p, v in od.buy_orders.items():
        nv = max(1, int(round(v * factor))) if factor > 0 else 0
        if rng is not None and factor < 1.0:
            keep = rng.binomial(v, factor)
            if keep > 0:
                new.buy_orders[p] = int(keep)
        elif factor != 1.0:
            extra = max(0, int(round(v * (factor - 1.0))))
            new.buy_orders[p] = v + extra
        else:
            new.buy_orders[p] = v
    for p, v in od.sell_orders.items():
        av = -v
        if rng is not None and factor < 1.0:
            keep = rng.binomial(av, factor)
            if keep > 0:
                new.sell_orders[p] = -int(keep)
        elif factor != 1.0:
            extra = max(0, int(round(av * (factor - 1.0))))
            new.sell_orders[p] = -(av + extra)
        else:
            new.sell_orders[p] = v
    return new

def simulate_day(prices_df, trader, factor=1.0, seed=42):
    rng = np.random.default_rng(seed) if factor < 1.0 else None
    timestamps = sorted(prices_df['timestamp'].unique())
    pos = {'ASH_COATED_OSMIUM': 0, 'INTARIAN_PEPPER_ROOT': 0}
    realized = {'ASH_COATED_OSMIUM': 0.0, 'INTARIAN_PEPPER_ROOT': 0.0}
    last_mid = {'ASH_COATED_OSMIUM': 10000.0, 'INTARIAN_PEPPER_ROOT': 12000.0}
    trader_data = ''
    pnl_curve = []
    fill_stats = {'ASH_COATED_OSMIUM': {'n': 0, 'vol': 0}, 'INTARIAN_PEPPER_ROOT': {'n': 0, 'vol': 0}}
    for ts in timestamps:
        rows = prices_df[prices_df['timestamp'] == ts]
        ods = {}
        for _, r in rows.iterrows():
            prod = r['product']
            if pd.isna(r['bid_price_1']) and pd.isna(r['ask_price_1']):
                continue
            base = build_order_depth(r)
            if factor != 1.0:
                base = scale_depth(base, factor, rng)
            ods[prod] = base
            if pd.notna(r['mid_price']) and r['mid_price'] > 0:
                last_mid[prod] = float(r['mid_price'])
        state = TradingState(traderData=trader_data, timestamp=int(ts), listings={}, order_depths=ods, own_trades={}, market_trades={}, position=dict(pos), observations=None)
        try:
            orders, _, trader_data = trader.run(state)
        except Exception as e:
            print(f'  trader err ts={ts}: {e}')
            continue
        for prod, oo in orders.items():
            od = ods.get(prod)
            if not od:
                continue
            for order in oo:
                qty = order.quantity
                px = order.price
                if qty > 0:
                    remaining = qty
                    for ap in sorted(od.sell_orders):
                        if remaining <= 0 or ap > px:
                            break
                        avail = -od.sell_orders[ap]
                        take = min(avail, remaining)
                        if take <= 0:
                            continue
                        new_pos = pos[prod] + take
                        if new_pos > lim[prod]:
                            take = lim[prod] - pos[prod]
                            if take <= 0:
                                break
                        pos[prod] += take
                        realized[prod] -= ap * take
                        fill_stats[prod]['n'] += 1
                        fill_stats[prod]['vol'] += take
                        remaining -= take
                        new_av = avail - take
                        if new_av <= 0:
                            del od.sell_orders[ap]
                        else:
                            od.sell_orders[ap] = -new_av
                elif qty < 0:
                    remaining = -qty
                    for bp in sorted(od.buy_orders, reverse=True):
                        if remaining <= 0 or bp < px:
                            break
                        avail = od.buy_orders[bp]
                        take = min(avail, remaining)
                        if take <= 0:
                            continue
                        new_pos = pos[prod] - take
                        if new_pos < -lim[prod]:
                            take = pos[prod] + lim[prod]
                            if take <= 0:
                                break
                        pos[prod] -= take
                        realized[prod] += bp * take
                        fill_stats[prod]['n'] += 1
                        fill_stats[prod]['vol'] += take
                        remaining -= take
                        new_bv = avail - take
                        if new_bv <= 0:
                            del od.buy_orders[bp]
                        else:
                            od.buy_orders[bp] = new_bv
        pnl_curve.append((ts, realized['ASH_COATED_OSMIUM'] + pos['ASH_COATED_OSMIUM'] * last_mid['ASH_COATED_OSMIUM'], realized['INTARIAN_PEPPER_ROOT'] + pos['INTARIAN_PEPPER_ROOT'] * last_mid['INTARIAN_PEPPER_ROOT']))
    final_aco = realized['ASH_COATED_OSMIUM'] + pos['ASH_COATED_OSMIUM'] * last_mid['ASH_COATED_OSMIUM']
    final_ipr = realized['INTARIAN_PEPPER_ROOT'] + pos['INTARIAN_PEPPER_ROOT'] * last_mid['INTARIAN_PEPPER_ROOT']
    return {'aco': final_aco, 'ipr': final_ipr, 'total': final_aco + final_ipr, 'pos': dict(pos), 'fills': fill_stats, 'pnl_curve': pnl_curve}

def analytic_take_uplift(prices_df, fv_aco=10000):
    aco = prices_df[prices_df['product'] == 'ASH_COATED_OSMIUM']
    aco = aco[(aco['mid_price'] > 0) & aco['bid_price_1'].notna() & aco['ask_price_1'].notna()]
    take_pnl_at = lambda factor: 0.0
    rows = []
    for factor in [0.8, 1.0, 1.25]:
        gross = 0.0
        capped = 0
        pos = 0
        cap = 80
        for _, r in aco.iterrows():
            local_pos = pos
            for i in [1, 2, 3]:
                ap = r[f'ask_price_{i}']
                av = r[f'ask_volume_{i}']
                if pd.notna(ap) and pd.notna(av) and (ap < fv_aco):
                    vol = max(0, int(round(av * factor)))
                    edge = fv_aco - ap
                    take = vol
                    if take > 0:
                        gross += edge * take
            for i in [1, 2, 3]:
                bp = r[f'bid_price_{i}']
                bv = r[f'bid_volume_{i}']
                if pd.notna(bp) and pd.notna(bv) and (bp > fv_aco):
                    vol = max(0, int(round(bv * factor)))
                    edge = bp - fv_aco
                    take = vol
                    if take > 0:
                        gross += edge * take
        rows.append((factor, gross))
    return rows

def main():
    hdr('maf uplift simulation (multi-seed)')
    prices = load_all_prices(2)
    scenarios = [('80pct_no_maf', 0.8), ('100pct_baseline', 1.0), ('125pct_maf', 1.25)]
    rows = []
    for day in R2_DAYS:
        print(f'\n  -- day {day} --')
        df = prices[day]
        for seed in [42, 7, 99]:
            for label, factor in scenarios:
                t = Trader()
                res = simulate_day(df, t, factor=factor, seed=seed)
                print(f"    seed={seed:>3d} {label:18s} aco={res['aco']:9.0f}  ipr={res['ipr']:9.0f}  total={res['total']:9.0f}  fills_a={res['fills']['ASH_COATED_OSMIUM']['vol']:>4d} fills_i={res['fills']['INTARIAN_PEPPER_ROOT']['vol']:>4d}")
                rows.append({'day': day, 'seed': seed, 'scenario': label, 'factor': factor, 'aco': res['aco'], 'ipr': res['ipr'], 'total': res['total'], 'fills_aco': res['fills']['ASH_COATED_OSMIUM']['vol'], 'fills_ipr': res['fills']['INTARIAN_PEPPER_ROOT']['vol']})
    df_out = pd.DataFrame(rows)
    df_out.to_csv(os.path.join(os.path.dirname(__file__), 'maf_uplift.csv'), index=False)
    hdr('per-day uplift (mean over seeds)')
    g = df_out.groupby(['day', 'scenario']).agg(aco=('aco', 'mean'), ipr=('ipr', 'mean'), total=('total', 'mean'), fills_aco=('fills_aco', 'mean'), fills_ipr=('fills_ipr', 'mean')).reset_index()
    pa = g.pivot(index='day', columns='scenario', values='aco')
    pi = g.pivot(index='day', columns='scenario', values='ipr')
    pt = g.pivot(index='day', columns='scenario', values='total')
    print('  aco:')
    print(pa.round(0).to_string())
    print('\n  ipr:')
    print(pi.round(0).to_string())
    print('\n  total:')
    print(pt.round(0).to_string())
    pa['aco_uplift_maf_vs_80'] = pa['125pct_maf'] - pa['80pct_no_maf']
    pi['ipr_uplift_maf_vs_80'] = pi['125pct_maf'] - pi['80pct_no_maf']
    pt['tot_uplift_maf_vs_80'] = pt['125pct_maf'] - pt['80pct_no_maf']
    hdr('uplift summary (maf 125% - no_maf 80%, mean over seeds)')
    print(f"  aco uplift / day: {pa['aco_uplift_maf_vs_80'].mean():+.0f} (per day: {list(pa['aco_uplift_maf_vs_80'].round(0).values)})")
    print(f"  ipr uplift / day: {pi['ipr_uplift_maf_vs_80'].mean():+.0f} (per day: {list(pi['ipr_uplift_maf_vs_80'].round(0).values)})")
    print(f"  tot uplift / day: {pt['tot_uplift_maf_vs_80'].mean():+.0f} (per day: {list(pt['tot_uplift_maf_vs_80'].round(0).values)})")
    print(f'\n  note: this sim under-counts passive make-side fills; r2 round runs ONE day only.')
    hdr('analytical aco take uplift (upper-bound, no pos cap effect)')
    aco_rows_all = []
    for day in R2_DAYS:
        ar = analytic_take_uplift(prices[day])
        d = dict(ar)
        print(f'  day {day}: 80pct={d[0.8]:>10.0f}  100pct={d[1.0]:>10.0f}  125pct={d[1.25]:>10.0f}  uplift_125_vs_80={d[1.25] - d[0.8]:>8.0f}')
        aco_rows_all.append(d)
    mean_aco_anlyt = np.mean([d[1.25] - d[0.8] for d in aco_rows_all])
    print(f'  mean analytical aco take uplift / day: {mean_aco_anlyt:.0f}')
    print(f'  note: analytic ignores 80-unit position cap (cap likely halves true uplift)')
    hdr('bid recommendation (round 2 = single live day)')
    sim_uplift = pt['tot_uplift_maf_vs_80'].mean()
    realistic_per_day = max(sim_uplift, mean_aco_anlyt * 0.4)
    print(f'  sim uplift estimate (biased low):    {sim_uplift:+.0f}/day')
    print(f'  analytic aco take uplift (gross):    {mean_aco_anlyt:+.0f}/day')
    print(f'  analytic w/ 60% pos-cap haircut:     {mean_aco_anlyt * 0.4:+.0f}/day')
    print(f'  --> single-day uplift estimate:      {realistic_per_day:+.0f}')
    print(f'\n  bid candidates (live = ONE day, ratio applied to ROUND profit):')
    for frac in [0.05, 0.1, 0.2, 0.25, 0.33, 0.5, 0.75]:
        bid = int(round(realistic_per_day * frac))
        net_if_won = int(round(realistic_per_day - bid))
        print(f'    bid={bid:6d} ({frac * 100:>4.0f}% of uplift): net_if_won={net_if_won:+6d}')
if __name__ == '__main__':
    main()
