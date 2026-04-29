import json
from typing import List, Dict
from datamodel import OrderDepth, TradingState, Order
lim = {'ASH_COATED_OSMIUM': 80, 'INTARIAN_PEPPER_ROOT': 80}
efv = 10000

class Trader:

    def run(self, state: TradingState):
        o: Dict[str, List[Order]] = {}
        for prod in state.order_depths:
            if prod == 'ASH_COATED_OSMIUM':
                ol = self.trade_aco(state.order_depths[prod], state.position.get(prod, 0), lim[prod])
                if ol:
                    o[prod] = ol
            elif prod == 'INTARIAN_PEPPER_ROOT':
                fv = self.wallmid(state.order_depths[prod])
                ol = self.trade_ipr(state.order_depths[prod], state.position.get(prod, 0), lim[prod], fv)
                if ol:
                    o[prod] = ol
        return (o, 0, '')

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

    def trade_aco(self, od: OrderDepth, pos: int, ml: int) -> List[Order]:
        o: List[Order] = []
        br = ml - pos
        sr = ml + pos
        for ap in sorted(od.sell_orders):
            if br <= 0:
                break
            if ap < efv:
                q = min(-od.sell_orders[ap], br)
                o.append(Order('ASH_COATED_OSMIUM', ap, q))
                br -= q
        for bp in sorted(od.buy_orders, reverse=True):
            if sr <= 0:
                break
            if bp > efv:
                q = min(od.buy_orders[bp], sr)
                o.append(Order('ASH_COATED_OSMIUM', bp, -q))
                sr -= q
        bb = max(od.buy_orders) if od.buy_orders else efv - 8
        ba = min(od.sell_orders) if od.sell_orders else efv + 8
        edge = 2
        ideal_bid = efv - edge
        ideal_ask = efv + edge
        pb = min(ideal_bid, bb + 1)
        pa = max(ideal_ask, ba - 1)
        if br > 0:
            o.append(Order('ASH_COATED_OSMIUM', pb, br))
        if sr > 0:
            o.append(Order('ASH_COATED_OSMIUM', pa, -sr))
        return o

    def trade_ipr(self, od: OrderDepth, pos: int, ml: int, fv: float) -> List[Order]:
        o: List[Order] = []
        br = max(0, 76 - pos)
        sr = max(0, 76 + pos)
        if not od.buy_orders or not od.sell_orders:
            return o
        for ap in sorted(od.sell_orders):
            if br <= 0:
                break
            if ap < fv:
                q = min(-od.sell_orders[ap], br)
                o.append(Order('INTARIAN_PEPPER_ROOT', ap, q))
                br -= q
            elif ap == fv and pos < 0:
                q = min(-od.sell_orders[ap], br)
                o.append(Order('INTARIAN_PEPPER_ROOT', ap, q))
                br -= q
        for bp in sorted(od.buy_orders, reverse=True):
            if sr <= 0:
                break
            if bp > fv:
                q = min(od.buy_orders[bp], sr)
                o.append(Order('INTARIAN_PEPPER_ROOT', bp, -q))
                sr -= q
            elif bp == fv and pos > 0:
                q = min(od.buy_orders[bp], sr)
                o.append(Order('INTARIAN_PEPPER_ROOT', bp, -q))
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
            o.append(Order('INTARIAN_PEPPER_ROOT', pb, br))
        if sr > 0:
            o.append(Order('INTARIAN_PEPPER_ROOT', pa, -sr))
        return o
