import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from datamodel import Listing, OrderDepth, Trade, TradingState, Observation
from trader import Trader

def mkstate(ts, eb, ea, tb, ta, pos, td=''):
    ls = {'EMERALDS': Listing('EMERALDS', 'EMERALDS', 'XIRECS'), 'TOMATOES': Listing('TOMATOES', 'TOMATOES', 'XIRECS')}
    od = {'EMERALDS': OrderDepth(buy_orders=eb, sell_orders=ea), 'TOMATOES': OrderDepth(buy_orders=tb, sell_orders=ta)}
    return TradingState(td, ts, ls, od, {'EMERALDS': [], 'TOMATOES': []}, {'EMERALDS': [], 'TOMATOES': []}, pos, Observation())

def porders(res):
    for p, ords in res.items():
        buys = [(o.price, o.quantity) for o in ords if o.quantity > 0]
        sells = [(o.price, -o.quantity) for o in ords if o.quantity < 0]
        tb = sum((q for _, q in buys))
        ts = sum((q for _, q in sells))
        print(f'  {p}: {len(buys)}b({tb}) {len(sells)}s({ts})')
        for pr, q in sorted(buys, key=lambda x: x[0]):
            print(f'    b {q}x@{pr}')
        for pr, q in sorted(sells, key=lambda x: -x[0]):
            print(f'    s {q}x@{pr}')

def chklim(res, pos, lims):
    for p, ords in res.items():
        ps = pos.get(p, 0)
        ml = lims[p]
        tb = sum((o.quantity for o in ords if o.quantity > 0))
        ts = sum((-o.quantity for o in ords if o.quantity < 0))
        assert ps + tb <= ml, f'{p} long ovf: {ps}+{tb}>{ml}'
        assert ps - ts >= -ml, f'{p} short ovf: {ps}-{ts}<{-ml}'
ml = {'EMERALDS': 80, 'TOMATOES': 80}
t = Trader()
print('t1: pos=0 init')
st = mkstate(0, {9992: 14, 9990: 29}, {10008: -14, 10010: -29}, {4995: 10, 4993: 20}, {5009: -10, 5011: -20}, {'EMERALDS': 0, 'TOMATOES': 0})
res, cv, td = t.run(st)
porders(res)
chklim(res, {'EMERALDS': 0, 'TOMATOES': 0}, ml)
print('  ok\n')
print('t2: em ask<fv')
st = mkstate(100, {9992: 14, 9990: 29}, {9998: -5, 10008: -14, 10010: -29}, {4995: 10, 4993: 20}, {5009: -10, 5011: -20}, {'EMERALDS': 0, 'TOMATOES': 0})
res, cv, td = t.run(st)
porders(res)
eb = [o for o in res['EMERALDS'] if o.quantity > 0]
ag = [o for o in eb if o.price == 9998]
assert len(ag) > 0, 'no take @9998'
assert ag[0].quantity == 5, f'exp 5 @9998, got {ag[0].quantity}'
chklim(res, {'EMERALDS': 0, 'TOMATOES': 0}, ml)
print('  ok\n')
print('t3: pos@lim')
st = mkstate(200, {9992: 14, 9990: 29}, {10008: -14, 10010: -29}, {4995: 10, 4993: 20}, {5009: -10, 5011: -20}, {'EMERALDS': 80, 'TOMATOES': -80})
res, cv, td = t.run(st)
porders(res)
ebt = sum((o.quantity for o in res['EMERALDS'] if o.quantity > 0))
tst = sum((-o.quantity for o in res['TOMATOES'] if o.quantity < 0))
assert ebt == 0, f'em@+80 buys={ebt}'
assert tst == 0, f'tm@-80 sells={tst}'
chklim(res, {'EMERALDS': 80, 'TOMATOES': -80}, ml)
print('  ok\n')
print('t4: flatten@fv')
st = mkstate(300, {9999: 5, 9992: 14, 9990: 29}, {10000: -5, 10008: -14, 10010: -29}, {4995: 10, 4993: 20}, {5009: -10, 5011: -20}, {'EMERALDS': 30, 'TOMATOES': 0})
res, cv, td = t.run(st)
porders(res)
esf = [o for o in res['EMERALDS'] if o.quantity < 0 and o.price == 10000]
print(f'  sell@10k: {esf}')
chklim(res, {'EMERALDS': 30, 'TOMATOES': 0}, ml)
print('  ok\n')
print('t5: aggr both sides')
st = mkstate(400, {10005: 10, 9992: 14, 9990: 29}, {9995: -8, 10008: -14, 10010: -29}, {5010: 5, 4995: 10, 4993: 20}, {4990: -5, 5009: -10, 5011: -20}, {'EMERALDS': 0, 'TOMATOES': 0})
res, cv, td = t.run(st)
porders(res)
eab = [o for o in res['EMERALDS'] if o.quantity > 0 and o.price == 9995]
eas = [o for o in res['EMERALDS'] if o.quantity < 0 and o.price == 10005]
assert len(eab) > 0, 'no buy@9995'
assert len(eas) > 0, 'no sell@10005'
chklim(res, {'EMERALDS': 0, 'TOMATOES': 0}, ml)
print('  ok\n')
print('all pass')
