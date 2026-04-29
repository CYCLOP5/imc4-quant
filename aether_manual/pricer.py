from __future__ import annotations
import math
import sys
from dataclasses import dataclass, field
import numpy as np
S0 = 50.0
SIGMA = 2.51
STEPS_PER_DAY = 4
TRADING_DAYS_PER_YEAR = 252
DT = 1.0 / (STEPS_PER_DAY * TRADING_DAYS_PER_YEAR)
CONTRACT_SIZE = 3000
WEEKS_21 = 3
WEEKS_14 = 2
TRADING_DAYS_21 = WEEKS_21 * 5
TRADING_DAYS_14 = WEEKS_14 * 5
STEPS_21 = TRADING_DAYS_21 * STEPS_PER_DAY
STEPS_14 = TRADING_DAYS_14 * STEPS_PER_DAY
N_MAIN = 200000
N_SCORE = 100
N_RESAMPLE = 1000
SEED = 42

def simulate(N: int, steps: int, dt: float, sigma: float, S0: float) -> np.ndarray:
    drift = -0.5 * sigma * sigma * dt
    diffusion = sigma * math.sqrt(dt)
    z = np.random.standard_normal((N, steps))
    log_increments = drift + diffusion * z
    log_paths = np.cumsum(log_increments, axis=1)
    log_paths = np.concatenate([np.zeros((N, 1)), log_paths], axis=1)
    return S0 * np.exp(log_paths)

def _norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

def bs_price(S: float, K: float, T: float, sigma: float, is_call: bool) -> float:
    if T <= 0:
        return max(0.0, S - K if is_call else K - S)
    sigT = sigma * math.sqrt(T)
    d1 = (math.log(S / K) + 0.5 * sigT * sigT) / sigT
    d2 = d1 - sigT
    if is_call:
        return S * _norm_cdf(d1) - K * _norm_cdf(d2)
    return K * _norm_cdf(-d2) - S * _norm_cdf(-d1)

def chooser_payoff(s_mid: np.ndarray, s_term: np.ndarray, K: float) -> np.ndarray:
    to_call = s_mid >= K
    call_payoff = np.maximum(s_term - K, 0.0)
    put_payoff = np.maximum(K - s_term, 0.0)
    return np.where(to_call, call_payoff, put_payoff)

def ko_put_payoff(min_path: np.ndarray, s_term: np.ndarray, K: float, barrier: float) -> np.ndarray:
    knocked_out = min_path < barrier
    return np.where(knocked_out, 0.0, np.maximum(K - s_term, 0.0))

def score_std(payoffs: np.ndarray, n_score: int=N_SCORE, n_resample: int=N_RESAMPLE, rng: np.random.Generator | None=None) -> float:
    if rng is None:
        rng = np.random.default_rng(123)
    n = len(payoffs)
    means = np.empty(n_resample)
    for i in range(n_resample):
        idx = rng.integers(0, n, size=n_score)
        means[i] = payoffs[idx].mean()
    return float(means.std(ddof=1))

@dataclass
class Contract:
    name: str
    kind: str
    bid: float
    ask: float
    size: int
    payoff: np.ndarray = field(repr=False)

