aether crystal manual (r4)
===========================

i wrote `pricer.py` to mc price the aether + listed options under the published rules: σ=2.51, 0 drift, 4 steps/trading day, contract multiplier 3000, score uses N=100 paths.

i screwed up once: "2 weeks" / "3 weeks" in the spec are **trading** days → 40 / 60 steps, not 14/21 calendar days. after that fix vanillas sat near mkt and ev came mostly from exotics + ko.

run:

```bash
python3 aether_manual/pricer.py
```

i committed `run_output.txt` from the same command. horizons: t+21 = 60 steps, t+14 = 40 steps; i reuse path prefixes so joint pnl is consistent.

i submitted a layered +ev ticket; realized pnl was in the left tail (see root `readme.md`). chooser + binary worked; ko + some vanillas hurt.
