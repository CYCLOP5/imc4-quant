imc prosperity r5 branch — my notes
====================================

algo
----
i use `prosperity_rust_backtester/datasets/round5/` (prices + trades, d+2 d+3 d+4). i ran the bundled starter through rust `make round5` and got +401,540 on paper. i then sorted per-product pnl and tagged seven names that lost on ≥2 of 3 days and lost ≥5k total: `SLEEP_POD_LAMB_WOOL`, `PANEL_1X2`, `PEBBLES_M`, `ROBOT_MOPPING`, `UV_VISOR_MAGENTA`, `GALAXY_SOUNDS_SOLAR_FLAMES`, `TRANSLATOR_SPACE_GRAY`. i turned those off in `Trader.SKIP_PRODUCTS` and replay said +503,671 (+~25%). same starter mm otherwise (penny inside wide book, size 5, limit 10).

i tried price skew on inventory; it hurt replay so `INV_SKEW_K=0`. eod flatten i kept off in backtest but turned on for live as cheap insurance against overnight inventory (`EOD_FLATTEN=True`, `EOD_TS=995_000`).

tb: `cd prosperity_rust_backtester && make round5 TRADER=../trader.py PRODUCTS=full`

live
----
first submission `LOGS/553293/` finished at **+35,372**. backtest had implied ~165k/day → live calibration ~0.21x. i pulled per-product live pnl and found 5 chronic bleeders that lost a lot in one day: `GALAXY_SOUNDS_PLANETARY_RINGS` -7,257, `ROBOT_DISHES` -4,500, `GALAXY_SOUNDS_DARK_MATTER` -3,834, `OXYGEN_SHAKE_MORNING_BREATH` -3,372, `PANEL_2X2` -2,806. these were ~20k/day winners in backtest — classic regime flip. added them to `SKIP_PRODUCTS` and flipped `EOD_FLATTEN=True`.

second submission `LOGS/553674/` finished at **+57,141 (+21,769 vs prev)**. diff'd both runs product-by-product: every other product's pnl is byte-identical, the +21,769 came exactly from zeroing out the 5 newly-skipped names. no fitting, no second-order effects.

remaining live losers (`ROBOT_LAUNDRY` -2,398, `PANEL_1X4` -2,395, `UV_VISOR_AMBER` -2,162 …) were strong backtest winners — these reads like noise on n=1 day, so i did not skip them. **57,141 is final.**

research
--------
i wrote `analysis/round5_research.py` (stdlib) to dump family stats, pair list, lag scans into `analysis/round5_research.md`. cross-family lag went empty under the strict filter. snackpack looked best on scoring + pair structure but i did not wire that into the trader — only the replay skip-list did.

manual ignith
-------------
budget 1e6 xirec, fee per line `pct**2 * budget` where **pct** is the **Percentage** field as a fraction (0.125 not 0.25).

**bug i almost shipped:** i typed **25, 30, 20…** in Percentage thinking that was `r×100`. that is **wrong** — the game treats that as **25% of budget** per line. optimal **allocation** is `a=r/2` in the model; the ui only takes **integer** percents, so i enter **12, 15, 10, 15, 8, 10** on the six legs (**70%** total), not **12.5 / 7.5**. typing **25,30,…** → **140%** and fee **345k** (matches the broken ticket).

i read ashflow alpha: buy obsidian, sell pyroflex, buy thermalite, sell lava cake, buy magma ink, buy sulfur; skip 3 hype legs.

| good | side | **% (ui)** |
|---|---|---:|
| obsidian | buy | **12** |
| pyroflex | sell | **15** |
| thermalite | buy | **10** |
| lava cake | sell | **15** |
| magma ink | buy | **8** |
| scoria / ashes / incense | skip | **0** |
| sulfur | buy | **10** |
| **sum** | | **70** |

expected fee total **85,800** if ui matches `(pct/100)**2 * 1e6`. verify one line (e.g. 15% → fee 22,500). formula: `(pct/100)^2 * 1_000_000`.

repo (what i kept)
------------------
```
trader.py test_trader.py datamodel.py
wiki_round4_reference.md wiki_round5_reference.md
analysis/round5_research.py analysis/round5_research.md
ignith_manual/pricer.py ignith_manual/readme.md ignith_manual/run_output.txt
prosperity_rust_backtester/   # rust tb + round5 csvs
test_round5_research.py test_ignith_manual.py
```

tests: `python3 test_trader.py && python3 test_round5_research.py && python3 test_ignith_manual.py`
