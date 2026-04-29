from __future__ import annotations
import os
import sys
import numpy as np
import pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
import loader
DEEP_ITM = [4000, 4500]
POS_LIM = {'VELVETFRUIT_EXTRACT': 200, 'VEV_4000': 300, 'VEV_4500': 300, 'VEV_5000': 300}

def best_quote_basis(df: pd.DataFrame, K: int) -> pd.DataFrame:
    velvet = df[df['product'] == 'VELVETFRUIT_EXTRACT'].set_index('timestamp')
    voucher = df[df['product'] == f'VEV_{K}'].set_index('timestamp')
    common = velvet.index.intersection(voucher.index)
    v = velvet.loc[common]
    o = voucher.loc[common]
    out = pd.DataFrame({'ts': common, 'v_bb': v['bid_price_1'].values, 'v_ba': v['ask_price_1'].values, 'v_mid': v['mid_price'].values, 'o_bb': o['bid_price_1'].values, 'o_ba': o['ask_price_1'].values, 'o_mid': o['mid_price'].values})
    out['intrinsic'] = (out['v_mid'] - K).clip(lower=0)
    out['basis_mid'] = out['o_mid'] - out['intrinsic']
    out['intrinsic_bb_side'] = (out['v_bb'] - K).clip(lower=0)
    out['intrinsic_ba_side'] = (out['v_ba'] - K).clip(lower=0)
    out['arb_buy_edge'] = out['v_bb'] - K - out['o_ba']
    out['arb_sell_edge'] = out['o_bb'] - (out['v_ba'] - K)
    return out

def basis_mean_rev(basis: pd.Series) -> dict:
    b = basis.dropna().values
    if len(b) < 5:
        return {}
    rets = np.diff(b)
    m = b.mean()
    s = b.std()

    def _ac(x, lag):
        if len(x) <= lag or x.std() == 0:
            return np.nan
        return float(((x[:-lag] - x.mean()) * (x[lag:] - x.mean())).sum() / ((len(x) - lag) * x.var()))
    return {'mean': round(float(m), 4), 'std': round(float(s), 4), 'q05': round(float(np.quantile(b, 0.05)), 3), 'q95': round(float(np.quantile(b, 0.95)), 3), 'acf1_level': round(_ac(b, 1), 4), 'acf1_ret': round(_ac(rets, 1), 4), 'n_extreme': int(np.sum(np.abs(b - m) > 2 * s))}

def synthetic_capacity_summary() -> None:
    base = POS_LIM['VELVETFRUIT_EXTRACT']
    v4000 = POS_LIM['VEV_4000']
    v4500 = POS_LIM['VEV_4500']
    v5000_delta = 0.99
    v5000 = int(POS_LIM['VEV_5000'] * v5000_delta)
    total = base + v4000 + v4500 + v5000
    print(f'native VELVET limit:   {base}')
    print(f'+ VEV_4000 (delta~1):  +{v4000}')
    print(f'+ VEV_4500 (delta~1):  +{v4500}')
    print(f'+ VEV_5000 (delta~0.99): +{v5000}')
    print(f'TOTAL synthetic VELVET exposure: {total}  ({total / base:.2f}x native)')

def main() -> None:
    for day in loader.R3_DAYS:
        df = loader.load_prices(3, day)
        print(f'\n==== day {day} ====')
        for K in DEEP_ITM:
            b = best_quote_basis(df, K)
            arb_buy = (b['arb_buy_edge'] > 0).sum()
            arb_sell = (b['arb_sell_edge'] > 0).sum()
            best_buy = b['arb_buy_edge'].max()
            best_sell = b['arb_sell_edge'].max()
            print(f'  VEV_{K}:')
            print(f'    ticks={len(b):5d}')
            print(f'    arb buy (v_bb-K > o_ba) count={arb_buy} best_edge={best_buy:.2f}')
            print(f'    arb sell (o_bb > v_ba-K) count={arb_sell} best_edge={best_sell:.2f}')
            mr = basis_mean_rev(b['basis_mid'])
            print(f'    basis (mid): {mr}')
    print('\n==== synthetic VELVET capacity ====')
    synthetic_capacity_summary()
    print('\n==== basis mean across days (should be ~0 for deep ITM) ====')
    for day in loader.R3_DAYS:
        df = loader.load_prices(3, day)
        row = []
        for K in DEEP_ITM:
            b = best_quote_basis(df, K)['basis_mid']
            row.append((K, b.mean(), b.std()))
        for K, m, s in row:
            print(f'  day{day} VEV_{K}: basis mean={m:+.4f}  std={s:.4f}')
if __name__ == '__main__':
    main()
