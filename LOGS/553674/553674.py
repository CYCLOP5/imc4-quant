from typing import Dict, List, Optional

from datamodel import Order, OrderDepth, TradingState


class Trader:
    ROUND5_PREFIXES = (
        "GALAXY_SOUNDS_",
        "SLEEP_POD_",
        "MICROCHIP_",
        "PEBBLES_",
        "ROBOT_",
        "UV_VISOR_",
        "TRANSLATOR_",
        "PANEL_",
        "OXYGEN_SHAKE_",
        "SNACKPACK_",
    )

    ROUND5_LIMIT = 10
    QUOTE_SIZE = 5

    SKIP_PRODUCTS = frozenset(
        {
            "SLEEP_POD_LAMB_WOOL",
            "PANEL_1X2",
            "PEBBLES_M",
            "ROBOT_MOPPING",
            "UV_VISOR_MAGENTA",
            "GALAXY_SOUNDS_SOLAR_FLAMES",
            "TRANSLATOR_SPACE_GRAY",
            "GALAXY_SOUNDS_PLANETARY_RINGS",
            "GALAXY_SOUNDS_DARK_MATTER",
            "ROBOT_DISHES",
            "OXYGEN_SHAKE_MORNING_BREATH",
            "PANEL_2X2",
        }
    )

    INV_SKEW_K = 0
    EOD_FLATTEN = True
    EOD_TS = 995_000

    def run(self, state: TradingState):
        orders_by_product: Dict[str, List[Order]] = {}
        ts = int(getattr(state, "timestamp", 0) or 0)

        for product, order_depth in state.order_depths.items():
            limit = self.limit_for(product)
            if limit is None or product in self.SKIP_PRODUCTS:
                orders_by_product[product] = []
                continue

            position = int(state.position.get(product, 0))

            if self.EOD_FLATTEN and ts >= self.EOD_TS:
                orders_by_product[product] = self.flatten(
                    product, order_depth, position
                )
                continue

            orders_by_product[product] = self.quote_both_sides(
                product,
                order_depth,
                position,
                limit,
            )

        return orders_by_product, 0, ""

    def limit_for(self, product: str) -> Optional[int]:
        if product.startswith(self.ROUND5_PREFIXES):
            return self.ROUND5_LIMIT
        return None

    def inv_skew(self, position: int, limit: int) -> int:
        if limit <= 0 or self.INV_SKEW_K == 0:
            return 0
        return int(round(self.INV_SKEW_K * position / limit))

    def quote_both_sides(
        self,
        product: str,
        order_depth: OrderDepth,
        position: int,
        limit: int,
    ) -> List[Order]:
        if not order_depth.buy_orders or not order_depth.sell_orders:
            return []

        best_bid = max(order_depth.buy_orders)
        best_ask = min(order_depth.sell_orders)
        if best_bid >= best_ask:
            return []

        if best_ask - best_bid > 1:
            base_bid = best_bid + 1
            base_ask = best_ask - 1
        else:
            base_bid = best_bid
            base_ask = best_ask

        skew = self.inv_skew(position, limit)
        bid_price = base_bid - skew
        ask_price = base_ask - skew

        if (
            bid_price >= best_ask
            or ask_price <= best_bid
            or bid_price >= ask_price
            or bid_price < 1
        ):
            bid_price = base_bid
            ask_price = base_ask

        buy_size = min(self.QUOTE_SIZE, max(0, limit - position))
        sell_size = min(self.QUOTE_SIZE, max(0, limit + position))

        orders: List[Order] = []
        if buy_size > 0:
            orders.append(Order(product, bid_price, buy_size))
        if sell_size > 0:
            orders.append(Order(product, ask_price, -sell_size))
        return orders

    def flatten(
        self,
        product: str,
        order_depth: OrderDepth,
        position: int,
    ) -> List[Order]:
        if position == 0:
            return []

        orders: List[Order] = []
        if position > 0 and order_depth.buy_orders:
            best_bid = max(order_depth.buy_orders)
            available = abs(int(order_depth.buy_orders[best_bid]))
            qty = min(position, available)
            if qty > 0:
                orders.append(Order(product, best_bid, -qty))
        elif position < 0 and order_depth.sell_orders:
            best_ask = min(order_depth.sell_orders)
            available = abs(int(order_depth.sell_orders[best_ask]))
            qty = min(-position, available)
            if qty > 0:
                orders.append(Order(product, best_ask, qty))
        return orders