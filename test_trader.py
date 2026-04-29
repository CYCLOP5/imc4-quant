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
print('t7 (v6): smile MM posts quotes on VEV_5300 (active in v6)')
t7 = Trader()
from datamodel import Listing as _Listing, OrderDepth as _OD, TradingState as _TS, Observation as _Obs
ls = {HYDRO: _Listing(HYDRO, HYDRO, 'XIRECS'), VELVET: _Listing(VELVET, VELVET, 'XIRECS'), 'VEV_5300': _Listing('VEV_5300', 'VEV_5300', 'XIRECS')}
od = {HYDRO: _OD(buy_orders={9998: 14}, sell_orders={10002: -14}), VELVET: _OD(buy_orders={5249: 10}, sell_orders={5251: -10}), 'VEV_5300': _OD(buy_orders={56: 20}, sell_orders={62: -20})}
pos = {HYDRO: 0, VELVET: 0, 'VEV_5300': 0}
td7 = ''
for ts in range(0, 500, 100):
    st7 = _TS(td7, ts, ls, od, {k: [] for k in ls}, {k: [] for k in ls}, pos, _Obs())
    _, _, td7 = t7.run(st7)
st7 = _TS(td7, 500, ls, od, {k: [] for k in ls}, {k: [] for k in ls}, pos, _Obs())
res7, _, _ = t7.run(st7)
v5300_orders = res7.get('VEV_5300', [])
print(f'  VEV_5300: {len(v5300_orders)} orders')
assert len(v5300_orders) >= 1, 'smile MM should post on VEV_5300 (active in v6)'
print('  ok\n')
print('t8 (v6): SKIP_PRODUCTS yields no orders for VEV_6000 / VEV_6500')
t8 = Trader()
for skip_sym in ('VEV_6000', 'VEV_6500'):
    ls8 = {HYDRO: _Listing(HYDRO, HYDRO, 'XIRECS'), VELVET: _Listing(VELVET, VELVET, 'XIRECS'), skip_sym: _Listing(skip_sym, skip_sym, 'XIRECS')}
    skip_od = _OD(buy_orders={0: 22}, sell_orders={1: -22})
    od8 = {HYDRO: _OD(buy_orders={9998: 14}, sell_orders={10002: -14}), VELVET: _OD(buy_orders={5249: 10}, sell_orders={5251: -10}), skip_sym: skip_od}
    pos8 = {HYDRO: 0, VELVET: 0, skip_sym: 0}
    st8 = _TS('', 0, ls8, od8, {k: [] for k in ls8}, {k: [] for k in ls8}, pos8, _Obs())
    res8, _, _ = t8.run(st8)
    skip_orders = res8.get(skip_sym, [])
    print(f'  {skip_sym}: {len(skip_orders)} orders (expected 0)')
    assert len(skip_orders) == 0, f'{skip_sym} is in SKIP_PRODUCTS but produced orders'
print('  ok\n')
print('t9 (v6): queue-jumper posts size-1 ping inside main MM on HYDRO')
t9 = Trader()
td9 = ''
for ts in range(0, 1000, 100):
    st9 = mkstate(ts, {9998: 14, 9996: 29}, {10002: -14, 10004: -29}, {5249: 10, 5247: 20}, {5251: -10, 5253: -20}, {HYDRO: 0, VELVET: 0}, td=td9)
    _, _, td9 = t9.run(st9)
st9 = mkstate(1000, {9990: 14, 9988: 29}, {10010: -14, 10012: -29}, {5249: 10, 5247: 20}, {5251: -10, 5253: -20}, {HYDRO: 0, VELVET: 0}, td=td9)
res9, _, _ = t9.run(st9)
porders(res9)
hydro_orders = res9.get(HYDRO, [])
buys = sorted([o for o in hydro_orders if o.quantity > 0], key=lambda o: o.price)
sells = sorted([o for o in hydro_orders if o.quantity < 0], key=lambda o: -o.price)
print(f'  buys: {[(o.price, o.quantity) for o in buys]}')
print(f'  sells: {[(o.price, o.quantity) for o in sells]}')
assert len(buys) >= 2, 'expected main MM buy + jumper buy'
assert len(sells) >= 2, 'expected main MM sell + jumper sell'
jumper_buys = [o for o in buys if o.quantity == 1]
jumper_sells = [o for o in sells if o.quantity == -1]
assert len(jumper_buys) >= 1 and len(jumper_sells) >= 1, 'expected size-1 jumper pings'
chklim(res9, {HYDRO: 0, VELVET: 0}, lims)
print('  ok\n')
print('t10 (v6): cp_nudge_v rises when Mark 67 buys VELVET (informed buyer signal)')
print('  (counterparty branch is GATED OFF in v6.1; i toggle it on for this test)')
from datamodel import Trade as _Trade
import trader as _trader_mod
_old_cp = _trader_mod.COUNTERPARTY_ENABLED
_trader_mod.COUNTERPARTY_ENABLED = True
try:
    t10 = Trader()
    ls10 = {HYDRO: _Listing(HYDRO, HYDRO, 'XIRECS'), VELVET: _Listing(VELVET, VELVET, 'XIRECS')}
    od10 = {HYDRO: _OD(buy_orders={9998: 14}, sell_orders={10002: -14}), VELVET: _OD(buy_orders={5249: 10}, sell_orders={5251: -10})}
    mt = {HYDRO: [], VELVET: [_Trade('VELVETFRUIT_EXTRACT', 5250, 10, buyer='Mark 67', seller='Mark 14', timestamp=100)]}
    pos10 = {HYDRO: 0, VELVET: 0}
    st10 = _TS('', 100, ls10, od10, {k: [] for k in ls10}, mt, pos10, _Obs())
    _, _, td10 = t10.run(st10)
    print(f'  cp_nudge_v after Mark 67 buy: {t10.cp_nudge_v:+.3f} (should be > 0)')
    assert t10.cp_nudge_v > 0, 'Mark 67 informed buy should raise cp_nudge_v'
finally:
    _trader_mod.COUNTERPARTY_ENABLED = _old_cp
print('  ok\n')
print('all pass')
