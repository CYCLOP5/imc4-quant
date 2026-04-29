from __future__ import annotations
import argparse
import os
import re
import subprocess
import sys
import time
import pandas as pd
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRADER_PATH = os.path.join(_ROOT, 'trader.py')
BACKTESTER_DIR = os.path.join(_ROOT, 'prosperity_rust_backtester')
PARAM_KEYS = ['FV_ALPHA_HYDRO', 'FV_ALPHA_VELVET', 'HYDRO_BUY_EDGE', 'HYDRO_SELL_EDGE', 'HYDRO_MAKE_EDGE', 'HYDRO_SKEW', 'VELVET_TAKE_THRESH', 'VELVET_MAKE_EDGE', 'VELVET_SKEW', 'DEEP_ITM_TAKE_EDGE', 'DEEP_ITM_MAKE_EDGE', 'DEEP_ITM_SKEW', 'SMILE_Z_TAKE', 'SMILE_MAKE_EDGE', 'SMILE_SKEW']

def read_params(path: str=TRADER_PATH) -> dict:
    with open(path) as f:
        src = f.read()
    out = {}
    for k in PARAM_KEYS:
        m = re.search(f'^{k}\\s*=\\s*([0-9.\\-]+)', src, re.M)
        if m:
            out[k] = float(m.group(1))
    return out

def patch_params(cfg: dict, path: str=TRADER_PATH) -> None:
    with open(path) as f:
        src = f.read()
    for k, v in cfg.items():
        pat = f'^{k}\\s*=\\s*[0-9.\\-]+'
        src = re.sub(pat, f'{k} = {v}', src, flags=re.M)
    with open(path, 'w') as f:
        f.write(src)

def run_once(tag: str) -> dict:
    t0 = time.time()
    res = subprocess.run(['make', 'round3', f'TRADER={os.path.relpath(TRADER_PATH, BACKTESTER_DIR)}'], cwd=BACKTESTER_DIR, capture_output=True, text=True)
    dt = time.time() - t0
    out = res.stdout + res.stderr
    pnl_by_day = {}
    total = None
    for line in out.splitlines():
        m = re.match('D[=+](-?\\d+)\\s+(-?\\d+)\\s+(-?\\d+)\\s+(-?\\d+)\\s+(-?\\d+\\.\\d+)\\s', line)
        if m:
            day = int(m.group(1))
            pnl = float(m.group(5))
            pnl_by_day[day] = pnl
        if line.startswith('TOTAL'):
            parts = line.split()
            try:
                total = float(parts[-2])
            except Exception:
                pass
    return {'tag': tag, 'dt': round(dt, 1), 'day0': pnl_by_day.get(0), 'day1': pnl_by_day.get(1), 'day2': pnl_by_day.get(2), 'total': total, 'raw_tail': out[-400:]}
CURATED = [('baseline', {}), ('edges_up_a', {'HYDRO_MAKE_EDGE': 3, 'VELVET_MAKE_EDGE': 2, 'VELVET_TAKE_THRESH': 3, 'DEEP_ITM_MAKE_EDGE': 3, 'SMILE_Z_TAKE': 3}), ('edges_up_b', {'HYDRO_MAKE_EDGE': 4, 'VELVET_MAKE_EDGE': 2, 'VELVET_TAKE_THRESH': 3, 'DEEP_ITM_MAKE_EDGE': 3, 'SMILE_Z_TAKE': 4}), ('edges_up_c', {'HYDRO_MAKE_EDGE': 5, 'VELVET_MAKE_EDGE': 3, 'VELVET_TAKE_THRESH': 4, 'DEEP_ITM_MAKE_EDGE': 4, 'SMILE_Z_TAKE': 4}), ('skew_up', {'HYDRO_SKEW': 5.0, 'VELVET_SKEW': 3.0, 'DEEP_ITM_SKEW': 3.0}), ('slow_fv', {'FV_ALPHA_HYDRO': 0.01, 'FV_ALPHA_VELVET': 0.02}), ('fast_fv', {'FV_ALPHA_HYDRO': 0.05, 'FV_ALPHA_VELVET': 0.1})]

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('mode', nargs='?', default='single', choices=['single', 'curated'])
    args = ap.parse_args()
    base = read_params()
    print(f'baseline params: {base}')
    results = []
    if args.mode == 'single':
        row = run_once('baseline')
        print(row)
        results.append(row)
    else:
        for tag, delta in CURATED:
            cfg = dict(base)
            cfg.update(delta)
            patch_params(cfg)
            print(f'running {tag}: delta={delta}')
            row = run_once(tag)
            row.update({k: cfg[k] for k in delta})
            print(f"  total={row['total']} day0={row['day0']} day1={row['day1']} day2={row['day2']}  ({row['dt']}s)")
            results.append(row)
        patch_params(base)
    outpath = os.path.join(os.path.dirname(__file__), 'sweep_v1_results.csv')
    df = pd.DataFrame(results).drop(columns=['raw_tail'], errors='ignore')
    df.to_csv(outpath, index=False)
    print(f'\nwritten: {outpath}')
    if not df.empty:
        print(df.to_string(index=False))
if __name__ == '__main__':
    main()
