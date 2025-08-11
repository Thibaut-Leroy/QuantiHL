from hyperliquid.info import Info
from hyperliquid.utils import constants

def get_all_positions(account):

    info = Info(constants.MAINNET_API_URL, skip_ws=True)
    user_state = info.user_state(account.address)
    account_val = user_state['marginSummary']['accountValue']
    account_val = round(float(account_val), 2)

    positions = []
    symbol = []
    size = []
    leverage = []
    value = []
    entry_px = []
    pnl_perc = []
    pos_type = []

    for position in user_state["assetPositions"]:
        if float(position["position"]["szi"]) != 0:
            positions.append(position["position"])
            symbol.append(position["position"]["coin"])
            size.append(float(position["position"]["szi"]))
            leverage.append(int(position["position"]["leverage"]['value']))
            value.append(float(position["position"]["positionValue"]))
            entry_px.append(float(position["position"]["entryPx"]))
            pnl_perc.append(float(position["position"]["returnOnEquity"]))
    
            if float(position["position"]["szi"]) > 0:
                pos_type.append('LONG')
            elif float(position["position"]["szi"]) < 0:
                pos_type.append('SHORT')
            else:
                pos_type.append('None')

    return positions, symbol, size, leverage, value, pos_type, entry_px, pnl_perc, account_val

def get_specific_position(coin, account):
    info = Info(constants.MAINNET_API_URL, skip_ws=True)
    user_state = info.user_state(account.address)
    account_val = user_state['marginSummary']['accountValue']
    account_val = round(float(account_val), 2)

    positions = []
    symbol = []
    size = []
    leverage = []
    value = []
    entry_px = []
    pnl_perc = []
    pos_type = []

    for position in user_state["assetPositions"]:
        if position['position']['coin'].upper() == coin.upper() and float(position["position"]["szi"]) != 0:
            positions.append(position["position"])
            symbol.append(position["position"]["coin"])
            size.append(float(position["position"]["szi"]))
            leverage.append(int(position["position"]["leverage"]['value']))
            value.append(float(position["position"]["positionValue"]))
            entry_px.append(float(position["position"]["entryPx"]))
            pnl_perc.append(float(position["position"]["returnOnEquity"]))
    
            if float(position["position"]["szi"]) > 0:
                pos_type.append('LONG')
            elif float(position["position"]["szi"]) < 0:
                pos_type.append('SHORT')
            else:
                pos_type.append('None')

    return symbol, size, leverage, value, pos_type, entry_px, pnl_perc
