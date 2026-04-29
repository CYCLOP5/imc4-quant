import os
import numpy as np
import pandas as pd
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R3_DIR = os.path.join(_ROOT, 'prosperity_rust_backtester', 'datasets', 'round3')
R2_DIR = os.path.join(_ROOT, 'prosperity_rust_backtester', 'datasets', 'round2')
R1_DIR = os.path.join(_ROOT, 'prosperity_rust_backtester', 'datasets', 'round1')
R3_DAYS = ['0', '1', '2']
R2_DAYS = ['-1', '0', '1']
R1_DAYS = ['-2', '-1', '0']
PRODUCTS = ['HYDROGEL_PACK', 'VELVETFRUIT_EXTRACT', 'VEV_4000', 'VEV_4500', 'VEV_5000', 'VEV_5100', 'VEV_5200', 'VEV_5300', 'VEV_5400', 'VEV_5500', 'VEV_6000', 'VEV_6500']
PLOT_DIR = os.path.join(os.path.dirname(__file__), 'plots')

def _base_dir(round_num):
    return {1: R1_DIR, 2: R2_DIR, 3: R3_DIR}[round_num]

def _days(round_num):
    return {1: R1_DAYS, 2: R2_DAYS, 3: R3_DAYS}[round_num]

def load_prices(round_num, day):
    p = os.path.join(_base_dir(round_num), f'prices_round_{round_num}_day_{day}.csv')
    return pd.read_csv(p, sep=';')

def load_trades(round_num, day):
    p = os.path.join(_base_dir(round_num), f'trades_round_{round_num}_day_{day}.csv')
    return pd.read_csv(p, sep=';')

def load_all_prices(round_num):
    return {d: load_prices(round_num, d) for d in _days(round_num)}

def load_all_trades(round_num):
    return {d: load_trades(round_num, d) for d in _days(round_num)}

def split_product(df, product, drop_empty=True):
    sub = df[df['product'] == product]
    if drop_empty:
        sub = sub[(sub['mid_price'] > 0) & sub['bid_price_1'].notna() & sub['ask_price_1'].notna()]
    return sub.reset_index(drop=True)

def best_quotes(df):
    out = df.copy()
    out['spread'] = out['ask_price_1'] - out['bid_price_1']
    out['micro'] = (out['bid_price_1'] * out['ask_volume_1'] + out['ask_price_1'] * out['bid_volume_1']) / (out['bid_volume_1'] + out['ask_volume_1'])
    return out

def total_depth(df):
    bv = df[['bid_volume_1', 'bid_volume_2', 'bid_volume_3']].fillna(0).sum(axis=1)
    av = df[['ask_volume_1', 'ask_volume_2', 'ask_volume_3']].fillna(0).sum(axis=1)
    return (bv, av)

def wallmid(df):
    bp = df[['bid_price_1', 'bid_price_2', 'bid_price_3']].values
    bv = df[['bid_volume_1', 'bid_volume_2', 'bid_volume_3']].fillna(0).values
    ap = df[['ask_price_1', 'ask_price_2', 'ask_price_3']].values
    av = df[['ask_volume_1', 'ask_volume_2', 'ask_volume_3']].fillna(0).values
    out = np.zeros(len(df))
    for i in range(len(df)):
        bj = np.argmax(bv[i]) if np.nansum(bv[i]) > 0 else -1
        aj = np.argmax(av[i]) if np.nansum(av[i]) > 0 else -1
        if bj < 0 or aj < 0 or np.isnan(bp[i, bj]) or np.isnan(ap[i, aj]):
            out[i] = df['mid_price'].iloc[i]
        else:
            out[i] = (bp[i, bj] + ap[i, aj]) / 2.0
    return out

def autocorr(x, lag):
    x = np.asarray(x, dtype=float)
    x = x[~np.isnan(x)]
    if len(x) <= lag:
        return np.nan
    m = x.mean()
    v = x.var()
    if v == 0:
        return np.nan
    return ((x[:-lag] - m) * (x[lag:] - m)).sum() / ((len(x) - lag) * v)

def ensure_plot_dir():
    os.makedirs(PLOT_DIR, exist_ok=True)
    return PLOT_DIR
