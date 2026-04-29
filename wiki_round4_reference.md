# Round 4 - "The More The Merrier"

For this second round of the Great Orbital Ascension Trials, the **Frontier Trade Watch** (FTW) has disclosed information about the counterparties active in the market. Their IDs have been added to the historical trade data available in the Data Capsule.

You will continue trading ***Hydrogel Packs*** (`HYDROGEL_PACK`), ***Velvetfruit Extract*** (`VELVETFRUIT_EXTRACT`), and ***10 Velvetfruit Extract Vouchers*** (`VELVETFRUIT_EXTRACT_VOUCHER`). This time, however, having insight into your counterparties, and understanding what defines their trading behavior and the unique opportunities they bring, could shift the balance for teams that know how to separate profit from pretense.

In addition to your algorithmic trading activities, you will also have the opportunity to manually trade the ***Aether Crystal***, along with ***a collection of option contracts*** based on it. Some of these contracts are more exotic than others. You must determine a strategy that turns this one-time opportunity into profit.

Be aware that these exotic options operate independently from your algorithmic trading activities.

## Round Objective

Optimize your Python program to trade `HYDROGEL_PACK`, `VELVETFRUIT_EXTRACT`, and `VELVETFRUIT_EXTRACT_VOUCHER`, incorporating the newly disclosed counterparty information into your strategy.

Select from the available Aether Crystal and corresponding option contracts, and submit your orders to generate additional profit.

## Algorithmic trading challenge: "Hello, I'm Mark"

The products are the same as in Round 3 (`HYDROGEL_PACK`, `VELVETFRUIT_EXTRACT`, and 10 `VELVETFRUIT_EXTRACT_VOUCHER` options), but now you have counterparty information available. That is, you can identify every other participant in the market and study their behavior.

In the datamodel described in Appendix B (`datamodel.py`), you will find the `Trade` class defined. For previous rounds 1, 2, 3, the `self.buyer` and `self.seller` fields were always `None` as no counterparty information was available.

```python
class Trade:
    def __init__(self, symbol: Symbol, price: int, quantity: int,
                 buyer: UserId = None, seller: UserId = None,
                 timestamp: int = 0) -> None:
        self.symbol = symbol
        self.price: int = price
        self.quantity: int = quantity
        self.buyer = buyer
        self.seller = seller
        self.timestamp = timestamp

    # Some methods
```

With increased transparency in the market, the `self.buyer` and `self.seller` fields now represent the names of the participants. Use this information however you see fit to refine your strategy.

### Position limits

- `HYDROGEL_PACK`: 200
- `VELVETFRUIT_EXTRACT`: 200
- `VELVETFRUIT_EXTRACT_VOUCHER`: 300 for each of the 10 vouchers

### Velvetfruit Extract Voucher universe

All vouchers have a TTE of **7 Solvenarian days starting from day 1**. So in round 4 (day 4), TTE = 4 days.

| Symbol     | Strike |
|------------|-------:|
| `VEV_4000` |  4,000 |
| `VEV_4500` |  4,500 |
| `VEV_5000` |  5,000 |
| `VEV_5100` |  5,100 |
| `VEV_5200` |  5,200 |
| `VEV_5300` |  5,300 |
| `VEV_5400` |  5,400 |
| `VEV_5500` |  5,500 |
| `VEV_6000` |  6,000 |
| `VEV_6500` |  6,500 |

> **Example** (building on the example from Round 3): `VEV_5000` is an option with strike price 5000, has TTE=4 days in round 4, and has a position limit of 300.

### Synthia hint — *Anticipating Activity*

> Can we just take a moment to acknowledge how bleak it is that every single counterparty is named Mark? All of them. Same name, different number, zero personality. I don't know what's more unsettling. That someone thought that was acceptable, or that nobody pushed back on it.
>
> You should still watch them. Obviously. Do certain Marks show up at predictable moments? Do they behave the same way each time? Because systems, like people, tend to repeat themselves. They were trained on something and they keep doing that something, which is actually very convenient for you if you pay attention.
>
> Ask yourself what each one is doing and why. Does one resemble a market maker, quietly providing liquidity on a schedule? Is another a liquidity taker, showing up when conditions suit it? Are there larger, clumsier ones whose arrival you can feel before you see it? Those are the interesting ones. The ones that might move the room.
>
> Yes. You should act on your read of the counterparties. Let your read change how you operate. Where you place orders. How you interpret a sudden price shift. Whether a movement is signal or just noise from a Mark that doesn't know any better.
>
> Pattern recognition is the easy part, honestly. Most people can do that. The harder part is actually letting it inform your decisions instead of just feeling clever about having noticed something.
>
> That's it. You can go trade now.

