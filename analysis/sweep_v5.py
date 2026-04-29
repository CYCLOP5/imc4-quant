import os
import re
import subprocess
import sys
ROOT = os.path.join(os.path.dirname(__file__), '..')
TRADER = os.path.join(ROOT, 'trader.py')
BT = os.path.join(ROOT, 'prosperity_rust_backtester')

def read_trader():
    with open(TRADER) as f:
        return f.read()

def write_trader(s):
    with open(TRADER, 'w') as f:
        f.write(s)

def patch(s, **kv):
    out = s
    for k, v in kv.items():
        if k == 'k_q11':
            out = re.sub('self\\.k_q11 = [\\d\\.eE+-]+', f'self.k_q11 = {v}', out)
        elif k == 'k_r':
            out = re.sub('self\\.k_r = [\\d\\.eE+-]+', f'self.k_r = {v}', out)
        elif k == 'k_h':
            out = re.sub('self\\.k_h = [\\d\\.eE+-]+', f'self.k_h = {v}', out)
        elif k == 'aco_edge':
            out = re.sub('(def trade_aco.*?)edge = \\d+', lambda m: m.group(1) + f'edge = {v}', out, count=1, flags=re.S)
        elif k == 'ipr_edge':
            out = re.sub('(def trade_ipr.*?)edge = \\d+', lambda m: m.group(1) + f'edge = {v}', out, count=1, flags=re.S)
        elif k == 'ipr_skew':
            out = re.sub('adj_mid = predicted_future - pos / 80\\.0 \\* [\\d\\.]+', f'adj_mid = predicted_future - pos / 80.0 * {v}', out)
        elif k == 'aco_skew':
            out = re.sub('adj_mid = efv - \\(pos / ml\\) \\* [\\d\\.]+', f'adj_mid = efv - (pos / ml) * {v}', out)
        elif k == 'take_thresh':
            out = re.sub('predicted_future > best_ask \\+ [\\d\\.]+', f'predicted_future > best_ask + {v}', out)
            out = re.sub('predicted_future < best_bid - [\\d\\.]+', f'predicted_future < best_bid - {v}', out)
    return out

def run_bt():
    r = subprocess.run(['make', 'round2', f'TRADER={TRADER}'], cwd=BT, capture_output=True, text=True)
    out = r.stdout
    total = None
    ipr = None
    aco = None
    for line in out.splitlines():
        if line.startswith('TOTAL'):
            parts = line.split()
            try:
                total = float(parts[-2])
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

def sweep():
    base = read_trader()
    rows = []
    grid = [{'tag': 'baseline_v4.4', 'patches': {}}, {'tag': 'final.A_tt3.5_s3', 'patches': {'aco_edge': 1, 'aco_skew': 3.0, 'take_thresh': 3.5, 'ipr_skew': 2.0}}, {'tag': 'final.B_tt3.5_s3_ie1', 'patches': {'aco_edge': 1, 'aco_skew': 3.0, 'take_thresh': 3.5, 'ipr_skew': 2.0, 'ipr_edge': 1}}, {'tag': 'final.C_tt3.5_s3_ie3', 'patches': {'aco_edge': 1, 'aco_skew': 3.0, 'take_thresh': 3.5, 'ipr_skew': 2.0, 'ipr_edge': 3}}, {'tag': 'final.D_tt3.5_s3_q005', 'patches': {'aco_edge': 1, 'aco_skew': 3.0, 'take_thresh': 3.5, 'ipr_skew': 2.0, 'k_q11': 0.005}}, {'tag': 'final.E_tt3_s3_is2_h12', 'patches': {'aco_edge': 1, 'aco_skew': 3.0, 'take_thresh': 3.0, 'ipr_skew': 2.0, 'k_h': 12.0}}, {'tag': 'final.F_tt3.5_s4', 'patches': {'aco_edge': 1, 'aco_skew': 4.0, 'take_thresh': 3.5, 'ipr_skew': 2.0}}, {'tag': 'final.G_e0_s3_tt3.5', 'patches': {'aco_edge': 0, 'aco_skew': 3.0, 'take_thresh': 3.5, 'ipr_skew': 2.0}}]
    print(f"{'tag':<22s} {'total':>10s} {'ipr':>10s} {'aco':>10s} {'d_total':>10s}")
    base_total = None
    for cfg in grid:
        new = patch(base, **cfg['patches'])
        write_trader(new)
        t, i, a = run_bt()
        if base_total is None and cfg['tag'] == 'baseline_v4.4':
            base_total = t
        d = t - base_total if t is not None and base_total is not None else None
        print(f"{cfg['tag']:<22s} {t:>10.0f} {i:>10.0f} {a:>10.0f} {d:>+10.0f}")
        rows.append((cfg['tag'], t, i, a, d))
    write_trader(base)
if __name__ == '__main__':
    sweep()
