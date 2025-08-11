import order_QuantiHL as orderHL
import time
import get_data_QuantiHL as get_data_HL
from key_file import address
from key_file import BotFather_QantiHL_key as BF_QauntiHL_key
import telebot

bot = telebot.TeleBot(token=BF_QauntiHL_key)

def adjust_leverage_size_signal(symbol, leverage, usd_commit, account):
    'this calculates size based on what we want'

    usd = usd_commit * 0.99

    price = orderHL.ask_bid(symbol)[0]

    size = (usd / price) * leverage
    size = float(size)
    rounding = orderHL.get_sz_px_decimals(symbol)[0]
    size = round(size, rounding)

    return leverage, size

############ BID ASK STRAT ############

def bid_ask_strat_function(chat_id, coin, usd_commit, leverage, account):
    
    ask, bid, l2 = orderHL.ask_bid(coin)
    lev, size = adjust_leverage_size_signal(coin, leverage, usd_commit, account)

    buy_order = orderHL.limit_order(coin, True, size, lev, bid, False, account)
    buy_order_id = buy_order[1]
    orderHL.is_order_filled(address, buy_order_id)
    send_message_when_order_filled(chat_id, True, usd_commit, coin, bid, leverage)

    sell_order = orderHL.limit_order(coin, False, size, lev, ask, True, account)
    sell_order_id = sell_order[1]
    orderHL.is_order_filled(address, sell_order_id)
    send_message_when_order_filled(chat_id, False, usd_commit, coin, ask, leverage)

    # Add something to track PNL and number of winning position

def bid_ask_bot(nb_loop, chat_id, coin, usd_commit, leverage, account):
    for i in range(nb_loop):
        bid_ask_strat_function(chat_id, coin, usd_commit, leverage, account)


def send_message_when_order_filled(chat_id, is_buy, usd, coin, price, leverage):
    if is_buy == True:
        buy_message = f"✅ You bought {usd:.4f} USD of {coin} at {price}, leverage x{leverage}"
        bot.send_message(chat_id, buy_message)
    elif is_buy == False:
        sell_message = f"❌ You sold {usd:.4f} USD of {coin} at {price}, leverage x{leverage}"
        bot.send_message(chat_id, sell_message)



############ SMA STRAT ############

def get_sma(coin, coin_timeframe, sma_period):
    data = get_data_HL.get_ohlcv(coin, coin_timeframe, sma_period)
    data_df = get_data_HL.process_data_to_df(data)
    sma_value = data_df['close'][-sma_period:].astype(float).mean()
    return sma_value

def sma_strat_function(coin, usd_commit, leverage, take_profit, stop_loss, coin_timeframe, sma_period, account, check_bot_stop):
    # Initilialisation
    ask, bid, l2 = orderHL.ask_bid(coin)
    mid = (ask + bid)/2
    lev, size = adjust_leverage_size_signal(coin, leverage, usd_commit, account)
    sma = get_sma(coin, coin_timeframe, sma_period)
    bot_started = False
    init_pos = 1 if sma > mid else 0
    pos_size = 0
    in_pos = False

    while bot_started == False:
        ask, bid, l2 = orderHL.ask_bid(coin)
        mid = (ask + bid)/2
        sma = get_sma(coin, coin_timeframe, sma_period)
        
        if init_pos == 1:
            if sma < mid:
                bot_started = True
            else:
                time.sleep(5) # Add a function to use coin_timeframe as second to wait indicator
        
        elif init_pos == 0:
            if sma > mid:
                bot_started = True
            else:
                time.sleep(5) # Add a function to use coin_timeframe as second to wait indicator


    while bot_started:  # Check if working
        stop_bot = break_bot_check(check_bot_stop)
        if stop_bot == True:
            bot_started = False
            break
        
        ask, bid, l2 = orderHL.ask_bid(coin)
        sma = get_sma(coin, coin_timeframe, sma_period)

        if in_pos == False:

            buy_signal = ask > sma
            sell_signal = bid < sma

            if buy_signal:
                buy_order = orderHL.limit_order(coin, True, size, lev, ask, False, account)
                buy_order_id = buy_order[1]
                orderHL.is_order_filled(address, buy_order_id)
                in_pos = True
                pos_size = 1
                tp = bid * (1 + take_profit)
                sl = ask * (1 - stop_loss)
            
            elif sell_signal:
                sell_order = orderHL.limit_order(coin, False, size, lev, bid, False, account)
                sell_order_id = sell_order[1]
                orderHL.is_order_filled(address, sell_order_id)
                in_pos = True
                pos_size = -1
                tp = ask * (1 - take_profit)
                sl = bid * (1 + stop_loss)
        
        elif in_pos == True:
            ask, bid, l2 = orderHL.ask_bid(coin)
            if pos_size > 0:
                if ask >= tp or bid <= sl:
                    close_buy_position = orderHL.limit_order(coin, False, size, lev, ask if ask>=tp else bid, True, account)
                    sell_order_id = close_buy_position[1]
                    orderHL.is_order_filled(address, sell_order_id)
                    # Add something to track PNL and number of winning position
                else:
                    print(f'Neither Take Profit nor Stop Loss have been reached, current price: {bid:2f}/{ask:2f}, SL: {sl:2f}, TP: {tp:2f}')
            
            elif pos_size < 0:
                if bid >= tp or ask <= sl:
                    close_sell_position = orderHL.limit_order(coin, True, size, lev, bid if bid>=tp else ask, True, account)
                    buy_order_id = close_sell_position[1]
                    orderHL.is_order_filled(address, buy_order_id)
                    # Add something to track PNL and number of winning position
                else:
                    print(f'Neither Take Profit nor Stop Loss have been reached, current price: {bid:2f}/{ask:2f}, SL: {sl:2f}, TP: {tp:2f}')
                
def break_bot_check(check_bot_stop):
    if input == False:
        return False
    else:
        return True
