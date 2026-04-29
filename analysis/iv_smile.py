from __future__ import annotations
import math
import os
import sys
import numpy as np
import pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
import loader
SMILE_STRIKES = [5000, 5100, 5200, 5300, 5400, 5500]
ALL_STRIKES = [4000, 4500] + SMILE_STRIKES
R3_TTE_DAYS = {'0': 8.0, '1': 7.0, '2': 6.0}
DAYS_PER_YEAR = 365.0

def _norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

def bs_call(S: float, K: float, T: float, sigma: float, r: float=0.0) -> float:
    if sigma <= 0 or T <= 0:
        return max(0.0, S - K)
    v = sigma * math.sqrt(T)
    d1 = (math.log(S / K) + 0.5 * sigma * sigma * T) / v
    d2 = d1 - v
    return S * _norm_cdf(d1) - K * math.exp(-r * T) * _norm_cdf(d2)

def implied_vol_call(price: float, S: float, K: float, T: float) -> float:
    intrinsic = max(0.0, S - K)
    if price <= intrinsic + 1e-08:
        return float('nan')
    lo, hi = (0.0001, 5.0)
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        pc = bs_call(S, K, T, mid)
        if pc > price:
            hi = mid
        else:
            lo = mid
        if hi - lo < 1e-06:
            break
    return 0.5 * (lo + hi)

def smile_per_tick(df: pd.DataFrame, T_years: float) -> pd.DataFrame:
    velvet = df[df['product'] == 'VELVETFRUIT_EXTRACT'].set_index('timestamp')['mid_price']
    vouchers = {K: df[df['product'] == f'VEV_{K}'].set_index('timestamp')['mid_price'] for K in SMILE_STRIKES}
    common = velvet.index
    for K, ser in vouchers.items():
        common = common.intersection(ser.index)
    velvet = velvet.reindex(common)
    vouchers = {K: ser.reindex(common) for K, ser in vouchers.items()}
    rows = []
    for ts in common:
        S = float(velvet.loc[ts])
        if S <= 0:
            continue
        ivs = []
        ms = []
        kept_strikes = []
        for K in SMILE_STRIKES:
            px = float(vouchers[K].loc[ts])
            iv = implied_vol_call(px, S, K, T_years)
            if np.isnan(iv):
                continue
            m = math.log(K / S) / math.sqrt(T_years)
            ivs.append(iv)
            ms.append(m)
            kept_strikes.append(K)
        if len(ivs) < 3:
            continue
        ms_arr = np.array(ms)
        ivs_arr = np.array(ivs)
        A = np.vstack([ms_arr ** 2, ms_arr, np.ones_like(ms_arr)]).T
        coef, _, _, _ = np.linalg.lstsq(A, ivs_arr, rcond=None)
        a, b, c = coef
        fit = A @ coef
        resid = ivs_arr - fit
        row = {'ts': ts, 'S': S, 'a': a, 'b': b, 'c': c}
        for k, r, iv in zip(kept_strikes, resid, ivs_arr):
            row[f'resid_{k}'] = r
            row[f'iv_{k}'] = iv
        rows.append(row)
    return pd.DataFrame(rows)

def main() -> None:
    summary = []
    for day in loader.R3_DAYS:
        T_years = R3_TTE_DAYS[day] / DAYS_PER_YEAR
        df = loader.load_prices(3, day)
        print(f'\n==== day {day}: TTE={R3_TTE_DAYS[day]}d (T={T_years:.4f}y) ====')
        s = smile_per_tick(df, T_years)
        if s.empty:
            print('  no valid smile ticks')
            continue
        print(f'  rows with valid smile fit: {len(s)}')
        print(f"  ATM IV (c): mean={s['c'].mean():.4f}  std={s['c'].std():.4f}  min={s['c'].min():.4f}  max={s['c'].max():.4f}")
        print(f"  skew (b):   mean={s['b'].mean():+.4f}  std={s['b'].std():.4f}")
        print(f"  curv (a):   mean={s['a'].mean():+.4f}  std={s['a'].std():.4f}")
        for K in SMILE_STRIKES:
            col = f'resid_{K}'
            if col in s.columns:
                r = s[col].dropna()
                print(f'  resid K={K}: n={len(r):5d} mean={r.mean():+.5f} std={r.std():.5f}  q05={r.quantile(0.05):+.4f}  q95={r.quantile(0.95):+.4f}')
        c = s['c'].values
        if len(c) > 100:
            c1 = np.corrcoef(c[:-1], c[1:])[0, 1]
            c10 = np.corrcoef(c[:-10], c[10:])[0, 1]
            print(f'  ATM IV acf: lag1={c1:+.4f}  lag10={c10:+.4f}')
        summary.append({'day': day, 'atm_iv_mean': s['c'].mean(), 'atm_iv_std': s['c'].std(), 'skew_mean': s['b'].mean(), 'curv_mean': s['a'].mean()})
        outpath = os.path.join(os.path.dirname(__file__), f'r3_smile_day{day}.csv')
        s.to_csv(outpath, index=False)
    print('\n==== across-day summary ====')
    print(pd.DataFrame(summary).to_string(index=False))
    print('\n==== is ATM IV stationary across days? (potential alpha) ====')
    for row in summary:
        print(f"  day {row['day']}: ATM_IV = {row['atm_iv_mean']:.4f} +/- {row['atm_iv_std']:.4f}")
if __name__ == '__main__':
    main()
