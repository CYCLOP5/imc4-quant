import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from loader import load_all_prices, split_product, best_quotes, total_depth, autocorr, ensure_plot_dir, PRODUCTS, R1_DAYS, R2_DAYS
PLOT = ensure_plot_dir()

def hdr(s):
    print('\n' + '=' * 64)
    print('  ' + s)
    print('=' * 64)

def per_day_summary(prices, days, label):
    rows = []
    for day in days:
        df = prices[day]
        for prod in PRODUCTS:
            sub = best_quotes(split_product(df, prod))
            mid = sub['mid_price'].values
            sp = sub['spread'].values
            ret = np.diff(mid)
            bv, av = total_depth(sub)
            rows.append({'rnd': label, 'day': day, 'prod': prod[:3], 'mid_mean': mid.mean(), 'mid_std': mid.std(), 'mid_min': mid.min(), 'mid_max': mid.max(), 'mid_drift': mid[-1] - mid[0], 'sp_med': float(np.median(sp)), 'sp_mean': float(sp.mean()), 'ret_std': ret.std(), 'ret_p99': float(np.percentile(np.abs(ret), 99)), 'ac1': autocorr(ret, 1), 'bv_mean': float(bv.mean()), 'av_mean': float(av.mean()), 'l1_bv': sub['bid_volume_1'].mean(), 'l1_av': sub['ask_volume_1'].mean()})
    return pd.DataFrame(rows)

def main():
    hdr('compare r1 vs r2')
    r1 = load_all_prices(1)
    r2 = load_all_prices(2)
    df1 = per_day_summary(r1, R1_DAYS, 'r1')
    df2 = per_day_summary(r2, R2_DAYS, 'r2')
    full = pd.concat([df1, df2]).reset_index(drop=True)
    out_csv = os.path.join(os.path.dirname(__file__), 'r1_vs_r2.csv')
    full.to_csv(out_csv, index=False)
    print(f'\nsaved -> {out_csv}\n')
    print(full.to_string(index=False))
    hdr('aggregated by round x product')
    g = full.groupby(['rnd', 'prod']).agg({'mid_mean': 'mean', 'mid_std': 'mean', 'sp_med': 'mean', 'sp_mean': 'mean', 'ret_std': 'mean', 'ac1': 'mean', 'bv_mean': 'mean', 'av_mean': 'mean', 'l1_bv': 'mean', 'l1_av': 'mean'}).round(3)
    print(g.to_string())
    hdr('deltas r2 vs r1 (per product, mean across days)')
    for prod in ['ASH', 'INT']:
        a = g.loc['r1', prod]
        b = g.loc['r2', prod]
        print(f'\n  [{prod}]')
        for col in ['mid_std', 'sp_med', 'sp_mean', 'ret_std', 'ac1', 'bv_mean', 'av_mean', 'l1_bv', 'l1_av']:
            d = b[col] - a[col]
            r = b[col] / a[col] if a[col] != 0 else float('inf')
            print(f'    {col:10s}: r1={a[col]:8.3f}  r2={b[col]:8.3f}  d={d:+8.3f}  r={r:5.3f}x')
    hdr('aco anchor check')
    for label, prices, days in [('r1', r1, R1_DAYS), ('r2', r2, R2_DAYS)]:
        for day in days:
            sub = best_quotes(split_product(prices[day], 'ASH_COATED_OSMIUM'))
            m = sub['mid_price'].values
            within2 = (np.abs(m - 10000) <= 2).mean() * 100
            within5 = (np.abs(m - 10000) <= 5).mean() * 100
            within10 = (np.abs(m - 10000) <= 10).mean() * 100
            print(f'  {label} d{day}: mean={m.mean():.2f}  within2={within2:.1f}%  within5={within5:.1f}%  within10={within10:.1f}%')
    hdr('ipr drift profile')
    for label, prices, days in [('r1', r1, R1_DAYS), ('r2', r2, R2_DAYS)]:
        for day in days:
            sub = best_quotes(split_product(prices[day], 'INTARIAN_PEPPER_ROOT'))
            m = sub['mid_price'].values
            ts = sub['timestamp'].values
            slope = np.polyfit(ts, m, 1)[0]
            log_slope = np.polyfit(ts, np.log(m), 1)[0]
            print(f'  {label} d{day}: start={m[0]:.0f}  end={m[-1]:.0f}  drift={m[-1] - m[0]:+.0f}  px/tick={slope * 1000000.0:+.3f}  geom_per_tick={log_slope * 1000000.0:+.5f}')
    fig, axes = plt.subplots(2, 2, figsize=(14, 7))
    for i, prod in enumerate(PRODUCTS):
        ax = axes[i, 0]
        for label, prices, days in [('r1', r1, R1_DAYS), ('r2', r2, R2_DAYS)]:
            sps = []
            for day in days:
                sub = best_quotes(split_product(prices[day], prod))
                sps.extend(sub['spread'].dropna().values)
            ax.hist(sps, bins=range(0, 30), alpha=0.55, label=label, edgecolor='k')
        ax.set_title(f'{prod[:3]} spread r1 vs r2')
        ax.legend()
        ax.set_xlabel('spread')
        ax = axes[i, 1]
        for label, prices, days in [('r1', r1, R1_DAYS), ('r2', r2, R2_DAYS)]:
            depths = []
            for day in days:
                sub = split_product(prices[day], prod)
                bv, av = total_depth(sub)
                depths.extend((bv + av).values)
            ax.hist(depths, bins=30, alpha=0.55, label=label, edgecolor='k')
        ax.set_title(f'{prod[:3]} total depth r1 vs r2')
        ax.legend()
        ax.set_xlabel('bid+ask vol')
    plt.tight_layout()
    p = os.path.join(PLOT, 'compare_r1_r2.png')
    plt.savefig(p, dpi=110)
    plt.close()
    print(f'\nplot -> {p}')
if __name__ == '__main__':
    main()
