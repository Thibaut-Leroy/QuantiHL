import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend
import matplotlib.pyplot as plt
# Patch pyplot.show to prevent GUI crash
plt.show = lambda *args, **kwargs: None
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import backtrader as bt
import backtrader.analyzers as btanalyzers
from backtrader.plot import Plot
import datetime
from datetime import datetime
import pandas as pd
import math
import pandas_ta as ta

class Configuration():
    def __init__(self, initial_cash=100, take_profit=0.05, stop_loss=0.03,
                 use_sma=False, use_ema=False, use_wma=False, use_rsi=False, use_macd=False, use_mom=False, use_stoch=False, use_bb=False,
                 sma_period=20, ema_period=20, wma_period=20, rsi_period=14, rsi_overbought=70, rsi_oversold=30,
                 macd_fast=12, macd_slow=26, macd_signal=9, mom_period=10, stoch_period=14, stoch_period_d=3, stoch_period_k=3,
                 stoch_upper=80, stoch_lower=20, bb_period=20, bb_devfactor=2, datapath='',
                 buy_indicators=None, sell_indicators=None, close_buy_indicators=None, close_sell_indicators=None):
        
        self.initial_cash = initial_cash  
        self.take_profit = take_profit
        self.stop_loss = stop_loss
        self.use_sma = use_sma
        self.use_ema = use_ema
        self.use_wma = use_wma
        self.use_rsi = use_rsi
        self.use_macd = use_macd
        self.use_mom = use_mom
        self.use_stoch = use_stoch
        self.use_bb = use_bb

        self.sma_period = sma_period
        self.ema_period = ema_period
        self.wma_period = wma_period
        self.rsi_period = rsi_period
        self.rsi_overbought = rsi_overbought
        self.rsi_oversold = rsi_oversold
        self.macd_fast = macd_fast
        self.macd_slow = macd_slow
        self.macd_signal = macd_signal
        self.mom_period = mom_period
        self.stoch_period = stoch_period
        self.stoch_period_d = stoch_period_d
        self.stoch_period_k = stoch_period_k
        self.stoch_upper = stoch_upper
        self.stoch_lower = stoch_lower
        self.bb_period = bb_period
        self.bb_devfactor = bb_devfactor

        self.datapath = datapath

        # Signal parameters
        # If no indications, there are all activated by default
        default_indicators = {
            'use_sma': use_sma,
            'use_ema': use_ema,
            'use_wma': use_wma,
            'use_rsi': use_rsi,
            'use_macd': use_macd,
            'use_mom': use_mom,
            'use_stoch': use_stoch,
            'use_bb': use_bb
        }
        
        self.buy_indicators = buy_indicators if buy_indicators is not None else default_indicators
        self.sell_indicators = sell_indicators if sell_indicators is not None else default_indicators
        self.close_buy_indicators = close_buy_indicators if close_buy_indicators is not None else default_indicators
        self.close_sell_indicators = close_sell_indicators if close_sell_indicators is not None else default_indicators

