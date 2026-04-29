import json
from typing import Dict, List
from datamodel import OrderDepth, TradingState, Order
HYDRO = 'HYDROGEL_PACK'
VELVET = 'VELVETFRUIT_EXTRACT'
DEEP_ITM_STRIKES = {'VEV_4000': 4000, 'VEV_4500': 4500}
SMILE_STRIKES = {'VEV_5000': 5000, 'VEV_5100': 5100, 'VEV_5200': 5200, 'VEV_5300': 5300, 'VEV_5400': 5400, 'VEV_5500': 5500}
SKIP_PRODUCTS = {'VEV_6000', 'VEV_6500'}
ALL_VOUCHERS = list(DEEP_ITM_STRIKES) + list(SMILE_STRIKES) + ['VEV_6000', 'VEV_6500']
PRODUCTS = [HYDRO, VELVET] + ALL_VOUCHERS
LIMITS = {HYDRO: 200, VELVET: 200, **{v: 300 for v in ALL_VOUCHERS}}
FV_ALPHA_HYDRO = 0.05
FV_ALPHA_VELVET = 0.1
PREM_ALPHA = 0.05
PREM_VAR_ALPHA = 0.02
HYDRO_BUY_EDGE = 8
HYDRO_SELL_EDGE = 15
HYDRO_MAKE_EDGE = 1.0
HYDRO_SKEW = 4.0
HYDRO_INV_BIAS = 8
VELVET_INV_BIAS = 2
VELVET_TAKE_THRESH = 2.5
VELVET_MAKE_EDGE = 2.0
VELVET_SKEW = 0.0
DEEP_ITM_TAKE_EDGE = 1.0
DEEP_ITM_MAKE_EDGE = 2.0
DEEP_ITM_SKEW = 2.0
SMILE_Z_TAKE = 999.0
SMILE_MAKE_EDGE = 1.0
SMILE_SKEW = 2.0
SMILE_VAR_FLOOR = 0.25
SMILE_MAKE_ENABLED = True
FLOW_ALPHA = 0.1
FLOW_BETA = 0.0
IMB_SHADE = 0.0
IMB_THRESH = 0.4
LAYERED_MM = False
LAYER_FRACS = (1.0,)
LAYER_OFFSETS = (0,)
TREND_ALPHA_VELVET = 0.0001
TREND_ALPHA_HYDRO = 0.0007
TREND_BETA = -0.15
HYDRO_TREND_BETA = -0.35
DEEP_ITM_TREND_BETA = -0.25
TREND_CLIP = 20.0
COUNTERPARTY_ENABLED = False
COUNTERPARTY_ALPHA = 0.001
COUNTERPARTY_CLIP = 4.0
CP_WEIGHT_INFORMED = 1.0
CP_WEIGHT_FADE = 0.5
INFORMED_BUYERS_VELVET = {'Mark 67'}
NOISE_SELLERS_VELVET = {'Mark 22', 'Mark 49'}
QUEUE_JUMPER_ENABLED = True
QUEUE_JUMPER_SIZE = 1
QUEUE_JUMPER_SYMBOLS = {HYDRO, 'VEV_4000'}
EOD_TS = 995000

