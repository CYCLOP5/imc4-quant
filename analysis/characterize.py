from __future__ import annotations
import os
import sys
import numpy as np
import pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
import loader

def acf(x: np.ndarray, lag: int) -> float:
    x = np.asarray(x, dtype=float)
    x = x[~np.isnan(x)]
    if len(x) <= lag:
        return np.nan
    m = x.mean()
    v = x.var()
    if v == 0:
        return np.nan
    return float(((x[:-lag] - m) * (x[lag:] - m)).sum() / ((len(x) - lag) * v))

def per_product_day(df: pd.DataFrame, product: str, day: str) -> dict:
    sub = loader.split_product(df, product, drop_empty=True)
    mid = sub['mid_price'].dropna().values
    if len(mid) == 0:
        return {}
    sp = (sub['ask_price_1'] - sub['bid_price_1']).dropna().values
    rets = np.diff(mid)
    return {'day': day, 'product': product, 'n': len(sub), 'mid_mean': round(float(mid.mean()), 3), 'mid_std': round(float(mid.std()), 3), 'mid_min': float(mid.min()), 'mid_max': float(mid.max()), 'drift': round(float(mid[-1] - mid[0]), 2), 'sp_med': float(np.median(sp)) if len(sp) else np.nan, 'sp_mean': round(float(sp.mean()), 3) if len(sp) else np.nan, 'ret_std': round(float(rets.std()), 4) if len(rets) else np.nan, 'acf_1': round(acf(rets, 1), 4), 'acf_5': round(acf(rets, 5), 4), 'acf_50': round(acf(rets, 50), 4)}

def characterize_round(round_num: int=3) -> pd.DataFrame:
    prices_by_day = loader.load_all_prices(round_num)
    rows = []
    for day, df in prices_by_day.items():
        for p in loader.PRODUCTS:
            row = per_product_day(df, p, day)
            if row:
                rows.append(row)
    return pd.DataFrame(rows)

def main() -> None:
    out = characterize_round(3)
    print(out.to_string(index=False))
    outpath = os.path.join(os.path.dirname(__file__), 'r3_characterize.csv')
    out.to_csv(outpath, index=False)
    print(f'\nwritten to {outpath}')
    print('\n==== regime summary ====')
    for p in ['HYDROGEL_PACK', 'VELVETFRUIT_EXTRACT']:
        sub = out[out['product'] == p]
        print(f'{p}:')
        print(f"  mid_std  per day:    {sub['mid_std'].tolist()}")
        print(f"  drift    per day:    {sub['drift'].tolist()}")
        print(f"  ret_std  per day:    {sub['ret_std'].tolist()}")
        print(f"  acf_lag1 per day:    {sub['acf_1'].tolist()}")
        print(f"  sp_med   per day:    {sub['sp_med'].tolist()}")
    print('\n==== voucher premium over intrinsic (day 0) ====')
    df0 = loader.load_prices(3, loader.R3_DAYS[0])
    velvet = df0[df0['product'] == 'VELVETFRUIT_EXTRACT'].set_index('timestamp')['mid_price']
    for K in [4000, 4500, 5000, 5100, 5200, 5300, 5400, 5500]:
        vm = df0[df0['product'] == f'VEV_{K}'].set_index('timestamp')['mid_price']
        intrinsic = (velvet - K).clip(lower=0)
        prem = (vm - intrinsic).dropna()
        print(f'  K={K}: prem_mean={prem.mean():7.3f}  prem_std={prem.std():5.3f}  prem_q05={prem.quantile(0.05):+.2f}  prem_q95={prem.quantile(0.95):+.2f}')
if __name__ == '__main__':
    main()
