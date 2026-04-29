# r5 research pass 1

source: `prosperity_rust_backtester/datasets/round5/` days d+2 d+3 d+4. generator: `analysis/round5_research.py`.

## family snapshot

| family | mm_score | spread | trade_vol | abs_drift | ret_vol | acf1 | intra_corr |
|---|---|---|---|---|---|---|---|
| SNACKPACK | 457.87 | 16.79 | 9025 | 202.67 | 6.91 | -0.023 | -0.160 |
| GALAXY_SOUNDS | 246.08 | 13.73 | 9025 | 829.33 | 10.85 | -0.010 | 0.004 |
| UV_VISOR | 245.81 | 13.13 | 9025 | 761.57 | 10.34 | -0.001 | 0.006 |
| OXYGEN_SHAKE | 232.82 | 12.90 | 9025 | 797.23 | 10.77 | -0.041 | 0.007 |
| PANEL | 184.68 | 9.40 | 9025 | 823.87 | 9.88 | -0.005 | 0.004 |
| TRANSLATOR | 170.53 | 8.78 | 9025 | 747.73 | 9.94 | -0.004 | 0.005 |
| SLEEP_POD | 170.00 | 9.65 | 9025 | 870.43 | 11.06 | -0.001 | 0.003 |
| PEBBLES | 166.52 | 12.81 | 11415 | 1429.87 | 18.11 | 0.000 | -0.196 |
| ROBOT | 124.40 | 7.13 | 9025 | 691.40 | 11.69 | -0.046 | -0.001 |
| MICROCHIP | 100.86 | 8.79 | 5595 | 1502.93 | 14.01 | -0.009 | 0.006 |

## family day stability

signed drift: avg of (close-open) over the 5 names in the family. `drift_dispersion`: stdev of those 5 signed drifts — did they move together.

| family | day | spread | trade_vol | signed_drift | abs_drift | drift_dispersion |
|---|---|---|---|---|---|---|
| GALAXY_SOUNDS | D+2 | 13.26 | 2810 | 808.30 | 974.90 | 713.21 |
| GALAXY_SOUNDS | D+3 | 13.90 | 3245 | 358.20 | 635.60 | 621.95 |
| GALAXY_SOUNDS | D+4 | 14.02 | 2970 | -277.30 | 877.50 | 1014.54 |
| MICROCHIP | D+2 | 8.90 | 1710 | 142.20 | 1121.60 | 1309.88 |
| MICROCHIP | D+3 | 8.96 | 1915 | -402.00 | 1777.40 | 1992.17 |
| MICROCHIP | D+4 | 8.51 | 1970 | -491.80 | 1609.80 | 1616.51 |
| OXYGEN_SHAKE | D+2 | 12.80 | 2810 | 170.90 | 1002.90 | 1177.52 |
| OXYGEN_SHAKE | D+3 | 12.87 | 3245 | -180.90 | 625.30 | 797.28 |
| OXYGEN_SHAKE | D+4 | 13.01 | 2970 | 759.50 | 763.50 | 784.62 |
| PANEL | D+2 | 9.56 | 2810 | 4.90 | 760.90 | 922.47 |
| PANEL | D+3 | 9.31 | 3245 | -303.80 | 998.40 | 1183.19 |
| PANEL | D+4 | 9.33 | 2970 | 261.50 | 712.30 | 739.03 |
| PEBBLES | D+2 | 12.81 | 3770 | 0.10 | 1510.90 | 1949.24 |
| PEBBLES | D+3 | 12.82 | 4145 | 0.10 | 1173.30 | 1330.24 |
| PEBBLES | D+4 | 12.81 | 3500 | 0.20 | 1605.40 | 2067.23 |
| ROBOT | D+2 | 7.20 | 2810 | -86.50 | 212.90 | 248.50 |
| ROBOT | D+3 | 7.15 | 3245 | -329.40 | 1357.80 | 1533.29 |
| ROBOT | D+4 | 7.03 | 2970 | 59.30 | 503.50 | 588.90 |
| SLEEP_POD | D+2 | 9.17 | 2810 | 653.80 | 1103.00 | 987.26 |
| SLEEP_POD | D+3 | 9.63 | 3245 | 893.20 | 893.20 | 268.27 |
| SLEEP_POD | D+4 | 10.16 | 2970 | -200.50 | 615.10 | 694.33 |
| SNACKPACK | D+2 | 16.75 | 2810 | 30.90 | 260.30 | 313.59 |
| SNACKPACK | D+3 | 16.81 | 3245 | 4.20 | 138.80 | 179.71 |
| SNACKPACK | D+4 | 16.80 | 2970 | 23.50 | 208.90 | 220.78 |
| TRANSLATOR | D+2 | 8.74 | 2810 | 64.80 | 532.60 | 622.17 |
| TRANSLATOR | D+3 | 8.81 | 3245 | 55.30 | 884.90 | 993.90 |
| TRANSLATOR | D+4 | 8.79 | 2970 | -432.90 | 825.70 | 929.07 |
| UV_VISOR | D+2 | 13.04 | 2810 | 472.80 | 1072.60 | 1096.30 |
| UV_VISOR | D+3 | 13.16 | 3245 | -18.60 | 425.00 | 557.84 |
| UV_VISOR | D+4 | 13.19 | 2970 | -507.90 | 787.10 | 906.17 |

