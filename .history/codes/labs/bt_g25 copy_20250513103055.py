import backtrader as bt
    # 导入backtrader量化交易框架，并简写为bt
    # (引入一个专门做量化交易的Python工具箱，给它起个短名字bt方便后面使用)

import datetime
    # 导入datetime模块用于处理日期和时间
    # (引入一个能处理日期和时间的工具，比如可以知道今天是几号)

import math
    # 导入math模块提供数学运算功能
    # (引入数学计算工具，可以做开方、对数等运算)

import pandas as pd
    # 导入pandas数据分析库，并简写为pd
    # (引入一个专门处理表格数据的工具，类似Excel但更强大)

import os
    # 导入os模块提供操作系统相关功能
    # (引入能和电脑操作系统打交道的工具，比如查找文件)

import sys
    # 导入sys模块提供Python解释器相关功能
    # (引入能查看和控制Python程序运行环境的工具)

import numpy as np
    # 导入numpy数值计算库，并简写为np
    # (引入一个快速处理数字和数组的工具，特别适合做科学计算)

import matplotlib.pyplot as plt
    # 导入matplotlib的pyplot绘图模块，并简写为plt
    # (引入一个画图工具，可以把数据变成漂亮的图表)

import time
    # 导入time模块提供时间相关功能
    # (引入能获取当前时间和控制程序等待的工具)

import itertools
    # 导入itertools模块提供迭代器工具
    # (引入一个能高效处理循环和迭代的工具)


