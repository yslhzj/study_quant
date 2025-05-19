import backtrader as bt
# 导入 `backtrader` 库，并将其别名为 `bt`，用于后续代码中通过 `bt` 调用该库的功能。
# (引入一个叫做 `backtrader` 的工具箱，给它取个小名叫 `bt`，以后用 `bt` 就能找到它里面的工具，这个工具箱是专门用来做股票交易回测的。)
import datetime
# 导入 `datetime` 库，用于处理日期和时间相关的操作。
# (引入一个叫做 `datetime` 的工具箱，专门用来处理日期和时间，比如今天是几月几号，现在是几点几分。)
import math
# 导入 `math` 库，提供数学运算功能，例如平方根、对数等。
# (引入一个叫做 `math` 的工具箱，里面有很多数学计算工具，比如开平方、算对数这些。)
import pandas as pd
# 导入 `pandas` 库，并将其别名为 `pd`，用于数据处理和分析，特别是处理表格数据（如DataFrame）。
# (引入一个叫做 `pandas` 的工具箱，给它取个小名叫 `pd`，它特别擅长处理表格数据，就像我们用的Excel一样。)
import os
# 导入 `os` 库，提供与操作系统交互的功能，例如文件路径操作、目录管理等。
# (引入一个叫做 `os` 的工具箱，它可以帮我们的程序和电脑操作系统打交道，比如找文件、创建文件夹。)
import sys
# 导入 `sys` 库，提供访问和控制Python解释器运行时环境的功能。
# (引入一个叫做 `sys` 的工具箱，它可以让我们了解和控制Python程序当前是怎么运行的。)
import numpy as np
# 导入 `numpy` 库，并将其别名为 `np`，用于进行高效的数值计算，特别是处理多维数组和矩阵。
# (引入一个叫做 `numpy` 的工具箱，给它取个小名叫 `np`，它专门用来做快速的数字计算，尤其能处理一大堆数字排成的队伍或者表格。)
import matplotlib.pyplot as plt
# 导入 `matplotlib.pyplot` 模块，并将其别名为 `plt`，用于创建静态、动态和交互式的图表和可视化。
# (引入 `matplotlib` 工具箱里的一个叫 `pyplot` 的画图工具，给它取个小名叫 `plt`，用它可以画出各种各样的图表，让数据看起来更直观。)
import time
# 导入 `time` 库，提供时间相关的功能，例如获取当前时间、程序暂停等。
# (引入一个叫做 `time` 的工具箱，它可以帮我们处理时间，比如知道现在几点了，或者让程序等一会儿。)
import itertools
# 导入 `itertools` 模块，该模块提供了用于创建高效迭代器的函数。
# (引入一个叫做 `itertools` 的工具箱，里面有很多能帮你按顺序处理一堆东西的工具，而且用起来很省力。)


