import os
import re
import shutil
import subprocess
import sys
import tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRADER_SRC = os.path.join(ROOT, 'trader.py')
RUST_DIR = os.path.join(ROOT, 'prosperity_rust_backtester')
CONFIGS = [('v6_baseline', {'DEEP_ITM_TREND_BETA': 0.0, 'VELVET_INV_BIAS': 4, 'COUNTERPARTY_ENABLED': True, 'QUEUE_JUMPER_ENABLED': True}), ('v6_dit_-0.25', {'DEEP_ITM_TREND_BETA': -0.25, 'VELVET_INV_BIAS': 4, 'COUNTERPARTY_ENABLED': True, 'QUEUE_JUMPER_ENABLED': True}), ('v6_dit_-0.5', {'DEEP_ITM_TREND_BETA': -0.5, 'VELVET_INV_BIAS': 4, 'COUNTERPARTY_ENABLED': True, 'QUEUE_JUMPER_ENABLED': True}), ('v6_invbias_0', {'DEEP_ITM_TREND_BETA': -0.25, 'VELVET_INV_BIAS': 0, 'COUNTERPARTY_ENABLED': True, 'QUEUE_JUMPER_ENABLED': True}), ('v6_invbias_2', {'DEEP_ITM_TREND_BETA': -0.25, 'VELVET_INV_BIAS': 2, 'COUNTERPARTY_ENABLED': True, 'QUEUE_JUMPER_ENABLED': True}), ('v6_no_cp', {'DEEP_ITM_TREND_BETA': -0.25, 'VELVET_INV_BIAS': 2, 'COUNTERPARTY_ENABLED': False, 'QUEUE_JUMPER_ENABLED': True}), ('v6_no_jumper', {'DEEP_ITM_TREND_BETA': -0.25, 'VELVET_INV_BIAS': 2, 'COUNTERPARTY_ENABLED': True, 'QUEUE_JUMPER_ENABLED': False}), ('v6_dit_-0.35', {'DEEP_ITM_TREND_BETA': -0.35, 'VELVET_INV_BIAS': 2, 'COUNTERPARTY_ENABLED': True, 'QUEUE_JUMPER_ENABLED': True})]

def patch_trader(orig_text: str, overrides: dict) -> str:
    text = orig_text
    for k, v in overrides.items():
        pattern = re.compile(f'^{k}\\s*=.*$', re.MULTILINE)
        new_line = f'{k} = {v}'
        n = pattern.subn(new_line, text)
        if n[1] == 0:
            raise RuntimeError(f'could not find param {k}')
        text = n[0]
    return text

def run_backtest(trader_path: str) -> str:
    cmd = ['./scripts/cargo_local.sh', 'run', '--release', '--', '--trader', trader_path, '--products', 'summary', '--dataset', 'round4']
    res = subprocess.run(cmd, cwd=RUST_DIR, capture_output=True, text=True, timeout=180)
    return res.stdout + '\n' + res.stderr

def parse_summary(out: str) -> dict:
    info = {'total': None, 'per_day': {}, 'per_product': {}}
    lines = out.split('\n')
    in_set = in_prod = False
    for line in lines:
        if line.startswith('SET '):
            in_set, in_prod = (True, False)
            continue
        if line.startswith('PRODUCT '):
            in_set, in_prod = (False, True)
            continue
        if not line.strip():
            in_set = in_prod = False
            continue
        parts = line.split()
        if in_set:
            if parts[0] == 'TOTAL':
                info['total'] = float(parts[3])
            elif parts[0].startswith('D+'):
                info['per_day'][parts[0]] = float(parts[3])
        if in_prod:
            if parts[0] == 'OTHER':
                continue
            try:
                info['per_product'][parts[0]] = float(parts[-1])
            except ValueError:
                pass
    return info

def main():
    with open(TRADER_SRC, 'r') as f:
        orig = f.read()
    rows = []
    for name, overrides in CONFIGS:
        patched = patch_trader(orig, overrides)
        with tempfile.NamedTemporaryFile('w', suffix='.py', delete=False, dir=ROOT, prefix=f'_sweep_{name}_') as tf:
            tf.write(patched)
            tmp_path = tf.name
        try:
            print(f'\n=== {name} === overrides: {overrides}')
            out = run_backtest(tmp_path)
            info = parse_summary(out)
            print(f"  total: {info['total']:+,.0f}   per-day: {info['per_day']}")
            print(f"  per-product: {info['per_product']}")
            rows.append((name, info))
        finally:
            os.unlink(tmp_path)
    print('\n=== SWEEP SUMMARY ===')
    print(f"{'config':24s} {'total':>10s} {'D+1':>10s} {'D+2':>10s} {'D+3':>10s}  notes")
    for name, info in sorted(rows, key=lambda r: -(r[1]['total'] or 0)):
        d1 = info['per_day'].get('D+1', 0)
        d2 = info['per_day'].get('D+2', 0)
        d3 = info['per_day'].get('D+3', 0)
        print(f"{name:24s} {info['total']:>+10,.0f} {d1:>+10,.0f} {d2:>+10,.0f} {d3:>+10,.0f}")
if __name__ == '__main__':
    main()