## product passive-mm shortlist

`mm_score = avg_spread * sqrt(trade_volume) / (1 + return_vol)` — triage only.

| product | family | score | spread | trade_vol | abs_drift | acf1 | drifts d2/d3/d4 |
|---|---|---|---|---|---|---|---|
| SNACKPACK_PISTACHIO | SNACKPACK | 108.47 | 15.93 | 1805 | 298.17 | -0.025 | -489/-124/-282 |
| SNACKPACK_VANILLA | SNACKPACK | 95.39 | 16.87 | 1805 | 128.00 | -0.027 | 52/-28/304 |
| SNACKPACK_CHOCOLATE | SNACKPACK | 92.37 | 16.47 | 1805 | 113.67 | -0.031 | -84/-75/-182 |
| SNACKPACK_STRAWBERRY | SNACKPACK | 82.93 | 17.83 | 1805 | 297.00 | -0.014 | 436/358/98 |
| SNACKPACK_RASPBERRY | SNACKPACK | 78.70 | 16.84 | 1805 | 176.50 | -0.017 | 240/-110/180 |
| UV_VISOR_RED | UV_VISOR | 49.58 | 14.04 | 1805 | 574.00 | -0.004 | 842/182/698 |
| GALAXY_SOUNDS_SOLAR_FLAMES | GALAXY_SOUNDS | 49.43 | 14.07 | 1805 | 739.67 | -0.012 | 1346/-694/180 |
| GALAXY_SOUNDS_BLACK_HOLES | GALAXY_SOUNDS | 49.41 | 14.51 | 1805 | 1151.83 | -0.016 | 1446/688/1320 |
| GALAXY_SOUNDS_DARK_MATTER | GALAXY_SOUNDS | 49.31 | 13.05 | 1805 | 497.00 | -0.012 | 417/462/-612 |
| UV_VISOR_ORANGE | UV_VISOR | 49.25 | 13.28 | 1805 | 405.50 | 0.001 | 154/114/-948 |
| UV_VISOR_YELLOW | UV_VISOR | 49.22 | 13.91 | 1805 | 1339.67 | 0.003 | 1568/466/-1986 |
| OXYGEN_SHAKE_MINT | OXYGEN_SHAKE | 49.16 | 12.59 | 1805 | 312.50 | -0.003 | 106/-390/440 |
| OXYGEN_SHAKE_GARLIC | OXYGEN_SHAKE | 49.15 | 15.05 | 1805 | 1299.33 | -0.003 | 1828/111/1958 |
| UV_VISOR_MAGENTA | UV_VISOR | 49.06 | 14.09 | 1805 | 534.17 | -0.003 | 1300/254/-49 |
| GALAXY_SOUNDS_SOLAR_WINDS | GALAXY_SOUNDS | 48.97 | 13.30 | 1805 | 700.17 | -0.008 | -416/1176/-508 |

## family lead/lag candidates

lag in 100-tick bars. filter: meaningful |lag_corr|, not just lift off a weak same-time baseline.

| leader | follower | same_time | lag | lag_corr | lift |
|---|---|---|---|---|---|

## same-family product lead/lag candidates

stricter bar on |lag_corr| so the table is not fake signal from -0.9 same-time corr washing out at lag.

