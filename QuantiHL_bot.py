from key_file import BotFather_QantiHL_key as BF_QauntiHL_key
from key_file import private_key, pk_testnet, address
from eth_account.signers.local import LocalAccount
import eth_account
import telebot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
import get_data_QuantiHL as dataHL
import positions_QuantiHL as positionsHL
import balance_QuantiHL as balanceHL
import io
import order_QuantiHL as orderHL
import algo_strat_QuantiHL as algo_HL
import json
import ConfigurableStrategy as CS
import os
import tempfile
from datetime import datetime
import time
import threading

user_token = []
user_timeframe = []
secret_key = private_key
account = LocalAccount = eth_account.Account.from_key(private_key)

coin_chosen = []
order_choice = []
usd_amount = []
leverage = []

bot = telebot.TeleBot(token=BF_QauntiHL_key)

def run_in_thread(func):
    def wrapper(*args, **kwargs):
        threading.Thread(target=func, args=args, kwargs=kwargs).start()
    return wrapper


@bot.message_handler(commands=['start'])
def start_command(message):
    start_text = f'👋 Hello {message.from_user.first_name} and welcome on QuantiHL \n\n'
    start_text += f"💼 QuantiHL is your pocket compagnion to manage your Hyperliquid portfolio from anywhere \n\n"
    start_text += f"📁 /data - Get a CSV file with a coin historical price\n"
    start_text += f"🏦 /balance - Get your portfolio balance \n"
    start_text += f"📊 /positions - Manage all your positions \n"
    start_text += f"📝 /order - Open an order at a specifc price \n"
    start_text += f"👁️ /open_order - View your open orders \n"
    start_text += f"❌ /close_all - Close all your positions and open orders \n"
    start_text += f"🤖 /open_strategy - Run an algo strategy based on a tailored algorithm \n"
    start_text += f"🧪 /backtest - Backtest any algo strategy before running it live"
    
    #logo = "/Users/thibautleroy/PythonCode/0-Hyperliquid/QuantiHL/logo_QuantiHL.png"
    #with open(logo,'rb') as photo:
    #    bot.send_photo(chat_id=message.chat.id, photo=photo, caption=start_text)
    bot.send_message(message.chat.id, start_text)



#############################################################
################# GET HISTORICAL DATA PART ##################
#############################################################

@bot.message_handler(commands=['data'])
def data_command(message):
    bot.send_message(message.chat.id, "Please enter the token you want to get data on")
    bot.register_next_step_handler(message, process_token)

def process_token(message):
    token = message.text
    user_token.append(token)
    bot.send_message(message.chat.id, "Enter the desired timeframe")
    bot.register_next_step_handler(message, process_timeframe)

@run_in_thread
def process_timeframe(message):
    timeframe = message.text
    user_timeframe.append(timeframe)

    token = user_token[-1]
    timeframe = user_timeframe[-1]
    bot.send_message(message.chat.id, f'Here is a csv file with last available data on {token} using a {timeframe} timeframe')

    ohlcv = dataHL.get_ohlcv(token, timeframe, lookback_days=100)
    ohlcv_df = dataHL.process_data_to_df(ohlcv)
    csv_buffer = io.BytesIO()
    ohlcv_df.to_csv(csv_buffer, index=False, encoding='utf-8')
    csv_buffer.seek(0)
    bot.send_document(message.chat.id, document=csv_buffer)




#############################################################
#################### GET POSITIONS PART #####################
#############################################################

user_position = {
    "coin": None,
    "size": None,
    "leverage": None,
    "value": None,
    "pos_type": None,
    "entry_px": None,
    "pnl_perc": None,
    "pos_number": 0
}

@bot.message_handler(commands=['positions'])
@run_in_thread
def positions_command(message):
    positions, symbol, size, leverage, value, pos_type, entry_px, pnl_perc, account_val = positionsHL.get_all_positions(account)
    if positions == []:
        bot.send_message(message.chat.id, f'🏦 You currently have no position, and your wallet balance is {account_val} USD')
    else:
        positions_text = f"📊 You currently have {len(positions)} position(s) : \n"
        for i in range(len(positions)):
            positions_text += f"\n#{i+1} {pos_type[i]} x{leverage[i]} {float(size[i])} {symbol[i]} \n Value: {round(float(value[i]), 2)} USD (PNL: {round(float(pnl_perc[i]), 3)}%), entry price: {float(entry_px[i])} \n"

        positions_text += f'\n🏦 Your total wallet value is {account_val} USD'

        buttons = [
            InlineKeyboardButton(text="📊 Show Position", callback_data="show_specific_position"),
            InlineKeyboardButton(text="❌ Close All Position", callback_data="close_all_position")
        ]
        inline_keybord = InlineKeyboardMarkup(row_width=2)
        inline_keybord.add(*buttons)
        bot.send_message(message.chat.id, positions_text, reply_markup=inline_keybord)

@bot.callback_query_handler(func=lambda call: call.data == "show_specific_position")
def get_all_symbol(call):
    user_position["pos_number"] = 0
    specific_positions(call, user_position["pos_number"])

def specific_positions(call, i):
    positions, symbol, size, leverage, value, pos_type, entry_px, pnl_perc, account_val = positionsHL.get_all_positions(account)
    user_position['coin'] = symbol
    user_position['size'] = size
    user_position['leverage'] = leverage
    user_position['value'] = value
    user_position['pos_type'] = pos_type
    user_position['entry_px'] = entry_px
    user_position['pnl_perc'] = pnl_perc

    ask,bid,l2_data = orderHL.ask_bid(user_position["coin"][i])
    position_text = f"{user_position['pos_type'][i]} x{user_position['leverage'][i]} {user_position['coin'][i]}\n\n Size:{float(user_position['size'][i])} {user_position['coin'][i]}\n Value: {round(float(user_position['value'][i]), 2)} USD ({round(float(user_position['pnl_perc'][i]), 3)}%) \n Entry price: {float(user_position['entry_px'][i])} \n Current Price: {(ask+bid)/2} \n"
    
    buttons = [
        InlineKeyboardButton(text="⬅️", callback_data="previous_position"),
        InlineKeyboardButton(text=f"#{user_position['pos_number']+1}", callback_data='nothing'),
        InlineKeyboardButton(text="➡️", callback_data="next_position"),
        InlineKeyboardButton(text="❌ 50%", callback_data="close_position_50"),
        InlineKeyboardButton(text="❌ 100%", callback_data="close_position_100")
    ]
    inline_keybord = InlineKeyboardMarkup(row_width=3)
    inline_keybord.add(*buttons)
    inline_keybord.add(InlineKeyboardButton(text="Back to All Positions", callback_data="show_all_positions"))

    bot.edit_message_text(
        chat_id=call.message.chat.id, 
        message_id=call.message.message_id, 
        text=position_text, 
        reply_markup=inline_keybord
    )

@bot.callback_query_handler(func=lambda call: call.data == "show_all_positions")
@run_in_thread
def show_all_positions(call):
    positions, symbol, size, leverage, value, pos_type, entry_px, pnl_perc, account_val = positionsHL.get_all_positions(account)
    if positions == []:
        bot.send_message(call.message.chat.id, f'🏦 You currently have no position, and your wallet balance is {account_val} USD')
    else:
        positions_text = f"📊 You currently have {len(positions)} position(s) : \n"
        for i in range(len(positions)):
            positions_text += f"\n#{i+1} {pos_type[i]} x{leverage[i]} {float(size[i])} {symbol[i]} \n Value: {round(float(value[i]), 2)} USD (PNL: {round(float(pnl_perc[i]), 3)}%), entry price: {float(entry_px[i])} \n"

        positions_text += f'\n🏦 Your total wallet value is {account_val} USD'

        buttons = [
            InlineKeyboardButton(text="📊 Show Position", callback_data="show_specific_position"),
            InlineKeyboardButton(text="❌ Close All Position", callback_data="close_all_position")
        ]
        inline_keybord = InlineKeyboardMarkup(row_width=2)
        inline_keybord.add(*buttons)
        bot.edit_message_text(
            chat_id=call.message.chat.id, 
            message_id=call.message.message_id, 
            text=positions_text, 
            reply_markup=inline_keybord
        )

