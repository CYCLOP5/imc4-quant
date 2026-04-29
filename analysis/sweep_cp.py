import os, re, subprocess, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRADER_SRC = os.path.join(ROOT, 'trader.py')
RUST_DIR = os.path.join(ROOT, 'prosperity_rust_backtester')
CONFIGS = [('cp_off', {'COUNTERPARTY_ENABLED': False, 'CP_WEIGHT_INFORMED': 1.0, 'CP_WEIGHT_FADE': 0.5, 'COUNTERPARTY_CLIP': 4.0}), ('cp_w0.1', {'COUNTERPARTY_ENABLED': True, 'CP_WEIGHT_INFORMED': 0.1, 'CP_WEIGHT_FADE': 0.05, 'COUNTERPARTY_CLIP': 2.0}), ('cp_w0.2', {'COUNTERPARTY_ENABLED': True, 'CP_WEIGHT_INFORMED': 0.2, 'CP_WEIGHT_FADE': 0.1, 'COUNTERPARTY_CLIP': 2.0}), ('cp_fade_only', {'COUNTERPARTY_ENABLED': True, 'CP_WEIGHT_INFORMED': 0.0, 'CP_WEIGHT_FADE': 0.1, 'COUNTERPARTY_CLIP': 2.0}), ('cp_inf_only', {'COUNTERPARTY_ENABLED': True, 'CP_WEIGHT_INFORMED': 0.1, 'CP_WEIGHT_FADE': 0.0, 'COUNTERPARTY_CLIP': 2.0}), ('cp_neg', {'COUNTERPARTY_ENABLED': True, 'CP_WEIGHT_INFORMED': -0.1, 'CP_WEIGHT_FADE': 0.0, 'COUNTERPARTY_CLIP': 2.0})]

def patch(text, overrides):
    for k, v in overrides.items():
        text = re.sub(f'^{k}\\s*=.*$', f'{k} = {v}', text, count=1, flags=re.MULTILINE)
    return text

def run(path):
    return subprocess.run(['./scripts/cargo_local.sh', 'run', '--release', '--', '--trader', path, '--products', 'summary', '--dataset', 'round4'], cwd=RUST_DIR, capture_output=True, text=True, timeout=180).stdout

def parse(out):
    info = {'total': 0.0, 'velvet': 0.0}
    in_set = in_prod = False
    for line in out.split('\n'):
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
        if in_set and parts[0] == 'TOTAL':
            try:
                info['total'] = float(parts[4])
            except (IndexError, ValueError):
                pass
        if in_prod and parts[0] == 'VELVETFRUIT_EXTRACT':
            try:
                info['velvet'] = float(parts[-1])
            except (IndexError, ValueError):
                pass
    return info
with open(TRADER_SRC) as f:
    orig = f.read()
print(f"{'config':18s} {'total':>10s} {'velvet':>10s}")
for name, ov in CONFIGS:
    patched = patch(orig, ov)
    with tempfile.NamedTemporaryFile('w', suffix='.py', delete=False, dir=ROOT, prefix=f'_cp_{name}_') as tf:
        tf.write(patched)
        tp = tf.name
    try:
        info = parse(run(tp))
        print(f"{name:18s} {info['total']:>+10,.0f} {info['velvet']:>+10,.0f}")
    finally:
        os.unlink(tp)
