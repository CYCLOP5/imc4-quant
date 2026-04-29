import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from datamodel import Listing, OrderDepth, TradingState, Observation
from trader import Trader
HYDRO = 'HYDROGEL_PACK'
VELVET = 'VELVETFRUIT_EXTRACT'
VEV4000 = 'VEV_4000'

def mkstate(ts, ab, aa, bb, ba, pos, td='', v4000=None):
    ls = {HYDRO: Listing(HYDRO, HYDRO, 'XIRECS'), VELVET: Listing(VELVET, VELVET, 'XIRECS')}
    od = {HYDRO: OrderDepth(buy_orders=ab, sell_orders=aa), VELVET: OrderDepth(buy_orders=bb, sell_orders=ba)}
    if v4000 is not None:
        ls[VEV4000] = Listing(VEV4000, VEV4000, 'XIRECS')
        od[VEV4000] = OrderDepth(buy_orders=v4000[0], sell_orders=v4000[1])
    return TradingState(td, ts, ls, od, {HYDRO: [], VELVET: []}, {HYDRO: [], VELVET: []}, pos, Observation())

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
lims = {HYDRO: 200, VELVET: 200, VEV4000: 300}
t = Trader()
print('t1: pos=0 init, balanced books -> MM posts both sides')
st = mkstate(0, {9992: 14, 9990: 29}, {10008: -14, 10010: -29}, {4995: 10, 4993: 20}, {5009: -10, 5011: -20}, {HYDRO: 0, VELVET: 0})
res, cv, td = t.run(st)
porders(res)
assert HYDRO in res and VELVET in res, 'must quote both products'
chklim(res, {HYDRO: 0, VELVET: 0}, lims)
print('  ok\n')
print('t2: after strong hydro drop, take fires once fv-mid divergence > edge')
t2 = Trader()
for ts in range(0, 2000, 100):
    st = mkstate(ts, {9998: 14, 9996: 29}, {10002: -14, 10004: -29}, {4995: 10, 4993: 20}, {5009: -10, 5011: -20}, {HYDRO: 0, VELVET: 0}, td=td)
    _, _, td = t2.run(st)
st = mkstate(2000, {9998: 14, 9996: 29}, {9985: -5, 10002: -14, 10004: -29}, {4995: 10, 4993: 20}, {5009: -10, 5011: -20}, {HYDRO: 0, VELVET: 0}, td=td)
res, cv, td = t2.run(st)
porders(res)
ag = [o for o in res[HYDRO] if o.quantity > 0 and o.price <= 9992]
assert len(ag) > 0, 'expected take of deeply-discounted hydro ask'
chklim(res, {HYDRO: 0, VELVET: 0}, lims)
print('  ok\n')
print('t3: pos at limit -> no excess buys/sells on that side')
t3 = Trader()
st = mkstate(200, {9992: 14, 9990: 29}, {10008: -14, 10010: -29}, {4995: 10, 4993: 20}, {5009: -10, 5011: -20}, {HYDRO: 200, VELVET: -200})
res, cv, td = t3.run(st)
porders(res)
ebt = sum((o.quantity for o in res.get(HYDRO, []) if o.quantity > 0))
tst = sum((-o.quantity for o in res.get(VELVET, []) if o.quantity < 0))
assert ebt == 0, f'hydro@+200 buys={ebt}'
assert tst == 0, f'velvet@-200 sells={tst}'
chklim(res, {HYDRO: 200, VELVET: -200}, lims)
print('  ok\n')
print('t4: eod liquidation fires at ts=995000')
t4 = Trader()
st = mkstate(995000, {9999: 40, 9992: 14}, {10008: -14}, {5000: 20}, {5010: -20}, {HYDRO: 30, VELVET: -10})
res, cv, td = t4.run(st)
porders(res)
a_sells = [o for o in res.get(HYDRO, []) if o.quantity < 0]
b_buys = [o for o in res.get(VELVET, []) if o.quantity > 0]
assert len(a_sells) > 0, 'eod: expected hydro sell orders'
assert len(b_buys) > 0, 'eod: expected velvet buy orders'
chklim(res, {HYDRO: 30, VELVET: -10}, lims)
print('  ok\n')
print('t5: VEV_4000 quotes synthetic around fv_velvet - 4000')
t5 = Trader()
td5 = ''
for ts in range(0, 2000, 100):
    st = mkstate(ts, {9992: 14, 9990: 29}, {10008: -14, 10010: -29}, {5249: 10, 5247: 20}, {5251: -10, 5253: -20}, {HYDRO: 0, VELVET: 0, VEV4000: 0}, td=td5, v4000=({1248: 15}, {1252: -15}))
    res, cv, td5 = t5.run(st)
