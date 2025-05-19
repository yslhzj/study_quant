#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import datetime
import math
import pandas as pd
import os
import sys
import numpy as np
import time

import backtrader as bt

# ===================================================================================
# Custom Sizer
# ===================================================================================
class AShareETFSizer(bt.Sizer):
    params = (
        ('etf_type_param_name', 'etf_type'), 
        ('risk_per_trade_trend', 0.01), 
        ('risk_per_trade_range', 0.005), 
        ('max_position_per_etf_percent', 0.30),
        ('trend_stop_loss_atr_mult_param_name', 'trend_stop_loss_atr_mult'),
        ('range_stop_loss_buffer_param_name', 'range_stop_loss_buffer'),
    )

    def _getsizing(self, comminfo, cash, data, isbuy):
        if not isbuy: # This sizer is designed for long entries as per strategy logic
            return 0

        position = self.broker.getposition(data)
        if position.size != 0: # Already in market for this data
             # self.strategy.log(f"Sizer: Already in position for {data._name}. No new entry size.", data=data)
            return 0 

        d_name = data._name
        strategy = self.strategy 

        current_etf_type = getattr(strategy.params, self.p.etf_type_param_name, 'trend')
        
        entry_price_ref = data.close[0] # Reference for SL calculation (current close)
        # Actual entry for bracket order will be this price as a limit.

        if current_etf_type == 'trend':
            risk_per_trade_percent = self.p.risk_per_trade_trend
            atr_mult_param_name = self.p.trend_stop_loss_atr_mult_param_name
            atr_mult = getattr(strategy.params, atr_mult_param_name)
            
            if not hasattr(strategy, 'atrs') or d_name not in strategy.atrs:
                strategy.log(f"Sizer: ATR indicator for {d_name} not found in strategy.atrs. Skipping trade.", data=data)
                return 0
            current_atr = strategy.atrs[d_name][0]
            if math.isnan(current_atr) or current_atr <= 1e-9:
                strategy.log(f"Sizer: Invalid ATR value ({current_atr:.2f}) for {d_name}. Skipping trade.", data=data)
                return 0
            stop_loss_price_ref = entry_price_ref - atr_mult * current_atr
        
        elif current_etf_type == 'range':
            risk_per_trade_percent = self.p.risk_per_trade_range
            sl_buffer_param_name = self.p.range_stop_loss_buffer_param_name
            sl_buffer = getattr(strategy.params, sl_buffer_param_name)

            if not hasattr(strategy, 'lows') or d_name not in strategy.lows:
                strategy.log(f"Sizer: Low price series for {d_name} not found in strategy.lows. Skipping trade.", data=data)
                return 0
            # For range, SL reference is based on current low (consistent with strategy's bracket SL price)
            stop_loss_price_ref = strategy.lows[d_name][0] * (1 - sl_buffer)
        else:
            strategy.log(f"Sizer: Unknown ETF type '{current_etf_type}' for {d_name}. Skipping trade.", data=data)
            return 0

        if stop_loss_price_ref >= entry_price_ref:
            strategy.log(
                f"Sizer: Stop loss ref {stop_loss_price_ref:.2f} not below entry ref {entry_price_ref:.2f} for {d_name}. Cannot size.", data=data)
            return 0

        risk_per_share = entry_price_ref - stop_loss_price_ref
        if risk_per_share <= 1e-9:
            strategy.log(
                f"Sizer: Risk per share for {d_name} is zero or too small ({risk_per_share:.2f}). Cannot size.", data=data)
            return 0

        effective_risk_percent = risk_per_trade_percent * strategy.current_risk_multiplier
        equity = self.broker.getvalue()
        
        max_amount_to_risk_on_this_trade = equity * effective_risk_percent
        
        size_raw = max_amount_to_risk_on_this_trade / risk_per_share
        size = int(size_raw / 100) * 100 

        if size <= 0:
            # strategy.log(
            #     f"Sizer: Calculated size for {d_name} based on risk is {size}. Risk/share: {risk_per_share:.2f}. Amount to risk: {max_amount_to_risk_on_this_trade:.2f}", data=data)
            return 0

        max_pos_value_for_etf = equity * self.p.max_position_per_etf_percent
        price_for_value_calc = entry_price_ref
        
        if price_for_value_calc <= 1e-9:
            strategy.log(
                f"Sizer: Invalid price ({price_for_value_calc:.2f}) for {d_name} value calculation.", data=data)
            return 0
            
        size_limited_by_max_etf_pos = int(max_pos_value_for_etf / price_for_value_calc / 100) * 100
        if size > size_limited_by_max_etf_pos:
            # strategy.log(
            #     f"Sizer: Size for {d_name} reduced from {size} to {size_limited_by_max_etf_pos} by max_position_per_etf_percent.", data=data)
            size = size_limited_by_max_etf_pos

        if size <= 0:
            # strategy.log(
            #     f"Sizer: Calculated size for {d_name} after max ETF position limit is {size}.", data=data)
            return 0

        potential_trade_total_cost = size * price_for_value_calc
        if potential_trade_total_cost > cash:
            size_limited_by_cash = int(cash / price_for_value_calc / 100) * 100
            if size_limited_by_cash < size:
                # strategy.log(
                #     f"Sizer: Size for {d_name} reduced from {size} to {size_limited_by_cash} by cash limit. Cash: {cash:.2f}, Cost approx: {potential_trade_total_cost:.2f}", data=data)
                size = size_limited_by_cash
        
        if size <= 0:
            # strategy.log(
            #     f"Sizer: Final calculated size for {d_name} is {size}. Cannot place order.", data=data)
            return 0
        
        # strategy.log(f"Sizer for {d_name} calculated size: {size} (Entry Ref: {entry_price_ref:.2f}, SL Ref: {stop_loss_price_ref:.2f}, Risk/Share: {risk_per_share:.2f})", data=data)
        return size

