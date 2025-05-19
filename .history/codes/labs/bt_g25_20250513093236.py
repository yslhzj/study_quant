import backtrader as bt
import math

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
                        
