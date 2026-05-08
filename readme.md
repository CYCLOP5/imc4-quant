<img width="1200" height="630" alt="image" src="https://github.com/user-attachments/assets/2478b149-cd4b-4eec-a96a-50c7453a6595" />
<img width="1079" height="592" alt="image" src="https://github.com/user-attachments/assets/2306c3c3-4998-4f0f-8a9c-7863c896a214" />
Final results:
- 762/18k+ Overall
- 726 Algorithimic
- 1225 Manual
- 133 Country
there are multiple branches corresponding to the numbered rounds:

- `main` (demo)
- `round1`
- `round2`
- `round3`
- `round4`
- `round5`

---
imc prosperity — tutorial / early sandbox
==========================================

this was my scratch repo before the numbered rounds landed on other branches. products **emeralds** + **tomatoes** on round 0 sample csvs in the root; strategy notes were in the old long readme — now gone. current `trader.py` is wall-mid style tomatoes + fv=10k emeralds with aggressive takes at fair.

data: `prices_round_0_day_*.csv`, `trades_round_0_day_*.csv`.

`imc-prosperity-4-backtester/` is the early python backtester snapshot i was using.

util: `analyze_alpha.py`, `param_sweep.py`.

tests: `python3 test_trader.py`