## Manual trading challenge: "Vanilla Just Isn't Exotic Enough"

As the Intarian economy evolved, trading expanded beyond standard calls and puts. In this round, you can trade `AETHER_CRYSTAL`, vanilla options with 2 and 3 week expiries, and several exotic derivatives written on the same underlying.

A "week" here refers to **5 trading days**, with **252 trading days per year**. So "2 weeks" means 10 trading days, and "3 weeks" represents 15 trading days. The official conversion code:

```python
TRADING_DAYS_PER_YEAR = 252
STEPS_PER_DAY = 4
STEPS_PER_YEAR = TRADING_DAYS_PER_YEAR * STEPS_PER_DAY

def weeks_to_years(weeks: float) -> float:
    # 5 business days per week, annualized to 252 trading days
    return (weeks * 5) / TRADING_DAYS_PER_YEAR

def steps_for_weeks(weeks: float) -> int:
    return int(round(weeks * 5 * STEPS_PER_DAY))
```

So "2 weeks" = `2 * 5 * STEPS_PER_DAY` = 40 steps over 10 days; "3 weeks" = 60 steps over 15 days.

### Mechanics

- Construct positions for **positive expected PnL**. Unhedged exposure can lead to large losses, so risk management matters.
- PnL is marked to the **fair value upon expiry**, defined as the **mean payoff across 100 simulations** of the underlying.
- You buy or sell at **t = 0** (start of round 4) and **hold till expiry**. There is no intra-round trading.
- This challenge is completely standalone and has **no relationship to Round 1**.

### Underlying simulation

`AETHER_CRYSTAL` is simulated as Geometric Brownian Motion with:

- **zero risk-neutral drift**
- **fixed annualized volatility σ = 251%** (`σ = 2.51`)
- discrete grid: **4 steps per trading day, 252 trading days per year**

There is no continuous-time modelling under the hood that could trigger a knock-out — only the discrete points are considered.

### Available products

You can trade the underlying, 2-week and 3-week vanilla calls/puts, and three exotics.

#### Chooser Option

Expires in 3 weeks. After 2 weeks, the buyer chooses whether it becomes a call or a put, selecting whichever would be **in the money at that time**. It then behaves like a standard option for the final week until expiry.

#### Binary Put Option

All-or-nothing payoff. If the underlying is below the strike at expiry, it pays the specified amount. Otherwise it expires worthless.

#### Knock-Out Put Option

Behaves like a regular put **unless** the underlying ever trades below the knock-out barrier before expiry. If the barrier is breached at any of the discrete points, the option immediately becomes worthless.

### Contract list

The "contract size" is **3,000** across all products and is purely a PnL multiplier on the per-unit PnL. The per-unit prices in the table are quoted directly. The "Price" column shown in the UI is purely cosmetic ("investment cost") and should be ignored.

| Symbol      | Type            | Expiry    | Strike | Bid    | Ask    | Max Volume | Notes |
|-------------|-----------------|-----------|-------:|-------:|-------:|-----------:|-------|
| `AC`        | underlying      | n/a       |   —    | 49.975 | 50.025 |        200 | Aether Crystal |
| `AC_50_P`   | put             | T+21      |     50 | 12.000 | 12.050 |         50 | |
| `AC_50_C`   | call            | T+21      |     50 | 12.000 | 12.050 |         50 | |
| `AC_35_P`   | put             | T+21      |     35 |  4.330 |  4.350 |         50 | |
| `AC_40_P`   | put             | T+21      |     40 |  6.500 |  6.550 |         50 | |
| `AC_45_P`   | put             | T+21      |     45 |  9.050 |  9.100 |         50 | |
| `AC_60_C`   | call            | T+21      |     60 |  8.800 |  8.850 |         50 | |
| `AC_50_P_2` | put             | T+14      |     50 |  9.700 |  9.750 |         50 | |
| `AC_50_C_2` | call            | T+14      |     50 |  9.700 |  9.750 |         50 | |
| `AC_50_CO`  | chooser         | T+14 / 21 |     50 | 22.200 | 22.300 |         50 | choose call/put at T+14 |
| `AC_40_BP`  | binary put      | T+21      |     40 |  5.000 |  5.100 |         50 | pays 10 if `S_21 < 40` |
| `AC_45_KO`  | knock-out put   | T+21      |     45 |  0.150 |  0.175 |        500 | barrier 35; KO if breached |

