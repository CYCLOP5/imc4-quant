imc prosperity round 4
======================

i dug through `prosperity_rust_backtester/datasets/round4/` (prices + trades; `trade.buyer` / `trade.seller` are the Mark bots). i wrote `analysis/profile_marks.py` and `analysis/marks_signal_vs_noise.py` to see who mm's vs who overpays and whether prints drift.

what i took away: hydro + vev_4000 are mostly mark 14 vs mark 38 (taker bleeds vs mid); vev_6000 / vev_6500 are mark 22 ↔ mark 01 with no mark 14 — i don't quote those. velvet has mark 67 buys that drift up and noise sellers i mostly ignore in fv nudges; i left `COUNTERPARTY_ENABLED=False` after sweeps hurt backtest.

`trader.py` is my submitted mm: ema mids, deep-itm off velvet−K, smile premium mm, inventory bias, hydro anti-trend ema, size-1 queue jumper on hydro + vev_4000, `SKIP_PRODUCTS={'VEV_6000','VEV_6500'}`. params that moved vs older r3 code: `DEEP_ITM_TREND_BETA=-0.25`, `VELVET_INV_BIAS=2`.

tb (rust):

```bash
cd prosperity_rust_backtester
make round4 TRADER=../trader.py
```

i replayed about +194k xirec on that stack before live. official r4 i got algo **+84,121**, manual **−15,350** (aether options — aggressive ticket got unlucky vs mc mean). submission log: `LOGS/545137/545137.py`.

manual book: i mc-priced everything in `aether_manual/pricer.py` with trading-day step counts for t+14 / t+21; ticket notes in `aether_manual/readme.md`.

tree i care about:

```
trader.py  test_trader.py  datamodel.py
wiki_round4_reference.md
analysis/profile_marks.py  analysis/marks_signal_vs_noise.py
analysis/sweep_v6.py  analysis/sweep_cp.py
aether_manual/
prosperity_rust_backtester/   # rust engine + datasets/round4
LOGS/545137/
```

sanity: `python3 test_trader.py`