@bot.callback_query_handler(func=lambda call: call.data == "previous_position")
def get_previous_position(call):
    user_position["pos_number"] = user_position["pos_number"] - 1
    user_position["pos_number"] = user_position["pos_number"] % (len(user_position["coin"]))
    specific_positions(call, user_position["pos_number"])

@bot.callback_query_handler(func=lambda call: call.data == "next_position")
def get_next_position(call):
    user_position["pos_number"] = user_position["pos_number"] + 1
    user_position["pos_number"] = user_position["pos_number"] % (len(user_position["coin"]))
    specific_positions(call, user_position["pos_number"])

@bot.callback_query_handler(func=lambda call: call.data == "close_all_position")
def close_all_positions(call):
    buttons = [
        InlineKeyboardButton(text="✅ Confirm", callback_data="close_all_positions_confirm"),
        InlineKeyboardButton(text="❌ Cancel", callback_data="close_all_positions_cancel")
    ]
    inline_keybord = InlineKeyboardMarkup(row_width=1)
    inline_keybord.add(*buttons)
    bot.send_message(chat_id=call.message.chat.id, text="You are going to close all your open positions and cancel all your orders", reply_markup=inline_keybord)


@bot.callback_query_handler(func=lambda call: call.data in ["close_all_positions_confirm","close_all_positions_cancel"])
@run_in_thread
def close_all_positions_confirmed(call):
    if call.data == 'close_all_positions_confirm':
        bot.send_message(call.message.chat.id, '⏳ All your orders are being canceled and all your positions are being closed')
        orderHL.close_all_positions(account)
        bot.send_message(call.message.chat.id, '✅ All your orders have been canceled and all your positions have been closed')
    elif call.data == 'close_all_positions_cancel':
        bot.send_message(call.message.chat.id, '❌ Closing all your positions has been canceled')

@bot.message_handler(commands=['close_all'])
def close_all(message):
    buttons = [
        InlineKeyboardButton(text="✅ Confirm", callback_data="close_all_positions_confirm"),
        InlineKeyboardButton(text="❌ Cancel", callback_data="close_all_positions_cancel")
    ]
    inline_keybord = InlineKeyboardMarkup(row_width=1)
    inline_keybord.add(*buttons)
    bot.send_message(chat_id=message.chat.id, text="You are going to close all your open positions and cancel all your orders", reply_markup=inline_keybord)
    bot.register_next_step_handler(message, close_all_positions_confirmed)

@bot.callback_query_handler(func=lambda call: call.data.startswith("close_position_"))
@run_in_thread
def close_position(call):
    try:
        size_perc = call.data.replace("close_position_", "")
        size = float(abs(float(size_perc)/100 * user_position["size"][user_position["pos_number"]]))
        coin = user_position["coin"][user_position["pos_number"]]
        leverage = user_position["leverage"][user_position["pos_number"]]
        is_buy = False if user_position["pos_type"][user_position["pos_number"]].lower() == "long" else True
        ask,bid,l2data = orderHL.ask_bid(coin)

        order = orderHL.limit_order(coin, is_buy, size, leverage, ask if is_buy else bid, True, account)
        if order[2] == "":    
            bot.send_message(call.message.chat.id, f"⏳ Your order has been placed at {ask if is_buy else bid}")
            order_id = order[1]
            orderHL.is_order_filled(account.address, order_id)
            bot.send_message(call.message.chat.id, "✅ Your order has been filled")
            user_position["pos_number"] = 0
        else:
            bot.send_message(call.message.chat.id, f"Error: {order[2]}")
    except Exception as e:
        bot.send_message(call.message.chat.id, f"Error : {e}")


#############################################################
####################### BALANCE PART ########################
#############################################################

@bot.message_handler(commands=['balance'])
def balance_command(message):
    acct_balance = balanceHL.acct_bal(account)
    bot.send_message(message.chat.id, f'🏦 Your wallet balance is {acct_balance} USD')


#############################################################
######################## ORDER PART #########################
#############################################################

order_config = {
    "pos_type": None,
    "coin": None,
    "cash": None,
    "leverage": None
}

@bot.message_handler(commands=['order'])
def type_choice(message):
    bot.send_message(message.chat.id, "Do you want to go Long or Short ?")
    bot.register_next_step_handler(message, coin_choice)

def coin_choice(message):
    order_config["pos_type"] = str(message.text)
    if order_config["pos_type"].lower() in ["long","short"]:
        bot.send_message(message.chat.id, "Please enter the token you want")
        bot.register_next_step_handler(message, amount_choice)
    else:
        bot.send_message(message.chat.id, "Please enter a valid input")
        type_choice(message)

def amount_choice(message):
    order_config["coin"] = str(message.text)
    bot.send_message(message.chat.id, "Please enter the amount you want")
    bot.register_next_step_handler(message, process_leverage)

def process_leverage(message):
    try:
        order_config["cash"] = float(message.text)
        bot.send_message(message.chat.id, "Please enter the leverage you want")
        bot.register_next_step_handler(message, choose_price)
    except:
        bot.send_message(message.chat.id, "Invalid input. Please enter a valid number")
        amount_choice(message)

def choose_price(message):
    order_config["leverage"] = int(message.text)
    buttons = [
            InlineKeyboardButton(text="📈 Current Bid/Ask", callback_data="order_bid_ask_price"),
            InlineKeyboardButton(text="✏️ Custom Price", callback_data="order_custom_price")
    ]
    inline_keybord = InlineKeyboardMarkup(row_width=1)
    inline_keybord.add(*buttons)
    choose_price_message = "You are going to place an order \n\n Choose the price :"
    bot.send_message(message.chat.id, choose_price_message, reply_markup=inline_keybord)

@bot.callback_query_handler(func=lambda call: call.data == "order_bid_ask_price")
@run_in_thread
def place_order_bid_ask_price(call):
    ask, bid, l2_data = orderHL.ask_bid(order_config["coin"])

    if order_config["pos_type"].lower() == 'long':
        px = ask
        is_buy = True
    else:
        px = bid
        is_buy = False
    
    try:
        size = orderHL.usd_to_size(order_config["coin"], order_config["leverage"], order_config["cash"], is_buy)
        order = orderHL.limit_order(order_config["coin"], is_buy, size, order_config["leverage"], px, False, account)
        if order[2] == "":
            bot.send_message(call.message.chat.id, f"⏳ Your order has been placed at {px}")
            order_id = order[1]
            orderHL.is_order_filled(account.address, order_id)
            bot.send_message(call.message.chat.id, "✅ Your order has been filled")
        else:
            bot.send_message(call.message.chat.id, f"Error: {order[2]}")
    except Exception as e:
        bot.send_message(call.message.chat.id, f"Error : {e}")

@bot.callback_query_handler(func=lambda call: call.data == "order_custom_price")
def custom_price(call):
    ask, bid, l2_data = orderHL.ask_bid(order_config["coin"])

    msg = bot.send_message(call.message.chat.id, f"✏️ Enter the desired price : \n\n 💵 Current price : {(ask+bid)/2}")
    bot.register_next_step_handler(msg, place_order_custom_price)

