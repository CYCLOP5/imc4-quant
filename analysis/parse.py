import json
with open('LOGS/121448/121448.log') as f:
    data = json.load(f)
for k in data.keys():
    print(k, type(data[k]))
trades = []
for item in data.get('activitiesLog', []):
    trades.extend(item.get('activities', []))
pnl = {'ASH_COATED_OSMIUM': 0, 'INTARIAN_PEPPER_ROOT': 0}
pos = {'ASH_COATED_OSMIUM': 0, 'INTARIAN_PEPPER_ROOT': 0}
for row in data.get('sandboxLogs', []):
    log_text = row.get('log', '')
    if 'Profit' in log_text or 'PnL' in log_text:
        print(log_text)
trade_pnl = 0
for l in data.get('activitiesLog', []):
    for tr in l.get('activities', []):
        symbol = tr['symbol']
        price = tr['price']
        qty = tr['quantity']
        buyer = tr['buyer']
        seller = tr['seller']
        if buyer == 'SUBMISSION':
            pos[symbol] += qty
            pnl[symbol] -= price * qty
        elif seller == 'SUBMISSION':
            pos[symbol] -= qty
            pnl[symbol] += price * qty
print('Raw PnL (unrealized):', pnl)
print('Ending Pos:', pos)
print('Final PnL (mark to market roughly):', pnl['ASH_COATED_OSMIUM'] + pos['ASH_COATED_OSMIUM'] * 10000 + pnl['INTARIAN_PEPPER_ROOT'] + pos['INTARIAN_PEPPER_ROOT'] * 12000)
