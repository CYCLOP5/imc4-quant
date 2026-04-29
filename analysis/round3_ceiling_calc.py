LIMITS = {'HYDROGEL_PACK': 200, 'VELVETFRUIT_EXTRACT': 200, 'VEV_4000': 300, 'VEV_4500': 300, 'VEV_5000': 300, 'VEV_5100': 300, 'VEV_5200': 300, 'VEV_5300': 300, 'VEV_5400': 300, 'VEV_5500': 300, 'VEV_6000': 300, 'VEV_6500': 300}
DRIFT = {'HYDROGEL_PACK': -7.0, 'VELVETFRUIT_EXTRACT': -63.5, 'VEV_4000': -64.0, 'VEV_4500': -63.5, 'VEV_5000': -62.5, 'VEV_5100': -60.0, 'VEV_5200': -49.5, 'VEV_5300': -32.0, 'VEV_5400': -15.0, 'VEV_5500': -5.5, 'VEV_6000': 0.0, 'VEV_6500': 0.0}
ACTUAL = {'HYDROGEL_PACK': 40107, 'VELVETFRUIT_EXTRACT': 1523, 'VEV_4000': -15942, 'VEV_4500': -9037, 'VEV_5000': 321, 'VEV_5100': 360, 'VEV_5200': -68, 'VEV_5300': 110, 'VEV_5400': 3, 'VEV_5500': 0, 'VEV_6000': 0, 'VEV_6500': 0}
print(f"{'product':22s} {'lim':>4s} {'drift':>7s} {'maxShortMTM':>12s} {'maxLongMTM':>12s} {'actual':>10s}")
total_short = 0
total_long = 0
total_act = 0
for p, lim in LIMITS.items():
    d = DRIFT[p]
    short_mtm = -lim * d
    long_mtm = lim * d
    a = ACTUAL[p]
    total_short += short_mtm
    total_long += long_mtm
    total_act += a
    print(f'{p:22s} {lim:>4d} {d:>+7.1f} {short_mtm:>+12,.0f} {long_mtm:>+12,.0f} {a:>+10,.0f}')
print('-' * 76)
print(f"{'TOTAL':22s}      {'':7s} {total_short:>+12,.0f} {total_long:>+12,.0f} {total_act:>+10,.0f}")
print()
print('hypothetical: same strategy but DEEP_ITM_TREND_BETA=+0.5 (momentum)')
print('  -> would have been SHORT vouchers as velvet fell')
print(f'  -> est swing on VEV_4000+4500 alone: ~+38,000 (from −25k to ~+13k)')
print(f'  -> hypothetical algo total: 17,377 + 38,000 = ~55,000')
print()
print('perfect-foresight max-short ceiling: ', f'{total_short:+,.0f}', '(no fees/slippage)')
print('top algo actual                    : +345,941')
print('our actual                          : +17,377')
