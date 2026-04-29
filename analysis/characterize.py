import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from collections import Counter
from loader import load_all_prices, load_all_trades, split_product, best_quotes, total_depth, autocorr, ensure_plot_dir, PRODUCTS, R2_DAYS
ensure_plot_dir()
PLOT = os.path.join(os.path.dirname(__file__), 'plots')

def hdr(s):
    print('\n' + '=' * 64)
    print('  ' + s)
    print('=' * 64)

def stats(arr):
    a = np.asarray(arr, dtype=float)
    a = a[~np.isnan(a)]
    return {'n': len(a), 'mean': a.mean(), 'median': np.median(a), 'std': a.std(), 'min': a.min(), 'max': a.max(), 'p1': np.percentile(a, 1), 'p99': np.percentile(a, 99)}

def fmt_stats(s):
    return f"n={s['n']} mean={s['mean']:.2f} med={s['median']:.2f} std={s['std']:.3f} min={s['min']:.1f} max={s['max']:.1f} p1={s['p1']:.2f} p99={s['p99']:.2f}"

def per_product_per_day(prices, trades_by_day):
    summary = []
    for day in R2_DAYS:
        df = prices[day]
        for prod in PRODUCTS:
            sub = split_product(df, prod)
            sub = best_quotes(sub)
            mid = sub['mid_price'].values
            spread = sub['spread'].values
            ret = np.diff(mid)
            bv, av = total_depth(sub)
            tdf = trades_by_day[day]
            tsub = tdf[tdf['symbol'] == prod]
            row = {'day': day, 'product': prod, 'ticks': len(sub), 'mid_mean': float(np.nanmean(mid)), 'mid_med': float(np.nanmedian(mid)), 'mid_std': float(np.nanstd(mid)), 'mid_min': float(np.nanmin(mid)), 'mid_max': float(np.nanmax(mid)), 'mid_range': float(np.nanmax(mid) - np.nanmin(mid)), 'sp_mean': float(np.nanmean(spread)), 'sp_med': float(np.nanmedian(spread)), 'sp_p99': float(np.nanpercentile(spread, 99)), 'ret_mean': float(np.nanmean(ret)), 'ret_std': float(np.nanstd(ret)), 'ret_p1': float(np.nanpercentile(ret, 1)), 'ret_p99': float(np.nanpercentile(ret, 99)), 'rv': float(np.sqrt(np.nansum(ret * ret))), 'ac1': float(autocorr(ret, 1)), 'ac2': float(autocorr(ret, 2)), 'ac5': float(autocorr(ret, 5)), 'ac10': float(autocorr(ret, 10)), 'bv_mean': float(bv.mean()), 'av_mean': float(av.mean()), 'imb_mean': float(((bv - av) / (bv + av).replace(0, 1)).mean()), 'trades': len(tsub), 'trade_qty_med': float(tsub['quantity'].median()) if len(tsub) else 0.0, 'trade_qty_max': int(tsub['quantity'].max()) if len(tsub) else 0, 'trade_vol': int(tsub['quantity'].sum()) if len(tsub) else 0}
            summary.append(row)
    return summary

def plot_mid_overview(prices):
    fig, axes = plt.subplots(2, 3, figsize=(15, 6), sharex=False)
    for j, day in enumerate(R2_DAYS):
        df = prices[day]
        for i, prod in enumerate(PRODUCTS):
            sub = split_product(df, prod)
            ax = axes[i, j]
            ax.plot(sub['timestamp'], sub['mid_price'], lw=0.5)
            ax.set_title(f'{prod[:3]} day {day}')
            ax.set_xlabel('ts')
    plt.tight_layout()
    p = os.path.join(PLOT, 'mid_overview.png')
    plt.savefig(p, dpi=110)
    plt.close()
    return p

def plot_spread_hist(prices):
    fig, axes = plt.subplots(2, 3, figsize=(15, 6))
    for j, day in enumerate(R2_DAYS):
        df = prices[day]
        for i, prod in enumerate(PRODUCTS):
            sub = best_quotes(split_product(df, prod))
            sp = sub['spread'].dropna().astype(int)
            ax = axes[i, j]
            ax.hist(sp, bins=range(int(sp.min()), int(sp.max()) + 2), color='steelblue', edgecolor='k')
            ax.set_title(f'{prod[:3]} day {day} spread (med={sp.median():.0f})')
            ax.set_xlabel('spread')
    plt.tight_layout()
    p = os.path.join(PLOT, 'spread_hist.png')
    plt.savefig(p, dpi=110)
    plt.close()
    return p

