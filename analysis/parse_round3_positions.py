import json
import os
from collections import defaultdict
PATH = os.path.join('LOGS', '486260', '486260.json')
with open(PATH, 'r') as f:
    blob = json.load(f)
positions = blob.get('positions', [])
print(f'positions type={type(positions).__name__}, count={len(positions)}')
print('=== final positions (end of run) ===')
for entry in positions:
    print(f'  {entry}')
graph = blob.get('graphLog')
if isinstance(graph, str):
    print(f'\ngraphLog len={len(graph)} chars; first 600:\n{graph[:600]}')
elif isinstance(graph, dict):
    print(f'\ngraphLog keys: {list(graph)}')
elif isinstance(graph, list):
    print(f'\ngraphLog list len={len(graph)}; sample [0]: {str(graph[0])[:300]}')
else:
    print(f'\ngraphLog type={type(graph).__name__}')
if False and isinstance(positions, dict):
    print('\n=== position extremes per product ===')
    for prod, series in positions.items():
        if isinstance(series, dict):
            vals = list(series.values())
            try:
                vals_n = [int(v) for v in vals]
            except Exception:
                vals_n = []
            if vals_n:
                print(f'  {prod:22s}: min={min(vals_n):+5d}  max={max(vals_n):+5d}  abs_avg={sum((abs(v) for v in vals_n)) / len(vals_n):6.1f}  ticks={len(vals_n)}')
        elif isinstance(series, list):
            try:
                vals_n = [int(v) for v in series]
                print(f'  {prod:22s}: list len={len(vals_n)}, min={min(vals_n):+5d} max={max(vals_n):+5d}')
            except Exception:
                print(f'  {prod:22s}: list len={len(series)}, sample={series[:5]}')