class AShareETFSizer(bt.Sizer):
    # 定义A股ETF头寸计算类，继承自backtrader的Sizer基类
    # (创建一个专门计算A股ETF买卖数量的工具，基于backtrader的基础工具改造)
    
    params = (
        ('etf_type_param_name', 'etf_type'),
            # 定义策略中ETF类型参数的名称，默认为'etf_type'
            # (告诉Sizer去哪里找策略中的ETF类型参数)
        
        ('risk_per_trade_trend', 0.01),
            # 趋势型ETF每笔交易风险比例，默认为1%
            # (如果是趋势型ETF，每次交易最多亏总资金的1%)
        
        ('risk_per_trade_range', 0.005),
            # 区间型ETF每笔交易风险比例，默认为0.5%
            # (如果是区间型ETF，每次交易最多亏总资金的0.5%)
        
        ('max_position_per_etf_percent', 0.30),
            # 单个ETF最大持仓比例，默认为30%
            # (不管怎么买，单个ETF的市值不能超过总资产的30%)
        
        ('trend_stop_loss_atr_mult_param_name', 'trend_stop_loss_atr_mult'),
            # 趋势止损ATR倍数参数的名称
        # 定义参数 `trend_stop_loss_atr_mult_param_name`，默认值为 'trend_stop_loss_atr_mult'，用于指定策略中趋势型止损ATR倍数的参数名称。
        # (设置一个选项叫 'trend_stop_loss_atr_mult_param_name'，它的默认值是 'trend_stop_loss_atr_mult'，这样Sizer就知道去策略里找哪个参数来确定趋势型止损要用几倍的ATR。)
        ('range_stop_loss_buffer_param_name', 'range_stop_loss_buffer'),
        # 定义参数 `range_stop_loss_buffer_param_name`，默认值为 'range_stop_loss_buffer'，用于指定策略中区间型止损缓冲区的参数名称。
        # (设置一个选项叫 'range_stop_loss_buffer_param_name'，它的默认值是 'range_stop_loss_buffer'，这样Sizer就知道去策略里找哪个参数来确定区间型止损的缓冲幅度。)
        ('atr_indicator_name_prefix', 'atr_'),
        # 定义参数 `atr_indicator_name_prefix`，默认值为 'atr_'，用于构建策略中ATR指标的名称，假设策略将ATR指标存储为类似 self.atr_DATANAME 的形式。
        # (设置一个选项叫 'atr_indicator_name_prefix'，默认是 'atr_'，如果策略里ATR指标的名字是像 'atr_股票代码' 这样的，Sizer就能通过这个前缀找到它。)
    )

    def _getsizing(self, comminfo, cash, data, isbuy):
        # 定义 `_getsizing` 方法，此方法由Backtrader在需要确定头寸大小时调用。
        # (定义一个名叫 `_getsizing` 的函数，`backtrader` 每次要决定买多少股票的时候，就会来问这个函数。)
        if not isbuy:
            # 检查当前操作是否为买入操作，如果不是 (即 `isbuy` 为 `False`)。
            # (判断一下是不是要买入，如果不是买入操作。)
            return 0
            # 返回0，表示不进行任何头寸调整或下单（此Sizer仅处理买入）。
            # (那就返回0，意思是不买，数量是0，因为这个Sizer只管买，不管卖。)

        position = self.broker.getposition(data)
        # 获取当前数据对象（例如某ETF）的持仓情况。
        # (查一下现在手上有没有这只ETF，有多少。)
        if position.size != 0:
            # 如果当前数据对象已有持仓 (持仓数量不为0)。
            # (如果已经持有这只ETF了。)
            return 0
            # 返回0，表示不进行新的买入操作，因为已经持有该ETF。
            # (那就返回0，意思是不再买了，因为已经有了。)

        d_name = data._name
        # 获取当前数据对象的名称（例如ETF的代码）。
        # (拿到这只ETF的名字，比如它的代码。)
        strategy = self.strategy
        # 获取关联的策略实例，以便访问策略的参数和指标。
        # (拿到咱们正在用的那个交易策略，好从策略里取东西。)

        current_etf_type = getattr(
        # 使用 `getattr` 函数动态获取策略参数中定义的ETF类型。
        # (去策略的参数设置里找一下当前这只ETF是什么类型的。)
            strategy.params, self.p.etf_type_param_name, 'trend')
            # 从 `strategy.params` 中获取名为 `self.p.etf_type_param_name` (例如 'etf_type') 的参数值，如果找不到，则默认为 'trend'。
            # (具体找的是由 `self.p.etf_type_param_name` 指定的那个参数，如果策略里没设，就当它是 'trend' 型的。)

        if current_etf_type == 'trend':
            # 如果当前ETF类型为 'trend' (趋势型)。
            # (如果这只ETF是趋势型的。)
            risk_per_trade_percent = self.p.risk_per_trade_trend
            # 设置单次交易风险百分比为Sizer参数中定义的趋势型风险比例。
            # (那么这次交易的风险就用咱们Sizer里设定的趋势型风险比例。)
            atr_mult_param_name = self.p.trend_stop_loss_atr_mult_param_name
            # 获取策略中用于趋势型止损的ATR倍数参数的名称。
            # (找到策略里那个决定趋势型止损用几倍ATR的参数的名字。)
            atr_mult = getattr(strategy.params, atr_mult_param_name)
            # 从策略参数中获取实际的ATR倍数值。
            # (根据上面找到的名字，从策略的参数设置里拿到具体的ATR倍数。)

            if not hasattr(strategy, 'atrs') or d_name not in strategy.atrs:
                # 检查策略实例中是否有 'atrs' 字典，或者当前数据名称是否在 'atrs' 字典中。
                # (看看策略里有没有存所有ETF的ATR值，或者这只ETF的ATR值在不在里面。)
                strategy.log(
                # 如果ATR数据不存在，则记录日志。
                # (要是找不到ATR，就记个日志说一下。)
                    f"Sizer: ATR indicator for {d_name} not found in strategy.atrs. Skipping trade.", data=data)
                    # 日志内容：Sizer无法为 {d_name} 找到ATR指标，跳过交易。
                    # (日志内容是：Sizer算不了，因为在策略的atrs记录里找不到 {d_name} 的ATR指标。这次交易就算了。)
                return 0
                # 返回0，不进行交易。
                # (返回0，不买了。)
            current_atr = strategy.atrs[d_name][0]
            # 获取当前数据对象最新的ATR值。
            # (从策略记录的ATR值里，拿到这只ETF最新的ATR。)
            if math.isnan(current_atr) or current_atr <= 1e-9:
                # 检查获取的ATR值是否为非数字 (NaN) 或过小 (接近0)。
                # (看看这个ATR值是不是有问题，比如不是个数字，或者太小了几乎等于0。)
                strategy.log(
                # 如果ATR值无效，则记录日志。
                # (如果ATR值不对，就记个日志。)
                    f"Sizer: Invalid ATR value ({current_atr}) for {d_name}. Skipping trade.", data=data)
                    # 日志内容：Sizer发现 {d_name} 的ATR值 ({current_atr}) 无效，跳过交易。
                    # (日志内容是：Sizer算不了，因为 {d_name} 的ATR值 ({current_atr}) 不对劲。这次交易就算了。)
                return 0
                # 返回0，不进行交易。
                # (返回0，不买了。)

            entry_price_ref = data.close[0]
            # 使用当前K线的收盘价作为参考入场价格。
            # (把现在这根K线的收盘价当作是我们要买入的价格参考。)
            stop_loss_price_ref = entry_price_ref - atr_mult * current_atr
            # 计算参考止损价格：入场参考价 - ATR倍数 * ATR值。
            # (算一下止损价大概是多少：参考买入价减去几倍的ATR。)

        elif current_etf_type == 'range':
            # 如果当前ETF类型为 'range' (区间型)。
            # (如果这只ETF是区间型的。)
            risk_per_trade_percent = self.p.risk_per_trade_range
            # 设置单次交易风险百分比为Sizer参数中定义的区间型风险比例。
            # (那么这次交易的风险就用咱们Sizer里设定的区间型风险比例。)
            sl_buffer_param_name = self.p.range_stop_loss_buffer_param_name
            # 获取策略中用于区间型止损的缓冲百分比参数的名称。
            # (找到策略里那个决定区间型止损缓冲区的参数的名字。)
            sl_buffer = getattr(strategy.params, sl_buffer_param_name)
            # 从策略参数中获取实际的止损缓冲百分比。
            # (根据上面找到的名字，从策略的参数设置里拿到具体的缓冲百分比。)

            entry_price_ref = data.close[0]
            # 使用当前K线的收盘价作为参考入场价格。
            # (把现在这根K线的收盘价当作是我们要买入的价格参考。)
            if not hasattr(strategy, 'lows') or d_name not in strategy.lows:
                # 检查策略实例中是否有 'lows' 字典（存储最低价序列），或者当前数据名称是否在 'lows' 字典中。
                # (看看策略里有没有存所有ETF的最低价序列，或者这只ETF的最低价序列在不在里面。)
                strategy.log(
                # 如果最低价数据不存在，则记录日志。
                # (要是找不到最低价，就记个日志说一下。)
                    f"Sizer: Low price series for {d_name} not found in strategy.lows. Skipping trade.", data=data)
                    # 日志内容：Sizer无法为 {d_name} 找到最低价序列，跳过交易。
                    # (日志内容是：Sizer算不了，因为在策略的lows记录里找不到 {d_name} 的最低价序列。这次交易就算了。)
                return 0
                # 返回0，不进行交易。
                # (返回0，不买了。)

            stop_loss_price_ref = strategy.lows[d_name][0] * (1 - sl_buffer)
            # 计算参考止损价格：当前K线的最低价 * (1 - 止损缓冲百分比)。
            # (算一下止损价大概是多少：用现在这根K线的最低价再往下浮动一点点（由缓冲百分比决定）。)
        else:
            # 如果ETF类型未知。
            # (如果ETF的类型不是趋势型也不是区间型。)
            strategy.log(
            # 记录日志，说明ETF类型未知。
            # (记个日志说一下，不认识这个ETF类型。)
                f"Sizer: Unknown ETF type '{current_etf_type}' for {d_name}. Skipping trade.", data=data)
                # 日志内容：Sizer遇到未知的ETF类型 '{current_etf_type}' (针对 {d_name})，跳过交易。
                # (日志内容是：Sizer搞不懂 '{current_etf_type}' 是啥类型的ETF（针对 {d_name}）。这次交易就算了。)
            return 0
            # 返回0，不进行交易。
            # (返回0，不买了。)

        if stop_loss_price_ref >= entry_price_ref:
            # 如果计算出的参考止损价不低于参考入场价。
            # (如果算出来的止损价比参考买入价还要高或者一样。)
            strategy.log(
            # 记录日志，说明止损设置无效。
            # (记个日志说一下，这个止损价不对头。)
                f"Sizer: Stop loss {stop_loss_price_ref:.2f} not below entry {entry_price_ref:.2f} for {d_name}. Cannot size.", data=data)
                # 日志内容：Sizer发现 {d_name} 的止损价 {stop_loss_price_ref} 不低于入场价 {entry_price_ref}，无法计算头寸。
                # (日志内容是：Sizer算不了，因为 {d_name} 的止损价 {stop_loss_price_ref:.2f} 没有比参考买入价 {entry_price_ref:.2f} 低。没法算买多少。)
            return 0
            # 返回0，不进行交易。
            # (返回0，不买了。)

        risk_per_share = entry_price_ref - stop_loss_price_ref
        # 计算每股的风险金额：参考入场价 - 参考止损价。
        # (算一下如果买一股，最多会亏多少钱：就是参考买入价和参考止损价的差额。)
        if risk_per_share <= 1e-9:
            # 如果每股风险金额过小 (接近0)。
            # (如果算出来每股的风险特别小，几乎是0。)
            strategy.log(
            # 记录日志，说明每股风险过小。
            # (记个日志说一下，这个每股风险太小了。)
                f"Sizer: Risk per share for {d_name} is zero or too small ({risk_per_share:.2f}). Cannot size.", data=data)
                # 日志内容：Sizer发现 {d_name} 的每股风险 ({risk_per_share}) 为零或过小，无法计算头寸。
                # (日志内容是：Sizer算不了，因为 {d_name} 每股的风险 ({risk_per_share:.2f}) 是零或者太小了。没法算买多少。)
            return 0
            # 返回0，不进行交易。
            # (返回0，不买了。)

        effective_risk_percent = risk_per_trade_percent * strategy.current_risk_multiplier
        # 计算有效单次交易风险百分比：基础风险百分比 * 策略当前的风险乘数。
        # (算一下这次交易实际能承担的风险比例：基础的风险比例乘以策略当前的一个风险调整系数。)
        equity = self.broker.getvalue()
        # 获取当前账户总值。
        # (看看现在账户里总共有多少钱。)

        max_amount_to_risk_on_this_trade = equity * effective_risk_percent
        # 计算本次交易允许承担的最大风险金额：账户总值 * 有效单次交易风险百分比。
        # (算一下这次交易最多能亏多少钱：就是总资产乘以实际能承担的风险比例。)

        size_raw = max_amount_to_risk_on_this_trade / risk_per_share
        # 根据最大风险金额和每股风险计算原始的股票数量。
        # (用最多能亏的钱除以每股亏的钱，得到一个初步的购买数量。)
        size = int(size_raw / 100) * 100
        # 对原始数量向下取整到最近的100的倍数 (A股交易单位通常为100股的整数倍)。
        # (因为A股买卖最少是100股，所以把上面算出来的数量向下凑个整，变成100的倍数。)

        if size <= 0:
            # 如果根据风险计算出的头寸数量小于或等于0。
            # (如果算出来要买的数量是0或者负数。)
            strategy.log(
            # 记录日志，说明基于风险计算的头寸为0或负。
            # (记个日志说一下，按风险算下来买不了。)
                f"Sizer: Calculated size for {d_name} based on risk is {size}. Risk/share: {risk_per_share:.2f}. Amount to risk: {max_amount_to_risk_on_this_trade:.2f}", data=data)
                # 日志内容：Sizer为 {d_name} 基于风险计算的头寸为 {size}。每股风险: {risk_per_share}。允许风险金额: {max_amount_to_risk_on_this_trade}。
                # (日志内容是：Sizer给 {d_name} 按风险算出来的购买数量是 {size}。每股风险是 {risk_per_share:.2f}，这次交易能承受的总风险是 {max_amount_to_risk_on_this_trade:.2f}。)
            return 0
            # 返回0，不进行交易。
            # (返回0，不买了。)

        max_pos_value_for_etf = equity * self.p.max_position_per_etf_percent
        # 计算单个ETF允许的最大持仓市值：账户总值 * Sizer参数中定义的单个ETF最大持仓比例。
        # (算一下这只ETF最多能买多少钱的：就是总资产乘以Sizer里设定的单个ETF最大持仓比例。)
        price_for_value_calc = entry_price_ref
        # 使用参考入场价格计算持仓市值。
        # (用之前那个参考买入价来算市值。)

        if price_for_value_calc <= 1e-9:
            # 如果用于市值计算的价格过小 (接近0)。
            # (如果这个参考买入价太小了，几乎是0。)
            strategy.log(
            # 记录日志，说明价格无效。
            # (记个日志说一下，这个价格不对。)
                f"Sizer: Invalid price ({price_for_value_calc:.2f}) for {d_name} value calculation.", data=data)
                # 日志内容：Sizer发现 {d_name} 用于市值计算的价格 ({price_for_value_calc}) 无效。
                # (日志内容是：Sizer发现 {d_name} 用来算市值的价格 ({price_for_value_calc:.2f}) 不对劲。)
            return 0
            # 返回0，不进行交易。
            # (返回0，不买了。)

        size_limited_by_max_etf_pos = int(
        # 根据单个ETF最大持仓市值和价格计算允许的最大股数。
        # (根据这只ETF最多能买多少钱，以及它的价格，算出最多能买多少股。)
            max_pos_value_for_etf / price_for_value_calc / 100) * 100
            # 计算公式：(最大持仓市值 / 价格 / 100) 向下取整 * 100，确保是100的倍数。
            # (具体算法是：最多能买的钱数除以价格，再除以100，向下取整，然后再乘以100，保证是100的倍数。)
        if size > size_limited_by_max_etf_pos:
            # 如果基于风险计算的头寸数量超过了单个ETF最大持仓限制所允许的数量。
            # (如果前面按风险算出来的购买数量，比这只ETF本身能买的最大数量还要多。)
            strategy.log(
            # 记录日志，说明头寸被最大持仓限制所调整。
            # (记个日志说一下，因为单个ETF仓位限制，买的数量减少了。)
                f"Sizer: Size for {d_name} reduced from {size} to {size_limited_by_max_etf_pos} by max_position_per_etf_percent.", data=data)
                # 日志内容：Sizer将 {d_name} 的头寸从 {size} 减少到 {size_limited_by_max_etf_pos}，因为受到 `max_position_per_etf_percent` 限制。
                # (日志内容是：Sizer把 {d_name} 的购买数量从 {size} 股减到了 {size_limited_by_max_etf_pos} 股，因为受到了单个ETF最大仓位百分比的限制。)
            size = size_limited_by_max_etf_pos
            # 将头寸数量调整为单个ETF最大持仓限制所允许的数量。
            # (那就把购买数量改成这个ETF能买的最大数量。)

        if size <= 0:
            # 如果经过最大ETF持仓限制调整后的头寸数量小于或等于0。
            # (如果调整完之后，发现购买数量变成0或者负数了。)
            strategy.log(
            # 记录日志。
            # (记个日志。)
                f"Sizer: Calculated size for {d_name} after max ETF position limit is {size}.", data=data)
                # 日志内容：Sizer为 {d_name} 在最大ETF持仓限制后计算的头寸为 {size}。
                # (日志内容是：Sizer给 {d_name} 在单个ETF最大仓位限制之后算出来的购买数量是 {size}。)
            return 0
            # 返回0，不进行交易。
            # (返回0，不买了。)

        potential_trade_total_cost = size * price_for_value_calc
        # 计算潜在交易的总成本：调整后的头寸数量 * 参考价格。
        # (算一下如果按这个数量买，大概要花多少钱。)
        if potential_trade_total_cost > cash:
            # 如果潜在交易总成本超过当前可用现金。
            # (如果要花的钱比现在账户里能用的现金还多。)
            size_limited_by_cash = int(cash / price_for_value_calc / 100) * 100
            # 根据可用现金和价格计算能买的最大股数，并向下取整到100的倍数。
            # (那就用能用的现金，看看能买多少股，同样要凑成100的倍数。)
            if size_limited_by_cash < size:
                # 如果现金限制的股数小于当前计算的股数。
                # (如果按现金算出来能买的数量，比之前算出来的数量还要少。)
                strategy.log(
                # 记录日志，说明头寸被现金限制所调整。
                # (记个日志说一下，因为钱不够，买的数量又减少了。)
                    f"Sizer: Size for {d_name} reduced from {size} to {size_limited_by_cash} by cash limit. Cash: {cash:.2f}, Cost approx: {potential_trade_total_cost:.2f}", data=data)
                    # 日志内容：Sizer将 {d_name} 的头寸从 {size} 减少到 {size_limited_by_cash}，因为受到现金限制。可用现金: {cash}，预估成本: {potential_trade_total_cost}。
                    # (日志内容是：Sizer把 {d_name} 的购买数量从 {size} 股减到了 {size_limited_by_cash} 股，因为钱不够了。现在可用现金是 {cash:.2f}，本来预计要花 {potential_trade_total_cost:.2f}。)
                size = size_limited_by_cash
                # 将头寸数量调整为现金允许的最大数量。
                # (那就把购买数量改成现金能买的最大数量。)

        if size <= 0:
            # 如果最终计算出的头寸数量小于或等于0。
            # (如果最后算下来，购买数量是0或者负数。)
            strategy.log(
            # 记录日志，说明最终头寸为0或负，无法下单。
            # (记个日志说一下，最后算出来买不了。)
                f"Sizer: Final calculated size for {d_name} is {size}. Cannot place order.", data=data)
                # 日志内容：Sizer为 {d_name} 最终计算的头寸为 {size}，无法下单。
                # (日志内容是：Sizer给 {d_name} 最后算出来的购买数量是 {size}。下不了单了。)
            return 0
            # 返回0，不进行交易。
            # (返回0，不买了。)

        strategy.log(
        # 记录最终计算出的头寸大小及计算依据。
        # (记个日志，告诉大家最后算出来要买多少，以及是根据什么价格算出来的。)
            f"Sizer for {d_name} calculated size: {size} based on entry_ref: {entry_price_ref:.2f}, sl_ref: {stop_loss_price_ref:.2f}", data=data)
            # 日志内容：Sizer为 {d_name} 计算的头寸为: {size}，基于参考入场价: {entry_price_ref}，参考止损价: {stop_loss_price_ref}。
            # (日志内容是：Sizer给 {d_name} 算出来的购买数量是：{size} 股，参考的买入价是 {entry_price_ref:.2f}，参考的止损价是 {stop_loss_price_ref:.2f}。)
        return size
        # 返回最终计算出的、符合所有限制条件的头寸数量。
        # (把最后算好的购买数量告诉 `backtrader`。)


