import backtrader as bt
# 导入backtrader库，并将其命名为bt，以便后续代码中可以使用bt来调用backtrader库中的功能。 (引入交易回测框架backtrader，并给它起个简称bt，方便后面用。)
import datetime
# 导入datetime库，用于处理日期和时间相关的操作。 (引入日期时间库，让程序能处理年月日时分秒。)
import math
# 导入math库，提供数学运算功能，例如平方根、对数等。 (引入数学库，有了它就能做各种数学计算，像加减乘除开方。)
import pandas as pd
# 导入pandas库，用于数据处理和分析，特别是处理表格数据。 (引入pandas数据分析库，专门用来处理表格数据，就像Excel那样。)
import os
# 导入os库，提供与操作系统交互的功能，例如文件路径操作。 (引入操作系统库，让程序能跟电脑系统打交道，比如找文件，创建文件夹。)
import sys
# 导入sys库，提供访问和控制Python运行时环境的功能。 (引入系统库，可以用来访问和控制Python程序的运行环境。)
import numpy as np
# 导入numpy库，用于进行数值计算，特别是处理多维数组。 (引入numpy数值计算库，擅长处理数字，特别是很多数字排成队的那种。)
import matplotlib.pyplot as plt
# 导入matplotlib.pyplot模块，用于创建图表和可视化。 (引入matplotlib绘图库，pyplot是它的一个画图工具，用来画各种图表。)
import time
# 导入time库，提供时间相关的功能，例如暂停程序执行。 (引入时间库，可以用来获取当前时间，或者让程序休息一下。)
import itertools  # 可能需要引入

