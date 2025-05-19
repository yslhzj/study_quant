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
import pprint


class AShareETFSizer(bt.Sizer):
    # 定义一个名为 AShareETFSizer 的类，它继承自 backtrader.Sizer 类。
    # (我们正在创建一个专门用来计算A股ETF买卖数量的工具，这个工具是基于 `backtrader` 框架里的 `Sizer` 类来定制的。)
    params = (
        # 定义该Sizer的参数，这些参数可以在Sizer实例化时被覆盖。
        # (这里可以设置一些这个算数量工具的选项，用的时候可以改。)
        ('max_position_per_etf_percent', 0.30),
        # 定义参数 `max_position_per_etf_percent`，默认值为0.30 (30%)。
        # (这个选项是 'max_position_per_etf_percent'，默认是0.30，意思是单个ETF最多能占总资产的30%。)
    )

    def _getsizing(self, comminfo, cash, data, isbuy):
        # 定义 `_getsizing` 方法，此方法由Backtrader在需要确定头寸大小时调用。
        # (定义一个名叫 `_getsizing` 的函数，`backtrader` 每次要决定买多少股票的时候，就会来调用这个函数。)
        # comminfo: 交易手续费信息对象。 (手续费怎么算的信息。)
        # cash: 当前可用的现金。 (现在账户里有多少钱能用。)
        # data: 当前交易的金融产品数据。 (当前要交易的这只ETF的数据。)
        # isbuy: 布尔值，指示当前操作是否为买入。 (告诉我们现在是要买还是卖，True就是要买。)

        # --- 初始化和基本检查 ---
        # (Initial checks and setup)
        if not isbuy:
            # 检查当前操作是否为买入操作。
            # (判断一下是不是要买入。)
            return 0
            # 如果不是买入操作，则返回0，表示不进行任何头寸调整（此Sizer只处理买入）。
            # (如果不是买入，就返回0，意思是不买也不卖，这个工具只管买的时候算数量。)

        position = self.broker.getposition(data)
        # 获取当前数据对象（例如某ETF）在经纪商处的持仓情况。
        # (查一下现在手上有没有这只ETF，有多少股。)
        if position.size != 0:
            # 检查是否已持有该ETF的仓位。
            # (如果已经持有这只ETF了，也就是持仓数量不是0。)
            return 0
            # 如果已有持仓，则返回0，表示不重复开仓。
            # (那就返回0，意思是不再买了，避免重复买入已经有的。)

        d_name = data._name
        # 获取当前数据对象（ETF）的名称。
        # (拿到这只ETF的名字，比如“华夏沪深300ETF”。)
        strategy = self.strategy
        # 获取与此Sizer关联的策略实例。
        # (拿到咱们正在用的那个交易策略本身，这样可以从策略那里获取信息。)

        # --- 从策略获取预计算的风险信息 ---
        # (Decoupling Point: Get pre-calculated risk info from strategy)
        if not hasattr(strategy, 'pending_trade_info') or d_name not in strategy.pending_trade_info:
            # 检查策略实例中是否存在 'pending_trade_info' 属性，并且该属性（通常是一个字典）中是否包含当前ETF名称的键。
            # (看看策略那边有没有准备好一个叫 'pending_trade_info' 的本子，以及本子里有没有记录这只ETF的交易计划。)
            strategy.log(
                f"Sizer: 无法在 strategy.pending_trade_info 中找到 {d_name} 的待处理交易信息。跳过。", data=data)
            # 记录日志，说明未找到当前ETF的待处理交易信息。
            # (如果找不到，就记个日志说一声，这只ETF的交易计划没找到，这次买不了。)
            return 0
            # 返回0，表示不进行交易。
            # (返回0，不买了。)

        trade_info = strategy.pending_trade_info[d_name]
        # 从策略的 'pending_trade_info' 字典中获取当前ETF的交易信息。
        # (从策略的 'pending_trade_info' 本子里拿出这只ETF的交易计划。)

        entry_price = trade_info.get('entry_price')
        # 从交易信息中获取策略计算的参考入场价。
        # (拿到策略计划的买入参考价。)
        risk_per_share = trade_info.get('risk_per_share')
        # 从交易信息中获取策略计算的每股风险。
        # (拿到策略算好的买一股可能亏多少钱。)
        amount_to_risk = trade_info.get('amount_to_risk')
        # 从交易信息中获取策略计算的本次交易允许的最大风险金额。
        # (拿到策略算好的这次交易最多能亏多少钱。)

        # --- 验证从策略获取的信息是否有效 ---
        # (Validate info received from strategy)
        if entry_price is None or risk_per_share is None or amount_to_risk is None:
            # 检查从策略获取的关键交易信息（入场价、每股风险、总风险金额）是否有缺失。
            # (看看是不是缺了买入价、每股风险、或者总风险金额这些重要的信息。)
            strategy.log(
                f"Sizer: 从策略获取的 {d_name} 交易信息不完整。跳过。信息: {trade_info}", data=data)
            # 记录日志，说明交易信息不完整。
            # (如果信息不全，记个日志说一下，这次买不了，顺便把不全的信息也记下来。)
            del strategy.pending_trade_info[d_name]
            # 从策略的 'pending_trade_info' 中删除这条无效的交易信息，避免后续混淆。
            # (把策略那边对应的这条无效计划也删掉，免得下次还用它。)
            return 0
            # 返回0，表示不进行交易。
            # (返回0，不买了。)

        if risk_per_share <= 1e-9: # 使用一个很小的数来避免浮点数比较问题
            # 检查策略计算的每股风险是否过小（接近或等于0）。
            # (如果策略算出来每股风险几乎是0，或者是个负数，这不合理。)
            strategy.log(
                f"Sizer: 策略计算的 {d_name} 每股风险({risk_per_share:.2f})过小。跳过。", data=data)
            # 记录日志，说明每股风险过小。
            # (记个日志说策略算出来的风险太小了，不正常，买不了。)
            del strategy.pending_trade_info[d_name]
            # 从策略的 'pending_trade_info' 中删除这条无效的交易信息。
            # (把策略那边对应的计划删掉。)
            return 0
            # 返回0，表示不进行交易。
            # (返回0，不买了。)
        if amount_to_risk <= 1e-9: # 使用一个很小的数来避免浮点数比较问题
            # 检查策略计算的本次交易允许的最大风险金额是否过小（接近或等于0）。
            # (如果策略算出来这次交易能承担的总风险几乎是0，或者是个负数，那也没法买。)
            strategy.log(
                f"Sizer: 策略计算的 {d_name} 最大风险金额({amount_to_risk:.2f})过小。跳过。", data=data)
            # 记录日志，说明最大风险金额过小。
            # (记个日志说策略算出来的总风险太小了，买不了。)
            del strategy.pending_trade_info[d_name]
            # 从策略的 'pending_trade_info' 中删除这条无效的交易信息。
            # (把策略那边对应的计划删掉。)
            return 0
            # 返回0，表示不进行交易。
            # (返回0，不买了。)

        # --- 核心计算：基于策略提供的风险信息计算头寸 ---
        # (Core Calculation: Size based on risk info provided by strategy)
        size_raw = amount_to_risk / risk_per_share
        # 根据最大风险金额和每股风险计算原始的股票数量（可能带有小数）。
        # (用最多能亏的钱除以每股亏的钱，得到一个初步的购买数量，这个数可能有小数。)
        size = int(size_raw / 100) * 100
        # 将原始数量向下取整到最近的100的倍数（A股交易单位通常为100股的整数倍）。
        # (按A股规矩，买股票得是100股的整数倍，所以把上面算出来的数量向下凑个整，比如算出来150股，就按100股算。)

        if size <= 0:
            # 检查根据风险计算出的头寸数量是否小于或等于0。
            # (如果算出来要买的数量是0或者负数。)
            strategy.log(
                f"Sizer: 基于策略风险计算 {d_name} 的头寸为 {size}。风险/股: {risk_per_share:.2f}, 允许风险额: {amount_to_risk:.2f}", data=data)
            # 记录日志，说明基于风险计算的头寸无效。
            # (记个日志说按风险算下来买不了，或者买的数量是0。)
            del strategy.pending_trade_info[d_name]
            # 从策略的 'pending_trade_info' 中删除这条交易信息。
            # (把策略那边对应的计划删掉。)
            return 0
            # 返回0，表示不进行交易。
            # (返回0，不买了。)

        # --- 应用 Sizer 自身的全局限制 (例如：单个ETF最大仓位占比) ---
        # (Apply Sizer's own global constraints, e.g., max position per ETF)
        equity = self.broker.getvalue()
        # 获取当前账户总净值（总资产）。
        # (看看现在账户里总共有多少钱，包括股票市值和现金。)
        max_pos_value_for_etf = equity * self.p.max_position_per_etf_percent
        # 根据账户总净值和Sizer参数中设定的单个ETF最大持仓比例，计算单个ETF允许的最大持仓市值。
        # (用总资产乘以咱们之前设定的单个ETF最多占30%的比例，算出这只ETF最多能买多少钱的。)
        price_for_value_calc = entry_price
        # 使用策略提供的参考入场价进行后续的市值和数量计算。
        # (用策略计划的那个买入参考价来算市值。)

        if price_for_value_calc <= 1e-9: # 使用一个很小的数来避免浮点数比较问题
            # 检查策略提供的参考入场价是否有效（大于一个极小值）。
            # (如果策略给的买入价太小了，比如是0或者负数，这不合理。)
            strategy.log(
                f"Sizer: 策略提供的 {d_name} 参考入场价 ({price_for_value_calc:.2f}) 无效。", data=data)
            # 记录日志，说明参考入场价无效。
            # (记个日志说策略给的价格不对。)
            del strategy.pending_trade_info[d_name]
            # 从策略的 'pending_trade_info' 中删除这条交易信息。
            # (把策略那边对应的计划删掉。)
            return 0
            # 返回0，表示不进行交易。
            # (返回0，不买了。)

        size_limited_by_max_etf_pos = int(
            max_pos_value_for_etf / price_for_value_calc / 100) * 100
        # 根据单个ETF允许的最大持仓市值和参考入场价，计算允许的最大股数，并向下取整到100的倍数。
        # (根据这只ETF最多能买多少钱，以及它的价格，算出最多能买多少股，同样要凑100股的整数倍。)
        if size > size_limited_by_max_etf_pos:
            # 如果基于风险计算的头寸数量超过了单个ETF最大仓位限制所允许的数量。
            # (如果前面按风险算出来的数量，比按“单个ETF最多占总资产30%”这个规矩算出来的数量还多。)
            strategy.log(
                f"Sizer: {d_name} 头寸从 {size} 减少到 {size_limited_by_max_etf_pos} (受限于 max_position_per_etf_percent)。", data=data)
            # 记录日志，说明头寸因达到最大ETF仓位限制而被调整。
            # (记个日志说因为单个ETF仓位限制，买的数量减少了。)
            size = size_limited_by_max_etf_pos
            # 将头寸数量调整为单个ETF最大仓位限制所允许的最大数量。
            # (那就按最大仓位允许的数量来买。)

        if size <= 0:
            # 检查在应用最大ETF仓位限制后，头寸数量是否小于或等于0。
            # (如果调整完发现买不了了，比如最大仓位允许买0股。)
            strategy.log(f"Sizer: {d_name} 头寸在最大ETF仓位限制后为 {size}。", data=data)
            # 记录日志，说明调整后的头寸无效。
            # (记个日志说因为仓位限制，最后买不了。)
            del strategy.pending_trade_info[d_name]
            # 从策略的 'pending_trade_info' 中删除这条交易信息。
            # (把策略那边对应的计划删掉。)
            return 0
            # 返回0，表示不进行交易。
            # (返回0，不买了。)

        # --- 检查现金是否足够 ---
        # (Check if cash is sufficient)
        potential_trade_total_cost = size * price_for_value_calc
        # 根据当前计算出的头寸数量和参考入场价，估算本次交易的总成本（不含手续费）。
        # (算一下按这个数量和价格买，大概要花多少钱。)
        if potential_trade_total_cost > cash:
            # 如果预估的交易总成本超过当前账户可用现金。
            # (如果要花的钱比现在账户里能用的现金还多。)
            size_limited_by_cash = int(cash / price_for_value_calc / 100) * 100
            # 根据可用现金和参考入场价，计算能买的最大股数，并向下取整到100的倍数。
            # (那就用能用的现金，看看能买多少股，也要凑100股的整数倍。)
            if size_limited_by_cash < size:
                # 如果根据现金计算出的可买股数小于当前已计算的股数。
                # (如果按现金算出来能买的数量，比之前算出来的数量还要少。)
                strategy.log(
                    f"Sizer: {d_name} 头寸从 {size} 减少到 {size_limited_by_cash} (受限于现金)。现金: {cash:.2f}, 预估成本: {potential_trade_total_cost:.2f}", data=data)
                # 记录日志，说明头寸因现金不足而被调整。
                # (记个日志说因为钱不够，买的数量又减少了。)
                size = size_limited_by_cash
                # 更新头寸数量为现金允许的最大数量。
                # (那就按现金能买的最大数量来买。)

        if size <= 0:
            # 检查在所有限制（风险、最大仓位、现金）应用后，最终计算的头寸数量是否小于或等于0。
            # (如果最后算下来，综合各种限制，发现买不了了，数量是0或者负数。)
            strategy.log(f"Sizer: {d_name} 最终计算头寸为 {size}。无法下单。", data=data)
            # 记录日志，说明最终计算的头寸无效，无法下单。
            # (记个日志说最后算出来买不了。)
            del strategy.pending_trade_info[d_name]
            # 从策略的 'pending_trade_info' 中删除这条交易信息。
            # (把策略那边对应的计划删掉。)
            return 0
            # 返回0，表示不进行交易。
            # (返回0，不买了。)

        # --- Sizer 计算完成，返回最终头寸 ---
        # (Sizer calculation complete, return final size)
        strategy.log(f"Sizer为 {d_name} 计算头寸: {size} (基于策略风险信息)", data=data)
        # 记录日志，说明Sizer为当前ETF计算得到的最终头寸数量。
        # (记个日志，告诉大家最后算出来要买多少股，这个数量是根据策略给的风险信息，并且考虑了各种限制后得出的。)

        # 注意：Sizer成功计算并返回头寸后，相关的pending_trade_info应由策略在notify_order中根据订单状态进行清理。
        # (提醒一下：如果这里成功算出了购买数量，那么策略那边对应的交易计划，应该在订单被接受或者成交之后再清理，而不是在这里清理。)
        return size
        # 返回最终计算得到的头寸数量。
        # (把最后算好的购买数量告诉 `backtrader`，它会用这个数量去下单。)

