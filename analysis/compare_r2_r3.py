from __future__ import annotations
import os
import sys
import numpy as np
import pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
import loader

def stats_one(df: pd.DataFrame, product: str) -> dict:
    sub = loader.split_product(df, product, drop_empty=True)
    mid = sub['mid_price'].dropna().values
    sp = (sub['ask_price_1'] - sub['bid_price_1']).dropna().values
    rets = np.diff(mid)
    return {'mid_mean': float(mid.mean()), 'mid_std': float(mid.std()), 'drift': float(mid[-1] - mid[0]), 'sp_med': float(np.median(sp)), 'ret_std': float(rets.std()), 'acf_1': _acf(rets, 1)}

def _acf(x, lag):
    x = np.asarray(x, dtype=float)
    x = x[~np.isnan(x)]
    if len(x) <= lag:
        return float('nan')
    m, v = (x.mean(), x.var())
    if v == 0:
        return float('nan')
    return float(((x[:-lag] - m) * (x[lag:] - m)).sum() / ((len(x) - lag) * v))

def delta_table() -> pd.DataFrame:
    rows = []
    for product_r2 in ['ASH_COATED_OSMIUM']:
        for day in loader.R2_DAYS:
            df = loader.load_prices(2, day)
            s = stats_one(df, product_r2)
            s.update({'round': 'r2', 'product': product_r2, 'day': day, 'role': 'stationary'})
            rows.append(s)
    for day in loader.R3_DAYS:
        df = loader.load_prices(3, day)
        s = stats_one(df, 'HYDROGEL_PACK')
        s.update({'round': 'r3', 'product': 'HYDROGEL_PACK', 'day': day, 'role': 'stationary'})
        rows.append(s)
    for day in loader.R2_DAYS:
        df = loader.load_prices(2, day)
        s = stats_one(df, 'INTARIAN_PEPPER_ROOT')
        s.update({'round': 'r2', 'product': 'INTARIAN_PEPPER_ROOT', 'day': day, 'role': 'momentum/drift'})
        rows.append(s)
    for day in loader.R3_DAYS:
        df = loader.load_prices(3, day)
        s = stats_one(df, 'VELVETFRUIT_EXTRACT')
        s.update({'round': 'r3', 'product': 'VELVETFRUIT_EXTRACT', 'day': day, 'role': 'momentum/drift'})
        rows.append(s)
    return pd.DataFrame(rows)

def main() -> None:
    df = delta_table()
    cols = ['round', 'role', 'product', 'day', 'mid_mean', 'mid_std', 'drift', 'sp_med', 'ret_std', 'acf_1']
    df = df[cols].copy()
    for c in ('mid_mean', 'mid_std', 'drift', 'ret_std'):
        df[c] = df[c].round(3)
    df['acf_1'] = df['acf_1'].round(4)
    print(df.to_string(index=False))
    agg = df.groupby(['round', 'product']).agg({'mid_mean': 'mean', 'mid_std': 'mean', 'drift': 'mean', 'sp_med': 'mean', 'ret_std': 'mean', 'acf_1': 'mean'}).round(3)
    print('\n==== 3-day averages ====')
    print(agg.to_string())
    outpath = os.path.join(os.path.dirname(__file__), 'r2_vs_r3.csv')
    df.to_csv(outpath, index=False)
    print(f'\nwritten: {outpath}')
    print('\n==== headline regime shifts ====')
    ipr_drift_abs = np.abs(df[df['product'] == 'INTARIAN_PEPPER_ROOT']['drift']).mean()
    vel_drift_abs = np.abs(df[df['product'] == 'VELVETFRUIT_EXTRACT']['drift']).mean()
    aco_sp = df[df['product'] == 'ASH_COATED_OSMIUM']['sp_med'].mean()
    hyd_sp = df[df['product'] == 'HYDROGEL_PACK']['sp_med'].mean()
    print(f'mean |drift| per day: IPR={ipr_drift_abs:.1f}  VELVET={vel_drift_abs:.1f}   -> {ipr_drift_abs / max(1, vel_drift_abs):.1f}x drop in systematic drift')
    print(f'median spread: ACO={aco_sp:.1f}  HYDRO={hyd_sp:.1f}   -> {hyd_sp / max(1, aco_sp):.1f}x wider quotes on r3 stationary product')
if __name__ == '__main__':
    main()