# ===================================================================================
# Strategy Definition
# ===================================================================================
class AShareETFStrategy(bt.Strategy):
    params = (
        ('etf_type', 'trend'), 
        ('ema_medium_period', 60),
        ('ema_long_period', 120),
        ('adx_period', 14),
        ('atr_period', 20), 
        ('bbands_period', 20),
        ('bbands_devfactor', 2.0),
        ('rsi_period', 14),
        ('rsi_oversold', 30),
        ('trend_breakout_lookback', 60),
        ('trend_volume_avg_period', 20),
        ('trend_volume_ratio_min', 1.1),
        ('trend_stop_loss_atr_mult', 2.5), # Used for bracket SL price
        ('trend_take_profit_rratio', 2.0), # Used for bracket TP price
        ('range_stop_loss_buffer', 0.005), # Used for bracket SL price
        ('max_total_account_risk_percent', 0.06), 
        ('drawdown_level1_threshold', 0.05),
        ('drawdown_level2_threshold', 0.10),
    )

    def log(self, txt, dt=None, data=None):
        # return # Uncomment to disable logging
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
        self.closes = {d._name: d.close for d in self.datas}
        self.opens = {d._name: d.open for d in self.datas}
        self.highs = {d._name: d.high for d in self.datas}
        self.lows = {d._name: d.low for d in self.datas}
        self.volumes = {d._name: d.volume for d in self.datas}

        self.emas_medium = {d._name: bt.indicators.EMA(d.close, period=self.params.ema_medium_period) for d in self.datas}
        self.emas_long = {d._name: bt.indicators.EMA(d.close, period=self.params.ema_long_period) for d in self.datas}
        self.adxs = {d._name: bt.indicators.ADX(d, period=self.params.adx_period) for d in self.datas}
        self.atrs = {d._name: bt.indicators.ATR(d, period=self.params.atr_period) for d in self.datas}
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
        self.current_risk_multiplier = 1.0

    def notify_order(self, order):
        order_data_name = order.data._name if hasattr(order.data, '_name') else 'Unknown_Data'

        if order.status in [order.Submitted, order.Accepted]:
            # self.log(f'Order {order.ref} Submitted/Accepted for {order_data_name}', data=order.data)
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
                f'Order {order.ref} for {order_data_name} {order.getstatusname()}', data=order.data)

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

    def next(self):
        if self.halt_trading:
            for d_obj in self.datas:
                d_name = d_obj._name
                position = self.getposition(d_obj)
                order = self.orders.get(d_name)
                if position.size != 0 and not order:
                    # self.log(
                    #     f'HALTED: Attempting to close position for {d_name} Size: {position.size}', data=d_obj)
                    order_close = self.close(data=d_obj)
                    if order_close:
                        self.orders[d_name] = order_close
                    # else:
                        # self.log(
                        #     f'HALTED: Failed to create close order for {d_name}', data=d_obj)
            return

        for i, d_obj in enumerate(self.datas):
            d_name = d_obj._name
            position = self.getposition(d_obj)
            order = self.orders.get(d_name)

            if order:
                continue
            
            if position.size == 0: 
                market_state = 'UNCERTAIN_DO_NOT_TRADE'
                current_close = self.closes[d_name][0]
                current_open = self.opens[d_name][0]
                current_low = self.lows[d_name][0]
                current_volume = self.volumes[d_name][0]
                
                # Ensure enough data for all indicators before accessing them
                min_lookback = max(self.p.ema_medium_period, self.p.ema_long_period, 
                                   self.p.adx_period, self.p.bbands_period, 
                                   self.p.rsi_period, self.p.trend_breakout_lookback,
                                   self.p.trend_volume_avg_period, self.p.atr_period)
                if len(d_obj) < min_lookback +1 : # +1 for current bar access
                    continue

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
                elif is_range_confirmed and self.p.etf_type == 'range':
                    market_state = 'RANGE_CONFIRMED'

                entry_signal = False
                potential_position_type = None
                limit_entry_price_calc = current_close 
                
                stop_loss_price_calc = None
                take_profit_price_calc = None
                
                if market_state == 'TREND_UP' and self.p.etf_type == 'trend':
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
                            else: entry_signal = False
                        else: entry_signal = False

                elif market_state == 'RANGE_CONFIRMED' and self.p.etf_type == 'range':
                    is_range_buy = (current_low <= bb_bot and
                                    current_close > bb_bot and 
                                    rsi_val < self.params.rsi_oversold)
                    if is_range_buy:
                        entry_signal = True
                        potential_position_type = 'range'
                        stop_loss_price_calc = current_low * (1 - self.p.range_stop_loss_buffer)
                        take_profit_price_calc = bb_mid
                        if stop_loss_price_calc >= limit_entry_price_calc: entry_signal = False
                
                if entry_signal and stop_loss_price_calc is not None and limit_entry_price_calc > stop_loss_price_calc:
                    # Size is determined by the sizer.
                    # We still need to provide the prices for the bracket legs.
                    main_order_limit_price = limit_entry_price_calc 
                    
                    tp_price_for_bracket = take_profit_price_calc if take_profit_price_calc and take_profit_price_calc > main_order_limit_price else None
                    
                    if tp_price_for_bracket is None and potential_position_type == 'trend' and take_profit_price_calc is not None:
                         self.log(f'Warning for {d_name}: TP price for trend trade ({take_profit_price_calc:.2f}) is not above entry limit ({main_order_limit_price:.2f}). Bracket will not have a limit sell.', data=d_obj)


                    # self.log(
                    #     f'Attempting BUY SIGNAL (Bracket): {d_name}, Proposed Limit Entry: {main_order_limit_price:.2f}, SL for bracket: {stop_loss_price_calc:.2f}, TP for bracket: {tp_price_for_bracket if tp_price_for_bracket else "N/A"}, Type: {potential_position_type}', data=d_obj)

                    bracket_orders_list = self.buy_bracket(
                        data=d_obj,
                        # size=  Let sizer handle this
                        price=main_order_limit_price, 
                        exectype=bt.Order.Limit, 
                        stopprice=stop_loss_price_calc,
                        limitprice=tp_price_for_bracket, 
                    )

                    if bracket_orders_list and bracket_orders_list[0]:
                        self.orders[d_name] = bracket_orders_list[0] 
                        self.position_types[d_name] = potential_position_type
                    # else: # Sizer might return 0, or order creation failed for other reasons
                        # self.log(f'Buy_bracket order for {d_name} not created (possibly sizer returned 0 or other issue).', data=d_obj)


