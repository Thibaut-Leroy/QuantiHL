from hyperliquid.info import Info
from hyperliquid.utils import constants
from key_file import address

def acct_bal(account):
    info = Info(constants.TESTNET_API_URL, skip_ws=True)
    user_state = info.user_state(address)

    value = user_state['marginSummary']['accountValue']
    value = round(float(value), 2)

    return value