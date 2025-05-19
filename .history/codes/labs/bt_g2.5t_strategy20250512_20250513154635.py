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
    # 定义一个名为 `AShareETFSizer` 的类，它继承自 `backtrader.Sizer` 类，用于自定义A股ETF的头寸计算逻辑。
    # (创建一个专门给A股ETF算每次买多少的工具，基于 `backtrader` 的 `Sizer` 改造。职责更纯粹：根据策略算好的风险信息来计算数量。)
    params = (
        # 定义该Sizer的参数。
        # (给这个算数量的工具预设一些可以调整的选项。)
        ('max_position_per_etf_percent', 0.30),
        # 定义参数 `max_position_per_etf_percent`，默认值为0.30 (30%)，表示单个ETF持仓市值占总账户价值的最大比例。
        # (设置一个选项叫 'max_position_per_etf_percent'，默认是0.30，意思是不管怎么买，单个ETF的市值不能超过总资产的30%。这个限制由Sizer自己控制。)
    )

    def _getsizing(self, comminfo, cash, data, isbuy):
        # 定义 `_getsizing` 方法，此方法由Backtrader在需要确定头寸大小时调用。
        # (定义一个名叫 `_getsizing` 的函数，`backtrader` 每次要决定买多少股票的时候，就会来问这个函数。)
        if not isbuy:
            # 检查当前操作是否为买入操作。
            # (判断一下是不是要买入。)
            return 0  # 只处理买入
            # (如果不是买入，就返回0。)

        position = self.broker.getposition(data)
        # 获取当前数据对象（例如某ETF）的持仓情况。
        # (查一下现在手上有没有这只ETF，有多少。)
        if position.size != 0:
            # 如果当前数据对象已有持仓。
            # (如果已经持有这只ETF了。)
            return 0  # 不重复开仓
            # (那就返回0，意思是不再买了。)

        d_name = data._name
        # 获取当前数据对象的名称。
        # (拿到这只ETF的名字。)
        strategy = self.strategy
        # 获取关联的策略实例。
        # (拿到咱们正在用的那个交易策略。)

        # --- 解耦关键点：从策略获取预计算的风险信息 ---
        # (Decoupling Point: Get pre-calculated risk info from strategy)
        if not hasattr(strategy, 'pending_trade_info') or d_name not in strategy.pending_trade_info:
            # 检查策略是否有 'pending_trade_info' 字典，以及是否有当前ETF的待处理信息。
            # (看看策略那边有没有准备好一个叫 'pending_trade_info' 的本子，以及本子里有没有记录这只ETF的交易计划。)
            strategy.log(
                f"Sizer: 无法在 strategy.pending_trade_info 中找到 {d_name} 的待处理交易信息。跳过。", data=data)
            # (如果找不到，记个日志说一声，这次买不了。)
            return 0
            # (返回0，不买了。)

        trade_info = strategy.pending_trade_info[d_name]
        # 获取策略为当前ETF准备的交易信息字典。
        # (从策略的 'pending_trade_info' 本子里拿出这只ETF的交易计划。)

        entry_price = trade_info.get('entry_price')
        # 获取策略计算的参考入场价。
        # (拿到策略计划的买入参考价。)
        risk_per_share = trade_info.get('risk_per_share')
        # 获取策略计算的每股风险。
        # (拿到策略算好的买一股可能亏多少钱。)
        amount_to_risk = trade_info.get('amount_to_risk')
        # 获取策略计算的本次交易允许的最大风险金额。
        # (拿到策略算好的这次交易最多能亏多少钱。)

        # 验证从策略获取的信息是否有效
        # (Validate info received from strategy)
        if entry_price is None or risk_per_share is None or amount_to_risk is None:
            # 检查关键信息是否缺失。
            # (看看是不是缺了买入价、每股风险、或者总风险金额。)
            strategy.log(
                f"Sizer: 从策略获取的 {d_name} 交易信息不完整。跳过。信息: {trade_info}", data=data)
            # (如果信息不全，记个日志说一下，这次买不了。)
            # 清理策略中的无效信息，避免后续混淆
            # (Clean up invalid info in strategy to avoid later confusion)
            del strategy.pending_trade_info[d_name]
            # (把策略那边对应的这条无效计划也删掉。)
            return 0
            # (返回0，不买了。)

        if risk_per_share <= 1e-9:
            # 如果每股风险过小 (由策略计算得出)。
            # (如果策略算出来每股风险几乎是0。)
            strategy.log(
                f"Sizer: 策略计算的 {d_name} 每股风险({risk_per_share:.2f})过小。跳过。", data=data)
            # (记个日志说策略算出来的风险太小了，买不了。)
            del strategy.pending_trade_info[d_name]
            # (把策略那边对应的计划删掉。)
            return 0
            # (返回0，不买了。)
        if amount_to_risk <= 1e-9:
            # 如果最大风险金额过小。
            # (如果策略算出来这次交易能承担的总风险几乎是0。)
            strategy.log(
                f"Sizer: 策略计算的 {d_name} 最大风险金额({amount_to_risk:.2f})过小。跳过。", data=data)
            # (记个日志说策略算出来的总风险太小了，买不了。)
            del strategy.pending_trade_info[d_name]
            # (把策略那边对应的计划删掉。)
            return 0
            # (返回0，不买了。)

        # --- 核心计算：基于策略提供的风险信息计算头寸 ---
        # (Core Calculation: Size based on risk info provided by strategy)
        size_raw = amount_to_risk / risk_per_share
        # 根据最大风险金额和每股风险计算原始的股票数量。
        # (用最多能亏的钱除以每股亏的钱，得到一个初步的购买数量。)
        size = int(size_raw / 100) * 100
        # 对原始数量向下取整到最近的100的倍数。
        # (按A股规矩，向下凑个100股的整数倍。)

        if size <= 0:
            # 如果根据风险计算出的头寸数量小于或等于0。
            # (如果算出来要买的数量是0或者负数。)
            strategy.log(
                f"Sizer: 基于策略风险计算 {d_name} 的头寸为 {size}。风险/股: {risk_per_share:.2f}, 允许风险额: {amount_to_risk:.2f}", data=data)
            # (记个日志说按风险算下来买不了。)
            del strategy.pending_trade_info[d_name]  # 清理信息
            # (把策略那边对应的计划删掉。)
            return 0
            # (返回0，不买了。)

        # --- 应用 Sizer 自身的全局限制 ---
        # (Apply Sizer's own global constraints)
        equity = self.broker.getvalue()
        # 获取当前账户总值。
        # (看看现在账户里总共有多少钱。)
        max_pos_value_for_etf = equity * self.p.max_position_per_etf_percent
        # 计算单个ETF允许的最大持仓市值。
        # (算一下这只ETF最多能买多少钱的。)
        price_for_value_calc = entry_price  # 使用策略提供的入场价
        # (用策略计划的那个买入参考价来算市值。)

        if price_for_value_calc <= 1e-9:
            # 如果策略提供的价格无效。
            # (如果策略给的买入价太小了。)
            strategy.log(
                f"Sizer: 策略提供的 {d_name} 参考入场价 ({price_for_value_calc:.2f}) 无效。", data=data)
            # (记个日志说策略给的价格不对。)
            del strategy.pending_trade_info[d_name]  # 清理信息
            # (把策略那边对应的计划删掉。)
            return 0
            # (返回0，不买了。)

        size_limited_by_max_etf_pos = int(
            max_pos_value_for_etf / price_for_value_calc / 100) * 100
        # 根据单个ETF最大持仓市值和价格计算允许的最大股数。
        # (根据这只ETF最多能买多少钱，以及它的价格，算出最多能买多少股。)
        if size > size_limited_by_max_etf_pos:
            # 如果基于风险计算的头寸超过了单个ETF最大仓位限制。
            # (如果前面按风险算出来的数量，比按最大仓位算出来的还多。)
            strategy.log(
                f"Sizer: {d_name} 头寸从 {size} 减少到 {size_limited_by_max_etf_pos} (受限于 max_position_per_etf_percent)。", data=data)
            # (记个日志说因为单个ETF仓位限制，买的数量减少了。)
            size = size_limited_by_max_etf_pos
            # 将头寸调整为限制内的最大数量。
            # (那就按最大仓位允许的数量来买。)

        if size <= 0:
            # 如果调整后头寸小于等于0。
            # (如果调整完发现买不了了。)
            strategy.log(f"Sizer: {d_name} 头寸在最大ETF仓位限制后为 {size}。", data=data)
            # (记个日志说因为仓位限制，最后买不了。)
            del strategy.pending_trade_info[d_name]  # 清理信息
            # (把策略那边对应的计划删掉。)
            return 0
            # (返回0，不买了。)

        # --- 检查现金是否足够 ---
        # (Check if cash is sufficient)
        potential_trade_total_cost = size * price_for_value_calc
        # 计算潜在交易的总成本。
        # (算一下按这个数量买，大概要花多少钱。)
        if potential_trade_total_cost > cash:
            # 如果成本超过可用现金。
            # (如果要花的钱比现在账户里能用的现金还多。)
            size_limited_by_cash = int(cash / price_for_value_calc / 100) * 100
            # 根据可用现金计算能买的最大股数。
            # (那就用能用的现金，看看能买多少股。)
            if size_limited_by_cash < size:
                # 如果现金限制的股数更少。
                # (如果按现金算出来能买的数量，比之前算出来的数量还要少。)
                strategy.log(
                    f"Sizer: {d_name} 头寸从 {size} 减少到 {size_limited_by_cash} (受限于现金)。现金: {cash:.2f}, 预估成本: {potential_trade_total_cost:.2f}", data=data)
                # (记个日志说因为钱不够，买的数量又减少了。)
                size = size_limited_by_cash
                # 更新头寸为现金允许的最大数量。
                # (那就按现金能买的最大数量来买。)

        if size <= 0:
            # 如果最终计算的头寸小于等于0。
            # (如果最后算下来买不了了。)
            strategy.log(f"Sizer: {d_name} 最终计算头寸为 {size}。无法下单。", data=data)
            # (记个日志说最后算出来买不了。)
            del strategy.pending_trade_info[d_name]  # 清理信息
            # (把策略那边对应的计划删掉。)
            return 0
            # (返回0，不买了。)

        # Sizer 计算完成，返回最终头寸
        # (Sizer calculation complete, return final size)
        strategy.log(f"Sizer为 {d_name} 计算头寸: {size} (基于策略风险信息)", data=data)
        # (记个日志，告诉大家最后算出来要买多少股，是根据策略给的风险信息算的。)

        # Sizer执行成功后，策略会在notify_order中清理pending_trade_info
        # (After Sizer executes successfully, the strategy will clean up pending_trade_info in notify_order)
        return size
        # (把最后算好的购买数量告诉 `backtrader`。)


