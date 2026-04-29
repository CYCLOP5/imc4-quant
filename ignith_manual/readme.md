# ignith manual — my sheet

i treat fee as `pct**2 * 1_000_000` per leg (verify one line in the ui — wiki copy is broken).

i solved `max Σ (a_i r_i - a_i^2) B` s.t. `Σ a_i ≤ 1`, `0 ≤ a_i ≤ 0.4` with `a_i* = r_i/2` when slack, else lagrange on `{r_i > λ}`.

ashflow alpha read (direction + r, then `pricer.py` prints sizes):

| story | my side | r |
|---|---|---:|
| obsidian halt / contamination | buy | 0.25 |
| pyroflex tax cut ends, levy doubles | sell | 0.30 |
| thermalite forecast 1.42M→3.89M users | buy | 0.20 |
| lava cake recall / lawsuits | sell | 0.30 |
| magma ink pen drop + queues | buy | 0.15 |
| scoria — influencer only | skip | 0 |
| ashes — pr mess, unclear net | skip | 0 |
| volcanic incense — pump character | skip | 0 |
| sulfur index 118 inclusion | buy | 0.20 |

i dropped three legs on purpose — r4 manual taught me variance eats small edge legs.

run:

```bash
python3 ignith_manual/pricer.py
```

paste numbers from terminal into the game. totals: **70%** deployed, **+86,250** expected in the quadratic toy model (real score has rng).
