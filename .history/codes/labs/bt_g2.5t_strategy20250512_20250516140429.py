# 1. 导入模块
# (这个部分是把我们程序需要用到的各种工具箱（也叫库或模块）给引进来，就像做菜前准备好各种厨具和调料一样。)
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

# 2. 自定义仓位管理器类 AShareETFSizer
# (这部分定义了一个专门用来计算每次买卖多少A股ETF的工具。它不决定什么时候买卖，只负责根据策略算好的风险信息来决定买卖数量。)


class AShareETFSizer(bt.Sizer):
    # 定义一个名为 `AShareETFSizer` 的类，它继承自 `backtrader.Sizer` 类，用于自定义A股ETF的头寸计算逻辑。
    # (创建一个专门给A股ETF算每次买多少的工具，这个工具是基于 `backtrader` 里面一个叫 `Sizer` 的基础工具改造的。它的职责更纯粹：根据策略算好的风险信息来计算数量。)

    # 2.1 Sizer参数定义
    # (这里是给这个"算数量工具"预设一些可以调整的选项。)
    params = (
        # 定义该Sizer的参数。
        # (给这个算数量的工具预设一些可以调整的选项。)
        ('max_position_per_etf_percent', 0.30),
        # 定义参数 `max_position_per_etf_percent`，默认值为0.30 (30%)，表示单个ETF持仓市值占总账户价值的最大比例。
        # (设置一个选项叫 'max_position_per_etf_percent'，默认是0.30，意思是不管怎么买，单个ETF的市值不能超过总资产的30%。这个限制由Sizer自己控制。)
    )

    # 2.2 计算头寸大小的核心方法 _getsizing
    # (这个函数是 `backtrader` 在需要决定买卖多少股票时会自动调用的，我们在这里写清楚计算逻辑。)
    def _getsizing(self, comminfo, cash, data, isbuy):
        # 定义 `_getsizing` 方法，此方法由Backtrader在需要确定头寸大小时调用。
        # (定义一个名叫 `_getsizing` 的函数，`backtrader` 每次要决定买多少股票的时候，就会来问这个函数。)

        # 2.2.1 初始检查和设置
        # (开始计算前，先做一些基本的判断和准备工作。)
        if not isbuy:
            # 检查当前操作是否为买入操作。
            # (判断一下是不是要买入。)
            return 0
            # 如果不是买入操作，则返回0，表示不进行任何操作（此Sizer只处理买入）。
            # (如果不是买入，就返回0，意思是这次不买也不卖。)

        position = self.broker.getposition(data)
        # 获取当前数据对象（例如某ETF）的持仓情况。
        # (查一下现在手上有没有这只ETF，有多少。)
        if position.size != 0:
            # 如果当前数据对象已有持仓。
            # (如果已经持有这只ETF了。)
            return 0
            # 如果已有持仓，则返回0，表示不重复开仓。
            # (那就返回0，意思是不再买了，避免重复买。)

        d_name = data._name
        # 获取当前数据对象的名称（例如ETF代码）。
        # (拿到这只ETF的名字，比如它的代码。)
        strategy = self.strategy
        # 获取关联的策略实例，以便后续从中获取信息。
        # (拿到咱们正在用的那个交易策略，因为策略那边会有一些计算好的信息。)

        # 2.2.2 解耦关键点：从策略获取预计算的风险信息
        # (这一步是本Sizer设计的核心，它不去自己算复杂的风险，而是从策略那里拿已经算好的风险数据。)
        if not hasattr(strategy, 'pending_trade_info') or d_name not in strategy.pending_trade_info:
            # 检查策略实例中是否存在 `pending_trade_info` 字典，并且该字典中是否包含当前ETF的待处理交易信息。
            # (看看策略那边有没有准备好一个叫 'pending_trade_info' 的本子，以及本子里有没有记录这只ETF的交易计划。)
            strategy.log(
                f"Sizer: 无法在 strategy.pending_trade_info 中找到 {d_name} 的待处理交易信息。跳过。", data=data)
            # 如果找不到相关信息，则记录日志并返回0。
            # (如果找不到，记个日志说一声，这次买不了。)
            return 0
            # 返回0，表示不进行交易。
            # (返回0，不买了。)

        trade_info = strategy.pending_trade_info[d_name]
        # 从策略的 `pending_trade_info` 字典中获取当前ETF的交易信息。
        # (从策略的 'pending_trade_info' 本子里拿出这只ETF的交易计划。)

        entry_price = trade_info.get('entry_price')
        # 从交易信息中获取策略计算的参考入场价。
        # (拿到策略计划的买入参考价。)
        risk_per_share = trade_info.get('risk_per_share')
        # 从交易信息中获取策略计算的每股风险。
        # (拿到策略算好的买这一只ETF一股可能亏多少钱。)
        amount_to_risk = trade_info.get('amount_to_risk')
        # 从交易信息中获取策略计算的本次交易允许的最大风险金额。
        # (拿到策略算好的这次交易最多能亏多少钱。)

        # 2.2.3 验证从策略获取的信息是否有效
        # (检查一下从策略拿到的这些信息是不是都全的，是不是有效的。)
        if entry_price is None or risk_per_share is None or amount_to_risk is None:
            # 检查入场价、每股风险、最大风险金额等关键信息是否缺失。
            # (看看是不是缺了买入价、每股风险、或者总风险金额这些重要的数。)
            strategy.log(
                f"Sizer: 从策略获取的 {d_name} 交易信息不完整。跳过。信息: {trade_info}", data=data)
            # 如果信息不完整，则记录日志。
            # (如果信息不全，记个日志说一下，这次买不了。)
            del strategy.pending_trade_info[d_name]
            # 从策略的 `pending_trade_info` 中删除该ETF的无效信息，避免后续混淆。
            # (把策略那边对应的这条无效计划也删掉，免得下次还用错。)
            return 0
            # 返回0，表示不进行交易。
            # (返回0，不买了。)

        if risk_per_share <= 1e-9:
            # 如果策略计算的每股风险过小（接近或等于0）。
            # (如果策略算出来每股风险几乎是0，或者是个负数，这不合理。)
            strategy.log(
                f"Sizer: 策略计算的 {d_name} 每股风险({risk_per_share:.2f})过小。跳过。", data=data)
            # 记录日志说明每股风险过小。
            # (记个日志说策略算出来的风险太小了，不正常，买不了。)
            del strategy.pending_trade_info[d_name]
            # 清理策略中的无效信息。
            # (把策略那边对应的计划删掉。)
            return 0
            # 返回0，不进行交易。
            # (返回0，不买了。)
        if amount_to_risk <= 1e-9:
            # 如果策略计算的本次交易允许的最大风险金额过小。
            # (如果策略算出来这次交易能承担的总风险几乎是0，或者是个负数。)
            strategy.log(
                f"Sizer: 策略计算的 {d_name} 最大风险金额({amount_to_risk:.2f})过小。跳过。", data=data)
            # 记录日志说明最大风险金额过小。
            # (记个日志说策略算出来的总风险太小了，不正常，买不了。)
            del strategy.pending_trade_info[d_name]
            # 清理策略中的无效信息。
            # (把策略那边对应的计划删掉。)
            return 0
            # 返回0，不进行交易。
            # (返回0，不买了。)

        # 2.2.4 核心计算：基于策略提供的风险信息计算头寸
        # (根据策略给的风险数据，来算到底买多少股。)
        size_raw = amount_to_risk / risk_per_share
        # 根据最大风险金额和每股风险计算原始的股票数量（可能带小数）。
        # (用最多能亏的钱除以每股亏的钱，得到一个初步的购买数量，这个数可能是小数。)
        size = int(size_raw / 100) * 100
        # 对原始数量向下取整到最近的100的倍数，符合A股交易规则（通常最小交易单位为100股）。
        # (按A股规矩，买股票得是100股的整数倍，所以把上面算出来的数量向下凑个整，比如算出来150股，就买100股。)

        if size <= 0:
            # 如果根据风险计算出的头寸数量小于或等于0。
            # (如果算出来要买的数量是0或者负数，那肯定是买不了的。)
            strategy.log(
                f"Sizer: 基于策略风险计算 {d_name} 的头寸为 {size}。风险/股: {risk_per_share:.2f}, 允许风险额: {amount_to_risk:.2f}", data=data)
            # 记录日志说明计算出的头寸为0或负数。
            # (记个日志说按风险算下来买不了，顺便把计算依据也记上。)
            del strategy.pending_trade_info[d_name]
            # 清理策略中的信息。
            # (把策略那边对应的计划删掉。)
            return 0
            # 返回0，不进行交易。
            # (返回0，不买了。)

        # 2.2.5 应用 Sizer 自身的全局限制
        # (除了策略给的风险，Sizer自己也有一些全局的限制，比如单个ETF不能买太多。)
        equity = self.broker.getvalue()
        # 获取当前账户总值。
        # (看看现在账户里总共有多少钱（包括现金和股票市值）。)
        max_pos_value_for_etf = equity * self.p.max_position_per_etf_percent
        # 根据Sizer参数中设定的单个ETF最大持仓比例，计算该ETF允许的最大持仓市值。
        # (用总资产乘以之前设定的单个ETF最大占比（比如30%），算出这只ETF最多能买多少钱的。)
        price_for_value_calc = entry_price
        # 使用策略提供的参考入场价来计算市值。
        # (用策略计划的那个买入参考价来算买多少股会花多少钱。)

        if price_for_value_calc <= 1e-9:
            # 如果策略提供的参考入场价无效（过小或为0）。
            # (如果策略给的买入价太小了，比如是0或者负数，这不合理。)
            strategy.log(
                f"Sizer: 策略提供的 {d_name} 参考入场价 ({price_for_value_calc:.2f}) 无效。", data=data)
            # 记录日志说明价格无效。
            # (记个日志说策略给的价格不对。)
            del strategy.pending_trade_info[d_name]
            # 清理策略中的信息。
            # (把策略那边对应的计划删掉。)
            return 0
            # 返回0，不进行交易。
            # (返回0，不买了。)

        size_limited_by_max_etf_pos = int(
            max_pos_value_for_etf / price_for_value_calc / 100) * 100
        # 根据单个ETF允许的最大持仓市值和参考入场价，计算允许的最大股数（同样向下取整到100的倍数）。
        # (根据这只ETF最多能买多少钱，以及它的价格，算出最多能买多少股，也要凑100的整数倍。)
        if size > size_limited_by_max_etf_pos:
            # 如果基于风险计算的头寸超过了单个ETF最大仓位限制所允许的股数。
            # (如果前面按风险算出来的数量，比按"单个ETF最多买多少"算出来的还多。)
            strategy.log(
                f"Sizer: {d_name} 头寸从 {size} 减少到 {size_limited_by_max_etf_pos} (受限于 max_position_per_etf_percent)。", data=data)
            # 记录日志说明头寸因达到最大ETF仓位限制而被减少。
            # (记个日志说因为单个ETF仓位限制，买的数量减少了。)
            size = size_limited_by_max_etf_pos
            # 将头寸调整为限制内的最大数量。
            # (那就按最大仓位允许的数量来买。)

        if size <= 0:
            # 如果经过最大ETF仓位限制调整后，头寸数量小于等于0。
            # (如果调整完发现买不了了，比如限制后变成0股了。)
            strategy.log(f"Sizer: {d_name} 头寸在最大ETF仓位限制后为 {size}。", data=data)
            # 记录日志。
            # (记个日志说因为仓位限制，最后买不了。)
            del strategy.pending_trade_info[d_name]
            # 清理策略中的信息。
            # (把策略那边对应的计划删掉。)
            return 0
            # 返回0，不进行交易。
            # (返回0，不买了。)

        # 2.2.6 检查现金是否足够
        # (最后再看看账户里的现金够不够买这么多。)
        potential_trade_total_cost = size * price_for_value_calc
        # 计算按当前头寸和参考入场价计算的潜在交易总成本。
        # (算一下按这个数量和价格买，大概要花多少钱。)
        if potential_trade_total_cost > cash:
            # 如果潜在交易总成本超过当前可用现金。
            # (如果要花的钱比现在账户里能用的现金还多。)
            size_limited_by_cash = int(cash / price_for_value_calc / 100) * 100
            # 根据可用现金和参考入场价，重新计算能买的最大股数。
            # (那就用能用的现金，看看能买多少股，也要凑100的整数倍。)
            if size_limited_by_cash < size:
                # 如果因现金不足导致能买的股数少于之前计算的股数。
                # (如果按现金算出来能买的数量，比之前算出来的数量还要少。)
                strategy.log(
                    f"Sizer: {d_name} 头寸从 {size} 减少到 {size_limited_by_cash} (受限于现金)。现金: {cash:.2f}, 预估成本: {potential_trade_total_cost:.2f}", data=data)
                # 记录日志说明头寸因现金不足而被减少。
                # (记个日志说因为钱不够，买的数量又减少了。)
                size = size_limited_by_cash
                # 更新头寸为现金允许的最大数量。
                # (那就按现金能买的最大数量来买。)

        if size <= 0:
            # 如果最终计算的头寸（经过所有限制后）小于等于0。
            # (如果最后算下来买不了了，比如因为钱不够最后变成0股了。)
            strategy.log(f"Sizer: {d_name} 最终计算头寸为 {size}。无法下单。", data=data)
            # 记录日志说明最终无法下单。
            # (记个日志说最后算出来买不了。)
            del strategy.pending_trade_info[d_name]
            # 清理策略中的信息。
            # (把策略那边对应的计划删掉。)
            return 0
            # 返回0，不进行交易。
            # (返回0，不买了。)

        # 2.2.7 Sizer 计算完成，返回最终头寸
        # (所有计算和检查都做完了，把最终决定买多少股告诉 `backtrader`。)
        strategy.log(f"Sizer为 {d_name} 计算头寸: {size} (基于策略风险信息)", data=data)
        # 记录最终为该ETF计算的头寸大小。
        # (记个日志，告诉大家最后算出来要买多少股，是根据策略给的风险信息，并考虑了各种限制后得到的。)

        # 注意：Sizer执行成功后，策略会在notify_order中清理pending_trade_info。
        # (这里只是个提醒：这个Sizer算完后，策略那边会在订单状态更新时清理掉之前存的交易计划。)
        return size
        # 返回最终计算得到的头寸大小。
        # (把最后算好的购买数量告诉 `backtrader`，它就会按这个数量去下单了。)

