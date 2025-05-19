#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-

import backtrader as bt
# 导入 backtrader 库，并将其简写为 bt，方便后续调用。
# (就像给一个很长的名字取个小名，方便叫唤。)
import datetime
# 导入 datetime 库，用于处理日期和时间。
# (就像导入一个日历和时钟工具。)
import math
# 导入 math 库，用于进行数学计算，例如开方、取整等。
# (就像导入一个计算器。)
import pandas as pd
import os
import sys
import numpy as np
import matplotlib.pyplot as plt

import warnings


class AShareETFStrategy(bt.Strategy):
    # 定义一个名为 AShareETFStrategy 的策略类，它继承自 backtrader 的 Strategy 类。
    # (就像创建一个新的游戏角色，这个角色天生就具备一些基础的交易能力。)
    params = (
        # 定义策略的参数，这些参数可以在之后调整以优化策略表现。
        # (就像给游戏角色设定初始属性，比如力量、敏捷度，这些属性可以调整。)
        ('etf_type', 'trend'),
        # 定义ETF类型参数，'trend'表示趋势型，'range'表示震荡型。
        # (设定这个ETF适合玩"追涨杀跌"还是"高抛低吸"。)
        ('ema_medium_period', 60),
        # 定义中期指数移动平均线（EMA）的计算周期为60天。
        # (设定一个观察最近60天平均价格的指标。)
        ('ema_long_period', 120),
        # 定义长期指数移动平均线（EMA）的计算周期为120天。
        # (设定一个观察最近120天平均价格的指标，比上面的看得更长远。)
        ('adx_period', 14),
        # 定义平均动向指数（ADX）的计算周期为14天。
        # (设定一个观察最近14天趋势强弱的指标。)
        ('atr_period', 20),
        # 定义平均真实波幅（ATR）的计算周期为20天。
        # (设定一个观察最近20天价格波动幅度的指标。)
        ('bbands_period', 20),
        # 定义布林带（Bollinger Bands）的计算周期为20天。
        # (设定一个观察最近20天价格通道的指标。)
        ('bbands_devfactor', 2.0),
        # 定义布林带的标准差倍数为2.0。
        # (设定布林带通道的宽度，数值越大通道越宽。)
        ('rsi_period', 14),
        # 定义相对强弱指数（RSI）的计算周期为14天。
        # (设定一个观察最近14天买卖力量对比的指标。)
        ('rsi_oversold', 30),
        # 定义RSI指标的超卖阈值为30。
        # (设定一个标准，低于30就认为可能卖得太多，价格可能反弹。)
        ('trend_breakout_lookback', 60),
        # 定义趋势突破策略回顾期为60天，用于寻找近期高点。
        # (设定在趋势策略中，要看过去60天内的最高价。)
        ('trend_volume_avg_period', 20),
        # 定义趋势策略中计算平均成交量的周期为20天。
        # (设定在趋势策略中，要看过去20天的平均交易量。)
        ('trend_volume_ratio_min', 1.1),
        # 定义趋势突破时成交量需要达到的最小倍数（相对于平均成交量）。
        # (设定突破时，交易量至少要放大到平均值的1.1倍才算数。)
        ('trend_stop_loss_atr_mult', 2.5),
        # 定义趋势策略中止损计算使用的ATR倍数。
        # (设定在趋势交易中，亏损多少（用ATR衡量）就得认赔出局。)
        ('trend_take_profit_rratio', 2.0),
        # 定义趋势策略中的盈亏比目标。
        # (设定在趋势交易中，期望赚的钱至少是亏损风险的2倍。)
        ('range_stop_loss_buffer', 0.005),
        # 定义震荡策略中止损设置在K线最低点下方的缓冲比例。
        # (设定在震荡交易中，止损线比最低价再低一点点，留个缓冲空间。)
        ('max_risk_per_trade_trend', 0.01),
        # 定义趋势策略下单笔交易允许的最大风险占总资金的比例（1%）。
        # (设定每次趋势交易最多只允许亏掉总资金的1%。)
        ('max_risk_per_trade_range', 0.005),
        # 定义震荡策略下单笔交易允许的最大风险占总资金的比例（0.5%）。
        # (设定每次震荡交易最多只允许亏掉总资金的0.5%。)
        ('max_position_per_etf_percent', 0.30),
        # 定义单个ETF允许持有的最大仓位占总资金的比例（30%）。
        # (设定单个ETF最多只能买总资金的30%。)
        ('max_total_account_risk_percent', 0.06),
        # 定义整个账户允许承担的总风险上限比例（6%）（简化版，仅考虑当前ETF）。
        # (设定整个账户最多能承受总资金6%的潜在亏损。)
        ('drawdown_level1_threshold', 0.05),
        # 定义一级回撤阈值（5%），触发时可能降低风险。
        # (设定当账户亏损达到总资金的5%时，发出黄色警报，可能要小心点。)
        ('drawdown_level2_threshold', 0.10),
        # 定义二级回撤阈值（10%），触发时可能暂停交易。
        # (设定当账户亏损达到总资金的10%时，发出红色警报，可能要停止交易。)
    )

    def log(self, txt, dt=None, data=None):
        return
        # 定义一个日志记录函数，用于在控制台输出策略执行信息。
        # (就像写日记，记录下策略在做什么。)
        # 如果未提供数据对象，则尝试使用第一个数据源的日期
        _data = data if data is not None else (
            self.datas[0] if self.datas else None)
        if _data:
            dt = dt or _data.datetime.date(0)
            # 获取当前数据点的时间戳，如果没有提供dt参数，则使用指定数据或第一个数据的日期。
            # (确定这条日记是哪一天写的。)
            # 添加数据名称前缀
            prefix = f"[{_data._name}] " if hasattr(_data, '_name') else ""
            print(f"{dt.isoformat()} {prefix}{txt}")
            # 格式化输出日期、数据名称前缀和日志文本。
            # (把日期、哪个数据源、和内容打印出来，格式是"YYYY-MM-DD [数据名] 内容"。)
        else:
            # 如果没有数据对象，只打印文本
            print(txt)

    def __init__(self):
        print(f"初始化策略，参数: {self.params}")  # 添加初始化日志
        # Store lines and indicators per data feed
        self.closes = [d.close for d in self.datas]
        self.opens = [d.open for d in self.datas]
        self.highs = [d.high for d in self.datas]
        self.lows = [d.low for d in self.datas]
        self.volumes = [d.volume for d in self.datas]

        # Initialize indicator lists/dicts
        self.emas_medium = []
        self.emas_long = []
        self.adxs = []
        self.atrs = []
        self.bbands = []
        self.rsis = []
        self.highest_highs = []
        self.sma_volumes = []

        # Create indicators for each data feed
        print("开始创建技术指标...")  # 添加指标创建日志
        for i, d in enumerate(self.datas):
            self.emas_medium.append(bt.indicators.EMA(
                self.closes[i], period=self.params.ema_medium_period))
            self.emas_long.append(bt.indicators.EMA(
                self.closes[i], period=self.params.ema_long_period))
            self.adxs.append(bt.indicators.ADX(
                d, period=self.params.adx_period))
            self.atrs.append(bt.indicators.ATR(
                d, period=self.params.atr_period))
            self.bbands.append(bt.indicators.BollingerBands(self.closes[i],
                                                            period=self.params.bbands_period,
                                                            devfactor=self.params.bbands_devfactor))
            self.rsis.append(bt.indicators.RSI(
                self.closes[i], period=self.params.rsi_period))
            self.highest_highs.append(bt.indicators.Highest(
                self.highs[i], period=self.params.trend_breakout_lookback))
            self.sma_volumes.append(bt.indicators.SMA(
                self.volumes[i], period=self.params.trend_volume_avg_period))
        print("技术指标创建完成")  # 添加指标创建完成日志

        # State variables per data feed (using dictionaries)
        self.orders = {d: None for d in self.datas}
        self.buy_prices = {d: None for d in self.datas}
        self.buy_comms = {d: None for d in self.datas}
        self.stop_loss_prices = {d: None for d in self.datas}
        self.take_profit_prices = {d: None for d in self.datas}
        self.position_types = {d: None for d in self.datas}

        # Shared state variables
        self.high_water_mark = 0
        self.drawdown_level1_triggered = False
        self.halt_trading = False
        self.current_risk_multiplier = 1.0
        print("策略初始化完成")  # 添加初始化完成日志

    def _calculate_trade_size(self, current_price, entry_price, stop_loss_price, risk_per_trade_percent):
        """
        计算交易头寸大小
        :param current_price: 当前价格
        :param entry_price: 入场价格
        :param stop_loss_price: 止损价格
        :param risk_per_trade_percent: 单笔交易风险比例
        :return: 交易数量
        """
        # 计算账户总价值
        total_value = self.broker.getvalue()

        # 计算单笔交易允许的最大风险金额
        max_risk_amount = total_value * risk_per_trade_percent

        # 计算每股风险金额
        risk_per_share = abs(entry_price - stop_loss_price)

        # 如果风险为0，返回0
        if risk_per_share == 0:
            return 0

        # 计算基于风险的交易数量
        size = int(max_risk_amount / risk_per_share)

        # 考虑单个ETF的最大仓位限制
        max_position_value = total_value * self.params.max_position_per_etf_percent
        max_position_size = int(max_position_value / current_price)

        # 取两者中的较小值
        size = min(size, max_position_size)

        # 确保size是100的整数倍（A股交易规则）
        size = (size // 100) * 100

        return size

    def start(self):
        print("策略开始运行")  # 添加策略开始日志
        super().start()

    def stop(self):
        print("策略结束运行")  # 添加策略结束日志
        super().stop()

    def next(self):
        if len(self) == 1:  # 只在第一个bar打印
            print(f"开始处理数据，当前日期: {self.datetime.date()}")
        # Loop through each data feed
        for i, d in enumerate(self.datas):
            # 获取当前数据对象 d 和它的索引 i
            # (轮流检查每一只ETF)

            position = self.getposition(d)  # Get position for current data
            order = self.orders[d]  # Get order status for current data

            # Skip if order is pending for this specific data feed
            if order:
                # 检查当前此ETF是否有挂单。
                # (如果这只ETF昨天下了指令还没成交。)
                continue  # Move to the next data feed
                # 如果有挂单，则跳过此ETF，处理下一个。
                # (那就先等着它的指令结果，去看下一只ETF。)

            # --- 开仓逻辑 ---
            # (如果现在手里没货，才考虑要不要买。)
            # (如果现在这只ETF手里没货，才考虑要不要买。)

            # Global halt check
            if self.halt_trading:
                # 检查是否处于全局暂停交易状态。
                # (看看是不是因为之前亏太多暂停交易了。)
                continue  # Skip to next data if halted
                # 如果处于暂停交易状态，则不执行任何操作。
                # (如果是，那今天这只ETF啥也别干，去看下一只。)

            # 只有在没有持仓时才考虑开仓 (for this specific data feed)
            # if not self.position:
            if not position:
                # (如果现在这只ETF手里没货)
                market_state = 'UNCERTAIN_DO_NOT_TRADE'
                # 初始化市场状态为不确定，不交易。
                # (先假设今天这只ETF市场情况不明朗，最好别交易。)
                # Access indicators using the index 'i'
                is_trend_up = (self.closes[i][0] > self.emas_medium[i][0] > self.emas_long[i][0] and
                               self.emas_medium[i][0] > self.emas_medium[i][-1] and
                               self.emas_long[i][0] > self.emas_long[i][-1])
                # 判断是否处于上升趋势：当前收盘价>中期均线>长期均线，且两条均线都在向上。
                # (判断这只ETF是不是牛市：短期均线在长期均线上方，而且两条线都在往上走。)
                is_range_confirmed = (not is_trend_up and
                                      # 放宽均线走平条件
                                      abs(self.emas_medium[i][0] / self.emas_medium[i][-1] - 1) < 0.003 and
                                      # 放宽均线走平条件
                                      abs(self.emas_long[i][0] / self.emas_long[i][-1] - 1) < 0.003 and
                                      self.adxs[i].adx[0] < 20 and
                                      # 新增：布林带相对宽度小于7%
                                      (self.bbands[i].top[0] - self.bbands[i].bot[0]) / self.closes[i][0] < 0.07)
                # 判断是否处于震荡市：不是上升趋势，均线近似走平（允许小幅波动），ADX值较低，且布林带宽度较窄。
                # (判断这只ETF是不是震荡市：不是牛市，均线稍微有点动静没事，趋势强度弱，而且最近价格波动范围不大。)

                if is_trend_up:
                    # 如果判断为上升趋势。
                    # (如果是牛市。)
                    market_state = 'TREND_UP'
                    # 将市场状态设置为上升趋势。
                    # (那就标记一下，现在是上升趋势。)
                elif is_range_confirmed and self.p.etf_type == 'range':
                    # 如果判断为震荡市，并且该ETF被设定为适合震荡交易。
                    # (如果是震荡市，而且这个ETF适合"高抛低吸"。)
                    market_state = 'RANGE_CONFIRMED'
                    # 将市场状态设置为确认震荡。
                    # (那就标记一下，现在是震荡市。)

                entry_signal = False
                # 初始化入场信号为False。
                # (先假设今天这只ETF没有买入信号。)
                potential_position_type = None
                # 初始化潜在持仓类型。
                # (先假设不知道要按哪种策略买这只ETF。)
                # Assume entry at close for calculations, bracket order might use limit/market
                entry_price_calc = self.closes[i][0]
                # 假设以收盘价入场进行计算，括号订单可能使用限价或市价

                if market_state == 'TREND_UP' and self.p.etf_type == 'trend':
                    # 如果市场处于上升趋势，并且该ETF适合趋势交易。
                    # (如果是上升趋势，而且这个ETF适合"追涨杀跌"。)
                    is_breakout = (self.closes[i][0] > self.highest_highs[i][-1] and
                                   self.volumes[i][0] > self.sma_volumes[i][0] * self.params.trend_volume_ratio_min)
                    # 判断是否为突破信号：当前收盘价创近期新高，并且成交量放大。
                    # (判断这只ETF是不是突破了：价格创了最近60天新高，而且交易量比平时大。)
                    is_pullback = (min(abs(self.lows[i][0]/self.emas_medium[i][0]-1), abs(self.lows[i][0]/self.emas_long[i][0]-1)) < 0.01 and
                                   self.closes[i][0] > self.opens[i][0])
                    # 判断是否为回调企稳信号：当日最低价接近均线，并且当日收阳线。
                    # (判断这只ETF是不是回调站稳了：价格跌到均线附近，但当天又涨回来了。)

                    if is_breakout or is_pullback:
                        # 如果出现突破信号或回调企稳信号。
                        # (如果突破了或者回调站稳了。)
                        entry_signal = True
                        # 设置入场信号为True。
                        # (标记：可以买这只ETF了！)
                        potential_position_type = 'trend'
                        # 设置潜在持仓类型为趋势。
                        # (标记：这是按趋势策略买的。)
                        risk_per_trade_percent = self.params.max_risk_per_trade_trend
                        # 设置单笔交易风险比例为趋势策略的设定值。
                        # (标记：这次交易最多亏总资金的1%。)
                        stop_loss_price_calc = entry_price_calc - \
                            self.params.trend_stop_loss_atr_mult * \
                            self.atrs[i][0]
                        # 使用ATR计算止损价 (基于假定入场价计算)。
                        # (根据这只ETF最近的平均波动幅度，算出止损价应该设在假定入场价下方多少。)

                        # 检查止损价是否有效
                        if stop_loss_price_calc < entry_price_calc:
                            risk_per_share = entry_price_calc - stop_loss_price_calc
                            # 计算每股的风险金额。
                            # (算一下如果买在这只ETF当前价，跌到止损价，每股会亏多少钱。)
                            if risk_per_share > 0:
                                take_profit_price_calc = entry_price_calc + \
                                    self.params.trend_take_profit_rratio * risk_per_share
                                # 根据盈亏比计算止盈价 (基于假定入场价计算)。
                                # (根据设定的盈亏比（比如2倍），算出止盈价应该设在假定入场价上方多少。)
                            else:
                                entry_signal = False  # Stop loss is not below entry price
                                self.log(
                                    f"Trend signal skipped: Stop loss {stop_loss_price_calc:.2f} not below entry {entry_price_calc:.2f}", data=d)
                                # 记录跳过信号的日志。
                                # (记日记：趋势信号跳过，因为止损价不在入场价下方。)

                elif market_state == 'RANGE_CONFIRMED' and self.p.etf_type == 'range':
                    # 如果市场处于震荡市，并且该ETF适合震荡交易。
                    # (如果是震荡市，而且这个ETF适合"高抛低吸"。)
                    is_range_buy = (self.lows[i][0] <= self.bbands[i].bot[0] and
                                    self.closes[i][0] > self.bbands[i].bot[0] and
                                    self.rsis[i][0] < self.params.rsi_oversold)
                    # 判断是否为震荡买入信号：价格触及或下穿布林带下轨后收回，且RSI处于超卖区。
                    # (判断这只ETF是不是到底了：价格碰到或跌破布林带下轨，但当天收盘又涨回来了，并且RSI显示超卖。)

                    if is_range_buy:
                        # 如果出现震荡买入信号。
                        # (如果满足上面的条件。)
                        entry_signal = True
                        # 设置入场信号为True。
                        # (标记：可以买这只ETF了！)
                        potential_position_type = 'range'
                        # 设置潜在持仓类型为震荡。
                        # (标记：这是按震荡策略买的。)
                        risk_per_trade_percent = self.params.max_risk_per_trade_range
                        # 设置单笔交易风险比例为震荡策略的设定值。
                        # (标记：这次交易最多亏总资金的0.5%。)
                        stop_loss_price_calc = self.lows[i][0] * \
                            (1 - self.params.range_stop_loss_buffer)
                        # 计算止损价：触发信号K线的最低价下方一定比例。
                        # (把止损价设在触发信号那天最低价再低一点点的位置。)
                        take_profit_price_calc = self.bbands[i].mid[0]
                        # 计算止盈价：布林带中轨。
                        # (把止盈目标设在布林带的中线位置。)

                        # 检查止损价是否有效
                        if stop_loss_price_calc >= entry_price_calc:
                            entry_signal = False  # Stop loss is not below entry price
                            self.log(
                                f"Range signal skipped: Stop loss {stop_loss_price_calc:.2f} not below entry {entry_price_calc:.2f}", data=d)
                            # 记录跳过信号的日志。
                            # (记日记：震荡信号跳过，因为止损价不在入场价下方。)

                if entry_signal and stop_loss_price_calc is not None and entry_price_calc > stop_loss_price_calc:
                    # 如果有入场信号，且成功计算出有效的止损价。
                    # (如果决定要买这只ETF，而且算好了有效的止损价。)

                    # 调用辅助方法计算仓位大小, pass the current data's close price
                    # (让小工具帮忙算算买多少股。)
                    size = self._calculate_trade_size(
                        self.closes[i][0], entry_price_calc, stop_loss_price_calc, risk_per_trade_percent)

                    if size > 0:
                        # (如果算了一圈下来，确实还能买 > 0 股这只ETF。)
                        self.log(
                            f'CREATE BRACKET BUY ORDER, Size: {size}, StopPrice: {stop_loss_price_calc:.2f}, LimitPrice: {take_profit_price_calc if take_profit_price_calc else "N/A"}, Market State: {market_state}, Signal Type: {potential_position_type}', data=d)
                        # 记录创建买入括号订单的日志。
                        # (记日记：准备买入（括号单）！买多少股，止损价，止盈价，当前市场状态，是按哪种策略买的。)

                        # 使用 buy_bracket 创建订单
                        # 注意: buy_bracket 默认的入场订单类型是 Limit，价格是 price 参数。
                        # 如果想用市价单入场，需要设置 exectype=bt.Order.Market，并且 price 参数会被忽略。
                        # 这里我们假设希望以接近当前收盘价的价格入场，使用限价单可能更可控，但也可能无法成交。
                        # 如果希望尽快入场，可以使用市价单。我们暂时使用限价单，价格设为当前收盘价。
                        # 如果止盈价未计算出 (例如在某些趋势条件下)，则不设置止盈单 (limitexec=None)。
                        limit_exec_type = bt.Order.Limit if take_profit_price_calc is not None else None

                        bracket_orders = self.buy_bracket(
                            data=d,  # Specify the data feed for the order
                            size=size,
                            price=entry_price_calc,  # 主订单的价格 (Limit Order)
                            exectype=bt.Order.Limit,
                            # --- 止损参数 ---
                            stopprice=stop_loss_price_calc,  # 止损触发价格
                            stopexec=bt.Order.Stop,       # 止损单类型 (触发后市价卖出)
                            # --- 止盈参数 (可选) ---
                            limitprice=take_profit_price_calc,  # 止盈触发价格
                            limitexec=limit_exec_type         # 止盈单类型 (限价卖出)
                        )
                        # buy_bracket 返回一个包含三个订单的列表：[main_order, stop_order, limit_order]
                        # 我们需要将 self.order 设置为主订单，以便策略知道有挂单 (use dictionary)
                        if bracket_orders and bracket_orders[0]:
                            self.orders[d] = bracket_orders[0]
                        # 不需要再手动保存 stop_loss_price 和 take_profit_price (use dictionary if needed, but bracket handles exits)
                        # 也不需要保存 position_type，因为出场由括号单管理 (use dictionary if needed)


def optimize_strategy():
    print("开始初始化优化引擎...")  # 添加初始化日志
    # 在优化时禁用 stdstats, 避免 Observer 导致的序列化问题
    cerebro = bt.Cerebro(optreturn=True, stdstats=False, maxcpus=1)

    # 添加数据 - 复用主程序的数据加载逻辑
    data_files = [
        r'D:\\BT2025\\datas\\510050_d.xlsx',
        r'D:\\BT2025\\datas\\510300_d.xlsx',
        r'D:\\BT2025\\datas\\159949_d.xlsx',
    ]

    column_mapping = {
        'date': 'datetime',
        'open': 'open',
        'high': 'high',
        'low': 'low',
        'close': 'close',
        'volume': 'volume',
    }

    fromdate = datetime.datetime(2015, 1, 1)
    todate = datetime.datetime(2024, 4, 30)

    print("开始加载优化数据...")
    for file_path in data_files:
        try:
            print(f"正在加载数据文件: {file_path}")  # 添加文件加载日志
            dataframe = pd.read_excel(file_path)
            dataframe.rename(columns=column_mapping, inplace=True)

            if 'datetime' in dataframe.columns:
                dataframe['datetime'] = pd.to_datetime(dataframe['datetime'])
            else:
                print(f"错误: 在 {file_path} 中找不到映射后的 'datetime' 列。")
                continue

            dataframe.set_index('datetime', inplace=True)
            dataframe = dataframe.loc[fromdate:todate]

            data = bt.feeds.PandasData(
                dataname=dataframe,
                fromdate=fromdate,
                todate=todate,
                datetime=None,
                open='open',
                high='high',
                low='low',
                close='close',
                volume='volume',
                openinterest=-1
            )

            data_name = os.path.basename(file_path).split('.')[0]
            cerebro.adddata(data, name=data_name)
            print(f"优化数据加载成功: {data_name}")

        except Exception as e:
            print(f"加载数据 {file_path} 时出错: {e}")

    print("所有优化数据加载完成。")

    # 添加分析器
    print("添加分析器...")  # 添加分析器日志
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trade_analyzer')
    print("分析器添加完成。")  # 添加分析器完成日志

    # 设置优化参数范围
    print("设置优化参数范围...")
    print("参数组合数量估计：2 * 2 * 2 * 2 * 2 * 2 * 2 = 128 组")  # 添加参数组合数量估计
    cerebro.optstrategy(
        AShareETFStrategy,
        # 趋势判断参数 - 减少参数范围
        ema_medium_period=[40, 60],  # 只测试两个值
        ema_long_period=[100, 130],  # 只测试两个值

        # 风险控制参数 - 减少参数范围
        trend_stop_loss_atr_mult=[2.0, 2.5],  # 只测试两个值
        max_risk_per_trade_trend=[0.008, 0.01],  # 只测试两个值
        max_position_per_etf_percent=[0.25, 0.30],  # 只测试两个值

        # 震荡判断参数 - 减少参数范围
        bbands_period=[15, 20],  # 只测试两个值
        rsi_oversold=[25, 30],  # 只测试两个值
    )

    # 运行优化
    print("开始运行参数优化...")
    try:
        print("正在调用cerebro.run()...")
        print("这个过程可能需要几分钟到几小时，取决于参数组合数量和数据量...")  # 添加时间预期提示
        results = cerebro.run()
        print(
            f"cerebro.run()执行完成，结果类型: {type(results)}，长度: {len(results) if results else 0}")
    except Exception as e:
        print(f"cerebro.run()执行出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

    print("参数优化运行结束。")

    # 分析结果
    if results:
        print(f"开始分析优化结果，共有{len(results)}组结果...")
        analyze_results(results)
    else:
        print("没有可分析的结果。")

    return results


def analyze_results(results):
    # 提取每组参数的评估指标
    total_combinations = len(results)  # 获取总参数组合数
    if not total_combinations:
        print("没有优化结果可供分析")
        return

    print(f"\n总共测试了 {total_combinations} 个参数组合")
    print("开始逐个分析参数组合...")  # 添加分析开始日志

    for i, result in enumerate(results, 1):  # 使用enumerate获取序号,从1开始计数
        if not result:  # 检查结果是否为空
            print(f"跳过空结果组合 {i}")
            continue

        params = result[0].params
        analyzers = result[0].analyzers

        try:
            print(f'\n分析参数组合 [{i}/{total_combinations}]')  # 修改进度提示

            # 获取关键指标(添加默认值处理)
            sharpe = getattr(analyzers.sharpe.get_analysis(),
                             'sharperatio', 0.0)
            drawdown = getattr(
                analyzers.drawdown.get_analysis().max, 'drawdown', 0.0)
            returns = getattr(analyzers.returns.get_analysis(), 'rtot', 0.0)

            # 计算综合得分(示例权重)
            score = returns * 0.5 + sharpe * 0.3 - drawdown * 0.2

            # 打印结果
            print(f'参数: {params}')
            print(f'夏普比率: {sharpe:.2f}')
            print(f'最大回撤: {drawdown:.2%}')
            print(f'总收益率: {returns:.2%}')
            print(f'综合得分: {score:.2f}')
            print('---')
        except Exception as e:
            print(f'分析结果处理出错: {str(e)}')
            print(f'参数: {params}')
            print('---')
            continue

    print("\n优化分析完成")


if __name__ == '__main__':
    # 是否进行参数优化
    DO_OPTIMIZATION = True  # 控制是否执行优化

    if DO_OPTIMIZATION:
        # 执行参数优化
        results = optimize_strategy()
        if results:  # 确保有结果才进行分析
            analyze_results(results)
    else:
        # 原有的回测代码
        cerebro = bt.Cerebro()

        # 定义 Excel 数据文件路径列表
        data_files = [
            r'D:\\BT2025\\datas\\510050_d.xlsx',
            r'D:\\BT2025\\datas\\510300_d.xlsx',
            r'D:\\BT2025\\datas\\159949_d.xlsx',
        ]

        # 定义 Excel 列名到 Backtrader 标准名称的映射
        # (因为 Excel 里的菜单（列名）可能是中文，我们需要翻译成大厨（Backtrader）认识的标准名称)
        # 更新：根据截图，Excel 中的列名是英文的
        column_mapping = {
            'date': 'datetime',  # 'date' 列对应 'datetime'
            'open': 'open',      # 'open' 列对应 'open' (名称相同，映射保持)
            'high': 'high',      # 'high' 列对应 'high'
            'low': 'low',        # 'low' 列对应 'low'
            'close': 'close',    # 'close' 列对应 'close'
            'volume': 'volume',  # 'volume' 列对应 'volume'
            # 'code' 列我们不需要映射给 Backtrader 的标准 OHLCV
        }
        # 指定持仓量列，-1 表示不存在或不使用
        # (告诉大厨我们这份菜单里没有'持仓量'这道菜)
        openinterest_col = -1

        # 设置回测的起止日期
        # (设定我们要回顾哪段时间的交易历史)
        fromdate = datetime.datetime(2015, 1, 1)
        # (从 2015 年 1 月 1 日开始)
        todate = datetime.datetime(2024, 4, 30)
        # (到 2024 年 4 月 30 日结束)

        print("开始加载数据...")
        # (准备开始上菜了)
        # 循环处理每个 Excel 文件
        # (一道菜一道菜地准备)
        for file_path in data_files:
            # (处理当前这道菜的文件路径)
            try:
                # 使用 pandas 读取 Excel 文件
                # (让 pandas 去读 Excel 菜单)
                dataframe = pd.read_excel(file_path)
                # (读取成功，拿到菜单内容)

                # 重命名列以匹配 Backtrader 要求
                # (按照我们定义的映射关系，翻译菜单上的菜名)
                dataframe.rename(columns=column_mapping, inplace=True)
                # (翻译完成)

                # 检查并转换日期时间列
                # (确保菜单上的日期是大厨能看懂的格式)
                if 'datetime' in dataframe.columns:
                    # (菜单上有日期这一项)
                    try:
                        # 尝试将 'datetime' 列转换为 pandas 的 datetime 对象
                        # (尝试把日期文字变成标准的日期格式)
                        dataframe['datetime'] = pd.to_datetime(
                            dataframe['datetime'])
                        # (转换成功)
                    except Exception as e:
                        # (如果转换失败)
                        print(f"警告: 无法解析 {file_path} 中的日期时间列，请检查格式。错误: {e}")
                        # (打印警告信息，提示用户检查日期格式)
                        continue  # 跳过这个文件
                        # (这道菜的日期格式不对，先不上了)
                else:
                    # (如果菜单上找不到'日期'这一项)
                    print(
                        f"错误: 在 {file_path} 中找不到映射后的 'datetime' 列。请确保Excel文件中有'日期'列，或正确修改脚本中的column_mapping。")
                    # (打印错误信息)
                    continue  # 跳过这个文件
                    # (这道菜缺了最重要的日期，没法上)

                # 将 'datetime' 列设置为 DataFrame 的索引
                # (把日期作为菜单的主键/行号，方便查找)
                dataframe.set_index('datetime', inplace=True)
                # (设置完成)

                # 检查必需的 OHLCV 列是否存在
                # (检查菜单上是否有开盘、最高、最低、收盘、成交量这几样核心信息)
                required_cols = ['open', 'high', 'low', 'close', 'volume']
                # (定义需要检查的核心信息列表)
                if not all(col in dataframe.columns for col in required_cols):
                    # (如果核心信息不全)
                    print(f"错误: {file_path} 映射后缺少必需的列。")
                    # (打印错误信息)
                    print(f"可用的列: {dataframe.columns.tolist()}")
                    # (告诉用户现在菜单上都有哪些信息)
                    continue  # 跳过这个文件
                    # (这道菜信息不全，没法上)

                # 筛选指定日期范围内的数据
                # (只选取我们设定回顾时间段内的菜单记录)
                dataframe = dataframe.loc[fromdate:todate]
                # (选取完成)

                # 创建 PandasData 数据源实例
                # (准备用 Backtrader 的 PandasData 工具来包装这份整理好的菜单)
                data = bt.feeds.PandasData(
                    dataname=dataframe,  # 指定数据源为我们处理好的 DataFrame
                    # (告诉工具，食材数据在这里)
                    fromdate=fromdate,  # 开始日期 (虽然上面筛选过，这里也指定以防万一)
                                         # (再次确认开始时间)
                    todate=todate,      # 结束日期 (再次确认结束时间)
                                         # (再次确认结束时间)
                    # 以下参数指定 DataFrame 中的列名，PandasData 会自动查找
                    # (告诉工具，菜单上各项信息对应的标准名称是什么)
                    datetime=None,      # Datetime 已经是索引，设为 None 或 -1
                                         # (日期是行号，不用特别指定列)
                    open='open',        # 开盘价列名
                                         # (开盘价看这里)
                    high='high',        # 最高价列名
                                         # (最高价看这里)
                    low='low',          # 最低价列名
                                         # (最低价看这里)
                    close='close',      # 收盘价列名
                                         # (收盘价看这里)
                    volume='volume',    # 成交量列名
                                         # (成交量看这里)
                    openinterest=openinterest_col  # 持仓量列，-1 表示无
                    # (持仓量没有)
                )

                # 从文件名提取数据名称，用于绘图或区分
                # (给这道菜取个名字，比如 '510050_d')
                data_name = os.path.basename(file_path).split('.')[0]
                # (名字取好了)
                # 将数据源添加到 Cerebro 引擎
                # (把这道准备好的菜（数据源）交给大脑（Cerebro）)
                cerebro.adddata(data, name=data_name)
                # (上菜成功！)
                print(f"数据加载成功: {data_name}")
                # (报告一下，这道菜上好了)

            except FileNotFoundError:
                # (如果找不到 Excel 文件)
                print(f"错误: 文件未找到 {file_path}")
                # (打印找不到文件的错误)
            except Exception as e:
                # (如果在读取或处理过程中发生其他错误)
                print(f"加载数据 {file_path} 时出错: {e}")
                # (打印具体的错误信息)

        print("所有数据加载完成。")
        # (所有的菜都上齐了)

        # 添加策略到 Cerebro
        # (告诉大脑要用哪个大厨（策略）来做菜)
        cerebro.addstrategy(AShareETFStrategy, etf_type='trend')  # 假设策略能处理多数据
        # (指定使用 AShareETFStrategy 这个策略，并给它一个参数 'trend')

        # 设置初始资金
        # (给大厨起始的本金，比如 50 万)
        cerebro.broker.setcash(500000.0)
        # (设置初始资金为 500,000)

        # 设置交易佣金
        # (设定每次买卖要交的手续费，比如万分之三)
        cerebro.broker.setcommission(commission=0.0003, stocklike=True)
        # (设置佣金为 0.0003，计算方式类似股票)

        # 添加分析器
        # (添加一些分析工具，帮我们评估策略表现)
        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
        # 添加交易分析器
        cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trade_analyzer')

        print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
        # (打印开始时的总资产)

        # 运行回测
        # (让大脑开始指挥整个回测过程)
        results = cerebro.run()
        # (运行结束，拿到结果)

        # 添加检查，防止因数据加载失败导致 results 为空而出错
        if not results:
            # (如果结果列表是空的)
            print("\n错误：没有策略成功运行。请检查数据加载部分是否有错误（例如'datetime'列名问题）。")
            # (打印错误信息，提示检查数据加载)
        else:
            # (如果结果列表不为空，正常处理)
            strat = results[0]  # 获取策略实例
            # (拿到策略实例，方便后续获取分析结果)

            print('\nFinal Portfolio Value: %.2f' % cerebro.broker.getvalue())
            # (打印结束时的总资产)

            # 打印分析结果 (示例)
            # (展示分析工具给出的报告)
            print(
                f"夏普比率 (Sharpe Ratio): {strat.analyzers.sharpe.get_analysis().get('sharperatio', 'N/A')}")
            # (打印夏普比率)
            print(
                f"最大回撤 (Max Drawdown): {strat.analyzers.drawdown.get_analysis().max.drawdown:.2f}%")
            # (打印最大回撤百分比)
            print(
                f"年化收益率 (Annualized Return): {strat.analyzers.returns.get_analysis().get('rnorm100', 'N/A'):.2f}%")
            # (打印年化收益率)
            # print trade analysis details
            # (打印交易分析的详细信息)
            if hasattr(strat.analyzers, 'trade_analyzer'):  # 增加检查
                trade_analysis = strat.analyzers.trade_analyzer.get_analysis()
                for k, v in trade_analysis.items():
                    # (遍历分析结果的每一项)
                    if isinstance(v, dict):  # 打印字典类型的子分析结果
                        # (如果是字典类型的结果，比如各种统计)
                        print(f"--- {k} ---")  # 打印标题
                        # (打印小标题)
                        for k2, v2 in v.items():
                            # (遍历字典内的每一项)
                            print(f"  {k2}: {v2}")  # 打印键值对
                            # (打印具体的统计项和值)
                    else:
                        print(f"{k}: {v}")  # 直接打印非字典类型的结果
                        # (如果不是字典，直接打印)

            # 绘制结果图
            # (把回测过程和结果画成图表)
            # 注意：当数据量很大或运行多数据时，绘图可能需要较长时间或内存
            # cerebro.plot(style='candlestick', barup='red', bardown='green')
            # (使用k线图风格绘制，可以根据喜好调整参数)
            # 如果遇到绘图问题，可以尝试减少数据量或分批绘图，或者使用 cerebro.plot(iplot=False) 保存到文件
            try:
                print("\n开始绘制图表...")
                # (尝试绘制图表)
                cerebro.plot(style='candlestick', barup='red',
                             bardown='green', iplot=True, volume=True)
                # (使用指定的样式和颜色进行绘图，包含成交量)
                print("图表绘制完成。")
                # (报告图表绘制完毕)
            except Exception as e:
                # (如果绘图过程中出错)
                print(f"\n绘制图表时出错: {e}")
                # (打印绘图错误信息)
                print("请尝试调整绘图参数或检查数据。")
                # (给出建议)
