import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datamodel import Listing, Observation, OrderDepth, TradingState
from trader import Trader

GALAXY = "GALAXY_SOUNDS_BLACK_HOLES"
SNACK = "SNACKPACK_RASPBERRY"
SKIPPED = "SLEEP_POD_LAMB_WOOL"
SKIPPED_NEW = "ROBOT_DISHES"
UNKNOWN = "NOT_A_ROUND5_PRODUCT"


def mkstate(product, buy_orders, sell_orders, position=None, timestamp=100):
    position = position or {}
    return TradingState(
        "",
        timestamp,
        {product: Listing(product, product, "XIRECS")},
        {product: OrderDepth(buy_orders=buy_orders, sell_orders=sell_orders)},
        {product: []},
        {product: []},
        position,
        Observation(),
    )


def quantities(orders):
    return [(order.price, order.quantity) for order in orders]


def test_default_starter_quotes_inside_wide_book():
    trader = Trader()
    state = mkstate(GALAXY, {9994: 13, 9992: 21}, {10006: -13, 10008: -21})

    orders, conversions, trader_data = trader.run(state)

    assert conversions == 0
    assert trader_data == ""
    assert quantities(orders[GALAXY]) == [(9995, 5), (10005, -5)]


def test_default_respects_round5_position_limit():
    trader = Trader()
    galaxy_state = mkstate(GALAXY, {9994: 13}, {10006: -13}, {GALAXY: 9})
    snack_state = mkstate(SNACK, {9992: 36}, {10008: -36}, {SNACK: -9})

    galaxy_orders, _, _ = trader.run(galaxy_state)
    snack_orders, _, _ = trader.run(snack_state)

    assert quantities(galaxy_orders.get(GALAXY, [])) == [(9995, 1), (10005, -5)]
    assert quantities(snack_orders.get(SNACK, [])) == [(9993, 5), (10007, -1)]


def test_skip_list_quiet():
    trader = Trader()
    state = mkstate(SKIPPED, {9994: 13}, {10006: -13}, {SKIPPED: 0})

    orders, _, _ = trader.run(state)

    assert orders[SKIPPED] == []


def test_skip_list_includes_live_losers():
    trader = Trader()
    state = mkstate(SKIPPED_NEW, {9994: 13}, {10006: -13}, {SKIPPED_NEW: 0})

    orders, _, _ = trader.run(state)

    assert orders[SKIPPED_NEW] == []


def test_default_flattens_at_close():
    trader = Trader()
    state = mkstate(
        GALAXY,
        {9994: 13},
        {10006: -13},
        position={GALAXY: 7},
        timestamp=999_900,
    )

    orders, _, _ = trader.run(state)

    assert quantities(orders[GALAXY]) == [(9994, -7)]


def test_ignores_unknown_products():
    trader = Trader()
    state = mkstate(UNKNOWN, {9990: 10}, {10010: -10})

    orders, _, _ = trader.run(state)

    assert orders[UNKNOWN] == []


class _SkewedTrader(Trader):
    INV_SKEW_K = 2


class _FlatteningTrader(Trader):
    EOD_FLATTEN = True


def test_inv_skew_pulls_quotes_down_when_long():
    trader = _SkewedTrader()
    state = mkstate(GALAXY, {9994: 13}, {10006: -13}, {GALAXY: 9})

    orders, _, _ = trader.run(state)

    assert quantities(orders[GALAXY]) == [(9993, 1), (10003, -5)]


def test_inv_skew_pulls_quotes_up_when_short():
    trader = _SkewedTrader()
    state = mkstate(SNACK, {9992: 36}, {10008: -36}, {SNACK: -9})

    orders, _, _ = trader.run(state)

    assert quantities(orders[SNACK]) == [(9995, 5), (10009, -1)]


def test_inv_skew_falls_back_when_it_would_cross_the_book():
    trader = _SkewedTrader()
    state = mkstate(GALAXY, {9999: 13}, {10001: -13}, {GALAXY: 6})

    orders, _, _ = trader.run(state)

    assert quantities(orders[GALAXY]) == [(10000, 4), (10000, -5)]


def test_eod_flatten_long_position():
    trader = _FlatteningTrader()
    state = mkstate(
        GALAXY,
        {9994: 13},
        {10006: -13},
        position={GALAXY: 7},
        timestamp=Trader.EOD_TS,
    )

    orders, _, _ = trader.run(state)

    assert quantities(orders[GALAXY]) == [(9994, -7)]


def test_eod_flatten_short_position():
    trader = _FlatteningTrader()
    state = mkstate(
        GALAXY,
        {9994: 13},
        {10006: -13},
        position={GALAXY: -4},
        timestamp=Trader.EOD_TS + 1000,
    )

    orders, _, _ = trader.run(state)

    assert quantities(orders[GALAXY]) == [(10006, 4)]


def test_eod_flatten_caps_to_visible_depth():
    trader = _FlatteningTrader()
    state = mkstate(
        GALAXY,
        {9994: 3},
        {10006: -13},
        position={GALAXY: 10},
        timestamp=Trader.EOD_TS,
    )

    orders, _, _ = trader.run(state)

    assert quantities(orders[GALAXY]) == [(9994, -3)]


def test_eod_flatten_no_action_when_flat():
    trader = _FlatteningTrader()
    state = mkstate(
        GALAXY,
        {9994: 13},
        {10006: -13},
        position={GALAXY: 0},
        timestamp=Trader.EOD_TS,
    )

    orders, _, _ = trader.run(state)

    assert orders[GALAXY] == []


def run_all():
    tests = [
        test_default_starter_quotes_inside_wide_book,
        test_default_respects_round5_position_limit,
        test_skip_list_quiet,
        test_skip_list_includes_live_losers,
        test_default_flattens_at_close,
        test_ignores_unknown_products,
        test_inv_skew_pulls_quotes_down_when_long,
        test_inv_skew_pulls_quotes_up_when_short,
        test_inv_skew_falls_back_when_it_would_cross_the_book,
        test_eod_flatten_long_position,
        test_eod_flatten_short_position,
        test_eod_flatten_caps_to_visible_depth,
        test_eod_flatten_no_action_when_flat,
    ]
    for test in tests:
        test()
        print(f"{test.__name__}: ok")


if __name__ == "__main__":
    run_all()