class AShareETFStrategy(bt.Strategy):
    # 定义一个名为 `AShareETFStrategy` 的类，它继承自 `backtrader.Strategy` 类，用于实现A股ETF的交易策略。
    # (创建一个专门针对A股ETF的交易策略，这个策略是基于 `backtrader` 里面一个叫 `Strategy` 的基础策略改造的。)
    params = (
        # 定义该策略的参数，这些参数可以在实例化策略时进行配置。
        # (给这个策略预设一些可以调整的选项。)
        ('etf_type', 'trend'),
        # 定义参数 `etf_type`，默认值为 'trend'，表示ETF的类型（例如 'trend' 或 'range'）。此参数会被Sizer访问。
        # (设置一个选项叫 'etf_type'，默认是 'trend'，用来区分ETF是趋势型还是区间型。这个设置会被上面的Sizer用到。)
        ('ema_medium_period', 60),
        # 定义参数 `ema_medium_period`，默认值为60，表示中期指数移动平均线 (EMA) 的周期。
        # (设置一个选项叫 'ema_medium_period'，默认是60天，用来算中期均线。)
        ('ema_long_period', 120),
        # 定义参数 `ema_long_period`，默认值为120，表示长期指数移动平均线 (EMA) 的周期。
        # (设置一个选项叫 'ema_long_period'，默认是120天，用来算长期均线。)
        ('adx_period', 14),
        # 定义参数 `adx_period`，默认值为14，表示平均动向指数 (ADX) 的周期。
        # (设置一个选项叫 'adx_period'，默认是14天，用来算ADX指标，判断趋势强度。)
        ('atr_period', 20),
        # 定义参数 `atr_period`，默认值为20，表示平均真实波幅 (ATR) 的周期。策略需要此参数将ATR值间接传递给Sizer。
        # (设置一个选项叫 'atr_period'，默认是20天，用来算ATR指标，衡量价格波动。这个值Sizer会用到。)
        ('bbands_period', 20),
        # 定义参数 `bbands_period`，默认值为20，表示布林带 (Bollinger Bands) 的周期。
        # (设置一个选项叫 'bbands_period'，默认是20天，用来算布林带。)
        ('bbands_devfactor', 2.0),
        # 定义参数 `bbands_devfactor`，默认值为2.0，表示布林带的标准差倍数。
        # (设置一个选项叫 'bbands_devfactor'，默认是2.0倍，用来确定布林带的宽度。)
        ('rsi_period', 14),
        # 定义参数 `rsi_period`，默认值为14，表示相对强弱指数 (RSI) 的周期。
        # (设置一个选项叫 'rsi_period'，默认是14天，用来算RSI指标，判断超买超卖。)
        ('rsi_oversold', 30),
        # 定义参数 `rsi_oversold`，默认值为30，表示RSI的超卖阈值。
        # (设置一个选项叫 'rsi_oversold'，默认是30，当RSI低于这个值时，可能表示超卖了。)
        ('trend_breakout_lookback', 60),
        # 定义参数 `trend_breakout_lookback`，默认值为60，表示趋势突破策略中回顾最高价的周期。
        # (设置一个选项叫 'trend_breakout_lookback'，默认是60天，用于趋势突破时，看过去这段时间的最高价。)
        ('trend_volume_avg_period', 20),
        # 定义参数 `trend_volume_avg_period`，默认值为20，表示趋势策略中计算平均成交量的周期。
        # (设置一个选项叫 'trend_volume_avg_period'，默认是20天，用于趋势策略里算平均成交量。)
        ('trend_volume_ratio_min', 1.1),
        # 定义参数 `trend_volume_ratio_min`，默认值为1.1，表示趋势策略中当前成交量与平均成交量的最小比率。
        # (设置一个选项叫 'trend_volume_ratio_min'，默认是1.1倍，用于趋势策略里，要求当前成交量至少是平均成交量的这么多倍。)
        ('trend_stop_loss_atr_mult', 2.5),
        # 定义参数 `trend_stop_loss_atr_mult`，默认值为2.5，表示趋势型交易中止损所使用的ATR倍数。Sizer已移走部分逻辑，但策略仍需此参数计算止损价格。
        # (设置一个选项叫 'trend_stop_loss_atr_mult'，默认是2.5倍，趋势交易时用几倍ATR来设置止损。虽然Sizer也用了，但策略自己算止损价时也需要。)
        ('trend_take_profit_rratio', 2.0),
        # 定义参数 `trend_take_profit_rratio`，默认值为2.0，表示趋势型交易中止盈与止损的风险回报比。
        # (设置一个选项叫 'trend_take_profit_rratio'，默认是2.0，趋势交易时，目标盈利应该是亏损的好几倍，这里是2倍。)
        ('range_stop_loss_buffer', 0.005),
        # 定义参数 `range_stop_loss_buffer`，默认值为0.005 (0.5%)，表示区间型交易中止损的缓冲百分比。
        # (设置一个选项叫 'range_stop_loss_buffer'，默认是0.005，区间交易时，止损价比最低点再低这么一点点作为缓冲。)
        ('max_total_account_risk_percent', 0.06),
        # 定义参数 `max_total_account_risk_percent`，默认值为0.06 (6%)，表示账户总风险敞口的最大百分比。这是策略层面在下单前的检查。
        # (设置一个选项叫 'max_total_account_risk_percent'，默认是0.06，意思是所有持仓的总风险不能超过账户总资产的6%。这个是策略在下单前自己要检查的。)
        ('drawdown_level1_threshold', 0.05),
        # 定义参数 `drawdown_level1_threshold`，默认值为0.05 (5%)，表示一级回撤阈值。
        # (设置一个选项叫 'drawdown_level1_threshold'，默认是0.05，当账户亏损达到5%时，算是一级回撤。)
        ('drawdown_level2_threshold', 0.10),
        # 定义参数 `drawdown_level2_threshold`，默认值为0.10 (10%)，表示二级回撤阈值。
        # (设置一个选项叫 'drawdown_level2_threshold'，默认是0.10，当账户亏损达到10%时，算是二级回撤。)
    )

    def log(self, txt, dt=None, data=None):
        # 定义 `log` 方法，用于在策略执行过程中输出日志信息。
        # (定义一个名叫 `log` 的函数，专门用来在策略跑的时候打印一些信息，方便我们看过程。)
        return
        # 立即从 `log` 方法返回，此行之后的代码不会被执行。
        # (写到这里就结束了，后面的代码实际上不会跑。)
        _data = data if data is not None else (
            self.datas[0] if self.datas else None)
        # 如果 `data` 参数已提供，则使用它；否则，如果策略有数据源，则使用第一个数据源；如果都没有，则为 `None`。
        # (看看调用log的时候有没有指定是哪个股票的数据，有就用那个；没有的话，如果策略本身在处理股票数据，就用第一个；如果啥数据都没有，那就没办法了。)

        log_dt_str = ""
        # 初始化日志日期时间字符串为空。
        # (准备一个空字符串，用来放日志的时间信息。)
        if _data and hasattr(_data, 'datetime') and len(_data.datetime) > 0:
            # 如果 `_data` 存在，并且它有 `datetime` 属性，并且 `datetime` 序列不为空。
            # (如果咱们有具体的股票数据，而且这个数据里面有时间信息，并且时间信息不是空的。)
            dt = dt or _data.datetime.date(0)
            # 如果 `dt` 参数未提供，则使用 `_data` 的当前日期。
            # (如果外面没传时间进来，就用当前这个股票数据对应的日期。)
            log_dt_str = dt.isoformat()
            # 将日期格式化为 ISO 格式的字符串。
            # (把日期变成标准格式的文字，比如 "2023-10-26"。)
        elif dt:
            # 如果 `_data` 不可用，但 `dt` 参数已提供。
            # (如果没股票数据，但是外面传了时间进来。)
            log_dt_str = dt.isoformat() if isinstance(
                dt, (datetime.date, datetime.datetime)) else str(dt)
            # 如果 `dt` 是日期或日期时间对象，则格式化为 ISO 格式；否则，转换为字符串。
            # (如果传进来的是正经的日期时间，就变成标准格式；如果不是，就直接变成文字。)
        else:
            # 如果 `_data` 和 `dt` 都不可用。
            # (如果既没股票数据，外面也没传时间。)
            log_dt_str = datetime.datetime.now().date().isoformat()
            # 使用当前系统的日期，并格式化为 ISO 格式。
            # (那就用电脑现在的日期，变成标准格式。)

        prefix = ""
        # 初始化日志前缀为空字符串。
        # (准备一个空字符串，用来放日志的前缀，比如股票代码。)
        if _data and hasattr(_data, '_name') and _data._name:
            # 如果 `_data` 存在，并且它有 `_name` 属性，并且 `_name` 不为空。
            # (如果咱们有具体的股票数据，而且这个数据有名字（比如股票代码），并且名字不是空的。)
            prefix = f"[{_data._name}] "
            # 设置前缀为 "[数据名称] "。
            # (就把前缀设置成 "[股票代码] " 这种样子。)

        print(f"{log_dt_str} {prefix}{txt}")
        # 打印格式化的日志消息，包括日期时间、前缀和日志文本 `txt`。
        # (把时间、前缀（股票代码）和要记录的内容 `txt` 一起打印出来。)

    def __init__(self):
        # 定义策略的构造函数 `__init__`，在策略实例化时执行。
        # (这是策略刚被创建出来的时候要做的事情，就像一个初始化仪式。)
        self.closes = {d._name: d.close for d in self.datas}
        # 创建一个字典 `self.closes`，用于存储每个数据源的收盘价序列，键为数据源名称，值为收盘价序列。
        # (创建一个叫 `self.closes` 的本子，把每个股票的收盘价都记下来，用股票代码当标签。)
        self.opens = {d._name: d.open for d in self.datas}
        # 创建一个字典 `self.opens`，用于存储每个数据源的开盘价序列。
        # (创建一个叫 `self.opens` 的本子，把每个股票的开盘价都记下来。)
        self.highs = {d._name: d.high for d in self.datas}
        # 创建一个字典 `self.highs`，用于存储每个数据源的最高价序列。
        # (创建一个叫 `self.highs` 的本子，把每个股票的最高价都记下来。)
        self.lows = {d._name: d.low for d in self.datas}
        # 创建一个字典 `self.lows`，用于存储每个数据源的最低价序列。
        # (创建一个叫 `self.lows` 的本子，把每个股票的最低价都记下来。)
        self.volumes = {d._name: d.volume for d in self.datas}
        # 创建一个字典 `self.volumes`，用于存储每个数据源的成交量序列。
        # (创建一个叫 `self.volumes` 的本子，把每个股票的成交量都记下来。)

        self.emas_medium = {d._name: bt.indicators.EMA(
            d.close, period=self.params.ema_medium_period) for d in self.datas}
        # 为每个数据源创建中期EMA指标，并存储在 `self.emas_medium` 字典中。EMA周期由策略参数 `ema_medium_period` 定义。
        # (给每个股票都算一个中期均线（EMA），周期用的是策略参数里设的 `ema_medium_period`，结果存在叫 `self.emas_medium` 的本子里。)
        self.emas_long = {d._name: bt.indicators.EMA(
            d.close, period=self.params.ema_long_period) for d in self.datas}
        # 为每个数据源创建长期EMA指标，并存储在 `self.emas_long` 字典中。EMA周期由策略参数 `ema_long_period` 定义。
        # (给每个股票都算一个长期均线（EMA），周期用的是策略参数里设的 `ema_long_period`，结果存在叫 `self.emas_long` 的本子里。)
        self.adxs = {d._name: bt.indicators.ADX(
            d, period=self.params.adx_period) for d in self.datas}
        # 为每个数据源创建ADX指标，并存储在 `self.adxs` 字典中。ADX周期由策略参数 `adx_period` 定义。
        # (给每个股票都算一个ADX指标，周期用的是策略参数里设的 `adx_period`，结果存在叫 `self.adxs` 的本子里。)
        self.atrs = {d._name: bt.indicators.ATR(
            d, period=self.params.atr_period) for d in self.datas}
        # 为每个数据源创建ATR指标，并存储在 `self.atrs` 字典中。ATR周期由策略参数 `atr_period` 定义。Sizer将需要访问这些ATR值。
        # (给每个股票都算一个ATR指标，周期用的是策略参数里设的 `atr_period`，结果存在叫 `self.atrs` 的本子里。这个Sizer会用到。)
        self.bbands = {d._name: bt.indicators.BollingerBands(
            d.close, period=self.params.bbands_period, devfactor=self.params.bbands_devfactor) for d in self.datas}
        # 为每个数据源创建布林带指标，并存储在 `self.bbands` 字典中。周期和标准差倍数由策略参数定义。
        # (给每个股票都算一个布林带指标，参数用的是策略里设的 `bbands_period` 和 `bbands_devfactor`，结果存在叫 `self.bbands` 的本子里。)
        self.rsis = {d._name: bt.indicators.RSI(
            d.close, period=self.params.rsi_period) for d in self.datas}
        # 为每个数据源创建RSI指标，并存储在 `self.rsis` 字典中。RSI周期由策略参数 `rsi_period` 定义。
        # (给每个股票都算一个RSI指标，周期用的是策略参数里设的 `rsi_period`，结果存在叫 `self.rsis` 的本子里。)
        self.highest_highs = {d._name: bt.indicators.Highest(
            d.high, period=self.params.trend_breakout_lookback) for d in self.datas}
        # 为每个数据源创建N周期内最高价指标 (`Highest`)，并存储在 `self.highest_highs` 字典中。周期由 `trend_breakout_lookback` 参数定义。
        # (给每个股票都算一个在过去一段时间（由 `trend_breakout_lookback` 参数决定）里的最高价，结果存在叫 `self.highest_highs` 的本子里。)
        self.sma_volumes = {d._name: bt.indicators.SMA(
            d.volume, period=self.params.trend_volume_avg_period) for d in self.datas}
        # 为每个数据源创建成交量的简单移动平均 (SMA) 指标，并存储在 `self.sma_volumes` 字典中。周期由 `trend_volume_avg_period` 参数定义。
        # (给每个股票都算一个成交量的均线（SMA），周期用的是策略参数里设的 `trend_volume_avg_period`，结果存在叫 `self.sma_volumes` 的本子里。)

        self.orders = {d._name: None for d in self.datas}
        # 初始化一个字典 `self.orders`，用于跟踪每个数据源的活动订单，初始时所有值为 `None`。
        # (创建一个叫 `self.orders` 的本子，用来记录每个股票当前的订单情况，一开始都是空的。)
        self.buy_prices = {d._name: None for d in self.datas}
        # 初始化一个字典 `self.buy_prices`，用于存储每个数据源的买入价格，初始时所有值为 `None`。
        # (创建一个叫 `self.buy_prices` 的本子，用来记录每个股票的买入价格，一开始都是空的。)
        self.position_types = {d._name: None for d in self.datas}
        # 初始化一个字典 `self.position_types`，用于存储每个数据源的持仓类型（例如 'trend' 或 'range'），初始时所有值为 `None`。
        # (创建一个叫 `self.position_types` 的本子，用来记录每个持仓是基于什么类型（比如趋势型还是区间型）买入的，一开始都是空的。)

        self.high_water_mark = self.broker.startingcash
        self.drawdown_level1_triggered = False
        self.halt_trading = False
        self.current_risk_multiplier = 1.0  # Sizer will access this

    # ... (notify_order, notify_trade, notify_cashvalue remain largely the same,
    #      ensure they use d_name for dictionary access)

    def notify_order(self, order):
        order_data_name = order.data._name if hasattr(
            order.data, '_name') else 'Unknown_Data'

        if order.status in [order.Submitted, order.Accepted]:
            self.log(
                f'Order {order.ref} Submitted/Accepted for {order_data_name}', data=order.data)
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
        data_name = trade.data._name if hasattr(
            trade.data, '_name') else 'Unknown_Data'
        self.log(
            f'OPERATION PROFIT for {data_name}, GROSS {trade.pnl:.2f}, NET {trade.pnlcomm:.2f}, Position Type: {self.position_types.get(data_name, "N/A")}', data=trade.data)

        if data_name in self.position_types:
            self.position_types[data_name] = None
        if data_name in self.buy_prices:
            self.buy_prices[data_name] = None

    def notify_cashvalue(self, cash, value):
        self.high_water_mark = max(self.high_water_mark, value)
        drawdown = (self.high_water_mark - value) / \
            self.high_water_mark if self.high_water_mark > 1e-9 else 0

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
                        self.log(
                            '--- Risk Level Restored (Drawdown below Level 1) ---')
                        self.drawdown_level1_triggered = False
                        self.current_risk_multiplier = 1.0
                elif self.drawdown_level1_triggered:
                    self.current_risk_multiplier = 0.5
            elif self.drawdown_level1_triggered and drawdown <= self.params.drawdown_level1_threshold:
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

            if position.size == 0:  # No position, check for entry
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
                    elif is_range_confirmed and self.p.etf_type == 'range':  # Use self.p for strategy params
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
                                    take_profit_price_calc = current_close + \
                                        self.p.trend_take_profit_rratio * risk_per_share_calc
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
                            stop_loss_price_calc = current_low * \
                                (1 - self.p.range_stop_loss_buffer)
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
                        self.log(
                            f'Warning for {d_name}: TP price for trend trade is None or invalid. Bracket will not have a limit sell.', data=d_obj)

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
                        self.log(
                            f'Failed to create buy_bracket order for {d_name} (possibly sizer returned 0 or error)', data=d_obj)