### Submitting

Enter orders (side and volume) directly in the Manual Challenge Overview window and click **Submit**. You can re-submit until the round ends; only the last submission is processed. The "Total investment" shown is cosmetic.

### Synthia hint — *Combining Vanillas and Exotics*

> Exotic options. Sure. They sound impressive. Attractive payoffs, interesting structures, the whole thing. And then you look a little closer and realize they are also sensitive to basically everything. The spot price. The timing. The exact path the underlying took to get there. All of it. Which is fine, until it isn't.
>
> So before you get too attached to your exotic position, ask yourself whether part of that exposure could be replicated with vanilla options. Calls and puts are less spectacular, yes. Deliberately so. That is actually the point. Less spectacular usually means a bit easier to price. It means it does not suddenly behave differently because the underlying took an unexpected detour on the way to where you thought it was going.
>
> Look at the exotic payoff on its own first. Then see what happens when you layer vanillas alongside it. Does the combination smooth out the extreme outcomes? Does it make the whole thing less dependent on one very specific scenario playing out perfectly? It usually does. Not always in a dramatic way. But enough to matter when things get weird.
>
> The goal is not to turn your exotic into a vanilla. It is to build something around it that does not fall apart the moment conditions shift. Control the exposure. Do not let the exposure control you.
>
> I'm going to stop right here. If I did any more explaining, it would look an awful lot like work.

### Synthia hint — *Choosing a Strategy for Chooser Options*

> Okay so a chooser option has two phases and they are not the same thing. Like, at all. Treating them like they are is how people end up confused and slightly poorer than they expected.
>
> In the first phase you still get to decide whether the option becomes a call or a put. That flexibility is worth something. An actual measurable something. Ask yourself whether you could approximate that exposure using vanilla options. A combination of calls and puts might get you close enough to give you a useful reference point for what that optionality is actually worth right now. Which is good to know before you do anything else.
>
> Then the decision window closes. And everything changes. The option type gets fixed and suddenly you are not dealing with open-ended flexibility anymore. You are dealing with a directional position that has a very specific opinion about where the underlying is going. That is a completely different situation and it needs a completely different approach.
>
> So manage the two phases separately. What works in the first phase might not serve you well in the second. The transition is the part most people gloss over because it feels like a formality. It is not. It is the whole thing.
>
> Two phases. Two frameworks. Don't mix them up. Please.

### Synthia hint — *Binary, Knock-Out and Risk*

> Right. These two. Pay attention because the risk in both of them is concentrated in a way that catches people off guard.
>
> The binary put is all about one number. One threshold. Everything concentrates there. That kind of abrupt shift is very different from a standard put where the payoff changes gradually and gives you room to think. Here it does not. It just flips. Which is fine if you are positioned correctly and a little catastrophic if you are not.
>
> The knock-out put is weirder. Its value does not just shift at a threshold. It can disappear entirely depending on how the underlying got there. Not where it ended up. How it traveled. A position that looked completely reasonable at entry can simply stop existing before it ever pays out. Cool feature. Terrible to be on the wrong side of it.
>
> In both cases, think about whether vanilla options could soften the extreme scenarios. A well placed vanilla position can soften the binary cliff. It can cushion the knock-out risk before it becomes your whole problem. Yes, combining them reshapes the payoff. But a payoff you actually understand under bad conditions beats an elegant one that surprises you at the worst possible moment.
>
> When payoffs are discontinuous, risk management stops being about direction and starts being about structure. Which is a more interesting problem, if you think about it. So there's that.

## Tradable good — Aether Crystal flavor text

Aether Crystals (AETHER-CRYSTAL) are precision-grown minerals formed under controlled electromagnetic conditions. Each crystal stores and stabilizes ambient energy fluctuations, making them invaluable in advanced communication systems, architectural harmonics, and precision instrumentation.

## Algorithmic Challenge brief (FTW disclosure)

The FTW has identified your trading counterparties as products of several local neuro-robotics research programs. Surprisingly, they are all named **"Mark" followed by a number**. These IDs have been added to the historical trade data in the Data Capsule. Use this information to re-evaluate your strategy for trading Hydrogel Packs, Velvetfruit Extract, and VEVs.