# ===================================================================================
# Data Loading Function
# ===================================================================================
def load_data_to_cerebro(cerebro, data_files, column_mapping, openinterest_col_name, fromdate, todate):
    print("开始加载数据...")
    loaded_data_count = 0
    for file_path in data_files:
        try:
            dataframe = pd.read_excel(file_path)
            dataframe.rename(columns=column_mapping, inplace=True)
            
            if 'datetime' in dataframe.columns:
                try:
                    dataframe['datetime'] = pd.to_datetime(dataframe['datetime'])
                except Exception as e:
                    print(f"警告: 无法解析 {file_path} 中的日期时间列，请检查格式。错误: {e}")
                    continue
            else:
                print(f"错误: 在 {file_path} 中找不到映射后的 'datetime' 列。请确保Excel文件中有'日期'列，或正确修改脚本中的column_mapping。")
                continue
            
            dataframe.set_index('datetime', inplace=True)
            required_cols = ['open', 'high', 'low', 'close', 'volume']
            missing_cols = [col for col in required_cols if col not in dataframe.columns]
            if missing_cols:
                print(f"错误: {file_path} 映射后缺少必需的列: {missing_cols}.")
                print(f"可用列: {dataframe.columns.tolist()}")
                continue
            
            for col in required_cols:
                dataframe[col] = pd.to_numeric(dataframe[col], errors='coerce')
            dataframe.dropna(subset=required_cols, inplace=True)

            dataframe = dataframe.loc[fromdate:todate]

            if dataframe.empty:
                print(f"警告: {file_path} 在指定日期范围内没有数据或数据无效。")
                continue

            oi_feed_name = openinterest_col_name if openinterest_col_name and openinterest_col_name in dataframe.columns else None

            data = bt.feeds.PandasData(dataname=dataframe,
                                       fromdate=fromdate, todate=todate,
                                       datetime=None, 
                                       open='open', high='high', low='low', close='close', volume='volume',
                                       openinterest=oi_feed_name) 
            
            data_name = os.path.basename(file_path).split('.')[0]
            cerebro.adddata(data, name=data_name)
            print(f"数据加载成功: {data_name} (从 {dataframe.index.min().date()} 到 {dataframe.index.max().date()})")
            loaded_data_count += 1

        except FileNotFoundError:
            print(f"错误: 文件未找到 {file_path}")
        except Exception as e:
            print(f"加载数据 {file_path} 时出错: {e}")
    return loaded_data_count