@run_in_thread
def place_order_custom_price(message):
    px = float(message.text)
    is_buy = True if order_config["pos_type"].lower() == 'long' else False

    try:
        size = orderHL.usd_to_size(order_config["coin"], order_config["leverage"],order_config["cash"], is_buy)
        order = orderHL.limit_order(order_config["coin"], is_buy, size, order_config["leverage"], px, False, account)
        if order[2] == "":
            bot.send_message(message.chat.id, f"⏳ Your order has been placed at {px}")
            order_id = order[1]
            orderHL.is_order_filled(account.address, order_id)
            bot.send_message(message.chat.id, "✅ Your order has been filled")
        else:
            bot.send_message(message.chat.id, f"Error : {order[2]}")
    except Exception as e:
        bot.send_message(message.chat.id, f"Error : {e}")

@bot.message_handler(commands=['open_order'])
def show_all_open_orders(message):
    order, pos_sym, pos_size, value, pos_type, price, oid = orderHL.show_open_orders(account)
    if order == []:
        orders_text = f"You curently have no open order"
        bot.send_message(chat_id=message.chat.id, text=orders_text)

    else:
        orders_text = f"You have {len(order)} open order{'s' if len(order)>1 else ''} :"
        for i in range(len(order)):
            orders_text += f"\n\n #{i+1} {pos_type[i]} {pos_sym[i]} for {round(value[i],2)} USD at {price[i]}"

        buttons = [InlineKeyboardButton(text=f"Cancel #{i+1}", callback_data=f"cancel_order_{i+1}") for i in range(len(order))]
        inline_keybord = InlineKeyboardMarkup(row_width=2)
        inline_keybord.add(*buttons)
        inline_keybord.add(InlineKeyboardButton(text="❌ Cancel all orders", callback_data="cancel_all_orders"))

        bot.send_message(chat_id=message.chat.id, text=orders_text,reply_markup=inline_keybord)

@bot.callback_query_handler(func=lambda call: call.data == "cancel_all_orders")
@run_in_thread
def cancel_all_orders(call):
    bot.send_message(call.message.chat.id, f"⏳ All orders are being cancelled")
    orderHL.cancel_all_orders(account)
    bot.send_message(call.message.chat.id, f"✅ All orders have been cancelled")

@bot.callback_query_handler(func=lambda call: call.data.startswith("cancel_order_"))
@run_in_thread
def cancel_order(call):
    order, pos_sym, pos_size, value, pos_type, price, oid = orderHL.show_open_orders(account)
    order_id = int(call.data.replace("cancel_order_", ""))
    oid = oid[order_id-1]
    coin = pos_sym[order_id-1]
    bot.send_message(call.message.chat.id, f"⏳ Order is being cancelled")
    orderHL.cancel_orders(account, coin, oid)
    bot.send_message(call.message.chat.id, f"✅ Order has been cancelled")

    show_all_open_orders(call.message)



#############################################################
###################### ALGO STRAT PART ######################
#############################################################

# Dictionary to store user algo configurations
algo_configs = {
            "coin": "HYPE",
            "timeframe": "5m",
            "initial_cash": 15,
            "leverage": 1,
            "tp": 0.08,
            "sl": 0.05,
            "sma_period": 20,
            "sma_strat": False
        }

# Show Main Menu with all strategies
@bot.message_handler(commands=['open_strategy'])
def open_strategy(message):
    buttons = [
        InlineKeyboardButton(text="Bid Ask Strategy", callback_data="bid_ask_strat_button"),
        InlineKeyboardButton(text="SMA Strategy", callback_data="sma_strat_button")
    ]
    inline_keybord = InlineKeyboardMarkup(row_width=1)
    inline_keybord.add(*buttons)

    open_strat_message = "You are going to open an algo strategy. \n\n Choose the desired strategy :"
    bot.send_message(message.chat.id, open_strat_message, reply_markup=inline_keybord)

@bot.callback_query_handler(func= lambda call: call.data in ["bid_ask_strat_button", "sma_strat_button"])
def launching_message(call):
    strategies = {
        "bid_ask_strat_button": ("Launching Bid Ask Strategy",set_bid_ask_strategy),
        "sma_strat_button": ("Launching SMA Strategy", set_sma_strategy)
    }

    launch_message, launch_function = strategies[call.data]

    edited_keybord = InlineKeyboardMarkup()
    selected_button = InlineKeyboardButton(text="✅ " + launch_message[10:], callback_data="selected")
    edited_keybord.add(selected_button)
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=edited_keybord)
    
    if call.data == "bid_ask_strat_button":
        buttons = [
        InlineKeyboardButton(text=f"Coin: {algo_configs['coin']}", callback_data="algo_strat_bid_ask_coin"),
        InlineKeyboardButton(text=f"{algo_configs['initial_cash']} USD", callback_data="algo_strat_bid_ask_usd_commit"),
        InlineKeyboardButton(text=f"Leverage: x{algo_configs['leverage']}", callback_data="algo_strat_bid_ask_leverage")
        ]
        inline_keybord = InlineKeyboardMarkup(row_width=1)
        inline_keybord.add(*buttons)

    elif call.data == "sma_strat_button":
        buttons = [
            InlineKeyboardButton(text=f"Coin: {algo_configs['coin']}", callback_data="algo_strat_sma_coin"),
            InlineKeyboardButton(text=f"{algo_configs['initial_cash']} USD", callback_data="algo_strat_sma_usd_commit"),
            InlineKeyboardButton(text=f"Leverage: x{algo_configs['leverage']}", callback_data="algo_strat_sma_leverage"),
            InlineKeyboardButton(text=f"Timeframe: {algo_configs['timeframe']}", callback_data="algo_strat_sma_timeframe"),
            InlineKeyboardButton(text=f"Period: {algo_configs['sma_period']}", callback_data="algo_strat_sma_sma_period"),
            InlineKeyboardButton(text=f"TP: {round(algo_configs['tp']*100,2)}%", callback_data="algo_strat_sma_tp_value"),
            InlineKeyboardButton(text=f"SL: {round(algo_configs['sl']*100,2)}%", callback_data="algo_strat_sma_sl_value")
        ]
        inline_keybord = InlineKeyboardMarkup(row_width=2)
        inline_keybord.add(*buttons)

    #bot.send_message(call.message.chat.id, launch_message, reply_markup=inline_keybord)

    launch_function(call.message.chat.id)

###### BID ASK STRATEGY ######
def set_bid_ask_strategy(chat_id):
    buttons = [
            InlineKeyboardButton(text=f"Coin: {algo_configs['coin']}", callback_data="algo_strat_bid_ask_coin"),
            InlineKeyboardButton(text=f"{algo_configs['initial_cash']} USD", callback_data="algo_strat_bid_ask_usd_commit"),
            InlineKeyboardButton(text=f"Leverage: x{algo_configs['leverage']}", callback_data="algo_strat_bid_ask_leverage")
    ]
    inline_keybord = InlineKeyboardMarkup(row_width=3)
    inline_keybord.add(*buttons)
    inline_keybord.add(InlineKeyboardButton(text="Launch Bid Ask Strategy", callback_data="launch_bid_ask_strategy"))

    bot.send_message(
        chat_id=chat_id,
        text="Current coonfig is:",
        reply_markup=inline_keybord
    )

@bot.callback_query_handler(func=lambda call: call.data == "launch_bid_ask_strategy")
@run_in_thread
def launch_bid_ask_strategy(call):
    buttons = [InlineKeyboardButton(text="Stop strategy", callback_data="stop_bid_ask_strat_button")]
    inline_keybord = InlineKeyboardMarkup(row_width=1)
    inline_keybord.add(*buttons)
    bot.send_message(chat_id=call.message.chat.id, text="Bid ask Strategy is now running",reply_markup=inline_keybord)
    algo_HL.bid_ask_bot(10, call.message.chat.id, algo_configs["coin"], algo_configs['initial_cash'], algo_configs["leverage"], account)
    bot.send_message(call.message.chat.id, "Bid ask Strategy is now over")