def main() -> None:
    np.random.seed(SEED)
    print('=' * 88)
    print(' AETHER CRYSTAL manual options pricer  --  IMC Prosperity Round 4')
    print('=' * 88)
    print(f' S0={S0}  sigma={SIGMA}  dt=1/(4*252)={DT:.6f}  contract_size={CONTRACT_SIZE}')
    print(f' Simulating {N_MAIN:,} GBM paths over {STEPS_21} steps (T+21 = 3wk = 15 trading days).')
    print(f' Mid-life check at step {STEPS_14} (T+14 = 2wk = 10 trading days, for chooser/T+14 vanillas).')
    print(f' Score-noise = std of mean across {N_RESAMPLE:,} resamples of {N_SCORE} paths.')
    print()
    paths = simulate(N_MAIN, STEPS_21, DT, SIGMA, S0)
    s_21 = paths[:, -1]
    s_14 = paths[:, STEPS_14]
    min_path = paths.min(axis=1)
    T21 = TRADING_DAYS_21 / TRADING_DAYS_PER_YEAR
    T14 = TRADING_DAYS_14 / TRADING_DAYS_PER_YEAR
    bs_atm_call_21 = bs_price(S0, 50.0, T21, SIGMA, is_call=True)
    bs_atm_put_21 = bs_price(S0, 50.0, T21, SIGMA, is_call=False)
    bs_atm_call_14 = bs_price(S0, 50.0, T14, SIGMA, is_call=True)
    bs_atm_put_14 = bs_price(S0, 50.0, T14, SIGMA, is_call=False)
    print(' BLACK-SCHOLES sanity checks (r=0):')
    print(f'   T+21 = 3wk = 15 trading days = {STEPS_21} steps; sigma*sqrt(T)={SIGMA * math.sqrt(T21):.4f}')
    print(f'   T+14 = 2wk = 10 trading days = {STEPS_14} steps; sigma*sqrt(T)={SIGMA * math.sqrt(T14):.4f}')
    print(f'   ATM call 21d  BS={bs_atm_call_21:7.4f}  MC={np.maximum(s_21 - 50, 0).mean():7.4f}')
    print(f'   ATM put  21d  BS={bs_atm_put_21:7.4f}  MC={np.maximum(50 - s_21, 0).mean():7.4f}')
    print(f'   ATM call 14d  BS={bs_atm_call_14:7.4f}  MC={np.maximum(s_14 - 50, 0).mean():7.4f}')
    print(f'   ATM put  14d  BS={bs_atm_put_14:7.4f}  MC={np.maximum(50 - s_14, 0).mean():7.4f}')
    print(f'   E[S_21]  BS=50.0000  MC={s_21.mean():7.4f}    (martingale test)')
    print(f'   E[S_14]  BS=50.0000  MC={s_14.mean():7.4f}')
    print(f'   P(S_21 < 35)  BS={_norm_cdf((math.log(35 / 50) + 0.5 * SIGMA ** 2 * T21) / (SIGMA * math.sqrt(T21))):7.4f}  MC={(s_21 < 35).mean():7.4f}')
    print(f'   P(min path < 35) MC={(min_path < 35).mean():7.4f}  (knock-out probability)')
    print()
    contracts = [Contract('AC', 'underlying', 49.975, 50.025, 200, s_21.copy()), Contract('AC_50_P', 'put 21d', 12.0, 12.05, 50, np.maximum(50 - s_21, 0.0)), Contract('AC_50_C', 'call 21d', 12.0, 12.05, 50, np.maximum(s_21 - 50, 0.0)), Contract('AC_35_P', 'put 21d', 4.33, 4.35, 50, np.maximum(35 - s_21, 0.0)), Contract('AC_40_P', 'put 21d', 6.5, 6.55, 50, np.maximum(40 - s_21, 0.0)), Contract('AC_45_P', 'put 21d', 9.05, 9.1, 50, np.maximum(45 - s_21, 0.0)), Contract('AC_60_C', 'call 21d', 8.8, 8.85, 50, np.maximum(s_21 - 60, 0.0)), Contract('AC_50_P_2', 'put 14d', 9.7, 9.75, 50, np.maximum(50 - s_14, 0.0)), Contract('AC_50_C_2', 'call 14d', 9.7, 9.75, 50, np.maximum(s_14 - 50, 0.0)), Contract('AC_50_CO', 'chooser', 22.2, 22.3, 50, chooser_payoff(s_14, s_21, 50.0)), Contract('AC_40_BP', 'binary put', 5.0, 5.1, 50, np.where(s_21 < 40, 10.0, 0.0)), Contract('AC_45_KO', 'KO put 35', 0.15, 0.175, 500, ko_put_payoff(min_path, s_21, 45.0, 35.0))]
    rng = np.random.default_rng(123)
    rows: list[dict] = []
    total_pnl_per_path = np.zeros(N_MAIN, dtype=np.float64)
    for c in contracts:
        po = c.payoff
        mu = float(po.mean())
        sd = float(po.std(ddof=1))
        mc_se = sd / math.sqrt(N_MAIN)
        sc_sd = score_std(po, rng=rng)
        edge_buy = mu - c.ask
        edge_sell = c.bid - mu
        force_skip = c.name == 'AC'
        if not force_skip and edge_buy > 0 and (edge_buy >= max(edge_sell, 0)):
            action = 'BUY'
            edge = edge_buy
            volume = c.size
            pnl_per_unit_per_path = (po - c.ask) * CONTRACT_SIZE
        elif not force_skip and edge_sell > 0:
            action = 'SELL'
            edge = edge_sell
            volume = c.size
            pnl_per_unit_per_path = (c.bid - po) * CONTRACT_SIZE
        else:
            action = 'SKIP'
            edge = max(edge_buy, edge_sell)
            volume = 0
            pnl_per_unit_per_path = np.zeros(N_MAIN)
        ev_total = edge * CONTRACT_SIZE * volume
        path_pnl_contrib = pnl_per_unit_per_path * volume
        total_pnl_per_path += path_pnl_contrib
        warnings = []
        if mu > 1e-06 and sd > 0.3 * mu:
            warnings.append(f'sd_payoff={sd:.2f} > 30% of mean ({mu:.2f})')
        if edge > 0 and sc_sd > edge:
            warnings.append(f'score_std={sc_sd:.3f} > edge ({edge:.3f}) -- 100-sim noise dominates')
        if edge > 0 and mc_se * 2 > edge:
            warnings.append(f'MC SE={mc_se:.4f} not <<edge -- MC fair value uncertain')
        if c.name == 'AC' and action != 'SKIP':
            warnings.append('underlying is a martingale; true edge equals MC noise')
        rows.append({'name': c.name, 'kind': c.kind, 'bid': c.bid, 'ask': c.ask, 'fair': mu, 'sd_payoff': sd, 'mc_se': mc_se, 'score_sd': sc_sd, 'edge': edge, 'action': action, 'volume': volume, 'ev_total': ev_total, 'path_pnl': path_pnl_contrib, 'warnings': warnings})
    print(' PER-CONTRACT PRICING')
    print(' ' + '-' * 130)
    header = f" {'Contract':<11} {'Kind':<11} {'Bid':>7} {'Ask':>7} {'Fair':>9} {'sdPay':>8} {'MC SE':>8} {'ScoreSD':>9} {'Edge':>9} {'Act':>5} {'Vol':>4} {'EV ($)':>15}"
    print(header)
    print(' ' + '-' * 130)
    for r in rows:
        print(f" {r['name']:<11} {r['kind']:<11} {r['bid']:>7.3f} {r['ask']:>7.3f} {r['fair']:>9.4f} {r['sd_payoff']:>8.3f} {r['mc_se']:>8.4f} {r['score_sd']:>9.4f} {r['edge']:>+9.4f} {r['action']:>5} {r['volume']:>4} {r['ev_total']:>+15,.0f}")
    print()
    total_ev = sum((r['ev_total'] for r in rows))
    print('=' * 88)
    print(' RECOMMENDED ORDER TICKET')
    print('=' * 88)
    n_actions = 0
    for r in rows:
        if r['action'] == 'SKIP':
            continue
        side_px = r['ask'] if r['action'] == 'BUY' else r['bid']
        print(f"   {r['action']:<4} {r['volume']:>4} x {r['name']:<11} @ {side_px:>7.3f}    fair={r['fair']:>8.3f}  edge={r['edge']:>+8.4f}/unit   EV = ${r['ev_total']:>+13,.0f}")
        n_actions += 1
    if n_actions == 0:
        print('   (no positive-edge trades found)')
    print('-' * 88)
    print(f'   TOTAL EXPECTED PNL:  ${total_ev:>+15,.0f}')
    print()
    pcts = [1, 5, 10, 25, 50, 75, 90, 95, 99]
    pct_vals = np.percentile(total_pnl_per_path, pcts)
    print(' JOINT PNL DISTRIBUTION (true model -- before scoring noise)')
    print(' ' + '-' * 70)
    print(f'   mean    = ${total_pnl_per_path.mean():>+15,.0f}    (matches sum of EVs above)')
    print(f'   std     = ${total_pnl_per_path.std(ddof=1):>+15,.0f}')
    print(f'   min     = ${total_pnl_per_path.min():>+15,.0f}')
    print(f'   max     = ${total_pnl_per_path.max():>+15,.0f}')
    for p, v in zip(pcts, pct_vals):
        print(f'   p{p:02d}     = ${v:>+15,.0f}')
    print()
    print(' WORST-CASE / BEST-CASE PNL  (at the recommended sizes)')
    print(' ' + '-' * 70)
    worst1 = np.percentile(total_pnl_per_path, 1)
    worst5 = np.percentile(total_pnl_per_path, 5)
    best95 = np.percentile(total_pnl_per_path, 95)
    best99 = np.percentile(total_pnl_per_path, 99)
    p_loss = float((total_pnl_per_path < 0).mean())
    print(f'   1%-tail loss:   ${worst1:>+15,.0f}')
    print(f'   5%-tail loss:   ${worst5:>+15,.0f}')
    print(f'   95%-tail gain:  ${best95:>+15,.0f}')
    print(f'   99%-tail gain:  ${best99:>+15,.0f}')
    print(f'   P(total PnL < 0) = {p_loss:.3f}')
    print()
    print(' RISK WARNINGS')
    print(' ' + '-' * 70)
    any_warn = False
    for r in rows:
        if r['warnings']:
            any_warn = True
            for w in r['warnings']:
                print(f"   [{r['name']}]  {w}")
    if not any_warn:
        print('   (none)')
    print()
    print(' 100-SIM SCORE-NOISE IMPACT ON ORDER-TICKET PNL')
    print(' ' + '-' * 70)
    rng2 = np.random.default_rng(321)
    score_pnls = np.zeros(N_RESAMPLE)
    for i in range(N_RESAMPLE):
        idx = rng2.integers(0, N_MAIN, size=N_SCORE)
        for r in rows:
            if r['action'] == 'SKIP':
                continue
            score_pnls[i] += r['path_pnl'][idx].mean() * 1
    print(f'   mean realised PnL across {N_RESAMPLE} N=100 trials: ${score_pnls.mean():>+13,.0f}')
    print(f'   std  realised PnL across {N_RESAMPLE} N=100 trials: ${score_pnls.std(ddof=1):>+13,.0f}')
    print(f'   5%-tail realised PnL: ${np.percentile(score_pnls, 5):>+13,.0f}')
    print(f'   95%-tail realised PnL: ${np.percentile(score_pnls, 95):>+13,.0f}')
    print(f'   P(score PnL < 0): {float((score_pnls < 0).mean()):.3f}')
    print()
    CONS_RATIO = 0.3
    print()
    print('=' * 88)
    print(f' CONSERVATIVE TICKET  --  only trades where edge >= {CONS_RATIO:.0%} of score-sd')
    print('=' * 88)
    cons_rows = [r for r in rows if r['action'] != 'SKIP' and r['edge'] >= CONS_RATIO * r['score_sd']]
    cons_total_ev = 0.0
    cons_pnl = np.zeros(N_MAIN, dtype=np.float64)
    for r in cons_rows:
        side_px = r['ask'] if r['action'] == 'BUY' else r['bid']
        print(f"   {r['action']:<4} {r['volume']:>4} x {r['name']:<11} @ {side_px:>7.3f}    fair={r['fair']:>8.3f}  edge={r['edge']:>+8.4f}/unit  scoreSD={r['score_sd']:.3f}  EV = ${r['ev_total']:>+13,.0f}")
        cons_total_ev += r['ev_total']
        cons_pnl += r['path_pnl']
    if not cons_rows:
        print('   (no trades pass the 0.5*score_sd filter)')
    print('-' * 88)
    print(f'   TOTAL CONSERVATIVE EV:  ${cons_total_ev:>+15,.0f}')
    print()
    if cons_rows:
        rng3 = np.random.default_rng(789)
        cons_score_pnls = np.zeros(N_RESAMPLE)
        for i in range(N_RESAMPLE):
            idx = rng3.integers(0, N_MAIN, size=N_SCORE)
            cons_score_pnls[i] = cons_pnl[idx].mean()
        print(f'   conservative-ticket bootstrap (N=100 score sims):')
        print(f'     mean realised PnL: ${cons_score_pnls.mean():>+13,.0f}')
        print(f'     std  realised PnL: ${cons_score_pnls.std(ddof=1):>+13,.0f}')
        print(f'     5%-tail:           ${np.percentile(cons_score_pnls, 5):>+13,.0f}')
        print(f'     95%-tail:          ${np.percentile(cons_score_pnls, 95):>+13,.0f}')
        print(f'     P(score PnL < 0):  {float((cons_score_pnls < 0).mean()):.3f}')
    print()
    print('=' * 88)
    print(' END OF REPORT')
    print('=' * 88)
if __name__ == '__main__':
    sys.exit(main())
