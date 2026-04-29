import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ignith_manual import pricer


def approx(a, b, eps=1e-9):
    return abs(a - b) <= eps


def test_unconstrained_optimum_is_half_the_return_rate():
    expected = {good: r for good, r in zip(pricer.GOODS, [0.10, 0.20, 0.05, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])}
    allocs = pricer.optimal_allocations(expected, max_allocation=1.0)
    assert approx(allocs["obsidian_cutlery"], 0.05)
    assert approx(allocs["pyroflex_cells"], 0.10)
    assert approx(allocs["thermalite_core"], 0.025)
    assert allocs["lava_cake"] == 0.0


def test_zero_returns_get_zero_allocation():
    expected = {good: 0.0 for good in pricer.GOODS}
    allocs = pricer.optimal_allocations(expected)
    for good in pricer.GOODS:
        assert allocs[good] == 0.0


def test_per_leg_cap_clamps_extreme_returns():
    expected = {good: 0.0 for good in pricer.GOODS}
    expected["thermalite_core"] = 1.5
    allocs = pricer.optimal_allocations(expected, max_allocation=0.40)
    assert allocs["thermalite_core"] == 0.40


def test_budget_constraint_binds_when_unconstrained_sum_over_one():
    expected = {good: 0.0 for good in pricer.GOODS}
    for good in ("obsidian_cutlery", "pyroflex_cells", "thermalite_core"):
        expected[good] = 1.0
    allocs = pricer.optimal_allocations(expected, max_allocation=1.0)
    assert approx(allocs["obsidian_cutlery"], 1 / 3, 1e-9)
    assert approx(allocs["pyroflex_cells"], 1 / 3, 1e-9)
    assert approx(allocs["thermalite_core"], 1 / 3, 1e-9)
    total = sum(allocs.values())
    assert approx(total, 1.0, 1e-9)


def test_unconstrained_optimum_has_fee_equal_net_pnl():
    expected = {good: 0.0 for good in pricer.GOODS}
    expected["thermalite_core"] = 0.30
    expected["magma_ink"] = 0.20
    legs = pricer.build_ticket(
        expected,
        {good: "buy" for good in pricer.GOODS},
        max_allocation=1.0,
    )
    by_good = {leg.good: leg for leg in legs}
    for good in ("thermalite_core", "magma_ink"):
        assert approx(by_good[good].fee, by_good[good].expected_pnl, 1e-6)


def test_skip_direction_when_return_or_alloc_is_zero():
    expected = {good: 0.0 for good in pricer.GOODS}
    expected["thermalite_core"] = 0.30
    legs = pricer.build_ticket(
        expected,
        {good: "buy" for good in pricer.GOODS},
    )
    by_good = {leg.good: leg for leg in legs}
    assert by_good["thermalite_core"].direction == "buy"
    assert by_good["lava_cake"].direction == "skip"
    assert by_good["lava_cake"].allocation == 0.0


def run_all():
    tests = [
        test_unconstrained_optimum_is_half_the_return_rate,
        test_zero_returns_get_zero_allocation,
        test_per_leg_cap_clamps_extreme_returns,
        test_budget_constraint_binds_when_unconstrained_sum_over_one,
        test_unconstrained_optimum_has_fee_equal_net_pnl,
        test_skip_direction_when_return_or_alloc_is_zero,
    ]
    for test in tests:
        test()
        print(f"{test.__name__}: ok")


if __name__ == "__main__":
    run_all()