####### Choose the Coin #######
@bot.callback_query_handler(func=lambda call: call.data == "algo_strat_bid_ask_coin")
def ba_coin(call):
    coins = ["BTC", "ETH", "SOL", "HYPE"]
    buttons = [InlineKeyboardButton(text=coin, callback_data=f"selected_ba_coin_{coin}") for coin in coins]
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(*buttons)
    markup.add(InlineKeyboardButton(text="Back", callback_data="back_to_ba_main"))
    
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="Select a coin:",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("selected_ba_coin_"))
def set_ba_coin(call):
    coin = call.data.replace("selected_ba_coin_", "")
    algo_configs["coin"] = coin
    bot.answer_callback_query(call.id, f"Selected pair: {coin}")
    show_ba_menu(call)

####### Choose the cash #######
@bot.callback_query_handler(func=lambda call: call.data == "algo_strat_bid_ask_usd_commit")
def ask_ba_cash(call):
    msg = bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="Enter your desired initial capital in USDC:"
    )
    bot.register_next_step_handler(msg, process_ba_cash)

def process_ba_cash(message):
    try:
        cash = float(message.text)
        algo_configs["initial_cash"] = cash
        # Recreate the main menu
        set_bid_ask_strategy(message.chat.id)

    except ValueError:
        bot.send_message(
            message.chat.id, 
            "Invalid input. Please enter a valid number."
        )
        # Retry
        msg = bot.send_message(message.chat.id, "Enter your desired initial capital in USD (numbers only):")
        bot.register_next_step_handler(msg, process_ba_cash)


####### Choose the leverage #######
@bot.callback_query_handler(func=lambda call: call.data == "algo_strat_bid_ask_leverage")
def leverage(call):
    leverages = [1, 2, 3, 4, 5, 10, 15, 20]
    markup = InlineKeyboardMarkup(row_width=4)
    buttons = [InlineKeyboardButton(text=leverage, callback_data=f"selected_ba_leverage_{leverage}") for leverage in leverages]
    markup.add(*buttons)
    markup.add(InlineKeyboardButton(text="Back", callback_data="back_to_ba_main"))
    
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="Select your leverage:",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("selected_ba_leverage_"))
def set_leverage(call):
    leverage = call.data.replace("selected_ba_leverage_", "")
    algo_configs["leverage"] = int(leverage)
    bot.answer_callback_query(call.id, f"Selected leverage: {leverage}")
    show_ba_menu(call)

@bot.callback_query_handler(func=lambda call: call.data.startswith("back_to_ba_main"))
def show_ba_menu(call):
    buttons = [
            InlineKeyboardButton(text=f"Coin: {algo_configs['coin']}", callback_data="algo_strat_bid_ask_coin"),
            InlineKeyboardButton(text=f"{algo_configs['initial_cash']} USD", callback_data="algo_strat_bid_ask_usd_commit"),
            InlineKeyboardButton(text=f"Leverage: x{algo_configs['leverage']}", callback_data="algo_strat_bid_ask_leverage")
    ]
    inline_keybord = InlineKeyboardMarkup(row_width=3)
    inline_keybord.add(*buttons)
    inline_keybord.add(InlineKeyboardButton(text="Launch Bid Ask Strategy", callback_data="launch_bid_ask_strategy"))

    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="Current coonfig is:",
        reply_markup=inline_keybord
    )

####### SMA STRATEGY #######
def set_sma_strategy(chat_id):
    inline_keybord = InlineKeyboardMarkup()

    inline_keybord.row(
        InlineKeyboardButton(text=f"Coin: {algo_configs['coin']}", callback_data="algo_strat_sma_coin"),
        InlineKeyboardButton(text=f"{algo_configs['initial_cash']} USD", callback_data="algo_strat_sma_usd_commit"),
        InlineKeyboardButton(text=f"Leverage: x{algo_configs['leverage']}", callback_data="algo_strat_sma_leverage")
    )

    inline_keybord.row(
        InlineKeyboardButton(text=f"Timeframe: {algo_configs['timeframe']}", callback_data="algo_strat_sma_timeframe"),
        InlineKeyboardButton(text=f"Period: {algo_configs['sma_period']}", callback_data="algo_strat_sma_sma_period")
    )

    inline_keybord.row(
        InlineKeyboardButton(text=f"TP: {algo_configs['tp']*100:.2f}%", callback_data="algo_strat_sma_tp_value"),
        InlineKeyboardButton(text=f"SL: {algo_configs['sl']*100:.2f}%", callback_data="algo_strat_sma_sl_value")
    )

    inline_keybord.row(
        InlineKeyboardButton(text="Launch SMA Strategy", callback_data="launch_sma_strategy")
    )

    bot.send_message(
        chat_id=chat_id,
        text="Current coonfig is:",
        reply_markup=inline_keybord
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("launch_sma_strategy"))
@run_in_thread
def launch_sma_strategy(call):
    buttons = [InlineKeyboardButton(text="Stop strategy", callback_data="stop_sma_strat_button")]
    inline_keybord = InlineKeyboardMarkup(row_width=1)
    inline_keybord.add(*buttons)
    bot.send_message(call.message.chat.id,"SMA Strategy is now running",reply_markup=inline_keybord)
    algo_configs["sma_strat"] = True
    algo_HL.sma_strat_function(algo_configs['coin'], algo_configs["initial_cash"], algo_configs["leverage"], algo_configs["tp"], algo_configs["sl"], algo_configs['timeframe'], algo_configs["sma_period"], account, False if algo_configs['sma_strat'] == True else True)
    #time.sleep(60)
    bot.send_message(call.message.chat.id,"SMA Strategy is now over")


####### Choose the Coin #######
@bot.callback_query_handler(func=lambda call: call.data == "algo_strat_sma_coin")
def coin(call):
    coins = ["BTC", "ETH", "SOL", "HYPE"]
    buttons = [InlineKeyboardButton(text=coin, callback_data=f"selected_coin_{coin}") for coin in coins]
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(*buttons)
    markup.add(InlineKeyboardButton(text="Back", callback_data="back_to_sma_main"))
    
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="Select a coin:",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("selected_coin_"))
def set_coin(call):
    coin = call.data.replace("selected_coin_", "")
    algo_configs["coin"] = coin
    bot.answer_callback_query(call.id, f"Selected pair: {coin}")
    show_sma_menu(call)


####### Choose the cash #######
@bot.callback_query_handler(func=lambda call: call.data == "algo_strat_sma_usd_commit")
def ask_cash(call):
    msg = bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="Enter your desired initial capital in USDC:"
    )
    bot.register_next_step_handler(msg, process_cash)

def process_cash(message):
    try:
        cash = float(message.text)
        algo_configs["initial_cash"] = cash
        # Recreate the main menu
        inline_keybord = InlineKeyboardMarkup()
        inline_keybord.row(
            InlineKeyboardButton(text=f"Coin: {algo_configs['coin']}", callback_data="algo_strat_sma_coin"),
            InlineKeyboardButton(text=f"{algo_configs['initial_cash']} USD", callback_data="algo_strat_sma_usd_commit"),
            InlineKeyboardButton(text=f"Leverage: x{algo_configs['leverage']}", callback_data="algo_strat_sma_leverage")
        )
        inline_keybord.row(
            InlineKeyboardButton(text=f"Timeframe: {algo_configs['timeframe']}", callback_data="algo_strat_sma_timeframe"),
            InlineKeyboardButton(text=f"Period: {algo_configs['sma_period']}", callback_data="algo_strat_sma_sma_period")
        )
        inline_keybord.row(
            InlineKeyboardButton(text=f"TP: {algo_configs['tp']*100:.2f}%", callback_data="algo_strat_sma_tp_value"),
            InlineKeyboardButton(text=f"SL: {algo_configs['sl']*100:.2f}%", callback_data="algo_strat_sma_sl_value")
        )
        inline_keybord.row(
            InlineKeyboardButton(text="Launch SMA Strategy", callback_data="launch_sma_strategy")
        )

        bot.send_message(
            chat_id=message.chat.id,
            text="Current coonfig is:",
            reply_markup=inline_keybord
        )

    except ValueError:
        bot.send_message(
            message.chat.id, 
            "Invalid input. Please enter a valid number."
        )
        # Retry
        msg = bot.send_message(message.chat.id, "Enter your desired initial capital in USD (numbers only):")
        bot.register_next_step_handler(msg, process_cash)