class AShareETFStrategy(bt.Strategy):
    # 定义一个名为 AShareETFStrategy 的类，它继承自 backtrader.Strategy 类。
    # (我们正在创建一个新的交易策略，专门给A股的ETF用，这个策略是基于 `backtrader` 框架的。)
    params = (
        # 定义策略的参数，这些参数可以在策略实例化时被覆盖。
        # (这里是策略可以用到的一些设置，比如用什么指标，指标的参数是多少等等，我们可以在用这个策略的时候改这些设置。)
        ('etf_type', 'trend'),
        # 参数：ETF交易类型，默认为'trend'（趋势型）。可选值可能包括'range'（区间型）。
        # (这个参数用来告诉策略，咱们主要想做趋势型的交易还是区间型的交易，默认是趋势型。)
        ('ema_medium_period', 60),
        # 参数：中期指数移动平均线（EMA）的周期，默认为60。
        # (这是中期指数移动平均线（EMA）要看多少天的数据，默认是60天。)
        ('ema_long_period', 120),
        # 参数：长期指数移动平均线（EMA）的周期，默认为120。
        # (这是长期指数移动平均线（EMA）要看多少天的数据，默认是120天。)
        ('adx_period', 14),
        # 参数：ADX（平均趋向指数）的周期，默认为14。
        # (这是ADX指标要看多少天的数据，默认是14天，ADX用来判断趋势的强度。)
        ('atr_period', 20),
        # 参数：ATR（平均真实波幅）的周期，默认为20。
        # (这是ATR指标要看多少天的数据，默认是20天，ATR用来衡量价格波动的幅度。)
        ('bbands_period', 20),
        # 参数：布林带（Bollinger Bands）的周期，默认为20。
        # (这是布林带指标要看多少天的数据，默认是20天。)
        ('bbands_devfactor', 2.0),
        # 参数：布林带的标准差倍数，默认为2.0。
        # (这是布林带上下轨离中轨多远，用标准差的倍数来算，默认是2倍。)
        ('rsi_period', 14),
        # 参数：RSI（相对强弱指数）的周期，默认为14。
        # (这是RSI指标要看多少天的数据，默认是14天，RSI用来判断是不是超买或超卖。)
        ('rsi_oversold', 30),
        # 参数：RSI的超卖阈值，默认为30。
        # (RSI指标低于这个数，就认为是超卖了，默认是30。)
        ('trend_breakout_lookback', 60),
        # 参数：趋势突破策略中回顾期窗口大小，用于寻找前期高点，默认为60。
        # (在趋势突破策略里，我们要看过去多少天内的最高价，默认是60天。)
        ('trend_volume_avg_period', 20),
        # 参数：趋势策略中计算成交量均线的周期，默认为20。
        # (在趋势策略里，我们要算成交量的平均值，看过去多少天，默认是20天。)
        ('trend_volume_ratio_min', 1.1),
        # 参数：趋势策略中当前成交量相对于成交量均线的最小比率，用于确认突破，默认为1.1。
        # (在趋势策略里，突破的时候，成交量至少要是平均成交量的多少倍才算数，默认是1.1倍。)
        ('trend_stop_loss_atr_mult', 2.5),
        # 参数：趋势策略中止损计算时ATR的倍数，默认为2.5。
        # (在趋势策略里，止损价是入场价减去ATR乘以这个数，默认是2.5倍ATR。)
        ('trend_take_profit_rratio', 2.0),
        # 参数：趋势策略中止盈目标相对于风险的倍数（Risk/Reward Ratio），默认为2.0。
        # (在趋势策略里，止盈目标是风险（入场价减止损价）的多少倍，默认是2倍。)
        ('range_stop_loss_buffer', 0.005),
        # 参数：区间策略中止损计算时的缓冲百分比，默认为0.005 (0.5%)。
        # (在区间策略里，止损价是最低价再往下浮动一点点，这个就是浮动的百分比，默认是0.5%。)
        ('max_total_account_risk_percent', 0.06),
        # 参数：账户允许的最大总风险百分比（例如，所有持仓的总风险不超过账户价值的6%），默认为0.06。
        # (整个账户里，所有股票加起来的总风险，不能超过账户总钱数的这个百分比，默认是6%。)
        ('drawdown_level1_threshold', 0.05),
        # 参数：一级回撤阈值，当账户回撤达到此水平时触发风险降低措施，默认为0.05 (5%)。
        # (当账户从最高点亏到这个百分比的时候，算是一级警报，默认是5%。)
        ('drawdown_level2_threshold', 0.10),
        # 参数：二级回撤阈值，当账户回撤达到此水平时触发暂停交易等更严厉措施，默认为0.10 (10%)。
        # (当账户从最高点亏到这个百分比的时候，算是二级警报，可能会暂停交易，默认是10%。)
        ('risk_per_trade_trend', 0.01),
        # 参数：趋势型交易中单笔交易所允许的最大风险占账户价值的百分比，默认为0.01 (1%)。
        # (做趋势交易的时候，每一笔最多允许亏损账户总钱数的这个百分比，默认是1%。)
        ('risk_per_trade_range', 0.005),
        # 参数：区间型交易中单笔交易所允许的最大风险占账户价值的百分比，默认为0.005 (0.5%)。
        # (做区间交易的时候，每一笔最多允许亏损账户总钱数的这个百分比，默认是0.5%。)
    )

    def log(self, txt, dt=None, data=None):
        # 定义一个日志记录方法，用于在策略执行过程中输出信息。
        # (定义一个名叫 `log` 的函数，专门用来在策略跑的时候打印一些信息，方便我们看过程。)
        return
        # 立即从log函数返回，此行为通常用于在开发或测试阶段临时禁用日志输出。
        # (这行代码会让日志功能立刻结束，啥也不打印。如果想看日志，需要把这行删掉或者在前面加个#号把它变成注释。)
        _data = data if data is not None else (
            self.datas[0] if self.datas else None)
        # 确定日志关联的数据源：如果提供了`data`参数则使用它，否则尝试使用策略的第一个数据源，如果策略没有数据源则为`None`。
        # (看看调用log的时候有没有指定是哪个股票的数据，有就用那个；没有的话，如果策略本身在处理股票数据，就用第一个；如果啥数据都没有，那就没办法了。)

        log_dt_str = ""
        # 初始化用于存储日志时间戳的字符串。
        # (准备一个空字符串，用来放日志的时间信息。)
        if _data and hasattr(_data, 'datetime') and hasattr(_data.datetime, 'date') and len(_data.datetime) > 0:
            # 如果存在有效的数据源`_data`且包含有效的日期时间信息。
            # (如果咱们有具体的股票数据，而且这个数据里面有时间信息，并且时间信息不是空的。)
            dt_val = _data.datetime.date(0)
            # 获取当前K线周期的日期。
            # (拿到当前这根K线的日期。)
            if isinstance(dt_val, (datetime.date, datetime.datetime)):
                # 如果日期是标准日期或日期时间对象。
                # (如果拿到的日期是正经的日期或者日期时间格式。)
                log_dt_str = dt_val.isoformat()
                # 将日期格式化为ISO标准格式字符串。
                # (就把日期变成 "年-月-日" 这种标准格式的文字。)
            elif isinstance(dt_val, float):
                # 如果日期是浮点数格式（Backtrader有时使用）。
                # (如果拿到的日期是个数字（backtrader有时候会这样）。)
                log_dt_str = bt.num2date(dt_val).date().isoformat()
                # 将浮点数日期转换为日期对象后再格式化为ISO标准格式字符串。
                # (就把这个数字转成日期，然后再变成标准格式的文字。)
            else:
                # 其他类型的日期值。
                # (如果是其他奇奇怪怪的格式。)
                log_dt_str = str(dt_val)
                # 直接转换为字符串。
                # (就直接把它变成文字。)

        elif dt:
            # 如果没有数据源信息但提供了`dt`参数（外部传入的日期时间）。
            # (如果没股票数据，但是外面传了时间进来。)
            log_dt_str = dt.isoformat() if isinstance(
                dt, (datetime.date, datetime.datetime)) else str(dt)
            # 如果`dt`是日期或日期时间对象，则格式化为ISO格式；否则，转换为字符串。
            # (如果传进来的是正经的日期时间，就变成标准格式；如果不是，就直接变成文字。)
        else:
            # 如果既无数据源信息也无外部传入的日期时间。
            # (如果既没股票数据，外面也没传时间。)
            log_dt_str = datetime.datetime.now().date().isoformat()
            # 使用当前系统日期并格式化为ISO标准格式。
            # (那就用电脑现在的日期，变成标准格式。)

        prefix = ""
        # 初始化日志信息的前缀字符串。
        # (准备一个空字符串，用来放日志的前缀，比如股票代码。)
        if _data and hasattr(_data, '_name') and _data._name:
            # 如果数据源`_data`存在且有名称（如股票代码）。
            # (如果咱们有具体的股票数据，而且这个数据有名字（比如股票代码），并且名字不是空的。)
            prefix = f"[{_data._name}] "
            # 设置前缀为"[数据源名称] "的格式。
            # (就把前缀设置成 "[股票代码] " 这种样子。)

        print(f"{log_dt_str} {prefix}{txt}")
        # 打印格式化的日志消息，包含时间戳、前缀和日志内容`txt`。
        # (把时间、前缀（股票代码）和要记录的内容 `txt` 一起打印出来。)

    def __init__(self):
        # 策略类的构造函数，在策略实例创建时执行初始化操作。
        # (这是策略刚被创建出来的时候要做的事情，初始化一些变量和指标。)
        self.closes = {d._name: d.close for d in self.datas}
        # 创建一个字典 `self.closes`，将每个数据源的名称映射到其收盘价序列。
        # (把每个股票的收盘价数据都存到 `self.closes` 这个本子里，用股票名字来区分。)
        self.opens = {d._name: d.open for d in self.datas}
        # 创建一个字典 `self.opens`，将每个数据源的名称映射到其开盘价序列。
        # (把每个股票的开盘价数据都存到 `self.opens` 这个本子里，用股票名字来区分。)
        self.highs = {d._name: d.high for d in self.datas}
        # 创建一个字典 `self.highs`，将每个数据源的名称映射到其最高价序列。
        # (把每个股票的最高价数据都存到 `self.highs` 这个本子里，用股票名字来区分。)
        self.lows = {d._name: d.low for d in self.datas}
        # 创建一个字典 `self.lows`，将每个数据源的名称映射到其最低价序列。
        # (把每个股票的最低价数据都存到 `self.lows` 这个本子里，用股票名字来区分。)
        self.volumes = {d._name: d.volume for d in self.datas}
        # 创建一个字典 `self.volumes`，将每个数据源的名称映射到其成交量序列。
        # (把每个股票的成交量数据都存到 `self.volumes` 这个本子里，用股票名字来区分。)

        self.emas_medium = {d._name: bt.indicators.EMA(
            d.close, period=self.params.ema_medium_period) for d in self.datas}
        # 为每个数据源计算中期EMA指标，并存储在 `self.emas_medium` 字典中。
        # (给每个股票都算一个中期EMA均线，算好了存到 `self.emas_medium` 本子里。)
        self.emas_long = {d._name: bt.indicators.EMA(
            d.close, period=self.params.ema_long_period) for d in self.datas}
        # 为每个数据源计算长期EMA指标，并存储在 `self.emas_long` 字典中。
        # (给每个股票都算一个长期EMA均线，算好了存到 `self.emas_long` 本子里。)
        self.adxs = {d._name: bt.indicators.ADX(
            d, period=self.params.adx_period) for d in self.datas}
        # 为每个数据源计算ADX指标，并存储在 `self.adxs` 字典中。
        # (给每个股票都算一个ADX指标，算好了存到 `self.adxs` 本子里。)
        self.atrs = {d._name: bt.indicators.ATR(
            d, period=self.params.atr_period) for d in self.datas}
        # 为每个数据源计算ATR（平均真实波幅）指标，并存储在 `self.atrs` 字典中。
        # (给每个股票都算一个ATR指标，这个指标能反映价格波动幅度，算好了也存到 `self.atrs` 本子里。)
        self.bbands = {d._name: bt.indicators.BollingerBands(
            d.close, period=self.params.bbands_period, devfactor=self.params.bbands_devfactor) for d in self.datas}
        # 为每个数据源计算布林带指标，并存储在 `self.bbands` 字典中。
        # (给每个股票都算一个布林带指标，算好了存到 `self.bbands` 本子里。)
        self.rsis = {d._name: bt.indicators.RSI(
            d.close, period=self.params.rsi_period) for d in self.datas}
        # 为每个数据源计算RSI指标，并存储在 `self.rsis` 字典中。
        # (给每个股票都算一个RSI指标，算好了存到 `self.rsis` 本子里。)
        self.highest_highs = {d._name: bt.indicators.Highest(
            d.high, period=self.params.trend_breakout_lookback) for d in self.datas}
        # 为每个数据源计算指定回顾期内的最高价，并存储在 `self.highest_highs` 字典中。
        # (给每个股票都算一个在过去一段时间里的最高价，算好了存到 `self.highest_highs` 本子里。)
        self.sma_volumes = {d._name: bt.indicators.SMA(
            d.volume, period=self.params.trend_volume_avg_period) for d in self.datas}
        # 为每个数据源计算成交量的简单移动平均线（SMA），并存储在 `self.sma_volumes` 字典中。
        # (给每个股票都算一个成交量的均线，算好了存到 `self.sma_volumes` 本子里。)

        self.orders = {d._name: None for d in self.datas}
        # 初始化一个字典 `self.orders`，用于存储每个数据源当前活动的订单对象，初始值均为None。
        # (准备一个叫 `self.orders` 的本子，用来记下给每个股票发的订单，一开始都是空的。)
        self.buy_prices = {d._name: None for d in self.datas}
        # 初始化一个字典 `self.buy_prices`，用于存储每个数据源的买入价格，初始值均为None。
        # (准备一个叫 `self.buy_prices` 的本子，用来记下每个股票的买入价，一开始都是空的。)
        self.position_types = {d._name: None for d in self.datas}
        # 初始化一个字典 `self.position_types`，用于存储每个数据源持仓的交易类型（如趋势型或区间型），初始值均为None。
        # (准备一个叫 `self.position_types` 的本子，用来记下买的每个股票是按什么类型（比如趋势型、区间型）买的，一开始都是空的。)

        self.high_water_mark = self.broker.startingcash
        # 初始化账户历史最高价值（高水位标记）为初始资金。
        # (记一下账户里钱最多的时候是多少，一开始就是本金。)
        self.drawdown_level1_triggered = False
        # 初始化一级回撤警报触发状态为False。
        # (设置一个标记，表示一级回撤警报响了没，一开始是没响。)
        self.halt_trading = False
        # 初始化暂停交易状态为False。
        # (设置一个开关，表示要不要暂停交易，一开始是不暂停。)
        self.current_risk_multiplier = 1.0
        # 初始化当前风险乘数为1.0，用于根据账户回撤情况调整交易风险。
        # (设置一个风险调整系数，初始是1.0，后面会根据账户亏损情况调整，比如亏多了就调小一点，少买点。)

        self.pending_trade_info = {}
        # 初始化一个空字典 `self.pending_trade_info`，用于在下单前临时存储待Sizer处理的交易风险信息。
        # (创建一个叫 `self.pending_trade_info` 的空本子，用来在下单前临时存放交易计划信息，Sizer会从这里读取。)

    def notify_order(self, order):
        # 当订单状态发生变化时，Backtrader会自动调用此方法。
        # (定义一个名叫 `notify_order` 的函数，每当订单有新情况时，`backtrader` 就会来告诉这个函数。)
        order_data_name = order.data._name if hasattr(
            order.data, '_name') else 'Unknown_Data'
        # 获取订单关联的数据源名称；如果无法获取，则标记为'Unknown_Data'。
        # (看看这个订单是哪个股票的，如果找不到名字就叫 'Unknown_Data'。)

        if order.status in [order.Submitted, order.Accepted]:
            # 如果订单状态为已提交（Submitted）或已接受（Accepted）。
            # (如果订单已经发出去了或者交易所已经收到了。)
            self.log(
                f'订单 {order.ref} 已提交/接受 for {order_data_name}', data=order.data)
            # 记录订单已提交或已接受的日志。
            # (就记个日志说一下这个订单发出去了或者被接受了。)
            if order.parent is None:
                # 如果是主订单（非括号单的止损或止盈部分）。
                # (如果这个订单不是某个大订单里的小订单（是主订单）。)
                self.orders[order_data_name] = order
                # 将此主订单存储在对应数据源的 `self.orders` 字典中以供跟踪。
                # (就把这个订单记在对应股票的 `self.orders` 本子里。)
            return
            # 对于已提交或已接受状态，处理完毕，直接返回。
            # (这事儿处理完了，不用往下看了。)

        if order_data_name in self.pending_trade_info:
            # 检查此订单对应的数据源是否存在待处理的交易信息。
            # (看看这个ETF之前是不是有还没处理完的交易计划。)
            if not order.alive():
                # 如果订单不再存活（例如已完成、取消、拒绝等）。
                # (如果这个订单已经结束了，不管是成功了、取消了还是被拒绝了。)
                self.log(
                    f'订单 {order.ref} 结束，清理 {order_data_name} 的 pending_trade_info', data=order.data)
                # 记录订单结束并清理相关待处理信息的日志。
                # (记个日志说订单结束了，把对应的交易计划清理掉。)
                del self.pending_trade_info[order_data_name]
                # 从 `pending_trade_info` 中删除该数据源的待处理信息。
                # (从 `pending_trade_info` 本子里删掉这个ETF的计划。)
            elif order.status in [order.Margin, order.Rejected]:
                # 如果订单因保证金不足（Margin）或被拒绝（Rejected）而失败。
                # (如果订单因为钱不够或者被交易所拒绝了而失败了。)
                self.log(
                    f'订单 {order.ref} 失败 ({order.getstatusname()}), 清理 {order_data_name} 的 pending_trade_info', data=order.data)
                # 记录订单失败并清理相关待处理信息的日志。
                # (记个日志说订单失败了，清理对应的交易计划。)
                del self.pending_trade_info[order_data_name]
                # 从 `pending_trade_info` 中删除该数据源的待处理信息。
                # (从 `pending_trade_info` 本子里删掉这个ETF的计划。)

        if order.status in [order.Completed]:
            # 如果订单状态为已完成（Completed）。
            # (如果订单已经成功交易了。)
            if order.isbuy():
                # 如果是买入订单。
                # (如果这是一个买单。)
                self.log(
                    f'买入执行 for {order_data_name} @ {order.executed.price:.2f}, 数量: {order.executed.size}, 成本: {order.executed.value:.2f}, 佣金: {order.executed.comm:.2f}', data=order.data)
                # 记录买入执行的详细信息（价格、数量、成本、佣金）。
                # (就记个日志说买入成功了，买了多少，花了多少钱，手续费多少。)
                self.buy_prices[order_data_name] = order.executed.price
                # 将成交价格存储在 `self.buy_prices` 字典中。
                # (把买入的价格记下来。)
            elif order.issell():
                # 如果是卖出订单。
                # (如果这是一个卖单。)
                self.log(
                    f'卖出执行 for {order_data_name} @ {order.executed.price:.2f}, 数量: {order.executed.size}, 价值: {order.executed.value:.2f}, 佣金: {order.executed.comm:.2f}', data=order.data)
                # 记录卖出执行的详细信息（价格、数量、价值、佣金）。
                # (就记个日志说卖出成功了，卖了多少，收回多少钱，手续费多少。)

        elif order.status in [order.Canceled, order.Margin, order.Rejected, order.Expired]:
            # 如果订单状态为已取消（Canceled）、保证金不足（Margin）、被拒绝（Rejected）或已过期（Expired）。
            # (如果订单被取消了、或者因为钱不够、或者被交易所拒绝了、或者过期了。)
            self.log(
                f'订单 {order.ref} for {order_data_name} 取消/保证金/拒绝/过期: 状态 {order.getstatusname()}', data=order.data)
            # 记录订单未能成功执行的原因。
            # (就记个日志说这个订单没成功，具体是什么原因。)

        if self.orders.get(order_data_name) == order and not order.alive():
            # 如果 `self.orders` 中存储的是当前订单，并且当前订单不再存活。
            # (如果之前记在 `self.orders` 本子里的这个股票的订单就是现在这个订单，并且这个订单已经结束了。)
            self.orders[order_data_name] = None
            # 将 `self.orders` 中对应数据源的记录清除（重置为None）。
            # (就把 `self.orders` 本子里对应这个股票的记录清空，表示现在没有正在处理的订单了。)

    def notify_trade(self, trade):
        # 当一笔交易（买入和卖出构成一个完整周期）关闭时，Backtrader会自动调用此方法。
        # (定义一个名叫 `notify_trade` 的函数，当一买一卖完整结束形成一笔交易后，`backtrader` 就会来告诉这个函数。)
        if not trade.isclosed:
            # 如果交易尚未关闭（即只有开仓，没有平仓）。
            # (如果这笔交易还没结束，比如只买了还没卖。)
            return
            # 则不处理，直接返回。
            # (那就先不管它，等卖了再说。)
        data_name = trade.data._name if hasattr(
            trade.data, '_name') else 'Unknown_Data'
        # 获取交易关联的数据源名称。
        # (看看这笔交易是哪个股票的。)
        self.log(
            f'交易利润 for {data_name}, 毛利 {trade.pnl:.2f}, 净利 {trade.pnlcomm:.2f}, 持仓类型: {self.position_types.get(data_name, "N/A")}', data=trade.data)
        # 记录交易的盈利情况（毛利润pnl和净利润pnlcomm）以及该持仓的原始交易类型。
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
        # 当账户现金或总价值发生变化时，Backtrader会自动调用此方法。
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
                    f'!!! 红色警报: 回撤 {drawdown*100:.2f}% > {self.params.drawdown_level2_threshold*100:.0f}%. 暂停交易 !!!')
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
                    f'-- 黄色警报: 回撤 {drawdown*100:.2f}% > {self.params.drawdown_level1_threshold*100:.0f}%. 降低风险.--')
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
                # 如果之前是暂停交易状态（意味着回撤曾超过二级阈值）。
                # (如果之前是暂停交易的状态。)
                self.log('--- 交易恢复 (回撤低于二级) ---')
                # 记录日志，说明交易已恢复 (因为回撤已低于二级阈值)。
                # (记个日志说交易恢复了，因为亏损已经回到二级线以下了。)
                self.halt_trading = False
                # 将 `halt_trading` 标志设置回 `False`。
                # (把暂停交易的开关关掉。)
                if drawdown <= self.params.drawdown_level1_threshold:
                    # 如果回撤同时也低于一级回撤阈值。
                    # (如果亏损也回到了一级线以下。)
                    if self.drawdown_level1_triggered:
                        # 并且之前一级警报曾被触发过。
                        # (如果之前一级警报响过。)
                        self.log(
                            '--- 风险水平恢复 (回撤低于一级) ---')
                        # 记录日志，说明风险水平已恢复正常。
                        # (记个日志说风险水平恢复正常了。)
                        self.drawdown_level1_triggered = False
                        # 重置一级回撤触发标志。
                        # (把一级警报的标记关掉。)
                        self.current_risk_multiplier = 1.0
                        # 将风险乘数恢复到1.0。
                        # (把风险调整系数恢复到1.0。)
                elif self.drawdown_level1_triggered:
                    # 如果交易已恢复（说明回撤低于二级），但回撤仍高于一级，且一级警报曾触发。
                    # (如果亏损在一级线和二级线之间，但交易已经恢复了（说明之前是暂停交易状态），并且一级警报之前响过。)
                    self.current_risk_multiplier = 0.5
                    # 风险乘数保持在0.5（较低风险水平）。
                    # (风险调整系数还是保持0.5。)

            elif self.drawdown_level1_triggered and drawdown <= self.params.drawdown_level1_threshold:
                # 如果之前一级回撤警报被触发过，且当前回撤已低于一级阈值 (并且之前未暂停交易)。
                # (如果之前一级警报响过，现在亏损回到一级线以下了，并且之前没有暂停交易。)
                self.log('--- 风险水平恢复 (回撤低于一级) ---')
                # 记录日志，说明风险水平已恢复正常。
                # (记个日志说风险水平恢复正常了。)
                self.drawdown_level1_triggered = False
                # 重置一级回撤触发标志。
                # (把一级警报的标记关掉。)
                self.current_risk_multiplier = 1.0
                # 将风险乘数恢复到1.0。
                # (把风险调整系数恢复到1.0。)

    def next(self):
        # 每个新的K线数据到达时，Backtrader会自动调用此方法来执行策略的主要逻辑。
        # (定义一个名叫 `next` 的函数，每当有新的一根K线数据来了，`backtrader` 就会运行一次这个函数，策略的主要逻辑在这里。)
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
                        # 将新创建的平仓订单存储在 `self.orders` 字典中，以便跟踪。
                        # (就把这个卖单记在 `self.orders` 本子里，方便以后查看订单状态。)
                    else:
                        # 如果未能创建平仓订单。
                        # (如果卖出指令没发出去。)
                        self.log(
                            f'暂停中: 无法为 {d_name} 创建平仓订单', data=d_obj)
                        # 记录日志，说明平仓失败。
                        # (记个日志说卖单没发出去。)
            return
            # 在暂停交易状态下，执行完必要的平仓操作后，不进行新的开仓检查，直接返回。
            # (暂停交易状态下，除了平仓，其他啥也不干了，到此为止。)

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

            if order or position.size != 0 or d_name in self.pending_trade_info:
                # 如果当前数据源存在活动订单，或已有持仓，或已有待Sizer处理的交易信息，则跳过此数据源。
                # (如果这只ETF有正在处理的订单，或者已经持有仓位了，或者已经有交易计划在Sizer那边等着处理，那就先跳过这只，看看下一只。)
                continue
                # 继续处理下一个数据源。
                # (那就先不看它了，等处理完了再说。)

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
            # 获取中期EMA的前一个周期的值。
            # (拿到这只ETF的中期均线上一个周期的值。)
            ema_long_val = self.emas_long[d_name][0]
            # 获取长期EMA的当前值。
            # (拿到这只ETF的长期均线现在的值。)
            ema_long_prev = self.emas_long[d_name][-1]
            # 获取长期EMA的前一个周期的值。
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
            # 获取前一周期内N日（由trend_breakout_lookback参数定义）最高价的值。
            # (拿到这只ETF在之前一段时间里的最高价。)
            sma_volume_val = self.sma_volumes[d_name][0]
            # 获取成交量SMA（简单移动平均）的当前值。
            # (拿到这只ETF的成交量均线现在的值。)
            atr_val = self.atrs[d_name][0]
            # 获取当前ATR（平均真实波幅）的值。
            # (拿到这只ETF的ATR指标现在的值，这个指标通常用来衡量价格波动幅度。)

            try:
                # 尝试执行以下可能因数据不足（例如回测初期）而引发 `IndexError` 的代码。
                # (试试看下面的判断，如果数据不够（比如刚开始回测没几天），可能会出错。)
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
                # 判断是否为区间震荡：非上升趋势，中期和长期EMA变化平缓（变化率小于0.3%），ADX < 20，且布林带宽度占收盘价比例小于7%。
                # (判断是不是区间震荡：首先不能是上升趋势，然后两条均线变化不大（几乎是平的，变化幅度小于0.3%），ADX指标小于20（表示趋势不强），并且布林带的上下轨之间的宽度相对于价格来说比较窄（小于价格的7%）。)

                if is_trend_up:
                    # 如果判断为上升趋势。
                    # (如果是上升趋势。)
                    market_state = 'TREND_UP'
                    # 将市场状态设置为 'TREND_UP'。
                    # (就把市场状态改成 'TREND_UP'。)
                elif is_range_confirmed and self.p.etf_type == 'range':
                    # 如果判断为区间震荡，并且策略参数 `etf_type` 设置为 'range'。
                    # (如果是区间震荡，并且咱们策略设置的是针对 'range' 区间型的ETF。)
                    market_state = 'RANGE_CONFIRMED'
                    # 将市场状态设置为 'RANGE_CONFIRMED'。
                    # (就把市场状态改成 'RANGE_CONFIRMED'。)
            except IndexError:
                # 如果在访问指标历史数据时发生 `IndexError` (通常在回测初期数据不足时)。
                # (如果因为数据不够，上面的判断出错了。)
                continue
                # 跳过当前循环的剩余部分，处理下一个数据点或数据源。
                # (那就先不处理这个ETF了，看看下一个。)

            entry_signal = False
            # 初始化入场信号为 `False`。
            # (先假设没有买入信号。)
            potential_position_type = None
            # 初始化潜在持仓类型为 `None`。
            # (先假设不知道要按什么类型买。)
            entry_price_calc = None
            # 初始化计算得出的参考入场价格为None。
            # (先假设不知道计划买入价是多少。)
            stop_loss_price_calc = None
            # 初始化计算得出的止损价格为None。
            # (先假设不知道止损价是多少。)
            take_profit_price_calc = None
            # 初始化计算得出的止盈价格为None。
            # (先假设不知道止盈价是多少。)
            risk_per_share = None
            # 初始化计算得出的每股风险为None。
            # (先假设不知道每股亏多少钱。)
            amount_to_risk = None
            # 初始化本次交易允许承担的总风险金额为None。
            # (先假设不知道这次交易最多能亏多少钱。)

            if market_state == 'TREND_UP' and self.p.etf_type == 'trend':
                # 如果市场状态为上升趋势，并且策略参数 `etf_type` 设置为 'trend'。
                # (如果市场是上升趋势，并且咱们策略设置的是针对 'trend' 趋势型的ETF。)
                try:
                    # 尝试执行趋势交易的信号判断和风险计算。
                    # (试试看趋势交易的买入条件。)
                    is_breakout = (current_close > highest_high_prev and
                                   current_volume > sma_volume_val * self.params.trend_volume_ratio_min)
                    # 判断是否为突破信号：当前收盘价创近期新高，并且成交量显著放大（大于均量的特定倍数）。
                    # (判断是不是突破了：现在的价格比之前一段时间的最高价还高，并且成交量也比平均成交量大不少。)
                    is_pullback = (min(abs(current_low / ema_medium_val - 1), abs(current_low / ema_long_val - 1)) < 0.01 and
                                   current_close > current_open) if ema_medium_val > 1e-9 and ema_long_val > 1e-9 else False
                    # 判断是否为回调信号：当前最低价接近中期或长期EMA (回调到均线附近，差异小于1%)，并且当天收阳线（收盘价大于开盘价）。
                    # (判断是不是回调买入机会：价格跌到中期均线或者长期均线附近了（距离均线不到1%），并且当天是涨的（收盘价比开盘价高）。)

                    if is_breakout or is_pullback:
                        # 如果出现突破信号或回调信号。
                        # (如果判断是突破了，或者是回调到均线的好机会。)
                        entry_signal = True
                        # 设置入场信号为 `True`。
                        # (那就认为有买入信号了。)
                        potential_position_type = 'trend'
                        # 设置潜在持仓类型为 'trend'。
                        # (这次买入是按趋势型来操作的。)
                        entry_price_calc = current_close
                        # 将当前收盘价作为计算时的参考入场价格。
                        # (先用现在的收盘价作为计划买入的价格。)

                        if math.isnan(atr_val) or atr_val <= 1e-9:
                            # 如果ATR值无效（NaN或过小）。
                            # (如果ATR的值不正常，比如是算不出来或者是0。)
                            self.log(
                                f"{d_name} ATR值无效 ({atr_val:.4f})，无法计算趋势止损。跳过。", data=d_obj)
                            # 记录ATR无效导致无法计算止损的日志。
                            # (记个日志说ATR值有问题，没法算止损，这次就不买了。)
                            entry_signal = False
                            # 取消入场信号。
                            # (那就不买了。)
                        else:
                            stop_loss_price_calc = entry_price_calc - \
                                self.p.trend_stop_loss_atr_mult * atr_val
                            # 根据ATR计算止损价格：参考入场价 - ATR倍数 * ATR值。
                            # (用计划买入价减去ATR乘以一个倍数，来算出止损价。)

                            if stop_loss_price_calc >= entry_price_calc:
                                # 如果计算出的止损价不低于参考入场价（无效止损）。
                                # (如果算出来的止损价比计划买入价还要高或者一样，说明这个止损设置有问题。)
                                self.log(
                                    f"{d_name} 趋势止损价 {stop_loss_price_calc:.2f} 不低于入场价 {entry_price_calc:.2f}。跳过。", data=d_obj)
                                # 记录无效止损的日志。
                                # (记个日志说止损价不合理，这次不买了。)
                                entry_signal = False
                                # 取消入场信号。
                                # (那就不买了。)
                            else:
                                risk_per_share = entry_price_calc - stop_loss_price_calc
                                # 计算每股风险：参考入场价 - 止损价。
                                # (算一下如果买一股，到了止损价会亏多少钱。)
                                if risk_per_share <= 1e-9:
                                    # 如果每股风险过小（接近或等于0）。
                                    # (如果算出来每股风险特别小，几乎不亏钱，这可能也有问题。)
                                    self.log(
                                        f"{d_name} 趋势交易每股风险过小 ({risk_per_share:.2f})。跳过。", data=d_obj)
                                    # 记录每股风险过小的日志。
                                    # (记个日志说每股风险太小了，不合理，这次不买了。)
                                    entry_signal = False
                                    # 取消入场信号。
                                    # (那就不买了。)
                                else:
                                    take_profit_price_calc = entry_price_calc + \
                                        self.p.trend_take_profit_rratio * risk_per_share
                                    # 计算止盈价格：参考入场价 + 风险回报比 * 每股风险。
                                    # (用计划买入价加上每股风险乘以一个倍数（风险回报比），来算出止盈价。)
                                    risk_per_trade_percent = self.p.risk_per_trade_trend
                                    # 从策略参数中获取趋势交易的单笔风险百分比。
                                    # (从咱们策略的设置里，找出趋势交易时，每一笔最多允许亏损多少钱（占总资产的百分比）。)
                                    effective_risk_percent = risk_per_trade_percent * self.current_risk_multiplier
                                    # 计算实际生效的单笔风险百分比（考虑当前风险乘数）。
                                    # (用上面那个百分比，再乘以当前的风险调整系数，得到这次交易实际能亏的钱的百分比。)
                                    amount_to_risk = self.broker.getvalue() * effective_risk_percent
                                    # 计算本次交易允许承担的总风险金额。
                                    # (用账户总钱数乘以实际能亏的百分比，得到这次交易最多能亏多少钱。)
                except IndexError:
                    # 如果在访问指标历史数据时发生 `IndexError`。
                    # (如果因为数据不够出错了。)
                    continue
                    # 跳过当前循环的剩余部分。
                    # (那就先不处理这个ETF了，看看下一个。)

            elif market_state == 'RANGE_CONFIRMED' and self.p.etf_type == 'range':
                # 如果市场状态为区间震荡，并且策略参数 `etf_type` 设置为 'range'。
                # (如果市场是区间震荡，并且咱们策略设置的是针对 'range' 区间型的ETF。)
                try:
                    # 尝试执行区间交易的信号判断和风险计算。
                    # (试试看区间交易的买入条件。)
                    is_range_buy = (current_low <= bb_bot and
                                    current_close > bb_bot and
                                    rsi_val < self.params.rsi_oversold)
                    # 判断是否为区间买入信号：最低价触及或跌破布林带下轨，收盘价回到下轨之上，且RSI处于超卖区。
                    # (判断是不是区间买入机会：价格碰到或者跌破布林带下轨了，然后收盘的时候又回到下轨上面，并且RSI指标显示超卖了。)
                    if is_range_buy:
                        # 如果出现区间买入信号。
                        # (如果判断是区间买入的好机会。)
                        entry_signal = True
                        # 设置入场信号为 `True`。
                        # (那就认为有买入信号了。)
                        potential_position_type = 'range'
                        # 设置潜在持仓类型为 'range'。
                        # (这次买入是按区间型来操作的。)
                        entry_price_calc = current_close
                        # 将当前收盘价作为计算时的参考入场价格。
                        # (先用现在的收盘价作为计划买入的价格。)
                        stop_loss_price_calc = current_low * \
                            (1 - self.p.range_stop_loss_buffer)
                        # 计算止损价格：当前最低价 * (1 - 区间止损缓冲百分比)。
                        # (用当前这根K线的最低价再往下跌一点点（由缓冲百分比决定）作为止损价。)

                        if stop_loss_price_calc >= entry_price_calc:
                            # 如果计算出的止损价不低于参考入场价（无效止损）。
                            # (如果算出来的止损价比计划买入价还要高或者一样，说明这个止损设置有问题。)
                            self.log(
                                f"{d_name} 区间止损价 {stop_loss_price_calc:.2f} 不低于入场价 {entry_price_calc:.2f}。跳过。", data=d_obj)
                            # 记录无效止损的日志。
                            # (记个日志说止损价不合理，这次不买了。)
                            entry_signal = False
                            # 取消入场信号。
                            # (那就不买了。)
                        else:
                            risk_per_share = entry_price_calc - stop_loss_price_calc
                            # 计算每股风险：参考入场价 - 止损价。
                            # (算一下如果买一股，到了止损价会亏多少钱。)
                            if risk_per_share <= 1e-9:
                                # 如果每股风险过小（接近或等于0）。
                                # (如果算出来每股风险特别小，几乎不亏钱，这可能也有问题。)
                                self.log(
                                    f"{d_name} 区间交易每股风险过小 ({risk_per_share:.2f})。跳过。", data=d_obj)
                                # 记录每股风险过小的日志。
                                # (记个日志说每股风险太小了，不合理，这次不买了。)
                                entry_signal = False
                                # 取消入场信号。
                                # (那就不买了。)
                            else:
                                take_profit_price_calc = bb_mid
                                # 设置止盈价格为布林带中轨。
                                # (区间交易的止盈目标一般是布林带的中轨。)
                                risk_per_trade_percent = self.p.risk_per_trade_range
                                # 从策略参数中获取区间交易的单笔风险百分比。
                                # (从咱们策略的设置里，找出区间交易时，每一笔最多允许亏损多少钱（占总资产的百分比）。)
                                effective_risk_percent = risk_per_trade_percent * self.current_risk_multiplier
                                # 计算实际生效的单笔风险百分比（考虑当前风险乘数）。
                                # (用上面那个百分比，再乘以当前的风险调整系数，得到这次交易实际能亏的钱的百分比。)
                                amount_to_risk = self.broker.getvalue() * effective_risk_percent
                                # 计算本次交易允许承担的总风险金额。
                                # (用账户总钱数乘以实际能亏的百分比，得到这次交易最多能亏多少钱。)
                except IndexError:
                    # 如果在访问指标历史数据时发生 `IndexError`。
                    # (如果因为数据不够出错了。)
                    continue
                    # 跳过当前循环的剩余部分。
                    # (那就先不处理这个ETF了，看看下一个。)

            if entry_signal and entry_price_calc is not None and \
               stop_loss_price_calc is not None and risk_per_share is not None and \
               amount_to_risk is not None and entry_price_calc > stop_loss_price_calc:
                # 如果有有效入场信号，并且所有必要的风险参数（入场价、止损价、每股风险、总风险额）都已计算完毕，且入场价高于止损价。
                # (如果前面判断出来有买入信号，并且买入价、止损价、每股风险、总风险金额这些都算好了，而且买入价比止损价高。)
                if risk_per_share <= 1e-9 or amount_to_risk <= 1e-9:
                    # 如果计算出的每股风险或总风险金额过小（无效）。
                    # (如果算出来的每股风险或者总风险金额太小了，不合理。)
                    self.log(
                        f"信号产生但风险计算无效 for {d_name} (Risk/Share: {risk_per_share:.4f}, AmountToRisk: {amount_to_risk:.2f})。跳过。", data=d_obj)
                    # 记录风险计算无效的日志。
                    # (记个日志说虽然有信号，但是风险算出来不对，这次不买了。)
                    continue
                    # 跳过此信号。
                    # (那就跳过这次交易。)

                self.pending_trade_info[d_name] = {
                    'entry_price': entry_price_calc,
                    'stop_loss_price': stop_loss_price_calc,
                    'risk_per_share': risk_per_share,
                    'amount_to_risk': amount_to_risk
                }
                # 将计算好的交易风险信息（参考入场价、止损价、每股风险、总风险额）存入 `pending_trade_info` 字典，供Sizer后续读取计算头寸。
                # (把算好的买入价、止损价、每股风险、总风险金额都打包存到 `pending_trade_info` 本子里，用ETF名字做标签，这样Sizer就能拿到这些信息去算买多少股。)
                self.log(
                    f"为 {d_name} 准备交易信息: 入场={entry_price_calc:.2f}, 止损={stop_loss_price_calc:.2f}, 风险/股={risk_per_share:.4f}, 允许风险额={amount_to_risk:.2f}", data=d_obj)
                # 记录已准备好交易信息的日志。
                # (记个日志说交易计划准备好了，具体参数是多少。)

                main_order_limit_price = entry_price_calc
                # 将计算得出的参考入场价作为主订单的限价。
                # (用之前算好的参考入场价，作为这次买入的限价，意思是希望以这个价格或更优价格成交。)
                tp_price_for_bracket = None
                # 初始化括号单的止盈价格为None。
                # (先假设不知道括号单的止盈价是多少。)
                if take_profit_price_calc is not None and take_profit_price_calc > main_order_limit_price:
                    # 如果已计算止盈价且该价格高于主订单限价（有效止盈）。
                    # (如果算出来了止盈价，并且这个止盈价比我们的买入限价要高。)
                    tp_price_for_bracket = take_profit_price_calc
                    # 使用计算出的止盈价作为括号单的止盈限价。
                    # (那就用这个算出来的止盈价。)
                elif potential_position_type == 'trend' and take_profit_price_calc is not None:
                    # 如果是趋势交易，已计算止盈价但无效（例如不高于入场价）。
                    # (如果是趋势交易，虽然算了个止盈价，但是这个止盈价不比买入价高，说明有问题。)
                    self.log(
                        f"警告 for {d_name}: 趋势交易止盈价 {take_profit_price_calc:.2f} 无效 (不高于入场价 {main_order_limit_price:.2f})。括号单将无止盈限价单。", data=d_obj)
                    # 记录趋势交易止盈价无效的警告，此时括号单将不设置止盈限价单。
                    # (记个警告说趋势交易的止盈价有问题，这次括号单就不设止盈了。)

                self.log(
                    f"发出买入括号单信号 for {d_name}, 参考入场: {main_order_limit_price:.2f}, 止损: {stop_loss_price_calc:.2f}, 止盈: {tp_price_for_bracket if tp_price_for_bracket else 'N/A'}", data=d_obj)
                # 记录发出买入括号单信号的日志，包含主要参数。
                # (记个日志说我们要下一个买入的括号单了，把计划的买入价、止损价、止盈价都写上。)
                bracket_orders_list = self.buy_bracket(
                    data=d_obj,
                    # 指定订单关联的数据源对象。
                    # (告诉系统这个订单是针对哪个ETF的。)
                    price=main_order_limit_price,
                    # 设置主买入订单的限价。
                    # (告诉系统我们希望以不高于这个价格买入。)
                    exectype=bt.Order.Limit,
                    # 设置主订单的执行类型为限价单（Limit Order）。
                    # (下单类型是限价单，就是指定一个价格买。)
                    stopprice=stop_loss_price_calc,
                    # 设置止损订单的触发价格（由策略计算）。
                    # (设置好止损单的触发价格，这个是前面算好的。)
                    limitprice=tp_price_for_bracket,
                    # 设置止盈订单的限价（由策略计算，可能为None）。
                    # (设置好止盈单的限价，这个也是前面算好的，如果没有就算了。)
                )

                if bracket_orders_list and bracket_orders_list[0]:
                    # 如果成功创建了括号订单列表，并且列表中的第一个订单 (主买入订单) 存在。
                    # (如果括号单成功发出去了，并且主买单也创建好了。)
                    self.position_types[d_name] = potential_position_type
                    # 记录该持仓的交易类型。
                    # (把这次买入是按什么类型（趋势型还是区间型）操作的记录下来。)
                    self.log(
                        f"成功为 {d_name} 创建 buy_bracket 请求。主订单 ref: {bracket_orders_list[0].ref if bracket_orders_list[0] else 'N/A'}", data=d_obj)
                    # 记录成功创建buy_bracket请求的日志，并显示主订单的引用号。
                    # (记个日志说买入括号单的请求成功发出去了，主订单的编号是多少。)
                else:
                    # 如果未能成功创建括号订单 (例如Sizer返回0股导致订单未创建，或发生其他错误)。
                    # (如果括号单没发出去（比如Sizer算出来买0股，或者其他错误）。)
                    self.log(
                        f"为 {d_name} 创建 buy_bracket 失败 (可能Sizer返回0或错误)", data=d_obj)
                    # 记录创建buy_bracket失败的日志。
                    # (记个日志说买入括号单失败了，可能是Sizer那边算出来不让买，或者有其他问题。)
                    if d_name in self.pending_trade_info:
                        # 如果下单失败，且之前已存储了待处理交易信息。
                        # (如果下单失败了，而且之前在 `pending_trade_info` 里存了这个ETF的计划。)
                        del self.pending_trade_info[d_name]
                        # 清理该数据源的待处理交易信息。
                        # (那就把之前存在 `pending_trade_info` 里的这个ETF的交易计划删掉。)