class ConfigurableStrategy(bt.SignalStrategy):
    params = (
        ('verbose', False),
        ('initial_cash', 100),
        
        ('take_profit', 0.05), 
        ('stop_loss', 0.03),
        
        ('use_sma', False),
        ('use_ema', False),
        ('use_wma', False),
        ('use_rsi', False),
        ('use_macd', False),
        ('use_mom', False),
        ('use_stoch', False),
        ('use_bb', False),

        ('sma_period', 20),
        ('ema_period', 20),
        ('wma_period', 20),
        ('rsi_period', 14),
        ('rsi_overbought', 70),
        ('rsi_oversold', 30),
        ('macd_fast', 12),
        ('macd_slow', 26),
        ('macd_signal', 9),
        ('mom_period', 10),
        ('stoch_period', 14),
        ('stoch_period_d', 3),
        ('stoch_period_k', 3),
        ('stoch_upper', 80),
        ('stoch_lower', 20),
        ('bb_period', 20),
        ('bb_devfactor', 2),

        ('buy_indicators', None),
        ('sell_indicators', None),
        ('close_buy_indicators', None),
        ('close_sell_indicators', None),
    )

    def __init__(self):
        self.export_data = []
        self.indicators = {}
        if self.params.use_sma:
            self.indicators['sma'] = bt.ind.SMA(self.data, period=self.params.sma_period)
        
        if self.params.use_ema:
            self.indicators['ema'] = bt.ind.EMA(self.data, period=self.params.ema_period)
        
        if self.params.use_wma:
            self.indicators['wma'] = bt.ind.WeightedMovingAverage(self.data, period=self.params.wma_period)
        
        if self.params.use_rsi:
            self.indicators['rsi'] = bt.ind.RSI(self.data, period=self.params.rsi_period)
        
        if self.params.use_macd:
            self.indicators['macd'] = bt.ind.MACD(self.data, period_me1=self.params.macd_fast, period_me2=self.params.macd_slow, period_signal=self.params.macd_signal)

        if self.params.use_mom:
            self.indicators['mom'] = bt.ind.Momentum(self.data, period=self.params.mom_period)
        
        if self.params.use_stoch:
            self.indicators['stoch'] = bt.ind.Stochastic(self.data, period=self.params.stoch_period, period_dfast=self.params.stoch_period_d, period_dslow=self.params.stoch_period_k)
        
        if self.params.use_bb:
            self.indicators['bb'] = bt.ind.BollingerBands(self.data, period=self.params.bb_period, devfactor=self.params.bb_devfactor)
        
        self.in_pos = False
        self.pos_size = 0
        self.order = None
        self.pnl = 0
        self.wintrade = 0

        self.buy_params_dict = self.params.buy_indicators if self.params.buy_indicators is not None else {
            'use_sma': self.params.use_sma,
            'use_ema': self.params.use_ema,
            'use_wma': self.params.use_wma,
            'use_rsi': self.params.use_rsi,
            'use_macd': self.params.use_macd,
            'use_mom': self.params.use_mom,
            'use_stoch': self.params.use_stoch,
            'use_bb': self.params.use_bb,
        }
        
        self.sell_params_dict = self.params.sell_indicators if self.params.sell_indicators is not None else {
            'use_sma': self.params.use_sma,
            'use_ema': self.params.use_ema,
            'use_wma': self.params.use_wma,
            'use_rsi': self.params.use_rsi,
            'use_macd': self.params.use_macd,
            'use_mom': self.params.use_mom,
            'use_stoch': self.params.use_stoch,
            'use_bb': self.params.use_bb,
        }
        
        self.close_buy_params_dict = self.params.close_buy_indicators if self.params.close_buy_indicators is not None else {
            'use_sma': self.params.use_sma,
            'use_ema': self.params.use_ema,
            'use_wma': self.params.use_wma,
            'use_rsi': self.params.use_rsi,
            'use_macd': self.params.use_macd,
            'use_mom': self.params.use_mom,
            'use_stoch': self.params.use_stoch,
            'use_bb': self.params.use_bb,
        }
        
        self.close_sell_params_dict = self.params.close_sell_indicators if self.params.close_sell_indicators is not None else {
            'use_sma': self.params.use_sma,
            'use_ema': self.params.use_ema,
            'use_wma': self.params.use_wma,
            'use_rsi': self.params.use_rsi,
            'use_macd': self.params.use_macd,
            'use_mom': self.params.use_mom,
            'use_stoch': self.params.use_stoch,
            'use_bb': self.params.use_bb,
        }

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return  # not yet filled

        if order.status == order.Completed:
            if order.isbuy():
                if self.in_pos: # Inverted as we defined data just before so here in_pos = False means we are in pos
                    print(f"✅ Buy at {order.executed.price:.5f}, TP: {self.tp_value}, SL: {self.sl_value}")
                else:
                    self.pnl += order.executed.pnl
                    if order.executed.pnl > 0:
                        self.wintrade += 1
                    print(f"❌ Close Sell at {order.executed.price:.5f}, PNL: {order.executed.pnl:5f} $, All PNL: {self.pnl:5f}, Win Trade: {self.wintrade}")    

            elif order.issell():
                if self.in_pos:
                    print(f"✅ Sell at {order.executed.price:.5f}, TP: {self.tp_value}, SL: {self.sl_value}")
                else:
                    self.pnl += order.executed.pnl
                    if order.executed.pnl > 0:
                        self.wintrade += 1 
                    print(f"❌ Close Buy at {order.executed.price:.5f}, PNL: {order.executed.pnl:5f} $, All PNL: {self.pnl:5f}, Win Trade: {self.wintrade}")   

        if order.status in [order.Completed, order.Canceled, order.Margin, order.Rejected]:
            self.order = None  

    def buy_conditions(self):
        buy_indicators = {
            'use_sma':   self.data.close[0] > self.indicators['sma'] if 'sma' in self.indicators else False,
            'use_ema':   self.data.close[0] > self.indicators['ema'] if 'ema' in self.indicators else False,
            'use_wma':   self.data.close[0] > self.indicators['wma'] if 'wma' in self.indicators else False,
            'use_rsi':   self.indicators['rsi'] < self.params.rsi_oversold if 'rsi' in self.indicators else False,
            'use_macd':  self.indicators['macd'].macd > self.indicators['macd'].signal if 'macd' in self.indicators else False,
            'use_mom':   self.indicators['mom'] > 0 if 'mom' in self.indicators else False,
            'use_stoch': self.indicators['stoch'] < self.params.stoch_lower if 'stoch' in self.indicators else False,
            'use_bb':    self.data.close <= self.indicators['bb'].lines.bot if 'bb' in self.indicators else False,
        }

        active_indicators = [key for key, value in self.buy_params_dict.items() if value]
        
        if not active_indicators:
            return False
        
        signal_expr = True
        for key in active_indicators:
            if key in buy_indicators:
                signal_expr = signal_expr and buy_indicators[key]
        
        return signal_expr
    
    def sell_conditions(self):
        sell_indicators = {
            'use_sma':   self.data.close[0] < self.indicators['sma'] if 'sma' in self.indicators else False,
            'use_ema':   self.data.close[0] < self.indicators['ema'] if 'ema' in self.indicators else False,
            'use_wma':   self.data.close[0] < self.indicators['wma'] if 'wma' in self.indicators else False,
            'use_rsi':   self.indicators['rsi'] > self.params.rsi_overbought if 'rsi' in self.indicators else False,
            'use_macd':  self.indicators['macd'].macd < self.indicators['macd'].signal if 'macd' in self.indicators else False,
            'use_mom':   self.indicators['mom'] < 0 if 'mom' in self.indicators else False,
            'use_stoch': self.indicators['stoch'] > self.params.stoch_upper if 'stoch' in self.indicators else False,
            'use_bb':    self.data.close[0] >= self.indicators['bb'].lines.top if 'bb' in self.indicators else False,
        }

        active_indicators = [key for key, value in self.sell_params_dict.items() if value]
        
        if not active_indicators:
            return False
        
        signal_expr = True
        for key in active_indicators:
            if key in sell_indicators:
                signal_expr = signal_expr and sell_indicators[key]
        
        return signal_expr
    
    def close_conditions(self):
        exit_buy_indicators = {
            'use_sma':   self.data.close[0] < self.indicators['sma'] if 'sma' in self.indicators else False,
            'use_ema':   self.data.close[0] < self.indicators['ema'] if 'ema' in self.indicators else False,
            'use_wma':   self.data.close[0] < self.indicators['wma'] if 'wma' in self.indicators else False,
            'use_rsi':   49 < self.indicators['rsi'] < 51 if 'rsi' in self.indicators else False,
            'use_macd':  self.indicators['macd'].macd < self.indicators['macd'].signal if 'macd' in self.indicators else False,
            'use_mom':   self.indicators['mom'] < 0 if 'mom' in self.indicators else False,
            'use_stoch': self.indicators['stoch'].lines.percK < self.indicators['stoch'].lines.percD if 'stoch' in self.indicators else False,
            'use_bb':    self.data.close[0] >= self.indicators['bb'].lines.mid if 'bb' in self.indicators else False,
        }

        exit_sell_indicators = {
            'use_sma':   self.data.close[0] > self.indicators['sma'] if 'sma' in self.indicators else False,
            'use_ema':   self.data.close[0] > self.indicators['ema'] if 'ema' in self.indicators else False,
            'use_wma':   self.data.close[0] > self.indicators['wma'] if 'wma' in self.indicators else False,
            'use_rsi':   49 < self.indicators['rsi'] < 51 if 'rsi' in self.indicators else False,
            'use_macd':  self.indicators['macd'].macd > self.indicators['macd'].signal if 'macd' in self.indicators else False,
            'use_mom':   self.indicators['mom'] > 0 if 'mom' in self.indicators else False,
            'use_stoch': self.indicators['stoch'].lines.percK > self.indicators['stoch'].lines.percD if 'stoch' in self.indicators else False,
            'use_bb':    self.data.close[0] <= self.indicators['bb'].lines.mid if 'bb' in self.indicators else False,
        }

        if self.pos_size > 0:
            active_indicators = [key for key, value in self.close_buy_params_dict.items() if value]
            signal_expr = False
            if active_indicators:
                signal_expr = True
                for key in active_indicators:
                    if key in exit_buy_indicators:
                        signal_expr = signal_expr and exit_buy_indicators[key]
            
            tp_reach = self.price > self.tp_value
            sl_reach = self.price < self.sl_value

            signal_expr = signal_expr or (tp_reach or sl_reach)

            return signal_expr
        
        if self.pos_size < 0:
            active_indicators = [key for key, value in self.close_sell_params_dict.items() if value]
            signal_expr = False
            if active_indicators:
                signal_expr = True
                for key in active_indicators:
                    if key in exit_sell_indicators:
                        signal_expr = signal_expr and exit_sell_indicators[key]
            
            tp_reach = self.price < self.tp_value
            sl_reach = self.price > self.sl_value

            signal_expr = signal_expr or (tp_reach or sl_reach)

            return signal_expr
        
        return False

    def next(self):
        # Stocking data so we can use it later
        dt = self.data.datetime.datetime(0)
        o = self.data.open[0]
        h = self.data.high[0]
        l = self.data.low[0]
        c = self.data.close[0]
        v = self.data.volume[0]

        self.export_data.append({
            'datetime': dt,
            'open': o,
            'high': h,
            'low': l,
            'close': c,
            'volume': v
        })

        self.price = self.data.close[0]
        if self.params.use_sma:
            self.sma = self.indicators['sma']
        if self.params.use_ema:
            self.ema = self.indicators['ema']
        if self.params.use_wma:
            self.wma = self.indicators['wma']
        if self.params.use_rsi:
            self.rsi = self.indicators['rsi']
        if self.params.use_macd:
            self.macd = self.indicators['macd'].macd
            self.signal = self.indicators['macd'].signal
        if self.params.use_mom:
            self.mom = self.indicators['mom']
        if self.params.use_stoch:
            self.stoch = self.indicators['stoch'].lines.percK
        if self.params.use_bb:
            self.lower_bb = self.indicators['bb'].lines.bot
            self.middle_bb = self.indicators['bb'].lines.mid
            self.upper_bb = self.indicators['bb'].lines.top

        amount = min(10, self.broker.get_cash())
        self.size = round(amount / self.price, 5)
        if self.order:
            return

        if not self.in_pos:
            if self.buy_conditions():
                self.order = self.buy(size=self.size)
                self.in_pos = True
                self.pos_size = 1
                self.sl_value = round((1 - self.params.stop_loss) * self.price, 5)
                self.tp_value = round((1 + self.params.take_profit) * self.price, 5)
                
            elif self.sell_conditions():
                self.order = self.sell(size=self.size)
                self.in_pos = True
                self.pos_size = -1
                self.sl_value = round((1 + self.params.stop_loss) * self.price, 5)
                self.tp_value = round((1 - self.params.take_profit) * self.price, 5)


        else:
            if self.close_conditions():
                    self.order = self.close()
                    self.in_pos = False
                    self.pos_size = 0

        # Check if we are on the latest price so we close everything before stopping the strat
        if len(self.data) == self.data.buflen() - 1:
            if self.in_pos:
                self.order = self.close()
                self.in_pos = False
                self.pos_size = 0

