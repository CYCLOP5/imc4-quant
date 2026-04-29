import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from loader import load_all_prices, split_product, best_quotes, ensure_plot_dir, R2_DAYS
PLOT = ensure_plot_dir()

def hdr(s):
    print('\n' + '=' * 64)
    print('  ' + s)
    print('=' * 64)

def run_kalman(mids, q00, q11, r):
    n = len(mids)
    p = mids[0]
    v = 0.0
    P00 = 1.0
    P01 = 0.0
    P10 = 0.0
    P11 = 1.0
    p_arr = np.zeros(n)
    v_arr = np.zeros(n)
    p_arr[0] = p
    for i in range(1, n):
        p_pred = p + v
        v_pred = v
        P00p = P00 + P10 + P01 + P11 + q00
        P01p = P01 + P11
        P10p = P10 + P11
        P11p = P11 + q11
        y = mids[i] - p_pred
        S = P00p + r
        K0 = P00p / S
        K1 = P10p / S
        p = p_pred + K0 * y
        v = v_pred + K1 * y
        P00 = P00p - K0 * P00p
        P01 = P01p - K0 * P01p
        P10 = P10p - K1 * P00p
        P11 = P11p - K1 * P01p
        p_arr[i] = p
        v_arr[i] = v
    return (p_arr, v_arr)

def fwd_score(mids, p_arr, v_arr, horiz):
    n = len(mids)
    h = int(horiz)
    if h >= n:
        return (0.0, 0.0)
    pred = (p_arr + v_arr * horiz)[:n - h]
    actual = mids[h:n]
    err = pred - actual
    rmse = float(np.sqrt(np.mean(err * err)))
    pred_dir = np.sign((p_arr + v_arr * horiz)[:n - 1] - mids[:n - 1])
    real_dir = np.sign(np.diff(mids))
    hit = float(np.mean(pred_dir == real_dir))
    return (rmse, hit)

def naive_carry_pnl(mids, p_arr, v_arr, horiz, edge):
    n = len(mids)
    pnl = 0.0
    pos = 0
    cap = 80
    for i in range(n - 1):
        pred = p_arr[i] + v_arr[i] * horiz
        if pred > mids[i] + edge and pos < cap:
            pos += 1
            pnl -= mids[i]
        elif pred < mids[i] - edge and pos > -cap:
            pos -= 1
            pnl += mids[i]
    pnl += pos * mids[-1]
    return (pnl, pos)

def sweep_per_day():
    hdr('kalman sweep per r2 day on ipr')
    prices = load_all_prices(2)
    rows = []
    for day in R2_DAYS:
        sub = best_quotes(split_product(prices[day], 'INTARIAN_PEPPER_ROOT'))
        mids = sub['mid_price'].values
        for q00 in [0.05, 0.1, 0.2, 0.5, 1.0]:
            for q11 in [0.001, 0.005, 0.01, 0.05, 0.1]:
                for r in [1.0, 2.0, 4.0, 8.0]:
                    p_arr, v_arr = run_kalman(mids, q00, q11, r)
                    for h in [10, 12, 15, 20, 25]:
                        rmse, hit = fwd_score(mids, p_arr, v_arr, h)
                        pnl, pos = naive_carry_pnl(mids, p_arr, v_arr, h, edge=0.5)
                        rows.append({'day': day, 'q00': q00, 'q11': q11, 'r': r, 'h': h, 'rmse': rmse, 'hit': hit, 'pnl': pnl, 'pos': pos})
    df = pd.DataFrame(rows)
    out_csv = os.path.join(os.path.dirname(__file__), 'kalman_sweep.csv')
    df.to_csv(out_csv, index=False)
    print(f'\nsaved -> {out_csv}\n')
    g = df.groupby(['q00', 'q11', 'r', 'h']).agg(pnl_mean=('pnl', 'mean'), rmse_mean=('rmse', 'mean'), hit_mean=('hit', 'mean')).reset_index()
    print('top 15 by mean pnl across days:')
    print(g.sort_values('pnl_mean', ascending=False).head(15).to_string(index=False))
    print('\nbottom 5 (worst):')
    print(g.sort_values('pnl_mean', ascending=True).head(5).to_string(index=False))
    print('\ncurrent trader v4.4 params (q00=0.1, q11=0.01, r=2.0, h=15):')
    cur = g[(g['q00'] == 0.1) & (g['q11'] == 0.01) & (g['r'] == 2.0) & (g['h'] == 15)]
    print(cur.to_string(index=False))
    print('\nbest h for each (q00,q11,r) (top 5):')
    g2 = g.loc[g.groupby(['q00', 'q11', 'r'])['pnl_mean'].idxmax()].sort_values('pnl_mean', ascending=False).head(5)
    print(g2.to_string(index=False))

def edge_sweep():
    hdr('edge sweep at best kalman params')
    prices = load_all_prices(2)
    rows = []
    for day in R2_DAYS:
        sub = best_quotes(split_product(prices[day], 'INTARIAN_PEPPER_ROOT'))
        mids = sub['mid_price'].values
        p_arr, v_arr = run_kalman(mids, 0.1, 0.01, 2.0)
        for h in [12, 15, 20]:
            for edge in [0.0, 0.25, 0.5, 1.0, 1.5, 2.0, 3.0]:
                pnl, pos = naive_carry_pnl(mids, p_arr, v_arr, h, edge=edge)
                rows.append({'day': day, 'h': h, 'edge': edge, 'pnl': pnl, 'pos': pos})
    df = pd.DataFrame(rows)
    g = df.groupby(['h', 'edge']).agg(pnl_mean=('pnl', 'mean')).reset_index()
    print(g.to_string(index=False))

def main():
    sweep_per_day()
    edge_sweep()
if __name__ == '__main__':
    main()
