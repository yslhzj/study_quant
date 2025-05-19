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
        self.final_trade_stats_by_type = {}  # 用于在 stop() 中赋值

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
        self.final_trade_stats_by_type = self.trade_details_by_type  # 关键赋值
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

    # 4.1 遍历并加载每个数据文件
    # (对我们指定的每一个Excel文件，都尝试读取和处理。)
    for file_path in data_files:
        # 遍历 `data_files` 列表中的每个文件路径。
        # (一个一个地处理列表 `data_files` 里的每个文件路径。)
        try:
            # 4.1.1 读取和预处理DataFrame
            # (用pandas读取Excel，改列名，处理日期格式。)
            dataframe = pd.read_excel(file_path)
            # 使用pandas的 `read_excel` 方法读取Excel文件到DataFrame中。
            # (用 `pandas` 这个工具把Excel文件 `file_path` 读成一个表格数据（DataFrame）。)
            dataframe.rename(columns=column_mapping, inplace=True)
            # 根据 `column_mapping` 字典重命名DataFrame的列名，`inplace=True` 表示直接在原DataFrame上修改。
            # (按照我们之前定义的 `column_mapping`，把表格里的中文列名改成英文的，比如把"开盘"改成"open"。)
            if 'datetime' in dataframe.columns:
                # 检查重命名后是否存在 'datetime' 列。
                # (看看表格里有没有一列叫 'datetime'（日期时间）。)
                try:
                    dataframe['datetime'] = pd.to_datetime(
                        dataframe['datetime'])
                    # 如果存在，则尝试将其转换为pandas的datetime对象。
                    # (如果有，就试着把这一列的文字日期（比如 "2023-01-01"）转换成 `pandas` 能识别的日期格式。)
                except Exception as e:
                    # 如果转换失败，打印警告信息并跳过此文件。
                    # (如果转换失败了，比如日期格式不对，就打印个警告，然后这个文件就不处理了。)
                    print(f"警告: 无法解析 {file_path} 中的日期时间列，请检查格式。错误: {e}")
                    # 打印警告信息，提示用户检查文件中的日期时间列格式。
                    # (告诉用户这个文件里的日期格式有问题，转换不了。)
                    continue
                    # 跳过当前文件的剩余处理步骤，继续处理下一个文件。
                    # (这个文件不处理了，跳到下一个。)
            else:
                # 如果不存在 'datetime' 列，打印错误信息并跳过此文件。
                # (如果表格里连 'datetime' 这一列都没有。)
                print(
                    f"错误: 在 {file_path} 中找不到映射后的 'datetime' 列。请确保Excel文件中有正确的日期列，或正确修改脚本中的column_mapping。")
                # 打印错误信息，提示用户检查列名映射或Excel文件。
                # (告诉用户找不到日期列，请检查Excel文件或者改列名的规则是不是写错了。)
                print(f"Excel文件中的原始列名是: {dataframe.columns.tolist()}")
                # 打印Excel文件中的原始列名，帮助用户排查问题。
                # (把Excel文件里本来的列名都打出来，方便用户对照检查。)
                continue
                # 跳过当前文件的剩余处理步骤。
                # (这个文件不处理了，跳到下一个。)
            dataframe.set_index('datetime', inplace=True)
            # 将 'datetime' 列设置为DataFrame的索引。
            # (把日期时间这一列作为表格的行标签（索引），这样方便按时间查找数据。)
            required_cols = ['open', 'high', 'low', 'close', 'volume']
            # 定义backtrader必需的列名列表：开盘价、最高价、最低价、收盘价、成交量。
            # (规定 `backtrader` 至少需要这几列数据：'open', 'high', 'low', 'close', 'volume'。)
            if not all(col in dataframe.columns for col in required_cols):
                # 检查DataFrame中是否包含所有必需的列。
                # (看看我们的表格里是不是都有这些必需的列。)
                print(f"错误: {file_path} 映射后缺少必需的列。")
                # 如果缺少必需列，打印错误信息。
                # (如果少了哪一列，就报错。)
                print(f"可用的列: {dataframe.columns.tolist()}")
                # 打印当前可用的列名，帮助排查。
                # (把表格里现在有的列名都打出来，方便用户看少了哪个。)
                continue
                # 跳过当前文件的剩余处理步骤。
                # (这个文件不处理了，跳到下一个。)
            dataframe = dataframe.loc[fromdate:todate]
            # 根据提供的 `fromdate` 和 `todate` 筛选DataFrame中的数据行，只保留指定日期范围内的数据。
            # (只留下从 `fromdate` 到 `todate` 这个时间段内的数据，其他时间的数据不要。)

            if dataframe.empty:
                # 如果筛选后的DataFrame为空（即指定日期范围内没有数据）。
                # (如果这个时间段内一行数据都没有。)
                print(f"警告: {file_path} 在指定日期范围内没有数据。")
                # 打印警告信息。
                # (就打印个警告，说这个文件在这个时间段没数据。)
                continue
                # 跳过当前文件的剩余处理步骤。
                # (这个文件不处理了，跳到下一个。)

            # 4.1.2 处理持仓量参数
            # (根据用户设置，决定是否以及如何使用Excel中的持仓量数据。)
            oi_param_val = -1
            # 初始化传递给 `PandasData` 的 `openinterest` 参数的默认值为-1，表示不使用持仓量。
            # (先假设不用持仓量数据，用-1表示。)
            if isinstance(openinterest_col, str) and openinterest_col in dataframe.columns:
                # 如果 `openinterest_col` 是字符串（列名）并且该列存在于DataFrame中。
                # (如果用户提供的是持仓量列的名字（字符串），并且这个名字在我们的表格里确实有这一列。)
                oi_param_val = openinterest_col
                # 则使用该列名作为 `openinterest` 参数的值。
                # (那就用这个列名来指定持仓量数据。)
            elif isinstance(openinterest_col, str):
                # 如果 `openinterest_col` 是字符串但该列不存在。
                # (如果用户提供的是列名，但在表格里找不到这一列。)
                print(
                    f"警告: 指定的 openinterest 列名 '{openinterest_col}' 在 {file_path} 中不存在。将忽略持仓量。")
                # 打印警告信息，说明将忽略持仓量。
                # (就打印个警告，说找不到用户指定的持仓量列，所以这次不用持仓量了。)
            elif isinstance(openinterest_col, int) and openinterest_col != -1:
                # 如果 `openinterest_col` 是整数索引且不为-1（backtrader的PandasData通常期望列名字符串或-1）。
                # (如果用户提供的是一个数字（列的序号），并且不是-1。)
                print(
                    f"警告: 为 openinterest 提供了整数索引 {openinterest_col}。如果意图是列名，请使用字符串。否则，行为可能未定义。")
                # 打印警告，提示这种用法可能导致未定义行为，建议使用列名字符串。
                # (就打印个警告，说用数字当列序号可能不太好，最好用列的名字。这里还是会尝试用这个数字，但要小心。)
                oi_param_val = openinterest_col
                # 谨慎使用整数索引。
                # (这里还是会用这个数字，但要小心点。)

            # 4.1.3 创建并添加数据到Cerebro
            # (把处理好的pandas表格数据转换成 `backtrader` 认识的数据格式，并添加到大脑 `cerebro` 中。)
            data = bt.feeds.PandasData(dataname=dataframe, fromdate=fromdate, todate=todate, datetime=None,
                                       open='open', high='high', low='low', close='close', volume='volume',
                                       openinterest=oi_param_val)
            # 使用 `bt.feeds.PandasData` 类将处理后的DataFrame转换为Backtrader的数据源（feed）对象。
            # - `dataname=dataframe`: 指定数据来源。
            # - `fromdate`, `todate`: 再次指定日期范围（通常PandasData会自行处理，但显式指定无害）。
            # - `datetime=None`: 因为索引已是datetime类型，所以这里设为None。
            # - `open`, `high`, `low`, `close`, `volume`: 映射到DataFrame中对应的列。
            # - `openinterest=oi_param_val`: 使用前面处理得到的持仓量参数值。
            # (用 `bt.feeds.PandasData` 把我们的 `pandas` 表格数据 `dataframe` 包装成 `backtrader` 能用的数据格式。告诉它日期范围、开盘价是哪列、收盘价是哪列等等，还有持仓量用哪个（`oi_param_val`）。)
            data_name = os.path.basename(file_path).split('.')[0]
            # 从文件路径中提取文件名（不含扩展名）作为数据源的名称。
            # (从文件名里提取出股票代码或者名字，比如 "510050_d.xlsx" 就变成 "510050_d"。)
            cerebro.adddata(data, name=data_name)
            # 将创建的数据源 `data` 添加到Cerebro引擎中，并赋予其名称 `data_name`。
            # (把这个包装好的数据 `data` 加到 `cerebro` 大脑里，并给它取个名字 `data_name`。)
            print(f"数据加载成功: {data_name}")
            # 打印数据加载成功的提示信息。
            # (在屏幕上显示某某数据加载成功了。)
            loaded_data_count += 1
            # 成功加载的数据文件计数器加1。
            # (成功加载了一个文件，计数器加1。)

        # 4.2 异常处理
        # (如果在加载某个文件的过程中出错了，比如文件找不到，就抓住这个错误并打印信息，然后继续处理下一个文件。)
        except FileNotFoundError:
            # 如果在读取文件时发生 `FileNotFoundError` 异常。
            # (如果Excel文件找不到了。)
            print(f"错误: 文件未找到 {file_path}")
            # 打印文件未找到的错误信息。
            # (就打印错误说找不到这个文件。)
        except Exception as e:
            # 捕获其他所有在加载数据过程中可能发生的异常。
            # (如果发生了其他类型的错误。)
            print(f"加载数据 {file_path} 时出错: {e}")
            # 打印加载数据时出错的通用错误信息及异常详情。
            # (就打印错误说加载这个文件时出错了，并显示具体的错误信息。)
            import traceback
            # 导入 `traceback` 模块，用于打印详细的错误堆栈信息。
            # (引入一个工具 `traceback`，它可以帮我们看错误发生在哪里的详细过程。)
            traceback.print_exc()
            # 打印完整的错误堆栈跟踪，帮助调试。
            # (把详细的错误过程打印出来，方便我们找到问题的原因。)
    # 4.3 返回加载计数
    # (告诉调用者总共成功加载了多少个数据文件。)
    return loaded_data_count
    # 返回成功加载的数据源数量。
    # (把最后成功加载了多少个文件的数量告诉外面。)