def load_data_to_cerebro(cerebro, data_files, column_mapping, openinterest_col, fromdate, todate):
    """
    加载Excel数据文件到Cerebro引擎中。
    Loads Excel data files into the Cerebro engine.

    Args:
        cerebro (bt.Cerebro): Cerebro引擎实例。 (Cerebro engine instance.)
        data_files (list): 包含Excel文件路径的列表。 (List containing Excel file paths.)
        column_mapping (dict): 列名映射字典。 (Dictionary for column name mapping.)
        openinterest_col (int): 持仓量列索引 (-1表示无)。 (Open interest column index (-1 for none).)
        fromdate (datetime.datetime): 回测起始日期。 (Backtest start date.)
        todate (datetime.datetime): 回测结束日期。 (Backtest end date.)

    Returns:
        int: 成功加载的数据源数量。 (Number of successfully loaded data feeds.)
    """
    print("开始加载数据...")
    # 打印提示信息，表示开始加载数据。 (Print a message indicating data loading has started.)
    loaded_data_count = 0  # 计数器，用于记录成功加载的数据数量
    # 初始化一个计数器，记录成功加载了多少个数据文件。 (Initialize a counter to track the number of successfully loaded data files.)
    for file_path in data_files:
        # 遍历数据文件路径列表。 (Iterate through the data file path list.)
        try:
            # 尝试执行以下代码，捕获可能发生的异常。 (Try to execute the following code, catching potential exceptions.)
            dataframe = pd.read_excel(file_path)
            # 使用pandas读取Excel文件到DataFrame。 (Use pandas to read the Excel file into a DataFrame.)
            dataframe.rename(columns=column_mapping, inplace=True)
            # 重命名DataFrame的列名，使其符合Backtrader标准。 (Rename the DataFrame columns to match Backtrader standards according to the mapping.)
            if 'datetime' in dataframe.columns:
                # 检查DataFrame中是否存在'datetime'列。 (Check if the 'datetime' column exists in the DataFrame.)
                try:
                    # 尝试将'datetime'列转换为datetime对象。 (Try to convert the 'datetime' column to datetime objects.)
                    dataframe['datetime'] = pd.to_datetime(
                        dataframe['datetime'])
                except Exception as e:
                    # 捕获日期时间转换异常。 (Catch datetime conversion exceptions.)
                    print(f"警告: 无法解析 {file_path} 中的日期时间列，请检查格式。错误: {e}")
                    # 打印警告信息，提示日期时间列解析失败，并显示错误信息。 (Print a warning message about parsing failure and the error.)
                    continue
                    # 跳过当前文件，继续处理下一个文件。 (Skip the current file and continue to the next.)
            else:
                # 如果DataFrame中不存在'datetime'列。 (If the 'datetime' column doesn't exist.)
                print(
                    f"错误: 在 {file_path} 中找不到映射后的 'datetime' 列。请确保Excel文件中有正确的日期列，或正确修改脚本中的column_mapping。")
                # 打印错误信息，提示找不到'datetime'列。 (Print an error message indicating the 'datetime' column is missing.)
                # 增加打印原始列名
                print(f"Excel文件中的原始列名是: {dataframe.columns.tolist()}")
                continue
                # 跳过当前文件，继续处理下一个文件。 (Skip the current file and continue to the next.)
            dataframe.set_index('datetime', inplace=True)
            # 将'datetime'列设置为DataFrame的索引。 (Set the 'datetime' column as the DataFrame index.)
            required_cols = ['open', 'high', 'low', 'close', 'volume']
            # 定义必需的OHLCV列名列表。 (Define the list of required OHLCV column names.)
            if not all(col in dataframe.columns for col in required_cols):
                # 检查DataFrame是否缺少必需的OHLCV列。 (Check if the DataFrame is missing any required OHLCV columns.)
                print(f"错误: {file_path} 映射后缺少必需的列。")
                # 打印错误信息，提示缺少必需的列。 (Print an error message indicating missing required columns.)
                print(f"可用的列: {dataframe.columns.tolist()}")
                # 打印可用的列名，帮助用户检查。 (Print the available column names to help the user check.)
                continue
                # 跳过当前文件，继续处理下一个文件。 (Skip the current file and continue to the next.)
            dataframe = dataframe.loc[fromdate:todate]
            # 筛选DataFrame，只保留指定日期范围内的数据。 (Filter the DataFrame to keep only data within the specified date range.)

            # 检查数据是否为空
            # Check if data is empty
            if dataframe.empty:
                print(f"警告: {file_path} 在指定日期范围内没有数据。")
                # 打印警告信息，提示在指定日期范围内没有数据。 (Print a warning that there is no data in the specified date range.)
                continue  # 跳过空数据
                # Skip empty data

            data = bt.feeds.PandasData(dataname=dataframe, fromdate=fromdate, todate=todate, datetime=None,
                                       open='open', high='high', low='low', close='close', volume='volume', openinterest=openinterest_col)
            # 创建PandasData数据源，使用处理后的DataFrame。 (Create a PandasData feed using the processed DataFrame.)
            data_name = os.path.basename(file_path).split('.')[0]
            # 从文件路径中提取数据名称。 (Extract the data name from the file path.)
            cerebro.adddata(data, name=data_name)
            # 将数据源添加到Cerebro引擎中。 (Add the data feed to the Cerebro engine.)
            print(f"数据加载成功: {data_name}")
            # 打印数据加载成功的提示信息。 (Print a success message for data loading.)
            loaded_data_count += 1  # 增加成功加载的计数
            # 计数器加1。 (Increment the successfully loaded counter.)

        except FileNotFoundError:
            # 捕获文件未找到异常。 (Catch file not found exceptions.)
            print(f"错误: 文件未找到 {file_path}")
            # 打印文件未找到的错误信息。 (Print a file not found error message.)
        except Exception as e:
            # 捕获其他所有异常。 (Catch all other exceptions.)
            print(f"加载数据 {file_path} 时出错: {e}")
            # 打印加载数据出错的错误信息，并显示具体的错误原因。 (Print an error message for data loading failure, including the specific error.)
    return loaded_data_count
    # 返回成功加载的数据源数量。 (Return the number of successfully loaded data feeds.)