| family | leader | follower | same_time | lag | lag_corr | lift |
|---|---|---|---|---|---|---|

## same-family pair candidates

`spread`: corr ≥ 0, residual `a-b`. `basket`: corr < 0, residual `a+b`.

| family | relation | a | b | corr | resid_std | resid_range | day_mean_range |
|---|---|---|---|---|---|---|---|
| SNACKPACK | basket | SNACKPACK_STRAWBERRY | SNACKPACK_RASPBERRY | -0.924 | 331.58 | 1287.50 | 720.78 |
| SNACKPACK | basket | SNACKPACK_CHOCOLATE | SNACKPACK_VANILLA | -0.916 | 76.20 | 342.00 | 154.95 |
| SNACKPACK | spread | SNACKPACK_PISTACHIO | SNACKPACK_STRAWBERRY | 0.913 | 476.96 | 1899.50 | 1045.61 |
| SNACKPACK | basket | SNACKPACK_PISTACHIO | SNACKPACK_RASPBERRY | -0.831 | 179.77 | 896.00 | 324.83 |
| PEBBLES | basket | PEBBLES_M | PEBBLES_XL | -0.512 | 2117.92 | 9529.50 | 4239.48 |
| PEBBLES | basket | PEBBLES_L | PEBBLES_XL | -0.500 | 1762.73 | 7536.50 | 3710.40 |
| PEBBLES | basket | PEBBLES_XS | PEBBLES_XL | -0.497 | 997.48 | 4170.00 | 308.67 |
| PEBBLES | basket | PEBBLES_S | PEBBLES_XL | -0.496 | 1174.79 | 5094.00 | 1459.37 |
| SNACKPACK | spread | SNACKPACK_VANILLA | SNACKPACK_PISTACHIO | 0.040 | 296.62 | 1453.00 | 448.78 |
| SNACKPACK | spread | SNACKPACK_VANILLA | SNACKPACK_STRAWBERRY | 0.031 | 356.57 | 1881.00 | 596.83 |
| SNACKPACK | spread | SNACKPACK_CHOCOLATE | SNACKPACK_RASPBERRY | 0.031 | 256.88 | 1357.00 | 278.90 |
| SNACKPACK | spread | SNACKPACK_CHOCOLATE | SNACKPACK_PISTACHIO | 0.025 | 200.09 | 1131.00 | 107.35 |
| UV_VISOR | spread | UV_VISOR_ORANGE | UV_VISOR_RED | 0.020 | 615.89 | 3120.50 | 909.79 |
| TRANSLATOR | spread | TRANSLATOR_GRAPHITE_MIST | TRANSLATOR_VOID_BLUE | 0.018 | 726.90 | 2908.50 | 771.49 |
| SNACKPACK | spread | SNACKPACK_CHOCOLATE | SNACKPACK_STRAWBERRY | 0.017 | 501.44 | 2485.00 | 1027.18 |
| PEBBLES | spread | PEBBLES_XS | PEBBLES_M | 0.015 | 1989.51 | 7018.50 | 4257.65 |
| SNACKPACK | spread | SNACKPACK_VANILLA | SNACKPACK_RASPBERRY | 0.014 | 243.66 | 1402.50 | 241.33 |
| GALAXY_SOUNDS | spread | GALAXY_SOUNDS_PLANETARY_RINGS | GALAXY_SOUNDS_SOLAR_FLAMES | 0.014 | 891.85 | 4166.50 | 1437.67 |
| OXYGEN_SHAKE | spread | OXYGEN_SHAKE_MORNING_BREATH | OXYGEN_SHAKE_GARLIC | 0.013 | 1424.57 | 6104.50 | 2930.85 |
| MICROCHIP | spread | MICROCHIP_CIRCLE | MICROCHIP_OVAL | 0.013 | 1838.11 | 6500.50 | 3903.91 |

## what i took from this

- cross-family lead/lag table was empty under the strict filter — i did not build the live trader on cross-family lag.
- `SNACKPACK` looked best on mm_score + internal pairs (berry/choc-vanilla neg corr). still needs causal replay before trusting.
- neg corr pairs → basket/residual framing more honest than pretending they move together.
- i promoted nothing from this file into `trader.py` without rust replay; the skip-list came from per-product replay pnl not from this notebook.
