import subprocess, re

def check(v, t, inv, cap):
    with open('trader.py', 'r') as f:
        c = f.read()
    c = re.sub('predicted_future = p_pred \\+ v_pred \\* [\\d\\.]+', f'predicted_future = p_pred + v_pred * {v}', c)
    c = re.sub('take_thresh = [\\d\\.]+ \\+ abs\\(pos\\) / 80\\.0 \\* [\\d\\.]+', f'take_thresh = 0.0 + abs(pos) / 80.0 * {t}', c)
    c = re.sub('adj_mid = predicted_future - pos / 80\\.0 \\* [\\d\\.]+', f'adj_mid = predicted_future - pos / 80.0 * {inv}', c)
    c = re.sub('passive_cap = \\d+', f'passive_cap = {cap}', c)
    with open('trader.py', 'w') as f:
        f.write(c)
    res = subprocess.run(['make', 'round1', 'TRADER=../trader.py'], cwd='prosperity_rust_backtester', capture_output=True, text=True)
    return res.stdout
for t in [0.0, 1.0, 2.0]:
    for v in [10.0, 15.0, 20.0]:
        print(f'Test v={v}, t={t}')
        out = check(v, t, 0.0, 80)
        for line in out.splitlines():
            if 'INTARIAN_PEPPER_ROOT' in line:
                print(line)