class AShareETFSizer(bt.Sizer):
    params = (
        # Parameters moved from strategy or new for sizer
        ('etf_type_param_name', 'etf_type'), # Name of the etf_type param in strategy
        ('risk_per_trade_trend', 0.01),
        ('risk_per_trade_range', 0.005),
        ('max_position_per_etf_percent', 0.30),
        # 'max_total_account_risk_percent' is harder to implement purely in sizer
        # as it requires knowledge of all other potential trades/positions' risk.
        # For simplicity, we'll focus the sizer on single trade constraints.
        # Strategy can provide an overall risk check before calling buy/sell.
        ('trend_stop_loss_atr_mult_param_name', 'trend_stop_loss_atr_mult'),
        ('range_stop_loss_buffer_param_name', 'range_stop_loss_buffer'),
        ('atr_indicator_name_prefix', 'atr_'), # If strategy stores ATRs like self.atr_DATANAME
    )

    def _getsizing(self, comminfo, cash, data, isbuy):
        if not isbuy: # This strategy/sizer is for long entries
            return 0

        position = self.broker.getposition(data)
        if position.size != 0: # Already in market for this data
            return 0 

        d_name = data._name
        strategy = self.strategy # Access to the strategy instance

        # Get etf_type for this data (assuming it's a global strategy param for now)
        # A more robust way would be if the strategy provides a per-data etf_type
        current_etf_type = getattr(strategy.params, self.p.etf_type_param_name, 'trend') # Default to trend

        if current_etf_type == 'trend':
            risk_per_trade_percent = self.p.risk_per_trade_trend
            atr_mult_param_name = self.p.trend_stop_loss_atr_mult_param_name
            atr_mult = getattr(strategy.params, atr_mult_param_name)
            
            # Sizer needs to access ATR calculated by the strategy
            # Assuming strategy stores ATR indicators in a dict like self.atrs keyed by data name
            if not hasattr(strategy, 'atrs') or d_name not in strategy.atrs:
                strategy.log(f"Sizer: ATR indicator for {d_name} not found in strategy.atrs. Skipping trade.", data=data)
                return 0
            current_atr = strategy.atrs[d_name][0]
            if math.isnan(current_atr) or current_atr <= 1e-9:
                strategy.log(f"Sizer: Invalid ATR value ({current_atr}) for {d_name}. Skipping trade.", data=data)
                return 0

            entry_price_ref = data.close[0] # Reference for SL calculation
            stop_loss_price_ref = entry_price_ref - atr_mult * current_atr
        
        elif current_etf_type == 'range':
            risk_per_trade_percent = self.p.risk_per_trade_range
            sl_buffer_param_name = self.p.range_stop_loss_buffer_param_name
            sl_buffer = getattr(strategy.params, sl_buffer_param_name)

            entry_price_ref = data.close[0] # Reference for SL calculation
            # For range, SL is based on current low. Sizer uses current data.
            # Strategy will use current low for its bracket order's stop price.
            # Sizer calculates its reference SL similarly.
            if not hasattr(strategy, 'lows') or d_name not in strategy.lows:
                strategy.log(f"Sizer: Low price series for {d_name} not found in strategy.lows. Skipping trade.", data=data)
                return 0

            stop_loss_price_ref = strategy.lows[d_name][0] * (1 - sl_buffer)
        else:
            strategy.log(f"Sizer: Unknown ETF type '{current_etf_type}' for {d_name}. Skipping trade.", data=data)
            return 0

        if stop_loss_price_ref >= entry_price_ref:
            strategy.log(
                f"Sizer: Stop loss {stop_loss_price_ref:.2f} not below entry {entry_price_ref:.2f} for {d_name}. Cannot size.", data=data)
            return 0

        risk_per_share = entry_price_ref - stop_loss_price_ref
        if risk_per_share <= 1e-9:
            strategy.log(
                f"Sizer: Risk per share for {d_name} is zero or too small ({risk_per_share:.2f}). Cannot size.", data=data)
            return 0

        # Access current_risk_multiplier from strategy
        effective_risk_percent = risk_per_trade_percent * strategy.current_risk_multiplier
        equity = self.broker.getvalue()
        
        max_amount_to_risk_on_this_trade = equity * effective_risk_percent
        
        size_raw = max_amount_to_risk_on_this_trade / risk_per_share
        size = int(size_raw / 100) * 100 # Round down for A-shares

        if size <= 0:
            strategy.log(
                f"Sizer: Calculated size for {d_name} based on risk is {size}. Risk/share: {risk_per_share:.2f}. Amount to risk: {max_amount_to_risk_on_this_trade:.2f}", data=data)
            return 0

        # Max position value per ETF
        max_pos_value_for_etf = equity * self.p.max_position_per_etf_percent
        price_for_value_calc = entry_price_ref # Use the same reference price
        
        if price_for_value_calc <= 1e-9:
            strategy.log(
                f"Sizer: Invalid price ({price_for_value_calc:.2f}) for {d_name} value calculation.", data=data)
            return 0
            
        size_limited_by_max_etf_pos = int(max_pos_value_for_etf / price_for_value_calc / 100) * 100
        if size > size_limited_by_max_etf_pos:
            strategy.log(
                f"Sizer: Size for {d_name} reduced from {size} to {size_limited_by_max_etf_pos} by max_position_per_etf_percent.", data=data)
            size = size_limited_by_max_etf_pos

        if size <= 0:
            strategy.log(
                f"Sizer: Calculated size for {d_name} after max ETF position limit is {size}.", data=data)
            return 0

        # Cash limit
        potential_trade_total_cost = size * price_for_value_calc
        if potential_trade_total_cost > cash:
            size_limited_by_cash = int(cash / price_for_value_calc / 100) * 100
            if size_limited_by_cash < size:
                strategy.log(
                    f"Sizer: Size for {d_name} reduced from {size} to {size_limited_by_cash} by cash limit. Cash: {cash:.2f}, Cost approx: {potential_trade_total_cost:.2f}", data=data)
                size = size_limited_by_cash
        
        if size <= 0:
            strategy.log(
                f"Sizer: Final calculated size for {d_name} is {size}. Cannot place order.", data=data)
            return 0
        
        strategy.log(f"Sizer for {d_name} calculated size: {size} based on entry_ref: {entry_price_ref:.2f}, sl_ref: {stop_loss_price_ref:.2f}", data=data)
        return size