# ===================================================================================
# 结果处理和评分函数 (Result Processing and Scoring Function)
# ===================================================================================


def analyze_optimization_results(results):
    """
    分析优化结果，计算归一化得分并找到最优参数。
    Analyzes optimization results, calculates normalized scores, and finds the best parameters.

    Args:
        results (list): cerebro.run() 返回的优化结果列表。 (List of optimization results returned by cerebro.run().)

    Returns:
        tuple: 包含最佳策略实例和所有结果得分的元组。 (Tuple containing the best strategy instance and scores for all results.)
               如果无法处理，则返回 (None, [])。 (Returns (None, []) if results cannot be processed.)
    """
    if not results:
        # 检查回测结果是否为空。 (Check if the backtest results are empty.)
        print("\n{:!^50}".format(' 错误 '))
        # 打印错误提示的分割线和标题。 (Print an error separator and title.)
        print("没有策略成功运行。请检查数据加载是否有误或参数范围是否有效。")
        # 打印错误信息，提示没有策略成功运行，建议检查数据加载或参数范围。 (Print an error message indicating no strategy ran successfully.)
        print('!' * 50)
        # 打印分割线。 (Print a separator line.)
        return None, []  # 返回空结果

    processed_results = []
    # 初始化一个列表，用于存储处理后的结果（参数、指标、原始得分）。 (Initialize a list to store processed results (params, metrics, raw scores).)

    print("\n--- 开始提取分析结果 ---")
    # 打印开始提取分析结果的提示。 (Print a message indicating the start of analysis result extraction.)
    for strat_list in results:  # optreturn=False时，results是列表的列表
        # 遍历每个策略回测结果列表（因为optreturn=False）。 (Iterate through each strategy backtest result list (because optreturn=False).)
        if not strat_list:
            continue  # 跳过空列表
        strategy_instance = strat_list[0]  # 获取策略实例
        # 获取策略实例。 (Get the strategy instance.)
        params = strategy_instance.params  # 获取参数
        # 获取当前策略的参数。 (Get the current strategy's parameters.)
        analyzers = strategy_instance.analyzers  # 获取分析器
        # 获取当前策略的分析器结果。 (Get the current strategy's analyzers.)

        try:
            # 尝试获取分析结果
            # Try to get analysis results
            sharpe_analysis = analyzers.sharpe_ratio.get_analysis()
            # 获取夏普比率分析结果。 (Get the Sharpe Ratio analysis result.)
            returns_analysis = analyzers.returns.get_analysis()
            # 获取收益率分析结果。 (Get the Returns analysis result.)
            drawdown_analysis = analyzers.drawdown.get_analysis()
            # 获取最大回撤分析结果。 (Get the Max Drawdown analysis result.)

            # 检查分析结果是否有效且包含所需键
            # Check if analysis results are valid and contain required keys
            if not sharpe_analysis or 'sharperatio' not in sharpe_analysis:
                print(f"警告: 参数组 {params.ema_medium_period}, {params.ema_long_period}, {params.bbands_period}, {params.bbands_devfactor} 的夏普比率分析结果不完整或为None，跳过。Sharpe: {sharpe_analysis}")
                # 打印警告信息，提示夏普比率结果不完整并跳过。 (Print a warning message about incomplete Sharpe Ratio results and skip.)
                continue
            if not returns_analysis or 'rtot' not in returns_analysis:
                print(f"警告: 参数组 {params.ema_medium_period}, {params.ema_long_period}, {params.bbands_period}, {params.bbands_devfactor} 的收益率分析结果不完整，跳过。Returns: {returns_analysis}")
                # 打印警告信息，提示收益率结果不完整并跳过。 (Print a warning message about incomplete Returns results and skip.)
                continue
            if not drawdown_analysis or 'max' not in drawdown_analysis or 'drawdown' not in drawdown_analysis.max:
                print(f"警告: 参数组 {params.ema_medium_period}, {params.ema_long_period}, {params.bbands_period}, {params.bbands_devfactor} 的最大回撤分析结果不完整，跳过。Drawdown: {drawdown_analysis}")
                # 打印警告信息，提示最大回撤结果不完整并跳过。 (Print a warning message about incomplete Max Drawdown results and skip.)
                continue

            sharpe = sharpe_analysis.get(
                'sharperatio', 0.0)  # Sharpe Ratio 可能为 None
            # 获取夏普比率，如果为None则设为0.0。 (Get the Sharpe Ratio, defaulting to 0.0 if None.)
            if sharpe is None:
                sharpe = 0.0  # 再次确认
            total_return = returns_analysis.get('rtot', 0.0)  # 总收益率（小数）
            # 从收益率分析器中获取总收益率（小数形式）。 (Get the total return (decimal form) from the Returns analyzer.)
            max_drawdown = drawdown_analysis.max.get(
                'drawdown', 0.0) / 100.0  # 最大回撤（转换为小数）
            # 从最大回撤分析器中获取最大回撤（转换为小数形式）。 (Get the max drawdown (converted to decimal form) from the Max Drawdown analyzer.)

            # Create a dictionary from the params object for easy access and printing
            current_params_dict = {}
            optimized_param_names = [
                'etf_type', 'ema_medium_period', 'ema_long_period',
                'bbands_period', 'bbands_devfactor', 'trend_stop_loss_atr_mult'
            ]
            for p_name in optimized_param_names:
                if hasattr(params, p_name):
                    current_params_dict[p_name] = getattr(params, p_name)
                else:
                    current_params_dict[p_name] = 'MISSING_IN_PARAMS_OBJ'

            processed_results.append({
                'instance': strategy_instance,
                'params_dict': current_params_dict,  # Store the created dictionary of parameters
                'sharpe': sharpe,
                'return': total_return,
                'drawdown': max_drawdown
            })
            # 将提取的结果添加到列表中。 (Add the extracted results to the list.)

        except AttributeError as e:
            # 捕获可能因分析器未正确运行或结果缺失引起的属性错误
            # Catch AttributeError possibly caused by analyzers not running correctly or missing results
            print(
                f"错误: 处理参数组时遇到属性错误 (可能是分析器结果缺失): {params.ema_medium_period if params else 'N/A'}, {params.ema_long_period if params else 'N/A'}, {params.bbands_period if params else 'N/A'}, {params.bbands_devfactor if params else 'N/A'}. 错误: {e}")
            # 打印错误信息。 (Print an error message.)
        except Exception as e:
            # 捕获处理单个结果时可能发生的其他异常。 (Catch other potential exceptions when processing a single result.)
            params_str = f"{params.ema_medium_period}, {params.ema_long_period}, {params.bbands_period}, {params.bbands_devfactor}" if params else "N/A"
            print(f"错误: 处理参数组 {params_str} 时出错: {e}")
            # 打印错误信息。 (Print an error message.)

    print(f"--- 成功提取 {len(processed_results)} 组分析结果 ---")
    # 打印成功提取的结果数量。 (Print the number of successfully extracted results.)

    if not processed_results:
        print("\n错误：未能成功提取任何有效的分析结果。无法进行评分。")
        # 打印错误信息。 (Print an error message.)
        return None, []

    # 提取所有指标用于计算min/max
    # Extract all metrics to calculate min/max
    all_sharpes = [r['sharpe'] for r in processed_results]
    # 提取所有夏普比率。 (Extract all Sharpe Ratios.)
    all_returns = [r['return'] for r in processed_results]
    # 提取所有总收益率。 (Extract all total returns.)
    all_drawdowns = [r['drawdown'] for r in processed_results]
    # 提取所有最大回撤。 (Extract all max drawdowns.)

    # 计算min/max，处理列表为空或只有一个元素的情况
    # Calculate min/max, handling cases where the list is empty or has only one element
    min_sharpe = min(all_sharpes) if all_sharpes else 0.0
    max_sharpe = max(all_sharpes) if all_sharpes else 0.0
    min_return = min(all_returns) if all_returns else 0.0
    max_return = max(all_returns) if all_returns else 0.0
    min_drawdown = min(all_drawdowns) if all_drawdowns else 0.0
    max_drawdown_val = max(all_drawdowns) if all_drawdowns else 0.0  # 重命名以避免覆盖

    # 归一化和评分
    # Normalization and scoring
    best_score = float('-inf')
    # 初始化最佳得分为负无穷。 (Initialize the best score to negative infinity.)
    best_result_data = None
    # 初始化最佳结果数据为None。 (Initialize the best result data to None.)
    scored_results = []
    # 初始化一个列表用于存储带得分的结果。 (Initialize a list to store results with scores.)

    print("\n--- 开始计算归一化得分 ---")
    # 打印开始计算得分的提示。 (Print a message indicating the start of score calculation.)
    print(f"Min/Max - Sharpe: ({min_sharpe:.4f}, {max_sharpe:.4f}), Return: ({min_return:.4f}, {max_return:.4f}), Drawdown: ({min_drawdown:.4f}, {max_drawdown_val:.4f})")
    # 打印计算出的min/max值。 (Print the calculated min/max values.)

    for result_data in processed_results:
        # 遍历处理后的结果。 (Iterate through the processed results.)
        sharpe = result_data['sharpe']
        # 获取夏普比率。 (Get the Sharpe Ratio.)
        ret = result_data['return']
        # 获取总收益率。 (Get the total return.)
        dd = result_data['drawdown']
        # 获取最大回撤。 (Get the max drawdown.)

        # 归一化，处理分母为0的情况
        # Normalize, handling division by zero
        sharpe_range = max_sharpe - min_sharpe
        # 计算夏普比率的范围。 (Calculate the range of Sharpe Ratios.)
        return_range = max_return - min_return
        # 计算总收益率的范围。 (Calculate the range of total returns.)
        drawdown_range = max_drawdown_val - min_drawdown
        # 计算最大回撤的范围。 (Calculate the range of max drawdowns.)

        sharpe_norm = (sharpe - min_sharpe) / \
            sharpe_range if sharpe_range > 1e-9 else 0.0
        # 计算归一化夏普比率，处理范围为0的情况。 (Calculate normalized Sharpe Ratio, handling zero range.)
        return_norm = (ret - min_return) / \
            return_range if return_range > 1e-9 else 0.0
        # 计算归一化总收益率，处理范围为0的情况。 (Calculate normalized total return, handling zero range.)
        # 注意：最大回撤值越小越好，但评分公式是减去它，所以正常归一化即可
        # Note: Lower drawdown is better, but the scoring formula subtracts it, so normal normalization is fine.
        drawdown_norm = (dd - min_drawdown) / \
            drawdown_range if drawdown_range > 1e-9 else 0.0
        # 计算归一化最大回撤，处理范围为0的情况。 (Calculate normalized max drawdown, handling zero range.)

        # 计算最终得分
        # Calculate the final score
        score = 0.5 * sharpe_norm + 0.3 * return_norm - 0.2 * drawdown_norm
        # 使用给定的权重计算最终得分。 (Calculate the final score using the given weights.)
        result_data['score'] = score
        # 将得分添加到结果数据中。 (Add the score to the result data.)
        scored_results.append(result_data)
        # 将带得分的结果添加到列表中。 (Add the scored result to the list.)

        if score > best_score:
            # 如果当前得分是最佳得分。 (If the current score is the best score.)
            best_score = score
            # 更新最佳得分。 (Update the best score.)
            best_result_data = result_data
            # 更新最佳结果数据。 (Update the best result data.)

    print(f"--- 完成 {len(scored_results)} 组得分计算 ---")
    # 打印完成得分计算的提示。 (Print a message indicating the completion of score calculation.)

    return best_result_data, scored_results
    # 返回最佳结果数据和所有带得分的结果。 (Return the best result data and all scored results.)