def plot_returns_dist(prices):
    fig, axes = plt.subplots(2, 3, figsize=(15, 6))
    for j, day in enumerate(R2_DAYS):
        df = prices[day]
        for i, prod in enumerate(PRODUCTS):
            sub = split_product(df, prod)
            r = np.diff(sub['mid_price'].values)
            ax = axes[i, j]
            ax.hist(r, bins=80, color='salmon', edgecolor='k')
            ax.set_yscale('log')
            ax.set_title(f'{prod[:3]} day {day} ret (std={r.std():.3f})')
    plt.tight_layout()
    p = os.path.join(PLOT, 'returns_dist.png')
    plt.savefig(p, dpi=110)
    plt.close()
    return p

def plot_returns_acf(prices):
    fig, axes = plt.subplots(2, 3, figsize=(15, 6))
    lags = range(1, 51)
    for j, day in enumerate(R2_DAYS):
        df = prices[day]
        for i, prod in enumerate(PRODUCTS):
            sub = split_product(df, prod)
            r = np.diff(sub['mid_price'].values)
            ac = [autocorr(r, l) for l in lags]
            ax = axes[i, j]
            ax.bar(list(lags), ac, color='teal')
            ax.axhline(0, color='k', lw=0.4)
            ax.set_title(f'{prod[:3]} day {day} acf')
            ax.set_ylim(-0.5, 0.5)
    plt.tight_layout()
    p = os.path.join(PLOT, 'returns_acf.png')
    plt.savefig(p, dpi=110)
    plt.close()
    return p

def intraday_seasonality(prices):
    print('\n-- intraday bins (1k-tick chunks) --')
    out = {}
    for day in R2_DAYS:
        df = prices[day]
        for prod in PRODUCTS:
            sub = split_product(df, prod)
            sub = best_quotes(sub)
            sub['bin'] = sub['timestamp'] // 100000
            grp = sub.groupby('bin').agg(mid_mean=('mid_price', 'mean'), mid_std=('mid_price', 'std'), sp_mean=('spread', 'mean'))
            print(f'  {prod[:3]} d{day}')
            for b, r in grp.iterrows():
                print(f'    chunk {b}: mid_mean={r.mid_mean:.1f} mid_std={r.mid_std:.2f} sp_mean={r.sp_mean:.2f}')
            out[day, prod] = grp
    return out

def trade_flow(trades_by_day, prices):
    print('\n-- trade flow per day per product --')
    for day in R2_DAYS:
        tdf = trades_by_day[day]
        for prod in PRODUCTS:
            t = tdf[tdf['symbol'] == prod]
            if len(t) == 0:
                continue
            qs = stats(t['quantity'].values)
            mid_idx = split_product(prices[day], prod).set_index('timestamp')['mid_price']
            t = t.copy()
            t['mid'] = t['timestamp'].map(mid_idx)
            t['side'] = np.where(t['price'] > t['mid'], 'BUY', np.where(t['price'] < t['mid'], 'SELL', 'AT'))
            sc = t['side'].value_counts().to_dict()
            print(f'  {prod[:3]} d{day} n={len(t)} qty[{fmt_stats(qs)}] sides={sc}')

def main():
    hdr('r2 dataset characterize')
    prices = load_all_prices(2)
    trades = load_all_trades(2)
    rows = per_product_per_day(prices, trades)
    df = pd.DataFrame(rows)
    out_csv = os.path.join(os.path.dirname(__file__), 'r2_characterize.csv')
    df.to_csv(out_csv, index=False)
    print(f'\nsaved per-day-product summary -> {out_csv}')
    print('\n-- per-day per-product summary --')
    cols = ['day', 'product', 'ticks', 'mid_mean', 'mid_std', 'mid_range', 'sp_mean', 'sp_med', 'ret_std', 'ret_p1', 'ret_p99', 'ac1', 'ac5', 'bv_mean', 'av_mean', 'imb_mean', 'trades', 'trade_qty_med', 'trade_qty_max']
    print(df[cols].to_string(index=False))
    p1 = plot_mid_overview(prices)
    p2 = plot_spread_hist(prices)
    p3 = plot_returns_dist(prices)
    p4 = plot_returns_acf(prices)
    print(f'\nplots: {p1} {p2} {p3} {p4}')
    intraday_seasonality(prices)
    trade_flow(trades, prices)
    print('\n-- spread regime breaks (consecutive ticks with sp >= 6) --')
    for day in R2_DAYS:
        for prod in PRODUCTS:
            sub = best_quotes(split_product(prices[day], prod))
            sp = sub['spread'].fillna(0).values
            wide = sp >= 6
            runs = []
            cur = 0
            for w in wide:
                if w:
                    cur += 1
                else:
                    if cur > 0:
                        runs.append(cur)
                    cur = 0
            if cur > 0:
                runs.append(cur)
            print(f'  {prod[:3]} d{day}: wide_runs={len(runs)} mean_len={(np.mean(runs) if runs else 0):.1f} max={(max(runs) if runs else 0)}')
if __name__ == '__main__':
    main()