class AShareETFStrategy(bt.Strategy):
    params = (
        ('etf_type', 'trend'), # THIS PARAMETER IS NOW ACCESSED BY THE SIZER
        ('ema_medium_period', 60),
        ('ema_long_period', 120),
        ('adx_period', 14),
        ('atr_period', 20), # Strategy still needs this to pass ATR values to sizer indirectly
        ('bbands_period', 20),
        ('bbands_devfactor', 2.0),
        ('rsi_period', 14),
        ('rsi_oversold', 30),
        ('trend_breakout_lookback', 60),
        ('trend_volume_avg_period', 20),
        ('trend_volume_ratio_min', 1.1),
        # Sizing specific params moved to sizer, but strategy needs these for bracket price calculation
        ('trend_stop_loss_atr_mult', 2.5),
        ('trend_take_profit_rratio', 2.0),
        ('range_stop_loss_buffer', 0.005),
        # Risk per trade is now in sizer
        # Max position per ETF is now in sizer
        # Max total account risk is a strategy-level concern before calling buy/sell
        ('max_total_account_risk_percent', 0.06), 
        ('drawdown_level1_threshold', 0.05),
        ('drawdown_level2_threshold', 0.10),
    )

    def log(self, txt, dt=None, data=None):
        # ... (log function remains the same)
        _data = data if data is not None else (
            self.datas[0] if self.datas else None) 
        
        log_dt_str = ""
        if _data and hasattr(_data, 'datetime') and len(_data.datetime) > 0 : 
            dt = dt or _data.datetime.date(0)
            log_dt_str = dt.isoformat()
        elif dt: 
             log_dt_str = dt.isoformat() if isinstance(dt, (datetime.date, datetime.datetime)) else str(dt)
        else: 
            log_dt_str = datetime.datetime.now().date().isoformat()

        prefix = ""
        if _data and hasattr(_data, '_name') and _data._name:
            prefix = f"[{_data._name}] "
        
        print(f"{log_dt_str} {prefix}{txt}")

    def __init__(self):
        # Keep data series references easily accessible
        self.closes = {d._name: d.close for d in self.datas}
        self.opens = {d._name: d.open for d in self.datas}
        self.highs = {d._name: d.high for d in self.datas}
        self.lows = {d._name: d.low for d in self.datas}
        self.volumes = {d._name: d.volume for d in self.datas}

        # Store indicators in dictionaries keyed by data name
        self.emas_medium = {d._name: bt.indicators.EMA(d.close, period=self.params.ema_medium_period) for d in self.datas}
        self.emas_long = {d._name: bt.indicators.EMA(d.close, period=self.params.ema_long_period) for d in self.datas}
        self.adxs = {d._name: bt.indicators.ADX(d, period=self.params.adx_period) for d in self.datas}
        self.atrs = {d._name: bt.indicators.ATR(d, period=self.params.atr_period) for d in self.datas} # Sizer will need this
        self.bbands = {d._name: bt.indicators.BollingerBands(d.close, period=self.params.bbands_period, devfactor=self.params.bbands_devfactor) for d in self.datas}
        self.rsis = {d._name: bt.indicators.RSI(d.close, period=self.params.rsi_period) for d in self.datas}
        self.highest_highs = {d._name: bt.indicators.Highest(d.high, period=self.params.trend_breakout_lookback) for d in self.datas}
        self.sma_volumes = {d._name: bt.indicators.SMA(d.volume, period=self.params.trend_volume_avg_period) for d in self.datas}

        self.orders = {d._name: None for d in self.datas}
        self.buy_prices = {d._name: None for d in self.datas}
        self.position_types = {d._name: None for d in self.datas}

        self.high_water_mark = self.broker.startingcash
        self.drawdown_level1_triggered = False
        self.halt_trading = False
        self.current_risk_multiplier = 1.0 # Sizer will access this

    # ... (notify_order, notify_trade, notify_cashvalue remain largely the same,
    #      ensure they use d_name for dictionary access)

    def notify_order(self, order):
        order_data_name = order.data._name if hasattr(order.data, '_name') else 'Unknown_Data'

        if order.status in [order.Submitted, order.Accepted]:
            self.log(f'Order {order.ref} Submitted/Accepted for {order_data_name}', data=order.data)
            if order.parent is None: 
                self.orders[order_data_name] = order
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    f'BUY EXECUTED for {order_data_name} @ {order.executed.price:.2f}, Size: {order.executed.size}, Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}', data=order.data)
                self.buy_prices[order_data_name] = order.executed.price
            elif order.issell(): 
                self.log(
                    f'SELL EXECUTED for {order_data_name} @ {order.executed.price:.2f}, Size: {order.executed.size}, Value: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}', data=order.data)
        
        elif order.status in [order.Canceled, order.Margin, order.Rejected, order.Expired]:
            self.log(
                f'Order {order.ref} for {order_data_name} Canceled/Margin/Rejected/Expired: Status {order.getstatusname()}', data=order.data)

        if self.orders.get(order_data_name) == order and not order.alive():
            self.orders[order_data_name] = None
            
    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        data_name = trade.data._name if hasattr(trade.data, '_name') else 'Unknown_Data'
        self.log(
            f'OPERATION PROFIT for {data_name}, GROSS {trade.pnl:.2f}, NET {trade.pnlcomm:.2f}, Position Type: {self.position_types.get(data_name, "N/A")}', data=trade.data)

        if data_name in self.position_types: self.position_types[data_name] = None
        if data_name in self.buy_prices: self.buy_prices[data_name] = None
            
    def notify_cashvalue(self, cash, value):
        self.high_water_mark = max(self.high_water_mark, value)
        drawdown = (self.high_water_mark - value) / self.high_water_mark if self.high_water_mark > 1e-9 else 0

        if drawdown > self.params.drawdown_level2_threshold:
            if not self.halt_trading:
                self.log(
                    f'!!! RED ALERT: Drawdown {drawdown*100:.2f}% > {self.params.drawdown_level2_threshold*100:.0f}%. HALTING TRADING !!!')
                self.halt_trading = True
        elif drawdown > self.params.drawdown_level1_threshold:
            if not self.drawdown_level1_triggered: 
                self.log(
                    f'-- YELLOW ALERT: Drawdown {drawdown*100:.2f}% > {self.params.drawdown_level1_threshold*100:.0f}%. Reducing risk.--')
                self.drawdown_level1_triggered = True
                self.current_risk_multiplier = 0.5
        else: 
            if self.halt_trading: 
                self.log('--- Trading Resumed (Drawdown below Level 2) ---')
                self.halt_trading = False
                if drawdown <= self.params.drawdown_level1_threshold:
                    if self.drawdown_level1_triggered:
                         self.log('--- Risk Level Restored (Drawdown below Level 1) ---')
                         self.drawdown_level1_triggered = False
                         self.current_risk_multiplier = 1.0
                elif self.drawdown_level1_triggered: 
                    self.current_risk_multiplier = 0.5
            elif self.drawdown_level1_triggered and drawdown <= self.params.drawdown_level1_threshold : 
                self.log('--- Risk Level Restored (Drawdown below Level 1) ---')
                self.drawdown_level1_triggered = False
                self.current_risk_multiplier = 1.0

    # REMOVE _calculate_trade_size method from strategy

    def next(self):
        if self.halt_trading:
            for d_obj in self.datas:
                d_name = d_obj._name
                position = self.getposition(d_obj)
                order = self.orders.get(d_name)
                if position.size != 0 and not order:
                    self.log(
                        f'HALTED: Attempting to close position for {d_name} Size: {position.size}', data=d_obj)
                    order_close = self.close(data=d_obj)
                    if order_close:
                        self.orders[d_name] = order_close
                    else:
                        self.log(
                            f'HALTED: Failed to create close order for {d_name}', data=d_obj)
            return

        for i, d_obj in enumerate(self.datas):
            d_name = d_obj._name
            position = self.getposition(d_obj)
            order = self.orders.get(d_name)

            if order:
                continue
            
            if position.size == 0: # No position, check for entry
                market_state = 'UNCERTAIN_DO_NOT_TRADE'
                current_close = self.closes[d_name][0]
                current_open = self.opens[d_name][0]
                current_low = self.lows[d_name][0]
                current_volume = self.volumes[d_name][0]
                
                ema_medium_val = self.emas_medium[d_name][0]
                ema_medium_prev = self.emas_medium[d_name][-1]
                ema_long_val = self.emas_long[d_name][0]
                ema_long_prev = self.emas_long[d_name][-1]
                adx_val = self.adxs[d_name].adx[0]
                bb_top = self.bbands[d_name].top[0]
                bb_bot = self.bbands[d_name].bot[0]
                bb_mid = self.bbands[d_name].mid[0]
                rsi_val = self.rsis[d_name][0]
                highest_high_prev = self.highest_highs[d_name][-1]
                sma_volume_val = self.sma_volumes[d_name][0]
                atr_val = self.atrs[d_name][0]

                try:
                    is_trend_up = (current_close > ema_medium_val > ema_long_val and
                                   ema_medium_val > ema_medium_prev and
                                   ema_long_val > ema_long_prev)
                    
                    is_range_confirmed = (not is_trend_up and
                                          abs(ema_medium_val / ema_medium_prev - 1) < 0.003 and
                                          abs(ema_long_val / ema_long_prev - 1) < 0.003 and
                                          adx_val < 20 and
                                          (bb_top - bb_bot) / current_close < 0.07 if current_close > 1e-9 else False)

                    if is_trend_up:
                        market_state = 'TREND_UP'
                    elif is_range_confirmed and self.p.etf_type == 'range': # Use self.p for strategy params
                        market_state = 'RANGE_CONFIRMED'
                except IndexError:
                    continue

                entry_signal = False
                potential_position_type = None
                limit_entry_price_calc = current_close 
                
                stop_loss_price_calc = None
                take_profit_price_calc = None
                # risk_per_trade_percent is now handled by Sizer based on etf_type

                if market_state == 'TREND_UP' and self.p.etf_type == 'trend':
                    try:
                        is_breakout = (current_close > highest_high_prev and
                                       current_volume > sma_volume_val * self.params.trend_volume_ratio_min)
                        is_pullback = (min(abs(current_low / ema_medium_val - 1), abs(current_low / ema_long_val - 1)) < 0.01 and
                                       current_close > current_open) if ema_medium_val > 1e-9 and ema_long_val > 1e-9 else False

                        if is_breakout or is_pullback:
                            entry_signal = True
                            potential_position_type = 'trend'
                            stop_loss_price_calc = current_close - self.p.trend_stop_loss_atr_mult * atr_val
                            if stop_loss_price_calc < current_close:
                                risk_per_share_calc = current_close - stop_loss_price_calc
                                if risk_per_share_calc > 1e-9:
                                    take_profit_price_calc = current_close + self.p.trend_take_profit_rratio * risk_per_share_calc
                                else:
                                    entry_signal = False
                            else:
                                entry_signal = False
                    except IndexError:
                        continue

                elif market_state == 'RANGE_CONFIRMED' and self.p.etf_type == 'range':
                    try:
                        is_range_buy = (current_low <= bb_bot and
                                        current_close > bb_bot and
                                        rsi_val < self.params.rsi_oversold)
                        if is_range_buy:
                            entry_signal = True
                            potential_position_type = 'range'
                            stop_loss_price_calc = current_low * (1 - self.p.range_stop_loss_buffer)
                            take_profit_price_calc = bb_mid
                            if stop_loss_price_calc >= limit_entry_price_calc:
                                entry_signal = False
                    except IndexError:
                        continue
                
                if entry_signal and stop_loss_price_calc is not None and limit_entry_price_calc > stop_loss_price_calc:
                    # The Sizer will be called automatically by buy_bracket if size is not provided.
                    # The Sizer will use its own logic (based on current data and strategy state)
                    # to determine the size.
                    
                    # Check max_total_account_risk_percent before attempting to place new trade
                    # This is a strategy-level check before invoking sizer
                    # For simplicity, this check is omitted here but would involve summing
                    # potential risk of existing positions + potential risk of this new trade.
                    # If this check fails, we would 'continue' to the next data or bar.

                    self.log(
                        f'BUY SIGNAL (Bracket): {d_name}, Proposed Limit Entry: {limit_entry_price_calc:.2f}, SL for bracket: {stop_loss_price_calc:.2f}, TP for bracket: {take_profit_price_calc if take_profit_price_calc else "N/A"}, Type: {potential_position_type}', data=d_obj)
                    
                    main_order_limit_price = limit_entry_price_calc 
                    
                    tp_price_for_bracket = take_profit_price_calc if take_profit_price_calc and take_profit_price_calc > main_order_limit_price else None
                    
                    if tp_price_for_bracket is None and potential_position_type == 'trend':
                         self.log(f'Warning for {d_name}: TP price for trend trade is None or invalid. Bracket will not have a limit sell.', data=d_obj)

                    # Call buy_bracket WITHOUT size. Sizer will determine it.
                    bracket_orders_list = self.buy_bracket(
                        data=d_obj,
                        # size= REMOVED - Sizer will handle this
                        price=main_order_limit_price, 
                        exectype=bt.Order.Limit, 
                        stopprice=stop_loss_price_calc,
                        limitprice=tp_price_for_bracket,
                    )

                    if bracket_orders_list and bracket_orders_list[0]:
                        self.orders[d_name] = bracket_orders_list[0] 
                        self.position_types[d_name] = potential_position_type
                    else:
                        self.log(f'Failed to create buy_bracket order for {d_name} (possibly sizer returned 0 or error)', data=d_obj)
                        