class AShareETFStrategy(bt.Strategy):
    # 定义一个名为 `AShareETFStrategy` 的类，它继承自 `backtrader.Strategy` 类，用于实现A股ETF的交易策略。
    # (创建一个专门针对A股ETF的交易策略。)
    params = (
        ('etf_type', 'trend'),  # 策略决定基础交易类型
        # ('etf_type', 'trend'), # Strategy determines base trade type
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
        ('trend_stop_loss_atr_mult', 2.5),  # 策略用这个计算止损价
        # ('trend_stop_loss_atr_mult', 2.5), # Strategy uses this to calculate stop loss price
        ('trend_take_profit_rratio', 2.0),
        ('range_stop_loss_buffer', 0.005),  # 策略用这个计算止损价
        # ('range_stop_loss_buffer', 0.005), # Strategy uses this to calculate stop loss price
        ('max_total_account_risk_percent', 0.06),
        ('drawdown_level1_threshold', 0.05),
        ('drawdown_level2_threshold', 0.10),
        # --- 新增：定义策略层面的单笔交易风险 ---
        # (--- NEW: Define per-trade risk at the strategy level ---)
        ('risk_per_trade_trend', 0.01),  # 趋势型单笔风险
        # ('risk_per_trade_trend', 0.01), # Trend per-trade risk
        ('risk_per_trade_range', 0.005),  # 区间型单笔风险
        # ('risk_per_trade_range', 0.005), # Range per-trade risk
    )

    def log(self, txt, dt=None, data=None):
        # 定义 `log` 方法，用于在策略执行过程中输出日志信息。
        # (定义一个名叫 `log` 的函数，专门用来在策略跑的时候打印一些信息，方便我们看过程。)
        # --- 重新启用日志 ---
        # (--- Re-enable logging ---)
        return  # <--- 注释掉或删除这行以启用日志
        # (<--- Comment out or remove this line to enable logging)
        _data = data if data is not None else (
            self.datas[0] if self.datas else None)
        # 如果 `data` 参数已提供，则使用它；否则，如果策略有数据源，则使用第一个数据源；如果都没有，则为 `None`。
        # (看看调用log的时候有没有指定是哪个股票的数据，有就用那个；没有的话，如果策略本身在处理股票数据，就用第一个；如果啥数据都没有，那就没办法了。)

        log_dt_str = ""
        # 初始化日志日期时间字符串为空。
        # (准备一个空字符串，用来放日志的时间信息。)
        if _data and hasattr(_data, 'datetime') and hasattr(_data.datetime, 'date') and len(_data.datetime) > 0:
            # 如果 `_data` 存在，并且它有 `datetime` 属性，并且 `datetime` 序列不为空。
            # (如果咱们有具体的股票数据，而且这个数据里面有时间信息，并且时间信息不是空的。)
            dt_val = _data.datetime.date(0)  # 获取当前bar的日期
            # (获取当前bar的日期)
            if isinstance(dt_val, (datetime.date, datetime.datetime)):
                log_dt_str = dt_val.isoformat()
                # (将日期格式化为 ISO 格式的字符串。)
            elif isinstance(dt_val, float):  # 有时 backtrader 的日期可能是浮点数
                # (有时 backtrader 的日期可能是浮点数)
                log_dt_str = bt.num2date(dt_val).date().isoformat()
                # (将浮点数日期转换为标准格式。)
            else:
                log_dt_str = str(dt_val)  # 其他情况直接转字符串
                # (其他情况直接转字符串)

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
        # (这是策略刚被创建出来的时候要做的事情。)
        self.closes = {d._name: d.close for d in self.datas}
        self.opens = {d._name: d.open for d in self.datas}
        self.highs = {d._name: d.high for d in self.datas}
        self.lows = {d._name: d.low for d in self.datas}
        self.volumes = {d._name: d.volume for d in self.datas}

        self.emas_medium = {d._name: bt.indicators.EMA(
            d.close, period=self.params.ema_medium_period) for d in self.datas}
        self.emas_long = {d._name: bt.indicators.EMA(
            d.close, period=self.params.ema_long_period) for d in self.datas}
        self.adxs = {d._name: bt.indicators.ADX(
            d, period=self.params.adx_period) for d in self.datas}
        self.atrs = {d._name: bt.indicators.ATR(
            d, period=self.params.atr_period) for d in self.datas}  # 策略仍需ATR计算止损
        # (d, period=self.params.atr_period) for d in self.datas} # Strategy still needs ATR to calculate stop loss
        self.bbands = {d._name: bt.indicators.BollingerBands(
            d.close, period=self.params.bbands_period, devfactor=self.params.bbands_devfactor) for d in self.datas}
        self.rsis = {d._name: bt.indicators.RSI(
            d.close, period=self.params.rsi_period) for d in self.datas}
        self.highest_highs = {d._name: bt.indicators.Highest(
            d.high, period=self.params.trend_breakout_lookback) for d in self.datas}
        self.sma_volumes = {d._name: bt.indicators.SMA(
            d.volume, period=self.params.trend_volume_avg_period) for d in self.datas}

        self.orders = {d._name: None for d in self.datas}
        self.buy_prices = {d._name: None for d in self.datas}
        self.position_types = {d._name: None for d in self.datas}

        self.high_water_mark = self.broker.startingcash
        self.drawdown_level1_triggered = False
        self.halt_trading = False
        self.current_risk_multiplier = 1.0  # 策略控制风险乘数
        # self.current_risk_multiplier = 1.0 # Strategy controls risk multiplier

        # --- 新增：用于暂存待处理交易信息的字典 ---
        # (--- NEW: Dictionary to temporarily store pending trade info ---)
        self.pending_trade_info = {}
        # (创建一个叫 `self.pending_trade_info` 的空本子，用来在下单前临时存放交易计划信息，Sizer会从这里读取。)

    def notify_order(self, order):
        # 定义 `notify_order` 方法，当订单状态发生变化时由Backtrader调用。
        # (定义一个名叫 `notify_order` 的函数，每当订单有新情况时，`backtrader` 就会来告诉这个函数。)
        order_data_name = order.data._name if hasattr(
            order.data, '_name') else 'Unknown_Data'
        # 获取订单关联的数据源名称。
        # (看看这个订单是哪个股票的。)

        if order.status in [order.Submitted, order.Accepted]:
            # 如果订单状态是已提交 (Submitted) 或已接受 (Accepted)。
            # (如果订单已经发出去了或者交易所已经收到了。)
            self.log(
                f'订单 {order.ref} 已提交/接受 for {order_data_name}', data=order.data)
            # 记录订单提交/接受的日志。
            # (就记个日志说一下这个订单发出去了或者被接受了。)
            if order.parent is None:  # 主订单
                # (如果这个订单不是某个大订单里的小订单（是主订单）。)
                self.orders[order_data_name] = order
            # 将此订单存储在对应数据源的 `self.orders` 字典中。
            # (就把这个订单记在对应股票的 `self.orders` 本子里。)
            return
            # 从方法返回。
            # (这事儿处理完了。)

        # --- 清理 pending_trade_info ---
        # (--- Clean up pending_trade_info ---)
        # 订单处理完成或失败后，清理对应的待处理信息
        # (After order processing is complete or failed, clean up corresponding pending info)
        if order_data_name in self.pending_trade_info:
            # 如果这个ETF之前有待处理的交易计划。
            # (If this ETF had a pending trade plan before.)
            if not order.alive():  # 如果订单已结束（完成、取消、拒绝等）
                # (If the order is no longer alive (completed, canceled, rejected, etc.))
                self.log(
                    f'订单 {order.ref} 结束，清理 {order_data_name} 的 pending_trade_info', data=order.data)
                # (记个日志说订单结束了，把对应的交易计划清理掉。)
                del self.pending_trade_info[order_data_name]
                # (从 `pending_trade_info` 本子里删掉这个ETF的计划。)
            elif order.status in [order.Margin, order.Rejected]:  # 如果订单因保证金或被拒而失败
                # (If the order failed due to margin or rejection)
                self.log(
                    f'订单 {order.ref} 失败 ({order.getstatusname()}), 清理 {order_data_name} 的 pending_trade_info', data=order.data)
                # (记个日志说订单失败了，清理对应的交易计划。)
                del self.pending_trade_info[order_data_name]
                # (从 `pending_trade_info` 本子里删掉这个ETF的计划。)

        if order.status in [order.Completed]:
            # 如果订单状态是已完成。
            # (如果订单已经成功交易了。)
            if order.isbuy():
                # 如果是买入订单。
                # (如果这是一个买单。)
                self.log(
                    f'买入执行 for {order_data_name} @ {order.executed.price:.2f}, 数量: {order.executed.size}, 成本: {order.executed.value:.2f}, 佣金: {order.executed.comm:.2f}', data=order.data)
                # 记录买入执行的详细日志。
                # (就记个日志说买入成功了。)
                self.buy_prices[order_data_name] = order.executed.price
                # 将成交价格存储起来。
                # (把买入的价格记下来。)
            elif order.issell():
                # 如果是卖出订单。
                # (如果这是一个卖单。)
                self.log(
                    f'卖出执行 for {order_data_name} @ {order.executed.price:.2f}, 数量: {order.executed.size}, 价值: {order.executed.value:.2f}, 佣金: {order.executed.comm:.2f}', data=order.data)
                # 记录卖出执行的详细日志。
                # (就记个日志说卖出成功了。)

        elif order.status in [order.Canceled, order.Margin, order.Rejected, order.Expired]:
            # 如果订单状态是已取消、保证金不足、被拒绝或已过期。
            # (如果订单被取消了、或者因为钱不够、或者被交易所拒绝了、或者过期了。)
            self.log(
                f'订单 {order.ref} for {order_data_name} 取消/保证金/拒绝/过期: 状态 {order.getstatusname()}', data=order.data)
            # 记录订单未能成功执行的日志。
            # (就记个日志说这个订单没成功，具体是什么原因。)

        if self.orders.get(order_data_name) == order and not order.alive():
            # 如果 `self.orders` 中存储的是当前订单，并且当前订单不再存活。
            # (如果之前记在 `self.orders` 本子里的这个股票的订单就是现在这个订单，并且这个订单已经结束了。)
            self.orders[order_data_name] = None
            # 将 `self.orders` 中对应记录清除。
            # (就把 `self.orders` 本子里对应这个股票的记录清空。)

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
            f'交易利润 for {data_name}, 毛利 {trade.pnl:.2f}, 净利 {trade.pnlcomm:.2f}, 持仓类型: {self.position_types.get(data_name, "N/A")}', data=trade.data)
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
            if self.halt_trading:  # 如果之前是暂停状态，现在回撤低于二级线了
                # 如果之前是暂停交易状态。
                # (如果之前是暂停交易的状态。)
                self.log('--- 交易恢复 (回撤低于二级) ---')
                # 记录日志，说明交易已恢复 (因为回撤已低于二级阈值)。
                # (记个日志说交易恢复了，因为亏损已经回到二级线以下了。)
                self.halt_trading = False
                # 将 `halt_trading` 标志设置回 `False`。
                # (把暂停交易的开关关掉。)
                # 交易恢复后，检查是否需要恢复风险乘数
                # (After trading resumes, check if risk multiplier needs to be restored)
                if drawdown <= self.params.drawdown_level1_threshold:  # 如果同时也低于一级回撤
                    # 如果回撤也低于一级阈值。
                    # (如果亏损也回到了一级线以下。)
                    if self.drawdown_level1_triggered:  # 并且之前一级警报响过
                        # 如果一级回撤警报之前被触发过。
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
                elif self.drawdown_level1_triggered:  # 回撤在1级和2级之间，但交易已恢复
                    # 如果回撤在1级和2级之间，但交易已恢复（说明之前是halt_trading=True）
                    # (如果亏损在一级线和二级线之间，但交易已经恢复了（说明之前是暂停交易状态）)
                    self.current_risk_multiplier = 0.5  # 保持较低风险
                    # 风险乘数保持在0.5。
                    # (风险调整系数还是保持0.5。)

            elif self.drawdown_level1_triggered and drawdown <= self.params.drawdown_level1_threshold:
                # 如果之前一级回撤警报被触发过，且当前回撤已低于一级阈值 (且之前未暂停交易)。
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
                        f'暂停中: 尝试关闭 {d_name} 的仓位, 数量: {position.size}', data=d_obj)
                    # 记录日志，说明因交易暂停而尝试平仓。
                    # (记个日志说因为暂停交易了，要赶紧把手上的这只ETF卖掉。)
                    order_close = self.close(data=d_obj)
                    # 发出市价平仓订单。
                    # (下一个卖出指令，把这只ETF卖掉。)
                    if order_close:
                        # 如果成功创建平仓订单。
                        # (如果卖出指令成功发出去了。)
                        self.orders[d_name] = order_close  # 跟踪平仓单
                        # (就把这个卖单记在 `self.orders` 本子里。)
                    else:
                        # 如果未能创建平仓订单。
                        # (如果卖出指令没发出去。)
                        self.log(
                            f'暂停中: 无法为 {d_name} 创建平仓订单', data=d_obj)
                        # 记录日志，说明平仓失败。
                        # (记个日志说卖单没发出去。)
            return  # 暂停状态下不进行新的开仓检查
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

            # 如果有挂单，或已有持仓，或已有待处理交易信息，则跳过（避免重复处理）
            # (Skip if there's an active order, existing position, or pending trade info)
            if order or position.size != 0 or d_name in self.pending_trade_info:
                # (如果这只ETF有正在处理的订单，或者已经持有，或者已经有交易计划在Sizer处理中，就先跳过。)
                continue
                # (那就先不看它了，等处理完了再说。)

            # --- 策略核心逻辑：判断入场信号并计算风险信息 ---
            # (--- Core Strategy Logic: Check entry signals and calculate risk info ---)
            # (No position, check for entry)
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
            atr_val = self.atrs[d_name][0]  # 策略需要ATR来计算止损
            # atr_val = self.atrs[d_name][0] # Strategy needs ATR for stop loss calculation

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
                continue  # 指标数据不足
                # (Insufficient indicator data)

            entry_signal = False
            # 初始化入场信号为 `False`。
            # (先假设没有买入信号。)
            potential_position_type = None
            # 初始化潜在持仓类型为 `None`。
            # (先假设不知道要按什么类型买。)
            entry_price_calc = None  # 参考入场价
            # entry_price_calc = None # Reference entry price
            stop_loss_price_calc = None  # 止损价
            # stop_loss_price_calc = None # Stop loss price
            take_profit_price_calc = None  # 止盈价
            # take_profit_price_calc = None # Take profit price
            risk_per_share = None  # 每股风险
            # risk_per_share = None # Risk per share
            amount_to_risk = None  # 本次交易最大风险金额
            # amount_to_risk = None # Max risk amount for this trade

            # --- 趋势交易信号判断 ---
            # (--- Trend Trading Signal Check ---)
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
                        # 产生趋势信号，计算风险信息
                        # (Trend signal generated, calculate risk info)
                        entry_signal = True
                        # 设置入场信号为 `True`。
                        # (那就认为有买入信号了。)
                        potential_position_type = 'trend'
                        # 设置潜在持仓类型为 'trend'。
                        # (这次买入是按趋势型来操作的。)
                        entry_price_calc = current_close  # 以收盘价作为参考入场价
                        # entry_price_calc = current_close # Use close as reference entry price

                        if math.isnan(atr_val) or atr_val <= 1e-9:
                            self.log(
                                f"{d_name} ATR值无效 ({atr_val:.4f})，无法计算趋势止损。跳过。", data=d_obj)
                            # (Invalid ATR value ({atr_val:.4f}) for {d_name}, cannot calculate trend stop loss. Skipping.)
                            entry_signal = False  # 取消信号
                            # (Cancel signal)
                        else:
                            stop_loss_price_calc = entry_price_calc - \
                                self.p.trend_stop_loss_atr_mult * atr_val
                            # 计算止损价格。
                            # (Calculate stop loss price.)

                            if stop_loss_price_calc >= entry_price_calc:
                                self.log(
                                    f"{d_name} 趋势止损价 {stop_loss_price_calc:.2f} 不低于入场价 {entry_price_calc:.2f}。跳过。", data=d_obj)
                                # ({d_name} trend stop loss {stop_loss_price_calc:.2f} not below entry {entry_price_calc:.2f}. Skipping.)
                                entry_signal = False
                                # 取消入场信号。
                                # (那就不买了。)
                            else:
                                risk_per_share = entry_price_calc - stop_loss_price_calc
                                # 计算每股风险。
                                # (Calculate risk per share.)
                                if risk_per_share <= 1e-9:
                                    self.log(
                                        f"{d_name} 趋势交易每股风险过小 ({risk_per_share:.2f})。跳过。", data=d_obj)
                                    # ({d_name} trend trade risk per share too small ({risk_per_share:.2f}). Skipping.)
                                    entry_signal = False
                                    # 取消入场信号。
                                    # (那就不买了。)
                                else:
                                    take_profit_price_calc = entry_price_calc + \
                                        self.p.trend_take_profit_rratio * risk_per_share
                                    # 计算止盈价格。
                                    # (Calculate take profit price.)
                                    # 计算本次交易允许的最大风险金额
                                    # (Calculate max risk amount for this trade)
                                    risk_per_trade_percent = self.p.risk_per_trade_trend  # 使用策略参数
                                    # risk_per_trade_percent = self.p.risk_per_trade_trend # Use strategy param
                                    effective_risk_percent = risk_per_trade_percent * self.current_risk_multiplier
                                    # (Calculate effective risk percentage)
                                    amount_to_risk = self.broker.getvalue() * effective_risk_percent
                                    # (Calculate total amount to risk)
                except IndexError:
                    # 如果发生 `IndexError`。
                    # (如果数据不够出错了。)
                    continue  # 指标数据不足
                    # (Insufficient indicator data)

            # --- 区间交易信号判断 ---
            # (--- Range Trading Signal Check ---)
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
                        # 产生区间信号，计算风险信息
                        # (Range signal generated, calculate risk info)
                        entry_signal = True
                        # 设置入场信号为 `True`。
                        # (那就认为有买入信号了。)
                        potential_position_type = 'range'
                        # 设置潜在持仓类型为 'range'。
                        # (这次买入是按区间型来操作的。)
                        entry_price_calc = current_close  # 以收盘价作为参考入场价
                        # entry_price_calc = current_close # Use close as reference entry price
                        stop_loss_price_calc = current_low * \
                            (1 - self.p.range_stop_loss_buffer)
                        # 计算止损价格。
                        # (Calculate stop loss price.)

                        if stop_loss_price_calc >= entry_price_calc:
                            self.log(
                                f"{d_name} 区间止损价 {stop_loss_price_calc:.2f} 不低于入场价 {entry_price_calc:.2f}。跳过。", data=d_obj)
                            # ({d_name} range stop loss {stop_loss_price_calc:.2f} not below entry {entry_price_calc:.2f}. Skipping.)
                            entry_signal = False
                            # 取消入场信号。
                            # (那就不买了。)
                        else:
                            risk_per_share = entry_price_calc - stop_loss_price_calc
                            # 计算每股风险。
                            # (Calculate risk per share.)
                            if risk_per_share <= 1e-9:
                                self.log(
                                    f"{d_name} 区间交易每股风险过小 ({risk_per_share:.2f})。跳过。", data=d_obj)
                                # ({d_name} range trade risk per share too small ({risk_per_share:.2f}). Skipping.)
                                entry_signal = False
                                # 取消入场信号。
                                # (那就不买了。)
                            else:
                                take_profit_price_calc = bb_mid  # 区间止盈目标是中轨
                                # take_profit_price_calc = bb_mid # Range take profit target is mid band
                                # 计算本次交易允许的最大风险金额
                                # (Calculate max risk amount for this trade)
                                risk_per_trade_percent = self.p.risk_per_trade_range  # 使用策略参数
                                # risk_per_trade_percent = self.p.risk_per_trade_range # Use strategy param
                                effective_risk_percent = risk_per_trade_percent * self.current_risk_multiplier
                                # (Calculate effective risk percentage)
                                amount_to_risk = self.broker.getvalue() * effective_risk_percent
                                # (Calculate total amount to risk)
                except IndexError:
                    # 如果发生 `IndexError`。
                    # (如果数据不够出错了。)
                    continue  # 指标数据不足
                    # (Insufficient indicator data)

            # --- 如果有有效入场信号，则准备并下单 ---
            # (--- If valid entry signal, prepare and place order ---)
            if entry_signal and entry_price_calc is not None and \
               stop_loss_price_calc is not None and risk_per_share is not None and \
               amount_to_risk is not None and entry_price_calc > stop_loss_price_calc:
                # 检查所有必要信息是否都已计算完毕，并且入场价高于止损价
                # (Check if all necessary info has been calculated and entry price is above stop loss)
                if risk_per_share <= 1e-9 or amount_to_risk <= 1e-9:
                    self.log(
                        f"信号产生但风险计算无效 for {d_name} (Risk/Share: {risk_per_share:.4f}, AmountToRisk: {amount_to_risk:.2f})。跳过。", data=d_obj)
                    # (Signal generated but risk calculation invalid for {d_name}. Skipping.)
                    continue  # 跳过无效风险的信号
                    # (Skip signal with invalid risk)

                # --- 关键：将计算好的风险信息存入 pending_trade_info 供 Sizer 读取 ---
                # (--- Key: Store calculated risk info in pending_trade_info for Sizer to read ---)
                self.pending_trade_info[d_name] = {
                    'entry_price': entry_price_calc,
                    'stop_loss_price': stop_loss_price_calc,  # Sizer 可能不需要，但记录无妨
                    # 'stop_loss_price': stop_loss_price_calc, # Sizer might not need, but no harm storing
                    'risk_per_share': risk_per_share,
                    'amount_to_risk': amount_to_risk
                }
                # (把算好的买入价、止损价、每股风险、总风险金额都打包存到 `pending_trade_info` 本子里，用ETF名字做标签。)
                self.log(
                    f"为 {d_name} 准备交易信息: 入场={entry_price_calc:.2f}, 止损={stop_loss_price_calc:.2f}, 风险/股={risk_per_share:.4f}, 允许风险额={amount_to_risk:.2f}", data=d_obj)
                # (记个日志说交易计划准备好了。)

                # 设置括号单参数
                # (Set bracket order parameters)
                main_order_limit_price = entry_price_calc  # 主订单限价使用参考入场价
                # main_order_limit_price = entry_price_calc # Main order limit price uses reference entry price
                tp_price_for_bracket = None
                # (Initialize take profit price for bracket)
                if take_profit_price_calc is not None and take_profit_price_calc > main_order_limit_price:
                    tp_price_for_bracket = take_profit_price_calc
                # (If take profit is valid, use it)
                elif potential_position_type == 'trend' and take_profit_price_calc is not None:  # 只有当TP已计算但无效时才警告
                    # (Only warn if TP was calculated but is invalid)
                    self.log(
                        f"警告 for {d_name}: 趋势交易止盈价 {take_profit_price_calc:.2f} 无效 (不高于入场价 {main_order_limit_price:.2f})。括号单将无止盈限价单。", data=d_obj)
                    # (Warning for {d_name}: Trend trade TP price {take_profit_price_calc:.2f} invalid (not above entry {main_order_limit_price:.2f}). Bracket will have no limit sell for TP.)

                # 调用 buy_bracket，Sizer 会自动被调用来计算 size
                # (Call buy_bracket, Sizer will be called automatically to calculate size)
                self.log(
                    f"发出买入括号单信号 for {d_name}, 参考入场: {main_order_limit_price:.2f}, 止损: {stop_loss_price_calc:.2f}, 止盈: {tp_price_for_bracket if tp_price_for_bracket else 'N/A'}", data=d_obj)
                # (Log signal to place buy bracket order)
                bracket_orders_list = self.buy_bracket(
                    data=d_obj,
                    # size= REMOVED - Sizer will handle this
                    price=main_order_limit_price,  # 主单限价
                    # price=main_order_limit_price, # Main order limit price
                    exectype=bt.Order.Limit,
                    # (Set execution type to Limit)
                    stopprice=stop_loss_price_calc,  # 止损触发价 (由策略计算)
                    # stopprice=stop_loss_price_calc, # Stop trigger price (calculated by strategy)
                    limitprice=tp_price_for_bracket,  # 止盈限价 (由策略计算)
                    # limitprice=tp_price_for_bracket, # Limit price for take profit (calculated by strategy)
                )

                if bracket_orders_list and bracket_orders_list[0]:
                    # 如果成功创建了括号订单列表，并且列表中的第一个订单 (主订单) 存在。
                    # (If bracket order list created successfully and main order exists)
                    # self.orders[d_name] = bracket_orders_list[0] # notify_order 会处理
                    # (self.orders[d_name] = bracket_orders_list[0] # notify_order will handle)
                    # 记录持仓类型
                    self.position_types[d_name] = potential_position_type
                    # self.position_types[d_name] = potential_position_type # Record position type
                    self.log(
                        f"成功为 {d_name} 创建 buy_bracket 请求。主订单 ref: {bracket_orders_list[0].ref if bracket_orders_list[0] else 'N/A'}", data=d_obj)
                    # (Successfully created buy_bracket request for {d_name}. Main order ref: {bracket_orders_list[0].ref if bracket_orders_list[0] else 'N/A'})
                else:
                    # 如果未能成功创建括号订单 (例如Sizer返回0股，或发生错误)。
                    # (If failed to create bracket order (e.g., Sizer returned 0 or error))
                    self.log(
                        f"为 {d_name} 创建 buy_bracket 失败 (可能Sizer返回0或错误)", data=d_obj)
                    # (Failed to create buy_bracket for {d_name} (possibly sizer returned 0 or error))
                    # 如果下单失败，也需要清理 pending_trade_info
                    # (If order placement fails, also need to clean up pending_trade_info)
                    if d_name in self.pending_trade_info:
                        del self.pending_trade_info[d_name]
                        # (Remove pending info for this data name)


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
    loaded_data_count = 0  # 计数器，用于记录成功加载的数据数量
    for file_path in data_files:
        try:
            dataframe = pd.read_excel(file_path)
            dataframe.rename(columns=column_mapping, inplace=True)
            if 'datetime' in dataframe.columns:
                try:
                    dataframe['datetime'] = pd.to_datetime(
                        dataframe['datetime'])
                except Exception as e:
                    print(f"警告: 无法解析 {file_path} 中的日期时间列，请检查格式。错误: {e}")
                    continue
            else:
                print(
                    f"错误: 在 {file_path} 中找不到映射后的 'datetime' 列。请确保Excel文件中有正确的日期列，或正确修改脚本中的column_mapping。")
                print(f"Excel文件中的原始列名是: {dataframe.columns.tolist()}")
                continue
            dataframe.set_index('datetime', inplace=True)
            required_cols = ['open', 'high', 'low', 'close', 'volume']
            if not all(col in dataframe.columns for col in required_cols):
                print(f"错误: {file_path} 映射后缺少必需的列。")
                print(f"可用的列: {dataframe.columns.tolist()}")
                continue
            dataframe = dataframe.loc[fromdate:todate]

            if dataframe.empty:
                print(f"警告: {file_path} 在指定日期范围内没有数据。")
                continue  # 跳过空数据

            # 处理 openinterest 参数
            # (Handle openinterest parameter)
            oi_param_val = -1  # 默认值，表示不使用持仓量
            # (Default value, indicating open interest is not used)
            if isinstance(openinterest_col, str) and openinterest_col in dataframe.columns:
                oi_param_val = openinterest_col  # 如果是字符串且列存在，则使用列名
                # (If it's a string and the column exists, use the column name)
            elif isinstance(openinterest_col, str):  # 如果是字符串但列不存在，则警告
                # (If it's a string but the column doesn't exist, warn)
                print(
                    f"警告: 指定的 openinterest 列名 '{openinterest_col}' 在 {file_path} 中不存在。将忽略持仓量。")
                # (Warning: Specified openinterest column name '{openinterest_col}' does not exist in {file_path}. Open interest will be ignored.)
            elif isinstance(openinterest_col, int) and openinterest_col != -1:
                # 如果是整数索引 (backtrader PandasData 不直接支持整数索引作为列名，通常应为列名字符串或-1)
                # (If it's an integer index (backtrader PandasData doesn't directly support integer index as column name, should usually be column name string or -1))
                # 这种用法比较罕见且可能导致混淆，建议使用列名字符串
                # (This usage is rare and can be confusing, string column name is recommended)
                print(
                    f"警告: 为 openinterest 提供了整数索引 {openinterest_col}。如果意图是列名，请使用字符串。否则，行为可能未定义。")
                # (Warning: Integer index {openinterest_col} provided for openinterest. If column name was intended, use a string. Otherwise, behavior might be undefined.)
                oi_param_val = openinterest_col  # 谨慎使用
                # (Use with caution)

            data = bt.feeds.PandasData(dataname=dataframe, fromdate=fromdate, todate=todate, datetime=None,
                                       open='open', high='high', low='low', close='close', volume='volume',
                                       openinterest=oi_param_val)  # 使用处理后的 oi_param_val
            # openinterest=oi_param_val) # Use processed oi_param_val
            data_name = os.path.basename(file_path).split('.')[0]
            cerebro.adddata(data, name=data_name)
            print(f"数据加载成功: {data_name}")
            loaded_data_count += 1  # 增加成功加载的计数

        except FileNotFoundError:
            print(f"错误: 文件未找到 {file_path}")
        except Exception as e:
            print(f"加载数据 {file_path} 时出错: {e}")
            import traceback
            traceback.print_exc()  # 打印详细错误堆栈
            # traceback.print_exc() # Print detailed error stack trace
    return loaded_data_count


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
                            bbands_period=bbands_period_range,
                            bbands_devfactor=bbands_dev_range,
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
        results = cerebro.run(maxcpus=1)
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