# 5. 参数优化结果分析函数 analyze_optimization_results
# (当策略参数优化运行结束后，这个函数负责处理优化结果，计算每个参数组合的得分，并找出最好的那组参数。)


def analyze_optimization_results(results):
    # 定义 `analyze_optimization_results` 函数，用于分析优化结果，计算归一化得分并找到最优参数。
    # (定义一个名叫 `analyze_optimization_results` 的函数，它会帮我们分析参数优化的结果，给每个参数组合打分，然后找出分数最高的那个。)
    """
    分析优化结果，计算归一化得分并找到最优参数。
    (这个函数的作用是：当 `backtrader` 对很多不同的参数组合都跑了一遍回测后，我们会得到很多结果。这个函数就负责把这些结果拿过来，
     提取出关键的性能指标（比如夏普率、收益率、最大回撤），然后根据这些指标给每个参数组合打一个综合分数，最后找出分数最高的那个组合。)

    Args:
        results (list): cerebro.run() 在优化模式下返回的优化结果列表。每个元素通常是一个包含单个策略实例的列表。
                        (一个列表，里面装着所有参数组合的回测结果。每个结果里包含了策略实例和它的分析器数据。)

    Returns:
        tuple: 包含最佳策略结果数据（字典）和所有带得分的结果数据列表的元组。
               格式为 (best_result_data, all_scored_results)。
               如果无法处理，则返回 (None, [])。
               (返回两个东西：一个是最好的那个参数组合的结果数据（一个字典），另一个是所有参数组合及其得分的列表。如果没结果或者处理不了，就返回空。)
    """
    # 5.1 检查初始结果是否为空
    # (先看看优化有没有产生任何结果，如果没有就直接返回。)
    if not results:
        # 如果 `results` 列表为空（即没有策略成功运行或没有结果返回）。
        # (如果 `results` 是空的，说明可能一次回测都没成功跑完。)
        print("\n{:!^50}".format(' 错误 '))
        # 打印错误标题。
        # (在屏幕上打一个醒目的错误提示。)
        print("没有策略成功运行。请检查数据加载是否有误或参数范围是否有效。")
        # 打印错误信息，提示用户检查数据加载或参数范围。
        # (告诉用户没有策略成功跑完，请检查数据或者参数设置是不是有问题。)
        print('!' * 50)
        # 打印分隔线。
        # (再打一行感叹号，强调一下。)
        return None, []
        # 返回 `None` 表示没有最佳结果，返回空列表表示没有带得分的结果。
        # (返回空结果，表示没找到最好的，也没有其他结果。)

    # 5.2 提取并处理每个参数组合的分析结果
    # (遍历所有参数组合的运行结果，从中提取出夏普率、收益率、最大回撤等性能指标。)
    processed_results = []
    # 初始化一个空列表 `processed_results`，用于存储从每个策略实例中提取并处理后的分析结果。
    # (准备一个空列表 `processed_results`，用来放我们从每个回测结果里提取出来的关键信息。)
    print("\n--- 开始提取分析结果 ---")
    # 打印开始提取分析结果的提示信息。
    # (告诉用户现在开始从回测结果里拿数据了。)
    run_count = 0
    # 初始化运行次数计数器。
    # (准备一个计数器 `run_count`，记一下总共跑了多少次回测。)
    successful_runs = 0
    # 初始化成功提取结果的运行次数计数器。
    # (准备一个计数器 `successful_runs`，记一下成功提取出结果的回测有多少次。)
    for strat_list in results:
        # 遍历 `results` 列表中的每个元素。在 `optreturn=False` 时，`results` 是一个列表的列表，外层列表对应每次参数组合的运行，内层列表通常只包含一个策略实例。
        # (一个一个地看 `results` 里的每个回测结果。每个结果 `strat_list` 其实也是个列表，里面装着那次跑完的策略。)
        run_count += 1
        # 运行次数加1。
        # (跑的次数加1。)
        if not strat_list:
            # 如果当前参数组合的运行结果 `strat_list` 为空，则跳过。
            # (如果这个 `strat_list` 是空的，说明这次回测可能没东西。)
            continue
            # 跳过空的结果列表。
            # (那就跳过，看下一个。)

        strategy_instance = strat_list[0]
        # 获取策略实例，通常是 `strat_list` 中的第一个元素。
        # (从 `strat_list` 里拿出第一个东西，这个就是那次跑完的策略实例。)
        params = strategy_instance.params
        # 获取该策略实例的参数对象。
        # (拿到这个策略实例当时用的参数。)
        analyzers = strategy_instance.analyzers
        # 获取该策略实例的分析器集合。
        # (拿到这个策略实例跑完后生成的各种分析结果，比如夏普率分析器、收益分析器等。)

        # 5.2.1 构建参数字符串用于日志/调试
        # (把这次运行用的参数组合成一个字符串，方便看是哪些参数。)
        params_str_parts = []
        # 初始化一个空列表，用于存储参数名和值的字符串片段。
        # (准备一个空列表 `params_str_parts`，用来放 "参数名=参数值" 这种小字符串。)
        optimized_param_names = [
            # 'etf_type', # 我们不再通过参数强制类型，所以可以不在这里列出，或者列出并显示其默认值
            'ema_medium_period', 'ema_long_period',
            'bbands_period', 'bbands_devfactor', 'trend_stop_loss_atr_mult',
            'range_stop_loss_buffer',
            'risk_per_trade_trend',
            'risk_per_trade_range'
        ]
        # 定义在优化过程中实际使用的参数名称列表，应与 `optstrategy` 中设置的参数一致。
        # (列出我们这次优化主要关心的那些参数的名字。)
        for p_name in optimized_param_names:
            # 遍历这些关心的参数名。
            # (一个一个地看这些参数名。)
            if hasattr(params, p_name):
                # 检查策略参数对象 `params` 是否具有名为 `p_name` 的属性。
                # (看看这个策略的参数里有没有这个名字的参数。)
                params_str_parts.append(f"{p_name}={getattr(params, p_name)}")
                # 如果有，则将 "参数名=参数值" 格式的字符串添加到列表中。
                # (如果有，就把 "参数名=参数值" 加到 `params_str_parts` 列表里。)
            else:
                # 如果没有该属性。
                # (如果没有这个参数。)
                params_str_parts.append(f"{p_name}=MISSING")
                # 则添加 "参数名=MISSING" 表示该参数缺失。
                # (就记一个 "参数名=MISSING"，表示这个参数没找到。)
        params_str = ", ".join(params_str_parts)
        # 将列表中的所有参数字符串片段用逗号和空格连接成一个完整的参数字符串。
        # (把 `params_str_parts` 列表里的所有小字符串用逗号连起来，变成一个长字符串，比如 "ema_medium_period=60, ema_long_period=120, ..."。)

        # 5.2.2 尝试获取并验证分析结果
        # (从分析器里拿出夏普率、收益率、最大回撤这些数据，并检查它们是不是有效的。)
        try:
            # 使用 try-except 块处理在获取分析结果时可能发生的错误（如分析器未正确运行或结果缺失）。
            # (试试看能不能拿到分析结果，如果拿不到或者分析结果有问题，就跳过。)
            sharpe_analysis = analyzers.sharpe_ratio.get_analysis()
            # 获取名为 'sharpe_ratio' 的分析器的分析结果。
            # (从夏普率分析器里拿出分析结果。)
            returns_analysis = analyzers.returns.get_analysis()
            # 获取名为 'returns' 的分析器的分析结果。
            # (从收益分析器里拿出分析结果。)
            drawdown_analysis = analyzers.drawdown.get_analysis()
            # 获取名为 'drawdown' 的分析器的分析结果。
            # (从回撤分析器里拿出分析结果。)

            valid_analysis = True
            # 初始化分析结果有效性标志为 `True`。
            # (先假设分析结果是有效的。)
            if not sharpe_analysis or 'sharperatio' not in sharpe_analysis:
                # 如果夏普分析结果为空或不包含 'sharperatio' 键。
                # (如果夏普率分析结果是空的，或者里面没有 'sharperatio' 这个东西。)
                valid_analysis = False
                # 则标记为无效。
                # (那就认为这个分析结果无效。)
            if not returns_analysis or 'rtot' not in returns_analysis:
                # 如果收益分析结果为空或不包含 'rtot' (总收益率) 键。
                # (如果收益分析结果是空的，或者里面没有 'rtot' 这个东西。)
                valid_analysis = False
                # 则标记为无效。
                # (那就认为这个分析结果无效。)
            if not drawdown_analysis or 'max' not in drawdown_analysis or 'drawdown' not in drawdown_analysis.get('max', {}):
                # 如果回撤分析结果为空，或不包含 'max' 键，或 'max' 字典中不包含 'drawdown' 键。
                # (如果回撤分析结果是空的，或者里面没有 'max'，或者 'max' 里面又没有 'drawdown'。)
                valid_analysis = False
                # 则标记为无效。
                # (那就认为这个分析结果无效。)

            if not valid_analysis:
                # 如果分析结果被标记为无效。
                # (如果上面的检查发现分析结果无效。)
                continue
                # 跳过当前参数组合的后续处理。
                # (那就跳过这个参数组合，不处理了。)

            # 5.2.3 提取关键性能指标
            # (如果分析结果有效，就从中提取出具体的夏普率、总收益率和最大回撤值。)
            sharpe = sharpe_analysis.get('sharperatio')
            # 从夏普分析结果中获取 'sharperatio' 的值。
            # (从夏普率分析结果里拿出夏普率的值。)
            if sharpe is None:
                # 如果夏普比率值为 `None` (可能在某些情况下发生，如无交易或收益为0)。
                # (如果夏普率是空的（比如没交易或者收益是0）。)
                sharpe = 0.0
                # 则将其设置为0.0。
                # (那就当它是0.0。)
            total_return = returns_analysis.get('rtot', 0.0)
            # 从收益分析结果中获取 'rtot' (总收益率，小数形式) 的值，如果缺失则默认为0.0。
            # (从收益分析结果里拿出总收益率（是个小数，比如0.1代表10%），如果拿不到就当是0.0。)
            max_drawdown = drawdown_analysis.get('max', {}).get(
                'drawdown', 0.0) / 100.0
            # 从回撤分析结果的 'max' 字典中获取 'drawdown' (最大回撤百分比) 的值，除以100转换为小数形式，如果缺失则默认为0.0。
            # (从回撤分析结果里拿出最大回撤的百分比（比如5代表5%），然后除以100变成小数（0.05），如果拿不到就当是0.0。)

            # 5.2.4 创建参数字典并存储处理结果
            # (把这次运行的参数和提取到的性能指标一起存起来。)
            current_params_dict = {}
            # 初始化一个空字典，用于存储当前运行的参数键值对。
            # (准备一个空字典 `current_params_dict`，用来放这次跑的参数。)
            for p_name in optimized_param_names:
                # 再次遍历关心的参数名。
                # (一个一个地看那些我们关心的参数名。)
                if hasattr(params, p_name):
                    # 如果策略参数对象 `params` 具有该属性。
                    # (如果这个策略的参数里有这个名字的参数。)
                    current_params_dict[p_name] = getattr(params, p_name)
                    # 则将参数名和参数值存入字典。
                    # (就把这个参数名和它的值存到 `current_params_dict` 字典里。)
                else:
                    # 如果没有该属性。
                    # (如果没有这个参数。)
                    current_params_dict[p_name] = 'MISSING_IN_PARAMS_OBJ'
                    # 则标记为在参数对象中缺失。
                    # (就记一个 "MISSING_IN_PARAMS_OBJ"，表示这个参数在策略对象里没找到。)

            # 新增：提取策略内部的交易类型统计
            trade_stats_by_type = {}
            if hasattr(strategy_instance, 'final_trade_stats_by_type'):
                trade_stats_by_type = strategy_instance.final_trade_stats_by_type
            else:  # Fallback if the attribute is somehow missing
                trade_stats_by_type = {
                    'trend': {'pnl': 0.0, 'count': 0}, 'range': {'pnl': 0.0, 'count': 0}, 'unknown': {'pnl': 0.0, 'count': 0}
                }

            processed_results.append({
                'instance': strategy_instance,  # 保留实例可能导致内存问题，如果结果集很大，考虑不存储
                'params_dict': current_params_dict,
                'sharpe': sharpe,
                'return': total_return,
                'drawdown': max_drawdown,
                'trade_stats_by_type': trade_stats_by_type  # <--- 存储统计数据
            })
            successful_runs += 1
            # 成功提取结果的运行次数加1。
            # (成功处理了一个结果，计数器 `successful_runs` 加1。)

        except AttributeError as e:
            # 捕获在访问分析器属性时可能发生的 `AttributeError` (例如分析器未正确添加或运行)。
            # (如果在拿分析结果的时候出错了，比如某个分析器没有正确运行。)
            pass
            # 忽略此错误，继续处理下一个参数组合。
            # (那就跳过这个参数组合，继续处理其他的。)
        except Exception as e:
            # 捕获其他所有在处理单个参数组结果时发生的异常。
            # (如果发生了其他类型的错误。)
            import traceback
            # 导入 `traceback` 模块。
            # (引入 `traceback` 工具。)
            pass
            # 忽略此错误，继续处理。
            # (也跳过这个参数组合，继续处理其他的。)

    print(f"--- 完成提取分析。总运行次数: {run_count}, 成功提取结果: {successful_runs} ---")
    # 打印完成提取分析的统计信息。
    # (告诉用户分析提取完了，总共跑了多少次，成功提取出多少次的结果。)

    if not processed_results:
        # 如果 `processed_results` 列表为空（即未能成功提取任何有效的分析结果）。
        # (如果一个有效的结果都没提取出来。)
        print("\n错误：未能成功提取任何有效的分析结果。无法进行评分。")
        # 打印错误信息。
        # (就报错说没提取到有效结果，没法打分。)
        return None, []
        # 返回空结果。
        # (返回空。)

    # 5.3 提取所有结果中的各项指标并计算范围
    # (把所有成功处理的结果中的夏普率、收益率、最大回撤分别拿出来，并计算它们各自的最大值和最小值，为后续归一化做准备。)
    all_sharpes = [r['sharpe']
                   for r in processed_results if r['sharpe'] is not None]  # 过滤 None
    # 从所有处理结果 `processed_results` 中提取每个策略的夏普比率值，形成一个列表。
    # (把 `processed_results` 列表里每个结果的夏普比率都拿出来，放到一个新的列表 `all_sharpes` 里。)
    all_returns = [r['return'] for r in processed_results]
    # 提取每个策略的总收益率值。
    # (把每个结果的收益率都拿出来，放到 `all_returns` 列表里。)
    all_drawdowns = [r['drawdown'] for r in processed_results]
    # 提取每个策略的最大回撤值。
    # (把每个结果的最大回撤都拿出来，放到 `all_drawdowns` 列表里。)

    min_sharpe = min(all_sharpes) if all_sharpes else 0.0
    # 如果夏普比率列表 `all_sharpes` 不为空，则取其最小值；否则默认为0.0。
    # (如果 `all_sharpes` 列表里有数，就找出最小的那个夏普率；如果没有，就当最小是0.0。)
    max_sharpe = max(all_sharpes) if all_sharpes else 0.0
    # 计算夏普比率的最大值。
    # (找出最大的那个夏普率，如果列表是空的就当最大是0.0。)
    min_return = min(all_returns) if all_returns else 0.0
    # 计算总收益率的最小值。
    # (找出最小的那个收益率。)
    max_return = max(all_returns) if all_returns else 0.0
    # 计算总收益率的最大值。
    # (找出最大的那个收益率。)
    min_drawdown = min(all_drawdowns) if all_drawdowns else 0.0
    # 计算最大回撤的最小值。
    # (找出最小的那个最大回撤。)
    max_drawdown_val = max(all_drawdowns) if all_drawdowns else 0.0
    # 计算最大回撤的最大值（变量名用 `max_drawdown_val` 以区别于单个结果的 `max_drawdown`）。
    # (找出最大的那个最大回撤。)

    # 5.4 计算每个参数组合的归一化得分
    # (对每个参数组合的夏普率、收益率、最大回撤进行归一化处理（缩放到0-1之间），然后加权计算一个综合得分。)
    best_overall_score = float('-inf')  # Renamed from best_score
    # 初始化最佳得分为负无穷大，确保任何有效的正得分都能成为初始最佳得分。
    # (先把"最好分数"设成一个非常非常小的数（负无穷大），这样任何一个算出来的分数都会比它大。)
    best_overall_result_data = None  # Renamed from best_result_data
    # 初始化最佳结果数据为 `None`。
    # (先把"最好的结果"设成空的，等找到分数最高的再把它填进去。)
    scored_results = []
    # 初始化一个空列表 `scored_results`，用于存储所有带得分的策略结果。
    # (准备一个空列表 `scored_results`，用来放所有算过分的结果。)

    print("\n--- 开始计算归一化得分 ---")
    # 打印开始计算归一化得分的提示信息。
    # (告诉用户现在开始算每个参数组合的得分了。)
    print(f"Min/Max - Sharpe: ({min_sharpe:.4f}, {max_sharpe:.4f}), Return: ({min_return:.4f}, {max_return:.4f}), Drawdown: ({min_drawdown:.4f}, {max_drawdown_val:.4f})")
    # 打印各指标的最小值和最大值，用于了解数据分布和归一化依据。
    # (把夏普率、收益率、回撤的最小值和最大值都打出来，让用户心里有数。)

    for result_data in processed_results:
        # 遍历所有已处理的参数组合结果 `processed_results`。
        # (一个一个地看我们之前处理好的那些结果 `processed_results`。)
        sharpe = result_data.get('sharpe', 0.0)
        # 获取当前结果的夏普比率。
        # (拿出这个结果的夏普比率。)
        ret = result_data.get('return', 0.0)
        # 获取当前结果的总收益率。
        # (拿出这个结果的收益率。)
        dd = result_data.get('drawdown', 0.0)
        # 获取当前结果的最大回撤。
        # (拿出这个结果的最大回撤。)

        # 5.4.1 计算各指标的取值范围
        # (计算夏普率、收益率、最大回撤在所有结果中的波动范围。)
        sharpe_range = max_sharpe - min_sharpe
        # 计算夏普比率的取值范围（最大值 - 最小值）。
        # (算一下所有夏普率里，最大和最小的差多少。)
        return_range = max_return - min_return
        # 计算总收益率的取值范围。
        # (算一下所有收益率里，最大和最小的差多少。)
        drawdown_range = max_drawdown_val - min_drawdown
        # 计算最大回撤的取值范围。
        # (算一下所有最大回撤里，最大和最小的差多少。)

        # 5.4.2 归一化各指标到0-1范围
        # (把每个指标都转换成0到1之间的小数，方便后续加权。)
        sharpe_norm = (sharpe - min_sharpe) / \
            sharpe_range if sharpe_range > 1e-9 else 0.0
        # 归一化夏普比率：(当前值 - 最小值) / 范围。如果范围过小（接近0），则归一化值为0.0，避免除以0错误。
        # (把当前的夏普率转换成0到1之间的小数。如果所有夏普率都一样（范围是0），那就当它是0。)
        return_norm = (ret - min_return) / \
            return_range if return_range > 1e-9 else 0.0
        # 归一化总收益率。
        # (把当前的收益率也转换成0到1之间的小数。)
        drawdown_norm = (dd - min_drawdown) / \
            drawdown_range if drawdown_range > 1e-9 else 0.0
        # 归一化最大回撤。注意：这里回撤是数值越大越不好，但在计算综合得分时会用负权重。
        # (把当前的最大回撤也转换成0到1之间的小数。)

        # 5.4.3 计算综合得分
        # (根据归一化后的指标和预设的权重，计算一个综合分数。夏普率和收益率越高越好，回撤越小越好。)
        score = 0.6 * sharpe_norm + 0.1 * return_norm - 0.3 * drawdown_norm
        # 计算综合得分：夏普比率权重0.6，总收益率权重0.1，最大回撤权重-0.3（因为回撤是负面指标，所以用减号）。
        # (算总分：归一化后的夏普率占60%权重，收益率占10%权重，回撤占30%权重并且是扣分项（所以是减去）。)

        result_data['score'] = score
        # 将计算出的综合得分添加到当前结果数据字典中。
        # (把算好的这个总分 `score` 加到当前这个结果 `result_data` 里。)
        scored_results.append(result_data)
        # 将带有得分的当前结果数据添加到 `scored_results` 列表中。
        # (把这个带分数的结果 `result_data` 加到 `scored_results` 列表里。)

        # 5.4.4 更新最佳得分和结果
        # (如果当前这个参数组合的得分比之前记录的最高分还要高，就更新最高分和对应的结果。)
        if score > best_overall_score:
            # 如果当前计算的得分 `score` 高于已知的最佳得分 `best_overall_score`。
            # (如果这个分数比我们之前记录的"最好分数" `best_overall_score` 还要高。)
            best_overall_score = score
            # 更新最佳得分为当前得分。
            # (那就把这个分数更新成新的"最好分数"。)
            best_overall_result_data = result_data
            # 更新最佳结果数据为当前结果数据。
            # (同时把当前这个结果 `result_data` 记为"最好的结果" `best_overall_result_data`。)

    print(f"--- 完成 {len(scored_results)} 组得分计算 ---")
    # 打印完成得分计算的统计信息。
    # (告诉用户所有参数组合的得分都算完了，总共算了多少组。)

    # 5.5 返回最佳结果和所有带得分的结果
    # (把找到的最好的那个结果，以及所有结果的得分情况都返回出去。)
    return best_overall_result_data, scored_results
    # 函数返回最佳结果数据和所有带得分的结果列表。
    # (把最好的那个结果 `best_overall_result_data` 和所有带分数的结果列表 `scored_results` 都返回出去。)


