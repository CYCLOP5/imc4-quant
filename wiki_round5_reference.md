# Round 5 - "The Final Stretch"

Round 5 replaces all previous algorithmic products with **50 new tradable goods**. Previous-round symbols are not tradeable. Submit one final Python program before the round closes.

The **Data Capsule** contains historical performance data for all 50 algorithmic goods. The **A.R.I.A. Uplink** publishes three notes: *Same but Slower*, *It's a Lot*, and *Pairing for Profit*. The **Ashflow Alpha** newsletter informs the separate **Ignith manual** portfolio; it does not interact with algorithmic positions.

## Round Objective

Write one program to trade the 50 goods. The point is not to quote every symbol if there's no edge — find families and products with repeatable structure, then trade them for a reason you can explain.

Manual trading is disconnected: one Ignith ticket from Ashflow Alpha, locked at round close.

## Algorithmic challenge: Cherry Picking Winners

Position limit **10** for each of the 50 products.

### TG01 - Galaxy Sounds Recordings

- `GALAXY_SOUNDS_DARK_MATTER`
- `GALAXY_SOUNDS_BLACK_HOLES`
- `GALAXY_SOUNDS_PLANETARY_RINGS`
- `GALAXY_SOUNDS_SOLAR_WINDS`
- `GALAXY_SOUNDS_SOLAR_FLAMES`

### TG02 - Vertical Sleeping Pods

- `SLEEP_POD_SUEDE`
- `SLEEP_POD_LAMB_WOOL`
- `SLEEP_POD_POLYESTER`
- `SLEEP_POD_NYLON`
- `SLEEP_POD_COTTON`

### TG03 - Organic Microchip Modules

- `MICROCHIP_CIRCLE`
- `MICROCHIP_OVAL`
- `MICROCHIP_SQUARE`
- `MICROCHIP_RECTANGLE`
- `MICROCHIP_TRIANGLE`

### TG04 - Purification Pebbles

- `PEBBLES_XS`
- `PEBBLES_S`
- `PEBBLES_M`
- `PEBBLES_L`
- `PEBBLES_XL`

### TG05 - Domestic Robotics

- `ROBOT_VACUUMING`
- `ROBOT_MOPPING`
- `ROBOT_DISHES`
- `ROBOT_LAUNDRY`
- `ROBOT_IRONING`

### TG06 - UV-Visors

- `UV_VISOR_YELLOW`
- `UV_VISOR_AMBER`
- `UV_VISOR_ORANGE`
- `UV_VISOR_RED`
- `UV_VISOR_MAGENTA`

### TG07 - Instant Translators

- `TRANSLATOR_SPACE_GRAY`
- `TRANSLATOR_ASTRO_BLACK`
- `TRANSLATOR_ECLIPSE_CHARCOAL`
- `TRANSLATOR_GRAPHITE_MIST`
- `TRANSLATOR_VOID_BLUE`

### TG08 - Construction Panels

- `PANEL_1X2`
- `PANEL_2X2`
- `PANEL_1X4`
- `PANEL_2X4`
- `PANEL_4X4`

### TG09 - Liquid Breath Oxygen Shakes

- `OXYGEN_SHAKE_MORNING_BREATH`
- `OXYGEN_SHAKE_EVENING_BREATH`
- `OXYGEN_SHAKE_MINT`
- `OXYGEN_SHAKE_CHOCOLATE`
- `OXYGEN_SHAKE_GARLIC`

### TG10 - Protein Snack Packs

- `SNACKPACK_CHOCOLATE`
- `SNACKPACK_VANILLA`
- `SNACKPACK_PISTACHIO`
- `SNACKPACK_STRAWBERRY`
- `SNACKPACK_RASPBERRY`

## A.R.I.A. Uplink — Same but Slower

> Related products do not just look the same — some move first and others catch up later. The edge is not "they correlate"; it is "there is a stable delay". Measure lag inside categories and across aggregates, but only trust what still works when the follower can only see the leader's **past** timestamps. A lag table without causality is not a strategy.

## A.R.I.A. Uplink — It's a Lot

> Fifty names are too many to micromanage on day one. Start with the **ten families**: spread, traded volume, drift, mean reversion, how the passive starter makes money. Rank groups, then drill into the good groups.

## A.R.I.A. Uplink — Pairing for Profit

> Strong clusters deserve a story. Inside a promising family, look for **pairs**: correlation, spread variance, range, whether residuals mean-revert. Use pairs to confirm or kill a headline signal — do not trade the correlation table blind.

## Manual challenge: Extra! Extra! Read All About It!

One-day **Ignith** portfolio using **Ashflow Alpha**. Budget **`1,000,000`** XIRECs. You may allocate less than 100%; unused budget does not roll into PnL. Used capital and fees reduce PnL. Last submission before close locks.

The wiki's fee line is garbled in some copies:

```text
fee = (volume_for_specific_product / 100) * (volume_for_specific_product / 100) ** budget
```

The **worked narrative** in the same document is the quadratic rule on percent: e.g. **10%** of budget costs **`0.1 × 0.1 × 1,000,000 = 10,000`** XIRECs in fees. Cross-check the live **fee** field on one line before you submit.

**Goods**

- Obsidian cutlery
- Pyroflex cells
- Thermalite core
- Lava cake
- Magma ink
- Scoria paste
- Ashes of the Phoenix
- Volcanic incense
- Sulfur reactor

**Per line**

- Buy or sell
- Percent allocation
- Investment (usually auto)
- Fee (usually auto)

**Constraints**

- Total allocation ≤ 100%
- Used budget + fees hit PnL
- Unused budget expires
- Final ticket is the last save before deadline
