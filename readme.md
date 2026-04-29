imc prosperity round 2
======================

i traded ash-coated osmium (aco) and intarian pepper root (ipr) with a market-access bid (`bid()` → 1000) and the invest & expand manual. shipped v6 aco mean-rev tighter takes (<=fv-3, >=fv+5) + skew; ipr kalman w/ selective takes. official **+82,269** algo sub **359962**; manual invest **+204,355** gross; combined **286,624**.

i dug r2 tapes in `analysis/` (characterize, r1 vs r2, signals, kalman sweep naive — i learned naive sweep lied vs rust replay).

tb: `cd prosperity_rust_backtester && make round2 TRADER=../trader.py`

manual sim inputs: `invest_expand/sim.py` (readme there if present).

i keep `wiki_round2_reference.md` as offline imc brief — imc wording below my one-line note at top.

tests: `python3 test_trader.py`
