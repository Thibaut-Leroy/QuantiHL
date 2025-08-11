from hyperliquid.info import Info
from hyperliquid.utils import constants

def acct_bal(account):
    info = Info(constants.MAINNET_API_URL, skip_ws=True)
    user_state = info.user_state(account.address)

    value = user_state['marginSummary']['accountValue']
    value = round(float(value), 2)

    return value
