# ignith manual — my sheet

**ui gotcha:** the **Percentage** field is **allocation `a`** (half of `r` in the optimizer output), **not** ashflow `r×100`. if you type **25 / 30 / 20** you are **not** typing r=0.25 — you are telling the game **25% / 30% / 20%** of the 1M budget. that sums to **140%** and fees go to **345k**. the client only accepts **whole** percents — **12.5 / 7.5** won’t work. use **12, 15, 10, 15, 8, 0, 0, 0, 10** → **70%** total (same ev near-continuous in the toy model), fees **85,800**.

i treat fee as `pct**2 * 1_000_000` per leg (verify one line in the ui — wiki copy is broken).

i solved `max Σ (a_i r_i - a_i^2) B` s.t. `Σ a_i ≤ 1`, `0 ≤ a_i ≤ 0.4` with `a_i* = r_i/2` when slack, else lagrange on `{r_i > λ}`.

ashflow alpha read (**r** = expected return rate per xirec, **not** what you type in %):

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

**what to enter in-game (Percentage column = 100×a):**

| good | side | % |
|---|---|---:|
| obsidian | buy | **12** |
| pyroflex | sell | **15** |
| thermalite | buy | **10** |
| lava cake | sell | **15** |
| magma ink | buy | **8** |
| scoria / ashes / incense | skip | **0** |
| sulfur | buy | **10** |
| sum | | **70** |

i dropped three legs on purpose — r4 manual taught me variance eats small edge legs.

run:

```bash
python3 ignith_manual/pricer.py
```

paste **alloc** column into the game (integers only). totals: **70%** deployed, **+86,200** expected in the quadratic toy model (real score has rng).
