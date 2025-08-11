import requests
import json
import time
from hyperliquid.exchange import Exchange
from hyperliquid.utils import constants
from hyperliquid.info import Info
import positions_QuantiHL as positionsHL

def usd_to_size(symbol, leverage, usd_size, is_buy):
    
    usd_size = float(usd_size)
    price = ask_bid(symbol)[0 if is_buy else 1]

    size = (usd_size / price) * leverage
    size = float(size)
    rounding = get_sz_px_decimals(symbol)[0]
    size = round(size, rounding)

    return size

def ask_bid(symbol):
    'this gets the bid ask for any symbol passed in'

    url = 'https://api.hyperliquid.xyz/info'
    headers = {'Content-Type': 'application/json'}

    data = {
        'type': 'l2Book',
        'coin': symbol
    } 

    response = requests.post(url, headers=headers, data=json.dumps(data))
    l2_data = response.json()
    l2_data = l2_data['levels']

    # get bid ask
    bid = float(l2_data[0][0]['px'])
    ask = float(l2_data[1][0]['px'])

    return ask, bid, l2_data

def get_sz_px_decimals(symbol):
    'This return size decimals and price decimals'
    url = 'https://api.hyperliquid.xyz/info'
    headers = {'Content-Type': 'application/json'}
    data = {'type': 'meta'}

    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        data = response.json()
        symbols = data['universe']
        symbol_info = next((s for s in symbols if s['name'] == symbol), None)
        if symbol_info:
            sz_decimals = symbol_info['szDecimals']
        
        else:
            print('Symbol not found')
    
    else:
         print('Error', response.status_code)
        
    
    ask = ask_bid(symbol)[0]

    ask_str = str(ask)

    if '.' in ask_str:
        px_decimals = len(ask_str.split('.')[1])
    else:
        px_decimals = 0
    
    return sz_decimals, px_decimals

def limit_order(coin, is_buy, size, leverage, limit_px, reduce_only, account):
    
    exchange = Exchange(account, constants.MAINNET_API_URL)
    exchange.update_leverage(leverage, coin, is_cross=True)

    #rounding = get_sz_px_decimals(coin)[0]
    #sz = round(size, rounding)
    try:
        order_result = exchange.order(coin, is_buy, size, limit_px, {"limit": {"tif": 'Gtc'}}, reduce_only=reduce_only)
        erreur = ""
    except Exception as e:
        if "Insufficient margin" in str(e):
            erreur = "Insufficient margin to place order"
        elif f"Order price cannot be more than 80% away" in str(e):
            erreur = f"Order price cannot be more than 80% away from the current price"

    try:
        order_id = int(order_result['response']['data']['statuses'][0]['resting']['oid'])
    except:
        print(order_result['response']['data']['statuses'][0])
        order_id = int(order_result['response']['data']['statuses'][0]['filled']['oid'])

    if is_buy == True:
        print(f"limit BUY order placed, resting: {order_result['response']['data']['statuses'][0]}")
    else:
        print(f"limit SELL order placed, resting: {order_result['response']['data']['statuses'][0]}")

    return order_result, order_id, erreur

def market_open(coin, is_buy, usd_size, leverage, px, reduce_only, account):
    exchange = Exchange(account, constants.MAINNET_API_URL)
    exchange.update_leverage(leverage, coin)

    sz = usd_to_size(coin, leverage, usd_size, is_buy)
    rounding = get_sz_px_decimals(coin)[0]
    sz = round(sz, rounding)

    market_result = exchange.market_open(coin, is_buy, sz, px, reduce_only=reduce_only)

    if is_buy == True:
        print(f"You bought {sz} USD worth of {coin} at {px}")
    else:
        print(f"You sold {sz} USD worth of {coin} at {px}")

    return market_result

def market_close(coin, sz, leverage, px, account):

    exchange = Exchange(account, constants.MAINNET_API_URL)
    exchange.update_leverage(leverage, coin)

    rounding = get_sz_px_decimals(coin)[0]
    sz = round(sz, rounding)

    market_result = exchange.market_close(coin, sz, px)

    print(f"You close a {sz} USD position on {coin} at {px}")

    return market_result