# 3. 自定义交易策略类 AShareETFStrategy
# (这部分定义了我们具体的交易策略，包括什么时候判断买入、什么时候判断卖出，以及如何管理风险等。)


class AShareETFStrategy(bt.Strategy):
    # 定义一个名为 `AShareETFStrategy` 的类，它继承自 `backtrader.Strategy` 类，用于实现A股ETF的交易策略。
    # (创建一个专门针对A股ETF的交易策略，这个策略是基于 `backtrader` 里面一个叫 `Strategy` 的基础策略改造的。)

    # 3.1 策略参数定义
    # (这里是给这个交易策略预设一些可以调整的选项，比如用到的技术指标的参数等。)
    params = (
        # 定义策略的参数。
        # (给这个策略预设一些可以调整的选项。)
        ('etf_type', 'trend'),
        # 定义参数 `etf_type`，默认值为 'trend'，用于指定策略是基于趋势交易还是区间交易。策略会根据这个参数决定基础交易类型。
        # (设置一个选项叫 'etf_type'，默认是 'trend'（趋势型），也可以设成 'range'（区间型），策略会根据这个来决定主要用哪种交易方法。)
        ('ema_medium_period', 60),
        # 定义参数 `ema_medium_period`，默认值为60，表示中期指数移动平均线（EMA）的周期。
        # (设置中期EMA均线的计算周期，默认是60天。)
        ('ema_long_period', 120),
        # 定义参数 `ema_long_period`，默认值为120，表示长期EMA的周期。
        # (设置长期EMA均线的计算周期，默认是120天。)
        ('adx_period', 14),
        # 定义参数 `adx_period`，默认值为14，表示平均动向指数（ADX）的周期。
        # (设置ADX指标的计算周期，默认是14天。)
        ('atr_period', 20),
        # 定义参数 `atr_period`，默认值为20，表示平均真实波幅（ATR）的周期。
        # (设置ATR指标的计算周期，默认是20天，策略仍需ATR计算止损。)
        ('bbands_period', 20),
        # 定义参数 `bbands_period`，默认值为20，表示布林带（Bollinger Bands）的周期。
        # (设置布林带指标的计算周期，默认是20天。)
        ('bbands_devfactor', 2.0),
        # 定义参数 `bbands_devfactor`，默认值为2.0，表示布林带的标准差倍数。
        # (设置布林带上下轨是几倍标准差，默认是2倍。)
        ('rsi_period', 14),
        # 定义参数 `rsi_period`，默认值为14，表示相对强弱指数（RSI）的周期。
        # (设置RSI指标的计算周期，默认是14天。)
        ('rsi_oversold', 30),
        # 定义参数 `rsi_oversold`，默认值为30，表示RSI的超卖阈值。
        # (设置RSI指标低于多少算超卖，默认是30。)
        ('trend_breakout_lookback', 60),
        # 定义参数 `trend_breakout_lookback`，默认值为60，表示趋势突破时回顾的K线数量（用于寻找前期高点）。
        # (设置在判断趋势突破时，往前看多少根K线来找最近的最高点，默认是60根。)
        ('trend_volume_avg_period', 20),
        # 定义参数 `trend_volume_avg_period`，默认值为20，表示趋势交易中计算平均成交量的周期。
        # (设置在趋势交易中，计算平均成交量时用多少天的成交量，默认是20天。)
        ('trend_volume_ratio_min', 1.1),
        # 定义参数 `trend_volume_ratio_min`，默认值为1.1，表示趋势突破时当前成交量相对于平均成交量的最小倍数。
        # (设置在趋势突破时，当天的成交量至少是平均成交量的多少倍才算有效，默认是1.1倍。)
        ('trend_stop_loss_atr_mult', 2.5),
        # 定义参数 `trend_stop_loss_atr_mult`，默认值为2.5，表示趋势交易中止损价格基于ATR的倍数。策略用这个计算止损价。
        # (设置在趋势交易中，止损位置是入场价减去几倍的ATR值，默认是2.5倍。这个是策略用来算止损价的。)
        ('trend_take_profit_rratio', 2.0),
        # 定义参数 `trend_take_profit_rratio`，默认值为2.0，表示趋势交易中止盈目标相对于风险的倍数（盈亏比）。
        # (设置在趋势交易中，目标赚多少钱是亏损风险的几倍，默认是2倍。)
        ('range_stop_loss_buffer', 0.005),
        # 定义参数 `range_stop_loss_buffer`，默认值为0.005 (0.5%)，表示区间交易中止损价格相对于入场点（通常是K线低点）的缓冲百分比。策略用这个计算止损价。
        # (设置在区间交易中，止损位置比买入那根K线的最低点再低百分之多少，默认是0.5%。这个也是策略用来算止损价的。)
        ('max_total_account_risk_percent', 0.06),
        # 定义参数 `max_total_account_risk_percent`，默认值为0.06 (6%)，表示整个账户允许的最大单笔交易风险占总资金的百分比。
        # (设置整个账户在任何一笔交易中，最多允许亏损总资金的百分之多少，默认是6%。)
        ('drawdown_level1_threshold', 0.05),
        # 定义参数 `drawdown_level1_threshold`，默认值为0.05 (5%)，表示一级回撤警报阈值。
        # (设置当账户从最高点回撤达到5%时，触发一级警报。)
        ('drawdown_level2_threshold', 0.10),
        # 定义参数 `drawdown_level2_threshold`，默认值为0.10 (10%)，表示二级回撤警报阈值，通常会触发更严格的风控措施（如暂停交易）。
        # (设置当账户从最高点回撤达到10%时，触发二级警报，可能会暂停交易。)
        ('risk_per_trade_trend', 0.01),
        # 新增参数：定义趋势型交易的单笔风险百分比，默认值为0.01 (1%)。
        # (给趋势型交易设置一个单笔能亏多少钱的比例，默认是总资金的1%。)
        ('risk_per_trade_range', 0.005),
        # 新增参数：定义区间型交易的单笔风险百分比，默认值为0.005 (0.5%)。
        # (给区间型交易设置一个单笔能亏多少钱的比例，默认是总资金的0.5%。)
    )

    # 3.2 日志记录方法 log
    # (这个函数是策略内部用来打印信息的，方便在回测过程中观察策略的运行状态和决策。)
    def log(self, txt, dt=None, data=None):
        # 定义 `log` 方法，用于在策略执行过程中输出日志信息。
        # (定义一个名叫 `log` 的函数，专门用来在策略跑的时候打印一些信息，方便我们看过程。)
        return
        # 当前日志功能被禁用。若要启用，请注释掉或删除此行。
        # (这行代码 `return` 会让日志功能不生效。如果想看日志，就把这行删掉或者在前面加个 `#` 注释掉它。)
        _data = data if data is not None else (
            self.datas[0] if self.datas else None)
        # 确定日志关联的数据对象：如果传入了 `data` 参数则使用它；否则，如果策略有数据源，则使用第一个数据源；如果都没有，则为 `None`。
        # (看看调用log的时候有没有指定是哪个股票的数据，有就用那个；没有的话，如果策略本身在处理股票数据，就用第一个；如果啥数据都没有，那就没办法了。)

        log_dt_str = ""
        # 初始化日志日期时间字符串为空。
        # (准备一个空字符串，用来放日志的时间信息。)
        if _data and hasattr(_data, 'datetime') and hasattr(_data.datetime, 'date') and len(_data.datetime) > 0:
            # 如果 `_data` 存在，并且它有 `datetime` 属性（通常是时间序列），并且该时间序列不为空。
            # (如果咱们有具体的股票数据，而且这个数据里面有时间信息（比如每天的日期），并且时间信息不是空的。)
            dt_val = _data.datetime.date(0)
            # 获取当前K线（bar）的日期。 `_data.datetime.date(0)` 返回当前bar的日期对象。
            # (拿到当前这根K线对应的日期。)
            if isinstance(dt_val, (datetime.date, datetime.datetime)):
                # 如果获取到的是标准的日期或日期时间对象。
                # (如果拿到的日期是正经的日期格式。)
                log_dt_str = dt_val.isoformat()
                # 将日期格式化为 ISO 格式的字符串 (例如 'YYYY-MM-DD')。
                # (就把日期变成 '年-月-日' 这种标准文字格式。)
            elif isinstance(dt_val, float):
                # 如果获取到的是浮点数（backtrader 有时会将日期表示为浮点数）。
                # (有时候 `backtrader` 里的日期可能是一个数字，不是直接的日期格式。)
                log_dt_str = bt.num2date(dt_val).date().isoformat()
                # 使用 `bt.num2date` 将浮点数转换为日期时间对象，然后取日期部分，再格式化为 ISO 字符串。
                # (那就用 `backtrader` 提供的工具把这个数字转成日期，然后再变成标准文字格式。)
            else:
                # 其他情况下，直接将获取到的值转换为字符串。
                # (如果都不是上面两种情况，就直接把它变成文字。)
                log_dt_str = str(dt_val)

        elif dt:
            # 如果没有传入 `_data` 对象，但传入了 `dt` 参数（通常是一个日期时间对象）。
            # (如果没股票数据，但是外面传了时间进来。)
            log_dt_str = dt.isoformat() if isinstance(
                dt, (datetime.date, datetime.datetime)) else str(dt)
            # 如果 `dt` 是日期或日期时间对象，则格式化为 ISO 格式；否则，转换为字符串。
            # (如果传进来的是正经的日期时间，就变成标准格式；如果不是，就直接变成文字。)
        else:
            # 如果既没有 `_data` 也没有 `dt` 参数。
            # (如果既没股票数据，外面也没传时间。)
            log_dt_str = datetime.datetime.now().date().isoformat()
            # 使用当前系统的日期，并格式化为 ISO 格式。
            # (那就用电脑现在的日期，变成标准格式。)

        prefix = ""
        # 初始化日志前缀为空字符串。
        # (准备一个空字符串，用来放日志的前缀，比如股票代码。)
        if _data and hasattr(_data, '_name') and _data._name:
            # 如果 `_data` 存在，并且它有 `_name` 属性（通常是数据源的名称，如股票代码），并且 `_name` 不为空。
            # (如果咱们有具体的股票数据，而且这个数据有名字（比如股票代码），并且名字不是空的。)
            prefix = f"[{_data._name}] "
            # 设置前缀为 "[数据名称] " 的格式。
            # (就把前缀设置成 "[股票代码] " 这种样子。)

        print(f"{log_dt_str} {prefix}{txt}")
        # 打印格式化的日志消息，包括日期时间、前缀（如果存在）和日志文本 `txt`。
        # (把时间、前缀（股票代码）和要记录的内容 `txt` 一起打印出来。)

    # 3.3 策略初始化方法 __init__
    # (这个函数在策略刚被创建（实例化）的时候会自动运行一次，用来做一些初始化的准备工作，比如设置好要用的技术指标。)
    def __init__(self):
        # 定义策略的构造函数 `__init__`，在策略实例化时执行。
        # (这是策略刚被创建出来的时候要做的事情，比如准备好各种计算工具和记录本。)
        self.closes = {d._name: d.close for d in self.datas}
        # 为每个数据源（ETF）创建一个收盘价序列的字典。键是数据源名称，值是对应的收盘价数据线。
        # (为我们关注的每一只ETF都准备好它的收盘价数据，存到一个叫 `self.closes` 的本子里，用ETF的名字来区分。)
        self.opens = {d._name: d.open for d in self.datas}
        # 为每个数据源创建一个开盘价序列的字典。
        # (同样，为每一只ETF准备好它的开盘价数据，存到 `self.opens` 本子里。)
        self.highs = {d._name: d.high for d in self.datas}
        # 为每个数据源创建一个最高价序列的字典。
        # (为每一只ETF准备好它的最高价数据，存到 `self.highs` 本子里。)
        self.lows = {d._name: d.low for d in self.datas}
        # 为每个数据源创建一个最低价序列的字典。
        # (为每一只ETF准备好它的最低价数据，存到 `self.lows` 本子里。)
        self.volumes = {d._name: d.volume for d in self.datas}
        # 为每个数据源创建一个成交量序列的字典。
        # (为每一只ETF准备好它的成交量数据，存到 `self.volumes` 本子里。)

        # 3.3.1 技术指标初始化
        # (这里是把策略中要用到的各种技术指标（比如均线、布林带等）都设置好，让它们能根据价格数据自动计算。)
        self.emas_medium = {d._name: bt.indicators.EMA(
            d.close, period=self.params.ema_medium_period) for d in self.datas}
        # 为每个数据源初始化中期EMA指标，使用其收盘价和策略参数中定义的周期。
        # (为每一只ETF都创建一个中期EMA均线指标，用它的收盘价和我们之前设置的中期周期来算，结果存到 `self.emas_medium` 本子里。)
        self.emas_long = {d._name: bt.indicators.EMA(
            d.close, period=self.params.ema_long_period) for d in self.datas}
        # 为每个数据源初始化长期EMA指标。
        # (为每一只ETF都创建一个长期EMA均线指标，结果存到 `self.emas_long` 本子里。)
        self.adxs = {d._name: bt.indicators.ADX(
            d, period=self.params.adx_period) for d in self.datas}
        # 为每个数据源初始化ADX指标。ADX需要传入整个数据对象 `d` (包含高、低、收盘价)。
        # (为每一只ETF都创建一个ADX趋势强度指标，结果存到 `self.adxs` 本子里。)
        self.atrs = {d._name: bt.indicators.ATR(
            d, period=self.params.atr_period) for d in self.datas}
        # 为每个数据源初始化ATR指标。ATR也需要传入整个数据对象 `d`。策略仍需ATR计算止损。
        # (为每一只ETF都创建一个ATR波动率指标，结果存到 `self.atrs` 本子里。这个指标策略后面会用来算止损。)
        self.bbands = {d._name: bt.indicators.BollingerBands(
            d.close, period=self.params.bbands_period, devfactor=self.params.bbands_devfactor) for d in self.datas}
        # 为每个数据源初始化布林带指标，使用其收盘价和策略参数中定义的周期及标准差倍数。
        # (为每一只ETF都创建一个布林带指标，结果存到 `self.bbands` 本子里。)
        self.rsis = {d._name: bt.indicators.RSI(
            d.close, period=self.params.rsi_period) for d in self.datas}
        # 为每个数据源初始化RSI指标。
        # (为每一只ETF都创建一个RSI相对强弱指标，结果存到 `self.rsis` 本子里。)
        self.highest_highs = {d._name: bt.indicators.Highest(
            d.high, period=self.params.trend_breakout_lookback) for d in self.datas}
        # 为每个数据源初始化N周期内最高价指标，使用其最高价和策略参数中定义的回顾期。
        # (为每一只ETF都创建一个"过去一段时间最高价"的指标，结果存到 `self.highest_highs` 本子里。)
        self.sma_volumes = {d._name: bt.indicators.SMA(
            d.volume, period=self.params.trend_volume_avg_period) for d in self.datas}
        # 为每个数据源初始化成交量简单移动平均线（SMA）指标。
        # (为每一只ETF都创建一个成交量均线指标，结果存到 `self.sma_volumes` 本子里。)

        # 3.3.2 订单和持仓状态跟踪初始化
        # (这些是用来记录订单状态和持仓信息的本子。)
        self.orders = {d._name: None for d in self.datas}
        # 初始化一个字典 `self.orders`，用于跟踪每个数据源的活动订单。初始时均无活动订单，故值为 `None`。
        # (准备一个叫 `self.orders` 的本子，用来记录给每只ETF下的单子，一开始都是空的。)
        self.buy_prices = {d._name: None for d in self.datas}
        # 初始化一个字典 `self.buy_prices`，用于记录每个数据源的买入价格。初始时均未买入，故值为 `None`。
        # (准备一个叫 `self.buy_prices` 的本子，用来记录每只ETF的买入价格，一开始都是空的。)
        self.position_types = {d._name: None for d in self.datas}
        # 初始化一个字典 `self.position_types`，用于记录每个数据源持仓的类型（如 'trend' 或 'range'）。初始时均无持仓，故值为 `None`。
        # (准备一个叫 `self.position_types` 的本子，用来记录买入每只ETF是基于什么类型的信号（比如趋势型还是区间型），一开始都是空的。)

        # 3.3.3 风险管理状态初始化
        # (这些是用来做风险控制的变量，比如记录账户最高赚到过多少钱，有没有触发风险警报等。)
        self.high_water_mark = self.broker.startingcash
        # 初始化 `high_water_mark` (历史最高账户净值) 为初始资金。
        # (准备一个变量 `self.high_water_mark`，记录账户资金的最高点，一开始就是我们的本金。)
        self.drawdown_level1_triggered = False
        # 初始化一级回撤警报触发标志为 `False`。
        # (准备一个开关 `self.drawdown_level1_triggered`，记录一级回撤警报有没有响过，一开始是关着的（没响过）。)
        self.halt_trading = False
        # 初始化暂停交易标志为 `False`。
        # (准备一个开关 `self.halt_trading`，记录要不要暂停交易，一开始是关着的（不暂停）。)
        self.current_risk_multiplier = 1.0
        # 初始化当前风险乘数为1.0。当触发回撤警报时，此乘数可能被调整以降低风险。策略控制风险乘数。
        # (准备一个风险调整系数 `self.current_risk_multiplier`，默认是1.0，如果遇到大的回撤，可能会把它调小来降低风险。)

        # 3.3.4 待处理交易信息初始化
        # (这个本子是策略和Sizer之间沟通用的，策略把计算好的交易计划放这里，Sizer再从这里拿去算买多少。)
        self.pending_trade_info = {}
        # 初始化一个空字典 `self.pending_trade_info`，用于在下单前临时存储待处理的交易信息（如入场价、止损价、风险等），供Sizer读取。
        # (创建一个叫 `self.pending_trade_info` 的空本子，用来在下单前临时存放交易计划信息，比如计划买入价、止损价、愿意承担的风险等。Sizer（算数量的工具）会从这里读取这些信息。)

        self.trade_details_by_type = {
            'trend': {'pnl': 0.0, 'count': 0, 'wins': 0, 'losses': 0, 'total_pnl_wins': 0.0, 'total_pnl_losses': 0.0},
            'range': {'pnl': 0.0, 'count': 0, 'wins': 0, 'losses': 0, 'total_pnl_wins': 0.0, 'total_pnl_losses': 0.0},
            'unknown': {'pnl': 0.0, 'count': 0, 'wins': 0, 'losses': 0, 'total_pnl_wins': 0.0, 'total_pnl_losses': 0.0}
        }
        self.final_trade_stats_by_type = {} # 用于在 stop() 中赋值

    # 3.4 订单状态通知方法 notify_order
    # (这个函数会在我们下的订单状态发生变化时（比如订单提交了、成交了、取消了）被 `backtrader` 自动调用，我们可以在这里处理相应的逻辑。)
    def notify_order(self, order):
        # 定义 `notify_order` 方法，当订单状态发生变化时由Backtrader调用。
        # (定义一个名叫 `notify_order` 的函数，每当我们的订单有新情况（比如刚提交、被接受、成交了、或者失败了），`backtrader` 就会来告诉这个函数。)
        order_data_name = order.data._name if hasattr(
            order.data, '_name') else 'Unknown_Data'
        # 获取订单关联的数据源名称（ETF代码）。如果无法获取，则标记为 'Unknown_Data'。
        # (看看这个订单是哪个股票的，如果知道名字就用名字，不知道就叫 'Unknown_Data'。)

        # 3.4.1 订单提交/接受处理
        # (当订单刚发出去或者被交易所接受了，我们在这里记录一下。)
        if order.status in [order.Submitted, order.Accepted]:
            # 如果订单状态是已提交 (Submitted) 或已接受 (Accepted)。
            # (如果订单已经发出去了或者交易所已经收到了，但还没成交。)
            self.log(
                f'订单 {order.ref} 已提交/接受 for {order_data_name}', data=order.data)
            # 记录订单提交/接受的日志。
            # (就记个日志说一下这个订单发出去了或者被接受了。)
            if order.parent is None:
                # 如果这是一个主订单（非括号单的止损或止盈部分）。
                # (如果这个订单不是某个大订单里的小订单（比如不是止损单或止盈单，而是主要的买入或卖出单）。)
                self.orders[order_data_name] = order
                # 将此主订单存储在对应数据源的 `self.orders` 字典中，用于跟踪。
                # (就把这个订单记在对应股票的 `self.orders` 本子里，方便以后查。)
            return
            # 从方法返回，因为订单尚未最终确定（未成交、未取消等）。
            # (这事儿处理完了，先不用往下走了，等订单有更新再说。)

        # 3.4.2 清理 pending_trade_info
        # (当一个订单处理完了（不管成功还是失败），之前为它准备的交易计划信息就没用了，需要清理掉。)
        if order_data_name in self.pending_trade_info:
            # 检查当前订单关联的ETF是否在 `pending_trade_info` 中有待处理信息。
            # (看看这个ETF之前是不是有存在 `pending_trade_info` 本子里的交易计划。)
            if not order.alive():
                # 如果订单不再存活（即已完成、取消、拒绝、过期等）。
                # (如果这个订单已经结束了，比如成交了、被取消了、或者因为其他原因失败了。)
                self.log(
                    f'订单 {order.ref} 结束，清理 {order_data_name} 的 pending_trade_info', data=order.data)
                # 记录日志，说明订单结束，将清理对应的待处理信息。
                # (记个日志说订单结束了，要把之前为它准备的交易计划清理掉。)
                del self.pending_trade_info[order_data_name]
                # 从 `pending_trade_info` 字典中删除该ETF的条目。
                # (从 `pending_trade_info` 本子里删掉这个ETF的计划。)
            elif order.status in [order.Margin, order.Rejected]:
                # 如果订单因保证金不足 (Margin) 或被拒绝 (Rejected) 而失败。
                # (如果订单是因为钱不够或者被交易所拒绝了而失败。)
                self.log(
                    f'订单 {order.ref} 失败 ({order.getstatusname()}), 清理 {order_data_name} 的 pending_trade_info', data=order.data)
                # 记录日志，说明订单失败，将清理对应的待处理信息。
                # (记个日志说订单失败了，也要清理对应的交易计划。)
                del self.pending_trade_info[order_data_name]
                # 从 `pending_trade_info` 字典中删除该ETF的条目。
                # (从 `pending_trade_info` 本子里删掉这个ETF的计划。)

        # 3.4.3 订单完成处理
        # (当订单成功成交了，我们在这里记录成交信息。)
        if order.status in [order.Completed]:
            # 如果订单状态是已完成 (Completed)，即成功执行。
            # (如果订单已经成功交易了。)
            if order.isbuy():
                # 如果是买入订单。
                # (如果这是一个买单。)
                self.log(
                    f'买入执行 for {order_data_name} @ {order.executed.price:.2f}, 数量: {order.executed.size}, 成本: {order.executed.value:.2f}, 佣金: {order.executed.comm:.2f}', data=order.data)
                # 记录买入执行的详细日志，包括成交价格、数量、成本和佣金。
                # (就记个日志说买入成功了，买了多少，什么价格，花了多少钱，手续费多少。)
                self.buy_prices[order_data_name] = order.executed.price
                # 将成交价格存储在 `self.buy_prices` 字典中，以备后续使用（如计算盈亏）。
                # (把买入的价格记在 `self.buy_prices` 本子里，以后算赚了还是亏了可能会用到。)
            elif order.issell():
                # 如果是卖出订单。
                # (如果这是一个卖单。)
                self.log(
                    f'卖出执行 for {order_data_name} @ {order.executed.price:.2f}, 数量: {order.executed.size}, 价值: {order.executed.value:.2f}, 佣金: {order.executed.comm:.2f}', data=order.data)
                # 记录卖出执行的详细日志。
                # (就记个日志说卖出成功了，卖了多少，什么价格，收回多少钱，手续费多少。)

        # 3.4.4 订单失败/取消处理
        # (当订单因为各种原因没能成功执行，我们在这里记录一下。)
        elif order.status in [order.Canceled, order.Margin, order.Rejected, order.Expired]:
            # 如果订单状态是已取消 (Canceled)、保证金不足 (Margin)、被拒绝 (Rejected) 或已过期 (Expired)。
            # (如果订单被取消了、或者因为钱不够、或者被交易所拒绝了、或者过期了，总之就是没成功。)
            self.log(
                f'订单 {order.ref} for {order_data_name} 取消/保证金/拒绝/过期: 状态 {order.getstatusname()}', data=order.data)
            # 记录订单未能成功执行的日志，并说明具体状态。
            # (就记个日志说这个订单没成功，具体是什么原因。)

        # 3.4.5 清理已结束的订单跟踪
        # (如果之前跟踪的订单现在结束了，就把它从跟踪列表里去掉。)
        if self.orders.get(order_data_name) == order and not order.alive():
            # 如果 `self.orders` 字典中存储的是当前这个订单，并且当前订单不再存活。
            # (如果之前记在 `self.orders` 本子里的这个股票的订单就是现在这个订单，并且这个订单已经结束了（不管成功还是失败）。)
            self.orders[order_data_name] = None
            # 将 `self.orders` 字典中对应数据源的记录清除（设置为 `None`），表示当前无活动主订单。
            # (就把 `self.orders` 本子里对应这个股票的记录清空，表示现在没有正在进行的订单了。)

    # 3.5 交易完成通知方法 notify_trade
    # (这个函数会在一笔完整的交易（包括开仓和平仓）结束后被 `backtrader` 自动调用，我们可以在这里记录这笔交易的盈亏情况。)
    def notify_trade(self, trade):
        # 定义 `notify_trade` 方法，当一笔交易完成 (开仓和平仓都已发生) 时由Backtrader调用。
        # (定义一个名叫 `notify_trade` 的函数，当一买一卖完整结束形成一笔交易后（比如之前买了，现在卖了），`backtrader` 就会来告诉这个函数。)
        if not trade.isclosed:
            # 如果交易尚未关闭 (即只有开仓，没有平仓)。
            # (如果这笔交易还没结束，比如只买了还没卖。)
            return
            # 从方法返回，不处理未关闭的交易。
            # (那就先不管它，等卖了再说。)
        data_name = trade.data._name if hasattr(
            trade.data, '_name') else 'Unknown_Data'
        # 获取交易关联的数据源名称（ETF代码）。
        # (看看这笔交易是哪个股票的。)
        self.log(
            f'交易利润 for {data_name}, 毛利 {trade.pnl:.2f}, 净利 {trade.pnlcomm:.2f}, 持仓类型: {self.position_types.get(data_name, "N/A")}', data=trade.data)
        # 记录交易的盈利情况 (毛利润 `trade.pnl` 和扣除佣金后的净利润 `trade.pnlcomm`) 以及该持仓的类型。
        # (记个日志说这笔交易赚了还是亏了多少钱（没算手续费的和算了手续费的），以及当初是按什么类型（趋势/区间）买的。)

        # 3.5.1 清理持仓相关信息
        # (交易结束后，之前记录的关于这个持仓的信息（比如持仓类型、买入价）就可以清掉了。)
        if data_name in self.position_types:
            # 如果 `self.position_types` 字典中存在该数据源的记录。
            # (如果 `self.position_types` 本子里有这个股票的记录。)
            self.position_types[data_name] = None
            # 将对应数据源的持仓类型重置为 `None`，因为交易已关闭。
            # (就把这个股票的持仓类型记录清空，因为已经卖掉了，不再持有了。)
        if data_name in self.buy_prices:
            # 如果 `self.buy_prices` 字典中存在该数据源的记录。
            # (如果 `self.buy_prices` 本子里有这个股票的记录。)
            self.buy_prices[data_name] = None
            # 将对应数据源的买入价格重置为 `None`。
            # (就把这个股票的买入价格记录清空。)

    # 3.6 账户现金/总值变化通知方法 notify_cashvalue
    # (这个函数会在账户里的现金或者总资产（现金+股票市值）发生变化时被 `backtrader` 自动调用，我们可以在这里做风险监控，比如计算最大回撤。)
    def notify_cashvalue(self, cash, value):
        # 定义 `notify_cashvalue` 方法，当账户现金或总价值发生变化时由Backtrader调用。
        # (定义一个名叫 `notify_cashvalue` 的函数，每当账户里的现金或者总资产变化了，`backtrader` 就会来告诉这个函数。)

        # 3.6.1 更新历史最高净值并计算当前回撤
        # (记录账户曾经达到过的最高资金，并计算当前从最高点回撤了多少。)
        self.high_water_mark = max(self.high_water_mark, value)
        # 更新 `high_water_mark` (历史最高账户价值) 为当前账户总价值 `value` 与原记录中的较大者。
        # (看看现在的总资产是不是比以前最多的时候还要多，如果是，就更新一下记录 `self.high_water_mark`。)
        drawdown = (self.high_water_mark - value) / \
            self.high_water_mark if self.high_water_mark > 1e-9 else 0
        # 计算当前的回撤百分比：(历史最高价值 - 当前价值) / 历史最高价值。如果历史最高价值接近0（避免除以0错误），则回撤为0。
        # (算一下从账户钱最多的时候到现在，回撤了多少百分比。如果以前账户就没啥钱（比如接近0），那就当没回撤。)

        # 3.6.2 二级回撤处理（暂停交易）
        # (如果回撤太大了，达到二级警报线，就暂停交易。)
        if drawdown > self.params.drawdown_level2_threshold:
            # 如果当前回撤超过了策略参数中定义的二级回撤阈值 (例如10%)。
            # (如果回撤超过了咱们设定的二级警报线，比如10%。)
            if not self.halt_trading:
                # 如果当前尚未暂停交易。
                # (如果之前还没暂停交易。)
                self.log(
                    f'!!! 红色警报: 回撤 {drawdown*100:.2f}% > {self.params.drawdown_level2_threshold*100:.0f}%. 暂停交易 !!!')
                # 记录红色警报日志，说明回撤严重，将暂停交易。
                # (就记个红色警报日志，说亏得太多了，超过二级线了，要暂停交易！)
                self.halt_trading = True
                # 设置 `halt_trading` 标志为 `True`，以在 `next` 方法中暂停所有新的交易活动。
                # (把暂停交易的开关 `self.halt_trading` 打开。)
        # 3.6.3 一级回撤处理（降低风险）
        # (如果回撤达到一级警报线，就降低后续交易的风险。)
        elif drawdown > self.params.drawdown_level1_threshold:
            # 如果当前回撤超过了一级回撤阈值但未超过二级阈值 (例如5%-10%)。
            # (如果回撤超过了一级警报线，但还没到二级那么严重，比如亏了5%但没到10%。)
            if not self.drawdown_level1_triggered:
                # 如果一级回撤警报尚未被触发过（避免重复触发）。
                # (如果之前一级警报还没响过。)
                self.log(
                    f'-- 黄色警报: 回撤 {drawdown*100:.2f}% > {self.params.drawdown_level1_threshold*100:.0f}%. 降低风险.--')
                # 记录黄色警报日志，说明回撤达到一级，将降低风险。
                # (就记个黄色警报日志，说亏损达到一级线了，要降低点风险。)
                self.drawdown_level1_triggered = True
                # 设置 `drawdown_level1_triggered` 标志为 `True`，表示一级警报已触发。
                # (把一级警报的标记 `self.drawdown_level1_triggered` 打开，表示响过了。)
                self.current_risk_multiplier = 0.5
                # 将当前风险乘数 `self.current_risk_multiplier` 减半 (例如从1.0降至0.5)，以减少后续交易的头寸规模。
                # (把风险调整系数 `self.current_risk_multiplier` 减半，比如从1.0变成0.5，这样以后买股票就会少买点。)
        # 3.6.4 回撤恢复处理
        # (如果之前触发了警报，现在回撤情况好转了，就恢复正常的交易或风险水平。)
        else:
            # 如果当前回撤低于一级回撤阈值 (例如小于5%)，表示情况好转。
            # (如果回撤又回到一级警报线以下了，比如亏损小于5%了，说明情况好转了。)
            if self.halt_trading:
                # 如果之前是暂停交易状态（即曾触发二级回撤）。
                # (如果之前是暂停交易的状态。)
                self.log('--- 交易恢复 (回撤低于二级) ---')
                # 记录日志，说明交易已恢复 (因为回撤已低于二级阈值，尽管可能仍高于一级)。
                # (记个日志说交易恢复了，因为亏损已经回到二级线以下了。)
                self.halt_trading = False
                # 将 `halt_trading` 标志设置回 `False`，允许进行新的交易。
                # (把暂停交易的开关 `self.halt_trading` 关掉。)
                if drawdown <= self.params.drawdown_level1_threshold:
                    # 如果回撤不仅低于二级阈值，同时也低于一级回撤阈值。
                    # (如果亏损也回到了一级线以下了。)
                    if self.drawdown_level1_triggered:
                        # 并且之前一级警报确实响过。
                        # (如果之前一级警报响过。)
                        self.log(
                            '--- 风险水平恢复 (回撤低于一级) ---')
                        # 记录日志，说明风险水平也已恢复正常。
                        # (记个日志说风险水平恢复正常了。)
                        self.drawdown_level1_triggered = False
                        # 重置一级回撤触发标志。
                        # (把一级警报的标记 `self.drawdown_level1_triggered` 关掉。)
                        self.current_risk_multiplier = 1.0
                        # 将风险乘数恢复到1.0。
                        # (把风险调整系数 `self.current_risk_multiplier` 恢复到1.0。)
                elif self.drawdown_level1_triggered:
                    # 如果交易已恢复（说明之前是halt_trading=True，现在回撤低于二级线），但回撤仍在1级和2级之间。
                    # (如果亏损在一级线和二级线之间，但交易已经恢复了（说明之前是暂停交易状态）。)
                    self.current_risk_multiplier = 0.5
                    # 风险乘数保持在0.5（因为仍处于一级回撤区间）。
                    # (风险调整系数还是保持0.5，因为还在一级警报的范围内。)

            elif self.drawdown_level1_triggered and drawdown <= self.params.drawdown_level1_threshold:
                # 如果之前一级回撤警报被触发过，当前回撤已低于一级阈值，并且之前未暂停交易（即未触发二级回撤）。
                # (如果之前一级警报响过，现在亏损回到一级线以下了，并且之前没有暂停交易。)
                self.log('--- 风险水平恢复 (回撤低于一级) ---')
                # 记录日志，说明风险水平已恢复正常。
                # (记个日志说风险水平恢复正常了。)
                self.drawdown_level1_triggered = False
                # 重置一级回撤触发标志。
                # (把一级警报的标记 `self.drawdown_level1_triggered` 关掉。)
                self.current_risk_multiplier = 1.0
                # 将风险乘数恢复到1.0。
                # (把风险调整系数 `self.current_risk_multiplier` 恢复到1.0。)

    # 3.7 K线处理核心方法 next
    # (这个函数是策略最核心的部分，每当有新的一根K线数据来了，`backtrader` 就会运行一次这个函数。我们在这里判断交易信号，并执行买卖操作。)
    def next(self):
        # 定义 `next` 方法，每个新的K线数据到达时由Backtrader调用。
        # (定义一个名叫 `next` 的函数，每当有新的一根K线数据来了（比如一天结束了，有了今天的收盘价），`backtrader` 就会运行一次这个函数。)

        # 3.7.1 暂停交易逻辑
        # (如果之前因为风险太大暂停交易了，这里就只做平仓操作，不看新的买入机会。)
        if self.halt_trading:
            # 如果 `halt_trading` 标志为 `True` (即交易已因高回撤而暂停)。
            # (如果现在是暂停交易状态（`self.halt_trading` 是开着的）。)
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
                        f'暂停中: 尝试关闭 {d_name} 的仓位, 数量: {position.size}', data=d_obj)
                    # 记录日志，说明因交易暂停而尝试平仓。
                    # (记个日志说因为暂停交易了，要赶紧把手上的这只ETF卖掉。)
                    order_close = self.close(data=d_obj)
                    # 发出市价平仓订单。
                    # (下一个卖出指令，把这只ETF卖掉。)
                    if order_close:
                        # 如果成功创建平仓订单。
                        # (如果卖出指令成功发出去了。)
                        self.orders[d_name] = order_close
                        # 将此平仓订单存储在 `self.orders` 字典中进行跟踪。
                        # (就把这个卖单记在 `self.orders` 本子里，方便跟踪。)
                    else:
                        # 如果未能创建平仓订单（例如，某些情况下broker可能不允许）。
                        # (如果卖出指令没发出去，比如某些特殊情况。)
                        self.log(
                            f'暂停中: 无法为 {d_name} 创建平仓订单', data=d_obj)
                        # 记录日志，说明平仓失败。
                        # (记个日志说卖单没发出去。)
            return
            # 在暂停交易状态下，执行完必要的平仓检查后，直接返回，不进行新的开仓信号判断。
            # (暂停交易状态下，除了平仓，其他啥也不干了，直接结束这次 `next` 的运行。)

        # 3.7.2 遍历数据源进行交易决策
        # (对我们关注的每一只ETF，都检查一下有没有交易机会。)
        for i, d_obj in enumerate(self.datas):
            # 遍历所有数据源（ETF）及其索引。
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

            # 3.7.2.1 跳过条件检查
            # (如果这只ETF已经有单子在处理，或者已经持有了，或者已经有交易计划了，就先不管它。)
            if order or position.size != 0 or d_name in self.pending_trade_info:
                # 如果当前ETF有活动订单，或已有持仓，或已存在于 `pending_trade_info` (意味着Sizer正在处理或即将处理)，则跳过此ETF。
                # (如果这只ETF有正在处理的订单，或者已经持有仓位了，或者它的交易计划已经在 `pending_trade_info` 本子里等着Sizer处理了，那就先跳过它，看看别的ETF。)
                continue
                # 继续下一次循环，处理下一个数据源。
                # (那就先不看它了，等处理完了再说。)

            # 3.7.2.2 准备数据和指标值
            # (获取当前K线的数据和计算好的技术指标值，为后续判断做准备。)
            market_state = 'UNCERTAIN_DO_NOT_TRADE'
            # 初始化市场状态为 'UNCERTAIN_DO_NOT_TRADE' (不确定，不交易)。
            # (先假设市场情况不明朗，不适合交易。)
            current_close = self.closes[d_name][0]
            # 获取当前K线的收盘价。 `[0]` 表示当前最新的值。
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
            # 获取中期EMA的前一个周期的值。 `[-1]` 表示上一个值。
            # (拿到这只ETF的中期均线上一个周期的值。)
            ema_long_val = self.emas_long[d_name][0]
            # 获取长期EMA的当前值。
            # (拿到这只ETF的长期均线现在的值。)
            ema_long_prev = self.emas_long[d_name][-1]
            # 获取长期EMA的前一个周期的值。
            # (拿到这只ETF的长期均线上一个周期的值。)
            adx_val = self.adxs[d_name].adx[0]
            # 获取ADX指标的ADX线的当前值。
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
            # 获取前一周期内N日最高价的值（即到上一根K线为止的N日最高价）。
            # (拿到这只ETF在之前一段时间里的最高价，不包括当前这根K线。)
            sma_volume_val = self.sma_volumes[d_name][0]
            # 获取成交量SMA的当前值。
            # (拿到这只ETF的成交量均线现在的值。)
            atr_val = self.atrs[d_name][0]
            # 获取ATR指标的当前值。策略需要ATR来计算止损。
            # (拿到这只ETF的ATR指标现在的值，后面算止损会用到。)

            # 3.7.2.3 判断市场状态
            # (根据技术指标，判断当前市场是上升趋势还是区间震荡。)
            try:
                # 使用 try-except 块处理可能因指标数据不足（尤其在回测初期）引发的 `IndexError`。
                # (试试看下面的判断，如果因为刚开始回测，数据不够长，可能会出错，比如指标算不出来。)
                is_trend_up = (current_close > ema_medium_val > ema_long_val and
                               ema_medium_val > ema_medium_prev and
                               ema_long_val > ema_long_prev)
                # 判断是否为上升趋势：当前收盘价 > 中期EMA > 长期EMA，且中期EMA和长期EMA均在上升（当前值 > 前一周期值）。
                # (判断是不是上升趋势：收盘价比中期均线高，中期均线比长期均线高，而且两条均线都在往上走。)

                is_range_confirmed = (not is_trend_up and
                                      abs(ema_medium_val / ema_medium_prev - 1) < 0.003 and
                                      abs(ema_long_val / ema_long_prev - 1) < 0.003 and
                                      adx_val < 20 and
                                      (bb_top - bb_bot) / current_close < 0.07 if current_close > 1e-9 else False)
                # 判断是否为区间震荡：
                # 1. 首先不能是上升趋势。
                # 2. 中期和长期EMA变化平缓（当前值与前一周期值的变化率绝对值小于0.3%）。
                # 3. ADX < 20（表示趋势不强）。
                # 4. 布林带宽度（上轨-下轨）占收盘价的比例小于7%（表示波动不大）。
                #    (如果收盘价接近0，则条件不成立，避免除以0错误。)
                # (判断是不是区间震荡：首先不能是上升趋势，然后两条均线变化不大（几乎是平的），ADX指标小于20（表示趋势不强），并且布林带的上下轨之间的宽度相对于价格来说比较窄（小于7%）。)

                if is_trend_up:
                    # 如果判断为上升趋势。
                    # (如果是上升趋势。)
                    market_state = 'TREND_UP'
                    # 将市场状态设置为 'TREND_UP'。
                    # (就把市场状态改成 'TREND_UP'。)
                # elif is_range_confirmed and self.p.etf_type == 'range':
                elif is_range_confirmed:
                    # 如果判断为区间震荡，并且策略参数 `etf_type` 设置为 'range'（即当前策略允许进行区间交易）。
                    # (如果是区间震荡，并且咱们策略设置的是针对 'range' 区间型的ETF。)
                    market_state = 'RANGE_CONFIRMED'
                    # 将市场状态设置为 'RANGE_CONFIRMED'。
                    # (就把市场状态改成 'RANGE_CONFIRMED'。)
            except IndexError:
                # 如果在访问指标历史数据时发生 `IndexError` (通常在回测初期数据不足时)。
                # (如果因为数据不够，上面的判断出错了，比如某个指标 `[-1]` 取不到值。)
                continue
                # 跳过当前ETF，处理下一个。因为指标数据不足，无法做出判断。
                # (那就先不处理这只ETF了，跳到下一只。)

            # 3.7.2.4 初始化交易信号和风险变量
            # (准备一些变量，用来存放是否要买、按什么类型买、以及相关的价格和风险信息。)
            entry_signal = False
            # 初始化入场信号为 `False`。
            # (先假设没有买入信号。)
            potential_position_type = None
            # 初始化潜在持仓类型为 `None`。
            # (先假设不知道要按什么类型买。)
            entry_price_calc = None
            # 初始化参考入场价为 `None`。
            # (先假设不知道计划的买入价是多少。)
            stop_loss_price_calc = None
            # 初始化止损价为 `None`。
            # (先假设不知道计划的止损价是多少。)
            take_profit_price_calc = None
            # 初始化止盈价为 `None`。
            # (先假设不知道计划的止盈价是多少。)
            risk_per_share = None
            # 初始化每股风险为 `None`。
            # (先假设不知道每股可能亏多少。)
            amount_to_risk = None
            # 初始化本次交易最大风险金额为 `None`。
            # (先假设不知道这次交易总共愿意亏多少钱。)

            # 3.7.2.5 趋势交易信号判断与风险计算
            # (如果当前市场是上升趋势，并且策略允许趋势交易，就检查趋势买入信号，并计算相应的风险。)
            # if market_state == 'TREND_UP' and self.p.etf_type == 'trend':
            if market_state == 'TREND_UP':
                # 如果市场状态为上升趋势，并且策略参数 `etf_type` 设置为 'trend'。
                # (如果市场是上升趋势，并且咱们策略设置的是针对 'trend' 趋势型的ETF。)
                try:
                    # 尝试执行趋势交易的信号判断和风险计算。
                    # (试试看趋势交易的买入条件，这里也可能因为数据不足出错。)
                    is_breakout = (current_close > highest_high_prev and
                                   current_volume > sma_volume_val * self.params.trend_volume_ratio_min)
                    # 判断是否为突破信号：当前收盘价创近期新高（大于上一周期的N日最高价），并且当前成交量大于平均成交量的一定倍数。
                    # (判断是不是突破了：现在的价格比之前一段时间的最高价还高，并且成交量也比平均成交量大不少（具体大多少由参数 `trend_volume_ratio_min` 控制）。)
                    is_pullback = (min(abs(current_low / ema_medium_val - 1), abs(current_low / ema_long_val - 1)) < 0.01 and
                                   current_close > current_open) if ema_medium_val > 1e-9 and ema_long_val > 1e-9 else False
                    # 判断是否为回调信号：
                    # 1. 当前最低价接近中期EMA或长期EMA（回调到均线附近，距离小于1%）。
                    # 2. 当天收阳线（收盘价 > 开盘价）。
                    #    (如果均线值接近0，则条件不成立，避免计算错误。)
                    # (判断是不是回调买入机会：价格跌到中期均线或者长期均线附近了（距离均线不到1%），并且当天是涨的（收盘价比开盘价高）。)

                    if is_breakout or is_pullback:
                        # 如果出现突破信号或回调信号。
                        # (如果满足了突破条件或者回调条件中的任何一个。)
                        entry_signal = True
                        # 设置入场信号为 `True`。
                        # (那就认为有买入信号了。)
                        potential_position_type = 'trend'
                        # 设置潜在持仓类型为 'trend'。
                        # (这次买入是按趋势型来操作的。)
                        entry_price_calc = current_close
                        # 以当前收盘价作为参考入场价。
                        # (计划用现在的收盘价作为买入价。)

                        if math.isnan(atr_val) or atr_val <= 1e-9:
                            # 如果ATR值无效（例如为NaN或过小）。
                            # (如果算出来的ATR值不正常，比如是NaN或者太小了。)
                            self.log(
                                f"{d_name} ATR值无效 ({atr_val:.4f})，无法计算趋势止损。跳过。", data=d_obj)
                            # 记录日志，说明无法计算止损。
                            # (记个日志说ATR值有问题，没法算止损，这次不买了。)
                            entry_signal = False
                            # 取消入场信号。
                            # (那就不买了。)
                        else:
                            stop_loss_price_calc = entry_price_calc - \
                                self.p.trend_stop_loss_atr_mult * atr_val
                            # 计算止损价格：参考入场价 - ATR倍数 * ATR值。
                            # (用计划买入价减去几倍的ATR（这个倍数是参数设的），得到止损价。)

                            if stop_loss_price_calc >= entry_price_calc:
                                # 如果计算出的止损价不低于（或等于）入场价，说明ATR过大或价格波动异常。
                                # (如果算出来的止损价比买入价还高或者一样，说明ATR太大或者价格有问题，不合理。)
                                self.log(
                                    f"{d_name} 趋势止损价 {stop_loss_price_calc:.2f} 不低于入场价 {entry_price_calc:.2f}。跳过。", data=d_obj)
                                # 记录日志。
                                # (记个日志说止损价不合理，这次不买了。)
                                entry_signal = False
                                # 取消入场信号。
                                # (那就不买了。)
                            else:
                                risk_per_share = entry_price_calc - stop_loss_price_calc
                                # 计算每股风险：参考入场价 - 止损价。
                                # (用计划买入价减去止损价，得到买一股可能亏多少钱。)
                                if risk_per_share <= 1e-9:
                                    # 如果每股风险过小（接近0），可能导致后续Sizer计算问题。
                                    # (如果算出来每股风险几乎是0，这也不太好，Sizer可能算不出来买多少。)
                                    self.log(
                                        f"{d_name} 趋势交易每股风险过小 ({risk_per_share:.2f})。跳过。", data=d_obj)
                                    # 记录日志。
                                    # (记个日志说每股风险太小了，这次不买了。)
                                    entry_signal = False
                                    # 取消入场信号。
                                    # (那就不买了。)
                                else:
                                    take_profit_price_calc = entry_price_calc + \
                                        self.p.trend_take_profit_rratio * risk_per_share
                                    # 计算止盈价格：参考入场价 + 盈亏比 * 每股风险。
                                    # (用计划买入价加上几倍的每股风险（这个倍数是参数设的盈亏比），得到止盈价。)
                                    risk_per_trade_percent = self.p.risk_per_trade_trend
                                    # 获取策略参数中定义的趋势交易单笔风险百分比。
                                    # (从策略参数里拿到趋势交易单笔愿意亏多少的百分比，比如1%。)
                                    effective_risk_percent = risk_per_trade_percent * self.current_risk_multiplier
                                    # 计算实际生效的风险百分比（考虑当前风险乘数，例如因回撤降低风险）。
                                    # (用这个百分比乘以当前的风险调整系数 `self.current_risk_multiplier`，得到实际这次交易能亏的百分比。)
                                    amount_to_risk = self.broker.getvalue() * effective_risk_percent
                                    # 计算本次交易允许的最大风险金额：账户总值 * 实际生效的风险百分比。
                                    # (用账户总资产乘以这个实际百分比，得到这次交易总共愿意亏多少钱。)
                except IndexError:
                    # 如果发生 `IndexError`。
                    # (如果因为数据不够出错了。)
                    continue
                    # 跳过当前ETF。
                    # (那就先不处理这只ETF了，跳到下一只。)

            # 3.7.2.6 区间交易信号判断与风险计算
            # (如果当前市场是区间震荡，并且策略允许区间交易，就检查区间买入信号，并计算相应的风险。)
            # elif market_state == 'RANGE_CONFIRMED' and self.p.etf_type == 'range':
            elif market_state == 'RANGE_CONFIRMED':
                # 如果市场状态为区间震荡，并且策略参数 `etf_type` 设置为 'range'。
                # (如果市场是区间震荡，并且咱们策略设置的是针对 'range' 区间型的ETF。)
                try:
                    # 尝试执行区间交易的信号判断和风险计算。
                    # (试试看区间交易的买入条件。)
                    is_range_buy = (current_low <= bb_bot and
                                    current_close > bb_bot and
                                    rsi_val < self.params.rsi_oversold)
                    # 判断是否为区间买入信号：
                    # 1. 当前最低价触及或跌破布林带下轨。
                    # 2. 当前收盘价回到布林带下轨之上（确认支撑）。
                    # 3. RSI指标处于超卖区（低于参数 `rsi_oversold` 定义的阈值）。
                    # (判断是不是区间买入机会：价格碰到或者跌破布林带下轨了，然后收盘的时候又回到下轨上面（说明下面有支撑），并且RSI指标显示超卖了（比如低于30）。)
                    if is_range_buy:
                        # 如果出现区间买入信号。
                        # (如果满足了区间买入的条件。)
                        entry_signal = True
                        # 设置入场信号为 `True`。
                        # (那就认为有买入信号了。)
                        potential_position_type = 'range'
                        # 设置潜在持仓类型为 'range'。
                        # (这次买入是按区间型来操作的。)
                        entry_price_calc = current_close
                        # 以当前收盘价作为参考入场价。
                        # (计划用现在的收盘价作为买入价。)
                        stop_loss_price_calc = current_low * \
                            (1 - self.p.range_stop_loss_buffer)
                        # 计算止损价格：当前K线最低价 * (1 - 区间止损缓冲百分比)。
                        # (用当前这根K线的最低价再往下浮动一点点（这个浮动比例是参数 `range_stop_loss_buffer` 设的），作为止损价。)

                        if stop_loss_price_calc >= entry_price_calc:
                            # 如果计算出的止损价不低于入场价。
                            # (如果算出来的止损价比买入价还高或者一样，不合理。)
                            self.log(
                                f"{d_name} 区间止损价 {stop_loss_price_calc:.2f} 不低于入场价 {entry_price_calc:.2f}。跳过。", data=d_obj)
                            # 记录日志。
                            # (记个日志说止损价不合理，这次不买了。)
                            entry_signal = False
                            # 取消入场信号。
                            # (那就不买了。)
                        else:
                            risk_per_share = entry_price_calc - stop_loss_price_calc
                            # 计算每股风险。
                            # (用计划买入价减去止损价，得到买一股可能亏多少钱。)
                            if risk_per_share <= 1e-9:
                                # 如果每股风险过小。
                                # (如果算出来每股风险几乎是0。)
                                self.log(
                                    f"{d_name} 区间交易每股风险过小 ({risk_per_share:.2f})。跳过。", data=d_obj)
                                # 记录日志。
                                # (记个日志说每股风险太小了，这次不买了。)
                                entry_signal = False
                                # 取消入场信号。
                                # (那就不买了。)
                            else:
                                take_profit_price_calc = bb_mid
                                # 设置止盈目标为布林带中轨。
                                # (区间交易的止盈目标一般设在布林带的中轨。)
                                risk_per_trade_percent = self.p.risk_per_trade_range
                                # 获取策略参数中定义的区间交易单笔风险百分比。
                                # (从策略参数里拿到区间交易单笔愿意亏多少的百分比，比如0.5%。)
                                effective_risk_percent = risk_per_trade_percent * self.current_risk_multiplier
                                # 计算实际生效的风险百分比。
                                # (用这个百分比乘以当前的风险调整系数，得到实际这次交易能亏的百分比。)
                                amount_to_risk = self.broker.getvalue() * effective_risk_percent
                                # 计算本次交易允许的最大风险金额。
                                # (用账户总资产乘以这个实际百分比，得到这次交易总共愿意亏多少钱。)
                except IndexError:
                    # 如果发生 `IndexError`。
                    # (如果因为数据不够出错了。)
                    continue
                    # 跳过当前ETF。
                    # (那就先不处理这只ETF了，跳到下一只。)

            # 3.7.2.7 如果有有效入场信号，则准备并下单
            # (如果前面判断有买入信号，并且相关的价格和风险信息都算好了，就准备下单。)
            if entry_signal and entry_price_calc is not None and \
               stop_loss_price_calc is not None and risk_per_share is not None and \
               amount_to_risk is not None and entry_price_calc > stop_loss_price_calc:
                # 检查所有必要信息是否都已计算完毕且有效：
                # 1. `entry_signal` 为 `True`。
                # 2. `entry_price_calc`, `stop_loss_price_calc`, `risk_per_share`, `amount_to_risk` 均不为 `None`。
                # 3. 参考入场价 `entry_price_calc` 高于止损价 `stop_loss_price_calc`。
                # (确保有买入信号，并且计划买入价、止损价、每股风险、总风险金额这些都算出来了，而且买入价比止损价高。)
                if risk_per_share <= 1e-9 or amount_to_risk <= 1e-9:
                    # 再次校验每股风险和总风险金额是否有效（大于一个极小值）。
                    # (再检查一下，如果每股风险或者总风险金额太小了，接近0，那也不行。)
                    self.log(
                        f"信号产生但风险计算无效 for {d_name} (Risk/Share: {risk_per_share:.4f}, AmountToRisk: {amount_to_risk:.2f})。跳过。", data=d_obj)
                    # 记录日志，说明风险计算无效。
                    # (记个日志说虽然有信号，但是风险算出来不对，这次不买了。)
                    continue
                    # 跳过此信号。
                    # (跳过这个有问题的信号。)

                # 3.7.2.7.1 将计算好的风险信息存入 pending_trade_info 供 Sizer 读取
                # (把算好的这些交易计划信息（买入价、止损价、风险等）放到 `pending_trade_info` 本子里，Sizer会从这里拿。)
                self.pending_trade_info[d_name] = {
                    'entry_price': entry_price_calc,
                    'stop_loss_price': stop_loss_price_calc,
                    'risk_per_share': risk_per_share,
                    'amount_to_risk': amount_to_risk
                }
                # 将计算得到的参考入场价、止损价、每股风险和本次交易最大风险金额存入 `self.pending_trade_info` 字典，以当前ETF名称 `d_name` 为键。
                # Sizer 稍后会读取这些信息来计算头寸。
                # (把算好的买入价、止损价、每股风险、总风险金额都打包存到 `pending_trade_info` 本子里，用ETF名字做标签。Sizer（算数量的工具）等会儿会从这里拿这些信息去算到底买多少股。)
                self.log(
                    f"为 {d_name} 准备交易信息: 入场={entry_price_calc:.2f}, 止损={stop_loss_price_calc:.2f}, 风险/股={risk_per_share:.4f}, 允许风险额={amount_to_risk:.2f}", data=d_obj)
                # 记录日志，说明已为该ETF准备好交易信息。
                # (记个日志说交易计划准备好了，包括计划买入价、止损价等等。)

                # 3.7.2.7.2 设置括号单参数
                # (准备下括号单（一种包含止损和止盈的订单）需要的价格参数。)
                main_order_limit_price = entry_price_calc
                # 主订单（买入单）的限价使用策略计算的参考入场价。
                # (主要的买入订单，就用我们上面算好的计划买入价 `entry_price_calc` 作为限价。)
                tp_price_for_bracket = None
                # 初始化括号单的止盈价格为 `None`。
                # (先假设没有止盈价。)
                if take_profit_price_calc is not None and take_profit_price_calc > main_order_limit_price:
                    # 如果计算了止盈价，并且该止盈价高于主订单限价（买入价）。
                    # (如果我们算出了止盈价，并且这个止盈价比计划买入价高。)
                    tp_price_for_bracket = take_profit_price_calc
                    # 则使用此计算出的止盈价作为括号单的止盈限价。
                    # (那就用这个算出来的止盈价。)
                elif potential_position_type == 'trend' and take_profit_price_calc is not None:
                    # 如果是趋势交易，并且计算了止盈价，但该止盈价无效（例如不高于入场价）。
                    # (如果是趋势交易，并且算出了止盈价，但是这个止盈价不比买入价高（比如算错了或者市场情况特殊），就警告一下。)
                    self.log(
                        f"警告 for {d_name}: 趋势交易止盈价 {take_profit_price_calc:.2f} 无效 (不高于入场价 {main_order_limit_price:.2f})。括号单将无止盈限价单。", data=d_obj)
                    # 记录警告日志，说明止盈价无效，括号单将不包含止盈限价单。
                    # (记个日志警告一下，说止盈价有问题，这次的括号单可能就没有止盈部分了。)

                # 3.7.2.7.3 调用 buy_bracket 下单
                # (发出买入括号单的指令。Sizer 会在这个过程中被自动调用来计算买多少股。)
                self.log(
                    f"发出买入括号单信号 for {d_name}, 参考入场: {main_order_limit_price:.2f}, 止损: {stop_loss_price_calc:.2f}, 止盈: {tp_price_for_bracket if tp_price_for_bracket else 'N/A'}", data=d_obj)
                # 记录日志，说明将要发出买入括号单，并显示相关价格。
                # (记个日志说我们要下一个买入的括号单了，包括计划的买入价、止损价和止盈价（如果有的话）。)
                bracket_orders_list = self.buy_bracket(
                    data=d_obj,
                    price=main_order_limit_price,
                    exectype=bt.Order.Limit,
                    stopprice=stop_loss_price_calc,
                    limitprice=tp_price_for_bracket,
                )
                # 调用 `self.buy_bracket` 方法下达括号订单：
                # - `data=d_obj`: 指定交易对象。
                # - `price=main_order_limit_price`: 主买入订单的限价。
                # - `exectype=bt.Order.Limit`: 主订单类型为限价单。
                # - `stopprice=stop_loss_price_calc`: 止损订单的触发价格（由策略计算）。
                # - `limitprice=tp_price_for_bracket`: 止盈订单的限价（由策略计算，可能为None）。
                # 注意：`size` 参数未在此处传递，因为 `AShareETFSizer` 会自动计算并应用头寸大小。
                # (正式下单！用 `self.buy_bracket` 来下一个括号单。这个单子会自动包含一个买入单、一个止损单和一个止盈单（如果设置了止盈价）。我们告诉它要买哪个ETF (`data`)，计划的买入限价 (`price`)，止损触发价 (`stopprice`)，还有止盈限价 (`limitprice`)。买多少股 (`size`) 不用我们说，Sizer会自动算。)

                # 3.7.2.7.4 处理 buy_bracket 返回结果
                # (下单后，看看是不是成功发出了订单请求。)
                if bracket_orders_list and bracket_orders_list[0]:
                    # 如果 `buy_bracket` 成功返回了订单列表，并且列表中的第一个订单 (主买入订单) 存在。
                    # (如果成功创建了括号订单（会返回一个包含主单、止损单、止盈单的列表），并且主订单是有的。)
                    self.position_types[d_name] = potential_position_type
                    # 记录本次开仓的持仓类型（'trend' 或 'range'）。
                    # (把这次买入是按什么类型（趋势/区间）操作的，记在 `self.position_types` 本子里。)
                    self.log(
                        f"成功为 {d_name} 创建 buy_bracket 请求。主订单 ref: {bracket_orders_list[0].ref if bracket_orders_list[0] else 'N/A'}", data=d_obj)
                    # 记录日志，说明成功创建了买入括号单请求，并显示主订单的引用号。
                    # (记个日志说买入括号单的请求成功发出去了，并记下主订单的编号。)
                else:
                    # 如果未能成功创建括号订单 (例如Sizer返回0股导致订单未创建，或发生其他错误)。
                    # (如果括号单没创建成功，比如Sizer算出来买0股，或者其他原因。)
                    self.log(
                        f"为 {d_name} 创建 buy_bracket 失败 (可能Sizer返回0或错误)", data=d_obj)
                    # 记录日志，说明创建失败。
                    # (记个日志说创建括号单失败了，可能是Sizer算出来买0股或者有其他错误。)
                    if d_name in self.pending_trade_info:
                        # 如果下单失败，也需要清理 `pending_trade_info` 中为此次尝试准备的信息。
                        # (如果下单失败了，之前存在 `pending_trade_info` 本子里的计划也就没用了，要删掉。)
                        del self.pending_trade_info[d_name]
                        # 从 `pending_trade_info` 中删除该ETF的条目。
                        # (把这个ETF的计划从本子里删掉。)

    def stop(self):
        # ... (原有的日志和计算逻辑可以保留) ...
        self.final_trade_stats_by_type = self.trade_details_by_type # 关键赋值
        # self.log('策略内部交易类型统计 (in stop):') # 可以选择在这里也打印，用于调试
        # for trade_type, stats in self.final_trade_stats_by_type.items():
        #     self.log(f"  Type: {trade_type}, PnL: {stats['pnl']:.2f}, Count: {stats['count']}")

