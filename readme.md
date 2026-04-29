imc prosperity round 3
======================

i traded hydro, velvet, 10 vouchers (same universe as r2) with disclosed flow. i wrote `trader.py` v5.1 (ema fairs, deep-itm off velvet−K, smile premium mm, OTM pinned branch that never filled, anti-trend on hydro). official algo **+17,377** (#1349); manual gardeners guild **+65,190**; combined **+82,567** (#1708). sub log `LOGS/486260/486260.py` is the one i cite for the final ticket.

i learned the live day is **10k ticks** one day — i had wrongly thought in 3× terms for projection. calibration vs single-day replay was ~0.31, same ballpark as r2. structural ceiling argument: top algo beat naive directional max; i needed spread / basis work not bigger directional bets.

i mined r3 tapes in `analysis/` (parse scripts, iv smile, vouchers, sweeps) and shipped `wiki_round3_reference.md` as an offline rules copy (imc wording below the note line).

tb: `cd prosperity_rust_backtester && make round3 TRADER=../trader.py`

extras: `gardeners_guild/` sim for the manual nutrient puzzle.

sanity: `python3 test_trader.py`
