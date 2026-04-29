import json
import pandas as pd
with open('LOGS/118510/118510.log') as f:
    data = json.load(f)
trade_hist = data.get('tradeHistory', [])
df = pd.DataFrame(trade_hist)
for sym in df['symbol'].unique():
    sym_df = df[df['symbol'] == sym].copy()
    buys = sym_df[sym_df['buyer'] == 'SUBMISSION']
    sells = sym_df[sym_df['seller'] == 'SUBMISSION']
    print(f'[{sym}]')
    print(f'Total Trades: {len(sym_df)}')
    if len(buys) > 0 and len(sells) > 0:
        qty_b = buys['quantity'].sum()
        qty_s = sells['quantity'].sum()
        avg_buy = (buys['price'] * buys['quantity']).sum() / qty_b
        avg_sell = (sells['price'] * sells['quantity']).sum() / qty_s
        print(f'Total Buys: {len(buys)} for {qty_b} units')
        print(f'Total Sells: {len(sells)} for {qty_s} units')
        print(f'Avg Buy: {avg_buy:.2f}')
        print(f'Avg Sell: {avg_sell:.2f}')
        print(f'Realized Spread: {avg_sell - avg_buy:.2f}')
    print()
