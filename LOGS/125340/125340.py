from datamodel import OrderDepth, TradingState, Order
import json
from typing import List, Dict
lim = {'ASH_COATED_OSMIUM': 80, 'INTARIAN_PEPPER_ROOT': 80}
efv = 10000

class Trader:

    def __init__(self):
        self.k_p = 0.0
        self.k_v = 0.0
        self.k_p00 = 1.0
        self.k_p01 = 0.0
        self.k_p10 = 0.0
        self.k_p11 = 1.0
        self.k_q00 = 0.1
        self.k_q01 = 0.0
        self.k_q10 = 0.0
        self.k_q11 = 0.01
        self.k_r = 2.0

    def run(self, state: TradingState):
        o: Dict[str, List[Order]] = {}
        if state.traderData:
            try:
                td = json.loads(state.traderData)
                self.k_p = td.get('k_p', 0.0)
                self.k_v = td.get('k_v', 0.0)
                self.k_p00 = td.get('k_p00', 1.0)
                self.k_p01 = td.get('k_p01', 0.0)
                self.k_p10 = td.get('k_p10', 0.0)
                self.k_p11 = td.get('k_p11', 1.0)
            except:
                pass
        td_out = {'k_p': self.k_p, 'k_v': self.k_v, 'k_p00': self.k_p00, 'k_p01': self.k_p01, 'k_p10': self.k_p10, 'k_p11': self.k_p11}
        for prod in state.order_depths:
            if prod == 'ASH_COATED_OSMIUM':
                ol = self.trade_aco(state.order_depths[prod], state.position.get(prod, 0), lim[prod])
                if ol:
                    o[prod] = ol
            elif prod == 'INTARIAN_PEPPER_ROOT':
                ol = self.trade_ipr(state.order_depths[prod], state.position.get(prod, 0), lim[prod])
                if ol:
                    o[prod] = ol
                td_out['k_p'] = self.k_p
                td_out['k_v'] = self.k_v
                td_out['k_p00'] = self.k_p00
                td_out['k_p01'] = self.k_p01
                td_out['k_p10'] = self.k_p10
                td_out['k_p11'] = self.k_p11
        return (o, 0, json.dumps(td_out))

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
        edge = 1
        ideal_bid = efv - edge
        ideal_ask = efv + edge
        pb = min(ideal_bid, bb + 1)
        pa = max(ideal_ask, ba - 1)
        if ba - bb > 4 and br > 0:
            inner_qty = min(br // 2, 15)
            if inner_qty > 0:
                o.append(Order('ASH_COATED_OSMIUM', efv - 1, inner_qty))
                br -= inner_qty
        if ba - bb > 4 and sr > 0:
            inner_qty = min(sr // 2, 15)
            if inner_qty > 0:
                o.append(Order('ASH_COATED_OSMIUM', efv + 1, -inner_qty))
                sr -= inner_qty
        if br > 0:
            o.append(Order('ASH_COATED_OSMIUM', pb, br))
        if sr > 0:
            o.append(Order('ASH_COATED_OSMIUM', pa, -sr))
        return o

    def trade_ipr(self, od: OrderDepth, pos: int, ml: int) -> List[Order]:
        o: List[Order] = []
        br = ml - pos
        sr = ml + pos
        if not od.buy_orders or not od.sell_orders:
            return o
        best_bid = max(od.buy_orders.keys())
        best_ask = min(od.sell_orders.keys())
        mid = (best_bid + best_ask) / 2.0
        if self.k_p == 0.0:
            self.k_p = mid
        p_pred = self.k_p + self.k_v
        v_pred = self.k_v
        P00_pred = self.k_p00 + self.k_p10 + self.k_p01 + self.k_p11 + self.k_q00
        P01_pred = self.k_p01 + self.k_p11 + self.k_q01
        P10_pred = self.k_p10 + self.k_p11 + self.k_q10
        P11_pred = self.k_p11 + self.k_q11
        y = mid - p_pred
        S = P00_pred + self.k_r
        K0 = P00_pred / S
        K1 = P10_pred / S
        self.k_p = p_pred + K0 * y
        self.k_v = v_pred + K1 * y
        self.k_p00 = P00_pred - K0 * P00_pred
        self.k_p01 = P01_pred - K0 * P01_pred
        self.k_p10 = P10_pred - K1 * P00_pred
        self.k_p11 = P11_pred - K1 * P01_pred
        predicted_future = p_pred + v_pred * 8.0
        take_thresh = 0.5 + abs(pos) / 80.0 * 4.0
        if predicted_future > best_ask + take_thresh:
            for p in sorted(od.sell_orders):
                if br > 0 and p < predicted_future:
                    q = min(-od.sell_orders[p], br)
                    o.append(Order('INTARIAN_PEPPER_ROOT', p, q))
                    br -= q
                else:
                    break
        if predicted_future < best_bid - take_thresh:
            for p in sorted(od.buy_orders, reverse=True):
                if sr > 0 and p > predicted_future:
                    q = min(od.buy_orders[p], sr)
                    o.append(Order('INTARIAN_PEPPER_ROOT', p, -q))
                    sr -= q
                else:
                    break
        adj_mid = predicted_future - pos / 80.0 * 8.0
        edge = 2 + int(abs(pos) / 30)
        ideal_bid = int(adj_mid - edge)
        ideal_ask = int(adj_mid + edge)
        pb = min(ideal_bid, best_bid + 1)
        pa = max(ideal_ask, best_ask - 1)
        passive_cap = 70
        passive_br = max(0, passive_cap - pos) if pos > 0 else br
        passive_sr = max(0, passive_cap + pos) if pos < 0 else sr
        if passive_br > 0:
            o.append(Order('INTARIAN_PEPPER_ROOT', pb, passive_br))
        if passive_sr > 0:
            o.append(Order('INTARIAN_PEPPER_ROOT', pa, -passive_sr))
        return o
