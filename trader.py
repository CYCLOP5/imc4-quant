from datamodel import OrderDepth, TradingState, Order
from typing import List, Dict
lim = {'EMERALDS': 80, 'TOMATOES': 80}
efv = 10000

class Trader:

    def run(self, state: TradingState):
        res: Dict[str, List[Order]] = {}
        for p in state.order_depths:
            od: OrderDepth = state.order_depths[p]
            pos = state.position.get(p, 0)
            ml = lim.get(p, 20)
            if p == 'EMERALDS':
                res[p] = self.tradem(od, pos, ml)
            elif p == 'TOMATOES':
                fv = self.wallmid(od)
                res[p] = self.tradet(od, pos, ml, fv)
        return (res, 0, '')

    def wallmid(self, od: OrderDepth) -> float:
        if not od.buy_orders or not od.sell_orders:
            return 0
        sb = sorted(od.buy_orders.items(), key=lambda x: -x[0])
        sa = sorted(od.sell_orders.items(), key=lambda x: x[0])
        wb = sb[0][0]
        mbv = sb[0][1]
        for pr, v in sb[1:]:
            if v > mbv:
                wb = pr
                mbv = v
        wa = sa[0][0]
        mav = abs(sa[0][1])
        for pr, v in sa[1:]:
            if abs(v) > mav:
                wa = pr
                mav = abs(v)
        return (wb + wa) / 2.0

    def tradem(self, od: OrderDepth, pos: int, ml: int) -> List[Order]:
        o: List[Order] = []
        br = ml - pos
        sr = ml + pos
        for ap in sorted(od.sell_orders):
            if br <= 0:
                break
            if ap <= efv:
                q = min(-od.sell_orders[ap], br)
                o.append(Order('EMERALDS', ap, q))
                br -= q
        for bp in sorted(od.buy_orders, reverse=True):
            if sr <= 0:
                break
            if bp >= efv:
                q = min(od.buy_orders[bp], sr)
                o.append(Order('EMERALDS', bp, -q))
                sr -= q
        bb = max(od.buy_orders) if od.buy_orders else efv - 8
        ba = min(od.sell_orders) if od.sell_orders else efv + 8
        pb = bb + 1
        pa = ba - 1
        if pb >= efv:
            pb = efv - 1
        if pa <= efv:
            pa = efv + 1
        if br > 0:
            o.append(Order('EMERALDS', pb, br))
        if sr > 0:
            o.append(Order('EMERALDS', pa, -sr))
        return o

    def tradet(self, od: OrderDepth, pos: int, ml: int, fv: float) -> List[Order]:
        o: List[Order] = []
        br = ml - pos
        sr = ml + pos
        for ap in sorted(od.sell_orders):
            if br <= 0:
                break
            if ap < fv:
                q = min(-od.sell_orders[ap], br)
                o.append(Order('TOMATOES', ap, q))
                br -= q
            elif ap == fv and pos < 0:
                q = min(-od.sell_orders[ap], br)
                o.append(Order('TOMATOES', ap, q))
                br -= q
        for bp in sorted(od.buy_orders, reverse=True):
            if sr <= 0:
                break
            if bp > fv:
                q = min(od.buy_orders[bp], sr)
                o.append(Order('TOMATOES', bp, -q))
                sr -= q
            elif bp == fv and pos > 0:
                q = min(od.buy_orders[bp], sr)
                o.append(Order('TOMATOES', bp, -q))
                sr -= q
        bb = max(od.buy_orders) if od.buy_orders else int(fv) - 2
        ba = min(od.sell_orders) if od.sell_orders else int(fv) + 2
        fi = int(round(fv))
        pb = bb + 1
        if pb >= fi:
            pb = fi - 1
        pa = ba - 1
        if pa <= fi:
            pa = fi + 1
        if br > 0:
            o.append(Order('TOMATOES', pb, br))
        if sr > 0:
            o.append(Order('TOMATOES', pa, -sr))
        return o