# 6. 主程序入口
# (这是我们整个程序开始运行的地方。)
if __name__ == '__main__':
    # Python脚本的主入口点。当直接运行此脚本时，`if __name__ == '__main__':` 下的代码块将被执行。
    # (这行代码的意思是，如果我们是直接运行这个Python文件，而不是把它当做一个工具被其他文件调用，那么下面的代码就会执行。)

    # 6.1 配置回测模式和基本参数
    # (设置一些基本的回测选项，比如是否要进行参数优化、初始资金多少、手续费多少等。)
    optimize = True
    # 设置 `optimize` 标志为 `True`，表示执行参数优化模式。如果设为 `False`，则执行单次回测。
    # (设置一个开关 `optimize`，如果是 `True` 就做参数优化，如果是 `False` 就只跑一次回测。这里设的是 `True`。)
    # optimize = False # 可以取消注释此行并注释上一行，以切换到单次回测模式。
    # (如果想跑单次回测，可以把上面那行 `optimize = True` 前面加个 `#`，然后把这行 `optimize = False` 前面的 `#` 去掉。)

    initial_cash = 500000.0
    # 设置回测的初始资金金额为500,000.0。
    # (设置回测开始时的账户资金是50万元。)
    commission_rate = 0.0003
    # 设置交易佣金率为0.0003 (即万分之三)。
    # (设置每笔交易的手续费率是万分之三。)

    # 6.2 设置数据文件路径
    # (告诉程序我们的股票数据Excel文件放在哪里。)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # 获取当前脚本文件所在的绝对路径的目录部分。
    # (找出当前这个Python脚本文件所在的文件夹路径。)
    data_folder = os.path.join(script_dir, '..', '..', 'datas')
    # 基于脚本目录构建数据文件夹的相对路径，假设 'datas' 文件夹位于脚本所在目录的上两级。
    # (根据脚本的位置，找到存放数据文件的 'datas' 文件夹。这里假设 'datas' 文件夹在脚本所在文件夹的外面两层。)
    data_folder = r'D:\\BT2025\\datas\\'
    # 直接指定数据文件夹的绝对路径。这会覆盖上面通过相对路径计算得到的 `data_folder`。
    # (这里直接写死了数据文件夹的路径在 D盘的 BT2025 文件夹下的 datas 文件夹里。这会覆盖上面用相对路径算出来的结果。)
    print(f"数据文件夹路径: {data_folder}")
    # 打印最终使用的数据文件夹路径。
    # (在屏幕上显示一下数据文件夹的路径，让我们确认一下。)

    # 6.2.1 检查数据文件夹是否存在
    # (看看指定的数据文件夹是不是真的存在。)
    if not os.path.isdir(data_folder):
        # 如果指定的数据文件夹路径不是一个有效的目录。
        # (如果找不到这个数据文件夹。)
        print(f"错误: 数据文件夹路径不存在: {data_folder}")
        # 打印错误信息。
        # (就报错说找不到数据文件夹。)
        sys.exit(1)
        # 退出程序，状态码1表示错误退出。
        # (程序直接退出，因为没有数据就没法跑了。)

    # 6.2.2 定义并检查数据文件列表
    # (列出我们要用的具体数据文件名，并检查这些文件是不是都在数据文件夹里。)
    data_files = [
        os.path.join(data_folder, '510050_d.xlsx'),
        os.path.join(data_folder, '510300_d.xlsx'),
        os.path.join(data_folder, '159949_d.xlsx')
    ]
    # 创建包含三个ETF数据文件完整路径的列表。文件名分别为 '510050_d.xlsx', '510300_d.xlsx', '159949_d.xlsx'。
    # (指定我们要用的三个ETF的数据文件，分别是上证50ETF、沪深300ETF和创业板ETF的日线数据。)
    missing_files = [f for f in data_files if not os.path.isfile(f)]
    # 检查 `data_files` 列表中的每个文件路径是否存在且为文件，将不存在的文件路径收集到 `missing_files` 列表中。
    # (看看这三个文件是不是都能在数据文件夹里找到，如果哪个找不到了，就记在 `missing_files` 列表里。)
    if missing_files:
        # 如果 `missing_files` 列表不为空（即有缺失的数据文件）。
        # (如果 `missing_files` 列表里有东西，说明有文件找不到了。)
        print(f"错误: 以下数据文件未找到:")
        # 打印错误提示。
        # (就报错说有些数据文件没找到。)
        for f in missing_files:
            # 遍历并打印每个缺失文件的路径。
            # (把每个找不到的文件的名字都打出来。)
            print(f" - {f}")
        sys.exit(1)
        # 退出程序。
        # (程序直接退出，因为缺了数据也没法跑。)

    # 6.3 设置数据加载参数
    # (告诉 `load_data_to_cerebro` 函数如何处理Excel列名，以及回测的时间范围等。)
    column_mapping = {'date': 'datetime', '开盘': 'open',
                      '最高': 'high', '最低': 'low', '收盘': 'close', '成交量': 'volume'}
    # 定义Excel列名到Backtrader所需标准列名的映射字典。
    # (告诉程序Excel表格里的中文列名（比如"开盘"）对应 `backtrader` 需要的英文列名（比如"open"）。)
    openinterest_col_name = None
    # 设置持仓量列的名称为 `None`，表示数据中不使用持仓量信息。
    # (我们这里不使用持仓量数据，所以设成 `None`。)
    fromdate = datetime.datetime(2015, 1, 1)
    # 设置回测的开始日期为2015年1月1日。
    # (设定回测从2015年1月1日开始。)
    todate = datetime.datetime(2024, 4, 30)
    # 设置回测的结束日期为2024年4月30日。
    # (设定回测到2024年4月30日结束。)

    # 6.4 设置Sizer参数和策略优化参数范围
    # (为仓位管理器和策略中的可调参数设定在优化时尝试的范围。)
    sizer_params = dict(
        max_position_per_etf_percent=0.30,
    )
    # 设置传递给 `AShareETFSizer` 的参数，这里指定单个ETF最大持仓市值占总账户价值的30%。
    # (给我们的仓位管理器 `AShareETFSizer` 设置参数，这里是说单个ETF最多只能占总资金的30%。)
    ema_medium_range = range(40, 81, 20)
    # 定义EMA中期均线周期的优化范围：从40到80（不含81），步长为20 (即尝试 40, 60, 80)。
    # (设置中期EMA均线的周期在优化时尝试这几个值：40、60、80。)
    ema_long_range = range(100, 141, 20)
    # 定义EMA长期均线周期的优化范围：从100到140（不含141），步长为20 (即尝试 100, 120, 140)。
    # (设置长期EMA均线的周期在优化时尝试这几个值：100、120、140。)
    bbands_period_range = range(15, 26, 5)
    # 定义布林带周期的优化范围：从15到25（不含26），步长为5 (即尝试 15, 20, 25)。
    # (设置布林带周期的优化范围：15、20、25。)
    bbands_dev_range = np.arange(1.8, 2.3, 0.2).tolist()
    # 定义布林带标准差倍数的优化范围：从1.8到2.2（不含2.3），步长为0.2 (即尝试 1.8, 2.0, 2.2)。
    # (设置布林带标准差倍数的优化范围：1.8、2.0、2.2。)
    trend_sl_atr_mult_range = np.arange(2.0, 3.1, 0.5).tolist()
    # 定义趋势交易止损ATR倍数的优化范围：从2.0到3.0（不含3.1），步长为0.5 (即尝试 2.0, 2.5, 3.0)。
    # (设置趋势交易止损的ATR倍数优化范围：2.0、2.5、3.0。)
    range_sl_buffer_range = np.arange(0.003, 0.008, 0.002).tolist()
    # 定义区间交易止损缓冲百分比的优化范围：从0.003到0.007（不含0.008），步长为0.002 (即尝试 0.003, 0.005, 0.007)。
    # (设置区间交易止损缓冲的优化范围：0.3%、0.5%、0.7%。)
    risk_trend_range = np.arange(0.008, 0.013, 0.002).tolist()
    # 定义趋势交易每笔风险百分比的优化范围：从0.008到0.012（不含0.013），步长为0.002 (即尝试 0.8%, 1.0%, 1.2%)。
    # (设置趋势交易每笔风险比例的优化范围：0.8%、1.0%、1.2%。)
    risk_range_range = np.arange(0.004, 0.007, 0.001).tolist()
    # 定义区间交易每笔风险百分比的优化范围：从0.004到0.006（不含0.007），步长为0.001 (即尝试 0.4%, 0.5%, 0.6%)。
    # (设置区间交易每笔风险比例的优化范围：0.4%、0.5%、0.6%。)

    # 6.5 初始化Cerebro引擎
    # (创建 `backtrader` 的核心大脑 `cerebro`。)
    cerebro = bt.Cerebro(stdstats=not optimize, optreturn=False)
    # 创建Cerebro引擎实例。
    # - `stdstats=not optimize`: 如果不是优化模式 (即单次回测)，则启用标准统计图表输出；优化模式下关闭以提高效率。
    # - `optreturn=False`: 在优化模式下，不直接返回每个策略实例的完整列表，而是返回一个包含分析结果的结构，由 `analyze_optimization_results` 处理。
    # (创建回测引擎 `cerebro`。如果不是优化模式，就显示标准图表；这里还设置了 `optreturn=False`，表示优化结果的返回方式。)

    # 6.6 加载数据到Cerebro
    # (把我们准备好的ETF数据喂给 `cerebro` 大脑。)
    loaded_data_count = load_data_to_cerebro(
        cerebro, data_files, column_mapping, openinterest_col_name, fromdate, todate)
    # 调用 `load_data_to_cerebro` 函数加载数据，并获取成功加载的数据源数量。
    # (用我们前面定义的 `load_data_to_cerebro` 函数，把数据文件、列名映射规则、时间范围等传给它，让它把数据加载到 `cerebro` 里。)
    if loaded_data_count == 0:
        # 如果没有成功加载任何数据文件。
        # (如果一个数据都没加载成功。)
        print("\n错误：未能成功加载任何数据文件。无法继续执行。")
        # 打印错误信息。
        # (就报错说没加载到数据，没法继续了。)
        sys.exit(1)
        # 退出程序。
        # (程序退出。)
    print(f"\n总共加载了 {loaded_data_count} 个数据源。")
    # 打印成功加载的数据源数量。
    # (告诉用户成功加载了多少个ETF的数据。)

    # 6.7 设置初始资金和佣金
    # (告诉 `cerebro` 开始有多少钱，以及交易手续费是多少。)
    cerebro.broker.setcash(initial_cash)
    # 设置Cerebro引擎中模拟券商的初始资金。
    # (在 `cerebro` 的模拟账户里放入初始资金 `initial_cash`。)
    cerebro.broker.setcommission(commission=commission_rate, stocklike=True)
    # 设置交易佣金率，`stocklike=True` 表示使用类似股票的佣金计算方式（通常是按成交金额的百分比）。
    # (设置交易手续费，费率是 `commission_rate`，并且按股票的方式算（成交金额乘以费率）。)

    # 6.8 添加Sizer和分析器
    # (给 `cerebro` 添加我们自定义的仓位管理器和一些用来分析回测结果的工具。)
    cerebro.addsizer(AShareETFSizer, **sizer_params)
    # 添加自定义的 `AShareETFSizer` 仓位管理器到Cerebro，并传入 `sizer_params` 中定义的参数。
    # (把我们之前定义的 `AShareETFSizer`（算买多少股的工具）加到 `cerebro` 里，并把 `sizer_params` 里的参数传给它。)
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe_ratio',
                        timeframe=bt.TimeFrame.Days, riskfreerate=0.0, annualize=True, factor=252)
    # 添加夏普比率分析器：
    # - `_name='sharpe_ratio'`: 分析器的名称，方便后续获取结果。
    # - `timeframe=bt.TimeFrame.Days`: 基于日数据计算。
    # - `riskfreerate=0.0`: 无风险利率设为0。
    # - `annualize=True`: 计算年化夏普比率。
    # - `factor=252`: 年化因子，假设一年有252个交易日。
    # (添加一个夏普比率分析器，用来评估策略的风险调整后收益。告诉它按天算，无风险利率是0，要算年化的，一年按252天算。)
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    # 添加回撤分析器，用于计算策略的最大回撤等回撤相关指标。
    # (添加一个回撤分析器，用来算策略的最大亏损幅度。)
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
    # 添加收益率分析器，用于计算策略的总收益率、年化收益率等。
    # (添加一个收益率分析器，用来算策略赚了多少钱。)
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trade_analyzer')
    # 添加交易分析器，用于分析策略的交易详情，如交易次数、胜率、平均盈亏等。
    # (添加一个交易分析器，用来分析每一笔交易的情况，比如赢了多少次，输了多少次。)

    # 6.9 根据 `optimize` 标志选择执行参数优化或单次回测
    # (根据之前设置的 `optimize` 开关，决定是跑参数优化还是只跑一次。)
    if optimize:
        # 如果 `optimize` 标志为 `True`，则执行参数优化流程。
        # (如果 `optimize` 是 `True`，就进入参数优化模式。)

        # 6.9.1 打印参数优化设置
        # (显示一下这次参数优化要尝试哪些参数范围。)
        print("\n{:-^50}".format(' 参数优化设置 '))
        # 打印参数优化设置的标题。
        # (打一个标题"参数优化设置"。)
        print(f"  etf_type: ['trend', 'range']")
        # 打印ETF类型的优化选项。
        # (显示ETF交易类型会尝试 'trend' 和 'range'。)
        print(f"  ema_medium_period: {list(ema_medium_range)}")
        # 打印EMA中期均线周期的优化范围。
        # (显示中期EMA均线周期会尝试的值。)
        print(f"  ema_long_period: {list(ema_long_range)}")
        # 打印EMA长期均线周期的优化范围。
        # (显示长期EMA均线周期会尝试的值。)
        print(f"  bbands_period: {list(bbands_period_range)}")
        # 打印布林带周期的优化范围。
        # (显示布林带周期会尝试的值。)
        print(f"  bbands_devfactor: {bbands_dev_range}")
        # 打印布林带标准差倍数的优化范围。
        # (显示布林带标准差倍数会尝试的值。)
        print(f"  trend_stop_loss_atr_mult: {trend_sl_atr_mult_range}")
        # 打印趋势止损ATR倍数的优化范围。
        # (显示趋势止损ATR倍数会尝试的值。)
        print(f"  range_stop_loss_buffer: {range_sl_buffer_range}")
        # 打印区间止损缓冲的优化范围。
        # (显示区间止损缓冲会尝试的值。)
        print(f"  risk_per_trade_trend: {risk_trend_range}")
        # 打印趋势交易风险的优化范围。
        # (显示趋势交易风险比例会尝试的值。)
        print(f"  risk_per_trade_range: {risk_range_range}")
        # 打印区间交易风险的优化范围。
        # (显示区间交易风险比例会尝试的值。)
        print('-' * 50)
        # 打印分隔线。
        # (打一条分隔线。)

        # 6.9.2 添加优化策略到Cerebro
        # (告诉 `cerebro` 我们要用哪个策略 (`AShareETFStrategy`) 来进行优化，以及每个参数要尝试哪些值。)
        cerebro.optstrategy(AShareETFStrategy,
                            # etf_type=['trend', 'range'],
                            ema_medium_period=ema_medium_range,
                            ema_long_period=ema_long_range,
                            bbands_period=bbands_period_range,
                            bbands_devfactor=bbands_dev_range,
                            trend_stop_loss_atr_mult=trend_sl_atr_mult_range,
                            # range_stop_loss_buffer=range_sl_buffer_range, # 注意：以下参数被注释，不会参与此次优化
                            # risk_per_trade_trend=risk_trend_range,
                            # risk_per_trade_range=risk_range_range
                            )
        # 调用 `cerebro.optstrategy` 方法添加要进行参数优化的策略。
        # - 第一个参数是策略类 `AShareETFStrategy`。
        # - 后续参数是策略中定义的可优化参数及其对应的尝试值范围（或列表）。
        # - 被注释掉的参数将不会参与本次优化，会使用策略类中定义的默认值。
        # (把我们的 `AShareETFStrategy` 策略加到 `cerebro` 里进行优化。告诉它 `etf_type` 尝试 'trend' 和 'range'，`ema_medium_period` 尝试 `ema_medium_range` 里的值，以此类推。注意，有些参数比如 `range_stop_loss_buffer` 被注释掉了，所以这次优化不会改变它们，会用策略里默认的值。)

        # 6.9.3 运行参数优化并计时
        # (开始跑优化，并记录花了多长时间。)
        print('开始参数优化运行...')
        # 打印开始参数优化运行的提示信息。
        # (告诉用户开始跑参数优化了。)
        start_time = time.time()
        # 记录优化开始的时间戳。
        # (记一下开始时间。)
        results = cerebro.run(maxcpus=os.cpu_count() or 1)
        # 运行Cerebro引擎的优化过程。
        # - `maxcpus=os.cpu_count() or 1`: 尝试使用所有可用的CPU核心进行并行计算，如果无法获取CPU数量则默认为1。
        # (开始运行优化！`maxcpus` 会让程序尽量用电脑上所有的CPU核心一起跑，加快速度。如果电脑只有一个核心，就用一个。)
        end_time = time.time()
        # 记录优化结束的时间戳。
        # (记一下结束时间。)
        total_time = end_time - start_time
        # 计算优化的总耗时（秒）。
        # (算一下总共花了多少秒。)

        # 6.9.4 打印优化运行统计
        # (显示优化总共跑了多少组参数，花了多少时间等信息。)
        actual_combinations = 0
        # 初始化实际运行的参数组合数量。
        # (先假设实际跑的参数组合是0组。)
        if results:
            # 如果优化有结果返回。
            # (如果 `results` 不是空的，说明跑出结果了。)
            actual_combinations = len(results)
            # 计算实际运行的参数组合数量（`results` 列表的长度）。
            # (那实际跑的参数组合数量就是 `results` 列表里有多少个东西。)
        avg_time_per_run = total_time / actual_combinations if actual_combinations > 0 else 0
        # 计算每组参数组合的平均耗时。如果实际组合数为0，则平均耗时也为0。
        # (算一下平均每组参数跑了多久。如果没跑，就是0秒。)

        print('\n{:=^50}'.format(' 优化完成统计 '))
        # 打印优化完成统计的标题。
        # (打一个标题"优化完成统计"。)
        print(f"{'总用时':<20}: {total_time:.2f}秒 ({total_time/60:.2f}分钟)")
        # 打印总用时（秒和分钟）。
        # (显示总共花了多少秒，相当于多少分钟。)
        print(f"{'实际参数组数':<20}: {actual_combinations}")
        # 打印实际运行的参数组数。
        # (显示实际跑了多少组不同的参数。)
        print(f"{'每组平均用时':<20}: {avg_time_per_run:.2f}秒")
        # 打印每组平均用时。
        # (显示平均每组参数花了多少秒。)
        print('=' * 50)
        # 打印分隔线。
        # (打一条分隔线。)

        # 6.9.5 分析优化结果
        # (调用之前定义的 `analyze_optimization_results` 函数来处理优化结果，找出最好的参数。)
        best_overall_result, all_scored_results = analyze_optimization_results(results)
        # 调用 `analyze_optimization_results` 函数分析优化结果，获取最佳结果数据和所有带得分的结果列表。
        # (用我们前面写的 `analyze_optimization_results` 函数来分析这些优化结果 `results`，它会返回最好的那个结果 `best_result` 和所有结果的得分情况 `all_scored_results`。)

        # 6.9.6 打印优化结果表格
        # (如果找到了最佳结果，就把得分靠前的参数组合和它们的性能指标打印成一个表格。)
        if best_result:
            # 如果 `best_result` 不为 `None` (即成功找到了最佳结果)。
            # (如果 `best_result` 不是空的，说明找到了最好的结果。)
            best_params_dict = best_result.get('params_dict', {})
            # 获取最佳结果中的参数字典，如果缺失则默认为空字典。
            # (从最好的结果里拿出它的参数。)

            header_format_str = '{:<8} {:<8} {:<8} {:<8} {:<8} {:<8} {:<8} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10}'
            # 定义结果表格的表头格式字符串。
            # (规定一下表格表头的格式，每个字段占多少宽度，怎么对齐。)
            row_format_str = '{etf_type:<8} {ema_medium_period:<8.0f} {ema_long_period:<8.0f} {bbands_period:<8.0f} {bbands_devfactor:<8.1f} {trend_stop_loss_atr_mult:<8.1f} {range_stop_loss_buffer:<8.3f} {risk_per_trade_trend:<10.3f} {risk_per_trade_range:<10.3f} {sharpe:<10.4f} {return_val:<10.2f} {drawdown_val:<10.2f} {score:<10.4f}'
            # 定义结果表格每行数据的格式字符串。
            # (规定一下表格每一行数据的格式。)

            num_cols = 13
            # 表格的列数。
            # (表格总共有13列。)
            col_widths = [8, 8, 8, 8, 8, 8, 8, 10, 10, 10, 10, 10, 10]
            # 每列的宽度列表。
            # (每一列的宽度分别是多少。)
            total_width = sum(col_widths) + len(col_widths) - 1
            # 计算表格总宽度。
            # (算一下表格总共多宽。)

            print(f'\n{(" 参数优化结果 (按得分排序) "):=^{total_width}}')
            # 打印表格标题，使其在总宽度内居中。
            # (打一个表格的标题"参数优化结果 (按得分排序)"，让它在表格中间。)
            print(header_format_str.format('ETF类型', 'EMA中', 'EMA长', 'BB周期',
                  'BB标差', 'ATR止损', '区间SL', '趋势风险%', '区间风险%', '夏普', '收益%', '回撤%', '得分'))
            # 打印表头。
            # (把表头打出来，比如"ETF类型"、"EMA中"等等。)
            print('-' * total_width)
            # 打印分隔线。
            # (在表头下面打一条横线。)

            all_scored_results.sort(key=lambda x: x.get(
                'score', float('-inf')), reverse=True)
            # 将所有带得分的结果 `all_scored_results` 按 'score' 键的值进行降序排序。如果 'score' 缺失，则默认为负无穷大。
            # (把所有算过分的结果 `all_scored_results` 按照分数从高到低排个序。)

            for res_data in all_scored_results[:min(20, len(all_scored_results))]:
                # 遍历排序后得分最高的前20个结果（或所有结果，如果总数少于20）。
                # (只看分数最高的那些结果，最多看20个，如果总共不到20个就全看。)
                p_dict = res_data.get('params_dict', {})
                # 获取当前结果的参数字典。
                # (拿出这个结果的参数。)
                print(row_format_str.format(
                    etf_type=p_dict.get('etf_type', 'N/A'),
                    ema_medium_period=p_dict.get('ema_medium_period', 0),
                    ema_long_period=p_dict.get('ema_long_period', 0),
                    bbands_period=p_dict.get('bbands_period', 0),
                    bbands_devfactor=p_dict.get('bbands_devfactor', 0.0),
                    trend_stop_loss_atr_mult=p_dict.get(
                        'trend_stop_loss_atr_mult', 0.0),
                    range_stop_loss_buffer=p_dict.get(
                        'range_stop_loss_buffer', 0.0),
                    risk_per_trade_trend=p_dict.get(
                        'risk_per_trade_trend', 0.0) * 100,  # 转换为百分比显示
                    risk_per_trade_range=p_dict.get(
                        'risk_per_trade_range', 0.0) * 100,  # 转换为百分比显示
                    sharpe=res_data.get('sharpe', 0.0),
                    return_val=res_data.get('return', 0.0) * 100,  # 转换为百分比显示
                    drawdown_val=res_data.get(
                        'drawdown', 0.0) * 100,  # 转换为百分比显示
                    score=res_data.get('score', 0.0)
                ))
                # 使用行格式字符串打印当前结果的参数和性能指标。
                # (把这个结果的参数、夏普率、收益率（转成百分比）、回撤（转成百分比）、得分都按照格式打出来。)

            # 6.9.7 打印最优参数组合详情
            # (把找到的那个最好的参数组合和它的性能指标单独再详细打印一遍。)
            print(f'\n{(" 最优参数组合 "):=^50}')
            # 打印最优参数组合的标题。
            # (打一个标题"最优参数组合"。)
            print(f"{'ETF类型':<25}: {best_params_dict.get('etf_type', 'N/A')}")
            # 打印最优ETF类型。
            # (显示最好的ETF类型是什么。)
            print(f"{'EMA中期':<25}: {best_params_dict.get('ema_medium_period', 0)}")
            # 打印最优EMA中期周期。
            # (显示最好的EMA中期周期是多少。)
            print(f"{'EMA长期':<25}: {best_params_dict.get('ema_long_period', 0)}")
            # 打印最优EMA长期周期。
            # (显示最好的EMA长期周期是多少。)
            print(f"{'布林带周期':<25}: {best_params_dict.get('bbands_period', 0)}")
            # 打印最优布林带周期。
            # (显示最好的布林带周期是多少。)
            print(
                f"{'布林带标准差':<25}: {best_params_dict.get('bbands_devfactor', 0.0):.1f}")
            # 打印最优布林带标准差倍数，保留一位小数。
            # (显示最好的布林带标准差倍数是多少，保留一位小数。)
            print(
                f"{'趋势止损ATR倍数':<25}: {best_params_dict.get('trend_stop_loss_atr_mult', 0.0):.1f}")
            # 打印最优趋势止损ATR倍数，保留一位小数。
            # (显示最好的趋势止损ATR倍数是多少，保留一位小数。)
            print(
                f"{'区间止损缓冲':<25}: {best_params_dict.get('range_stop_loss_buffer', 0.0):.4f}")
            # 打印最优区间止损缓冲，保留四位小数。
            # (显示最好的区间止损缓冲是多少，保留四位小数。)
            print(
                f"{'趋势交易风险':<25}: {best_params_dict.get('risk_per_trade_trend', 0.0)*100:.2f}%")
            # 打印最优趋势交易风险百分比，保留两位小数。
            # (显示最好的趋势交易风险比例是多少，转成百分比后保留两位小数。)
            print(
                f"{'区间交易风险':<25}: {best_params_dict.get('risk_per_trade_range', 0.0)*100:.2f}%")
            # 打印最优区间交易风险百分比，保留两位小数。
            # (显示最好的区间交易风险比例是多少，转成百分比后保留两位小数。)
            print(f"{'夏普比率':<25}: {best_result.get('sharpe', 0.0):.4f}")
            # 打印最优夏普比率，保留四位小数。
            # (显示最好的夏普比率是多少，保留四位小数。)
            print(f"{'总收益率':<25}: {best_result.get('return', 0.0) * 100:.2f}%")
            # 打印最优总收益率百分比，保留两位小数。
            # (显示最好的总收益率是多少，转成百分比后保留两位小数。)
            print(f"{'最大回撤':<25}: {best_result.get('drawdown', 0.0) * 100:.2f}%")
            # 打印最优最大回撤百分比，保留两位小数。
            # (显示最好的最大回撤是多少，转成百分比后保留两位小数。)
            print(f"{'得分':<25}: {best_result.get('score', 0.0):.4f}")
            # 打印最优得分，保留四位小数。
            # (显示最好的得分是多少，保留四位小数。)
            print('=' * 50)
            # 打印分隔线。
            # (打一条分隔线。)
        else:
            # 如果未能确定最优策略或处理结果时出错。
            # (如果 `best_result` 是空的，说明没找到最好的结果或者处理出错了。)
            print("\n错误：未能确定最优策略或处理结果时出错。")
            # 打印错误信息。
            # (就报错说没找到最好的策略或者处理结果出错了。)

    # 6.10 单次回测模式
    # (如果 `optimize` 开关是关着的，就执行这里，只用一组固定的参数跑一次回测。)
    else:
        # 如果 `optimize` 标志为 `False`，则执行单次回测流程。
        # (如果 `optimize` 是 `False`，就进入单次回测模式。)
        print("\n{:-^50}".format(' 单次回测设置 '))
        # 打印单次回测设置的标题。
        # (打一个标题"单次回测设置"。)
        print(f"优化开关: 关闭")
        # 表明优化开关已关闭。
        # (告诉用户优化开关是关着的。)
        print(f"Observer 图表: 开启")
        # 表明在单次回测时，标准统计图表（Observers）是开启的（由 `stdstats=not optimize` 控制）。
        # (告诉用户这次会显示图表。)
        print("\nSizer 参数:")
        # 打印Sizer参数的子标题。
        # (显示Sizer（仓位管理器）用的参数。)
        for k, v in sizer_params.items():
            # 遍历并打印 `sizer_params` 字典中的每个键值对。
            # (把 `sizer_params` 里的每个参数和它的值都打出来。)
            print(f"  {k}: {v}")

        strategy_run_params = dict(
            # etf_type='trend',
            ema_medium_period=60,
            ema_long_period=120,
            bbands_period=20,
            bbands_devfactor=2.0,
            trend_stop_loss_atr_mult=2.5,
            range_stop_loss_buffer=0.005,
            risk_per_trade_trend=0.01,
            risk_per_trade_range=0.005
        )
        # 定义单次回测时使用的固定策略参数。
        # (这里写死了一套参数，单次回测就用这套参数来跑。)
        print("\n策略 参数:")
        # 打印策略参数的子标题。
        # (显示策略用的参数。)
        for k, v in strategy_run_params.items():
            # 遍历并打印 `strategy_run_params` 字典中的每个键值对。
            # (把这套固定参数里的每个参数和它的值都打出来。)
            print(f"  {k}: {v}")
        print('-' * 50)
        # 打印分隔线。
        # (打一条分隔线。)

        cerebro.addstrategy(AShareETFStrategy, **strategy_run_params)
        # 将 `AShareETFStrategy` 策略添加到Cerebro，并传入 `strategy_run_params` 中定义的固定参数。
        # (把我们的 `AShareETFStrategy` 策略加到 `cerebro` 里，并告诉它用 `strategy_run_params` 这套参数。)

        print('开始单次回测运行...')
        # 打印开始单次回测运行的提示信息。
        # (告诉用户开始跑单次回测了。)
        print('期初总资金: %.2f' % cerebro.broker.getvalue())
        # 打印回测开始时的账户总资金。
        # (显示回测开始时账户里有多少钱。)
        start_time = time.time()
        # 记录回测开始的时间戳。
        # (记一下开始时间。)
        results = cerebro.run()
        # 运行Cerebro引擎的单次回测。`results` 将是一个包含单个策略实例的列表。
        # (开始跑回测！这次 `results` 里会装着跑完的那个策略实例。)
        end_time = time.time()
        # 记录回测结束的时间戳。
        # (记一下结束时间。)
        final_value = cerebro.broker.getvalue()
        # 获取回测结束时的账户总资金。
        # (看看回测结束后账户里还剩多少钱。)
        print('期末总资金: %.2f' % final_value)
        # 打印回测结束时的账户总资金。
        # (显示回测结束后账户里的钱。)
        print('回测总用时: {:.2f}秒'.format(end_time - start_time))
        # 打印回测总用时。
        # (显示这次回测总共花了多少秒。)
        print(f"总收益率: {(final_value / initial_cash - 1) * 100:.2f}%")
        # 计算并打印总收益率。
        # (算一下总共赚了还是亏了百分之多少。)

        print("\n{:-^50}".format(' 单次回测分析结果 '))
        # 打印单次回测分析结果的标题。
        # (打一个标题"单次回测分析结果"。)
        if results:  # 检查 results 是否非空 (单次回测时，results是包含一个策略实例的列表)
            # 如果 `results` 列表不为空（即策略成功运行并返回了实例）。
            # (如果 `results` 不是空的，说明策略跑完了。)
            strat_instance = results[0]
            # 获取策略实例，它是 `results` 列表中的第一个（也是唯一一个）元素。
            # (从 `results` 里拿出那个策略实例。)
            for analyzer_name, analyzer_obj in strat_instance.analyzers.getitems():
                # 遍历策略实例中所有已添加的分析器。
                # (看看这个策略实例有哪些分析器，比如夏普率分析器、回撤分析器等。)
                analysis = analyzer_obj.get_analysis()
                # 获取当前分析器的分析结果。
                # (拿出这个分析器的分析结果。)
                print(f"\n--- {analyzer_name} ---")
                # 打印分析器的名称作为子标题。
                # (把分析器的名字打出来，比如"--- sharpe_ratio ---"。)
                if isinstance(analysis, dict):
                    # 如果分析结果是一个字典。
                    # (如果分析结果是个字典，里面可能有很多项。)
                    for k, v in analysis.items():
                        # 遍历字典中的每个键值对。
                        # (就把字典里的每一项都打出来。)
                        if isinstance(v, dict):
                            # 如果值本身也是一个字典（嵌套字典）。
                            # (如果值本身还是个字典，那就再往里一层打。)
                            print(f"  {k}:")
                            for sub_k, sub_v in v.items():
                                # 遍历内层字典的键值对。
                                # (把内层字典的每一项也打出来。)
                                if isinstance(sub_v, float):
                                    # 如果内层字典的值是浮点数，则格式化输出。
                                    # (如果是数字，就保留几位小数再打。)
                                    print(f"    {sub_k}: {sub_v:.4f}")
                                else:
                                    # 否则直接打印。
                                    # (如果不是数字，就直接打。)
                                    print(f"    {sub_k}: {sub_v}")
                        else:
                            # 如果值不是字典。
                            # (如果值不是字典。)
                            if isinstance(v, float):
                                # 如果值是浮点数，则格式化输出。
                                # (如果是数字，就保留几位小数再打。)
                                print(f"  {k}: {v:.4f}")
                            else:
                                # 否则直接打印。
                                # (如果不是数字，就直接打。)
                                print(f"  {k}: {v}")
                elif isinstance(analysis, float):
                    # 如果分析结果本身就是一个浮点数。
                    # (如果分析结果直接就是一个数字。)
                    print(f"{analysis:.4f}")
                    # 则格式化输出。
                    # (那就保留几位小数再打。)
                else:
                    # 其他类型的分析结果直接打印。
                    # (如果是其他类型的结果，就直接打。)
                    print(analysis)
        print('-' * 50)
        # 打印分隔线。
        # (打一条分隔线。)

        # 6.10.1 尝试绘制图表 (仅在单次回测且非优化模式下)
        # (如果不是优化模式，就尝试画出K线图和交易点位图。)
        if not optimize:  # 确保 optimize 确实为 False
            # 再次确认当前不是优化模式。
            # (确保现在确实是单次回测模式。)
            try:
                # 6.10.1.1 检查数据并绘制
                # (看看有没有数据可以画，有的话就画第一个数据的图。)
                print("\n尝试绘制图表...")
                # 打印尝试绘制图表的提示信息。
                # (告诉用户要开始画图了。)
                if cerebro.datas:
                    # 检查Cerebro引擎中是否已加载数据源。
                    # (看看 `cerebro` 大脑里有没有数据。)
                    data_to_plot_name = cerebro.datas[0]._name
                    # 获取第一个数据源的名称，用于在图表标题或日志中显示。
                    # (拿出第一个数据的名字，比如股票代码。)
                    print(f"尝试为 {data_to_plot_name} 生成图表...")
                    # 打印为哪个数据源生成图表的提示。
                    # (告诉用户要给这个数据画图了。)
                    cerebro.plot(style='candlestick', barup='red', bardown='green',
                                 volume=True, plotdatanames=[data_to_plot_name])
                    # 调用 `cerebro.plot()` 方法绘制图表：
                    # - `style='candlestick'`: 使用K线图样式。
                    # - `barup='red'`, `bardown='green'`: 设置阳线为红色，阴线为绿色 (A股习惯)。
                    # - `volume=True`: 显示成交量副图。
                    # - `plotdatanames=[data_to_plot_name]`: 指定只绘制第一个数据源的图表。
                    # (开始画图！用K线图的样式，涨的时候是红柱子，跌的时候是绿柱子（A股习惯），下面带成交量图，只画第一个数据的图。)
                    print("图表已尝试使用 Matplotlib 显示。")
                    # 打印图表已尝试显示的提示。
                    # (告诉用户图已经试着画出来了，如果电脑环境配置好了就能看到。)
                else:
                    # 如果没有数据可供绘制。
                    # (如果 `cerebro` 里没数据。)
                    print("没有数据可供绘制。")
                    # 打印没有数据可绘制的提示。
                    # (就说没数据，画不了图。)
            # 6.10.1.2 处理绘图相关的导入错误
            # (如果画图需要的 `matplotlib` 库没装，就提示一下。)
            except ImportError:
                # 捕获因缺少 'matplotlib' 库而引发的 `ImportError`。
                # (如果电脑上没装 `matplotlib` 这个画图工具包。)
                print("\n无法绘制图表：缺少 'matplotlib' 库。请使用 pip install matplotlib 安装。")
                # 打印错误信息，并提示用户如何安装。
                # (就告诉用户画不了图，因为缺了 `matplotlib`，可以用 `pip install matplotlib` 来装。)
            # 6.10.1.3 处理其他绘图异常
            # (如果画图时发生其他错误，也提示一下。)
            except Exception as e:
                # 捕获在绘制图表过程中可能发生的其他所有异常。
                # (如果画图的时候发生了其他错误。)
                print(f"\n绘制图表时出错: {e}")
                # 打印通用错误信息及异常详情。
                # (就告诉用户画图出错了，并显示具体的错误信息。)
                print("请确保已安装绘图库 (matplotlib) 且图形环境配置正确。")
                # 提示用户检查绘图库安装和图形环境配置。
                # (提醒用户检查一下是不是 `matplotlib` 装好了，或者电脑的图形显示环境有没有问题。)