####### Choose the leverage #######
@bot.callback_query_handler(func=lambda call: call.data == "algo_strat_sma_leverage")
def leverage(call):
    leverages = [1, 2, 3, 4, 5, 10, 15, 20]
    markup = InlineKeyboardMarkup(row_width=4)
    buttons = [InlineKeyboardButton(text=leverage, callback_data=f"selected_leverage_{leverage}") for leverage in leverages]
    markup.add(*buttons)
    markup.add(InlineKeyboardButton(text="Back", callback_data="back_to_sma_main"))
    
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="Select your leverage:",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("selected_leverage_"))
def set_leverage(call):
    leverage = call.data.replace("selected_leverage_", "")
    algo_configs["leverage"] = int(leverage)
    bot.answer_callback_query(call.id, f"Selected leverage: {leverage}")
    show_sma_menu(call)


####### Choose the timeframe #######
@bot.callback_query_handler(func=lambda call: call.data == "algo_strat_sma_timeframe")
def timeframe(call):
    timeframes = ["1m", "5m", "15m", "30m", "1h", "4h", "1d"]
    markup = InlineKeyboardMarkup(row_width=3)
    buttons = [InlineKeyboardButton(text=tf, callback_data=f"selected_timeframe_{tf}") for tf in timeframes]
    markup.add(*buttons)
    markup.add(InlineKeyboardButton(text="Back", callback_data="back_to_sma_main"))
    
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="Select a timeframe:",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("selected_timeframe_"))
def set_timeframe(call):
    timeframe = call.data.replace("selected_timeframe_", "")
    algo_configs["timeframe"] = timeframe
    bot.answer_callback_query(call.id, f"Selected timeframe: {timeframe}")
    show_sma_menu(call)


####### Choose the SMA period #######
@bot.callback_query_handler(func=lambda call: call.data == "algo_strat_sma_sma_period")
def sma_period(call):
    sma_periods = [10, 20, 50, 75, 100, 200]
    markup = InlineKeyboardMarkup(row_width=3)
    buttons = [InlineKeyboardButton(text=sma_period, callback_data=f"selected_sma_period_{sma_period}") for sma_period in sma_periods]
    markup.add(*buttons)
    markup.add(InlineKeyboardButton(text="Back", callback_data="back_to_sma_main"))
    
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="Select a period:",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("selected_sma_period_"))
def set_sma_period(call):
    sma_period = call.data.replace("selected_sma_period_", "")
    algo_configs["sma_period"] = int(sma_period)
    bot.answer_callback_query(call.id, f"Selected period: {sma_period}")
    show_sma_menu(call)



####### Choose the TP value #######
@bot.callback_query_handler(func=lambda call: call.data == "algo_strat_sma_tp_value")
def ask_tp(call):
    msg = bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="Enter your Take Profit (in %)"
    )
    bot.register_next_step_handler(msg, process_tp)

def process_tp(message):
    try:
        tp = float(message.text)
        algo_configs["tp"] = tp / 100
        # Recreate the main menu
        inline_keybord = InlineKeyboardMarkup()
        inline_keybord.row(
            InlineKeyboardButton(text=f"Coin: {algo_configs['coin']}", callback_data="algo_strat_sma_coin"),
            InlineKeyboardButton(text=f"{algo_configs['initial_cash']} USD", callback_data="algo_strat_sma_usd_commit"),
            InlineKeyboardButton(text=f"Leverage: x{algo_configs['leverage']}", callback_data="algo_strat_sma_leverage")
        )
        inline_keybord.row(
            InlineKeyboardButton(text=f"Timeframe: {algo_configs['timeframe']}", callback_data="algo_strat_sma_timeframe"),
            InlineKeyboardButton(text=f"Period: {algo_configs['sma_period']}", callback_data="algo_strat_sma_sma_period")
        )
        inline_keybord.row(
            InlineKeyboardButton(text=f"TP: {algo_configs['tp']*100:.2f}%", callback_data="algo_strat_sma_tp_value"),
            InlineKeyboardButton(text=f"SL: {algo_configs['sl']*100:.2f}%", callback_data="algo_strat_sma_sl_value")
        )
        inline_keybord.row(
            InlineKeyboardButton(text="Launch SMA Strategy", callback_data="launch_sma_strategy")
        )

        bot.send_message(
            chat_id=message.chat.id,
            text="Current coonfig is:",
            reply_markup=inline_keybord
        )

    except ValueError:
        bot.send_message(
            message.chat.id, 
            "Invalid input. Please enter a valid number."
        )
        # Retry
        msg = bot.send_message(message.chat.id, "Enter your Take Profit (in %):")
        bot.register_next_step_handler(msg, process_tp)


####### Choose the SL value #######
@bot.callback_query_handler(func=lambda call: call.data == "algo_strat_sma_sl_value")
def ask_sl(call):
    msg = bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="Enter your Stop Loss (in %)"
    )
    bot.register_next_step_handler(msg, process_sl)

def process_sl(message):
    try:
        sl = float(message.text)
        algo_configs["sl"] = sl / 100
        # Recreate the main menu
        inline_keybord = InlineKeyboardMarkup()
        inline_keybord.row(
            InlineKeyboardButton(text=f"Coin: {algo_configs['coin']}", callback_data="algo_strat_sma_coin"),
            InlineKeyboardButton(text=f"{algo_configs['initial_cash']} USD", callback_data="algo_strat_sma_usd_commit"),
            InlineKeyboardButton(text=f"Leverage: x{algo_configs['leverage']}", callback_data="algo_strat_sma_leverage")
        )
        inline_keybord.row(
            InlineKeyboardButton(text=f"Timeframe: {algo_configs['timeframe']}", callback_data="algo_strat_sma_timeframe"),
            InlineKeyboardButton(text=f"Period: {algo_configs['sma_period']}", callback_data="algo_strat_sma_sma_period")
        )
        inline_keybord.row(
            InlineKeyboardButton(text=f"TP: {algo_configs['tp']*100:.2f}%", callback_data="algo_strat_sma_tp_value"),
            InlineKeyboardButton(text=f"SL: {algo_configs['sl']*100:.2f}%", callback_data="algo_strat_sma_sl_value")
        )
        inline_keybord.row(
            InlineKeyboardButton(text="Launch SMA Strategy", callback_data="launch_sma_strategy")
        )

        bot.send_message(
            chat_id=message.chat.id,
            text="Current coonfig is:",
            reply_markup=inline_keybord
        )

    except ValueError:
        bot.send_message(
            message.chat.id, 
            "Invalid input. Please enter a valid number."
        )
        # Retry
        msg = bot.send_message(message.chat.id, "Enter your Stop Loss (in %):")
        bot.register_next_step_handler(msg, process_sl)


####### SHOW THE MAIN WHEN MODIF ARE MADE #######
@bot.callback_query_handler(func=lambda call: call.data == "back_to_sma_main")
def back_to_sma_main(call):
    show_sma_menu(call)

