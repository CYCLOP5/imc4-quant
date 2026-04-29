import json
import sys
with open(sys.argv[1]) as f:
    d = json.load(f)
tr = d.get('tradeHistory', [])
pnl = {'ASH_COATED_OSMIUM': 0, 'INTARIAN_PEPPER_ROOT': 0}
pos = {'ASH_COATED_OSMIUM': 0, 'INTARIAN_PEPPER_ROOT': 0}
vol = {'ASH_COATED_OSMIUM': 0, 'INTARIAN_PEPPER_ROOT': 0}
for k in tr:
    sym = k['symbol']
    buyer = k['buyer']
    seller = k['seller']
    q = k['quantity']
    p = k['price']
    if buyer == 'SUBMISSION':
        pos[sym] += q
        pnl[sym] -= p * q
        vol[sym] += q
    elif seller == 'SUBMISSION':
        pos[sym] -= q
        pnl[sym] += p * q
        vol[sym] += q
print('Raw PnL:', pnl)
print('Pos:', pos)
print('Vol:', vol)
print('FV PnL M2M:', pnl['ASH_COATED_OSMIUM'] + pos['ASH_COATED_OSMIUM'] * 10000 + pnl['INTARIAN_PEPPER_ROOT'] + pos['INTARIAN_PEPPER_ROOT'] * 12000)
