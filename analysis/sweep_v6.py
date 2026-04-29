import os
import re
import shutil
import subprocess
ROOT = os.path.join(os.path.dirname(__file__), '..')
TRADER = os.path.join(ROOT, 'trader.py')
TRADER_BAK = os.path.join(ROOT, 'trader.py.bak')
BT = os.path.join(ROOT, 'prosperity_rust_backtester')

def run_bt(dataset='round2'):
    r = subprocess.run(['make', dataset, f'TRADER={TRADER}'], cwd=BT, capture_output=True, text=True)
    out = r.stdout
    total = ipr = aco = None
    for line in out.splitlines():
        if line.startswith('TOTAL'):
            try:
                total = float(line.split()[-2])
            except Exception:
                pass
        if 'INTARIAN_PEPPER_ROOT' in line:
            try:
                ipr = float(line.split()[-1])
            except Exception:
                pass
        if 'ASH_COATED_OSMIUM' in line:
            try:
                aco = float(line.split()[-1])
            except Exception:
                pass
    return (total, ipr, aco)

def patch(src, **kv):
    out = src
    if 'aco_skew' in kv:
        out = re.sub('adj_mid = efv - \\(pos / ml\\) \\* [\\d\\.]+', f"adj_mid = efv - (pos / ml) * {kv['aco_skew']}", out)
    if 'aco_take_buy_le' in kv and kv['aco_take_buy_le']:
        out = out.replace('if ap < efv:', 'if ap <= efv:')
    if 'aco_take_buy_strict' in kv and kv['aco_take_buy_strict']:
        out = out.replace('if ap < efv:', f"if ap <= efv - {kv['aco_take_buy_strict']}:")
    if 'aco_take_sell_strict' in kv and kv['aco_take_sell_strict']:
        out = out.replace('if bp > efv:', f"if bp >= efv + {kv['aco_take_sell_strict']}:")
    if 'aco_make_pb_inside' in kv and kv['aco_make_pb_inside']:
        out = out.replace('pb = min(ideal_bid, bb + 1)', f"pb = min(ideal_bid, bb + {kv['aco_make_pb_inside']})")
    if 'aco_make_pa_inside' in kv and kv['aco_make_pa_inside']:
        out = out.replace('pa = max(ideal_ask, ba - 1)', f"pa = max(ideal_ask, ba - {kv['aco_make_pa_inside']})")
    if 'aco_skew_nonlin' in kv and kv['aco_skew_nonlin']:
        out = re.sub('adj_mid = efv - \\(pos / ml\\) \\* [\\d\\.]+', f"adj_mid = efv - (pos / ml) * 3.0 - (pos / ml) * abs(pos / ml) * {kv['aco_skew_nonlin']}", out)
    return out

def sweep(grid):
    with open(TRADER) as f:
        base = f.read()
    shutil.copy(TRADER, TRADER_BAK)
    print(f"{'tag':<28s} {'total':>10s} {'ipr':>10s} {'aco':>10s} {'d':>10s}")
    base_total = None
    try:
        for cfg in grid:
            new = patch(base, **cfg.get('patches', {}))
            with open(TRADER, 'w') as f:
                f.write(new)
            t, i, a = run_bt()
            if base_total is None and cfg['tag'].startswith('v5_base'):
                base_total = t
            d = t - base_total if t and base_total else 0
            print(f"{cfg['tag']:<28s} {t:>10.0f} {i:>10.0f} {a:>10.0f} {d:>+10.0f}")
    finally:
        shutil.copy(TRADER_BAK, TRADER)
        os.remove(TRADER_BAK)
if __name__ == '__main__':
    grid = [{'tag': 'v5_base', 'patches': {}}, {'tag': 'se5+be3', 'patches': {'aco_take_sell_strict': 5, 'aco_take_buy_strict': 3}}, {'tag': 'se6+be4', 'patches': {'aco_take_sell_strict': 6, 'aco_take_buy_strict': 4}}, {'tag': 'se7+be5', 'patches': {'aco_take_sell_strict': 7, 'aco_take_buy_strict': 5}}, {'tag': 'se8+be6', 'patches': {'aco_take_sell_strict': 8, 'aco_take_buy_strict': 6}}, {'tag': 'se5+be4', 'patches': {'aco_take_sell_strict': 5, 'aco_take_buy_strict': 4}}, {'tag': 'se5+be5', 'patches': {'aco_take_sell_strict': 5, 'aco_take_buy_strict': 5}}, {'tag': 'se6+be3', 'patches': {'aco_take_sell_strict': 6, 'aco_take_buy_strict': 3}}, {'tag': 'se6+be5', 'patches': {'aco_take_sell_strict': 6, 'aco_take_buy_strict': 5}}, {'tag': 'se7+be4', 'patches': {'aco_take_sell_strict': 7, 'aco_take_buy_strict': 4}}, {'tag': 'se7+be3', 'patches': {'aco_take_sell_strict': 7, 'aco_take_buy_strict': 3}}, {'tag': 'se10+be8', 'patches': {'aco_take_sell_strict': 10, 'aco_take_buy_strict': 8}}]
    sweep(grid)