# ===================================================================================
# Result Processing and Scoring Function
# ===================================================================================
def analyze_optimization_results(results):
    if not results:
        print("\n{:!^50}".format(' 错误 '))
        print("没有策略成功运行。请检查数据加载是否有误或参数范围是否有效。")
        print('!' * 50)
        return None, []

    processed_results = []
    print("\n--- 开始提取分析结果 ---")
    for strat_list in results: 
        if not strat_list:
            continue
        strategy_instance = strat_list[0]
        params = strategy_instance.params 
        analyzers = strategy_instance.analyzers

        try:
            sharpe_analysis = analyzers.sharpe_ratio.get_analysis()
            returns_analysis = analyzers.returns.get_analysis()
            drawdown_analysis = analyzers.drawdown.get_analysis()
            
            if not isinstance(sharpe_analysis, dict) or 'sharperatio' not in sharpe_analysis:
                continue
            if not isinstance(returns_analysis, dict) or 'rtot' not in returns_analysis:
                continue
            if not isinstance(drawdown_analysis, dict) or 'max' not in drawdown_analysis or not isinstance(drawdown_analysis['max'], dict) or 'drawdown' not in drawdown_analysis['max']:
                continue

            sharpe = sharpe_analysis.get('sharperatio') 
            if sharpe is None: sharpe = -float('inf') # Penalize missing Sharpe heavily
            total_return = returns_analysis.get('rtot', -float('inf')) # Penalize missing return
            max_drawdown_percent = drawdown_analysis['max'].get('drawdown', 100.0) # Default to 100% DD if missing
            max_drawdown = max_drawdown_percent / 100.0 

            processed_results.append({
                'instance': strategy_instance,
                'params_dict': dict(params.items()),
                'sharpe': sharpe,
                'return': total_return,
                'drawdown': max_drawdown
            })

        except AttributeError as e:
            params_dict_str = dict(params.items()) if hasattr(params, 'items') else "N/A"
        except Exception as e:
            params_dict_str = dict(params.items()) if hasattr(params, 'items') else "N/A"
            print(f"错误: 处理参数组 {params_dict_str} 时出错: {e}")

    print(f"--- 成功提取 {len(processed_results)} 组分析结果 ---")

    if not processed_results:
        print("\n错误：未能成功提取任何有效的分析结果。无法进行评分。")
        return None, []

    all_sharpes = [r['sharpe'] for r in processed_results if r['sharpe'] != -float('inf')]
    all_returns = [r['return'] for r in processed_results if r['return'] != -float('inf')]
    all_drawdowns = [r['drawdown'] for r in processed_results if r['drawdown'] != 1.0]


    min_sharpe = min(all_sharpes) if all_sharpes else 0.0
    max_sharpe = max(all_sharpes) if all_sharpes else 0.0
    min_return = min(all_returns) if all_returns else 0.0
    max_return = max(all_returns) if all_returns else 0.0
    min_drawdown = min(all_drawdowns) if all_drawdowns else 0.0
    max_drawdown_val = max(all_drawdowns) if all_drawdowns else 1.0 # max_drawdown is actually the highest DD value

    best_score = float('-inf')
    best_result_data = None
    scored_results = []

    # print("\n--- 开始计算归一化得分 ---")
    # if all_sharpes:
    #     print(f"Min/Max - Sharpe: ({min_sharpe:.4f}, {max_sharpe:.4f}), Return: ({min_return:.4f}, {max_return:.4f}), Drawdown: ({min_drawdown:.4f}, {max_drawdown_val:.4f})")

    for result_data in processed_results:
        sharpe = result_data['sharpe']
        ret = result_data['return']
        dd = result_data['drawdown']

        # Handle cases where metric might be default due to issues
        if sharpe == -float('inf') or ret == -float('inf') or dd == 1.0 and not all_drawdowns : # if dd is 1.0 and it's the only value (or all are 1.0)
            result_data['score'] = -float('inf') # Heavily penalize problematic runs
            scored_results.append(result_data)
            continue

        sharpe_range = max_sharpe - min_sharpe
        return_range = max_return - min_return
        # For drawdown, a smaller range is better if all are high, but normalization still works
        drawdown_range = max_drawdown_val - min_drawdown 
        
        sharpe_norm = (sharpe - min_sharpe) / sharpe_range if sharpe_range > 1e-9 else (0.5 if abs(max_sharpe - min_sharpe) < 1e-9 and len(all_sharpes)>0 else 0.0)
        return_norm = (ret - min_return) / return_range if return_range > 1e-9 else (0.5 if abs(max_return - min_return) < 1e-9 and len(all_returns)>0 else 0.0)
        # Normalize drawdown so that higher value (worse drawdown) gets lower score contribution
        # (dd - min_drawdown) means smaller dd gets smaller norm value. We want smaller dd to be better.
        # So, 1 - normalized_dd or (max_drawdown_val - dd) / range
        if drawdown_range > 1e-9:
            drawdown_norm = (max_drawdown_val - dd) / drawdown_range # Inverted: higher is better (less drawdown)
        else: # all drawdowns are the same
            drawdown_norm = 0.5 if abs(max_drawdown_val - min_drawdown) < 1e-9 and len(all_drawdowns) > 0 else 0.0
        
        # Score: Higher sharpe, higher return, and higher drawdown_norm (lower actual drawdown) are better.
        score = 0.5 * sharpe_norm + 0.3 * return_norm + 0.2 * drawdown_norm 
        result_data['score'] = score
        scored_results.append(result_data)

        if score > best_score:
            best_score = score
            best_result_data = result_data
            
    # print(f"--- 完成 {len(scored_results)} 组得分计算 ---")
    return best_result_data, scored_results

