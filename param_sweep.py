import subprocess, re, os
PROJ_DIR = '/Users/cyclops/Downloads/TUTORIAL_ROUND_1'
BACKTESTER_DIR = os.path.join(PROJ_DIR, 'imc-prosperity-4-backtester')
TRADER_SRC = os.path.join(PROJ_DIR, 'trader.py')
TMP_TRADER = os.path.join(PROJ_DIR, 'trader_sweep.py')
with open(TRADER_SRC) as f:
    template = f.read()
results = []
for mr_coeff in [0.05, 0.1, 0.15, 0.18, 0.2, 0.22, 0.25, 0.3]:
    for inv_nudge in [0.01, 0.02, 0.03, 0.04, 0.05]:
        modified = template.replace('delta * 0.4', f'delta * {mr_coeff}')
        modified = modified.replace('pos * 0.05', f'pos * {inv_nudge}')
        with open(TMP_TRADER, 'w') as f:
            f.write(modified)
        cmd = ['python', '-m', 'prosperity4bt', TMP_TRADER, '0']
        try:
            out = subprocess.run(cmd, capture_output=True, text=True, cwd=BACKTESTER_DIR, timeout=30)
            output = out.stdout + out.stderr
            day_profits = re.findall('Round 0 day -\\d+: ([\\d,]+)', output)
            total = sum((int(p.replace(',', '')) for p in day_profits))
            d2 = int(day_profits[0].replace(',', '')) if len(day_profits) > 0 else 0
            d1 = int(day_profits[1].replace(',', '')) if len(day_profits) > 1 else 0
            results.append((mr_coeff, inv_nudge, d2, d1, total))
            print(f'mr={mr_coeff:.2f} inv={inv_nudge:.2f} → d-2={d2:>6} d-1={d1:>6} TOT={total:>6}')
        except Exception as e:
            print(f'mr={mr_coeff:.2f} inv={inv_nudge:.2f} → ERROR: {e}')
if os.path.exists(TMP_TRADER):
    os.remove(TMP_TRADER)
results.sort(key=lambda x: -x[4])
print(f"\n{'=' * 60}")
print('TOP 10:')
print(f"{'=' * 60}")
for i, (mr, inv, d2, d1, total) in enumerate(results[:10]):
    print(f'  #{i + 1}: mr={mr:.2f} inv={inv:.2f} → d-2={d2:>6} d-1={d1:>6} TOT={total:>6}')