def show_sma_menu(call):    
    inline_keybord = InlineKeyboardMarkup()
    inline_keybord.row(
        InlineKeyboardButton(text=f"Coin: {algo_configs['coin']}", callback_data="algo_strat_sma_coin"),
        InlineKeyboardButton(text=f"{algo_configs['initial_cash']} USD", callback_data="algo_strat_sma_usd_commit"),
        InlineKeyboardButton(text=f"Leverage: x{algo_configs['leverage']}", callback_data="algo_strat_sma_leverage")
    )
    inline_keybord.row(
        InlineKeyboardButton(text=f"Timeframe: {algo_configs['timeframe']}", callback_data="algo_strat_sma_timeframe"),
        InlineKeyboardButton(text=f"Period: {algo_configs['sma_period']}", callback_data="algo_strat_sma_sma_period")
    )
    inline_keybord.row(
        InlineKeyboardButton(text=f"TP: {algo_configs['tp']*100:.2f}%", callback_data="algo_strat_sma_tp_value"),
        InlineKeyboardButton(text=f"SL: {algo_configs['sl']*100:.2f}%", callback_data="algo_strat_sma_sl_value")
    )
    inline_keybord.row(
        InlineKeyboardButton(text="Launch SMA Strategy", callback_data="launch_sma_strategy")
    )

    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="Current coonfig is:",
        reply_markup=inline_keybord
    )


####### STOPPING THE STRATEGY #######
@bot.callback_query_handler(func= lambda call: call.data in ["stop_sma_strat_button"])
def stop_sma_strat(call):
        algo_configs["sma_strat"] = False
        # Add something to stop the strat
        bot.send_message(call.meassage.chat.id, "SMA Strategy is now over")


#############################################################
####################### BACKTEST PART #######################
#############################################################

# Dictionary to store user backtest configurations
user_configs = {}

# Initialize user configuration if not exists
def get_user_config(user_id):
    if user_id not in user_configs:
        user_configs[user_id] = {
            "coin": "HYPE",
            "timeframe": "5m",
            "initial_cash": 100,
            "indicators": []
        }
    return user_configs[user_id]

@bot.message_handler(commands=['backtest'])
def backtesting_launch_message(message):
    user_id = str(message.from_user.id)
    config = get_user_config(user_id)

    inline_keybord = InlineKeyboardMarkup()
    inline_keybord.row(
        InlineKeyboardButton(text=f"{config['coin']}", callback_data="coin_button"),
        InlineKeyboardButton(text=f"{config['timeframe']}", callback_data="timeframe_button"),
        InlineKeyboardButton(text=f"{config['initial_cash']} USD", callback_data="initial_cash_button")
    )
    inline_keybord.row(
        InlineKeyboardButton(text="+ Add an indicator", callback_data="add_indicators_button"),
        InlineKeyboardButton(text="Reset all indicator", callback_data="reset_indicators_button")
    )
    inline_keybord.row(
        InlineKeyboardButton(text="Launch backtest", callback_data="launch_backtest_button")
    )

    open_strat_message = "Welcome to the backtesting mode of QuantiHL!\n\nChoose the parameters of the strategy you want:"
    bot.send_message(message.chat.id, open_strat_message, reply_markup=inline_keybord)

@bot.callback_query_handler(func=lambda call: call.data == "coin_button")
def choose_coin(call):
    coins = ["BTC", "ETH", "SOL", "HYPE", "WIF", "BNB"]
    markup = InlineKeyboardMarkup(row_width=3)
    buttons = [InlineKeyboardButton(text=coin, callback_data=f"select_coin_{coin}") for coin in coins]
    markup.add(*buttons)
    markup.add(InlineKeyboardButton(text="Back", callback_data="back_to_main"))
    
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="Select a coin:",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("select_coin_"))
def set_coin(call):
    coin = call.data.replace("select_coin_", "")
    user_id = str(call.from_user.id)
    config = get_user_config(user_id)
    config["coin"] = coin
    
    bot.answer_callback_query(call.id, f"Selected pair: {coin}")
    show_main_menu(call)

@bot.callback_query_handler(func=lambda call: call.data == "timeframe_button")
def choose_timeframe(call):
    timeframes = ["1m", "5m", "15m", "1h", "4h", "1d"]
    markup = InlineKeyboardMarkup(row_width=3)
    buttons = [InlineKeyboardButton(text=tf, callback_data=f"select_timeframe_{tf}") for tf in timeframes]
    markup.add(*buttons)
    markup.add(InlineKeyboardButton(text="Back", callback_data="back_to_main"))
    
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="Select a timeframe:",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("select_timeframe_"))
def set_timeframe(call):
    timeframe = call.data.replace("select_timeframe_", "")
    user_id = str(call.from_user.id)
    config = get_user_config(user_id)
    config["timeframe"] = timeframe
    
    bot.answer_callback_query(call.id, f"Selected timeframe: {timeframe}")
    show_main_menu(call)

@bot.callback_query_handler(func=lambda call: call.data == "initial_cash_button")
def choose_cash(call):
    cash_options = [50, 100, 500, 1000, 5000, 10000]
    markup = InlineKeyboardMarkup(row_width=3)
    buttons = [InlineKeyboardButton(text=f"{cash} USD", callback_data=f"select_cash_{cash}") for cash in cash_options]
    markup.add(*buttons)
    markup.add(InlineKeyboardButton(text="Custom amount", callback_data="custom_cash"))
    markup.add(InlineKeyboardButton(text="Back", callback_data="back_to_main"))
    
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="Select initial capital:",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("select_cash_"))
def set_cash(call):
    cash = int(call.data.replace("select_cash_", ""))
    user_id = str(call.from_user.id)
    config = get_user_config(user_id)
    config["initial_cash"] = cash
    
    bot.answer_callback_query(call.id, f"Initial capital set to: {cash:.2f} USD")
    show_main_menu(call)

@bot.callback_query_handler(func=lambda call: call.data == "custom_cash")
def ask_custom_cash(call):
    msg = bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="Enter your desired initial capital in USD (numbers only):"
    )
    
    bot.register_next_step_handler(msg, process_custom_cash)

def process_custom_cash(message):
    try:
        cash = float(message.text)
        user_id = str(message.from_user.id)
        config = get_user_config(user_id)
        config["initial_cash"] = cash
        
        # Recreate the main menu
        inline_keybord = InlineKeyboardMarkup()
        inline_keybord.row(
            InlineKeyboardButton(text=f"{config['coin']}", callback_data="coin_button"),
            InlineKeyboardButton(text=f"{config['timeframe']}", callback_data="timeframe_button"),
            InlineKeyboardButton(text=f"{config['initial_cash']} USD", callback_data="initial_cash_button")
        )
        inline_keybord.row(
            InlineKeyboardButton(text="+ Add an indicator", callback_data="add_indicators_button"),
            InlineKeyboardButton(text="Reset all indicator", callback_data="reset_indicators_button")
        )
        inline_keybord.row(
            InlineKeyboardButton(text="Launch backtest", callback_data="launch_backtest_button")
        )

        bot.send_message(
            message.chat.id, 
            f"Initial capital set to: {cash:.2f} USD\n\nCurrent configuration:",
            reply_markup=inline_keybord
        )
    except ValueError:
        bot.send_message(
            message.chat.id, 
            "Invalid input. Please enter a valid number."
        )
        # Retry
        msg = bot.send_message(message.chat.id, "Enter your desired initial capital in USD (numbers only):")
        bot.register_next_step_handler(msg, process_custom_cash)

