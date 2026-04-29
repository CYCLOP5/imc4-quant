from analysis import round5_research as r5


def test_cached_family_return_matches_direct_family_return():
    prices = {
        2: {
            "GALAXY_SOUNDS_DARK_MATTER": [{"mid": 1.0}, {"mid": 3.0}, {"mid": 6.0}],
            "GALAXY_SOUNDS_BLACK_HOLES": [{"mid": 2.0}, {"mid": 4.0}, {"mid": 7.0}],
            "GALAXY_SOUNDS_PLANETARY_RINGS": [{"mid": 3.0}, {"mid": 5.0}, {"mid": 8.0}],
            "GALAXY_SOUNDS_SOLAR_WINDS": [{"mid": 4.0}, {"mid": 6.0}, {"mid": 9.0}],
            "GALAXY_SOUNDS_SOLAR_FLAMES": [{"mid": 5.0}, {"mid": 7.0}, {"mid": 10.0}],
        }
    }

    cache = r5.build_return_cache(prices)

    assert r5.cached_family_return(cache, 2, "GALAXY_SOUNDS") == r5.family_return(
        prices, 2, "GALAXY_SOUNDS"
    )


def test_pair_residual_uses_sum_for_opposite_movers():
    relation, residual = r5.pair_residual_series([10.0, 12.0], [4.0, 3.0], -0.8)

    assert relation == "basket"
    assert residual == [14.0, 15.0]


if __name__ == "__main__":
    test_cached_family_return_matches_direct_family_return()
    test_pair_residual_uses_sum_for_opposite_movers()
    print("test_cached_family_return_matches_direct_family_return: ok")
    print("test_pair_residual_uses_sum_for_opposite_movers: ok")
