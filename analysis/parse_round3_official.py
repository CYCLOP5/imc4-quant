import json
import os
import sys
from collections import defaultdict
PATH = os.path.join('LOGS', '486260', '486260.json')
with open(PATH, 'r') as f:
    blob = json.load(f)
print(f'keys: {list(blob.keys())}')
print(f"round: {blob.get('round')}  status: {blob.get('status')}  profit: {blob.get('profit')}")
activities = blob['activitiesLog']
lines = activities.strip().split('\n')
header = lines[0].split(';')
print(f'\nactivities header: {header}')
print(f'activity rows: {len(lines) - 1}')
ix = {h: i for i, h in enumerate(header)}
last_pnl = defaultdict(lambda: defaultdict(float))
final_pnl_by_day = defaultdict(dict)
mid_price_seen = defaultdict(list)
ts_by_day = defaultdict(set)
days_seen = set()
for line in lines[1:]:
    parts = line.split(';')
    if len(parts) < len(header):
        continue
    day = int(parts[ix['day']])
    ts = int(parts[ix['timestamp']])
    prod = parts[ix['product']]
    days_seen.add(day)
    ts_by_day[day].add(ts)
    pnl_str = parts[ix['profit_and_loss']]
    if pnl_str:
        last_pnl[day][prod] = float(pnl_str)
    mid_str = parts[ix['mid_price']]
    if mid_str:
        mid_price_seen[day, prod].append((ts, float(mid_str)))
print(f'\ndays present: {sorted(days_seen)}')
for d in sorted(days_seen):
    ts_list = sorted(ts_by_day[d])
    print(f'  day {d}: {len(ts_list)} ticks, range [{ts_list[0]} .. {ts_list[-1]}]')
print('\n=== final PnL per product per day (from activities log) ===')
all_products = set()
for d in days_seen:
    for p in last_pnl[d]:
        all_products.add(p)
order = ['HYDROGEL_PACK', 'VELVETFRUIT_EXTRACT', 'VEV_4000', 'VEV_4500', 'VEV_5000', 'VEV_5100', 'VEV_5200', 'VEV_5300', 'VEV_5400', 'VEV_5500', 'VEV_6000', 'VEV_6500']
products_sorted = [p for p in order if p in all_products] + [p for p in sorted(all_products) if p not in order]
day_list = sorted(days_seen)
header_str = f"{'product':22s}" + ''.join((f"  {f'day{d}':>10s}" for d in day_list)) + f"  {'TOTAL':>10s}"
print(header_str)
print('-' * len(header_str))
day_totals = defaultdict(float)
grand_total = 0.0
for p in products_sorted:
    parts_str = f'{p:22s}'
    total_p = 0.0
    for d in day_list:
        v = last_pnl[d].get(p, 0.0)
        parts_str += f'  {v:10.0f}'
        total_p += v
        day_totals[d] += v
    parts_str += f'  {total_p:10.0f}'
    grand_total += total_p
    print(parts_str)
print('-' * len(header_str))
totals_str = f"{'DAY TOTAL':22s}" + ''.join((f'  {day_totals[d]:10.0f}' for d in day_list)) + f'  {grand_total:10.0f}'
print(totals_str)
print('\n=== mid-price drift per product per day (last - first) ===')
print(f"{'product':22s}" + ''.join((f"  {f'day{d}':>14s}" for d in day_list)))
for p in products_sorted:
    s = f'{p:22s}'
    for d in day_list:
        pts = mid_price_seen.get((d, p), [])
        if not pts:
            s += f"  {'--':>14s}"
            continue
        pts.sort()
        first_p = pts[0][1]
        last_p = pts[-1][1]
        drift = last_p - first_p
        s += f'  {first_p:6.1f}>{last_p:6.1f}'
    print(s)