@bot.callback_query_handler(func=lambda call: call.data == "add_indicators_button")
def add_indicators(call):
    indicators = {
        "SMA": "Simple Moving Average",
        "EMA": "Exponential Moving Average",
        "RSI": "Relative Strength Index",
        "MACD": "Moving Average Convergence Divergence",
        "Bollinger": "Bollinger Bands"
    }
    
    markup = InlineKeyboardMarkup(row_width=1)
    
    # Show current indicators first if they exist
    user_id = str(call.from_user.id)
    config = get_user_config(user_id)
    
    current_indicators_text = ""
    if config["indicators"]:
        current_indicators_text = "Current indicators:\n"
        for idx, indicator in enumerate(config["indicators"]):
            current_indicators_text += f"{idx+1}. {indicator['type']} ({indicator['params']})\n"
        current_indicators_text += "\n"
    
    # Add indicator buttons
    indicator_buttons = [InlineKeyboardButton(text=f"{k} - {v}", callback_data=f"indicator_{k}") for k, v in indicators.items()]
    markup.add(*indicator_buttons)
    
    # Add strategy and back buttons
    markup.row(
        InlineKeyboardButton(text="Back", callback_data="back_to_main")
    )
    
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f"{current_indicators_text}Select an indicator to add:",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("indicator_"))
def configure_indicator(call):
    indicator_type = call.data.replace("indicator_", "")
    
    if indicator_type == "SMA" or indicator_type == "EMA":
        markup = InlineKeyboardMarkup(row_width=3)
        periods = [5, 10, 20, 50, 100, 200]
        period_buttons = [InlineKeyboardButton(text=str(p), callback_data=f"set_period_{indicator_type}_{p}") for p in periods]
        markup.add(*period_buttons)
        markup.add(InlineKeyboardButton(text="Custom Period", callback_data=f"custom_period_{indicator_type}"))
        markup.add(InlineKeyboardButton(text="Back", callback_data="add_indicators_button"))
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"Select period for {indicator_type}:",
            reply_markup=markup
        )
    elif indicator_type == "RSI":
        markup = InlineKeyboardMarkup(row_width=3)
        periods = [7, 14, 21]
        period_buttons = [InlineKeyboardButton(text=str(p), callback_data=f"set_period_{indicator_type}_{p}") for p in periods]
        markup.add(*period_buttons)
        markup.add(InlineKeyboardButton(text="Custom Period", callback_data=f"custom_period_{indicator_type}"))
        markup.add(InlineKeyboardButton(text="Back", callback_data="add_indicators_button"))
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"Select period for {indicator_type}:",
            reply_markup=markup
        )
    elif indicator_type == "MACD":
        markup = InlineKeyboardMarkup(row_width=1)
        preset_configs = [
            "12,26,9 (Standard)",
            "5,35,5 (Fast)",
            "24,52,9 (Slow)"
        ]
        config_buttons = [InlineKeyboardButton(text=c, callback_data=f"set_macd_{c.split(' ')[0]}") for c in preset_configs]
        markup.add(*config_buttons)
        markup.add(InlineKeyboardButton(text="Custom MACD", callback_data="custom_macd"))
        markup.add(InlineKeyboardButton(text="Back", callback_data="add_indicators_button"))
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"Select MACD configuration (fast,slow,signal):",
            reply_markup=markup
        )
    elif indicator_type == "Bollinger":
        markup = InlineKeyboardMarkup(row_width=2)
        configs = [
            "20,2 (Standard)",
            "10,1.5 (Fast)",
            "50,2.5 (Slow)"
        ]
        config_buttons = [InlineKeyboardButton(text=c, callback_data=f"set_bollinger_{c.split(' ')[0]}") for c in configs]
        markup.add(*config_buttons)
        markup.add(InlineKeyboardButton(text="Custom Bollinger", callback_data="custom_bollinger"))
        markup.add(InlineKeyboardButton(text="Back", callback_data="add_indicators_button"))
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"Select Bollinger Bands configuration (period,std):",
            reply_markup=markup
        )

@bot.callback_query_handler(func=lambda call: call.data.startswith("set_period_"))
def set_indicator_period(call):
    a,b, indicator_type, period = call.data.split("_")
    
    user_id = str(call.from_user.id)
    config = get_user_config(user_id)
    
    # Add the indicator with its parameters
    config["indicators"].append({
        "type": indicator_type,
        "params": period
    })
    
    bot.answer_callback_query(call.id, f"Added {indicator_type} with period {period}")
    add_indicators(call)  # Go back to indicators menu

@bot.callback_query_handler(func=lambda call: call.data.startswith("set_macd_"))
def set_macd_params(call):
    params = call.data.replace("set_macd_", "")
    
    user_id = str(call.from_user.id)
    config = get_user_config(user_id)
    
    # Add the MACD indicator with parameters
    config["indicators"].append({
        "type": "MACD",
        "params": params
    })
    
    bot.answer_callback_query(call.id, f"Added MACD with parameters {params}")
    add_indicators(call)  # Go back to indicators menu

@bot.callback_query_handler(func=lambda call: call.data.startswith("set_bollinger_"))
def set_bollinger_params(call):
    params = call.data.replace("set_bollinger_", "")
    
    user_id = str(call.from_user.id)
    config = get_user_config(user_id)
    
    # Add the Bollinger Bands indicator with parameters
    config["indicators"].append({
        "type": "Bollinger",
        "params": params
    })
    
    bot.answer_callback_query(call.id, f"Added Bollinger Bands with parameters {params}")
    add_indicators(call)  # Go back to indicators menu

@bot.callback_query_handler(func=lambda call: call.data.startswith("custom_period_"))
def ask_custom_period(call):
    indicator_type = call.data.replace("custom_period_", "")
    
    msg = bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f"Enter custom period for {indicator_type} (number only):"
    )
    
    bot.register_next_step_handler(msg, lambda m: process_custom_period(m, indicator_type))

def process_custom_period(message, indicator_type):
    try:
        period = int(message.text)
        if period <= 0:
            raise ValueError("Period must be positive")
        
        user_id = str(message.from_user.id)
        config = get_user_config(user_id)
        
        # Add the indicator with custom period
        config["indicators"].append({
            "type": indicator_type,
            "params": str(period)
        })
        
        # Recreate indicators menu
        markup = create_indicators_menu(config)
        
        bot.send_message(
            message.chat.id,
            f"Added {indicator_type} with period {period}\n\nCurrent indicators:",
            reply_markup=markup
        )
    except ValueError:
        bot.send_message(
            message.chat.id,
            "Invalid input. Please enter a positive integer."
        )
        # Retry
        msg = bot.send_message(message.chat.id, f"Enter custom period for {indicator_type} (number only):")
        bot.register_next_step_handler(msg, lambda m: process_custom_period(m, indicator_type))

def create_indicators_menu(config):
    indicators = {
        "SMA": "Simple Moving Average",
        "EMA": "Exponential Moving Average",
        "RSI": "Relative Strength Index",
        "MACD": "Moving Average Convergence Divergence",
        "Bollinger": "Bollinger Bands"
    }
    
    markup = InlineKeyboardMarkup(row_width=1)
    
    # Add indicator buttons # ONlY THE ONES WE ADDED AND PRESENTS IN CONFIG ??
    indicator_buttons = [InlineKeyboardButton(text=f"{k} - {v}", callback_data=f"indicator_{k}") for k, v in indicators.items()]
    markup.add(*indicator_buttons)
    
    # Add strategy and back buttons
    markup.row(
        InlineKeyboardButton(text="Back", callback_data="back_to_main")
    )
    
    return markup