class AShareETFSizer(bt.Sizer):
    # 定义一个名为 `AShareETFSizer` 的类，它继承自 `backtrader.Sizer` 类，用于自定义A股ETF的头寸计算逻辑。
    # (创建一个专门给A股ETF算每次买多少的工具，这个工具是基于 `backtrader` 里面一个叫 `Sizer` 的基础工具改造的。)
    params = (
        # 定义该Sizer的参数，这些参数可以在实例化Sizer时进行配置。
        # (给这个算数量的工具预设一些可以调整的选项。)
        ('etf_type_param_name', 'etf_type'),
        # 定义参数 `etf_type_param_name`，默认值为字符串 'etf_type'，用于指定策略中ETF类型的参数名称。
        # (设置一个选项叫 'etf_type_param_name'，它的默认值是 'etf_type'，这样Sizer就知道去策略里找哪个参数来判断ETF是趋势型还是区间型。)
        ('risk_per_trade_trend', 0.01),
        # 定义参数 `risk_per_trade_trend`，默认值为0.01 (1%)，表示趋势型ETF每次交易允许承担的风险比例。
        # (设置一个选项叫 'risk_per_trade_trend'，默认是0.01，意思是如果是趋势型的ETF，每次交易最多拿账户里1%的钱去冒险。)
        ('risk_per_trade_range', 0.005),
        # 定义参数 `risk_per_trade_range`，默认值为0.005 (0.5%)，表示区间型ETF每次交易允许承担的风险比例。
        # (设置一个选项叫 'risk_per_trade_range'，默认是0.005，意思是如果是区间型的ETF，每次交易最多拿账户里0.5%的钱去冒险。)
        ('max_position_per_etf_percent', 0.30),
        # 定义参数 `max_position_per_etf_percent`，默认值为0.30 (30%)，表示单个ETF持仓市值占总账户价值的最大比例。
        # (设置一个选项叫 'max_position_per_etf_percent'，默认是0.30，意思是不管怎么买，单个ETF的市值不能超过总资产的30%。)
        ('trend_stop_loss_atr_mult_param_name', 'trend_stop_loss_atr_mult'),
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
        # 初始化 `high_water_mark` (历史最高账户价值) 为初始资金。
        # (记录一下账户里钱最多的时候是多少，一开始就是本金。)
        self.drawdown_level1_triggered = False
        # 初始化 `drawdown_level1_triggered` (一级回撤触发标志) 为 `False`。
        # (设置一个标记 `drawdown_level1_triggered`，表示一级回撤警报还没响，初始是关着的（False）。)
        self.halt_trading = False
        # 初始化 `halt_trading` (暂停交易标志) 为 `False`。
        # (设置一个标记 `halt_trading`，表示现在没有暂停交易，初始是关着的（False）。)
        self.current_risk_multiplier = 1.0  # Sizer will access this
        # 初始化 `current_risk_multiplier` (当前风险乘数) 为1.0，Sizer会访问此值。
        # (设置一个当前的风险调整系数 `current_risk_multiplier`，一开始是1.0，意思是按正常风险来。这个Sizer会用到。)

    # ... (notify_order, notify_trade, notify_cashvalue remain largely the same,
    #      ensure they use d_name for dictionary access)

    def notify_order(self, order):
        # 定义 `notify_order` 方法，当订单状态发生变化时由Backtrader调用。
        # (定义一个名叫 `notify_order` 的函数，每当订单有新情况（比如下单了、成交了、取消了），`backtrader` 就会来告诉这个函数。)
        order_data_name = order.data._name if hasattr(
            order.data, '_name') else 'Unknown_Data'
        # 获取订单关联的数据源名称；如果无法获取，则设为 'Unknown_Data'。
        # (看看这个订单是哪个股票的，如果知道名字就用名字，不知道就叫 'Unknown_Data'。)

        if order.status in [order.Submitted, order.Accepted]:
            # 如果订单状态是已提交 (Submitted) 或已接受 (Accepted)。
            # (如果订单已经发出去了或者交易所已经收到了。)
            self.log(
                f'Order {order.ref} Submitted/Accepted for {order_data_name}', data=order.data)
            # 记录订单提交/接受的日志。
            # (就记个日志说一下这个订单发出去了或者被接受了。)
            if order.parent is None:
            # 如果订单没有父订单 (即它是一个主订单，而不是止损/止盈单的一部分)。
            # (如果这个订单不是某个大订单（比如括号单）里的小订单。)
                self.orders[order_data_name] = order
            # 将此订单存储在对应数据源的 `self.orders` 字典中。
            # (就把这个订单记在对应股票的 `self.orders` 本子里。)
            return
            # 从方法返回，不再执行后续代码。
            # (这事儿处理完了，不用往下看了。)

        if order.status in [order.Completed]:
            # 如果订单状态是已完成 (Completed)。
            # (如果订单已经成功交易了。)
            if order.isbuy():
                # 如果是买入订单。
                # (如果这是一个买单。)
                self.log(
                    f'BUY EXECUTED for {order_data_name} @ {order.executed.price:.2f}, Size: {order.executed.size}, Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}', data=order.data)
                # 记录买入执行的详细日志，包括价格、数量、成本和佣金。
                # (就记个日志说买入成功了，成交价多少，买了多少股，花了多少钱，手续费多少。)
                self.buy_prices[order_data_name] = order.executed.price
                # 将成交价格存储在对应数据源的 `self.buy_prices` 字典中。
                # (把买入的价格记在对应股票的 `self.buy_prices` 本子里。)
            elif order.issell():
                # 如果是卖出订单。
                # (如果这是一个卖单。)
                self.log(
                    f'SELL EXECUTED for {order_data_name} @ {order.executed.price:.2f}, Size: {order.executed.size}, Value: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}', data=order.data)
                # 记录卖出执行的详细日志，包括价格、数量、价值和佣金。
                # (就记个日志说卖出成功了，成交价多少，卖了多少股，收回多少钱，手续费多少。)

        elif order.status in [order.Canceled, order.Margin, order.Rejected, order.Expired]:
            # 如果订单状态是已取消 (Canceled)、保证金不足 (Margin)、被拒绝 (Rejected) 或已过期 (Expired)。
            # (如果订单被取消了、或者因为钱不够、或者被交易所拒绝了、或者过期了。)
            self.log(
                f'Order {order.ref} for {order_data_name} Canceled/Margin/Rejected/Expired: Status {order.getstatusname()}', data=order.data)
            # 记录订单未能成功执行的日志，并说明原因。
            # (就记个日志说这个订单没成功，具体是什么原因。)

        if self.orders.get(order_data_name) == order and not order.alive():
            # 如果 `self.orders` 中存储的对应数据源的订单是当前订单，并且当前订单不再存活 (即已完成、取消等)。
            # (如果之前记在 `self.orders` 本子里的这个股票的订单就是现在这个订单，并且这个订单已经结束了（比如成交了、取消了）。)
            self.orders[order_data_name] = None
            # 将 `self.orders` 中对应数据源的订单设置回 `None`，表示当前没有活动的主订单。
            # (就把 `self.orders` 本子里对应这个股票的记录清空，表示现在没有挂着的订单了。)

    def notify_trade(self, trade):
        # 定义 `notify_trade` 方法，当一笔交易完成 (开仓和平仓都已发生) 时由Backtrader调用。
        # (定义一个名叫 `notify_trade` 的函数，当一买一卖完整结束形成一笔交易后，`backtrader` 就会来告诉这个函数。)
        if not trade.isclosed:
            # 如果交易尚未关闭 (即只有开仓，没有平仓)。
            # (如果这笔交易还没结束，比如只买了还没卖。)
            return
            # 从方法返回，不处理未关闭的交易。
            # (那就先不管它，等卖了再说。)
        data_name = trade.data._name if hasattr(
            trade.data, '_name') else 'Unknown_Data'
        # 获取交易关联的数据源名称。
        # (看看这笔交易是哪个股票的。)
        self.log(
            f'OPERATION PROFIT for {data_name}, GROSS {trade.pnl:.2f}, NET {trade.pnlcomm:.2f}, Position Type: {self.position_types.get(data_name, "N/A")}', data=trade.data)
        # 记录交易的盈利情况 (毛利润和净利润) 以及该持仓的类型。
        # (记个日志说这笔交易赚了还是亏了多少钱（没算手续费的和算了手续费的），以及当初是按什么类型（趋势/区间）买的。)

        if data_name in self.position_types:
            # 如果 `self.position_types` 字典中存在该数据源的记录。
            # (如果 `self.position_types` 本子里有这个股票的记录。)
            self.position_types[data_name] = None
            # 将对应数据源的持仓类型重置为 `None`，因为交易已关闭。
            # (就把这个股票的持仓类型记录清空，因为已经卖掉了。)
        if data_name in self.buy_prices:
            # 如果 `self.buy_prices` 字典中存在该数据源的记录。
            # (如果 `self.buy_prices` 本子里有这个股票的记录。)
            self.buy_prices[data_name] = None
            # 将对应数据源的买入价格重置为 `None`。
            # (就把这个股票的买入价格记录清空。)

    def notify_cashvalue(self, cash, value):
        # 定义 `notify_cashvalue` 方法，当账户现金或总价值发生变化时由Backtrader调用。
        # (定义一个名叫 `notify_cashvalue` 的函数，每当账户里的现金或者总资产变化了，`backtrader` 就会来告诉这个函数。)
        self.high_water_mark = max(self.high_water_mark, value)
        # 更新 `high_water_mark` (历史最高账户价值) 为当前账户总价值与原记录中的较大者。
        # (看看现在的总资产是不是比以前最多的时候还要多，如果是，就更新一下记录。)
        drawdown = (self.high_water_mark - value) / \
            self.high_water_mark if self.high_water_mark > 1e-9 else 0
        # 计算当前的回撤百分比：(历史最高价值 - 当前价值) / 历史最高价值。如果历史最高价值接近0，则回撤为0。
        # (算一下从账户钱最多的时候到现在，回撤了多少百分比。如果以前账户就没啥钱，那就当没回撤。)

        if drawdown > self.params.drawdown_level2_threshold:
            # 如果当前回撤超过了二级回撤阈值 (例如10%)。
            # (如果回撤超过了咱们设定的二级警报线，比如10%。)
            if not self.halt_trading:
                # 如果当前尚未暂停交易。
                # (如果之前还没暂停交易。)
                self.log(
                    f'!!! RED ALERT: Drawdown {drawdown*100:.2f}% > {self.params.drawdown_level2_threshold*100:.0f}%. HALTING TRADING !!!')
                # 记录红色警报日志，说明回撤严重，将暂停交易。
                # (就记个红色警报日志，说亏得太多了，超过二级线了，要暂停交易！)
                self.halt_trading = True
                # 设置 `halt_trading` 标志为 `True`，暂停所有新的交易活动。
                # (把暂停交易的开关打开。)
        elif drawdown > self.params.drawdown_level1_threshold:
            # 如果当前回撤超过了一级回撤阈值但未超过二级阈值 (例如5%-10%)。
            # (如果回撤超过了一级警报线，但还没到二级那么严重，比如亏了5%但没到10%。)
            if not self.drawdown_level1_triggered:
                # 如果一级回撤警报尚未被触发过。
                # (如果之前一级警报还没响过。)
                self.log(
                    f'-- YELLOW ALERT: Drawdown {drawdown*100:.2f}% > {self.params.drawdown_level1_threshold*100:.0f}%. Reducing risk.--')
                # 记录黄色警报日志，说明回撤达到一级，将降低风险。
                # (就记个黄色警报日志，说亏损达到一级线了，要降低点风险。)
                self.drawdown_level1_triggered = True
                # 设置 `drawdown_level1_triggered` 标志为 `True`。
                # (把一级警报的标记打开，表示响过了。)
                self.current_risk_multiplier = 0.5
                # 将当前风险乘数减半 (例如从1.0降至0.5)，以减少后续交易的头寸规模。
                # (把风险调整系数减半，比如从1.0变成0.5，这样以后买股票就会少买点。)
        else:
            # 如果当前回撤低于一级回撤阈值 (例如小于5%)。
            # (如果回撤又回到一级警报线以下了，比如亏损小于5%了。)
            if self.halt_trading:
                # 如果之前是暂停交易状态。
                # (如果之前是暂停交易的状态。)
                self.log('--- Trading Resumed (Drawdown below Level 2) ---')
                # 记录日志，说明交易已恢复 (因为回撤已低于二级阈值)。
                # (记个日志说交易恢复了，因为亏损已经回到二级线以下了。)
                self.halt_trading = False
                # 将 `halt_trading` 标志设置回 `False`。
                # (把暂停交易的开关关掉。)
                if drawdown <= self.params.drawdown_level1_threshold:
                    # 如果回撤也低于一级阈值。
                    # (如果亏损也回到了一级线以下。)
                     if self.drawdown_level1_triggered:
                        # 如果一级回撤警报之前被触发过。
                        # (如果之前一级警报响过。)
                        self.log(
                            '--- Risk Level Restored (Drawdown below Level 1) ---')
                        # 记录日志，说明风险水平已恢复正常。
                        # (记个日志说风险水平恢复正常了。)
                        self.drawdown_level1_triggered = False
                        # 重置一级回撤触发标志。
                        # (把一级警报的标记关掉。)
                        self.current_risk_multiplier = 1.0
                        # 将风险乘数恢复到1.0。
                        # (把风险调整系数恢复到1.0。)
                elif self.drawdown_level1_triggered:
                    # 如果回撤在1级和2级之间，但交易已恢复（说明之前是halt_trading=True）
                    # (如果亏损在一级线和二级线之间，但交易已经恢复了（说明之前是暂停交易状态）)
                    self.current_risk_multiplier = 0.5
                    # 风险乘数保持在0.5。
                    # (风险调整系数还是保持0.5。)
            elif self.drawdown_level1_triggered and drawdown <= self.params.drawdown_level1_threshold:
                 # 如果之前一级回撤警报被触发过，且当前回撤已低于一级阈值 (且之前未暂停交易)。
                # (如果之前一级警报响过，现在亏损回到一级线以下了，并且之前没有暂停交易。)
                self.log('--- Risk Level Restored (Drawdown below Level 1) ---')
                # 记录日志，说明风险水平已恢复正常。
                # (记个日志说风险水平恢复正常了。)
                self.drawdown_level1_triggered = False
                # 重置一级回撤触发标志。
                # (把一级警报的标记关掉。)
                self.current_risk_multiplier = 1.0
                # 将风险乘数恢复到1.0。
                # (把风险调整系数恢复到1.0。)

    # REMOVE _calculate_trade_size method from strategy

    def next(self):
        # 定义 `next` 方法，每个新的K线数据到达时由Backtrader调用。
        # (定义一个名叫 `next` 的函数，每当有新的一根K线数据来了，`backtrader` 就会运行一次这个函数。)
        if self.halt_trading:
            # 如果 `halt_trading` 标志为 `True` (即交易已暂停)。
            # (如果现在是暂停交易状态。)
            for d_obj in self.datas:
                # 遍历所有数据源 (例如所有ETF)。
                # (检查我们关注的每一只ETF。)
                d_name = d_obj._name
                # 获取数据源的名称。
                # (拿到这只ETF的名字。)
                position = self.getposition(d_obj)
                # 获取该数据源的当前持仓情况。
                # (看看手上有没有这只ETF。)
                order = self.orders.get(d_name)
                # 获取该数据源的当前活动订单。
                # (看看有没有给这只ETF挂着的单子。)
                if position.size != 0 and not order:
                    # 如果持有该ETF的仓位，并且没有活动的订单 (意味着没有正在进行的平仓操作)。
                    # (如果手上还拿着这只ETF，并且没有正在卖的单子。)
                    self.log(
                        f'HALTED: Attempting to close position for {d_name} Size: {position.size}', data=d_obj)
                    # 记录日志，说明因交易暂停而尝试平仓。
                    # (记个日志说因为暂停交易了，要赶紧把手上的这只ETF卖掉。)
                    order_close = self.close(data=d_obj)
                    # 发出市价平仓订单。
                    # (下一个卖出指令，把这只ETF卖掉。)
                    if order_close:
                        # 如果成功创建平仓订单。
                        # (如果卖出指令成功发出去了。)
                        self.orders[d_name] = order_close
                        # 将平仓订单存储在 `self.orders` 中。
                        # (就把这个卖单记在 `self.orders` 本子里。)
                    else:
                        # 如果未能创建平仓订单。
                        # (如果卖出指令没发出去。)
                        self.log(
                            f'HALTED: Failed to create close order for {d_name}', data=d_obj)
                        # 记录日志，说明平仓失败。
                        # (记个日志说卖单没发出去。)
            return
            # 从 `next` 方法返回，不执行任何其他交易逻辑。
            # (暂停交易状态下，除了平仓，其他啥也不干了。)

        for i, d_obj in enumerate(self.datas):
            # 遍历所有数据源及其索引。
            # (按顺序检查我们关注的每一只ETF。)
            d_name = d_obj._name
            # 获取当前数据源的名称。
            # (拿到这只ETF的名字。)
            position = self.getposition(d_obj)
            # 获取当前数据源的持仓情况。
            # (看看手上有没有这只ETF。)
            order = self.orders.get(d_name)
            # 获取当前数据源的活动订单。
            # (看看有没有给这只ETF挂着的单子。)

            if order:
                # 如果当前数据源有活动订单。
                # (如果这只ETF有正在处理的订单。)
                continue
                # 跳过此数据源，处理下一个。因为通常不希望在有未完成订单时再下新单。
                # (那就先不看它了，等订单处理完了再说，免得重复下单。)

            if position.size == 0:  # No position, check for entry
                # 如果当前数据源没有持仓 (即 `position.size` 为0)，则检查入场信号。
                # (如果手上没有这只ETF，那就看看有没有机会买入。)
                market_state = 'UNCERTAIN_DO_NOT_TRADE'
                # 初始化市场状态为 'UNCERTAIN_DO_NOT_TRADE' (不确定，不交易)。
                # (先假设市场情况不明朗，不适合交易。)
                current_close = self.closes[d_name][0]
                # 获取当前K线的收盘价。
                # (拿到这只ETF当前这根K线的收盘价。)
                current_open = self.opens[d_name][0]
                # 获取当前K线的开盘价。
                # (拿到这只ETF当前这根K线的开盘价。)
                current_low = self.lows[d_name][0]
                # 获取当前K线的最低价。
                # (拿到这只ETF当前这根K线的最低价。)
            current_volume = self.volumes[d_name][0]
                # 获取当前K线的成交量。
                # (拿到这只ETF当前这根K线的成交量。)

            ema_medium_val = self.emas_medium[d_name][0]
                # 获取中期EMA的当前值。
                # (拿到这只ETF的中期均线现在的值。)
            ema_medium_prev = self.emas_medium[d_name][-1]
                # 获取中期EMA的前一个值。
                # (拿到这只ETF的中期均线上一个周期的值。)
            ema_long_val = self.emas_long[d_name][0]
                # 获取长期EMA的当前值。
                # (拿到这只ETF的长期均线现在的值。)
            ema_long_prev = self.emas_long[d_name][-1]
                # 获取长期EMA的前一个值。
                # (拿到这只ETF的长期均线上一个周期的值。)
            adx_val = self.adxs[d_name].adx[0]
                # 获取ADX指标的当前值。
                # (拿到这只ETF的ADX指标现在的值。)
            bb_top = self.bbands[d_name].top[0]
                # 获取布林带上轨的当前值。
                # (拿到这只ETF的布林带上轨现在的值。)
            bb_bot = self.bbands[d_name].bot[0]
                # 获取布林带下轨的当前值。
                # (拿到这只ETF的布林带下轨现在的值。)
            bb_mid = self.bbands[d_name].mid[0]
                # 获取布林带中轨的当前值。
                # (拿到这只ETF的布林带中轨现在的值。)
            rsi_val = self.rsis[d_name][0]
                # 获取RSI指标的当前值。
                # (拿到这只ETF的RSI指标现在的值。)
            highest_high_prev = self.highest_highs[d_name][-1]
                # 获取前一周期内N日最高价的值。
                # (拿到这只ETF在之前一段时间里的最高价。)
            sma_volume_val = self.sma_volumes[d_name][0]
                # 获取成交量SMA的当前值。
                # (拿到这只ETF的成交量均线现在的值。)
                atr_val = self.atrs[d_name][0]
                # 获取ATR指标的当前值。
                # (拿到这只ETF的ATR指标现在的值。)

                try:
                    # 尝试执行以下可能因数据不足而引发 `IndexError` 的代码。
                    # (试试看下面的判断，如果数据不够可能会出错。)
                is_trend_up = (current_close > ema_medium_val > ema_long_val and
                               ema_medium_val > ema_medium_prev and
                               ema_long_val > ema_long_prev)
                    # 判断是否为上升趋势：收盘价 > 中期EMA > 长期EMA，且中期EMA和长期EMA均在上升。
                    # (判断是不是上升趋势：收盘价比中期均线高，中期均线比长期均线高，而且两条均线都在往上走。)

                is_range_confirmed = (not is_trend_up and
                                      abs(ema_medium_val / ema_medium_prev - 1) < 0.003 and
                                      abs(ema_long_val / ema_long_prev - 1) < 0.003 and
                                      adx_val < 20 and
                                      (bb_top - bb_bot) / current_close < 0.07 if current_close > 1e-9 else False)
                    # 判断是否为区间震荡：非上升趋势，中期和长期EMA变化平缓，ADX < 20，且布林带宽度占收盘价比例小于7%。
                    # (判断是不是区间震荡：首先不能是上升趋势，然后两条均线变化不大（几乎是平的），ADX指标小于20（表示趋势不强），并且布林带的上下轨之间的宽度相对于价格来说比较窄。)

                if is_trend_up:
                        # 如果是上升趋势。
                        # (如果是上升趋势。)
                    market_state = 'TREND_UP'
                        # 将市场状态设置为 'TREND_UP'。
                        # (就把市场状态改成 'TREND_UP'。)
                    elif is_range_confirmed and self.p.etf_type == 'range':  # Use self.p for strategy params
                        # 如果是区间震荡，并且策略参数 `etf_type` 设置为 'range'。
                        # (如果是区间震荡，并且咱们策略设置的是针对 'range' 区间型的ETF。)
                    market_state = 'RANGE_CONFIRMED'
                        # 将市场状态设置为 'RANGE_CONFIRMED'。
                        # (就把市场状态改成 'RANGE_CONFIRMED'。)
            except IndexError:
                    # 如果在访问指标历史数据时发生 `IndexError` (通常在回测初期数据不足时)。
                    # (如果因为数据不够，上面的判断出错了。)
                    continue
                    # 跳过当前K线，处理下一个。
                    # (那就先不管这根K线了，等数据够了再说。)

            entry_signal = False
                # 初始化入场信号为 `False`。
                # (先假设没有买入信号。)
            potential_position_type = None
                # 初始化潜在持仓类型为 `None`。
                # (先假设不知道要按什么类型买。)
                limit_entry_price_calc = current_close
                # 初始化计算用的限价入场价格为当前收盘价。
                # (先假设用现在的收盘价作为参考的买入价。)

                stop_loss_price_calc = None
                # 初始化计算用的止损价格为 `None`。
                # (先假设不知道止损价设在哪里。)
                take_profit_price_calc = None
                # 初始化计算用的止盈价格为 `None`。
                # (先假设不知道止盈价设在哪里。)
                # risk_per_trade_percent is now handled by Sizer based on etf_type

            if market_state == 'TREND_UP' and self.p.etf_type == 'trend':
                    # 如果市场状态为上升趋势，并且策略参数 `etf_type` 设置为 'trend'。
                    # (如果市场是上升趋势，并且咱们策略设置的是针对 'trend' 趋势型的ETF。)
                try:
                        # 尝试执行趋势交易的信号判断。
                        # (试试看趋势交易的买入条件。)
                    is_breakout = (current_close > highest_high_prev and
                                   current_volume > sma_volume_val * self.params.trend_volume_ratio_min)
                        # 判断是否为突破信号：当前收盘价创近期新高，并且成交量放大。
                        # (判断是不是突破了：现在的价格比之前一段时间的最高价还高，并且成交量也比平均成交量大不少。)
                    is_pullback = (min(abs(current_low / ema_medium_val - 1), abs(current_low / ema_long_val - 1)) < 0.01 and
                                   current_close > current_open) if ema_medium_val > 1e-9 and ema_long_val > 1e-9 else False
                        # 判断是否为回调信号：当前最低价接近中期或长期EMA (回调到均线附近)，并且当天收阳线。
                        # (判断是不是回调买入机会：价格跌到中期均线或者长期均线附近了，并且当天是涨的（收盘价比开盘价高）。)

                    if is_breakout or is_pullback:
                            # 如果是突破信号或回调信号。
                            # (如果满足突破条件或者回调条件。)
                        entry_signal = True
                            # 设置入场信号为 `True`。
                            # (那就认为有买入信号了。)
                        potential_position_type = 'trend'
                            # 设置潜在持仓类型为 'trend'。
                            # (这次买入是按趋势型来操作的。)
                            stop_loss_price_calc = current_close - self.p.trend_stop_loss_atr_mult * atr_val
                            # 计算止损价格：当前收盘价 - ATR倍数 * ATR值。
                            # (算一下止损价：用现在的收盘价减去几倍的ATR。)
                            if stop_loss_price_calc < current_close:
                                # 如果计算出的止损价低于当前收盘价 (有效止损)。
                                # (如果算出来的止损价比现在的收盘价低，这是个有效的止损。)
                                risk_per_share_calc = current_close - stop_loss_price_calc
                                # 计算每股风险。
                                # (算一下每股的风险是多少。)
                                if risk_per_share_calc > 1e-9:
                                    # 如果每股风险大于一个极小值 (避免除以0)。
                                    # (如果每股风险不是太小，避免计算问题。)
                                    take_profit_price_calc = current_close + \
                                        self.p.trend_take_profit_rratio * risk_per_share_calc
                                    # 计算止盈价格：当前收盘价 + 风险回报比 * 每股风险。
                                    # (算一下止盈价：用现在的收盘价加上风险回报比乘以每股风险。)
                        else:
                                    # 如果每股风险过小。
                                    # (如果每股风险太小了。)
                                entry_signal = False
                                    # 取消入场信号。
                                    # (那就不买了。)
                            else:
                                # 如果计算出的止损价不低于当前收盘价 (无效止损)。
                                # (如果算出来的止损价比收盘价还高，这个止损没意义。)
                                    entry_signal = False
                                # 取消入场信号。
                                # (那就不买了。)
                except IndexError:
                        # 如果发生 `IndexError`。
                        # (如果数据不够出错了。)
                        continue
                        # 跳过。
                        # (那就先不管。)

            elif market_state == 'RANGE_CONFIRMED' and self.p.etf_type == 'range':
                    # 如果市场状态为区间震荡，并且策略参数 `etf_type` 设置为 'range'。
                    # (如果市场是区间震荡，并且咱们策略设置的是针对 'range' 区间型的ETF。)
                try:
                        # 尝试执行区间交易的信号判断。
                        # (试试看区间交易的买入条件。)
                    is_range_buy = (current_low <= bb_bot and
                                    current_close > bb_bot and
                                    rsi_val < self.params.rsi_oversold)
                        # 判断是否为区间买入信号：最低价触及或跌破布林带下轨，收盘价回到下轨之上，且RSI处于超卖区。
                        # (判断是不是区间买入机会：价格碰到或者跌破布林带下轨了，然后收盘的时候又回到下轨上面，并且RSI指标显示超卖了。)
                    if is_range_buy:
                            # 如果是区间买入信号。
                            # (如果满足区间买入条件。)
                        entry_signal = True
                            # 设置入场信号为 `True`。
                            # (那就认为有买入信号了。)
                        potential_position_type = 'range'
                            # 设置潜在持仓类型为 'range'。
                            # (这次买入是按区间型来操作的。)
                            stop_loss_price_calc = current_low * \
                                (1 - self.p.range_stop_loss_buffer)
                            # 计算止损价格：当前最低价 * (1 - 止损缓冲百分比)。
                            # (算一下止损价：用现在的最低价再往下浮动一点点。)
                            take_profit_price_calc = bb_mid
                            # 设置止盈价格为布林带中轨。
                            # (止盈目标就设在布林带的中轨。)
                            if stop_loss_price_calc >= limit_entry_price_calc:
                                # 如果计算出的止损价不低于限价入场价 (无效止损)。
                                # (如果算出来的止损价比参考买入价还高，这个止损没意义。)
                            entry_signal = False
                                # 取消入场信号。
                                # (那就不买了。)
                except IndexError:
                        # 如果发生 `IndexError`。
                        # (如果数据不够出错了。)
                        continue
                        # 跳过。
                        # (那就先不管。)

                if entry_signal and stop_loss_price_calc is not None and limit_entry_price_calc > stop_loss_price_calc:
                    # 如果有入场信号，且止损价已计算，且限价入场价高于止损价 (确保有盈利空间和有效止损)。
                    # (如果前面判断有买入信号，止损价也算出来了，并且参考买入价比止损价高（这样才有意义）。)
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
                    # 记录买入信号日志，包括计划的限价入场价、止损价、止盈价和持仓类型。
                    # (记个日志说有买入信号了，计划用什么价格买，止损设在哪，止盈设在哪，是什么类型的交易。)

                    main_order_limit_price = limit_entry_price_calc
                    # 设置主订单的限价为计算出的限价入场价。
                    # (把主买单的限价就设成咱们参考的买入价。)

                    tp_price_for_bracket = take_profit_price_calc if take_profit_price_calc and take_profit_price_calc > main_order_limit_price else None
                    # 设置括号单的止盈价格：如果计算出的止盈价有效 (存在且高于入场价)，则使用它；否则为 `None`。
                    # (设置括号单的止盈价：如果算出来的止盈价有效（存在并且比买入价高），就用它；否则就没有止盈价。)

                    if tp_price_for_bracket is None and potential_position_type == 'trend':
                        # 如果趋势型交易没有有效的止盈价。
                        # (如果是趋势交易，但是没算出来有效的止盈价。)
                        self.log(
                            f'Warning for {d_name}: TP price for trend trade is None or invalid. Bracket will not have a limit sell.', data=d_obj)
                        # 记录警告日志，说明趋势交易的括号单将没有止盈限价卖出单。
                        # (记个警告说趋势交易的止盈价有问题，这次的括号单可能没有自动止盈的功能了。)

                    # Call buy_bracket WITHOUT size. Sizer will determine it.
                bracket_orders_list = self.buy_bracket(
                    data=d_obj,
                        # 指定数据源。
                        # (告诉它是针对哪个ETF的。)
                    # size= REMOVED - Sizer will handle this
                        price=main_order_limit_price,
                        # 设置主订单的限价。
                        # (告诉它主买单的限价是多少。)
                    exectype=bt.Order.Limit,
                        # 设置主订单的执行类型为限价单。
                        # (告诉它主买单是限价单。)
                        stopprice=stop_loss_price_calc,
                        # 设置止损订单的触发价格。
                        # (告诉它止损单的触发价是多少。)
                        limitprice=tp_price_for_bracket,
                        # 设置止盈订单的限价 (如果有效)。
                        # (告诉它止盈单的限价是多少（如果算出来了的话）。)
                    )
                    # 调用 `buy_bracket` 方法下达括号订单 (一个限价买入主订单，附带一个止损卖出订单和一个可选的止盈限价卖出订单)。
                    # (下一个括号单：一个限价买入单，如果买成功了，会自动带上一个止损卖出单和一个（可选的）止盈卖出单。这里不指定买多少股，让Sizer去算。)

                if bracket_orders_list and bracket_orders_list[0]:
                    # 如果成功创建了括号订单列表，并且列表中的第一个订单 (主订单) 存在。
                        # (如果括号单成功发出去了，并且主买单是有的。)
                        self.orders[d_name] = bracket_orders_list[0]
                        # 将主订单存储在 `self.orders` 中。
                        # (就把这个主买单记在 `self.orders` 本子里。)
                        self.position_types[d_name] = potential_position_type
                        # 将潜在持仓类型存储在 `self.position_types` 中。
                        # (把这次买入的类型（趋势/区间）记在 `self.position_types` 本子里。)
                else:
                    # 如果未能成功创建括号订单 (例如Sizer返回0股，或发生错误)。
                        # (如果括号单没发出去，可能是Sizer算出来买0股，或者其他错误。)
                        self.log(
                            f'Failed to create buy_bracket order for {d_name} (possibly sizer returned 0 or error)', data=d_obj)
                        # 记录日志，说明创建括号订单失败。
                        # (记个日志说括号单没成功发出去。)


def load_data_to_cerebro(cerebro, data_files, column_mapping, openinterest_col, fromdate, todate):
    # 定义 `load_data_to_cerebro` 函数，用于将Excel数据文件加载到Cerebro引擎中。
    # (定义一个名叫 `load_data_to_cerebro` 的函数，专门负责把Excel表格里的股票数据读到 `backtrader` 的大脑（Cerebro）里。)
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
    # 函数的文档字符串，解释其功能、参数和返回值。
    # (这是函数的说明书，告诉别人这个函数是干嘛的，需要什么，会返回什么。)
    print("开始加载数据...")
    # 打印提示信息，表示开始加载数据。
    # (在屏幕上打一行字，告诉用户"开始加载数据啦..."。)
    loaded_data_count = 0  # 计数器，用于记录成功加载的数据数量
    # 初始化一个计数器 `loaded_data_count` 为0，用于记录成功加载了多少个数据文件。
    # (准备一个计数本 `loaded_data_count`，一开始是0，用来记成功加载了几个文件。)
    for file_path in data_files:
        # 遍历 `data_files` 列表中的每个文件路径。
        # (一个一个地看 `data_files` 列表里的文件路径。)
        try:
            # 开始一个 `try` 代码块，用于捕获和处理在加载单个文件时可能发生的异常。
            # (试试看下面的操作，如果出错了就跳到 `except` 部分处理。)
            dataframe = pd.read_excel(file_path)
            # 使用 `pandas` 库的 `read_excel` 函数读取指定路径的Excel文件，并将其内容存储为一个DataFrame对象。
            # (用 `pandas` 这个工具打开Excel文件，把里面的数据读出来存到 `dataframe` 里。)
            dataframe.rename(columns=column_mapping, inplace=True)
            # 使用 `column_mapping` 字典重命名DataFrame的列名，使其符合Backtrader对列名的期望 (例如，将中文列名'日期'映射为'datetime')。`inplace=True`表示直接修改原DataFrame。
            # (把Excel表格里原来的列名（比如"开盘"）按照 `column_mapping` 的规则改成 `backtrader` 认识的名字（比如"open"），`inplace=True` 的意思是直接在原来的数据上改。)
            if 'datetime' in dataframe.columns:
                # 检查重命名后的DataFrame列中是否包含 'datetime' 列。
                # (看看改完名字后，有没有一列叫 'datetime'。)
                try:
                    # 尝试将 'datetime' 列的数据转换为pandas的datetime对象。
                    # (试试看把 'datetime' 这一列的文字（比如 "2023-01-01"）变成电脑能认的日期时间格式。)
                    dataframe['datetime'] = pd.to_datetime(
                        dataframe['datetime'])
                    # 将 'datetime' 列转换为pandas的datetime对象。
                    # (把 'datetime' 这一列的文字（比如 "2023-01-01"）变成电脑能认的日期时间格式。)
                except Exception as e:
                    # 如果在转换日期时间格式时发生任何异常。
                    # (如果转换日期的时候出错了。)
                    print(f"警告: 无法解析 {file_path} 中的日期时间列，请检查格式。错误: {e}")
                    # 打印警告信息，指出哪个文件的日期时间列无法解析，并显示具体的错误信息。
                    # (在屏幕上打个警告，说哪个文件的日期格式不对，具体错在哪。)
                    continue
                    # 跳过当前文件的剩余处理步骤，继续处理列表中的下一个文件。
                    # (这个文件日期有问题，就不处理它了，去看下一个文件。)
            else:
                # 如果重命名后的DataFrame列中不包含 'datetime' 列。
                # (如果改完名字后，还是没有一列叫 'datetime'。)
                print(
                    f"错误: 在 {file_path} 中找不到映射后的 'datetime' 列。请确保Excel文件中有正确的日期列，或正确修改脚本中的column_mapping。")
                # 打印错误信息，指出哪个文件缺少 'datetime' 列，并提示用户检查文件或映射配置。
                # (在屏幕上打个错误提示，说哪个文件里找不到 'datetime' 这一列，让用户检查一下Excel或者改列名的规则。)
                # 增加打印原始列名
                # (增加打印原始列名)
                print(f"Excel文件中的原始列名是: {dataframe.columns.tolist()}")
                # 打印该Excel文件中的原始列名列表，帮助用户诊断问题。
                # (把这个Excel文件里原来的列名都打出来，方便用户看看是哪里不对。)
                continue
                # 跳过当前文件的剩余处理步骤。
                # (这个文件有问题，不处理了。)
            dataframe.set_index('datetime', inplace=True)
            # 将 'datetime' 列设置为DataFrame的索引，这是Backtrader处理时间序列数据的标准做法。
            # (把 'datetime' 这一列作为表格的行标签（索引），`backtrader` 就知道怎么按时间顺序处理数据了。)
            required_cols = ['open', 'high', 'low', 'close', 'volume']
            # 定义一个列表 `required_cols`，包含Backtrader进行回测所必需的列名 (开盘价, 最高价, 最低价, 收盘价, 成交量)。
            # (定一个单子 `required_cols`，写上 `backtrader` 必须有的几列数据：开盘价、最高价、最低价、收盘价、成交量。)
            if not all(col in dataframe.columns for col in required_cols):
                # 检查DataFrame的列中是否包含了所有 `required_cols` 中定义的必需列。
                # (看看表格里是不是把上面单子里的这几列都凑齐了。)
                print(f"错误: {file_path} 映射后缺少必需的列。")
                # 如果缺少必需列，则打印错误信息。
                # (如果没凑齐，就打个错误提示，说哪个文件缺东西了。)
                print(f"可用的列: {dataframe.columns.tolist()}")
                # 打印当前DataFrame中实际存在的列名，帮助用户定位问题。
                # (把这个文件里现在有的列名都打出来，让用户看看缺了哪个。)
                continue
                # 跳过当前文件的剩余处理步骤。
                # (这个文件数据不全，不处理了。)
            dataframe = dataframe.loc[fromdate:todate]
            # 使用 `.loc` 索引筛选DataFrame，只保留 `fromdate` 和 `todate` (包含边界) 指定日期范围内的数据。
            # (从表格里选出从 `fromdate` 到 `todate` 这段时间的数据，其他时间的数据不要。)

            # 检查数据是否为空
            # (检查数据是否为空)
            if dataframe.empty:
                # 如果筛选后的DataFrame为空 (即指定日期范围内没有数据)。
                # (如果选完之后发现这段时间里啥数据都没有。)
                print(f"警告: {file_path} 在指定日期范围内没有数据。")
                # 打印警告信息。
                # (就打个警告，说这个文件在这段时间里没数据。)
                continue  # 跳过空数据
                # 跳过当前文件，继续处理下一个。
                # (这个文件没数据，跳过。)

            data = bt.feeds.PandasData(dataname=dataframe, fromdate=fromdate, todate=todate, datetime=None,
                                       open='open', high='high', low='low', close='close', volume='volume', openinterest=openinterest_col)
            # 使用 `bt.feeds.PandasData` 类将处理好的DataFrame转换为Backtrader可以识别的数据源 (feed)。
            # 参数指定了DataFrame本身、日期范围以及OHLCV和可选的持仓量列名。`datetime=None` 表示索引已是datetime类型。
            # (把整理好的 `dataframe` 数据喂给 `backtrader`，让它变成 `backtrader` 认识的数据格式。告诉它哪个是开盘价、最高价等等，还有时间范围。)
            data_name = os.path.basename(file_path).split('.')[0]
            # 从文件路径中提取文件名 (不含扩展名) 作为该数据源的名称。例如，从 'path/to/510050_d.xlsx' 提取 '510050_d'。
            # (从文件路径里把文件名（比如 "510050_d"）拿出来，作为这个数据的名字。)
            cerebro.adddata(data, name=data_name)
            # 将创建的数据源 `data` 添加到Cerebro引擎实例中，并赋予其名称 `data_name`。
            # (把这个准备好的数据源 `data` 加到 `backtrader` 的大脑 `cerebro` 里，并给它取个名字 `data_name`。)
            print(f"数据加载成功: {data_name}")
            # 打印数据加载成功的提示信息。
            # (在屏幕上打一行字，告诉用户这个数据加载成功了。)
            loaded_data_count += 1  # 增加成功加载的计数
            # 成功加载的数据文件计数器加1。
            # (在成功加载的计数本上加一笔。)

        except FileNotFoundError:
            # 如果在 `pd.read_excel(file_path)` 时发生 `FileNotFoundError` 异常 (即文件不存在)。
            # (如果 `try` 里面的操作中，发现文件找不到了。)
            print(f"错误: 文件未找到 {file_path}")
            # 打印文件未找到的错误信息。
            # (就打个错误提示，说哪个文件没找到。)
        except Exception as e:
            # 捕获在处理单个文件过程中可能发生的其他所有类型的异常。
            # (如果 `try` 里面的操作中，发生了其他类型的错误。)
            print(f"加载数据 {file_path} 时出错: {e}")
            # 打印加载数据时发生错误的具体信息，包括文件名和异常对象 `e`。
            # (就打个错误提示，说加载哪个文件的时候出错了，具体错在哪。)
    return loaded_data_count
    # 函数执行完毕后，返回成功加载的数据源总数。
    # (最后告诉调用这个函数的地方，总共成功加载了多少个文件。)

# ===================================================================================
# 结果处理和评分函数 (Result Processing and Scoring Function)
# (这是一条注释，说明下面的代码是关于结果处理和评分的函数。)
# (下面这块代码是用来分析回测跑完之后的结果，并且给不同的参数组合打分的。)
# ===================================================================================


def analyze_optimization_results(results):
    # 定义 `analyze_optimization_results` 函数，用于分析参数优化的结果。
    # (定义一个名叫 `analyze_optimization_results` 的函数，专门用来分析参数优化跑出来的结果。)
    """
    分析优化结果，计算归一化得分并找到最优参数。
    Analyzes optimization results, calculates normalized scores, and finds the best parameters.

    Args:
        results (list): cerebro.run() 返回的优化结果列表。 (List of optimization results returned by cerebro.run().)

    Returns:
        tuple: 包含最佳策略实例和所有结果得分的元组。 (Tuple containing the best strategy instance and scores for all results.)
               如果无法处理，则返回 (None, [])。 (Returns (None, []) if results cannot be processed.)
    """
    # 函数的文档字符串，解释其功能、参数和返回值。
    # (这是函数的说明书，告诉别人这个函数是干嘛的，需要什么，会返回什么。)
    if not results:
        # 检查传入的 `results` 列表是否为空。
        # (看看传进来的 `results` 是不是空的，啥都没有。)
        print("\n{:!^50}".format(' 错误 '))
        # 打印一个居中对齐、用'!'填充的错误标题。
        # (在屏幕上打一个醒目的错误标题。)
        print("没有策略成功运行。请检查数据加载是否有误或参数范围是否有效。")
        # 打印错误信息，提示用户可能的原因。
        # (告诉用户可能是因为没有策略跑成功，让他们检查下数据或者参数设置。)
        print('!' * 50)
        # 打印一行'!'作为分隔线。
        # (再打一行感叹号，把错误信息框起来。)
        return None, []  # 返回空结果
        # 如果结果为空，则返回 `None` (表示没有最佳结果) 和一个空列表 (表示没有评分结果)。
        # (既然没结果，就返回一个空的东西。)

    processed_results = []
    # 初始化一个空列表 `processed_results`，用于存储从原始结果中提取并处理过的数据。
    # (准备一个空本子 `processed_results`，用来记录整理好的结果。)

    print("\n--- 开始提取分析结果 ---")
    # 打印提示信息，表示开始提取分析结果。
    # (在屏幕上打一行字，告诉用户"开始提取分析结果啦---"。)
    for strat_list in results:  # optreturn=False时，results是列表的列表
        # 遍历 `results` 列表中的每个元素。当 `optreturn=False` 时，`results` 是一个包含策略实例列表的列表。
        # (一个一个地看 `results` 里面的每一组成绩。因为 `optreturn=False`，所以 `results` 里面是一堆列表，每个列表里装着一次回测的策略。)
        if not strat_list:
            # 如果当前 `strat_list` 为空。
            # (如果这一组是空的。)
            continue  # 跳过空列表
            # 跳过当前迭代，处理下一个 `strat_list`。
            # (那就跳过，看下一组。)
        strategy_instance = strat_list[0]  # 获取策略实例
        # 从 `strat_list` 中获取第一个元素，即策略实例。
        # (从这一组里拿出第一个，也就是那个策略本身。)
        params = strategy_instance.params  # 获取参数
        # 获取该策略实例的参数对象。
        # (拿到这个策略当时用的参数设置。)
        analyzers = strategy_instance.analyzers  # 获取分析器
        # 获取该策略实例的分析器集合。
        # (拿到这个策略跑完之后得到的各种分析结果，比如夏普率、收益率这些。)

        try:
            # 开始一个 `try` 代码块，用于处理在获取分析结果时可能发生的错误。
            # (试试看下面的操作，如果出错了就跳到 `except` 部分处理。)
            # 尝试获取分析结果
            # (尝试获取分析结果)
            sharpe_analysis = analyzers.sharpe_ratio.get_analysis()
            # 从分析器中获取名为 'sharpe_ratio' 的分析器的分析结果。
            # (从分析结果里找到夏普比率的分析数据。)
            returns_analysis = analyzers.returns.get_analysis()
            # 获取名为 'returns' 的分析器的分析结果。
            # (找到收益率的分析数据。)
            drawdown_analysis = analyzers.drawdown.get_analysis()
            # 获取名为 'drawdown' 的分析器的分析结果。
            # (找到最大回撤的分析数据。)

            # 检查分析结果是否有效且包含所需键
            # (检查分析结果是否有效且包含所需键)
            if not sharpe_analysis or 'sharperatio' not in sharpe_analysis:
                # 如果夏普比率分析结果为空或不包含 'sharperatio' 键。
                # (如果夏普比率的数据是空的，或者里面没有 'sharperatio' 这个项目。)
                print(f"警告: 参数组 {params.ema_medium_period}, {params.ema_long_period}, {params.bbands_period}, {params.bbands_devfactor} 的夏普比率分析结果不完整或为None，跳过。Sharpe: {sharpe_analysis}")
                # 打印警告信息，并跳过当前参数组。
                # (就打个警告，说这组参数的夏普比率数据有问题，跳过不处理了。)
                continue
                # (跳过。)
            if not returns_analysis or 'rtot' not in returns_analysis:
                # 如果收益率分析结果为空或不包含 'rtot' (总收益率) 键。
                # (如果收益率的数据是空的，或者里面没有 'rtot' 这个项目。)
                print(f"警告: 参数组 {params.ema_medium_period}, {params.ema_long_period}, {params.bbands_period}, {params.bbands_devfactor} 的收益率分析结果不完整，跳过。Returns: {returns_analysis}")
                # 打印警告信息，并跳过。
                # (就打个警告，说这组参数的收益率数据有问题，跳过不处理了。)
                continue
                # (跳过。)
            if not drawdown_analysis or 'max' not in drawdown_analysis or 'drawdown' not in drawdown_analysis.max:
                # 如果最大回撤分析结果为空，或其 'max' 字典为空，或 'max' 字典中不包含 'drawdown' 键。
                # (如果最大回撤的数据是空的，或者里面没有 'max' 这个项目，或者 'max' 里面又没有 'drawdown' 这个项目。)
                print(f"警告: 参数组 {params.ema_medium_period}, {params.ema_long_period}, {params.bbands_period}, {params.bbands_devfactor} 的最大回撤分析结果不完整，跳过。Drawdown: {drawdown_analysis}")
                # 打印警告信息，并跳过。
                # (就打个警告，说这组参数的最大回撤数据有问题，跳过不处理了。)
                continue
                # (跳过。)

            sharpe = sharpe_analysis.get(
                'sharperatio', 0.0)  # Sharpe Ratio 可能为 None
            # 从夏普比率分析结果中获取 'sharperatio' 的值，如果不存在或为 `None`，则默认为0.0。
            # (从夏普比率数据里拿出 'sharperatio' 的值，如果找不到或者它是空的，就当它是0.0。)
            if sharpe is None:
                # 再次检查 `sharpe` 是否为 `None` (以防 `get` 方法返回 `None` 而不是默认值)。
                # (再确认一下，如果 `sharpe` 还是空的。)
                sharpe = 0.0  # 再次确认
                # 将 `sharpe` 设为0.0。
                # (那就把它设成0.0。)
            total_return = returns_analysis.get('rtot', 0.0)  # 总收益率（小数）
            # 从收益率分析结果中获取 'rtot' (总收益率，以小数形式表示) 的值，默认为0.0。
            # (从收益率数据里拿出 'rtot'（总收益率，是小数形式）的值，如果找不到就当它是0.0。)
            max_drawdown = drawdown_analysis.max.get(
                'drawdown', 0.0) / 100.0  # 最大回撤（转换为小数）
            # 从最大回撤分析结果的 'max' 字典中获取 'drawdown' 的值 (通常是百分比)，除以100转换为小数形式，默认为0.0。
            # (从最大回撤数据里拿出 'drawdown' 的值（通常是个百分数），然后除以100变成小数，如果找不到就当它是0.0。)

            # Create a dictionary from the params object for easy access and printing
            # (创建一个字典，方便地从参数对象中读取和打印参数。)
            current_params_dict = {}
            # 初始化一个空字典 `current_params_dict`，用于存储当前策略实例的参数键值对。
            # (准备一个空字典 `current_params_dict`，用来放当前这组参数的具体值。)
            optimized_param_names = [
                'etf_type', 'ema_medium_period', 'ema_long_period',
                'bbands_period', 'bbands_devfactor', 'trend_stop_loss_atr_mult'
            ]
            # 定义一个列表 `optimized_param_names`，包含所有参与优化的参数名称。
            # (列出所有我们关心的、参与了优化的参数的名字。)
            for p_name in optimized_param_names:
                # 遍历 `optimized_param_names` 列表中的每个参数名。
                # (一个一个地看这些参数名。)
                if hasattr(params, p_name):
                    # 检查当前策略的参数对象 `params` 是否具有名为 `p_name` 的属性。
                    # (看看这个策略的参数设置里有没有这个名字的参数。)
                    current_params_dict[p_name] = getattr(params, p_name)
                    # 如果有，则获取该参数的值，并存入 `current_params_dict`。
                    # (如果有，就把它的值取出来，放到 `current_params_dict` 字典里。)
                else:
                    # 如果参数对象中没有该属性。
                    # (如果没有这个参数。)
                    current_params_dict[p_name] = 'MISSING_IN_PARAMS_OBJ'
                    # 将其值设为 'MISSING_IN_PARAMS_OBJ'，表示参数缺失。
                    # (就在字典里记下这个参数"找不着"。)

            processed_results.append({
                'instance': strategy_instance,
                'params_dict': current_params_dict,  # Store the created dictionary of parameters
                'sharpe': sharpe,
                'return': total_return,
                'drawdown': max_drawdown
            })
            # 将包含策略实例、参数字典、夏普比率、总收益率和最大回撤的字典添加到 `processed_results` 列表中。
            # (把这个策略本身、它的参数、算出来的夏普比率、总收益率和最大回撤，打包成一个字典，加到 `processed_results` 本子里。)

        except AttributeError as e:
            # 捕获在访问分析器结果时可能发生的 `AttributeError` (例如，分析器未运行或结果结构不符合预期)。
            # (如果在拿分析结果的时候，发现某个东西不存在（比如某个分析器没跑或者结果不对），就会出 `AttributeError` 这种错。)
            # Catch AttributeError possibly caused by analyzers not running correctly or missing results
            # (捕获可能由于分析器未正确运行或结果缺失而导致的AttributeError)
            print(
                f"错误: 处理参数组时遇到属性错误 (可能是分析器结果缺失): {params.ema_medium_period if params else 'N/A'}, {params.ema_long_period if params else 'N/A'}, {params.bbands_period if params else 'N/A'}, {params.bbands_devfactor if params else 'N/A'}. 错误: {e}")
            # 打印错误信息，包括相关的参数值和具体的异常。
            # (就打个错误提示，说处理哪组参数的时候出错了，可能是分析结果不全，具体错误是什么。)
        except Exception as e:
            # 捕获在处理单个结果时可能发生的其他所有类型的异常。
            # (如果处理这组结果的时候，发生了其他类型的错误。)
            params_str = f"{params.ema_medium_period}, {params.ema_long_period}, {params.bbands_period}, {params.bbands_devfactor}" if params else "N/A"
            # 格式化参数字符串用于日志记录，如果 `params` 为空则设为 "N/A"。
            # (把这组参数弄成一串文字，方便打印，如果参数是空的就显示 "N/A"。)
            print(f"错误: 处理参数组 {params_str} 时出错: {e}")
            # 打印错误信息。
            # (就打个错误提示，说处理哪组参数的时候出错了，具体错误是什么。)

    print(f"--- 成功提取 {len(processed_results)} 组分析结果 ---")
    # 打印成功提取并处理的分析结果组数。
    # (在屏幕上打一行字，告诉用户成功整理了多少组成绩。)

    if not processed_results:
        # 如果 `processed_results` 列表为空 (即没有成功处理任何结果)。
        # (如果整理完发现 `processed_results` 本子还是空的，啥也没有。)
        print("\n错误：未能成功提取任何有效的分析结果。无法进行评分。")
        # 打印错误信息。
        # (就打个错误提示，说没能拿到任何有效的结果，没法打分了。)
        return None, []
        # 返回 `None` 和空列表。
        # (返回一个空的东西。)

    # 提取所有指标用于计算min/max
    # (提取所有指标用于计算min/max)
    all_sharpes = [r['sharpe'] for r in processed_results]
    # 从 `processed_results` 中提取所有夏普比率值，存入 `all_sharpes` 列表。
    # (把 `processed_results` 本子里记录的所有夏普比率都拿出来，放到 `all_sharpes` 列表里。)
    all_returns = [r['return'] for r in processed_results]
    # 提取所有总收益率值，存入 `all_returns` 列表。
    # (把所有总收益率都拿出来，放到 `all_returns` 列表里。)
    all_drawdowns = [r['drawdown'] for r in processed_results]
    # 提取所有最大回撤值，存入 `all_drawdowns` 列表。
    # (把所有最大回撤都拿出来，放到 `all_drawdowns` 列表里。)

    # 计算min/max，处理列表为空或只有一个元素的情况
    # (计算min/max，处理列表为空或只有一个元素的情况)
    min_sharpe = min(all_sharpes) if all_sharpes else 0.0
    # 计算 `all_sharpes` 列表中的最小值，如果列表为空则默认为0.0。
    # (找出所有夏普比率里最小的那个，如果列表是空的就当它是0.0。)
    max_sharpe = max(all_sharpes) if all_sharpes else 0.0
    # 计算最大值，如果列表为空则默认为0.0。
    # (找出所有夏普比率里最大的那个，如果列表是空的就当它是0.0。)
    min_return = min(all_returns) if all_returns else 0.0
    # 计算 `all_returns` 列表中的最小值，默认为0.0。
    # (找出所有总收益率里最小的那个，默认为0.0。)
    max_return = max(all_returns) if all_returns else 0.0
    # 计算最大值，默认为0.0。
    # (找出所有总收益率里最大的那个，默认为0.0。)
    min_drawdown = min(all_drawdowns) if all_drawdowns else 0.0
    # 计算 `all_drawdowns` 列表中的最小值，默认为0.0。
    # (找出所有最大回撤里最小的那个，默认为0.0。)
    max_drawdown_val = max(all_drawdowns) if all_drawdowns else 0.0  # 重命名以避免覆盖
    # 计算最大值，默认为0.0。变量重命名为 `max_drawdown_val` 以避免与之前的 `max_drawdown` 变量名冲突。
    # (找出所有最大回撤里最大的那个，默认为0.0。这里换了个名字叫 `max_drawdown_val`，免得跟前面用过的 `max_drawdown` 搞混了。)

    # 归一化和评分
    # (归一化和评分)
    best_score = float('-inf')
    # 初始化 `best_score` (最佳得分) 为负无穷大，确保任何有效得分都会比它高。
    # (准备一个变量 `best_score` 来记录最好的分数，一开始把它设成一个非常非常小的值（负无穷大）。)
    best_result_data = None
    # 初始化 `best_result_data` (存储最佳结果对应的数据) 为 `None`。
    # (准备一个变量 `best_result_data` 来记录最好结果是哪个，一开始是空的。)
    scored_results = []
    # 初始化一个空列表 `scored_results`，用于存储所有结果及其计算出的得分。
    # (准备一个空本子 `scored_results`，用来记录所有结果和它们对应的分数。)

    print("\n--- 开始计算归一化得分 ---")
    # 打印提示信息。
    # (在屏幕上打一行字，告诉用户"开始计算归一化得分啦---"。)
    print(f"Min/Max - Sharpe: ({min_sharpe:.4f}, {max_sharpe:.4f}), Return: ({min_return:.4f}, {max_return:.4f}), Drawdown: ({min_drawdown:.4f}, {max_drawdown_val:.4f})")
    # 打印计算出的各指标的最小值和最大值，用于归一化参考。
    # (把刚才算出来的夏普比率、收益率、最大回撤的最小值和最大值都打印出来，让用户知道范围。)

    for result_data in processed_results:
        # 遍历 `processed_results` 列表中的每个已处理结果。
        # (一个一个地看 `processed_results` 本子里的每一条记录。)
        sharpe = result_data['sharpe']
        # 获取当前结果的夏普比率。
        # (拿出这条记录的夏普比率。)
        ret = result_data['return']
        # 获取总收益率。
        # (拿出总收益率。)
        dd = result_data['drawdown']
        # 获取最大回撤。
        # (拿出最大回撤。)

        # 归一化，处理分母为0的情况
        # (归一化，处理分母为0的情况)
        sharpe_range = max_sharpe - min_sharpe
        # 计算夏普比率的范围 (最大值 - 最小值)。
        # (算一下夏普比率的最大值和最小值差多少。)
        return_range = max_return - min_return
        # 计算总收益率的范围。
        # (算一下总收益率的最大值和最小值差多少。)
        drawdown_range = max_drawdown_val - min_drawdown
        # 计算最大回撤的范围。
        # (算一下最大回撤的最大值和最小值差多少。)

        sharpe_norm = (sharpe - min_sharpe) / \
            sharpe_range if sharpe_range > 1e-9 else 0.0
        # 计算归一化夏普比率: (当前值 - 最小值) / 范围。如果范围接近0，则归一化值为0.0，以避免除以零错误。
        # (把当前的夏普比率归一化，公式是 (当前值 - 最小值) / (最大值 - 最小值)。如果最大值和最小值差不多（范围接近0），就当它是0.0，免得出错。)
        return_norm = (ret - min_return) / \
            return_range if return_range > 1e-9 else 0.0
        # 计算归一化总收益率。
        # (同样的方法归一化总收益率。)
        # 注意：最大回撤值越小越好，但评分公式是减去它，所以正常归一化即可
        # (注意：最大回撤是越小越好，但是我们打分的时候是减去它，所以正常归一化就行。)
        drawdown_norm = (dd - min_drawdown) / \
            drawdown_range if drawdown_range > 1e-9 else 0.0
        # 计算归一化最大回撤。
        # (同样的方法归一化最大回撤。)

        # 计算最终得分
        # (计算最终得分)
        score = 0.5 * sharpe_norm + 0.3 * return_norm - 0.2 * drawdown_norm
        # 根据预设权重 (夏普比率0.5，总收益率0.3，最大回撤-0.2) 计算当前结果的综合得分。
        # (给归一化后的夏普比率、总收益率、最大回撤分别乘上权重（比如夏普占50%，收益占30%，回撤占-20%），然后加起来得到一个总分。)
        result_data['score'] = score
        # 将计算出的得分添加到当前结果数据字典中。
        # (把算出来的分数记到这条记录里。)
        scored_results.append(result_data)
        # 将带有得分的结果数据添加到 `scored_results` 列表中。
        # (把这条带分数的记录加到 `scored_results` 本子里。)

        if score > best_score:
            # 如果当前得分高于已记录的 `best_score`。
            # (如果这个分数比之前记录的最好分数还要高。)
            best_score = score
            # 更新 `best_score`。
            # (那就更新最好分数。)
            best_result_data = result_data
            # 更新 `best_result_data` 为当前结果数据。
            # (并且记下这个结果是目前最好的。)

    print(f"--- 完成 {len(scored_results)} 组得分计算 ---")
    # 打印完成得分计算的结果组数。
    # (在屏幕上打一行字，告诉用户总共给多少组成绩打了分。)

    return best_result_data, scored_results
    # 函数返回最佳结果数据 (`best_result_data`) 和包含所有结果及其得分的列表 (`scored_results`)。
    # (最后把最好的那个结果和所有带分数的结果都返回出去。)


# ===================================================================================
# Main Program Entry Point
# (这是一条注释，说明下面是程序的主要入口点。)
# (下面是程序开始运行的地方。)
# ===================================================================================
if __name__ == '__main__':
    # 这是一个Python的常用结构，确保以下代码只在直接运行此脚本时执行，而不是在被其他脚本导入时执行。
    # (这是一个Python的规矩，意思是如果直接运行这个文件，下面的代码就会执行；如果这个文件是被其他文件引用的，那下面的代码就不会主动执行。)
    optimize = True
    # 设置 `optimize` 标志为 `True`，表示执行参数优化。
    # (设置一个开关 `optimize`，现在是 `True`，表示要进行参数优化。)
    # optimize = False
    # (这行被注释掉了，如果取消注释并注释掉上面一行，就会执行单次回测而不是优化。)
    initial_cash = 500000.0
    # 设置初始资金为500,000.0。
    # (设置一开始有多少本金，这里是50万。)
    commission_rate = 0.0003
    # 设置交易佣金率为0.0003 (即万分之三)。
    # (设置每次交易的手续费比例是万分之三。)

    data_folder = r'D:\\BT2025\\datas\\'  # Make sure this path is correct
    # 设置数据文件夹的路径。`r''` 表示原始字符串，避免反斜杠被转义。
    # (告诉程序股票数据放在哪个文件夹里，这里用 `r''` 是为了防止路径里的斜杠出问题。)
    if not os.path.isdir(data_folder):
        # 检查指定的数据文件夹路径是否存在且是一个目录。
        # (看看这个文件夹是不是真的存在。)
        print(f"错误: 数据文件夹路径不存在: {data_folder}")
        # 如果路径不存在或不是目录，则打印错误信息。
        # (如果文件夹不存在，就打个错误提示。)
        sys.exit(1)
        # 退出程序，返回状态码1表示错误。
        # (程序就停在这里了，不往下跑了。)

    data_files = [
        os.path.join(data_folder, '510050_d.xlsx'),
        os.path.join(data_folder, '510300_d.xlsx'),
        os.path.join(data_folder, '159949_d.xlsx')
    ]
    # 定义一个列表 `data_files`，包含要加载的Excel数据文件的完整路径。
    # `os.path.join` 用于正确地拼接路径，使其跨平台兼容。
    # (列出要分析的几只ETF的数据文件名，用 `os.path.join` 把文件夹路径和文件名拼起来，这样不容易出错。)
    # ... (rest of data file checks) ...
    # (这里可能还有其他检查数据文件的代码，省略了。)

    column_mapping = {'date': 'datetime', '开盘': 'open',
                      '最高': 'high', '最低': 'low', '收盘': 'close', '成交量': 'volume'}
    # 定义一个字典 `column_mapping`，用于将Excel文件中的中文列名映射到Backtrader期望的英文标准列名。
    # (定义一个对应关系，告诉程序Excel表格里的中文列名（比如"开盘"）对应 `backtrader` 认识的英文名（比如"open"）。)
    openinterest_col_name = None
    # 设置持仓量列的名称为 `None`，表示数据中不包含或不使用持仓量信息。
    # (这里设置持仓量那一列的名字是 `None`，意思是我们用不到或者数据里没有这个信息。)

    fromdate = datetime.datetime(2015, 1, 1)
    # 设置回测的起始日期为2015年1月1日。
    # (设置回测从哪天开始，这里是2015年1月1日。)
    todate = datetime.datetime(2024, 4, 30)
    # 设置回测的结束日期为2024年4月30日。
    # (设置回测到哪天结束，这里是2024年4月30日。)

    # Sizer parameters (these were part of strategy params before)
    # (Sizer的参数（这些以前是策略参数的一部分）)
    sizer_params = dict(
        etf_type_param_name='etf_type',  # Tells sizer how to find etf_type in strategy
        # 定义一个字典 `sizer_params`，存储传递给自定义Sizer `AShareETFSizer` 的参数。
        # (准备一个字典 `sizer_params`，放一些要告诉Sizer的设置。)
        # 'etf_type_param_name' 告诉Sizer如何在策略参数中找到ETF类型。
        # ('etf_type_param_name' 这个设置是告诉Sizer怎么从策略的参数里找到ETF是趋势型还是区间型。)
        risk_per_trade_trend=0.01,
        # Corresponds to AShareETFStrategy.params.max_risk_per_trade_trend
        # 设置趋势型ETF每次交易的风险比例为1%。
        # (对应策略里趋势型ETF每次交易的最大风险比例，这里是1%。)
        risk_per_trade_range=0.005,
        # Corresponds to AShareETFStrategy.params.max_risk_per_trade_range
        # 设置区间型ETF每次交易的风险比例为0.5%。
        # (对应策略里区间型ETF每次交易的最大风险比例，这里是0.5%。)
        max_position_per_etf_percent=0.30,
        # 设置单个ETF持仓市值占总账户价值的最大比例为30%。
        # (设置单个ETF最多能占总资产的30%。)
        trend_stop_loss_atr_mult_param_name='trend_stop_loss_atr_mult',
        # Name of param in strategy
        # 告诉Sizer策略中趋势型止损ATR倍数参数的名称是 'trend_stop_loss_atr_mult'。
        # (告诉Sizer，在策略参数里，那个决定趋势型止损用几倍ATR的参数名字叫 'trend_stop_loss_atr_mult'。)
        range_stop_loss_buffer_param_name='range_stop_loss_buffer'
        # Name of param in strategy
        # 告诉Sizer策略中区间型止损缓冲参数的名称是 'range_stop_loss_buffer'。
        # (告诉Sizer，在策略参数里，那个决定区间型止损缓冲幅度的参数名字叫 'range_stop_loss_buffer'。)
    )

    # Optimization ranges for strategy params (sizing params are now fixed in sizer_params for this example)
    # (策略参数的优化范围（在这个例子中，Sizer的参数固定在sizer_params中）)
    # If you want to optimize sizer params, you'd optstrategy on the Sizer's params if Backtrader supported it directly,
    # (如果你想优化Sizer的参数，如果Backtrader直接支持的话，你会对Sizer的参数进行optstrategy操作，)
    # or create different sizer instances/subclasses.
    # (或者创建不同的Sizer实例/子类。)
    # For now, we optimize strategy params that influence signals and SL/TP prices for brackets.
    # (目前，我们优化影响信号和括号单止损/止盈价格的策略参数。)
    ema_medium_range = range(40, 81, 20)
    # 设置中期EMA周期的优化范围：从40到80 (不含81)，步长为20 (即40, 60, 80)。
    # (设置中期EMA均线周期的优化范围是40、60、80这几个值。)
    ema_long_range = range(100, 141, 20)
    # 设置长期EMA周期的优化范围：从100到140 (不含141)，步长为20 (即100, 120, 140)。
    # (设置长期EMA均线周期的优化范围是100、120、140这几个值。)
    bbands_period_range = range(15, 26, 5)
    # 设置布林带周期的优化范围：从15到25 (不含26)，步长为5 (即15, 20, 25)。
    # (设置布林带周期的优化范围是15、20、25这几个值。)
    # Convert numpy array to list
    # (将numpy数组转换为列表)
    bbands_dev_range = np.arange(1.8, 2.3, 0.2).tolist()
    # 设置布林带标准差倍数的优化范围：从1.8到2.2 (不含2.3)，步长为0.2 (即1.8, 2.0, 2.2)，并转换为列表。
    # (设置布林带标准差倍数的优化范围是1.8、2.0、2.2这几个值，这里用 `np.arange` 生成再转成列表。)
    # Example: optimizing ATR multiplier
    # (示例：优化ATR乘数)
    trend_sl_atr_mult_range = np.arange(
        2.0, 3.1, 0.5).tolist()  # Convert numpy array to list
    # 设置趋势型止损ATR倍数的优化范围：从2.0到3.0 (不含3.1)，步长为0.5 (即2.0, 2.5, 3.0)，并转换为列表。
    # (设置趋势型止损用几倍ATR的优化范围是2.0、2.5、3.0这几个值。)

    cerebro = bt.Cerebro(stdstats=not optimize, optreturn=False)
    # 创建Cerebro引擎实例。
    # `stdstats=not optimize` 表示如果不是优化模式 (即单次回测)，则自动添加标准统计分析器。
    # `optreturn=False` 表示在优化模式下，`cerebro.run()` 返回一个包含所有策略运行结果的列表的列表，而不是只返回优化后的参数。
    # (创建 `backtrader` 的大脑 `cerebro`。 `stdstats=not optimize` 的意思是如果不是优化就自动加一些标准的统计分析；`optreturn=False` 的意思是优化的时候，`run()` 会把每次跑的结果都返回来，而不是只给最好的那个。)

    loaded_data_count = load_data_to_cerebro(
        cerebro, data_files, column_mapping, openinterest_col_name, fromdate, todate)
    # 调用 `load_data_to_cerebro` 函数加载数据到Cerebro引擎，并获取成功加载的数据源数量。
    # (调用前面定义的 `load_data_to_cerebro` 函数，把数据喂给 `cerebro`，并拿到成功加载了多少个数据文件。)

    if loaded_data_count == 0:
        # 如果成功加载的数据源数量为0。
        # (如果一个数据文件都没加载成功。)
        print("\n错误：未能成功加载任何数据文件。无法继续执行。")
        # 打印错误信息。
        # (就打个错误提示，说没加载到数据，跑不了了。)
        sys.exit(1)
        # 退出程序。
        # (程序停掉。)

    print(f"\n总共加载了 {loaded_data_count} 个数据源。")
    # 打印成功加载的数据源总数。
    # (告诉用户总共加载了多少个数据文件。)

    cerebro.broker.setcash(initial_cash)
    # 设置Cerebro经纪商 (broker) 的初始现金。
    # (告诉 `cerebro` 的交易账户一开始有多少钱。)
    cerebro.broker.setcommission(commission=commission_rate, stocklike=True)
    # 设置交易佣金。`commission=commission_rate` 指定佣金率，`stocklike=True` 表示佣金计算方式类似股票 (通常是按成交金额的百分比)。
    # (设置交易手续费，`stocklike=True` 表示按股票的方式算手续费，也就是按成交金额的百分比。)

    # Add the custom sizer
    # (添加自定义Sizer)
    cerebro.addsizer(AShareETFSizer, **sizer_params)
    # 将自定义的 `AShareETFSizer` 添加到Cerebro引擎，并传递 `sizer_params` 字典中的参数。
    # (把我们自己写的那个 `AShareETFSizer` (算每次买多少的工具) 加到 `cerebro` 里，并且把 `sizer_params` 里的设置告诉它。)

    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe_ratio',
                        timeframe=bt.TimeFrame.Days, riskfreerate=0.0, annualize=True, factor=252)
    # 添加夏普比率分析器。
    # `_name` 为分析器指定一个名称，方便后续访问。
    # `timeframe` 指定时间框架 (日)，`riskfreerate` 指定无风险利率 (0.0)。
    # `annualize=True` 表示年化夏普比率，`factor=252` 指定年化因子 (一年约252个交易日)。
    # (给 `cerebro` 加一个夏普比率分析器，取名叫 'sharpe_ratio'，按天算，无风险利率是0，结果要年化，一年算252天。)
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    # 添加最大回撤分析器，并命名为 'drawdown'。
    # (加一个最大回撤分析器，取名叫 'drawdown'。)
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
    # 添加收益率分析器，并命名为 'returns'。
    # (加一个收益率分析器，取名叫 'returns'。)
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trade_analyzer')
    # 添加交易分析器，并命名为 'trade_analyzer'，用于分析每笔交易的详细情况。
    # (加一个交易分析器，取名叫 'trade_analyzer'，用来分析每一笔交易的细节。)

    if optimize:
        # 如果 `optimize` 标志为 `True` (执行参数优化)。
        # (如果 `optimize` 开关是开着的，表示要进行参数优化。)
        print("\n{:-^50}".format(' 参数优化设置 '))
        # 打印参数优化设置的标题。
        # (打一个标题，告诉用户下面是参数优化的设置。)
        print(f"  etf_type: ['trend', 'range']")  # This is a strategy param
        # 打印ETF类型的优化范围 (策略参数)。
        # (打印ETF类型的优化范围，这是策略的参数。)
        print(f"  ema_medium_period: {list(ema_medium_range)}")
        # 打印中期EMA周期的优化范围。
        # (打印中期EMA均线周期的优化范围。)
        print(f"  ema_long_period: {list(ema_long_range)}")
        # 打印长期EMA周期的优化范围。
        # (打印长期EMA均线周期的优化范围。)
        print(f"  bbands_period: {list(bbands_period_range)}")
        # 打印布林带周期的优化范围。
        # (打印布林带周期的优化范围。)
        print(f"  bbands_devfactor: {bbands_dev_range}")  # Already a list
        # 打印布林带标准差倍数的优化范围 (已是列表)。
        # (打印布林带标准差倍数的优化范围，它本身已经是个列表了。)
        # Strategy param for bracket SL
        # (用于括号单止损的策略参数)
        print(
            f"  trend_stop_loss_atr_mult: {trend_sl_atr_mult_range}")  # Already a list
        # 打印趋势型止损ATR倍数的优化范围 (已是列表)。
        # (打印趋势型止损用几倍ATR的优化范围，它本身也已经是个列表了。)
        print('-' * 50)
        # 打印分隔线。
        # (打一条分隔线。)

        cerebro.optstrategy(AShareETFStrategy,
                            etf_type=['trend', 'range'],
                            ema_medium_period=ema_medium_range,
                            ema_long_period=ema_long_range,
                            bbands_period=bbands_period_range,
                            bbands_devfactor=bbands_dev_range,
                            trend_stop_loss_atr_mult=trend_sl_atr_mult_range  # Optimizing this strategy param
                            # Note: range_stop_loss_buffer could also be optimized if desired
                            )
        # 调用 `cerebro.optstrategy` 方法添加要优化的策略 `AShareETFStrategy` 及其参数的优化范围。
        # (告诉 `cerebro` 我们要用 `AShareETFStrategy` 这个策略来进行优化，并且把每个参数要尝试的值的范围都告诉它。)
        # (注意：如果需要，也可以优化区间型止损的缓冲参数 `range_stop_loss_buffer`。)
        # ... (rest of the optimization execution and result processing logic remains the same)
        # (...剩余的优化执行和结果处理逻辑保持不变...)
        print('开始参数优化运行...')
        # 打印开始参数优化运行的提示。
        # (告诉用户"开始跑参数优化啦..."。)
        start_time = time.time()
        # 记录优化开始的时间。
        # (记一下现在几点了，优化要开始了。)
        # DEBUG: Force single CPU to get detailed error traceback from child processes
        # (调试：强制使用单个CPU以从子进程获取详细的错误回溯)
        results = cerebro.run(maxcpus=10)
        # 运行Cerebro引擎进行参数优化。`maxcpus=10` 表示最多使用10个CPU核心并行计算 (如果可用)。
        # (让 `cerebro` 开始跑优化，最多用10个CPU核心一起跑，这样快一点。)
        end_time = time.time()
        # 记录优化结束的时间。
        # (记一下现在几点了，优化跑完了。)
        total_time = end_time - start_time
        # 计算优化总耗时。
        # (算一下总共花了多长时间。)
        actual_combinations = len(results) if results else 0
        # 计算实际运行的参数组合数量。如果 `results` 为空则为0。
        # (看看实际跑了多少组参数，如果 `results` 是空的就说明一组都没跑。)
        avg_time_per_run = total_time / actual_combinations if actual_combinations > 0 else 0
        # 计算平均每组参数的运行时间。如果组合数为0则为0。
        # (算一下平均每组参数花了多长时间，如果一组都没跑那就没法算。)

        print('\n{:=^50}'.format(' 优化完成统计 '))
        # 打印优化完成统计的标题。
        # (打一个标题，告诉用户下面是优化完成的统计数据。)
        print(f"{'总用时':<20}: {total_time:.2f}秒 ({total_time/60:.2f}分钟)")
        # 打印总用时 (秒和分钟)。
        # (打印总共花了多少秒，相当于多少分钟。)
        print(f"{'实际参数组数':<20}: {actual_combinations}")
        # 打印实际运行的参数组数。
        # (打印实际跑了多少组参数。)
        print(f"{'每组平均用时':<20}: {avg_time_per_run:.2f}秒")
        # 打印每组平均用时。
        # (打印平均每组参数花了多少秒。)
        print('=' * 50)
        # 打印分隔线。
        # (打一条分隔线。)

        best_result, all_scored_results = analyze_optimization_results(results)
        # 调用 `analyze_optimization_results` 函数分析优化结果，获取最佳结果和所有带评分的结果。
        # (调用前面定义的 `analyze_optimization_results` 函数来分析优化结果，拿到最好的那个结果和所有带分数的结果。)

        if best_result:
            # 如果找到了最佳结果 (`best_result` 不为 `None`)。
            # (如果找到了最好的结果。)
            # Correctly access parameters from the dictionary
            # (从字典中正确访问参数)
            best_params_dict = best_result.get('params_dict', {})
            # 从 `best_result` 中获取参数字典 `params_dict`，如果不存在则为空字典。
            # (从最好的那个结果里拿出它的参数设置，如果找不到就当是个空字典。)

            # Prepare headers and format strings, ensuring alignment
            # (准备表头和格式字符串，确保对齐)
            # Adjusted width for ATR mult
            # (调整了ATR乘数的宽度)
            header_format = '{:<10} {:<12} {:<12} {:<12} {:<10} {:<10} {:<12} {:<12} {:<12} {:<12}'
            # 定义结果表格的表头格式字符串，用于对齐打印。
            # (定义一下打印结果表格的表头怎么排版，每个项目占多少位置。)
            # Adjusted width for ATR mult
            # (调整了ATR乘数的宽度)
            row_format = '{:<10} {:<12} {:<12} {:<12.0f} {:<10.1f} {:<10.1f} {:<12.4f} {:<12.2f} {:<12.2f} {:<12.4f}'
            # 定义结果表格每行数据的格式字符串。
            # (定义一下打印结果表格每一行数据怎么排版。)

            print('\n{:=^135}'.format(' 参数优化结果 (按得分排序) '))  # Adjusted width
            # 打印参数优化结果的标题 (按得分排序)，调整了总宽度。
            # (打一个标题，告诉用户下面是按分数排序的参数优化结果，调整了一下总宽度。)
            print(header_format.format('ETF类型', 'EMA中期', 'EMA长期', '布林周期',
                  '布林标差', 'ATR止损', '夏普比率', '收益率(%)', '最大回撤(%)', '得分'))
            # 使用表头格式字符串打印表头。
            # (用上面定义的表头格式把表头打印出来。)
            print('-' * 135)  # Adjusted width
            # 打印分隔线，调整了总宽度。
            # (打一条分隔线，宽度也调整了。)

            all_scored_results.sort(key=lambda x: x.get(
                'score', float('-inf')), reverse=True)
            # 对 `all_scored_results` 列表按 'score' (得分) 降序排序。如果结果中没有 'score'，则默认为负无穷。
            # (把所有带分数的结果按照分数从高到低排个序。如果哪个结果没分数，就当它是负无穷大。)

            for res_data in all_scored_results[:min(20, len(all_scored_results))]:
                # 遍历排序后结果列表中的前20个 (或所有结果，如果总数少于20)。
                # (一个一个地看排好序的结果，最多看前20个，如果总共没20个就全看。)
                # Safely get the params dict
                # (安全地获取参数字典)
                p_dict = res_data.get('params_dict', {})
                # 从当前结果数据 `res_data` 中获取参数字典。
                # (拿出当前这个结果的参数设置。)
                print(row_format.format(
                    p_dict.get('etf_type', 'N/A'),
                    p_dict.get('ema_medium_period', 0),
                    p_dict.get('ema_long_period', 0),
                    p_dict.get('bbands_period', 0),
                    p_dict.get('bbands_devfactor', 0.0),
                    # Display optimized ATR mult
                    # (显示优化的ATR乘数)
                    p_dict.get('trend_stop_loss_atr_mult', 0.0),
                    res_data.get('sharpe', 0.0),
                    res_data.get('return', 0.0) * 100,
                    res_data.get('drawdown', 0.0) * 100,
                    res_data.get('score', 0.0)
                ))
                # 使用行格式字符串打印当前结果的参数和性能指标。
                # (用上面定义的行格式把这个结果的参数、夏普比率、收益率（转成百分比）、最大回撤（转成百分比）和分数都打印出来。)

            print('\n{:=^50}'.format(' 最优参数组合 '))
            # 打印最优参数组合的标题。
            # (打一个标题，告诉用户下面是最好的那组参数。)
            # Use the already retrieved best_params_dict
            # (使用已经检索到的best_params_dict)
            print(f"{'ETF类型':<25}: {best_params_dict.get('etf_type', 'N/A')}")
            # 打印最优参数组合中的ETF类型。
            # (打印最好那组参数的ETF类型。)
            print(f"{'EMA中期':<25}: {best_params_dict.get('ema_medium_period', 0)}")
            # 打印最优EMA中期周期。
            # (打印最好那组参数的中期EMA周期。)
            print(f"{'EMA长期':<25}: {best_params_dict.get('ema_long_period', 0)}")
            # 打印最优EMA长期周期。
            # (打印最好那组参数的长期EMA周期。)
            print(f"{'布林带周期':<25}: {best_params_dict.get('bbands_period', 0)}")
            # 打印最优布林带周期。
            # (打印最好那组参数的布林带周期。)
            print(
                f"{'布林带标准差':<25}: {best_params_dict.get('bbands_devfactor', 0.0):.1f}")
            # 打印最优布林带标准差倍数 (保留一位小数)。
            # (打印最好那组参数的布林带标准差倍数，保留一位小数。)
            print(
                f"{'趋势止损ATR倍数':<25}: {best_params_dict.get('trend_stop_loss_atr_mult', 0.0):.1f}")
            # 打印最优趋势止损ATR倍数 (保留一位小数)。
            # (打印最好那组参数的趋势止损ATR倍数，保留一位小数。)
            print(f"{'夏普比率':<25}: {best_result.get('sharpe', 0.0):.4f}")
            # 打印最优结果的夏普比率 (保留四位小数)。
            # (打印最好那个结果的夏普比率，保留四位小数。)
            print(f"{'总收益率':<25}: {best_result.get('return', 0.0) * 100:.2f}%")
            # 打印最优结果的总收益率 (转换为百分比，保留两位小数)。
            # (打印最好那个结果的总收益率，转成百分比，保留两位小数。)
            print(f"{'最大回撤':<25}: {best_result.get('drawdown', 0.0) * 100:.2f}%")
            # 打印最优结果的最大回撤 (转换为百分比，保留两位小数)。
            # (打印最好那个结果的最大回撤，转成百分比，保留两位小数。)
            print(f"{'得分':<25}: {best_result.get('score', 0.0):.4f}")
            # 打印最优结果的得分 (保留四位小数)。
            # (打印最好那个结果的分数，保留四位小数。)
            print('=' * 50)
            # 打印分隔线。
            # (打一条分隔线。)
        else:
            # 如果未能确定最优策略 (`best_result` 为 `None`)。
            # (如果没有找到最好的结果。)
            print("\n错误：未能确定最优策略或处理结果时出错。")
            # 打印错误信息。
            # (就打个错误提示，说没找到最好的策略或者处理结果的时候出错了。)

    else:  # Single Run
        # 如果 `optimize` 标志为 `False` (执行单次回测)。
        # (如果 `optimize` 开关是关着的，表示要进行单次回测。)
        # ... (single run logic remains the same, just ensure AShareETFSizer is added)
        # (...单次运行逻辑保持不变，只需确保添加了AShareETFSizer...)
        print("\n{:-^50}".format(' 单次回测设置 '))
        # 打印单次回测设置的标题。
        # (打一个标题，告诉用户下面是单次回测的设置。)
        print(f"优化开关: 关闭")
        # 打印优化开关状态。
        # (告诉用户优化开关是关着的。)
        print(f"Observer 图表: 开启")
        # 打印Observer图表状态 (假设开启，实际绘图逻辑在后面)。
        # (告诉用户Observer图表是开着的，后面会尝试画图。)
        # Print Sizer parameters for single run
        # (打印单次运行的Sizer参数)
        print("\nSizer 参数:")
        # 打印Sizer参数的标题。
        # (打印Sizer参数的标题。)
        for k, v in sizer_params.items():
            # 遍历 `sizer_params` 字典中的键值对。
            # (一个一个地看 `sizer_params` 字典里的设置。)
            print(f"  {k}: {v}")
            # 打印每个Sizer参数及其值。
            # (把每个Sizer参数的名字和值都打印出来。)
        print('-' * 50)
        # 打印分隔线。
        # (打一条分隔线。)

        cerebro.addstrategy(AShareETFStrategy, etf_type='trend')
        # 添加 `AShareETFStrategy` 策略到Cerebro引擎进行单次回测，并指定 `etf_type` 为 'trend'。
        # (把 `AShareETFStrategy` 这个策略加到 `cerebro` 里跑一次，并且指定ETF类型是 'trend'。)

        print('开始单次回测运行...')
        # 打印开始单次回测运行的提示。
        # (告诉用户"开始跑单次回测啦..."。)
        print('期初总资金: %.2f' % cerebro.broker.getvalue())
        # 打印期初总资金 (格式化为两位小数)。
        # (打印一开始账户里有多少钱，保留两位小数。)
        start_time = time.time()
        # 记录回测开始时间。
        # (记一下现在几点了，回测要开始了。)
        results = cerebro.run()
        # 运行Cerebro引擎进行单次回测。
        # (让 `cerebro` 开始跑回测。)
        end_time = time.time()
        # 记录回测结束时间。
        # (记一下现在几点了，回测跑完了。)
        final_value = cerebro.broker.getvalue()
        # 获取回测结束后的账户总价值。
        # (看看跑完之后账户里还剩多少钱。)
        print('期末总资金: %.2f' % final_value)
        # 打印期末总资金。
        # (打印最后账户里有多少钱。)
        print('回测总用时: {:.2f}秒'.format(end_time - start_time))
        # 打印回测总用时。
        # (打印这次回测总共花了多少秒。)
        print(f"总收益率: {(final_value / initial_cash - 1) * 100:.2f}%")
        # 计算并打印总收益率 (百分比形式，保留两位小数)。
        # (算一下总共赚了还是亏了多少百分比，保留两位小数。)

        print("\n{:-^50}".format(' 单次回测分析结果 '))
        # 打印单次回测分析结果的标题。
        # (打一个标题，告诉用户下面是单次回测的分析结果。)
        if results and results[0]:
            # 如果回测结果 `results` 存在且不为空 (单次回测时 `results` 是一个包含策略实例的列表)。
            # (如果回测有结果，并且结果不是空的。)
            strat_instance = results[0]
            # 获取策略实例。
            # (拿出那个策略本身。)
            for analyzer_name, analyzer_obj in strat_instance.analyzers.getitems():
                # 遍历策略实例中所有分析器的名称和对象。
                # (一个一个地看这个策略跑完之后得到的各种分析结果。)
                analysis = analyzer_obj.get_analysis()
                # 获取当前分析器的分析结果。
                # (拿出这个分析器的具体分析数据。)
                print(f"\n--- {analyzer_name} ---")
                # 打印分析器名称作为小标题。
                # (打印这个分析器的名字。)
                if isinstance(analysis, dict):
                    # 如果分析结果是一个字典。
                    # (如果分析数据是一个字典（有很多项）。)
                    for k, v in analysis.items():
                        # 遍历字典中的键值对。
                        # (一个一个地看字典里的每一项。)
                        if isinstance(v, dict):
                            # 如果值本身也是一个字典 (嵌套字典)。
                            # (如果这一项本身也是个字典。)
                            print(f"  {k}:")
                            # 打印键名。
                            # (打印这一项的名字。)
                            for sub_k, sub_v in v.items():
                                # 遍历嵌套字典中的键值对。
                                # (再看这个小字典里的每一项。)
                                print(f"    {sub_k}: {sub_v}")
                                # 打印嵌套字典的键和值。
                                # (打印小字典里的项目和它的值。)
                        else:
                            # 如果值不是字典。
                            # (如果这一项不是字典。)
                            print(f"  {k}: {v}")
                            # 直接打印键和值。
                            # (就直接打印这一项的名字和它的值。)
                else:
                    # 如果分析结果不是字典 (例如，是单个值或字符串)。
                    # (如果分析数据不是一个字典，可能就是单个数字或者一段文字。)
                    print(analysis)
                    # 直接打印分析结果。
                    # (那就直接把这个分析数据打印出来。)
        print('-' * 50)
        # 打印分隔线。
        # (打一条分隔线。)

        if not optimize:
            # 如果不是优化模式 (即是单次回测)。
            # (如果 `optimize` 开关是关着的，表示是单次回测。)
            try:
                # 开始一个 `try` 代码块，用于处理绘图过程中可能发生的异常。
                # (试试看下面的画图操作，如果出错了就跳到 `except` 部分处理。)
                print("\n尝试绘制图表...")
                # 打印尝试绘制图表的提示。
                # (告诉用户"尝试画图啦..."。)
                plot_filename = 'backtest_plot_sizers.png'
                # 设置绘图输出的文件名为 'backtest_plot_sizers.png'。
                # (把图保存成一个叫 'backtest_plot_sizers.png' 的文件。)
                # Plotting the first data, assuming multiple datas might be too cluttered
                # (绘制第一个数据，假设多个数据可能会过于混乱)
                # If plotting specific data is needed, adjust data_to_plot
                # (如果需要绘制特定数据，请调整data_to_plot)
                data_to_plot = cerebro.datas[0]._name if cerebro.datas else None
                # 选择要绘制的数据：如果Cerebro中有数据源，则选择第一个数据源的名称；否则为 `None`。
                # (选第一个数据来画图，如果 `cerebro` 里有数据就用第一个数据的名字，没有就算了。)
                if data_to_plot:
                    # 如果有数据可供绘制 (`data_to_plot` 不为 `None`)。
                    # (如果有数据可以画。)
                    cerebro.plot(style='candlestick', barup='red', bardown='green',
                                 iplot=False, volume=True, savefig=True, figfilename=plot_filename,
                                 plotdatanames=[data_to_plot])
                    # 调用 `cerebro.plot` 方法绘制图表。
                    # `style='candlestick'` 指定K线图样式。
                    # `barup='red'` 上涨K线为红色，`bardown='green'` 下跌K线为绿色 (注意这可能与国内习惯相反)。
                    # `iplot=False` 表示不使用交互式绘图 (例如Jupyter Notebook中的内联绘图)。
                    # `volume=True` 表示包含成交量副图。
                    # `savefig=True` 表示保存图表到文件。
                    # `figfilename=plot_filename` 指定保存的文件名。
                    # `plotdatanames=[data_to_plot]` 指定只绘制选定的数据源。
                    # (让 `cerebro` 画图：用蜡烛图样式，涨的时候是红的，跌的时候是绿的（注意这可能跟国内习惯反了），不在程序里直接显示图，要画成交量，把图保存起来，文件名是 `plot_filename`，只画 `data_to_plot` 这个数据。)
                    print(f"图表已保存到 {plot_filename}")
                    # 打印图表已保存的提示信息。
                    # (告诉用户图已经保存到哪个文件了。)
                else:
                    # 如果没有数据可供绘制。
                    # (如果没有数据可以画。)
                    print("没有数据可供绘制。")
                    # 打印提示信息。
                    # (就告诉用户没数据画不了图。)
            except Exception as e:
                # 捕获在绘图过程中发生的任何异常。
                # (如果画图的时候出错了。)
                print(f"\n绘制图表时出错: {e}")
                # 打印绘图出错的错误信息。
                # (就打个错误提示，说画图的时候出错了，具体错在哪。)
                print("请确保已安装matplotlib且图形环境配置正确。")
                # 提示用户检查matplotlib安装和图形环境配置。
                # (提醒用户检查一下是不是装了 `matplotlib` 这个画图工具，或者电脑的画图环境有没有配好。)
                print("请确保已安装matplotlib且图形环境配置正确。")