class Trader:

    def __init__(self):
        self.fv_h: float = 0.0
        self.fv_v: float = 0.0
        self.slow_fv_h: float = 0.0
        self.slow_fv_v: float = 0.0
        self.prem_ema: Dict[str, float] = {}
        self.prem_var_ema: Dict[str, float] = {}
        self.flow_v: float = 0.0
        self.last_mid: Dict[str, float] = {}
        self.cp_nudge_v: float = 0.0
        self.last_seen_ts_v: int = -1

    def bid(self) -> int:
        return 0

    def run(self, state: TradingState):
        self._load_state(state.traderData)
        orders: Dict[str, List[Order]] = {}
        if state.timestamp >= EOD_TS:
            self._eod_liquidation(state, orders)
            return (orders, 0, self._dump_state())
        velvet_mid = self._mid(state.order_depths.get(VELVET))
        if velvet_mid is not None:
            self.fv_v = self._ema_update(self.fv_v, velvet_mid, FV_ALPHA_VELVET)
            self.slow_fv_v = self._ema_update(self.slow_fv_v, velvet_mid, TREND_ALPHA_VELVET)
        flow_obs = 0.0
        prev_mid_v = self.last_mid.get(VELVET)
        if prev_mid_v is not None:
            vtrades = state.market_trades.get(VELVET, []) if state.market_trades else []
            for tr in vtrades:
                if tr.price > prev_mid_v:
                    flow_obs += tr.quantity
                elif tr.price < prev_mid_v:
                    flow_obs -= tr.quantity
        self.flow_v = (1 - FLOW_ALPHA) * self.flow_v + FLOW_ALPHA * flow_obs
        if COUNTERPARTY_ENABLED:
            self.cp_nudge_v *= 1.0 - COUNTERPARTY_ALPHA
            vtrades = state.market_trades.get(VELVET, []) if state.market_trades else []
            for tr in vtrades:
                buyer = getattr(tr, 'buyer', None)
                seller = getattr(tr, 'seller', None)
                if buyer in INFORMED_BUYERS_VELVET:
                    self.cp_nudge_v += CP_WEIGHT_INFORMED * tr.quantity
                if seller in NOISE_SELLERS_VELVET:
                    self.cp_nudge_v += CP_WEIGHT_FADE * tr.quantity
            self.cp_nudge_v = max(-COUNTERPARTY_CLIP, min(COUNTERPARTY_CLIP, self.cp_nudge_v))
            self.last_seen_ts_v = state.timestamp
        if velvet_mid is not None:
            self.last_mid[VELVET] = velvet_mid
        od_h = state.order_depths.get(HYDRO)
        if od_h is not None:
            h_mid = self._mid(od_h)
            if h_mid is not None:
                self.fv_h = self._ema_update(self.fv_h, h_mid, FV_ALPHA_HYDRO)
                self.slow_fv_h = self._ema_update(self.slow_fv_h, h_mid, TREND_ALPHA_HYDRO)
            ol = self._trade_hydro(od_h, state.position.get(HYDRO, 0))
            if ol:
                orders[HYDRO] = ol
        od_v = state.order_depths.get(VELVET)
        if od_v is not None and velvet_mid is not None:
            ol = self._trade_velvet(od_v, state.position.get(VELVET, 0))
            if ol:
                orders[VELVET] = ol
        if self.fv_v > 0:
            for name, K in DEEP_ITM_STRIKES.items():
                if name in SKIP_PRODUCTS:
                    continue
                od = state.order_depths.get(name)
                if od is None:
                    continue
                ol = self._trade_deep_itm(name, K, od, state.position.get(name, 0))
                if ol:
                    orders[name] = ol
        if velvet_mid is not None:
            for name, K in SMILE_STRIKES.items():
                if name in SKIP_PRODUCTS:
                    continue
                od = state.order_depths.get(name)
                if od is None:
                    continue
                ol = self._trade_smile(name, K, od, state.position.get(name, 0), velvet_mid)
                if ol:
                    orders[name] = ol
        return (orders, 0, self._dump_state())

    def _trade_hydro(self, od: OrderDepth, pos: int) -> List[Order]:
        ml = LIMITS[HYDRO]
        br = ml - pos
        sr = ml + pos
        o: List[Order] = []
        if self.fv_h <= 0:
            return o
        trend_h = self.fv_h - self.slow_fv_h if self.slow_fv_h > 0 else 0.0
        trend_nudge = max(-TREND_CLIP, min(TREND_CLIP, HYDRO_TREND_BETA * trend_h))
        fv = self.fv_h + trend_nudge
        inv_frac = pos / ml
        floor = 0.6
        if abs(inv_frac) > floor:
            s = 1 if inv_frac > 0 else -1
            eff = s * ((abs(inv_frac) - floor) / (1.0 - floor)) * HYDRO_INV_BIAS
        else:
            eff = 0.0
        be_eff = HYDRO_BUY_EDGE + eff
        se_eff = HYDRO_SELL_EDGE - eff
        for ap in sorted(od.sell_orders):
            if br <= 0:
                break
            if ap <= fv - be_eff:
                q = min(-od.sell_orders[ap], br)
                if q > 0:
                    o.append(Order(HYDRO, ap, q))
                    br -= q
            else:
                break
        for bp in sorted(od.buy_orders, reverse=True):
            if sr <= 0:
                break
            if bp >= fv + se_eff:
                q = min(od.buy_orders[bp], sr)
                if q > 0:
                    o.append(Order(HYDRO, bp, -q))
                    sr -= q
            else:
                break
        if not od.buy_orders or not od.sell_orders:
            return o
        bb = max(od.buy_orders)
        ba = min(od.sell_orders)
        adj = fv - pos / ml * HYDRO_SKEW
        pb = min(int(adj - HYDRO_MAKE_EDGE), bb + 1)
        pa = max(int(adj + HYDRO_MAKE_EDGE + 0.5), ba - 1)
        br_main, sr_main, jb, ja = self._allocate_jumper(HYDRO, br, sr, pb, pa, bb, ba, fv)
        o.extend(self._layer_orders(HYDRO, 'B', pb, br_main, bb, ba))
        o.extend(self._layer_orders(HYDRO, 'S', pa, sr_main, bb, ba))
        if jb is not None:
            o.append(Order(HYDRO, jb[0], jb[1]))
        if ja is not None:
            o.append(Order(HYDRO, ja[0], ja[1]))
        return o

    def _trade_velvet(self, od: OrderDepth, pos: int) -> List[Order]:
        ml = LIMITS[VELVET]
        br = ml - pos
        sr = ml + pos
        o: List[Order] = []
        if self.fv_v <= 0 or not od.buy_orders or (not od.sell_orders):
            return o
        trend = self.fv_v - self.slow_fv_v if self.slow_fv_v > 0 else 0.0
        trend_nudge = max(-TREND_CLIP, min(TREND_CLIP, TREND_BETA * trend))
        flow_nudge = max(-2.0, min(2.0, FLOW_BETA * self.flow_v))
        cp_nudge = self.cp_nudge_v if COUNTERPARTY_ENABLED else 0.0
        fv = self.fv_v + trend_nudge + flow_nudge + cp_nudge
        inv_frac = pos / ml
        floor = 0.6
        if abs(inv_frac) > floor:
            s = 1 if inv_frac > 0 else -1
            eff_v = s * ((abs(inv_frac) - floor) / (1.0 - floor)) * VELVET_INV_BIAS
        else:
            eff_v = 0.0
        buy_thresh = VELVET_TAKE_THRESH + eff_v
        sell_thresh = VELVET_TAKE_THRESH - eff_v
        for ap in sorted(od.sell_orders):
            if br <= 0:
                break
            if ap <= fv - buy_thresh:
                q = min(-od.sell_orders[ap], br)
                if q > 0:
                    o.append(Order(VELVET, ap, q))
                    br -= q
            else:
                break
        for bp in sorted(od.buy_orders, reverse=True):
            if sr <= 0:
                break
            if bp >= fv + sell_thresh:
                q = min(od.buy_orders[bp], sr)
                if q > 0:
                    o.append(Order(VELVET, bp, -q))
                    sr -= q
            else:
                break
        bb = max(od.buy_orders)
        ba = min(od.sell_orders)
        bv = od.buy_orders.get(bb, 0)
        av = -od.sell_orders.get(ba, 0)
        imb = 0.0
        if bv + av > 0:
            imb = (bv - av) / (bv + av)
        shade = 0.0
        if abs(imb) >= IMB_THRESH:
            shade = imb * IMB_SHADE
        adj = fv + shade - pos / ml * VELVET_SKEW
        pb = min(int(adj - VELVET_MAKE_EDGE), bb + 1)
        pa = max(int(adj + VELVET_MAKE_EDGE + 0.5), ba - 1)
        o.extend(self._layer_orders(VELVET, 'B', pb, br, bb, ba))
        o.extend(self._layer_orders(VELVET, 'S', pa, sr, bb, ba))
        return o

    def _trade_deep_itm(self, name: str, K: int, od: OrderDepth, pos: int) -> List[Order]:
        ml = LIMITS[name]
        br = ml - pos
        sr = ml + pos
        o: List[Order] = []
        if not od.buy_orders or not od.sell_orders:
            return o
        trend_v = self.fv_v - self.slow_fv_v if self.slow_fv_v > 0 else 0.0
        trend_nudge_v = max(-TREND_CLIP, min(TREND_CLIP, DEEP_ITM_TREND_BETA * trend_v))
        voucher_fv = self.fv_v + trend_nudge_v - K
        if voucher_fv <= 0:
            return o
        for ap in sorted(od.sell_orders):
            if br <= 0:
                break
            if ap <= voucher_fv - DEEP_ITM_TAKE_EDGE:
                q = min(-od.sell_orders[ap], br)
                if q > 0:
                    o.append(Order(name, ap, q))
                    br -= q
            else:
                break
        for bp in sorted(od.buy_orders, reverse=True):
            if sr <= 0:
                break
            if bp >= voucher_fv + DEEP_ITM_TAKE_EDGE:
                q = min(od.buy_orders[bp], sr)
                if q > 0:
                    o.append(Order(name, bp, -q))
                    sr -= q
            else:
                break
        bb = max(od.buy_orders)
        ba = min(od.sell_orders)
        adj = voucher_fv - pos / ml * DEEP_ITM_SKEW
        pb = min(int(adj - DEEP_ITM_MAKE_EDGE), bb + 1)
        pa = max(int(adj + DEEP_ITM_MAKE_EDGE + 0.5), ba - 1)
        br_main, sr_main, jb, ja = self._allocate_jumper(name, br, sr, pb, pa, bb, ba, voucher_fv)
        o.extend(self._layer_orders(name, 'B', pb, br_main, bb, ba))
        o.extend(self._layer_orders(name, 'S', pa, sr_main, bb, ba))
        if jb is not None:
            o.append(Order(name, jb[0], jb[1]))
        if ja is not None:
            o.append(Order(name, ja[0], ja[1]))
        return o

    def _trade_smile(self, name: str, K: int, od: OrderDepth, pos: int, S: float) -> List[Order]:
        ml = LIMITS[name]
        br = ml - pos
        sr = ml + pos
        o: List[Order] = []
        if not od.buy_orders or not od.sell_orders:
            return o
        bb = max(od.buy_orders)
        ba = min(od.sell_orders)
        mid = (bb + ba) / 2.0
        trend_v = self.fv_v - self.slow_fv_v if self.slow_fv_v > 0 else 0.0
        trend_nudge_v = max(-TREND_CLIP, min(TREND_CLIP, TREND_BETA * trend_v))
        S_adj = self.fv_v + trend_nudge_v if self.fv_v > 0 else S
        intrinsic = max(0.0, S_adj - K)
        prem = mid - intrinsic
        prev_mean = self.prem_ema.get(name, prem)
        dev = prem - prev_mean
        new_mean = self._ema_update(prev_mean, prem, PREM_ALPHA)
        prev_var = self.prem_var_ema.get(name, dev * dev)
        new_var = self._ema_update(prev_var, dev * dev, PREM_VAR_ALPHA)
        self.prem_ema[name] = new_mean
        self.prem_var_ema[name] = new_var
        std = new_var ** 0.5
        if std < SMILE_VAR_FLOOR:
            std = SMILE_VAR_FLOOR
        z = dev / std
        fair_voucher_mid = intrinsic + new_mean
        if z >= SMILE_Z_TAKE and sr > 0:
            for bp in sorted(od.buy_orders, reverse=True):
                if sr <= 0:
                    break
                if bp > fair_voucher_mid + 0.5:
                    q = min(od.buy_orders[bp], sr)
                    if q > 0:
                        o.append(Order(name, bp, -q))
                        sr -= q
                else:
                    break
        if z <= -SMILE_Z_TAKE and br > 0:
            for ap in sorted(od.sell_orders):
                if br <= 0:
                    break
                if ap < fair_voucher_mid - 0.5:
                    q = min(-od.sell_orders[ap], br)
                    if q > 0:
                        o.append(Order(name, ap, q))
                        br -= q
                else:
                    break
        if not SMILE_MAKE_ENABLED:
            return o
        pb, pa = self._quote_inside_or_at(fair_voucher_mid, bb, ba, SMILE_MAKE_EDGE, pos, ml, SMILE_SKEW)
        if pb is not None and pa is not None and (pb < pa):
            if br > 0 and pb >= 0:
                o.append(Order(name, pb, br))
            if sr > 0 and pa >= 1:
                o.append(Order(name, pa, -sr))
        return o

    @staticmethod
    def _allocate_jumper(name: str, br: int, sr: int, pb: int, pa: int, bb: int, ba: int, fv: float):
        if not QUEUE_JUMPER_ENABLED or name not in QUEUE_JUMPER_SYMBOLS:
            return (br, sr, None, None)
        sz = QUEUE_JUMPER_SIZE
        max_off = 10
        jb = ja = None
        br_main, sr_main = (br, sr)
        if br > sz:
            pb_j = pb + 1
            if pb_j > pb and pb_j <= ba - 1 and (pb_j <= fv + max_off):
                jb = (pb_j, sz)
                br_main = br - sz
        if sr > sz:
            pa_j = pa - 1
            if pa_j < pa and pa_j >= bb + 1 and (pa_j >= fv - max_off):
                ja = (pa_j, -sz)
                sr_main = sr - sz
        return (br_main, sr_main, jb, ja)

    @staticmethod
    def _layer_orders(name: str, side: str, primary_px: int, total_size: int, bb: int, ba: int):
        out: List[Order] = []
        if total_size <= 0:
            return out
        if not LAYERED_MM or len(LAYER_FRACS) <= 1:
            qty = total_size if side == 'B' else -total_size
            return [Order(name, primary_px, qty)]
        remaining = total_size
        for i, (frac, off) in enumerate(zip(LAYER_FRACS, LAYER_OFFSETS)):
            sz = int(total_size * frac) if i < len(LAYER_FRACS) - 1 else remaining
            if sz <= 0:
                continue
            if side == 'B':
                px = primary_px - off
                if px < 1:
                    px = primary_px
                if px > ba - 1:
                    px = ba - 1
                out.append(Order(name, px, sz))
            else:
                px = primary_px + off
                if px < bb + 1:
                    px = bb + 1
                out.append(Order(name, px, -sz))
            remaining -= sz
        return out

    @staticmethod
    def _quote_inside_or_at(fair: float, bb: int, ba: int, edge: int, pos: int, ml: int, skew: float):
        adj = fair - pos / ml * skew
        ideal_b = int(adj - edge)
        ideal_a = int(adj + edge + 0.5)
        pb = min(ideal_b, bb + 1)
        pa = max(ideal_a, ba - 1)
        pb = min(pb, ba - 1)
        pa = max(pa, bb + 1)
        if pb >= pa:
            pb = bb
            pa = ba
        return (pb, pa)

    def _eod_liquidation(self, state: TradingState, orders: Dict[str, List[Order]]) -> None:
        for prod in state.order_depths:
            pos = state.position.get(prod, 0)
            if pos == 0:
                continue
            od = state.order_depths[prod]
            out: List[Order] = []
            if pos > 0:
                remaining = pos
                for bp in sorted(od.buy_orders, reverse=True):
                    if remaining <= 0:
                        break
                    q = min(od.buy_orders[bp], remaining)
                    if q > 0:
                        out.append(Order(prod, bp, -q))
                        remaining -= q
                if remaining > 0:
                    if od.buy_orders:
                        rest_px = min(od.buy_orders) - 1
                    elif od.sell_orders:
                        rest_px = min(od.sell_orders) - 1
                    else:
                        rest_px = None
                    if rest_px is not None and rest_px >= 1:
                        out.append(Order(prod, rest_px, -remaining))
            else:
                remaining = -pos
                for ap in sorted(od.sell_orders):
                    if remaining <= 0:
                        break
                    q = min(-od.sell_orders[ap], remaining)
                    if q > 0:
                        out.append(Order(prod, ap, q))
                        remaining -= q
                if remaining > 0:
                    if od.sell_orders:
                        rest_px = max(od.sell_orders) + 1
                    elif od.buy_orders:
                        rest_px = max(od.buy_orders) + 1
                    else:
                        rest_px = None
                    if rest_px is not None:
                        out.append(Order(prod, rest_px, remaining))
            if out:
                orders[prod] = out

    @staticmethod
    def _mid(od):
        if od is None or not od.buy_orders or (not od.sell_orders):
            return None
        return (max(od.buy_orders) + min(od.sell_orders)) / 2.0

    @staticmethod
    def _ema_update(prev: float, obs: float, alpha: float) -> float:
        if prev == 0.0:
            return obs
        return prev + alpha * (obs - prev)

    def _load_state(self, td: str) -> None:
        if not td:
            return
        try:
            d = json.loads(td)
        except Exception:
            return
        if not isinstance(d, dict):
            return
        self.fv_h = float(d.get('fv_h', self.fv_h))
        self.fv_v = float(d.get('fv_v', self.fv_v))
        self.slow_fv_v = float(d.get('sfv', self.slow_fv_v))
        self.slow_fv_h = float(d.get('sfh', self.slow_fv_h))
        self.flow_v = float(d.get('fl', self.flow_v))
        self.cp_nudge_v = float(d.get('cp', self.cp_nudge_v))
        self.last_seen_ts_v = int(d.get('lts', self.last_seen_ts_v))
        pe = d.get('pe', {})
        pv = d.get('pv', {})
        lm = d.get('lm', {})
        if isinstance(pe, dict):
            self.prem_ema = {k: float(v) for k, v in pe.items()}
        if isinstance(pv, dict):
            self.prem_var_ema = {k: float(v) for k, v in pv.items()}
        if isinstance(lm, dict):
            self.last_mid = {k: float(v) for k, v in lm.items()}

    def _dump_state(self) -> str:
        return json.dumps({'fv_h': round(self.fv_h, 4), 'fv_v': round(self.fv_v, 4), 'sfv': round(self.slow_fv_v, 4), 'sfh': round(self.slow_fv_h, 4), 'fl': round(self.flow_v, 3), 'cp': round(self.cp_nudge_v, 4), 'lts': self.last_seen_ts_v, 'pe': {k: round(v, 4) for k, v in self.prem_ema.items()}, 'pv': {k: round(v, 6) for k, v in self.prem_var_ema.items()}, 'lm': {k: round(v, 2) for k, v in self.last_mid.items()}}, separators=(',', ':'))