# 4. 数据加载函数 load_data_to_cerebro
# (这个函数专门负责把我们准备好的Excel格式的股票数据读进来，转换成 `backtrader` 能用的格式，并加载到回测引擎 `cerebro` 中。)


def load_data_to_cerebro(cerebro, data_files, column_mapping, openinterest_col, fromdate, todate):
    # 定义 `load_data_to_cerebro` 函数，用于将Excel数据文件加载到Cerebro引擎中。
    # (定义一个名叫 `load_data_to_cerebro` 的函数，它会帮我们把Excel文件里的股票数据读到 `cerebro` 引擎里去。)
    """
    加载Excel数据文件到Cerebro引擎中。
    (这个函数的作用是读取Excel文件里的股票历史数据，比如每天的开盘价、收盘价等，然后把这些数据加到 `backtrader` 的大脑（Cerebro引擎）里，为回测做准备。)

    Args:
        cerebro (bt.Cerebro): Cerebro引擎实例。
                              (Cerebro引擎，就是 `backtrader` 的大脑。)
        data_files (list): 包含Excel文件路径的列表。
                           (一个列表，里面放着所有Excel数据文件的路径，比如 `['股票A数据.xlsx', '股票B数据.xlsx']`。)
        column_mapping (dict): 列名映射字典。例如 {'日期': 'datetime', '开盘': 'open'}。
                               (一个字典，告诉程序Excel里的中文列名对应 `backtrader` 需要的英文列名，比如 '日期' 对应 'datetime'。)
        openinterest_col (int or str): 持仓量列的索引或名称。如果数据中没有持仓量，则传入 -1 或 None。
                                       (如果Excel里有"持仓量"这一列，就告诉程序是哪一列；如果没有，就设成-1或者None。)
        fromdate (datetime.datetime): 回测起始日期。
                                      (回测从哪天开始，比如 `datetime.datetime(2020, 1, 1)` 就是从2020年1月1日开始。)
        todate (datetime.datetime): 回测结束日期。
                                    (回测到哪天结束，比如 `datetime.datetime(2023, 12, 31)` 就是到2023年12月31日结束。)

    Returns:
        int: 成功加载的数据源数量。
             (返回成功加载了多少个数据文件（比如多少只股票的数据）。)
    """
    print("开始加载数据...")
    # 打印开始加载数据的提示信息。
    # (在屏幕上显示"开始加载数据..."，告诉用户程序正在做什么。)
    loaded_data_count = 0
    # 初始化成功加载的数据文件计数器为0。
    # (准备一个计数器 `loaded_data_count`，用来记成功加载了多少个文件，一开始是0。)