st = mkstate(2000, {9992: 14, 9990: 29}, {10008: -14, 10010: -29}, {5249: 10, 5247: 20}, {5251: -10, 5253: -20}, {HYDRO: 0, VELVET: 0, VEV4000: 0}, td=td5, v4000=({1248: 15}, {1252: -15}))
res, cv, td5 = t5.run(st)
porders(res)
assert VEV4000 in res, 'must quote VEV_4000 when velvet fv is warm'
v4_orders = res[VEV4000]
buys = [o.price for o in v4_orders if o.quantity > 0]
sells = [o.price for o in v4_orders if o.quantity < 0]
if buys:
    assert max(buys) <= 1252, f'VEV_4000 bid too high: {buys}'
if sells:
    assert min(sells) >= 1248, f'VEV_4000 ask too low: {sells}'
chklim(res, {HYDRO: 0, VELVET: 0, VEV4000: 0}, lims)
print('  ok\n')
print('t6: state round-trip via traderData')
t6a = Trader()
st = mkstate(0, {9992: 14}, {10008: -14}, {5249: 10}, {5251: -10}, {HYDRO: 0, VELVET: 0})
_, _, td = t6a.run(st)
assert td, 'traderData must be non-empty after run'
t6b = Trader()
st2 = mkstate(100, {9992: 14}, {10008: -14}, {5249: 10}, {5251: -10}, {HYDRO: 0, VELVET: 0}, td=td)
_, _, _ = t6b.run(st2)
assert t6b.fv_h > 0 and t6b.fv_v > 0, 'state did not deserialize'
assert t6b.slow_fv_v > 0, 'slow_fv_v did not deserialize'
print(f'  fv_h={t6b.fv_h:.2f} fv_v={t6b.fv_v:.2f} slow_fv_v={t6b.slow_fv_v:.2f}')
print('  ok\n')
print('t7: smile MM posts quotes on VEV_5000 (spread=6)')
t7 = Trader()
from datamodel import Listing as _Listing, OrderDepth as _OD, TradingState as _TS, Observation as _Obs
ls = {HYDRO: _Listing(HYDRO, HYDRO, 'XIRECS'), VELVET: _Listing(VELVET, VELVET, 'XIRECS'), 'VEV_5000': _Listing('VEV_5000', 'VEV_5000', 'XIRECS')}
od = {HYDRO: _OD(buy_orders={9998: 14}, sell_orders={10002: -14}), VELVET: _OD(buy_orders={5249: 10}, sell_orders={5251: -10}), 'VEV_5000': _OD(buy_orders={264: 20}, sell_orders={270: -20})}
pos = {HYDRO: 0, VELVET: 0, 'VEV_5000': 0}
td7 = ''
for ts in range(0, 500, 100):
    st7 = _TS(td7, ts, ls, od, {k: [] for k in ls}, {k: [] for k in ls}, pos, _Obs())
    _, _, td7 = t7.run(st7)
st7 = _TS(td7, 500, ls, od, {k: [] for k in ls}, {k: [] for k in ls}, pos, _Obs())
res7, _, _ = t7.run(st7)
v5000_orders = res7.get('VEV_5000', [])
print(f'  VEV_5000: {len(v5000_orders)} orders')
assert len(v5000_orders) >= 1, 'smile MM should post on VEV_5000 (sp=6 MM-able)'
buys = [o for o in v5000_orders if o.quantity > 0]
if buys:
    assert max((o.price for o in buys)) >= 265, f'smile bid should improve (>=265): {[o.price for o in buys]}'
print('  ok\n')
print('t8: OTM pinned voucher (VEV_6000) posts at best quotes')
t8 = Trader()
ls8 = {HYDRO: _Listing(HYDRO, HYDRO, 'XIRECS'), VELVET: _Listing(VELVET, VELVET, 'XIRECS'), 'VEV_6000': _Listing('VEV_6000', 'VEV_6000', 'XIRECS')}
od8 = {HYDRO: _OD(buy_orders={9998: 14}, sell_orders={10002: -14}), VELVET: _OD(buy_orders={5249: 10}, sell_orders={5251: -10}), 'VEV_6000': _OD(buy_orders={0: 22}, sell_orders={1: -22})}
pos8 = {HYDRO: 0, VELVET: 0, 'VEV_6000': 0}
st8 = _TS('', 0, ls8, od8, {k: [] for k in ls8}, {k: [] for k in ls8}, pos8, _Obs())
res8, _, _ = t8.run(st8)
v6000_orders = res8.get('VEV_6000', [])
print(f'  VEV_6000: {len(v6000_orders)} orders')
assert len(v6000_orders) == 2, f'OTM pinned should post 2 orders (buy at 0, sell at 1), got {len(v6000_orders)}'
buys = [o for o in v6000_orders if o.quantity > 0]
sells = [o for o in v6000_orders if o.quantity < 0]
assert buys and buys[0].price == 0, 'OTM buy should be at 0'
assert sells and sells[0].price == 1, 'OTM sell should be at 1'
print('  ok\n')
print('all pass')