@bot.callback_query_handler(func=lambda call: call.data == "back_to_main")
def show_main_menu(call):
    user_id = str(call.from_user.id)
    config = get_user_config(user_id)
    
    inline_keybord = InlineKeyboardMarkup()
    inline_keybord.row(
        InlineKeyboardButton(text=f"{config['coin']}", callback_data="coin_button"),
        InlineKeyboardButton(text=f"{config['timeframe']}", callback_data="timeframe_button"),
        InlineKeyboardButton(text=f"{config['initial_cash']} USD", callback_data="initial_cash_button")
    )
    inline_keybord.row(
        InlineKeyboardButton(text="+ Add an indicator", callback_data="add_indicators_button"),
        InlineKeyboardButton(text="Reset all indicator", callback_data="reset_indicators_button")
    )
    inline_keybord.row(
        InlineKeyboardButton(text="Launch backtest", callback_data="launch_backtest_button")
    )

    # Prepare message with configuration summary
    indicators_text = ""
    if config["indicators"]:
        indicators_text = "\nIndicators:\n"
        for idx, indicator in enumerate(config["indicators"]):
            indicators_text += f"• {indicator['type']} ({indicator['params']})\n"

    config_text = f"Current configuration:\nCoin: {config['coin']}\nTimeframe: {config['timeframe']}\nCapital: {config['initial_cash']} USD\n{indicators_text}"
    
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=config_text,
        reply_markup=inline_keybord
    )

@bot.callback_query_handler(func=lambda call: call.data == "reset_indicators_button")
def reset_all_indicators(call):
    user_id = str(call.from_user.id)
    config = get_user_config(user_id)
    config["indicators"] = []
    show_main_menu(call)

@bot.callback_query_handler(func=lambda call: call.data == "launch_backtest_button")
def launch_backtest(call):
    user_id = str(call.from_user.id)
    config = get_user_config(user_id)
    
    # Check if we have all necessary configurations
    if not config["indicators"]:
        bot.answer_callback_query(call.id, "Please add at least one indicator before starting backtest")
        add_indicators(call)
        return

    # Show loading message
    msg = bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="🔄 Starting backtest...\n\nRetrieving historical data for " + config["coin"] + " on " + config["timeframe"] + " timeframe..."
    )
    
    bot.register_next_step_handler(msg, run_backtest(call.message.chat.id, call.message.message_id, user_id))

@run_in_thread
def run_backtest(chat_id, message_id, user_id):
    config = get_user_config(user_id)
    try:
        # Get historical data
        config = get_user_config(user_id)
        ohlcv = dataHL.get_ohlcv(config['coin'], config['timeframe'], lookback_days=100)
        ohlcv_df = dataHL.process_data_to_df(ohlcv)

        with tempfile.NamedTemporaryFile(mode='w+', suffix='.csv', delete=True, encoding='utf-8') as tmpfile:
            # Écrire les données dans le fichier temporaire
            ohlcv_df.to_csv(tmpfile.name, index=False, encoding='utf-8')
            tmpfile.flush()

            # Update status message
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text="🔄 Data retrieved...\n\nCalculating indicators and running strategies..."
            )
            indicators_list = config['indicators']
            indicators = [indicator['type'] for indicator in indicators_list]

            # Create a Configuration instance with desired settings
            configu = CS.Configuration(
                initial_cash=config['initial_cash'],
                take_profit=0.05,
                stop_loss=0.03,
                
                # Activation des indicateurs à calculer
                use_sma=True if 'SMA' in indicators else False,
                use_ema=True if 'EMA' in indicators else False,
                use_wma=True if 'WMA' in indicators else False,
                use_rsi=True if 'RSI' in indicators else False,
                use_macd=True if 'MACD' in indicators else False,
                use_mom=True if 'MOM' in indicators else False,
                use_stoch=True if 'STOCH' in indicators else False,
                use_bb=True if 'Bollinger' in indicators else False,
                
                sma_period = next((int(ind["params"]) for ind in config["indicators"] if ind["type"] == "SMA"), None),
                ema_period = next((int(ind["params"]) for ind in config["indicators"] if ind["type"] == "EMA"), None),
                wma_period = next((int(ind["params"]) for ind in config["indicators"] if ind["type"] == "WMA"), None),
                rsi_period = next((int(ind["params"]) for ind in config["indicators"] if ind["type"] == "RSI"), None),
                rsi_overbought = 80,
                rsi_oversold = 20,
                macd_fast = next((int(ind["params"].split(',')[0]) for ind in config["indicators"] if ind["type"] == "MACD"), None),
                macd_slow = next((int(ind["params"].split(',')[1]) for ind in config["indicators"] if ind["type"] == "MACD"), None),
                macd_signal = next((int(ind["params"].split(',')[2]) for ind in config["indicators"] if ind["type"] == "MACD"), None),
                mom_period = None,
                stoch_period = None,
                stoch_period_d = None,
                stoch_period_k = None,
                stoch_upper = None,
                stoch_lower = None,
                bb_period = next((int(ind["params"].split(',')[0]) for ind in config["indicators"] if ind["type"] == "Bollinger"), None),
                bb_devfactor = next((float(ind["params"].split(',')[1]) for ind in config["indicators"] if ind["type"] == "Bollinger"), None),

                # Spécification des indicateurs pour les signaux d'achat
                buy_indicators={
                    'use_sma': True if 'SMA' in indicators else False,   # Prix > SMA pour acheter
                    'use_ema': True if 'EMA' in indicators else False,
                    'use_rsi': True if 'RSI' in indicators else False,   # RSI < seuil de survente pour acheter
                    'use_macd': True if 'MACD' in indicators else False,
                    'use_mom': True if 'MOM' in indicators else False,
                    'use_stoch': True if 'STOCH' in indicators else False,
                    'use_bb': True if 'Bollinger' in indicators else False,
                },
                    
                # Spécification des indicateurs pour les signaux de vente
                sell_indicators={
                    'use_sma': True if 'SMA' in indicators else False,   # Prix < SMA pour vendre
                    'use_ema': True if 'EMA' in indicators else False,
                    'use_rsi': True if 'RSI' in indicators else False,   # RSI > seuil de surachat pour vendre
                    'use_macd': True if 'MACD' in indicators else False,
                    'use_mom': True if 'MOM' in indicators else False,
                    'use_stoch': True if 'STOCH' in indicators else False,
                    'use_bb': True if 'Bollinger' in indicators else False,
                },
                    
                # Spécification des indicateurs pour la clôture des positions d'achat
                close_buy_indicators={
                    'use_sma': True if 'SMA' in indicators else False,   # Prix < SMA pour clôturer un achat
                    'use_ema': True if 'EMA' in indicators else False,
                    'use_rsi': True if 'RSI' in indicators else False,
                    'use_macd': True if 'MACD' in indicators else False,
                    'use_mom': True if 'MOM' in indicators else False,
                    'use_stoch': True if 'STOCH' in indicators else False,
                    'use_bb': True if 'Bollinger' in indicators else False,
                },
                    
                # Spécification des indicateurs pour la clôture des positions de vente
                close_sell_indicators={
                    'use_sma': True if 'SMA' in indicators else False,   # Prix > SMA pour clôturer une vente
                    'use_ema': True if 'EMA' in indicators else False,
                    'use_rsi': True if 'RSI' in indicators else False,
                    'use_macd': True if 'MACD' in indicators else False,
                    'use_mom': True if 'MOM' in indicators else False,
                    'use_stoch': True if 'STOCH' in indicators else False,
                    'use_bb': True if 'Bollinger' in indicators else False,
                },
                    
                datapath=tmpfile.name  # Set your data file path here
            )

            result, plot_file = CS.main(configu)

            bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=result
            )
            with open(plot_file, 'rb') as image_file:
                bot.send_photo(chat_id, image_file)
                
        # Clean up temporary files
        try:
            os.unlink(tmpfile)
            os.unlink(plot_file)
        except:
            pass
              
    except Exception as e:
        # Handle errors
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=f"❌ Error running backtest: {str(e)}\n\nPlease try again with different parameters.",
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton(text="Back to configuration", callback_data="back_to_main")
            )
        )

bot.infinity_polling()