def load_data_to_cerebro(cerebro, data_files, column_mapping, openinterest_col, fromdate, todate):
    """
    加载Excel数据文件到Cerebro引擎中。
    Loads Excel data files into the Cerebro engine.

    Args:
        cerebro (bt.Cerebro): Cerebro引擎实例。 (Cerebro engine instance.)
        data_files (list): 包含Excel文件路径的列表。 (List containing Excel file paths.)
        column_mapping (dict): 列名映射字典。 (Dictionary for column name mapping.)
        openinterest_col (int or str): 持仓量列索引或名称 (-1或None表示无)。 (Open interest column index or name (-1 or None for none).)
        fromdate (datetime.datetime): 回测起始日期。 (Backtest start date.)
        todate (datetime.datetime): 回测结束日期。 (Backtest end date.)

    Returns:
        int: 成功加载的数据源数量。 (Number of successfully loaded data feeds.)
    """
    print("开始加载数据...")
    # 打印提示信息，表示数据加载过程开始
    # (告诉用户，现在要开始往回测系统里装数据了)
    loaded_data_count = 0
    # 初始化成功加载的数据文件计数器为0
    # (准备一个计数器，记一下成功装了多少个数据文件)
    for file_path in data_files:
        # 遍历数据文件路径列表中的每个文件路径
        # (一个一个地处理咱们给定的数据文件列表)
        try:
            # 开始尝试处理单个数据文件，包含错误捕获机制
            # (试试看能不能把这个文件的数据读进来并处理好，如果中间出错了，就跳到except那里)
            dataframe = pd.read_excel(file_path)
            # 使用pandas库的read_excel函数读取指定路径的Excel文件内容到DataFrame中
            # (用pandas这个工具把Excel表格里的数据读出来，变成一个叫DataFrame的表格对象)
            dataframe.rename(columns=column_mapping, inplace=True)
            # 根据提供的列名映射字典column_mapping，重命名DataFrame的列名，并直接修改原DataFrame
            # (把Excel里原来的列标题，按照咱们设定的对应关系，改成回测系统能认得的列标题，比如把“日期”改成“datetime”)
            if 'datetime' in dataframe.columns:
                # 检查重命名后的DataFrame列中是否存在名为'datetime'的列
                # (看看表格里有没有一个叫“datetime”的列，这个是时间序列数据必须的)
                try:
                    # 尝试将'datetime'列的数据转换为pandas的datetime对象格式
                    # (试试把“datetime”这一列的文本内容，都转成标准的时间日期格式)
                    dataframe['datetime'] = pd.to_datetime(
                        dataframe['datetime'])
                    # 将'datetime'列的数据转换为pandas的datetime对象格式
                    # (把“datetime”列里的每个日期字符串，都变成程序能理解的日期时间)
                except Exception as e:
                    # 如果在转换日期时间格式时发生任何异常
                    # (如果转换日期的时候出错了，比如日期格式不对)
                    print(f"警告: 无法解析 {file_path} 中的日期时间列，请检查格式。错误: {e}")
                    # 打印警告信息，指出哪个文件的日期时间列无法解析，并显示错误详情
                    # (就告诉用户，这个文件的日期有问题，让他检查一下，顺便把具体的错误原因也打出来)
                    continue
                    # 跳过当前文件的后续处理，继续处理下一个文件
                    # (这个文件日期有问题，就不处理它了，直接去看下一个文件)
            else:
                # 如果重命名后的DataFrame列中不存在名为'datetime'的列
                # (如果改完列名之后，还是找不到“datetime”这一列)
                print(
                    f"错误: 在 {file_path} 中找不到映射后的 'datetime' 列。请确保Excel文件中有正确的日期列，或正确修改脚本中的column_mapping。")
                # 打印错误信息，指出在哪个文件中找不到'datetime'列，并提示用户检查文件或映射配置
                # (就报错，告诉用户这个文件里没有日期列，让他检查一下Excel文件或者改列名的设置对不对)
                print(f"Excel文件中的原始列名是: {dataframe.columns.tolist()}")
                # 打印该Excel文件原始的列名列表，帮助用户排查问题
                # (把这个Excel文件里原来的列标题都打出来，方便用户对照检查)
                continue
                # 跳过当前文件的后续处理，继续处理下一个文件
                # (这个文件缺了关键的日期列，处理不了，去看下一个文件)
            dataframe.set_index('datetime', inplace=True)
            # 将'datetime'列设置为DataFrame的索引，并直接修改原DataFrame
            # (把“datetime”这一列作为表格的行标签，这样每一行数据就都对应一个具体的时间点了)
            required_cols = ['open', 'high', 'low', 'close', 'volume']
            # 定义一个列表，包含backtrader进行回测所必需的标准列名：开盘价、最高价、最低价、收盘价、成交量
            # (规定好，一个合格的K线数据，至少要有开盘价、最高价、最低价、收盘价和成交量这几项)
            if not all(col in dataframe.columns for col in required_cols):
                # 检查DataFrame的列中是否包含了所有必需的列
                # (看看咱们的表格数据里，是不是把上面说的这几项都凑齐了)
                print(f"错误: {file_path} 映射后缺少必需的列。")
                # 如果缺少必需列，则打印错误信息，指出哪个文件缺少列
                # (如果没凑齐，就报错，告诉用户这个文件缺东西了)
                print(f"可用的列: {dataframe.columns.tolist()}")
                # 打印当前文件中实际存在的列名列表
                # (把这个文件里实际有的列标题打出来，让用户看看缺了啥)
                continue
                # 跳过当前文件的后续处理，继续处理下一个文件
                # (这个文件数据不全，没法用，去看下一个文件)
            dataframe = dataframe.loc[fromdate:todate]
            # 根据提供的起始日期fromdate和结束日期todate，筛选DataFrame中符合日期范围的数据行
            # (从表格数据里，只挑出咱们指定的回测开始日期到结束日期之间的数据)

            if dataframe.empty:
                # 检查筛选后的DataFrame是否为空
                # (看看挑出来的数据是不是空的，可能指定日期范围里根本没数据)
                print(f"警告: {file_path} 在指定日期范围内没有数据。")
                # 如果为空，打印警告信息，指出哪个文件在指定日期范围内无数据
                # (如果是空的，就提醒一下用户，这个文件在这个时间段里没数据)
                continue
                # 跳过当前文件的后续处理，继续处理下一个文件
                # (既然没数据，就不用管这个文件了，去看下一个)

            oi_param_val = -1
            # 初始化持仓量参数值为-1，这是backtrader中表示不使用持仓量数据的默认值
            # (先假设这个数据里没有持仓量信息，或者我们不打算用它)
            if isinstance(openinterest_col, str) and openinterest_col in dataframe.columns:
                # 检查传入的openinterest_col参数是否为字符串类型，并且该字符串作为列名存在于DataFrame中
                # (如果用户指定了一个持仓量列的名字，并且这个名字确实在咱们的表格数据里能找到)
                oi_param_val = openinterest_col
                # 如果条件满足，则将持仓量参数值设置为该列名字符串
                # (那就用这个列名来指定持仓量数据)
            elif isinstance(openinterest_col, str):
                # 如果openinterest_col是字符串类型，但该列名不在DataFrame中
                # (如果用户指定了持仓量列的名字，但在表格里找不到这个名字)
                print(
                    f"警告: 指定的 openinterest 列名 '{openinterest_col}' 在 {file_path} 中不存在。将忽略持仓量。")
                # 打印警告信息，告知用户指定的持仓量列名未找到，将忽略持仓量数据
                # (就提醒用户，他指定的那个持仓量列在这个文件里没有，所以持仓量数据就用不上了)
            elif isinstance(openinterest_col, int) and openinterest_col != -1:
                # 检查openinterest_col是否为整数类型，并且不等于-1 (因为-1是PandasData中表示无持仓量的特殊值)
                # (如果用户给的是一个数字编号，而且这个数字不是-1，-1代表不用持仓量)
                print(
                    f"警告: 为 openinterest 提供了整数索引 {openinterest_col}。如果意图是列名，请使用字符串。否则，行为可能未定义。")
                # 打印警告信息，提示用户为持仓量提供了整数索引，建议使用列名字符串，并指出直接使用整数索引的行为可能未定义
                # (就提醒用户，用数字编号来指定列在backtrader的PandasData里不太规范，最好还是用列的名字。如果非要用数字，可能会出问题)
                oi_param_val = openinterest_col
                # 尽管不推荐，但仍将持仓量参数值设置为该整数索引 (需谨慎使用)
                # (虽然不推荐，但还是按用户给的数字来设置，不过得小心点用)

            data = bt.feeds.PandasData(dataname=dataframe, fromdate=fromdate, todate=todate, datetime=None,
                                       open='open', high='high', low='low', close='close', volume='volume',
                                       openinterest=oi_param_val)
            # 使用处理好的DataFrame和各项参数，创建一个backtrader的PandasData数据源对象
            # (把咱们整理好的表格数据，还有开始结束日期、开高低收量这些列名，以及处理过的持仓量参数，一起打包成一个backtrader能认的数据源)
            data_name = os.path.basename(file_path).split('.')[0]
            # 从文件路径中提取文件名（不含扩展名），作为该数据源在Cerebro中的名称
            # (从完整的文件路径里，把文件名摘出来，比如 "D:/data/stock1.xlsx" 就变成 "stock1"，用作这个数据在回测系统里的名字)
            cerebro.adddata(data, name=data_name)
            # 将创建的数据源对象添加到Cerebro引擎实例中，并指定其名称
            # (把这个打包好的数据源，喂给回测大脑Cerebro，并给它起个名字)
            print(f"数据加载成功: {data_name}")
            # 打印成功加载数据的信息，并显示数据源名称
            # (告诉用户，这个数据成功加载进去了，名字叫啥)
            loaded_data_count += 1
            # 成功加载的数据文件计数器加1
            # (成功装了一个，计数器加一)

        except FileNotFoundError:
            # 如果在尝试读取文件时发生FileNotFoundError异常 (即文件不存在)
            # (如果压根就找不到这个Excel文件)
            print(f"错误: 文件未找到 {file_path}")
            # 打印错误信息，指出哪个文件未找到
            # (就报错，告诉用户这个文件找不着)
        except Exception as e:
            # 如果在处理文件的过程中发生其他任何未被捕获的异常
            # (如果在处理这个文件的时候，发生了其他意想不到的错误)
            print(f"加载数据 {file_path} 时出错: {e}")
            # 打印通用错误信息，指出哪个文件加载出错，并显示异常信息
            # (就报错，告诉用户这个文件加载失败了，顺便把错误原因打出来)
            import traceback
            # 导入traceback模块，用于打印详细的错误堆栈信息
            # (引入一个能看详细错误报告的工具)
            traceback.print_exc()
            # 打印完整的异常堆栈跟踪信息，帮助调试
            # (把出错的详细过程都打印出来，方便程序员找问题)
    return loaded_data_count
    # 返回成功加载的数据文件总数
    # (最后告诉调用者，总共成功加载了多少个数据文件)