# ===================================================================================
# Main Program Entry Point
# ===================================================================================
if __name__ == '__main__':
    optimize = True
    # optimize = False
    initial_cash = 500000.0
    commission_rate = 0.0003
    
    data_folder = r'D:\\BT2025\\datas\\' # Make sure this path is correct
    if not os.path.isdir(data_folder):
        print(f"错误: 数据文件夹路径不存在: {data_folder}")
        sys.exit(1)
        
    data_files = [
        os.path.join(data_folder, '510050_d.xlsx'),
        os.path.join(data_folder, '510300_d.xlsx'),
        os.path.join(data_folder, '159949_d.xlsx') 
    ]
    # ... (rest of data file checks) ...

    column_mapping = {'日期': 'datetime', '开盘': 'open', '最高': 'high', '最低': 'low', '收盘': 'close', '成交量': 'volume'}
    openinterest_col_name = None 
    
    fromdate = datetime.datetime(2015, 1, 1)
    todate = datetime.datetime(2024, 4, 30)

    # Sizer parameters (these were part of strategy params before)
    sizer_params = dict(
        etf_type_param_name='etf_type', # Tells sizer how to find etf_type in strategy
        risk_per_trade_trend=0.01,      # Corresponds to AShareETFStrategy.params.max_risk_per_trade_trend
        risk_per_trade_range=0.005,     # Corresponds to AShareETFStrategy.params.max_risk_per_trade_range
        max_position_per_etf_percent=0.30,
        trend_stop_loss_atr_mult_param_name = 'trend_stop_loss_atr_mult', # Name of param in strategy
        range_stop_loss_buffer_param_name = 'range_stop_loss_buffer' # Name of param in strategy
    )

    # Optimization ranges for strategy params (sizing params are now fixed in sizer_params for this example)
    # If you want to optimize sizer params, you'd optstrategy on the Sizer's params if Backtrader supported it directly,
    # or create different sizer instances/subclasses.
    # For now, we optimize strategy params that influence signals and SL/TP prices for brackets.
    ema_medium_range = range(40, 81, 20) 
    ema_long_range = range(100, 141, 20)
    bbands_period_range = range(15, 26, 5)
    bbands_dev_range = np.arange(1.8, 2.3, 0.2) 
    trend_sl_atr_mult_range = np.arange(2.0, 3.1, 0.5) # Example: optimizing ATR multiplier

    cerebro = bt.Cerebro(stdstats=not optimize, optreturn=False)

    loaded_data_count = load_data_to_cerebro(
        cerebro, data_files, column_mapping, openinterest_col_name, fromdate, todate)

    if loaded_data_count == 0:
        print("\n错误：未能成功加载任何数据文件。无法继续执行。")
        sys.exit(1)

    print(f"\n总共加载了 {loaded_data_count} 个数据源。")

    cerebro.broker.setcash(initial_cash)
    cerebro.broker.setcommission(commission=commission_rate, stocklike=True)

    # Add the custom sizer
    cerebro.addsizer(AShareETFSizer, **sizer_params)

    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe_ratio', 
                        timeframe=bt.TimeFrame.Days, riskfreerate=0.0, annualize=True, factor=252)
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trade_analyzer')

    if optimize:
        print("\n{:-^50}".format(' 参数优化设置 '))
        print(f"  etf_type: ['trend', 'range']") # This is a strategy param
        print(f"  ema_medium_period: {list(ema_medium_range)}")
        print(f"  ema_long_period: {list(ema_long_range)}")
        print(f"  bbands_period: {list(bbands_period_range)}")
        print(f"  bbands_devfactor: {list(np.round(bbands_dev_range, 2))}")
        print(f"  trend_stop_loss_atr_mult: {list(np.round(trend_sl_atr_mult_range,1))}") # Strategy param for bracket SL
        print('-' * 50)

        cerebro.optstrategy(AShareETFStrategy,
                            etf_type=['trend', 'range'], 
                            ema_medium_period=ema_medium_range,
                            ema_long_period=ema_long_range,
                            bbands_period=bbands_period_range,
                            bbands_devfactor=bbands_dev_range,
                            trend_stop_loss_atr_mult=trend_sl_atr_mult_range # Optimizing this strategy param
                            # Note: range_stop_loss_buffer could also be optimized if desired
                           )
        # ... (rest of the optimization execution and result processing logic remains the same)
        print('开始参数优化运行...')
        start_time = time.time()
        results = cerebro.run(maxcpus=max(1, os.cpu_count() -1 if os.cpu_count() else 1) ) 
        end_time = time.time()
        total_time = end_time - start_time
        actual_combinations = len(results) if results else 0
        avg_time_per_run = total_time / actual_combinations if actual_combinations > 0 else 0
        
        print('\n{:=^50}'.format(' 优化完成统计 '))
        print(f"{'总用时':<20}: {total_time:.2f}秒 ({total_time/60:.2f}分钟)")
        print(f"{'实际参数组数':<20}: {actual_combinations}")
        print(f"{'每组平均用时':<20}: {avg_time_per_run:.2f}秒")
        print('=' * 50)

        best_result, all_scored_results = analyze_optimization_results(results)

        if best_result:
            header_format = '{:<10} {:<12} {:<12} {:<12} {:<10} {:<8} {:<12} {:<12} {:<12} {:<12}'
            row_format    = '{:<10} {:<12} {:<12} {:<12.0f} {:<10.1f} {:<8.1f} {:<12.4f} {:<12.2f} {:<12.2f} {:<12.4f}' # Added ATR mult
            
            print('\n{:=^125}'.format(' 参数优化结果 (按得分排序) ')) # Adjusted width
            print(header_format.format('ETF类型', 'EMA中期', 'EMA长期', '布林周期', '布林标差', 'ATR止损', '夏普比率', '收益率(%)', '最大回撤(%)', '得分'))
            print('-' * 125) # Adjusted width

            all_scored_results.sort(key=lambda x: x['score'], reverse=True)
            
            for res_data in all_scored_results[:min(20, len(all_scored_results))]: 
                p_dict = res_data['params_dict'] 
                print(row_format.format(
                    p_dict.get('etf_type', 'N/A'),
                    p_dict.get('ema_medium_period', 0), 
                    p_dict.get('ema_long_period', 0), 
                    p_dict.get('bbands_period', 0), 
                    p_dict.get('bbands_devfactor', 0.0),
                    p_dict.get('trend_stop_loss_atr_mult', 0.0), # Display optimized ATR mult
                    res_data['sharpe'], 
                    res_data['return'] * 100, 
                    res_data['drawdown'] * 100, 
                    res_data['score']
                ))

            print('\n{:=^50}'.format(' 最优参数组合 '))
            best_params_dict = best_result['params_dict']
            print(f"{'ETF类型':<25}: {best_params_dict.get('etf_type', 'N/A')}")
            print(f"{'EMA中期':<25}: {best_params_dict.get('ema_medium_period', 0)}")
            print(f"{'EMA长期':<25}: {best_params_dict.get('ema_long_period', 0)}")
            print(f"{'布林带周期':<25}: {best_params_dict.get('bbands_period', 0)}")
            print(f"{'布林带标准差':<25}: {best_params_dict.get('bbands_devfactor', 0.0):.1f}")
            print(f"{'趋势止损ATR倍数':<25}: {best_params_dict.get('trend_stop_loss_atr_mult', 0.0):.1f}")
            print(f"{'夏普比率':<25}: {best_result['sharpe']:.4f}")
            print(f"{'总收益率':<25}: {best_result['return'] * 100:.2f}%")
            print(f"{'最大回撤':<25}: {best_result['drawdown'] * 100:.2f}%")
            print(f"{'得分':<25}: {best_result['score']:.4f}")
            print('=' * 50)
        else:
            print("\n错误：未能确定最优策略或处理结果时出错。")


    else: # Single Run
        # ... (single run logic remains the same, just ensure AShareETFSizer is added)
        print("\n{:-^50}".format(' 单次回测设置 '))
        print(f"优化开关: 关闭")
        print(f"Observer 图表: 开启")
        # Print Sizer parameters for single run
        print("\nSizer 参数:")
        for k, v in sizer_params.items():
            print(f"  {k}: {v}")
        print('-' * 50)

        cerebro.addstrategy(AShareETFStrategy, etf_type='trend') 

        print('开始单次回测运行...')
        print('期初总资金: %.2f' % cerebro.broker.getvalue())
        start_time = time.time()
        results = cerebro.run() 
        end_time = time.time()
        final_value = cerebro.broker.getvalue()
        print('期末总资金: %.2f' % final_value)
        print('回测总用时: {:.2f}秒'.format(end_time - start_time))
        print(f"总收益率: {(final_value / initial_cash - 1) * 100:.2f}%")

        print("\n{:-^50}".format(' 单次回测分析结果 '))
        if results and results[0]:
            strat_instance = results[0]
            for analyzer_name, analyzer_obj in strat_instance.analyzers.getitems():
                analysis = analyzer_obj.get_analysis()
                print(f"\n--- {analyzer_name} ---")
                if isinstance(analysis, dict):
                    for k, v in analysis.items():
                        if isinstance(v, dict): 
                            print(f"  {k}:")
                            for sub_k, sub_v in v.items():
                                print(f"    {sub_k}: {sub_v}")
                        else:
                             print(f"  {k}: {v}")
                else:
                    print(analysis)
        print('-' * 50)
        
        if not optimize: 
            try:
                print("\n尝试绘制图表...")
                plot_filename = 'backtest_plot_sizers.png'
                # Plotting the first data, assuming multiple datas might be too cluttered
                # If plotting specific data is needed, adjust data_to_plot
                data_to_plot = cerebro.datas[0]._name if cerebro.datas else None
                if data_to_plot:
                    cerebro.plot(style='candlestick', barup='red', bardown='green', 
                                 iplot=False, volume=True, savefig=True, figfilename=plot_filename,
                                 plotdatanames=[data_to_plot])
                    print(f"图表已保存到 {plot_filename}")
                else:
                    print("没有数据可供绘制。")
            except Exception as e:
                print(f"\n绘制图表时出错: {e}")
                print("请确保已安装matplotlib且图形环境配置正确。")