# ===================================================================================
# Main Program Entry Point
# ===================================================================================
if __name__ == '__main__':
    optimize = True
    # optimize = False
    initial_cash = 500000.0
    commission_rate = 0.0003

    data_folder = r'D:\\BT2025\\datas\\'  # Make sure this path is correct
    if not os.path.isdir(data_folder):
        print(f"错误: 数据文件夹路径不存在: {data_folder}")
        sys.exit(1)

    data_files = [
        os.path.join(data_folder, '510050_d.xlsx'),
        os.path.join(data_folder, '510300_d.xlsx'),
        os.path.join(data_folder, '159949_d.xlsx')
    ]
    # ... (rest of data file checks) ...

    column_mapping = {'date': 'datetime', '开盘': 'open',
                      '最高': 'high', '最低': 'low', '收盘': 'close', '成交量': 'volume'}
    openinterest_col_name = None

    fromdate = datetime.datetime(2015, 1, 1)
    todate = datetime.datetime(2024, 4, 30)

    # Sizer parameters (these were part of strategy params before)
    sizer_params = dict(
        etf_type_param_name='etf_type',  # Tells sizer how to find etf_type in strategy
        # Corresponds to AShareETFStrategy.params.max_risk_per_trade_trend
        risk_per_trade_trend=0.01,
        # Corresponds to AShareETFStrategy.params.max_risk_per_trade_range
        risk_per_trade_range=0.005,
        max_position_per_etf_percent=0.30,
        # Name of param in strategy
        trend_stop_loss_atr_mult_param_name='trend_stop_loss_atr_mult',
        # Name of param in strategy
        range_stop_loss_buffer_param_name='range_stop_loss_buffer'
    )

    # Optimization ranges for strategy params (sizing params are now fixed in sizer_params for this example)
    # If you want to optimize sizer params, you'd optstrategy on the Sizer's params if Backtrader supported it directly,
    # or create different sizer instances/subclasses.
    # For now, we optimize strategy params that influence signals and SL/TP prices for brackets.
    ema_medium_range = range(40, 81, 20)
    ema_long_range = range(100, 141, 20)
    bbands_period_range = range(15, 26, 5)
    # Convert numpy array to list
    bbands_dev_range = np.arange(1.8, 2.3, 0.2).tolist()
    # Example: optimizing ATR multiplier
    trend_sl_atr_mult_range = np.arange(
        2.0, 3.1, 0.5).tolist()  # Convert numpy array to list

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
        print(f"  etf_type: ['trend', 'range']")  # This is a strategy param
        print(f"  ema_medium_period: {list(ema_medium_range)}")
        print(f"  ema_long_period: {list(ema_long_range)}")
        print(f"  bbands_period: {list(bbands_period_range)}")
        print(f"  bbands_devfactor: {bbands_dev_range}")  # Already a list
        # Strategy param for bracket SL
        print(
            f"  trend_stop_loss_atr_mult: {trend_sl_atr_mult_range}")  # Already a list
        print('-' * 50)

        cerebro.optstrategy(AShareETFStrategy,
                            etf_type=['trend', 'range'],
                            ema_medium_period=ema_medium_range,
                            ema_long_period=ema_long_range,
                            bbands_period=bbands_period_range,
                            bbands_devfactor=bbands_dev_range,
                            trend_stop_loss_atr_mult=trend_sl_atr_mult_range  # Optimizing this strategy param
                            # Note: range_stop_loss_buffer could also be optimized if desired
                            )
        # ... (rest of the optimization execution and result processing logic remains the same)
        print('开始参数优化运行...')
        start_time = time.time()
        # DEBUG: Force single CPU to get detailed error traceback from child processes
        results = cerebro.run(maxcpus=10)
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
            # Correctly access parameters from the dictionary
            best_params_dict = best_result.get('params_dict', {})

            # Prepare headers and format strings, ensuring alignment
            # Adjusted width for ATR mult
            header_format = '{:<10} {:<12} {:<12} {:<12} {:<10} {:<10} {:<12} {:<12} {:<12} {:<12}'
            # Adjusted width for ATR mult
            row_format = '{:<10} {:<12} {:<12} {:<12.0f} {:<10.1f} {:<10.1f} {:<12.4f} {:<12.2f} {:<12.2f} {:<12.4f}'

            print('\n{:=^135}'.format(' 参数优化结果 (按得分排序) '))  # Adjusted width
            print(header_format.format('ETF类型', 'EMA中期', 'EMA长期', '布林周期',
                  '布林标差', 'ATR止损', '夏普比率', '收益率(%)', '最大回撤(%)', '得分'))
            print('-' * 135)  # Adjusted width

            all_scored_results.sort(key=lambda x: x.get(
                'score', float('-inf')), reverse=True)

            for res_data in all_scored_results[:min(20, len(all_scored_results))]:
                # Safely get the params dict
                p_dict = res_data.get('params_dict', {})
                print(row_format.format(
                    p_dict.get('etf_type', 'N/A'),
                    p_dict.get('ema_medium_period', 0),
                    p_dict.get('ema_long_period', 0),
                    p_dict.get('bbands_period', 0),
                    p_dict.get('bbands_devfactor', 0.0),
                    # Display optimized ATR mult
                    p_dict.get('trend_stop_loss_atr_mult', 0.0),
                    res_data.get('sharpe', 0.0),
                    res_data.get('return', 0.0) * 100,
                    res_data.get('drawdown', 0.0) * 100,
                    res_data.get('score', 0.0)
                ))

            print('\n{:=^50}'.format(' 最优参数组合 '))
            # Use the already retrieved best_params_dict
            print(f"{'ETF类型':<25}: {best_params_dict.get('etf_type', 'N/A')}")
            print(f"{'EMA中期':<25}: {best_params_dict.get('ema_medium_period', 0)}")
            print(f"{'EMA长期':<25}: {best_params_dict.get('ema_long_period', 0)}")
            print(f"{'布林带周期':<25}: {best_params_dict.get('bbands_period', 0)}")
            print(
                f"{'布林带标准差':<25}: {best_params_dict.get('bbands_devfactor', 0.0):.1f}")
            print(
                f"{'趋势止损ATR倍数':<25}: {best_params_dict.get('trend_stop_loss_atr_mult', 0.0):.1f}")
            print(f"{'夏普比率':<25}: {best_result.get('sharpe', 0.0):.4f}")
            print(f"{'总收益率':<25}: {best_result.get('return', 0.0) * 100:.2f}%")
            print(f"{'最大回撤':<25}: {best_result.get('drawdown', 0.0) * 100:.2f}%")
            print(f"{'得分':<25}: {best_result.get('score', 0.0):.4f}")
            print('=' * 50)
        else:
            print("\n错误：未能确定最优策略或处理结果时出错。")

    else:  # Single Run
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