def cancel_all_orders(account):

    exchange = Exchange(account, constants.MAINNET_API_URL)
    info = Info(constants.MAINNET_API_URL, skip_ws=True)

    open_orders = info.open_orders(account.address)

    for open_order in open_orders:
        exchange.cancel(open_order['coin'], open_order['oid'])

def kill_switch(symbol, account):
    
    positions, pos_sym, pos_size, leverage, value, pos_type, entry_px, pnl_perc, account_val = positionsHL.get_all_positions(account)

    while positions != []:
        for i in range(len(positions)):
            ask = ask_bid(symbol)[0]
            bid = ask_bid(symbol)[1]
            pos_size[i] = abs(pos_size[i])

            if pos_type[i] == 'LONG':
                limit_order(pos_sym[i], False, pos_size[i], leverage[i], ask, True, account)
                time.sleep(5)
            elif pos_type[i] == 'SHORT':
                limit_order(pos_sym[i], True, pos_size[i], leverage[i], bid, True, account)
                time.sleep(5)
        
        positions, pos_sym, pos_size, leverage, value, pos_type, entry_px, pnl_perc, account_val = positionsHL.get_all_positions(account)


def close_all_positions(account):
    info = Info(constants.MAINNET_API_URL, skip_ws=True)
    user_state = info.user_state(account.address)
    positions = []

    cancel_all_orders(account)

    for position in user_state["assetPositions"]:
        if float(position["position"]["szi"]) != 0:
            positions.append(position["position"]["coin"])
    
    for position in positions:
        kill_switch(position, account)

def is_order_filled(user_adress, order_id):

    url = "https://api.hyperliquid.xyz/info"
    headers = {"Content-Type": "application/json"}

    data = {
        "type": "frontendOpenOrders",
        "user": user_adress
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        data = response.json()
        orders = data

        order_found = None
        for order in orders:
            if int(order["oid"]) == int(order_id): 
                order_found = order
                break

        if order_found:
            is_trigger = False
            try:
                while order_found["isTrigger"] == False:
                    time.sleep(0.5)

                    url = "https://api.hyperliquid.xyz/info"
                    headers = {"Content-Type": "application/json"}

                    data = {
                        "type": "frontendOpenOrders",
                        "user": user_adress
                    }

                    response = requests.post(url, headers=headers, data=json.dumps(data))

                    if response.status_code == 200:
                        data = response.json()
                        orders = data

                        order_found = None
                        for order in orders:
                            if float(order["oid"]) == float(order_id): 
                                order_found = order
                                break
            except:
                is_trigger = True
                print('Order filled')
                return is_trigger
            
        else:
            print(f"Aucun ordre trouvé avec l'ID {order_id}.")
    else:
        print(f"Erreur API : {response.status_code}, {response.text}")


def show_open_orders(account):
    info = Info(constants.MAINNET_API_URL, skip_ws=True)
    open_orders = info.open_orders(account.address)

    order = []
    pos_sym = []
    pos_size = []
    value = []
    pos_type = []
    price = []
    oid = []

    for open_order in open_orders:
        order.append(open_order)
        pos_sym.append(str(open_order['coin']))
        pos_size.append(float(open_order['sz']))
        #leverage = open_order['']
        value.append(float(open_order['sz']) * float(open_order['limitPx']))
        pos_type.append('Long' if open_order['side'] == 'B' else 'Short')
        price.append(open_order['limitPx'])
        oid.append(int(open_order['oid']))
    
    return order, pos_sym, pos_size, value, pos_type, price, oid

def cancel_orders(account, coin, oid):

    exchange = Exchange(account, constants.MAINNET_API_URL)
    info = Info(constants.MAINNET_API_URL, skip_ws=True)

    open_orders = info.open_orders(account.address)
    for open_order in open_orders:
        if open_order['oid'] == oid:
            exchange.cancel(coin, oid)

