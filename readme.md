imc prosperity r5 branch — my notes
====================================

algo
----
i use `prosperity_rust_backtester/datasets/round5/` (prices + trades, d+2 d+3 d+4). i ran the bundled starter through rust `make round5` and got +401,540 on paper. i then sorted per-product pnl and tagged seven names that lost on ≥2 of 3 days and lost ≥5k total: `SLEEP_POD_LAMB_WOOL`, `PANEL_1X2`, `PEBBLES_M`, `ROBOT_MOPPING`, `UV_VISOR_MAGENTA`, `GALAXY_SOUNDS_SOLAR_FLAMES`, `TRANSLATOR_SPACE_GRAY`. i turned those off in `Trader.SKIP_PRODUCTS` and replay said +503,671 (+~25%). same starter mm otherwise (penny inside wide book, size 5, limit 10).

i tried price skew on inventory and eod flatten; both hurt replay on this dataset so `INV_SKEW_K=0` and `EOD_FLATTEN=False`. the methods stay in `trader.py` for subclasses in `test_trader.py`.

tb: `cd prosperity_rust_backtester && make round5 TRADER=../trader.py PRODUCTS=full`

research
--------
i wrote `analysis/round5_research.py` (stdlib) to dump family stats, pair list, lag scans into `analysis/round5_research.md`. cross-family lag went empty under the strict filter. snackpack looked best on scoring + pair structure but i did not wire that into the trader — only the replay skip-list did.

manual ignith
-------------
budget 1e6 xirec, fee per line i treat as `pct**2 * budget` (check the ui on one leg before lock — wiki text is messy).

i read ashflow alpha: buy obsidian (halt), sell pyroflex (tax doubles), buy thermalite (usage forecast), sell lava cake (recall), buy magma ink (launch queues), buy sulfur reactor (index 118 add). i skipped scoria (influencer hype), ashes (ambiguous pr), volcanic incense (pump narrative).

alloc comes from `a_i = r_i/2` with cap 0.4 and the lagrange step if Σa>1 — see `ignith_manual/pricer.py`. copy the table from `ignith_manual/run_output.txt` into the manual ui.

| good | side | % |
|---|---|---:|
| obsidian_cutlery | buy | 12.5 |
| pyroflex_cells | sell | 15.0 |
| thermalite_core | buy | 10.0 |
| lava_cake | sell | 15.0 |
| magma_ink | buy | 7.5 |
| scoria_paste | skip | 0 |
| ashes_of_the_phoenix | skip | 0 |
| volcanic_incense | skip | 0 |
| sulfur_reactor | buy | 10.0 |
| **sum** | | **70** |

expected pnl on this model before rng: +86,250 after fees in the quadratic closed form.

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