class BacktestRunner:
    def __init__(self, datapath, start_date=None, end_date=None):
        self.datapath = datapath
        self.start_date = start_date if start_date else datetime.datetime(2010, 1, 1)
        self.end_date = end_date if end_date else datetime.datetime.now()
        self.cerebro = bt.Cerebro()
        self.cerebro.broker.set_coc(True)
        self.strategy_params = {}
        self.result_texte = ''
        
    def set_params(self, **kwargs):
        self.strategy_params = kwargs
        print(self.strategy_params) ####################
        
    def add_data(self):
        data = bt.feeds.GenericCSVData(
            dataname = self.datapath,
            fromdate=self.start_date,
            todate=self.end_date,
            nullvalue=0.0,
            dtformat=('%Y-%m-%d %H:%M:%S'),
            datetime=0, high=2, low=3, open=1, close=4, volume=5, openinterest=-1    
        )
        self.cerebro.adddata(data)
        
    def run(self):
        self.cerebro.addstrategy(ConfigurableStrategy, **self.strategy_params)
        self.cerebro.broker.setcash(ConfigurableStrategy.params.initial_cash)
        #self.cerebro.broker.setcommission(commission=0.001)  # Add a commission (to use real market condition)
        #self.cerebro.addsizer(bt.sizers.PercentSizer, percents=95)  # Use 95% of capital for each trade
        
        # Add analyzers
        self.cerebro.addanalyzer(btanalyzers.SharpeRatio, _name = 'sharpe')
        self.cerebro.addanalyzer(btanalyzers.TradeAnalyzer, _name = 'TradeAnalyzor')
        self.cerebro.addanalyzer(btanalyzers.TradeAnalyzer, _name = 'trades')
        self.cerebro.addanalyzer(btanalyzers.DrawDown, _name='drawdown')
        self.cerebro.addanalyzer(btanalyzers.Returns, _name='returns')
        
        back = self.cerebro.run()
        #self.display_results(back[0])

        return back[0]    

    def plot_with_plotly(self, datafile):
        filename = "backtrader_plot.html"
        
        try:
            data = self.cerebro.datas[0]
            #dp = back.export_data
            dp = pd.read_csv(datafile)
            df = pd.DataFrame(dp)

            df = df.rename(columns={
                'timestamp': 'Date',
                'open': 'Open',
                'high': 'High',
                'low': 'Low',
                'close': 'Close',
                'volume': 'Volume'
            })
            #df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d %H:%M:%S')
            #df['Date'] = pd.to_datetime(df['Date'])  # conversion en datetime (PAS strftime)
            #df['Date'] += pd.to_timedelta(df.groupby('Date').cumcount(), unit='us')

            df = df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]
            strategies = self.cerebro.runstrats[0][0].indicators.items()

            if 'rsi' in dict(strategies):
                nb_row = 3
                titles = ('Price','Volume','RSI')
                height = [0.6, 0.1, 0.3]
            elif 'macd' in dict(strategies):
                nb_row = 3
                titles = ('Price','Volume','MACD')
                height = [0.6, 0.1, 0.3]
            else:
                nb_row = 2
                titles = ('Price','Volume')
                height = [0.8, 0.2]

            fig = make_subplots(rows=nb_row, cols=1, shared_xaxes=True, 
                                vertical_spacing=0.1, 
                                subplot_titles=titles,
                                row_heights=height)
            
            fig.add_trace(
                go.Candlestick(
                    x=df['Date'],
                    open=df['Open'],
                    high=df['High'],
                    low=df['Low'],
                    close=df['Close'],
                    name='Price'
                ),
                row=1, col=1
            )
            
            fig.add_trace(
                go.Bar(
                    x=df['Date'],
                    y=df['Volume'],
                    name='Volume'
                ),
                row=2, col=1
            )

            if 'macd' in dict(strategies):
                macd = ta.macd(df['Close'], fast=self.strategy_params['macd_fast'], slow=self.strategy_params['macd_slow'], signal=self.strategy_params['macd_signal'])

                macd_values = macd[f"MACD_{self.strategy_params['macd_fast']}_{self.strategy_params['macd_slow']}_{self.strategy_params['macd_signal']}"]
                signal_values = macd[f"MACDs_{self.strategy_params['macd_fast']}_{self.strategy_params['macd_slow']}_{self.strategy_params['macd_signal']}"]
                #histo_values = macd[f"MACDh_{self.strategy_params['macd_fast']}_{self.strategy_params['macd_slow']}_{self.strategy_params['macd_signal']}"]

                fig.add_trace(
                    go.Scatter(
                        x=df['Date'],
                        y=list(macd_values),
                        mode='lines',
                        name='MACD',
                        line=dict(color='blue')
                    ),
                    row=3, col=1
                )
                
                fig.add_trace(
                    go.Scatter(
                        x=df['Date'],
                        y=list(signal_values),
                        mode='lines',
                        name='Signal',
                        line=dict(color='red')
                    ),
                    row=3, col=1
                )
            
            if 'bb' in dict(strategies):
                bb = ta.bbands(df['Close'], length=self.strategy_params['bb_period'], std=self.strategy_params['bb_devfactor'])
                top_values = bb[f"BBU_{self.strategy_params['bb_period']}_{float(self.strategy_params['bb_devfactor'])}"]
                mid_values = bb[f"BBM_{self.strategy_params['bb_period']}_{float(self.strategy_params['bb_devfactor'])}"]
                bot_values = bb[f"BBL_{self.strategy_params['bb_period']}_{float(self.strategy_params['bb_devfactor'])}"]
                
                fig.add_trace(
                    go.Scatter(
                        x=df['Date'],
                        y=list(top_values),
                        mode='lines',
                        name='BB Upper',
                        line=dict(color='rgba(250, 0, 0, 0.7)')
                    ),
                    row=1, col=1
                )
                
                fig.add_trace(
                    go.Scatter(
                        x=df['Date'],
                        y=list(mid_values),
                        mode='lines',
                        name='BB Middle',
                        line=dict(color='rgba(0, 0, 250, 0.7)')
                    ),
                    row=1, col=1
                )
                
                fig.add_trace(
                    go.Scatter(
                        x=df['Date'],
                        y=list(bot_values),
                        mode='lines',
                        name='BB Lower',
                        line=dict(color='rgba(250, 0, 0, 0.7)')
                    ),
                    row=1, col=1
                )

            if 'sma' in dict(strategies):
                color = 'red'
                indicator_values = ta.sma(df['Close'], timeperiod=self.strategy_params['sma_period'])
                fig.add_trace(
                    go.Scatter(
                        x=df['Date'],
                        y=list(indicator_values),
                        mode='lines',
                        name='SMA',
                        line=dict(color=color)
                    ),
                    row=1, col=1
                )

            if 'ema' in dict(strategies):
                color = 'green'
                indicator_values = ta.ema(df['Close'], timeperiod=self.strategy_params['ema_period'])
                fig.add_trace(
                    go.Scatter(
                        x=df['Date'],
                        y=list(indicator_values),
                        mode='lines',
                        name='EMA',
                        line=dict(color=color)
                    ),
                    row=1, col=1
                )

            if 'rsi' in dict(strategies):
                color = 'black'
                indicator_values = ta.rsi(df['Close'], length=self.strategy_params['rsi_period'])
                fig.add_trace(
                    go.Scatter(
                        x=df['Date'],
                        y=list(indicator_values),
                        mode='lines',
                        name='RSI',
                        line=dict(color=color)
                    ),
                    row=3, col=1
                )

            fig.update_layout(
                title='Backtest Results',
                xaxis_title='Date',
                yaxis_title='Price',
                height=800,
                width=1200,
                showlegend=True,
                xaxis_rangeslider_visible=False
            )
            
            fig.write_image(filename, 'png')

            return filename
        except Exception as e:
            print(f"Error creating Plotly chart: {e}")
            return None

    def display_results(self, back):
        final_capital = self.cerebro.broker.getvalue()
        final_cash = self.cerebro.broker.getcash()

        trades = back.analyzers.trades.get_analysis()
        nombre_trade = trades.total.total

        if nombre_trade > 0:
            rtrn = back.analyzers.returns.get_analysis()
            win_trade = trades.won.total if trades.won else 0
            win_rate = (win_trade / nombre_trade) * 100
            avg_profit_per_trade = trades.pnl.gross.total  / nombre_trade
            max_drawdown = trades.lost.pnl.get('max', 'N/A')

            self.result_texte = "===== Backtest Result ====="
            self.result_texte+=f'\n Final Capital : {round(final_capital,2)} $'
            self.result_texte+=f'\n Total trades : {nombre_trade}'
            self.result_texte+=f"\n Average return : {round(rtrn.get('ravg','N/A'),3)} %"
            self.result_texte+=f'\n Average profit : {round(avg_profit_per_trade,6)} $'
            self.result_texte+=f"\n Total return: {rtrn.get('rtot100', 0.0):.4f}%"
            self.result_texte+=f"\n Annualized return: {rtrn.get('rnorm100', 0.0):.4f}%"
            self.result_texte+=f'\n Win rate : {round(win_rate,2)} %'
            self.result_texte+=f"\n Drawdown max : {round(max_drawdown,3)} $"
        else:
            self.result_texte+="===== Résumé des performances ====="
            self.result_texte+=f'\n Capital final : {round(final_capital,2)} $'
            self.result_texte+=f'\n Cash restant : {round(final_cash,2)} $'
            self.result_texte+=f"\n Aucune position n'a été prises"
        
        return str(self.result_texte)