def analyze_optimization_results(results):
    # 定义一个函数，用于分析优化结果
    # (这个函数是用来分析跑完策略优化后得到的一堆结果的)

    print("\n{:*^50}")
    # 打印一行由50个星号组成的分割线，用于视觉分隔
    # (在屏幕上打一行星星，好看一点，方便区分不同的输出内容)
    pprint.pprint(results)
    # 使用pprint模块的pprint函数格式化打印优化结果列表
    # (把优化跑出来的原始结果，用一种比较好看的方式打印出来瞅瞅)

    print("\n{:*^50}")
    # 再次打印一行由50个星号组成的分割线
    # (又打一行星星，跟上面的对应)
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
        # 检查优化结果列表是否为空
        # (看看是不是啥结果都没有)
        print("\n{:!^50}".format(' 错误 '))
        # 打印错误提示信息的标题，使用感叹号填充居中
        # (如果没结果，就打个大大的“错误”标题)
        print("没有策略成功运行。请检查数据加载是否有误或参数范围是否有效。")
        # 打印具体的错误信息
        # (告诉用户可能是数据没加载对，或者参数设置有问题，导致一个策略都没跑成功)
        print('!' * 50)
        # 打印一行由50个感叹号组成的分割线
        # (再打一行感叹号，强调一下错误)
        return None, []
        # 如果结果为空，则返回 None 和一个空列表
        # (既然没结果，就返回个空的东西，表示没法分析)

    processed_results = []
    # 初始化一个空列表，用于存储处理后的结果
    # (准备一个空篮子，待会儿把整理好的每个策略的结果放进去)
    print("\n--- 开始提取分析结果 ---")
    # 打印信息，提示开始提取分析结果
    # (告诉用户，现在要开始从原始结果里把有用的信息挑出来了)

    run_count = 0
    # 初始化运行计数器为0
    # (记一下总共跑了多少个参数组合)
    successful_runs = 0
    # 初始化成功提取结果的运行计数器为0
    # (记一下有多少个参数组合是成功提取出分析数据的)
    for strat_list in results:
        # 遍历优化结果列表中的每一个策略运行结果列表
        # (优化的时候，每个参数组合跑完会生成一个小列表，我们一个个来看这些小列表)
        run_count += 1
        # 运行计数器加1
        # (每看一个，总数就加一)
        if not strat_list:
            # 检查当前策略运行结果列表是否为空
            # (看看这个参数组合跑完有没有结果，有时候可能会是空的)
            continue
            # 如果为空，则跳过当前循环，处理下一个结果
            # (要是空的，就不处理了，直接看下一个)

        strategy_instance = strat_list[0]
        # 获取策略实例，通常是列表中的第一个元素
        # (每个小列表里第一个东西就是策略本身的一些信息)
        params = strategy_instance.params
        # 获取策略实例的参数
        # (从策略信息里拿到这次跑的参数是啥)
        analyzers = strategy_instance.analyzers
        # 获取策略实例的分析器
        # (从策略信息里拿到分析器，里面有夏普率、收益这些数据)

        params_str_parts = []
        # 初始化一个空列表，用于存储参数键值对字符串
        # (准备一个空列表，用来放“参数名=参数值”这样的字符串)

        optimized_param_names = [
            'etf_type', 'ema_medium_period', 'ema_long_period',
            'bbands_period', 'bbands_devfactor', 'trend_stop_loss_atr_mult',
            'range_stop_loss_buffer',
            'risk_per_trade_trend',
            'risk_per_trade_range'
        ]
        # 定义一个列表，包含所有参与优化的参数名称
        # (列出我们这次优化都调整了哪些参数，比如ETF类型、均线周期、布林带参数等等)
        for p_name in optimized_param_names:
            # 遍历预定义的优化参数名称列表
            # (一个个地看这些我们关心的参数)
            if hasattr(params, p_name):
                # 检查当前参数对象是否具有名为 p_name 的属性
                # (看看这个策略跑的时候，有没有用到这个参数)
                params_str_parts.append(f"{p_name}={getattr(params, p_name)}")
                # 如果存在该属性，则将其键值对格式化后添加到列表中
                # (有的话，就把它和它的值拼成“参数名=值”的样子，加到列表里)
            else:
                # 如果参数对象没有名为 p_name 的属性
                # (要是没这个参数)
                params_str_parts.append(f"{p_name}=MISSING")
                # 则添加一个表示该参数缺失的字符串
                # (就记一个“参数名=MISSING”，表示这个参数没找到)
        params_str = ", ".join(params_str_parts)
        # 使用逗号和空格将列表中的所有参数字符串连接成一个单一的字符串
        # (把列表里所有的“参数名=值”用逗号隔开，拼成一个长字符串，方便看)

        try:
            # 开始一个 try 块，用于捕获提取分析结果时可能发生的错误
            # (尝试一下提取数据，因为有时候可能会出错)

            sharpe_analysis = analyzers.sharpe_ratio.get_analysis()
            # 从分析器中获取夏普比率的分析结果
            # (从分析器里拿出夏普比率相关的数据)
            returns_analysis = analyzers.returns.get_analysis()
            # 从分析器中获取收益率的分析结果
            # (从分析器里拿出总收益相关的数据)
            drawdown_analysis = analyzers.drawdown.get_analysis()
            # 从分析器中获取最大回撤的分析结果
            # (从分析器里拿出最大亏损（回撤）相关的数据)

            valid_analysis = True
            # 初始化分析结果有效性标志为 True
            # (先假设分析结果是好的)

            if not sharpe_analysis or 'sharperatio' not in sharpe_analysis:
                # 检查夏普比率分析结果是否为空或不包含 'sharperatio' 键
                # (看看夏普比率的数据是不是空的，或者里面没有我们要的 'sharperatio' 这个值)
                valid_analysis = False
                # 如果条件为真，则将有效性标志设为 False
                # (如果是，那这个分析结果就不算好)
            if not returns_analysis or 'rtot' not in returns_analysis:
                # 检查收益率分析结果是否为空或不包含 'rtot' 键
                # (看看总收益的数据是不是空的，或者里面没有我们要的 'rtot' 这个值)
                valid_analysis = False
                # 如果条件为真，则将有效性标志设为 False
                # (如果是，那这个分析结果也不算好)
            if not drawdown_analysis or 'max' not in drawdown_analysis or 'drawdown' not in drawdown_analysis.get('max', {}):
                # 检查回撤分析结果是否为空，或不包含 'max' 键，或 'max' 字典中不包含 'drawdown' 键
                # (看看最大回撤的数据是不是空的，或者里面没有 'max'，或者 'max' 里面没有 'drawdown' 这个值)
                valid_analysis = False
                # 如果条件为真，则将有效性标志设为 False
                # (如果是，那这个分析结果还是不算好)

            if not valid_analysis:
                # 如果分析结果被标记为无效
                # (如果前面检查发现分析结果有问题)

                continue
                # 则跳过当前参数组的处理，继续下一个循环
                # (那这个参数组合就不分析了，直接看下一个)

            sharpe = sharpe_analysis.get('sharperatio')
            # 从夏普比率分析结果中获取 'sharperatio' 的值
            # (拿到夏普比率的值)

            if sharpe is None:
                # 如果获取到的夏普比率为 None
                # (万一夏普比率没取到，是个 None)
                sharpe = 0.0
                # 则将其设置为 0.0
                # (就当它是0吧)

            total_return = returns_analysis.get('rtot', 0.0)
            # 从收益率分析结果中获取 'rtot' 的值，如果不存在则默认为 0.0
            # (拿到总收益率，要是没有就当是0)

            max_drawdown = drawdown_analysis.get(
                'max', {}).get('drawdown', 0.0) / 100.0
            # 从回撤分析结果中获取 'max'字典下的 'drawdown' 值，如果不存在则默认为0.0，然后除以100转换为小数
            # (拿到最大回撤值，它原来是百分比的数字，比如20代表20%，我们把它变成0.2这样的小数)

            current_params_dict = {}
            # 初始化一个空字典，用于存储当前参数组的参数键值对
            # (准备一个字典，把当前这组参数存起来)

            for p_name in optimized_param_names:
                # 遍历预定义的优化参数名称列表
                # (再看一遍我们关心的那些参数名)
                if hasattr(params, p_name):
                    # 检查当前参数对象是否具有名为 p_name 的属性
                    # (看看这个策略跑的时候，有没有用到这个参数)
                    current_params_dict[p_name] = getattr(params, p_name)
                    # 如果存在，则将参数名作为键，参数值作为值，存入字典
                    # (有的话，就存到字典里，比如 'ema_period': 20)
                else:
                    # 如果参数对象没有名为 p_name 的属性
                    # (要是没这个参数)
                    current_params_dict[p_name] = 'MISSING_IN_PARAMS_OBJ'
                    # 则将参数名作为键，值为 'MISSING_IN_PARAMS_OBJ' 存入字典
                    # (就在字典里记一下这个参数缺失了)

            processed_results.append({
                'instance': strategy_instance,
                'params_dict': current_params_dict,
                'sharpe': sharpe,
                'return': total_return,
                'drawdown': max_drawdown
            })
            # 将当前参数组的分析结果(策略实例、参数字典、夏普比率、总回报、最大回撤)打包成字典并添加到 processed_results 列表中
            # (把这个策略实例、它的参数、算出来的夏普、收益、回撤都打包成一个字典，放到我们之前准备的篮子里)
            successful_runs += 1
            # 成功处理的运行次数加1
            # (成功处理完一个，计数加一)

        except AttributeError as e:
            # 捕获属性错误（AttributeError），通常发生在尝试访问不存在的属性时
            # (如果在尝试拿分析器数据的时候，发现某个东西没有，比如 analyzers.sharpe_ratio 根本不存在)

            pass
            # 捕获错误后不执行任何操作，直接跳过
            # (出错了就出错了吧，不影响处理下一个，这里就先不管它)

        except Exception as e:
            # 捕获所有其他类型的异常
            # (如果发生了其他类型的错误)

            import traceback
            # 导入 traceback 模块，用于打印详细的错误堆栈信息
            # (引入一个工具，能帮我们看错误出在哪儿)

            pass
            # 捕获错误后不执行任何操作，直接跳过
            # (同样，出错了也先不管，继续处理其他的)

    print(f"--- 完成提取分析。总运行次数: {run_count}, 成功提取结果: {successful_runs} ---")
    # 打印提取分析完成的信息，包括总运行次数和成功提取结果的次数
    # (告诉用户，数据都看完了，总共看了多少个参数组合，成功整理了多少个)

    if not processed_results:
        # 检查处理后的结果列表是否为空
        # (如果忙活了半天，一个有用的结果都没整理出来)
        print("\n错误：未能成功提取任何有效的分析结果。无法进行评分。")
        # 打印错误信息
        # (就告诉用户，没拿到有效数据，没法打分了)
        return None, []
        # 返回 None 和一个空列表
        # (返回空东西，表示分析失败)

    all_sharpes = [r['sharpe'] for r in processed_results]
    # 使用列表推导式从 processed_results 列表中提取所有结果的夏普比率
    # (把所有整理好的结果里的夏普比率都拿出来，放一个列表里)

    all_returns = [r['return'] for r in processed_results]
    # 使用列表推导式从 processed_results 列表中提取所有结果的总收益率
    # (把所有整理好的结果里的总收益率都拿出来，放一个列表里)

    all_drawdowns = [r['drawdown'] for r in processed_results]
    # 使用列表推导式从 processed_results 列表中提取所有结果的最大回撤
    # (把所有整理好的结果里的最大回撤都拿出来，放一个列表里)

    min_sharpe = min(all_sharpes) if all_sharpes else 0.0
    # 计算所有夏普比率中的最小值，如果列表为空则默认为 0.0
    # (找出所有夏普比率里最小的那个，要是列表是空的，就当最小是0)

    max_sharpe = max(all_sharpes) if all_sharpes else 0.0
    # 计算所有夏普比率中的最大值，如果列表为空则默认为 0.0
    # (找出所有夏普比率里最大的那个，要是列表是空的，就当最大是0)

    min_return = min(all_returns) if all_returns else 0.0
    # 计算所有总收益率中的最小值，如果列表为空则默认为 0.0
    # (找出所有总收益率里最小的那个，要是列表是空的，就当最小是0)

    max_return = max(all_returns) if all_returns else 0.0
    # 计算所有总收益率中的最大值，如果列表为空则默认为 0.0
    # (找出所有总收益率里最大的那个，要是列表是空的，就当最大是0)

    min_drawdown = min(all_drawdowns) if all_drawdowns else 0.0
    # 计算所有最大回撤中的最小值，如果列表为空则默认为 0.0
    # (找出所有最大回撤里最小的那个，要是列表是空的，就当最小是0)

    max_drawdown_val = max(all_drawdowns) if all_drawdowns else 0.0
    # 计算所有最大回撤中的最大值，如果列表为空则默认为 0.0 (变量名用 max_drawdown_val 避免与内置函数 max 冲突)
    # (找出所有最大回撤里最大的那个，要是列表是空的，就当最大是0)

    best_score = float('-inf')
    # 初始化最佳得分为负无穷大
    # (先假设最好的分数是负无穷，这样随便一个分数都比它大，方便后面比较更新)

    best_result_data = None
    # 初始化最佳结果数据为 None
    # (先假设还没有找到最好的结果)

    scored_results = []
    # 初始化一个空列表，用于存储带得分的策略结果
    # (准备一个空列表，用来放所有计算过得分的策略结果)

    print("\n--- 开始计算归一化得分 ---")
    # 打印信息，提示开始计算归一化得分
    # (告诉用户，现在要开始给每个策略结果打分了，打分前会先做个标准化处理)

    print(f"Min/Max - Sharpe: ({min_sharpe:.4f}, {max_sharpe:.4f}), Return: ({min_return:.4f}, {max_return:.4f}), Drawdown: ({min_drawdown:.4f}, {max_drawdown_val:.4f})")
    # 打印各指标（夏普、收益、回撤）的最小值和最大值，格式化为4位小数
    # (把刚才算出来的夏普、收益、回撤的最大最小值都打印出来看看，心里有个数)

    for result_data in processed_results:
        # 遍历所有已处理的策略结果数据
        # (一个个地看我们之前整理好的那些策略结果)

        sharpe = result_data['sharpe']
        # 从当前结果数据中获取夏普比率
        # (拿出这个结果的夏普比率)

        ret = result_data['return']
        # 从当前结果数据中获取总收益率
        # (拿出这个结果的总收益率)

        dd = result_data['drawdown']
        # 从当前结果数据中获取最大回撤
        # (拿出这个结果的最大回撤)

        sharpe_range = max_sharpe - min_sharpe
        # 计算夏普比率的最大值与最小值之差（即范围）
        # (算一下所有夏普比率的最大值和最小值的差距有多大)

        return_range = max_return - min_return
        # 计算总收益率的最大值与最小值之差（即范围）
        # (算一下所有总收益率的最大值和最小值的差距有多大)

        drawdown_range = max_drawdown_val - min_drawdown
        # 计算最大回撤的最大值与最小值之差（即范围）
        # (算一下所有最大回撤的最大值和最小值的差距有多大)

        sharpe_norm = (sharpe - min_sharpe) / \
            sharpe_range if sharpe_range > 1e-9 else 0.0
        # 归一化夏普比率：(当前值 - 最小值) / 范围。如果范围过小（接近0），则归一化值为0
        # (把当前的夏普比率，按照它在所有夏普比率里的位置，换算成一个0到1之间的数。如果所有夏普都差不多一样，就直接给0)

        return_norm = (ret - min_return) / \
            return_range if return_range > 1e-9 else 0.0
        # 归一化总收益率：(当前值 - 最小值) / 范围。如果范围过小，则归一化值为0
        # (同样的方法，把总收益率也换算成0到1之间的数)

        drawdown_norm = (dd - min_drawdown) / \
            drawdown_range if drawdown_range > 1e-9 else 0.0
        # 归一化最大回撤：(当前值 - 最小值) / 范围。如果范围过小，则归一化值为0
        # (最大回撤也一样，换算成0到1之间的数)

        score = 0.6 * sharpe_norm + 0.1 * return_norm - 0.3 * drawdown_norm
        # 计算综合得分：夏普比率权重0.6，收益率权重0.1，回撤权重-0.3 (回撤是负向指标)
        # (给这个策略打个总分：标准化的夏普比率占60%，标准化的收益率占10%，标准化的回撤扣30%的分，因为回撤越小越好)

        result_data['score'] = score
        # 将计算出的综合得分添加到当前结果数据字典中
        # (把算出来的总分，存到这个策略结果里)

        scored_results.append(result_data)
        # 将带有得分的当前结果数据添加到 scored_results 列表中
        # (把这个包含了参数、各项指标和总分的策略结果，加到打分结果列表里)

        if score > best_score:
            # 如果当前计算的得分高于已知的最佳得分
            # (如果这个策略的总分比我们目前见过的最高分还要高)

            best_score = score
            # 更新最佳得分为当前得分
            # (那这个分数就是新的最高分)

            best_result_data = result_data
            # 更新最佳结果数据为当前的策略结果数据
            # (这个策略就是目前最好的策略)

    print(f"--- 完成 {len(scored_results)} 组得分计算 ---")
    # 打印得分计算完成的信息，并显示总共计算了多少组结果的得分
    # (告诉用户，所有策略都打完分了，总共打了多少个)

    return best_result_data, scored_results
    # 返回最佳结果数据和所有带得分的结果列表
    # (把找到的最好策略的结果，以及所有策略的打分结果，都返回出去)


