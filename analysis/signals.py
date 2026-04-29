import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from collections import defaultdict
from loader import load_all_prices, load_all_trades, split_product, best_quotes, total_depth, wallmid, autocorr, ensure_plot_dir, PRODUCTS, R2_DAYS
PLOT = ensure_plot_dir()

def hdr(s):
    print('\n' + '=' * 64)
    print('  ' + s)
    print('=' * 64)

def wallmid_vs_mid(prices):
    hdr('wallmid vs mid lead-lag')
    for prod in PRODUCTS:
        for day in R2_DAYS:
            sub = best_quotes(split_product(prices[day], prod))
            mid = sub['mid_price'].values
            wm = wallmid(sub)
            ret_mid = np.diff(mid)
            ret_wm = np.diff(wm)
            div = wm[:-1] - mid[:-1]
            xc = []
            for k in range(0, 6):
                if k == 0:
                    c = np.corrcoef(div, ret_mid)[0, 1]
                else:
                    c = np.corrcoef(div[:-k], ret_mid[k:])[0, 1] if k < len(div) else np.nan
                xc.append(c)
            print(f'  {prod[:3]} d{day}: corr(wm-mid -> next mid_ret) k=0..5: ' + ' '.join((f'{c:+.3f}' for c in xc)))

def book_imbalance_signal(prices):
    hdr('book imbalance vs next-tick return')
    for prod in PRODUCTS:
        for day in R2_DAYS:
            sub = best_quotes(split_product(prices[day], prod))
            bv1 = sub['bid_volume_1'].fillna(0).values
            av1 = sub['ask_volume_1'].fillna(0).values
            mid = sub['mid_price'].values
            ret = np.diff(mid)
            imb = (bv1[:-1] - av1[:-1]) / np.maximum(bv1[:-1] + av1[:-1], 1)
            buckets = defaultdict(list)
            for i in range(len(imb)):
                b = round(imb[i] * 5) / 5
                buckets[b].append(ret[i])
            print(f'  {prod[:3]} d{day}:')
            for b in sorted(buckets):
                rs = buckets[b]
                if len(rs) >= 50:
                    print(f'    imb={b:+.1f} n={len(rs):5d} avg_next_ret={np.mean(rs):+.3f} std={np.std(rs):.2f}')

def trade_sign_autocorr(prices, trades):
    hdr('trade sign autocorrelation')
    for prod in PRODUCTS:
        for day in R2_DAYS:
            sub = best_quotes(split_product(prices[day], prod))
            mid_at = sub.set_index('timestamp')['mid_price']
            t = trades[day][trades[day]['symbol'] == prod].copy()
            t['mid'] = t['timestamp'].map(mid_at)
            t = t.dropna(subset=['mid'])
            sgn = np.sign(t['price'].values - t['mid'].values)
            sgn = sgn[sgn != 0]
            if len(sgn) > 5:
                ac1 = autocorr(sgn, 1)
                ac2 = autocorr(sgn, 2)
                ac5 = autocorr(sgn, 5)
                print(f'  {prod[:3]} d{day}: n={len(sgn)} ac1={ac1:+.3f} ac2={ac2:+.3f} ac5={ac5:+.3f}')

def aco_spread_regime_meanrev(prices):
    hdr('aco spread regime -> reversion magnitude')
    for day in R2_DAYS:
        sub = best_quotes(split_product(prices[day], 'ASH_COATED_OSMIUM'))
        mid = sub['mid_price'].values
        sp = sub['spread'].fillna(0).values
        dev = mid - 10000.0
        next_dev = np.roll(dev, -1)
        rev = dev[:-1] - next_dev[:-1]
        sp_buckets = defaultdict(list)
        for i in range(len(sp) - 1):
            sp_buckets[int(sp[i])].append((dev[i], rev[i]))
        print(f'\n  d{day}')
        for s in sorted(sp_buckets):
            arr = sp_buckets[s]
            if len(arr) < 30:
                continue
            devs = np.array([a[0] for a in arr])
            revs = np.array([a[1] for a in arr])
            corr = np.corrcoef(devs, revs)[0, 1] if devs.std() > 0 else np.nan
            print(f'    sp={s:2d} n={len(arr):5d}  mean|dev|={np.mean(np.abs(devs)):.2f}  mean_rev_per_tick={np.mean(revs):+.3f}  corr(dev,rev)={corr:+.3f}')

def eod_pattern(prices):
    hdr('end-of-day window analysis')
    for prod in PRODUCTS:
        for day in R2_DAYS:
            sub = best_quotes(split_product(prices[day], prod))
            for cut in [990000, 995000, 998000, 999000, 999500, 999800]:
                tail = sub[sub['timestamp'] >= cut]
                if len(tail) == 0:
                    continue
                mid = tail['mid_price'].values
                last_mid = mid[-1]
                bvm = tail['bid_volume_1'].mean()
                avm = tail['ask_volume_1'].mean()
                spm = tail['spread'].mean()
                print(f'  {prod[:3]} d{day} ts>={cut}: n={len(tail)}  last_mid={last_mid:.1f}  l1_bv={bvm:.1f} l1_av={avm:.1f} sp={spm:.1f}')
            break

def empty_book_freq(prices):
    hdr('empty book frequency (raw, before drop)')
    from loader import R2_DIR
    for day in R2_DAYS:
        df = pd.read_csv(os.path.join(R2_DIR, f'prices_round_2_day_{day}.csv'), sep=';')
        for prod in PRODUCTS:
            sub = df[df['product'] == prod]
            ne = sub[sub['mid_price'] == 0]
            tss = ne['timestamp'].values
            print(f'  {prod[:3]} d{day}: empty_book n={len(ne)}  example_ts={list(tss[:6])}')

def main():
    prices = load_all_prices(2)
    trades = load_all_trades(2)
    wallmid_vs_mid(prices)
    book_imbalance_signal(prices)
    trade_sign_autocorr(prices, trades)
    aco_spread_regime_meanrev(prices)
    eod_pattern(prices)
    empty_book_freq(prices)
if __name__ == '__main__':
    main()