def get_first_and_last_date(csv_file):
    df = pd.read_csv(csv_file)

    df['timestamp'] = pd.to_datetime(df['timestamp'])
    first_date = df['timestamp'].min()
    last_date = df['timestamp'].max()

    first_date = first_date.strftime('%Y-%m-%d')
    last_date = last_date.strftime('%Y-%m-%d')

    return first_date, last_date

def main(config):
    start, end = get_first_and_last_date(config.datapath)

    start_date = datetime.strptime(start, '%Y-%m-%d')
    end_date = datetime.strptime(end, '%Y-%m-%d')
    
    runner = BacktestRunner(config.datapath, start_date, end_date)
    
    params = {
        # General params
        'verbose': False,
        'initial_cash': config.initial_cash,
        'take_profit': config.take_profit,
        'stop_loss': config.stop_loss,
        
        # Add indicators
        'use_sma': config.use_sma,
        'use_ema': config.use_ema,
        'use_wma': config.use_wma,
        'use_rsi': config.use_rsi,
        'use_macd': config.use_macd,
        'use_mom': config.use_mom,
        'use_stoch': config.use_stoch,
        'use_bb': config.use_bb,
        
        # Indicators params
        'sma_period': config.sma_period,
        'ema_period': config.ema_period,
        'wma_period': config.wma_period,
        'rsi_period': config.rsi_period,
        'rsi_overbought': config.rsi_overbought,
        'rsi_oversold': config.rsi_oversold,
        'macd_fast': config.macd_fast,
        'macd_slow': config.macd_slow,
        'macd_signal': config.macd_signal,
        'mom_period': config.mom_period,
        'stoch_period': config.stoch_period,
        'stoch_period_d': config.stoch_period_d,
        'stoch_period_k': config.stoch_period_k,
        'stoch_upper': config.stoch_upper,
        'stoch_lower': config.stoch_lower,
        'bb_period': config.bb_period,
        'bb_devfactor': config.bb_devfactor,
    }
    
    runner.set_params(**params)
    runner.add_data()
    back = runner.run()
    sum = runner.display_results(back)
    plot_file = runner.plot_with_plotly(config.datapath)

    return sum, plot_file