# ===================================================================================
# Main Program Entry Point
# ===================================================================================
if __name__ == '__main__':
    # 设置是否进行参数优化
    optimize = True
    # optimize = False
    # 控制是否执行参数优化模式
    # (决定是进行参数优化还是单次回测)

    # 设置初始资金
    initial_cash = 500000.0
    # 设置回测的初始资金金额
    # (设置回测开始时的账户资金为50万元)

    # 设置交易佣金率
    commission_rate = 0.0003
    # 设置交易佣金比例，这里是万分之三
    # (设置每笔交易的佣金费率为0.03%)

    # 获取脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # 获取当前脚本文件的绝对路径的目录部分
    # (找出当前脚本文件所在的文件夹路径)

    # 构建数据文件夹路径
    data_folder = os.path.join(script_dir, '..', '..', 'datas')
    # 基于脚本目录构建数据文件夹路径，向上两级再进入datas文件夹
    # (根据脚本位置，找到存放数据文件的文件夹路径)

    # 直接指定数据文件夹路径
    data_folder = r'D:\\BT2025\\datas\\'
    # 覆盖之前的路径，直接使用硬编码的数据文件夹路径
    # (直接指定数据文件夹在D盘BT2025目录下的datas文件夹)

    # 打印数据文件夹路径
    print(f"数据文件夹路径: {data_folder}")
    # 输出数据文件夹的路径，方便用户确认
    # (显示数据文件夹的位置，让用户知道从哪里读取数据)

    # 检查数据文件夹是否存在
    if not os.path.isdir(data_folder):
        # 如果指定的数据文件夹路径不存在
        # (如果找不到这个数据文件夹)

        # 打印错误信息
        print(f"错误: 数据文件夹路径不存在: {data_folder}")
        # 输出错误信息，提示用户数据文件夹不存在
        # (告诉用户找不到数据文件夹，并显示具体路径)

        # 退出程序
        sys.exit(1)
        # 以错误状态码1退出程序
        # (直接结束程序，因为没有数据文件夹就无法继续)

    # 定义数据文件路径列表
    data_files = [
        os.path.join(data_folder, '510050_d.xlsx'),
        os.path.join(data_folder, '510300_d.xlsx'),
        os.path.join(data_folder, '159949_d.xlsx')
    ]
    # 创建包含三个ETF数据文件完整路径的列表
    # (指定三个ETF的数据文件：50ETF、300ETF和创业板ETF)

    # 检查是否有缺失的数据文件
    missing_files = [f for f in data_files if not os.path.isfile(f)]
    # 检查每个数据文件是否存在，创建缺失文件列表
    # (检查哪些数据文件是找不到的)

    # 如果有缺失文件，打印错误并退出
    if missing_files:
        # 如果存在缺失的数据文件
        # (如果有找不到的数据文件)

        # 打印错误信息
        print(f"错误: 以下数据文件未找到:")
        # 输出错误信息，提示用户有数据文件未找到
        # (告诉用户有些数据文件找不到)

        # 遍历打印每个缺失的文件
        for f in missing_files:
            # 打印缺失文件路径
            print(f" - {f}")
            # 输出每个缺失文件的路径
            # (列出每个找不到的数据文件的具体路径)

        # 退出程序
        sys.exit(1)
        # 以错误状态码1退出程序
        # (直接结束程序，因为缺少必要的数据文件)

    # 定义数据列名映射
    column_mapping = {'date': 'datetime', '开盘': 'open',
                      '最高': 'high', '最低': 'low', '收盘': 'close', '成交量': 'volume'}
    # 创建Excel列名到Backtrader所需列名的映射字典
    # (告诉程序如何把Excel表格中的中文列名转换成回测系统需要的英文列名)

    # 设置持仓量列名
    openinterest_col_name = None
    # 不使用持仓量数据，设置为None
    # (不使用持仓量数据，因为ETF数据中通常没有这一项)

    # 设置回测起始日期
    fromdate = datetime.datetime(2015, 1, 1)
    # 设置回测的开始日期为2015年1月1日
    # (设定回测从2015年1月1日开始)

    # 设置回测结束日期
    todate = datetime.datetime(2024, 4, 30)
    # 设置回测的结束日期为2024年4月30日
    # (设定回测到2024年4月30日结束)

    # 设置仓位管理器参数
    sizer_params = dict(
        max_position_per_etf_percent=0.30,
    )
    # 设置仓位管理器的参数，每个ETF最大持仓比例为30%
    # (设置每个ETF最多只能占用总资金的30%)

    # 定义EMA中期参数范围
    ema_medium_range = range(40, 81, 20)
    # 设置EMA中期均线周期的优化范围，从40到80，步长为20
    # (设置中期均线的周期范围：40、60、80)

    # 定义EMA长期参数范围
    ema_long_range = range(100, 141, 20)
    # 设置EMA长期均线周期的优化范围，从100到140，步长为20
    # (设置长期均线的周期范围：100、120、140)

    # 定义布林带周期参数范围
    bbands_period_range = range(15, 26, 5)
    # 设置布林带周期的优化范围，从15到25，步长为5
    # (设置布林带周期的范围：15、20、25)

    # 定义布林带标准差参数范围
    bbands_dev_range = np.arange(1.8, 2.3, 0.2).tolist()
    # 设置布林带标准差倍数的优化范围，从1.8到2.2，步长为0.2
    # (设置布林带标准差倍数的范围：1.8、2.0、2.2)

    # 定义趋势止损ATR倍数参数范围
    trend_sl_atr_mult_range = np.arange(2.0, 3.1, 0.5).tolist()
    # 设置趋势交易止损ATR倍数的优化范围，从2.0到3.0，步长为0.5
    # (设置趋势交易止损的ATR倍数范围：2.0、2.5、3.0)

    # 定义区间止损缓冲参数范围
    range_sl_buffer_range = np.arange(0.003, 0.008, 0.002).tolist()
    # 设置区间交易止损缓冲的优化范围，从0.003到0.007，步长为0.002
    # (设置区间交易止损缓冲的范围：0.3%、0.5%、0.7%)

    # 定义趋势交易风险参数范围
    risk_trend_range = np.arange(0.008, 0.013, 0.002).tolist()
    # 设置趋势交易每笔风险的优化范围，从0.8%到1.2%，步长为0.2%
    # (设置趋势交易每笔风险比例的范围：0.8%、1.0%、1.2%)

    # 定义区间交易风险参数范围
    risk_range_range = np.arange(0.004, 0.007, 0.001).tolist()
    # 设置区间交易每笔风险的优化范围，从0.4%到0.6%，步长为0.1%
    # (设置区间交易每笔风险比例的范围：0.4%、0.5%、0.6%)

    # 创建Cerebro引擎实例
    cerebro = bt.Cerebro(stdstats=not optimize, optreturn=False)
    # 创建Backtrader的Cerebro引擎，如果是优化模式则关闭标准统计图表，不返回优化结果
    # (创建回测引擎，优化模式下不显示图表，提高速度)

    # 加载数据到Cerebro
    loaded_data_count = load_data_to_cerebro(
        cerebro, data_files, column_mapping, openinterest_col_name, fromdate, todate)
    # 调用函数加载数据到Cerebro引擎，并返回成功加载的数据源数量
    # (把所有ETF数据加载到回测引擎中)

    # 检查是否成功加载数据
    if loaded_data_count == 0:
        # 如果没有成功加载任何数据
        # (如果一个数据都没加载成功)

        # 打印错误信息
        print("\n错误：未能成功加载任何数据文件。无法继续执行。")
        # 输出错误信息，提示用户未能加载任何数据
        # (告诉用户没有加载到任何数据，无法继续回测)

        # 退出程序
        sys.exit(1)
        # 以错误状态码1退出程序
        # (直接结束程序，因为没有数据就无法回测)

    # 打印加载的数据源数量
    print(f"\n总共加载了 {loaded_data_count} 个数据源。")
    # 输出成功加载的数据源数量
    # (告诉用户成功加载了多少个ETF的数据)

    # 设置初始资金
    cerebro.broker.setcash(initial_cash)
    # 设置Cerebro引擎中模拟券商的初始资金
    # (设置回测开始时的账户资金)

    # 设置交易佣金
    cerebro.broker.setcommission(commission=commission_rate, stocklike=True)
    # 设置交易佣金率，使用股票类型的佣金计算方式
    # (设置交易佣金费率，按照股票方式计算)

    # 添加仓位管理器
    cerebro.addsizer(AShareETFSizer, **sizer_params)
    # 添加自定义的A股ETF仓位管理器，传入仓位参数
    # (添加仓位管理器，控制每个ETF的持仓比例)

    # 添加夏普比率分析器
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe_ratio',
                        timeframe=bt.TimeFrame.Days, riskfreerate=0.0, annualize=True, factor=252)
    # 添加夏普比率分析器，使用日线数据，无风险利率为0，年化计算，交易日为252天
    # (添加夏普比率计算器，用来评估策略的风险调整后收益)

    # 添加回撤分析器
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    # 添加回撤分析器，用于计算策略的最大回撤
    # (添加回撤计算器，用来评估策略的风险)

    # 添加收益率分析器
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
    # 添加收益率分析器，用于计算策略的收益率
    # (添加收益率计算器，用来评估策略的盈利能力)

    # 添加交易分析器
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trade_analyzer')
    # 添加交易分析器，用于分析策略的交易情况
    # (添加交易分析器，用来评估策略的交易表现)

    # 判断是否进行参数优化
    if optimize:
        # 如果是优化模式
        # (如果选择了参数优化模式)

        # 打印参数优化设置标题
        print("\n{:-^50}".format(' 参数优化设置 '))
        # 输出参数优化设置的标题，居中显示
        # (显示参数优化的设置信息)

        # 打印各参数的优化范围
        print(f"  etf_type: ['trend', 'range']")
        # 输出ETF类型的优化选项
        # (显示ETF交易类型的选项：趋势型和区间型)

        print(f"  ema_medium_period: {list(ema_medium_range)}")
        # 输出EMA中期均线周期的优化范围
        # (显示中期均线周期的所有可能值)

        print(f"  ema_long_period: {list(ema_long_range)}")
        # 输出EMA长期均线周期的优化范围
        # (显示长期均线周期的所有可能值)

        print(f"  bbands_period: {list(bbands_period_range)}")
        # 输出布林带周期的优化范围
        # (显示布林带周期的所有可能值)

        print(f"  bbands_devfactor: {bbands_dev_range}")
        # 输出布林带标准差倍数的优化范围
        # (显示布林带标准差倍数的所有可能值)

        print(f"  trend_stop_loss_atr_mult: {trend_sl_atr_mult_range}")
        # 输出趋势止损ATR倍数的优化范围
        # (显示趋势交易止损的ATR倍数的所有可能值)

        print(f"  range_stop_loss_buffer: {range_sl_buffer_range}")
        # 输出区间止损缓冲的优化范围
        # (显示区间交易止损缓冲的所有可能值)

        print(f"  risk_per_trade_trend: {risk_trend_range}")
        # 输出趋势交易风险的优化范围
        # (显示趋势交易每笔风险比例的所有可能值)

        print(f"  risk_per_trade_range: {risk_range_range}")
        # 输出区间交易风险的优化范围
        # (显示区间交易每笔风险比例的所有可能值)

        # 打印分隔线
        print('-' * 50)
        # 输出分隔线
        # (用横线分隔不同部分的信息)

        # 添加优化策略
        cerebro.optstrategy(AShareETFStrategy,
                            etf_type=['trend', 'range'],
                            ema_medium_period=ema_medium_range,
                            ema_long_period=ema_long_range,
                            # bbands_period=bbands_period_range,
                            # bbands_devfactor=bbands_dev_range,
                            # trend_stop_loss_atr_mult=trend_sl_atr_mult_range,
                            # range_stop_loss_buffer=range_sl_buffer_range,
                            # risk_per_trade_trend=risk_trend_range,
                            # risk_per_trade_range=risk_range_range
                            )
        # 添加优化策略，设置要优化的参数及其范围
        # (设置要优化的策略和参数，注意有些参数被注释掉了，不参与优化)

        # 打印开始优化信息
        print('开始参数优化运行...')
        # 输出提示信息，表明开始参数优化
        # (告诉用户开始运行参数优化)

        # 记录开始时间
        start_time = time.time()
        # 记录优化开始的时间戳
        # (记录开始时间，用于后面计算耗时)

        # 运行优化
        results = cerebro.run(maxcpus=os.cpu_count() or 1)
        # results = cerebro.run(maxcpus=1)
        # 运行Cerebro引擎的优化，使用所有可用CPU核心
        # (开始运行优化，尽可能利用所有CPU核心加速)

        # 记录结束时间
        end_time = time.time()
        # 记录优化结束的时间戳
        # (记录结束时间，用于计算总耗时)

        # 计算总耗时
        total_time = end_time - start_time
        # 计算优化的总耗时（秒）
        # (计算整个优化过程花了多少秒)

        # 初始化实际组合数
        actual_combinations = 0
        # 初始化实际运行的参数组合数量
        # (先假设没有运行任何参数组合)

        # 如果有结果，计算实际组合数
        if results:
            # 如果优化结果不为空
            # (如果有优化结果)

            # 计算实际组合数
            actual_combinations = len(results)
            # 计算实际运行的参数组合数量
            # (计算实际运行了多少组不同的参数)

        # 计算每组平均耗时
        avg_time_per_run = total_time / actual_combinations if actual_combinations > 0 else 0

        print('\n{:=^50}'.format(' 优化完成统计 '))
        print(f"{'总用时':<20}: {total_time:.2f}秒 ({total_time/60:.2f}分钟)")
        print(f"{'实际参数组数':<20}: {actual_combinations}")
        print(f"{'每组平均用时':<20}: {avg_time_per_run:.2f}秒")
        print('=' * 50)

        best_result, all_scored_results = analyze_optimization_results(results)

        if best_result:
            best_params_dict = best_result.get('params_dict', {})

            header_format_str = '{:<8} {:<8} {:<8} {:<8} {:<8} {:<8} {:<8} {:<10} {:<10} {:<10} {:<10} {:<10} {:<10}'
            # (Header format string)
            row_format_str = '{etf_type:<8} {ema_medium_period:<8.0f} {ema_long_period:<8.0f} {bbands_period:<8.0f} {bbands_devfactor:<8.1f} {trend_stop_loss_atr_mult:<8.1f} {range_stop_loss_buffer:<8.3f} {risk_per_trade_trend:<10.3f} {risk_per_trade_range:<10.3f} {sharpe:<10.4f} {return_val:<10.2f} {drawdown_val:<10.2f} {score:<10.4f}'
            # (Row format string)

            num_cols = 13
            col_widths = [8, 8, 8, 8, 8, 8, 8, 10, 10, 10, 10, 10, 10]
            total_width = sum(col_widths) + len(col_widths) - 1

            print(f'\n{(" 参数优化结果 (按得分排序) "):=^{total_width}}')
            print(header_format_str.format('ETF类型', 'EMA中', 'EMA长', 'BB周期',
                  'BB标差', 'ATR止损', '区间SL', '趋势风险%', '区间风险%', '夏普', '收益%', '回撤%', '得分'))
            # (Print header row)
            print('-' * total_width)

            all_scored_results.sort(key=lambda x: x.get(
                'score', float('-inf')), reverse=True)

            for res_data in all_scored_results[:min(20, len(all_scored_results))]:
                p_dict = res_data.get('params_dict', {})
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
                        'risk_per_trade_trend', 0.0) * 100,
                    risk_per_trade_range=p_dict.get(
                        'risk_per_trade_range', 0.0) * 100,
                    sharpe=res_data.get('sharpe', 0.0),
                    return_val=res_data.get('return', 0.0) * 100,
                    drawdown_val=res_data.get('drawdown', 0.0) * 100,
                    score=res_data.get('score', 0.0)
                ))

            print(f'\n{(" 最优参数组合 "):=^50}')
            # (Print best parameter combination title)
            print(f"{'ETF类型':<25}: {best_params_dict.get('etf_type', 'N/A')}")
            print(f"{'EMA中期':<25}: {best_params_dict.get('ema_medium_period', 0)}")
            print(f"{'EMA长期':<25}: {best_params_dict.get('ema_long_period', 0)}")
            print(f"{'布林带周期':<25}: {best_params_dict.get('bbands_period', 0)}")
            print(
                f"{'布林带标准差':<25}: {best_params_dict.get('bbands_devfactor', 0.0):.1f}")
            print(
                f"{'趋势止损ATR倍数':<25}: {best_params_dict.get('trend_stop_loss_atr_mult', 0.0):.1f}")
            print(
                f"{'区间止损缓冲':<25}: {best_params_dict.get('range_stop_loss_buffer', 0.0):.4f}")
            print(
                f"{'趋势交易风险':<25}: {best_params_dict.get('risk_per_trade_trend', 0.0)*100:.2f}%")
            print(
                f"{'区间交易风险':<25}: {best_params_dict.get('risk_per_trade_range', 0.0)*100:.2f}%")
            print(f"{'夏普比率':<25}: {best_result.get('sharpe', 0.0):.4f}")
            print(f"{'总收益率':<25}: {best_result.get('return', 0.0) * 100:.2f}%")
            print(f"{'最大回撤':<25}: {best_result.get('drawdown', 0.0) * 100:.2f}%")
            print(f"{'得分':<25}: {best_result.get('score', 0.0):.4f}")
            print('=' * 50)
        else:
            print("\n错误：未能确定最优策略或处理结果时出错。")
            # (Error: Failed to determine optimal strategy or error occurred during result processing.)

    else:  # 单次回测
        # (Single Run)
        print("\n{:-^50}".format(' 单次回测设置 '))
        print(f"优化开关: 关闭")
        print(f"Observer 图表: 开启")
        print("\nSizer 参数:")
        for k, v in sizer_params.items():
            print(f"  {k}: {v}")

        strategy_run_params = dict(
            etf_type='trend',
            ema_medium_period=60,
            ema_long_period=120,
            bbands_period=20,
            bbands_devfactor=2.0,
            trend_stop_loss_atr_mult=2.5,
            range_stop_loss_buffer=0.005,
            risk_per_trade_trend=0.01,
            risk_per_trade_range=0.005
        )
        print("\n策略 参数:")
        # (Strategy Parameters:)
        for k, v in strategy_run_params.items():
            print(f"  {k}: {v}")
            # (Print key-value pair)
        print('-' * 50)

        cerebro.addstrategy(AShareETFStrategy, **strategy_run_params)
        # (Add strategy with specified parameters)

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
        # Modified line: Check if results list is not empty, instead of 'if results and results[0]:'
        if results:
            strat_instance = results[0]
            for analyzer_name, analyzer_obj in strat_instance.analyzers.getitems():
                analysis = analyzer_obj.get_analysis()
                print(f"\n--- {analyzer_name} ---")
                if isinstance(analysis, dict):
                    for k, v in analysis.items():
                        if isinstance(v, dict):
                            print(f"  {k}:")
                            for sub_k, sub_v in v.items():
                                if isinstance(sub_v, float):
                                    print(f"    {sub_k}: {sub_v:.4f}")
                                else:
                                    print(f"    {sub_k}: {sub_v}")
                        else:
                            if isinstance(v, float):
                                print(f"  {k}: {v:.4f}")
                            else:
                                print(f"  {k}: {v}")
                elif isinstance(analysis, float):
                    print(f"{analysis:.4f}")
                else:
                    print(analysis)
        print('-' * 50)

        if not optimize:
            try:
                print("\n尝试绘制图表...")
                if cerebro.datas:  # 检查是否有数据
                    data_to_plot_name = cerebro.datas[0]._name  # 获取第一个数据源的名称
                    print(f"尝试为 {data_to_plot_name} 生成图表...")
                    # 使用默认的 iplot=True 来尝试交互式显示, 不设置 savefig 来避免保存
                    # 仅绘制第一个数据源的图表
                    cerebro.plot(style='candlestick', barup='red', bardown='green',
                                 volume=True, plotdatanames=[data_to_plot_name])
                    print("图表已尝试使用 Matplotlib 显示。")
                else:
                    print("没有数据可供绘制。")
            except ImportError:
                print("\n无法绘制图表：缺少 'matplotlib' 库。请使用 pip install matplotlib 安装。")
            except Exception as e:
                print(f"\n绘制图表时出错: {e}")
                print("请确保已安装绘图库 (matplotlib) 且图形环境配置正确。")