# ===================================================================================
# Main Program Entry Point
# ===================================================================================
if __name__ == '__main__':
    optimize = True
    # optimize = False 
    initial_cash = 500000.0
    commission_rate = 0.0003
    
    data_folder = r'D:\\BT2025\\datas\\' 
    if not os.path.isdir(data_folder):
        print(f"错误: 数据文件夹路径不存在: {data_folder}")
        sys.exit(1)
        
    data_files = [
        os.path.join(data_folder, '510050_d.xlsx'),
        os.path.join(data_folder, '510300_d.xlsx'),
        os.path.join(data_folder, '159949_d.xlsx') 
    ]
    
    # Check if data files exist before proceeding
    actual_data_files = []
    for f_path in data_files:
        if not os.path.isfile(f_path):
            print(f"警告: 数据文件不存在，将跳过: {f_path}")
        else:
            actual_data_files.append(f_path)
    
    if not actual_data_files:
        print("错误: 没有可用的数据文件。请检查 'data_files' 列表和路径。")
        sys.exit(1)
    data_files = actual_data_files # Use only existing files

    column_mapping = {'date': 'datetime', '开盘': 'open',
                      '最高': 'high', '最低': 'low', '收盘': 'close', '成交量': 'volume'}
    openinterest_col_name = None 
    
    fromdate = datetime.datetime(2015, 1, 1)
    todate = datetime.datetime(2024, 4, 30)

    # Sizer parameters - these are fixed for the sizer instance
    sizer_params = dict(
        etf_type_param_name='etf_type', 
        risk_per_trade_trend=0.01,
        risk_per_trade_range=0.005,
        max_position_per_etf_percent=0.30,
        trend_stop_loss_atr_mult_param_name='trend_stop_loss_atr_mult',
        range_stop_loss_buffer_param_name='range_stop_loss_buffer'
    )

    # Parameters for strategy optimization
    # These are params of AShareETFStrategy
    opt_params_strategy = dict(
        etf_type=['trend', 'range'],
        ema_medium_period=range(40, 81, 20),
        ema_long_period=range(100, 141, 20),
        bbands_period=range(15, 26, 5),
        bbands_devfactor=np.arange(1.8, 2.3, 0.2),
        trend_stop_loss_atr_mult=np.arange(2.0, 3.1, 0.5),
        range_stop_loss_buffer=[0.003, 0.005, 0.007] # Example for range SL buffer
        # Other strategy params like atr_period, rsi_period etc., are kept default for this opto run
    )


    cerebro = bt.Cerebro(stdstats=not optimize, optreturn=False)

    loaded_data_count = load_data_to_cerebro(
        cerebro, data_files, column_mapping, openinterest_col_name, fromdate, todate)

    if loaded_data_count == 0:
        print("\n错误：未能成功加载任何数据文件。无法继续执行。")
        sys.exit(1)

    print(f"\n总共加载了 {loaded_data_count} 个数据源。")

    cerebro.broker.setcash(initial_cash)
    cerebro.broker.setcommission(commission=commission_rate, stocklike=True)

    # Add the custom sizer with its fixed parameters
    cerebro.addsizer(AShareETFSizer, **sizer_params)

    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe_ratio', 
                        timeframe=bt.TimeFrame.Days, riskfreerate=0.0, annualize=True, factor=252)
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trade_analyzer')

    if optimize:
        print("\n{:-^70}".format(' 参数优化设置 '))
        print(f"优化开关: 开启")
        print(f"Sizer参数 (固定):")
        for k,v in sizer_params.items():
            print(f"  {k}: {v}")
        print(f"策略优化参数范围:")
        for k,v in opt_params_strategy.items():
            print(f"  {k}: {list(v) if isinstance(v, (range, np.ndarray)) else v}")
        print('-' * 70)

        cerebro.optstrategy(AShareETFStrategy, **opt_params_strategy)

        print('开始参数优化运行...')
        start_time = time.time()
        results = cerebro.run(maxcpus=max(1, os.cpu_count() -1 if os.cpu_count() and os.cpu_count() > 1 else 1) )
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

        if best_result and all_scored_results:
            # Increased width for better display, include more params
            header_format = '{:<10} {:<8} {:<8} {:<8} {:<8} {:<8} {:<8} {:<10} {:<10} {:<10} {:<10}'
            row_format    = '{:<10} {:<8} {:<8} {:<8.0f} {:<8.1f} {:<8.1f} {:<8.3f} {:<10.4f} {:<10.2f} {:<10.2f} {:<10.4f}'
            
            print('\n{:=^120}'.format(' 参数优化结果 (按得分排序前20) '))
            print(header_format.format('ETF类型', 'EMA中', 'EMA长', 'BB周期', 'BB标差', '趋势ATR止损', '震荡SL缓冲', '夏普', '收益率%', '最大回撤%', '得分'))
            print('-' * 120)

            all_scored_results.sort(key=lambda x: x['score'], reverse=True)
            
            for res_data in all_scored_results[:min(20, len(all_scored_results))]: 
                p_dict = res_data['params_dict'] 
                print(row_format.format(
                    p_dict.get('etf_type', 'N/A'),
                    p_dict.get('ema_medium_period', 0), 
                    p_dict.get('ema_long_period', 0), 
                    p_dict.get('bbands_period', 0), 
                    p_dict.get('bbands_devfactor', 0.0),
                    p_dict.get('trend_stop_loss_atr_mult', 0.0),
                    p_dict.get('range_stop_loss_buffer', 0.0),
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
            print(f"{'震荡止损缓冲':<25}: {best_params_dict.get('range_stop_loss_buffer', 0.0):.3f}")
            print(f"{'夏普比率':<25}: {best_result['sharpe']:.4f}")
            print(f"{'总收益率':<25}: {best_result['return'] * 100:.2f}%")
            print(f"{'最大回撤':<25}: {best_result['drawdown'] * 100:.2f}%")
            print(f"{'得分':<25}: {best_result['score']:.4f}")
            print('=' * 50)
        else:
            print("\n错误：未能确定最优策略或处理结果时出错。请检查日志输出是否有关于分析器结果不完整的警告。")

    else: # Single Run
        print("\n{:-^50}".format(' 单次回测设置 '))
        print(f"优化开关: 关闭")
        print(f"Observer 图表: 开启")
        print("\nSizer 参数 (固定):")
        for k,v in sizer_params.items():
            print(f"  {k}: {v}")
        # Strategy params for single run (can be adjusted here)
        single_run_strat_params = {
            'etf_type': 'trend',
            'ema_medium_period': 60,
            'ema_long_period': 120,
            'bbands_period': 20,
            'bbands_devfactor': 2.0,
            'trend_stop_loss_atr_mult': 2.5,
            'range_stop_loss_buffer': 0.005
        }
        print("\n策略参数 (单次运行):")
        for k,v in single_run_strat_params.items():
            print(f"  {k}: {v}")
        print('-' * 50)


        cerebro.addstrategy(AShareETFStrategy, **single_run_strat_params) 

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
                try:
                    analysis = analyzer_obj.get_analysis()
                    print(f"\n--- {analyzer_name} ---")
                    if isinstance(analysis, dict):
                        for k, v in analysis.items():
                            if isinstance(v, dict): 
                                print(f"  {k}:")
                                for sub_k, sub_v in v.items():
                                    print(f"    {sub_k}: {sub_v}")
                            elif isinstance(v, (float, np.float64)):
                                 print(f"  {k}: {v:.4f}")
                            else:
                                 print(f"  {k}: {v}")
                    else:
                        print(analysis)
                except Exception as e:
                    print(f"获取分析器 '{analyzer_name}' 结果时出错: {e}")
        print('-' * 50)
        
        if not optimize: 
            try:
                print("\n尝试绘制图表...")
                plot_filename = 'backtest_plot_sizers.png'
                # Plotting only the first data source to avoid clutter if multiple are loaded
                data_to_plot_name = cerebro.datas[0]._name if cerebro.datas else None
                if data_to_plot_name:
                    cerebro.plot(style='candlestick', barup='red', bardown='green', 
                                 iplot=False, volume=True, savefig=True, figfilename=plot_filename,
                                 # plotdatanames=[data_to_plot_name] # This might cause issues if only one data is plotted by default
                                 )
                    print(f"图表已保存到 {plot_filename}")
                else:
                    print("没有数据可供绘制。")

            except Exception as e:
                print(f"\n绘制图表时出错: {e}")
                print("请确保已安装matplotlib且图形环境配置正确。")