# Create a Configuration instance with your desired settings
configu = Configuration(
    initial_cash=100,
    take_profit=0.05,
    stop_loss=0.03,
    
    # Add indicators to calculate
    use_sma=True,
    use_ema=False,
    use_rsi=False,
    use_macd=False,
    use_mom=False,
    use_stoch=False,
    use_bb=False,
    sma_period=200,

    # Indicators to use for buy signal
    buy_indicators={
        'use_sma': True,   # Price > SMA to buy
        'use_ema': False,
        'use_rsi': False,   # RSI < oversold to buy
        'use_macd': False,
        'use_mom': False,
        'use_stoch': False,
        'use_bb': False,
    },
        
    # Indicators to use for sell signal
    sell_indicators={
        'use_sma': True,   # Price < SMA to sell
        'use_ema': False,
        'use_rsi': False,   # RSI > overbought to sell
        'use_macd': False,
        'use_mom': False,
        'use_stoch': False,
        'use_bb': False,
    },
        
    # Indicators to use to close a buy position
    close_buy_indicators={
        'use_sma': True,   # Price < SMA pour to close a buy
        'use_ema': False,
        'use_rsi': False,
        'use_macd': False,
        'use_mom': False,
        'use_stoch': False,
        'use_bb': False,
    },
        
    # Indicators to use to close a sell position
    close_sell_indicators={
        'use_sma': True,   # Price > SMA to close a sell
        'use_ema': False,
        'use_rsi': False,
        'use_macd': False,
        'use_mom': False,
        'use_stoch': False,
        'use_bb': False,
    },
        
    datapath='/Users/thibautleroy/PythonCode/0-Hyperliquid/getdata/data/BTC_5m_20250406_163733_historical.csv'  # Set your data file path here
)
