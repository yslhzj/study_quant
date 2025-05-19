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


# --- 配置区 (Configuration Function) ---
def get_backtest_config():
    """
    返回包含所有回测配置的字典。
    Returns a dictionary containing all backtest configurations.
    """
    config = {
        # --- 常规设置 (General Settings) ---
        'optimize': False,  # 设置为True进行参数优化，False进行单次回测
        # optimize: False,  # Set to True to perform parameter optimization, False for a single backtest run.
        'initial_cash': 500000.0,  # 初始资金 (Initial cash)
        'commission_rate': 0.0003,  # 佣金率 (Commission rate)
        'data_files': [
            r'D:\BT2025\datas\510050_d.xlsx',
            r'D:\BT2025\datas\510300_d.xlsx',
            r'D:\BT2025\datas\159949_d.xlsx'
        ],  # 数据文件路径列表 (List of data file paths)
        'column_mapping': {
            'date': 'datetime', 'open': 'open', 'high': 'high',
            'low': 'low', 'close': 'close', 'volume': 'volume'
        },  # 列名映射 (Column name mapping)
        'openinterest_col': -1,  # 持仓量列索引 (-1表示无) (Open interest column index)
        # 回测起始日期 (Backtest start date)
        'fromdate': datetime.datetime(2015, 1, 1),
        'todate': datetime.datetime(2024, 4, 30),  # 回测结束日期 (Backtest end date)

        # --- 优化参数范围 (Optimization Parameter Ranges) ---
        'ema_medium_range': range(40, 81, 10),
        'ema_long_range': range(100, 141, 10),
        'bbands_period_range': range(15, 26, 5),
        'bbands_dev_range': [1.8, 2.0, 2.2],

        # --- 单次回测固定参数 (Single Backtest Fixed Parameters) ---
        'ema_medium_period_fixed': 60,
        'ema_long_period_fixed': 120,
        'bbands_period_fixed': 20,
        'bbands_devfactor_fixed': 2.0,
        # 'risk_per_trade_percent_fixed': 0.01, # 可以在策略参数中默认，或在这里传递
        # 'allow_short_fixed': False
    }
    return config
# ===================================================================================


class AShareETFStrategy(bt.Strategy):
    # 定义一个名为AShareETFStrategy的类，它继承自bt.Strategy，表示这是一个Backtrader交易策略类。 (创建一个叫做AShareETFStrategy的策略类，它继承了bt.Strategy，说明这是个交易策略。)
    params = (
        ('etf_type', 'trend'),
        # 定义策略参数etf_type，默认值为'trend'，用于指定ETF类型为趋势型或震荡型。 (设置策略的参数etf_type，默认是'trend'，用来区分ETF是趋势型的还是震荡型的。)
        ('ema_medium_period', 60),
        # 定义中期EMA均线的周期参数ema_medium_period，默认值为60，表示计算60日EMA。 (设置中期EMA均线的周期为60天，EMA就是指数移动平均线，用来看价格 среднесрочный 趋势。)
        ('ema_long_period', 120),
        # 定义长期EMA均线的周期参数ema_long_period，默认值为120，表示计算120日EMA。 (设置长期EMA均线的周期为120天，长期EMA看得更长远。)
        ('adx_period', 14),
        # 定义ADX指标的周期参数adx_period，默认值为14，表示计算14日ADX。 (设置ADX指标的周期为14天，ADX是平均趋向指数，用来判断趋势强弱。)
        ('atr_period', 20),
        # 定义ATR指标的周期参数atr_period，默认值为20，表示计算20日ATR。 (设置ATR指标的周期为20天，ATR是平均真实波幅，用来衡量价格波动大小。)
        ('bbands_period', 20),
        # 定义布林带的周期参数bbands_period，默认值为20，表示布林带基于20日均线计算。 (设置布林带的周期为20天，布林带是通道指标，由中轨、上轨和下轨组成。)
        ('bbands_devfactor', 2.0),
        # 定义布林带的标准差倍数参数bbands_devfactor，默认值为2.0，用于计算布林带上下轨。 (设置布林带的标准差倍数为2.0，这个数值决定了布林带通道的宽度。)
        ('rsi_period', 14),
        # 定义RSI指标的周期参数rsi_period，默认值为14，表示计算14日RSI。 (设置RSI指标的周期为14天，RSI是相对强弱指数，用来判断买卖力量对比。)
        ('rsi_oversold', 30),
        # 定义RSI超卖阈值参数rsi_oversold，默认值为30，当RSI低于30时视为超卖。 (设置RSI超卖线为30，RSI低于30就认为是卖超了，可能要反弹。)
        ('trend_breakout_lookback', 60),
        # 定义趋势突破策略的回顾期参数trend_breakout_lookback，默认值为60，用于寻找近60日最高价。 (设置趋势突破策略的回看期为60天，用来找最近60天里的最高价，判断是否突破。)
        ('trend_volume_avg_period', 20),
        # 定义趋势策略中成交量均线周期参数trend_volume_avg_period，默认值为20，计算20日成交量均线。 (设置趋势策略里成交量均线的周期为20天，算平均成交量。)
        ('trend_volume_ratio_min', 1.1),
        # 定义趋势突破时成交量最小放大倍数参数trend_volume_ratio_min，默认值为1.1，表示突破时成交量至少是均线的1.1倍。 (设置趋势突破时成交量要放大到至少平均成交量的1.1倍，才算有效突破。)
        ('trend_stop_loss_atr_mult', 2.5),
        # 定义趋势策略止损ATR倍数参数trend_stop_loss_atr_mult，默认值为2.5，止损价设置为入场价减去2.5倍ATR。 (设置趋势策略的止损，亏损幅度是ATR的2.5倍，ATR越大，止损越远。)
        ('trend_take_profit_rratio', 2.0),
        # 定义趋势策略盈亏比参数trend_take_profit_rratio，默认值为2.0，止盈目标是风险的2倍。 (设置趋势策略的止盈目标，期望盈利是止损风险的2倍。)
        ('range_stop_loss_buffer', 0.005),
        # 定义震荡策略止损缓冲比例参数range_stop_loss_buffer，默认值为0.005，止损价设置在最低价下方0.5%。 (设置震荡策略的止损缓冲比例为0.5%，止损价要比最低价再低一点点，防止假突破。)
        ('max_risk_per_trade_trend', 0.01),
        # 定义趋势策略单笔最大风险参数max_risk_per_trade_trend，默认值为0.01，表示单笔交易最大亏损不超过总资金的1%。 (设置趋势策略单次交易最大亏损不能超过总资金的1%，控制风险。)
        ('max_risk_per_trade_range', 0.005),
        # 定义震荡策略单笔最大风险参数max_risk_per_trade_range，默认值为0.005，表示单笔交易最大亏损不超过总资金的0.5%。 (设置震荡策略单次交易最大亏损不能超过总资金的0.5%，震荡策略风险更小。)
        ('max_position_per_etf_percent', 0.30),
        # 定义单个ETF最大仓位比例参数max_position_per_etf_percent，默认值为0.30，表示单个ETF持仓市值不超过总资金的30%。 (设置单个ETF最多只能买总资金的30%，防止All in one ETF。)
        ('max_total_account_risk_percent', 0.06),
        # 定义账户总风险上限参数max_total_account_risk_percent，默认值为0.06，表示账户总风险不超过总资金的6%。 (设置整个账户的最大风险承受能力，最多亏损不能超过总资金的6%。)
        ('drawdown_level1_threshold', 0.05),
        # 定义一级回撤阈值参数drawdown_level1_threshold，默认值为0.05，当回撤超过5%时触发一级警报。 (设置一级回撤警戒线为5%，亏损超过5%就发出黄色警报。)
        ('drawdown_level2_threshold', 0.10),
        # 定义二级回撤阈值参数drawdown_level2_threshold，默认值为0.10，当回撤超过10%时触发二级警报并可能暂停交易。 (设置二级回撤警戒线为10%，亏损超过10%就发出红色警报，甚至暂停交易。)
    )

    def log(self, txt, dt=None, data=None):
        return
        # 定义一个名为log的函数，用于记录日志信息，参数txt是日志文本，dt是日期时间，data是数据对象。 (定义一个日志记录函数，叫log，用来在程序运行的时候写日记。)
        # return  # 注释掉return以启用日志记录 <----- Remove this line or comment it out
        _data = data if data is not None else (
            self.datas[0] if self.datas else None)
        # 如果传入了data参数，则使用data，否则尝试使用self.datas[0]（第一个数据源），再否则设为None。 (判断有没有提供数据，有就用提供的数据，没有就用第一个数据，再没有就啥也不用。)
        if _data:
            # 检查_data是否为真（即是否成功获取了数据对象）。 (判断有没有拿到数据。)
            dt = dt or _data.datetime.date(0)
            # 如果传入了dt参数，则使用dt，否则从_data中获取日期。 (判断有没有提供日期，有就用提供的日期，没有就从数据里取日期。)
            prefix = f"[{_data._name}] " if hasattr(
                _data, '_name') and _data._name else ""  # 确保_data._name存在且不为空
            # 如果_data对象有_name属性，则创建带数据名称的前缀，否则前缀为空。 (判断数据有没有名字，有名字就加上名字前缀，没名字就啥也不加。)
            print(f"{dt.isoformat()} {prefix}{txt}")
            # 打印格式化的日志信息，包括日期、前缀和日志文本。 (把日期、前缀、日志内容拼起来，然后打印出来，就像写日记一样。)
        else:
            # 如果没有数据对象。 (如果啥数据都没拿到。)
            print(txt)
            # 直接打印日志文本，不包含日期和数据名称前缀。 (那就只打印日志内容，日期和数据名字就没了。)

    def __init__(self, **kwargs):  # 接受 **kwargs 以兼容 addstrategy 传递的参数
        # 定义策略的初始化函数__init__，在策略对象创建时自动执行。
        # (Define the initialization function __init__, executed automatically when the strategy object is created.)
        # (Accept **kwargs to be compatible with parameters passed by addstrategy)
        # 引用数据源。
        # Reference the data feeds.
        self.closes = [d.close for d in self.datas]
        # 创建一个列表self.closes，存储每个数据源的收盘价序列。 (创建一个列表，用来放每个ETF的收盘价数据，收盘价是最重要的价格数据。)
        self.opens = [d.open for d in self.datas]
        # 创建一个列表self.opens，存储每个数据源的开盘价序列。 (创建一个列表，用来放每个ETF的开盘价数据，开盘价是每天交易的第一个价格。)
        self.highs = [d.high for d in self.datas]
        # 创建一个列表self.highs，存储每个数据源的最高价序列。 (创建一个列表，用来放每个ETF的最高价数据，一天中最高的成交价。)
        self.lows = [d.low for d in self.datas]
        # 创建一个列表self.lows，存储每个数据源的最低价序列。 (创建一个列表，用来放每个ETF的最低价数据，一天中最低的成交价。)
        self.volumes = [d.volume for d in self.datas]
        # 创建一个列表self.volumes，存储每个数据源的成交量序列。 (创建一个列表，用来放每个ETF的成交量数据，成交量表示交易的活跃程度。)

        self.emas_medium = []
        # 初始化一个空列表self.emas_medium，用于存储中期EMA指标。 (创建一个空列表，用来存放中期EMA指标的计算结果。)
        self.emas_long = []
        # 初始化一个空列表self.emas_long，用于存储长期EMA指标。 (创建一个空列表，用来存放长期EMA指标的计算结果。)
        self.adxs = []
        # 初始化一个空列表self.adxs，用于存储ADX指标。 (创建一个空列表，用来存放ADX指标的计算结果。)
        self.atrs = []
        # 初始化一个空列表self.atrs，用于存储ATR指标。 (创建一个空列表，用来存放ATR指标的计算结果。)
        self.bbands = []
        # 初始化一个空列表self.bbands，用于存储布林带指标。 (创建一个空列表，用来存放布林带指标的计算结果。)
        self.rsis = []
        # 初始化一个空列表self.rsis，用于存储RSI指标。 (创建一个空列表，用来存放RSI指标的计算结果。)
        self.highest_highs = []
        # 初始化一个空列表self.highest_highs，用于存储近期最高价指标。 (创建一个空列表，用来存放近期最高价指标的计算结果。)
        self.sma_volumes = []
        # 初始化一个空列表self.sma_volumes，用于存储成交量均线指标。 (创建一个空列表，用来存放成交量均线指标的计算结果。)

        # 为每个数据源计算所需的指标
        # Loop through each data feed (ETF) to calculate necessary indicators
        for i, d in enumerate(self.datas):
            # 遍历每个数据源，i是索引，d是数据对象。 (循环处理每个ETF的数据，i是第几个ETF，d是ETF的数据。)
            self.emas_medium.append(bt.indicators.EMA(
                self.closes[i], period=self.params.ema_medium_period))
            # 为当前数据源计算中期EMA，并添加到self.emas_medium列表。 (计算当前ETF的中期EMA，然后放到列表中。)
            self.emas_long.append(bt.indicators.EMA(
                self.closes[i], period=self.params.ema_long_period))
            # 为当前数据源计算长期EMA，并添加到self.emas_long列表。 (计算当前ETF的长期EMA，然后放到列表中。)
            self.adxs.append(bt.indicators.ADX(
                d, period=self.params.adx_period))
            # 为当前数据源计算ADX指标，并添加到self.adxs列表。 (计算当前ETF的ADX指标，然后放到列表中。)
            self.atrs.append(bt.indicators.ATR(
                d, period=self.params.atr_period))
            # 为当前数据源计算ATR指标，并添加到self.atrs列表。 (计算当前ETF的ATR指标，然后放到列表中。)
            self.bbands.append(bt.indicators.BollingerBands(
                self.closes[i], period=self.params.bbands_period, devfactor=self.params.bbands_devfactor))
            # 为当前数据源计算布林带指标，并添加到self.bbands列表。 (计算当前ETF的布林带指标，然后放到列表中。)
            self.rsis.append(bt.indicators.RSI(
                self.closes[i], period=self.params.rsi_period))
            # 为当前数据源计算RSI指标，并添加到self.rsis列表。 (计算当前ETF的RSI指标，然后放到列表中。)
            self.highest_highs.append(bt.indicators.Highest(
                self.highs[i], period=self.params.trend_breakout_lookback))
            # 为当前数据源计算近期最高价指标，并添加到self.highest_highs列表。 (计算当前ETF的近期最高价指标，然后放到列表中。)
            self.sma_volumes.append(bt.indicators.SMA(
                self.volumes[i], period=self.params.trend_volume_avg_period))
            # 为当前数据源计算成交量均线指标，并添加到self.sma_volumes列表。 (计算当前ETF的成交量均线指标，然后放到列表中。)

        # 初始化订单和交易状态跟踪字典
        # Initialize dictionaries to track orders and trade states
        self.orders = {d: None for d in self.datas}
        # 创建一个字典self.orders，用于存储每个数据源的订单信息，初始值设为None。 (创建一个字典，用来记录每个ETF的订单状态，刚开始都没有订单，所以设为None。)
        self.buy_prices = {d: None for d in self.datas}
        # 创建一个字典self.buy_prices，用于存储每个数据源的买入价格，初始值设为None。 (创建一个字典，用来记录每个ETF的买入价格，初始时没有买入，所以设为None。)
        self.buy_comms = {d: None for d in self.datas}
        # 创建一个字典self.buy_comms，用于存储每个数据源的买入佣金，初始值设为None。 (创建一个字典，用来记录每个ETF的买入手续费，初始时没有买入，所以设为None。)
        self.stop_loss_prices = {d: None for d in self.datas}
        # 创建一个字典self.stop_loss_prices，用于存储每个数据源的止损价格，初始值设为None。 (创建一个字典，用来记录每个ETF的止损价格，初始时没有止损价，所以设为None。)
        self.take_profit_prices = {d: None for d in self.datas}
        # 创建一个字典self.take_profit_prices，用于存储每个数据源的止盈价格，初始值设为None。 (创建一个字典，用来记录每个ETF的止盈价格，初始时没有止盈价，所以设为None。)
        self.position_types = {d: None for d in self.datas}
        # 创建一个字典self.position_types，用于存储每个数据源的持仓类型，初始值设为None。 (创建一个字典，用来记录每个ETF的持仓类型，初始时没有持仓，所以设为None。)

        # 初始化风险管理相关变量
        # Initialize risk management related variables
        self.high_water_mark = 0
        # 初始化账户净值的历史最高点self.high_water_mark为0。 (初始化账户净值的最高纪录为0，就像新开账户，历史最高盈利是0。)
        self.drawdown_level1_triggered = False
        # 初始化一级回撤警报触发状态self.drawdown_level1_triggered为False。 (初始化一级回撤警报状态为未触发，刚开始肯定没亏损到警戒线。)
        self.halt_trading = False
        # 初始化交易暂停状态self.halt_trading为False。 (初始化交易暂停状态为未暂停，刚开始肯定是可以交易的。)
        self.current_risk_multiplier = 1.0
        # 初始化当前风险乘数self.current_risk_multiplier为1.0。 (初始化当前风险系数为1，正常情况下风险系数是1。)

    def notify_order(self, order):
        # 定义订单状态通知函数notify_order，当订单状态发生变化时被调用，参数order是订单对象。 (定义订单通知函数，当订单状态变化的时候，程序会跑这个函数来通知你。)
        order_data = order.data
        # 获取与订单关联的数据源。 (拿到这个订单是哪个ETF的。)
        data_name = order_data._name if hasattr(
            order_data, '_name') else 'Unknown Data'
        # 获取数据名称，如果不存在则为'Unknown Data'。 (获取这个ETF的名字，如果没名字就叫'Unknown Data'。)

        if order.status in [order.Submitted, order.Accepted]:
            # 检查订单状态是否为已提交或已接受。 (判断订单是不是刚提交或者刚被券商接受。)
            self.log(f'Order {order.ref} Submitted/Accepted', data=order_data)
            # 记录订单提交或接受的日志。 (记录一下订单提交/接受了。)
            return
            # 如果订单状态是已提交或已接受，则直接返回，不做进一步处理。 (如果是刚提交或者刚被接受，那就啥也不干，等着后续状态变化。)

        if order.status in [order.Completed]:
            # 检查订单状态是否为已完成（成交）。 (判断订单是不是已经成交了。)
            if order.isbuy():
                # 检查已完成的订单是否为买入订单。 (判断成交的订单是不是买入单。)
                self.log(
                    f'BUY EXECUTED @ {order.executed.price:.2f}, Size: {order.executed.size}, Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}', data=order_data)
                # 记录买入成交的日志，包括成交价格、数量、总成本和佣金。 (记录买入成功的日志，包括成交价格、买了多少股、花了多少钱、手续费多少。)
                self.buy_prices[order_data] = order.executed.price
                # 更新当前数据源的买入价格为成交价。 (把当前ETF的买入价格更新为成交价。)
                self.buy_comms[order_data] = order.executed.comm
                # 更新当前数据源的买入佣金为成交佣金。 (把当前ETF的买入手续费更新为实际手续费。)
                # 查找关联的括号订单，并记录止损止盈价
                # Find associated bracket orders and record stop-loss/take-profit prices
                if hasattr(order, 'parent') and order.parent:  # 检查是否有父订单
                    pass  # 主订单成交不直接处理括号订单，等broker处理
                elif hasattr(order, 'transmit') and order.transmit is False:  # 主买单可能是未transmit的
                    pass
                # 简单的逻辑：假设成交后马上设置SL/TP，实际需要更复杂的逻辑跟踪bracket order状态
                # Find stop loss and take profit orders associated with this buy order
                # This needs a robust way to link bracket orders; using tradeid might be one way if set properly.
                # For simplicity, we might have stored intended SL/TP prices when creating the order.
                # Let's assume we stored them temporarily or can retrieve from bracket logic
                # stop_price = self.stop_loss_prices.get(order_data) # Need to retrieve correctly
                # take_profit = self.take_profit_prices.get(order_data) # Need to retrieve correctly
                # self.log(f' Associated SL: {stop_price}, TP: {take_profit}', data=order_data)

            elif order.issell():
                # 检查已完成的订单是否为卖出订单。 (判断成交的订单是不是卖出单。)
                self.log(
                    f'SELL EXECUTED @ {order.executed.price:.2f}, Size: {order.executed.size}, Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}', data=order_data)
                # 记录卖出成交的日志，包括成交价格、数量、总价值和佣金。 (记录卖出成功的日志，包括成交价格、卖了多少股、卖了多少钱、手续费多少。)
                # 清理买入信息和止损止盈价格
                # Clear buy information and stop-loss/take-profit prices
                self.buy_prices[order_data] = None
                self.buy_comms[order_data] = None
                self.stop_loss_prices[order_data] = None
                self.take_profit_prices[order_data] = None
                self.position_types[order_data] = None

            self.bar_executed = len(order_data)
            # 记录订单执行时的数据索引（K线索引）。 (记录这笔交易是在第几根K线成交的。)

        elif order.status in [order.Canceled, order.Margin, order.Rejected, order.Expired]:
            # 检查订单状态是否为已取消、保证金不足、被拒绝或已过期。 (判断订单是不是被取消了、钱不够买、或者被券商拒绝了、或者过期了。)
            self.log(
                f'Order {order.ref} Canceled/Margin/Rejected/Expired: Status {order.getstatusname()}', data=order_data)
            # 记录订单取消、保证金不足、被拒绝或过期的日志，包含订单状态名称。 (记录订单失败的日志，说明订单被取消、钱不够、被拒绝或过期了，并说明具体原因。)

        # 不论订单状态如何，只要不是 PENDING 状态，就清除订单引用
        # Regardless of the order status, clear the order reference if it's no longer pending
        if order_data in self.orders and self.orders[order_data] is order:
            # 检查订单数据源是否在self.orders字典中，并且当前订单是记录的订单。 (确保这个订单对应的ETF在我们记录的订单列表里，并且就是这个订单。)
            self.orders[order_data] = None
            # 重置当前数据源的订单状态为None，表示没有活动的挂单了。 (把当前ETF的订单状态清空，表示现在没有挂单了。)

    def notify_trade(self, trade):
        # 定义交易通知函数notify_trade，当交易（一买一卖）完成时被调用，参数trade是交易对象。 (定义交易完成通知函数，当一次完整的买卖结束了，程序会跑这个函数来通知你。)
        if not trade.isclosed:
            # 检查交易是否已经关闭。 (判断这笔交易是不是已经结束了，比如买入后又卖出了。)
            return
            # 如果交易未关闭，则直接返回，不做进一步处理。 (如果交易还没结束，比如只买了还没卖，那就啥也不干，等着交易结束。)
        data_name = trade.data._name if hasattr(
            trade.data, '_name') else 'Unknown Data'
        # 获取数据名称。 (获取这个ETF的名字。)
        self.log(
            f'OPERATION PROFIT, GROSS {trade.pnl:.2f}, NET {trade.pnlcomm:.2f}, Position Type: {self.position_types.get(trade.data, "N/A")}', data=trade.data)
        # 记录交易的利润日志，包括毛利润、净利润和持仓类型。 (记录这次交易赚了多少钱，包括毛利润、扣掉手续费的净利润，以及是按哪种策略做的。)

        # 交易关闭后，清理相关状态
        # After a trade is closed, clear related states
        if trade.data in self.position_types:
            # 检查交易数据源是否在self.position_types字典中。 (确保这个交易对应的ETF在我们记录的持仓类型列表里。)
            self.position_types[trade.data] = None
            # 重置当前数据源的持仓类型为None。 (把当前ETF的持仓类型清空。)
        if trade.data in self.buy_prices:
            # 检查交易数据源是否在self.buy_prices字典中。 (确保这个交易对应的ETF在我们记录的买入价格列表里。)
            self.buy_prices[trade.data] = None
            # 重置当前数据源的买入价格为None。 (把当前ETF的买入价格清空。)
        if trade.data in self.buy_comms:
            # 检查交易数据源是否在self.buy_comms字典中。 (确保这个交易对应的ETF在我们记录的买入手续费列表里。)
            self.buy_comms[trade.data] = None
            # 重置当前数据源的买入佣金为None。 (把当前ETF的买入手续费清空。)
        if trade.data in self.stop_loss_prices:
            # 检查交易数据源是否在self.stop_loss_prices字典中。 (确保这个交易对应的ETF在我们记录的止损价格列表里。)
            self.stop_loss_prices[trade.data] = None
            # 重置当前数据源的止损价格为None。 (把当前ETF的止损价格清空。)
        if trade.data in self.take_profit_prices:
            # 检查交易数据源是否在self.take_profit_prices字典中。 (确保这个交易对应的ETF在我们记录的止盈价格列表里。)
            self.take_profit_prices[trade.data] = None
            # 重置当前数据源的止盈价格为None。 (把当前ETF的止盈价格清空。)

    def notify_cashvalue(self, cash, value):
        # 定义现金和总价值通知函数notify_cashvalue，在账户现金或总价值更新时被调用，参数cash是当前现金，value是当前总价值。 (定义现金和总资产值通知函数，当账户里的钱或者总资产变化的时候，程序会跑这个函数来通知你。)
        self.high_water_mark = max(self.high_water_mark, value)
        # 更新账户净值历史最高点，取当前总价值和历史最高点的较大值。 (更新账户净值的最高纪录，看看现在是不是比以前赚得更多了。)
        drawdown = (self.high_water_mark - value) / \
            self.high_water_mark if self.high_water_mark > 0 else 0
        # 计算当前的回撤比例，即从历史最高点下跌的百分比。 (计算当前亏损的比例，就是看看现在比历史最高点亏了多少百分比。)

        if drawdown > self.params.drawdown_level2_threshold:
            # 检查当前回撤是否超过二级回撤阈值。 (判断当前亏损比例是不是超过了二级警戒线，比如10%。)
            if not self.halt_trading:
                # 检查当前是否未暂停交易。 (判断现在是不是还没暂停交易。)
                # 全局信息，不关联特定data
                self.log(
                    f'!!! RED ALERT: Drawdown {drawdown*100:.2f}% > {self.params.drawdown_level2_threshold*100:.0f}%. HALTING TRADING !!!', data=None)
                # 记录二级回撤警报日志，并宣布暂停交易。 (记录红色警报日志，提示亏损太多了，要暂停交易了。)
                self.halt_trading = True
                # 设置交易暂停状态为True。 (把暂停交易的开关打开，后面就不能再买卖了。)
        elif drawdown > self.params.drawdown_level1_threshold:
            # 检查当前回撤是否超过一级回撤阈值，但未超过二级阈值。 (判断当前亏损比例是不是超过了一级警戒线，比如5%，但还没到二级警戒线。)
            if not self.drawdown_level1_triggered:
                # 检查一级回撤警报是否尚未触发。 (判断是不是还没触发过黄色警报。)
                self.log(
                    f'-- YELLOW ALERT: Drawdown {drawdown*100:.2f}% > {self.params.drawdown_level1_threshold*100:.0f}%. Reducing risk.--', data=None)  # 全局信息
                # 记录一级回撤警报日志，提示降低风险。 (记录黄色警报日志，提示亏损有点多了，要降低风险了。)
                self.drawdown_level1_triggered = True
                # 设置一级回撤警报触发状态为True。 (把触发黄色警报的标记设为真，下次再亏损就不用重复报警了。)
                self.current_risk_multiplier = 0.5
                # 将风险乘数降低为0.5，降低后续交易的仓位大小。 (把风险系数降低一半，下次买的时候少买点，控制风险。)
        else:
            # 如果回撤未超过一级阈值，表示回撤已恢复或未达到警报级别。 (如果亏损没那么多了，低于黄色警戒线了。)
            if self.halt_trading:
                # 检查之前是否处于暂停交易状态。 (判断之前是不是暂停了交易。)
                self.log('--- Trading Resumed ---', data=None)  # 全局信息
                # 记录交易恢复日志。 (记录交易恢复的日志，提示又可以开始交易了。)
                self.halt_trading = False
                # 重置交易暂停状态为False。 (把暂停交易的开关关掉，恢复正常交易。)
            if self.drawdown_level1_triggered:
                # 检查之前是否触发过一级回撤警报。 (判断之前是不是触发过黄色警报。)
                self.log('--- Risk Level Restored ---', data=None)  # 全局信息
                # 记录风险水平恢复日志。 (记录风险水平恢复正常的日志，提示风险又回到正常水平了。)
                self.drawdown_level1_triggered = False
                # 重置一级回撤警报触发状态为False。 (把触发黄色警报的标记设为假，表示现在风险正常了。)
                self.current_risk_multiplier = 1.0
                # 将风险乘数恢复为1.0。 (把风险系数恢复到正常的1，下次交易又可以按正常仓位买了。)

    def _calculate_trade_size(self, data_close_price, entry_price, stop_loss_price, risk_per_trade_percent, data=None):
        # 定义一个私有方法_calculate_trade_size，用于计算交易仓位大小，根据风险管理规则。 (定义一个计算交易仓位大小的小工具，根据风险控制规则来算。)
        data_name = data._name if hasattr(data, '_name') else 'Unknown Data'
        # 获取数据名称。 (获取这个ETF的名字。)

        if stop_loss_price >= entry_price:
            # 检查止损价是否大于等于入场价。 (判断止损价是不是比买入价还高，止损价应该比买入价低才对。)
            self.log(
                f"Stop loss price {stop_loss_price:.2f} is not below entry price {entry_price:.2f}. Cannot calculate size.", data=data)
            # 记录错误日志，提示止损价不低于入场价，无法计算仓位。 (记录错误日志，说止损价有问题，没法算买多少股。)
            return 0
            # 如果止损价不低于入场价，则返回0，表示无法交易。 (如果止损价有问题，那就返回0，表示这次不买了。)

        risk_per_share = entry_price - stop_loss_price
        # 计算每股的风险金额，即入场价减去止损价。 (计算每股会亏多少钱，就是买入价减去止损价。)
        if risk_per_share <= 0:
            # 防止除以零或负数风险，检查每股风险是否小于等于0。 (防止计算出错，判断每股风险是不是小于等于0，正常情况下应该是大于0的。)
            self.log(
                f"Calculated risk per share is zero or negative ({risk_per_share:.2f}). Cannot calculate size.", data=data)
            # 记录错误日志，提示每股风险为零或负数，无法计算仓位。 (记录错误日志，说每股风险有问题，没法算买多少股。)
            return 0
            # 如果每股风险小于等于0，则返回0，表示无法交易。 (如果每股风险有问题，那就返回0，表示这次不买了。)

        effective_risk_percent = risk_per_trade_percent * self.current_risk_multiplier
        # 计算有效的单笔交易风险比例，考虑当前的风险乘数。 (计算实际承担的风险比例，要考虑当前的风险系数。)
        cash = self.broker.get_cash()
        # 获取当前账户的可用现金。 (看看现在账户里有多少现金可以用。)
        equity = self.broker.get_value()
        # 获取当前账户的总净值（现金+持仓市值）。 (看看现在账户里总共有多少钱，包括现金和股票。)

        # 检查账户总风险
        # Check total account risk
        total_current_risk = 0
        # 初始化当前账户总风险为0。 (初始化当前账户的总风险为0。)
        for d, pos in self.broker.positions.items():
            # 遍历所有持仓。 (检查现在手里持有的所有ETF。)
            if pos.size != 0 and d in self.stop_loss_prices and self.stop_loss_prices[d] is not None and d in self.buy_prices and self.buy_prices[d] is not None:
                # 如果有持仓且记录了止损价。 (如果持有这只ETF，并且设置了止损价。)
                initial_buy_price = self.buy_prices[d]
                sl_price = self.stop_loss_prices[d]
                risk_per_share_original = initial_buy_price - sl_price  # Assuming long only

                if risk_per_share_original > 0:
                    total_current_risk += abs(pos.size) * \
                        risk_per_share_original
                else:
                    # Log if original risk calculation is problematic (should not happen if SL is below buy price)
                    self.log(
                        f"Warning: Original risk per share for existing position {d._name} is non-positive ({risk_per_share_original:.2f}). Buy: {initial_buy_price:.2f}, SL: {sl_price:.2f}", data=d)

        # 简化计算，以目标风险金额作为潜在新风险
        potential_new_risk = (equity * effective_risk_percent)
        # 计算潜在新交易的风险金额。 (计算这次交易打算承担的风险金额。)
        if (total_current_risk + potential_new_risk) / equity > self.params.max_total_account_risk_percent:
            # 检查加入新交易后，总风险是否超过账户总风险上限。 (判断如果加上这次交易的风险，会不会超过整个账户能承受的最大风险。)
            self.log(
                f"Trade skipped due to exceeding max total account risk limit. Current risk: {(total_current_risk/equity)*100:.2f}%, New trade risk: {effective_risk_percent*100:.2f}%, Limit: {self.params.max_total_account_risk_percent*100:.2f}%", data=data)
            # 记录日志，提示因超过账户总风险上限而跳过交易。 (记录日志，说风险太大了，超过账户总上限了，这次不买了。)
            return 0
            # 如果超过总风险上限，则返回0，表示无法交易。 (如果超过总风险上限，那就返回0，表示这次不买了。)

        risk_amount = equity * effective_risk_percent
        # 计算本次交易允许承担的最大风险金额，总净值乘以有效风险比例。 (计算这次交易最多能亏多少钱，用总资产乘以风险比例。)

        size_raw = risk_amount / risk_per_share
        # 计算理论上的仓位大小（股数），最大风险金额除以每股风险。 (计算理论上可以买多少股，用最大亏损金额除以每股亏损。)
        size = int(size_raw / 100) * 100
        # 将计算出的仓位大小向下取整到100的整数倍，因为A股交易单位是100股。 (因为A股买股票最少要买100股，所以把算出来的股数向下取整到100的倍数。)

        if size <= 0:
            # 检查计算出的仓位大小是否小于等于0。 (判断算出来的股数是不是小于等于0，小于等于0就说明买不了。)
            self.log(
                f"Calculated size is zero or negative ({size}). Cannot place order.", data=data)
            # 记录日志，提示计算出的仓位大小为零或负数，无法下单。 (记录日志，说算出来买不了，不买了。)
            return 0
            # 如果仓位大小小于等于0，则返回0，表示无法交易。 (如果算出来买不了，那就返回0，表示这次不买了。)

        max_pos_value = equity * self.params.max_position_per_etf_percent
        # 计算单个ETF允许的最大持仓市值，总净值乘以最大持仓比例。 (计算单个ETF最多能买多少钱的，用总资产乘以单个ETF最大仓位比例。)
        current_price_for_calc = data_close_price if data_close_price > 0 else entry_price  # 使用收盘价或入场价计算
        # 使用当前收盘价作为计算市值时的价格（如果有效）。 (用最新的收盘价或者入场价来算算钱。)

        if current_price_for_calc <= 0:
            # 检查用于计算的价格是否有效。 (检查用来算钱的价格是不是大于0。)
            self.log(
                f"Invalid price ({current_price_for_calc:.2f}) for size calculation.", data=data)
            # 记录日志，提示价格无效。 (记录日志，说价格有问题，算不了。)
            return 0
            # 如果价格无效，则返回0。 (如果价格有问题，那就返回0。)

        potential_trade_value = size * current_price_for_calc
        # 计算潜在交易的总市值，仓位大小乘以当前价格。 (算算如果按计划买这么多股，总共值多少钱。)

        if potential_trade_value > max_pos_value:
            # 检查潜在交易市值是否超过单个ETF最大持仓市值限制。 (判断算出来的要买的金额是不是超过了单个ETF的上限。)
            new_size = int(max_pos_value / current_price_for_calc / 100) * 100
            # 如果超过限制，则将仓位大小调整为不超过最大持仓市值的最大100股整数倍。 (如果超过了，那就减少买入股数，只买到上限允许的金额。)
            self.log(
                f"Size reduced from {size} to {new_size} due to max position limit ({self.params.max_position_per_etf_percent*100:.0f}% of equity).", data=data)
            # 记录日志，提示仓位大小因最大持仓限制而调整。 (记录日志，说买太多超标了，减少到多少股。)
            size = new_size
            # 更新仓位大小。 (更新买入股数。)

        potential_trade_value = size * current_price_for_calc
        # 重新计算调整后的潜在交易市值。 (重新算算调整后值多少钱。)
        if potential_trade_value > cash:
            # 检查调整后的潜在交易市值是否超过可用现金。 (看看算出来要买的金额是不是比现在手里的现金还多。)
            new_size = int(cash / current_price_for_calc / 100) * 100
            # 如果超过可用现金，则将仓位大小调整为不超过可用现金的最大100股整数倍。 (如果现金不够，那就再减少买入股数，只买现金够买的部分。)
            if new_size < size:  # 只有当现金限制导致规模减小时才记录
                self.log(
                    f"Size reduced from {size} to {new_size} due to cash limit (Available: {cash:.2f}, Required: {potential_trade_value:.2f}).", data=data)
                # 记录日志，提示仓位大小因现金限制而调整。 (记录日志，说现金不够买那么多了，减少到多少股。)
                size = new_size
                # 更新仓位大小。 (更新买入股数。)

        if size <= 0:
            # 再次检查计算出的仓位大小是否小于等于0。 (再次检查，经过各种限制后，算出来的股数是不是小于等于0。)
            self.log(
                f"Final calculated size is zero or negative ({size}). Cannot place order.", data=data)
            # 记录日志，提示最终仓位大小为零或负数，无法下单。 (记录日志，说最终算出来还是买不了，不买了。)
            return 0
            # 如果最终仓位大小小于等于0，则返回0。 (如果最终算出来买不了，那就返回0。)

        return size
        # 返回最终计算出的、经过风险和资金限制调整的仓位大小。 (最终决定买多少股，返回这个股数。)

    def next(self):
        # 定义next函数，在每个数据点（通常是每个交易日）都会被调用一次，用于执行策略的主要逻辑。 (定义next函数，这是策略的核心，每天开盘后都要运行一遍，决定今天该干啥。)
        # 检查是否暂停交易
        # Check if trading is halted
        if self.halt_trading:
            # 如果全局交易暂停。 (如果之前亏太多暂停交易了。)
            # 尝试平掉所有仓位
            # Attempt to close all positions
            for d in self.datas:
                # 遍历所有数据源。 (检查所有ETF。)
                position = self.getposition(d)
                # 获取持仓信息。 (看看手里有没有这只ETF。)
                order = self.orders.get(d)  # 使用get避免KeyError
                # 获取订单状态。 (看看有没有挂单。)
                if position.size != 0 and not order:
                    # 如果有持仓且没有挂单。 (如果手里有这只ETF，而且没有挂单。)
                    self.log(
                        f'HALTED: Attempting to close position for {d._name} Size: {position.size}', data=d)
                    # 记录日志，提示因暂停交易而平仓。 (记录日志：暂停交易了，把这只ETF卖掉。)
                    order_close = self.close(data=d)
                    # 发出平仓指令。 (下达卖出指令。)
                    if order_close:
                        self.orders[d] = order_close  # Track the closing order
                    else:
                        self.log(
                            f'HALTED: Failed to create close order for {d._name}', data=d)
            return  # Stop processing new signals

        for i, d in enumerate(self.datas):
            # 遍历每个数据源，i是索引，d是数据对象。 (轮流检查每一只ETF。)
            position = self.getposition(d)
            # 获取当前数据源的持仓信息。 (看看现在手里有没有这只ETF的股票。)
            order = self.orders.get(d)  # 使用get避免KeyError
            # 获取当前数据源的订单状态。 (看看这只ETF有没有挂单。)
            data_name = d._name if hasattr(d, '_name') else f'Data {i}'
            # 获取数据名称。 (获取这个ETF的名字。)

            # 检查是否有活动订单，如果有则跳过
            # Check for active orders, skip if any
            if order:
                # 检查当前数据源是否有未完成的订单。 (判断这只ETF昨天下的指令还没成交。)
                # self.log(f'Skipping {data_name}: Active order {order.ref} with status {order.getstatusname()}', data=d) # 可以取消注释以查看跳过日志
                continue
                # 如果有未完成的订单，则跳过当前数据源，处理下一个数据源。 (如果有挂单，那就先等着它的指令结果，去看下一只ETF。)

            # 如果有持仓，检查止损或止盈条件
            # If holding a position, check for stop-loss or take-profit conditions
            if position.size != 0:
                # 如果当前有持仓。 (如果现在手里有这只ETF的股票。)
                current_price = self.closes[i][0]
                # 获取当前收盘价。 (获取今天的收盘价。)
                stop_loss = self.stop_loss_prices.get(d)
                # 获取止损价。 (获取设置的止损价。)
                take_profit = self.take_profit_prices.get(d)
                # 获取止盈价。 (获取设置的止盈价。)

                # 检查止损
                # Check stop-loss
                if stop_loss is not None and current_price <= stop_loss:
                    # 如果设置了止损价并且当前价格低于或等于止损价。 (如果设置了止损价，并且今天的价格跌破了止损价。)
                    self.log(
                        f'STOP LOSS HIT: Closing {data_name} at {current_price:.2f} (Stop @ {stop_loss:.2f})', data=d)
                    # 记录止损触发日志。 (记录日志：跌破止损了！卖掉！)\
                    order_close = self.close(data=d)
                    if order_close:
                        self.orders[d] = order_close  # 记录平仓订单
                    # 发出平仓指令。 (下达卖出指令。)
                    continue  # 处理完止损后跳到下一个数据
                    # Continue to the next data after handling stop-loss

                # 检查止盈
                # Check take-profit
                elif take_profit is not None and current_price >= take_profit:
                    # 如果设置了止盈价并且当前价格高于或等于止盈价。 (如果设置了止盈价，并且今天的价格涨到了止盈价。)
                    self.log(
                        f'TAKE PROFIT HIT: Closing {data_name} at {current_price:.2f} (Profit Target @ {take_profit:.2f})', data=d)
                    # 记录止盈触发日志。 (记录日志：达到止盈目标了！卖掉！)
                    order_close = self.close(data=d)
                    if order_close:
                        self.orders[d] = order_close  # 记录平仓订单
                    # 发出平仓指令。 (下达卖出指令。)
                    continue  # 处理完止盈后跳到下一个数据
                    # Continue to the next data after handling take-profit

            # 如果没有持仓，检查入场条件
            # If no position, check for entry conditions
            elif position.size == 0:  # 明确判断持仓为0
                # 如果当前没有持仓。 (如果现在这只ETF手里没货。)
                market_state = 'UNCERTAIN_DO_NOT_TRADE'
                # 初始化市场状态为'UNCERTAIN_DO_NOT_TRADE'（不确定，不交易）。 (先假设今天这只ETF市场情况不明朗，最好别交易。)
                try:
                    # 尝试判断市场状态
                    # Try to determine market state
                    is_trend_up = (self.closes[i][0] > self.emas_medium[i][0] > self.emas_long[i][0] and
                                   self.emas_medium[i][0] > self.emas_medium[i][-1] and
                                   self.emas_long[i][0] > self.emas_long[i][-1])
                    # 判断是否为上升趋势：收盘价>中期EMA>长期EMA，且中期EMA和长期EMA均向上。 (判断这只ETF是不是牛市：短期均线在长期均线上方，而且两条线都在往上走。)
                    is_range_confirmed = (not is_trend_up and
                                          abs(self.emas_medium[i][0] / self.emas_medium[i][-1] - 1) < 0.003 and
                                          abs(self.emas_long[i][0] / self.emas_long[i][-1] - 1) < 0.003 and
                                          self.adxs[i].adx[0] < 20 and
                                          (self.bbands[i].top[0] - self.bbands[i].bot[0]) / self.closes[i][0] < 0.07)
                    # 判断是否为震荡市：非上升趋势，中期EMA和长期EMA近似走平，ADX值低，布林带宽度窄。 (判断这只ETF是不是震荡市：不是牛市，均线稍微有点动静没事，趋势强度弱，而且最近价格波动范围不大。)

                    if is_trend_up:
                        # 如果判断为上升趋势。 (如果是牛市。)
                        market_state = 'TREND_UP'
                        # 将市场状态设置为'TREND_UP'（上升趋势）。 (那就标记一下，现在是上升趋势。)
                    elif is_range_confirmed and self.params.etf_type == 'range':  # 使用params访问参数
                        # 如果判断为震荡市，并且该ETF类型设置为'range'（震荡型）。 (如果是震荡市，而且这个ETF适合"高抛低吸"。)
                        market_state = 'RANGE_CONFIRMED'
                        # 将市场状态设置为'RANGE_CONFIRMED'（确认震荡）。 (那就标记一下，现在是震荡市。)

                except IndexError:
                    # 捕获索引错误（通常发生在回测初期数据不足时）
                    # Catch index error (usually occurs at the beginning of backtesting when data is insufficient)
                    # self.log(f'Skipping {data_name}: Not enough data for indicator calculation.', data=d)
                    continue  # 跳过当前数据
                    # Skip current data

                entry_signal = False
                # 初始化入场信号为False。 (先假设今天这只ETF没有买入信号。)
                potential_position_type = None
                # 初始化潜在持仓类型为None。 (先假设不知道要按哪种策略买这只ETF。)
                entry_price_calc = self.closes[i][0]  # 使用收盘价计算，实际入场可能是次日开盘或其他
                # 假设以当前收盘价作为入场价进行计算。 (假设以收盘价买入，先用收盘价来算算。)
                stop_loss_price_calc = None
                # 初始化计算用的止损价为None。 (初始化止损价为空。)
                take_profit_price_calc = None
                # 初始化计算用的止盈价为None。 (初始化止盈价为空。)
                risk_per_trade_percent = 0
                # 初始化单笔交易风险比例为0。 (初始化风险比例为0。)

                # 趋势策略入场逻辑
                # Trend strategy entry logic
                if market_state == 'TREND_UP' and self.params.etf_type == 'trend':  # 使用params访问参数
                    # 如果市场状态为上升趋势，并且该ETF类型设置为'trend'（趋势型）。 (如果是上升趋势，而且这个ETF适合"追涨杀跌"。)
                    try:
                        # 尝试检查入场信号
                        # Try checking for entry signal
                        is_breakout = (self.closes[i][0] > self.highest_highs[i][-1] and
                                       self.volumes[i][0] > self.sma_volumes[i][0] * self.params.trend_volume_ratio_min)
                        # 判断是否为突破信号：当前收盘价创近期新高，且成交量放大。 (判断这只ETF是不是突破了：价格创了最近60天新高，而且交易量比平时大。)
                        is_pullback = (min(abs(self.lows[i][0] / self.emas_medium[i][0] - 1), abs(self.lows[i][0] / self.emas_long[i][0] - 1)) < 0.01 and
                                       self.closes[i][0] > self.opens[i][0])
                        # 判断是否为回调企稳信号：当日最低价接近均线，且当日收阳线。 (判断这只ETF是不是回调站稳了：价格跌到均线附近，但当天又涨回来了。)

                        if is_breakout or is_pullback:
                            # 如果出现突破信号或回调企稳信号。 (如果突破了或者回调站稳了。)
                            entry_signal = True
                            # 设置入场信号为True。 (标记：可以买这只ETF了！)\
                            potential_position_type = 'trend'
                            # 设置潜在持仓类型为'trend'（趋势）。 (标记：这是按趋势策略买的。)
                            risk_per_trade_percent = self.params.max_risk_per_trade_trend
                            # 设置单笔交易风险比例为趋势策略的设定值。 (标记：这次交易最多亏总资金的1%。)
                            stop_loss_price_calc = entry_price_calc - \
                                self.params.trend_stop_loss_atr_mult * \
                                self.atrs[i][0]
                            # 使用ATR计算止损价，入场价减去ATR的倍数。 (根据这只ETF最近的平均波动幅度，算出止损价应该设在假定入场价下方多少。)

                            if stop_loss_price_calc < entry_price_calc:
                                # 检查止损价是否有效，即是否低于入场价。 (判断止损价是不是真的比买入价低，止损价必须比买入价低才行。)
                                risk_per_share = entry_price_calc - stop_loss_price_calc
                                # 计算每股风险金额。 (算一下如果买在这只ETF当前价，跌到止损价，每股会亏多少钱。)
                                if risk_per_share > 0:
                                    # 检查每股风险是否大于0。 (判断每股风险是不是大于0，大于0才能算止盈。)
                                    take_profit_price_calc = entry_price_calc + \
                                        self.params.trend_take_profit_rratio * risk_per_share
                                    # 根据盈亏比计算止盈价，入场价加上风险金额的倍数。 (根据设定的盈亏比（比如2倍），算出止盈价应该设在假定入场价上方多少。)
                                else:
                                    # 如果每股风险不大于0。 (如果每股风险有问题。)
                                    entry_signal = False  # 取消信号
                                    # 取消入场信号。 (那就取消买入信号。)
                                    self.log(
                                        f"Trend signal {data_name} skipped: Risk per share is non-positive ({risk_per_share:.2f}). SL: {stop_loss_price_calc:.2f}, Entry: {entry_price_calc:.2f}", data=d)
                                    # 记录日志。 (记录日记：趋势信号跳过，因为每股风险有问题。)

                            else:
                                entry_signal = False  # 止损价不低于入场价，取消信号
                                # 如果止损价无效，则取消入场信号。 (如果止损价有问题，那就取消买入信号。)
                                self.log(
                                    f"Trend signal {data_name} skipped: Stop loss {stop_loss_price_calc:.2f} not below entry {entry_price_calc:.2f}", data=d)
                                # 记录日志，提示因止损价不低于入场价而跳过趋势信号。 (记录日记：趋势信号跳过，因为止损价不在入场价下方。)

                    except IndexError:
                        # 捕获索引错误
                        # Catch index error
                        # self.log(f'Skipping {data_name} trend check: Not enough data.', data=d)
                        continue

                # 震荡策略入场逻辑
                # Range strategy entry logic
                elif market_state == 'RANGE_CONFIRMED' and self.params.etf_type == 'range':  # 使用params访问参数
                    # 如果市场状态为震荡市，并且该ETF类型设置为'range'（震荡型）。 (如果是震荡市，而且这个ETF适合"高抛低吸"。)
                    try:
                        # 尝试检查入场信号
                        # Try checking for entry signal
                        is_range_buy = (self.lows[i][0] <= self.bbands[i].bot[0] and
                                        self.closes[i][0] > self.bbands[i].bot[0] and
                                        self.rsis[i][0] < self.params.rsi_oversold)
                        # 判断是否为震荡买入信号：最低价触及或下穿布林带下轨，收盘价回到下轨之上，且RSI超卖。 (判断这只ETF是不是到底了：价格碰到或跌破布林带下轨，但当天收盘又涨回来了，并且RSI显示超卖。)

                        if is_range_buy:
                            # 如果出现震荡买入信号。 (如果满足上面的条件。)
                            entry_signal = True
                            # 设置入场信号为True。 (标记：可以买这只ETF了！)
                            potential_position_type = 'range'
                            # 设置潜在持仓类型为'range'（震荡）。 (标记：这是按震荡策略买的。)
                            risk_per_trade_percent = self.params.max_risk_per_trade_range
                            # 设置单笔交易风险比例为震荡策略的设定值。 (标记：这次交易最多亏总资金的0.5%。)
                            stop_loss_price_calc = self.lows[i][0] * \
                                (1 - self.params.range_stop_loss_buffer)
                            # 计算止损价，为信号K线最低价下方一定比例。 (把止损价设在触发信号那天最低价再低一点点的位置。)
                            take_profit_price_calc = self.bbands[i].mid[0]
                            # 计算止盈价，为布林带中轨价格。 (把止盈目标设在布林带的中线位置。)

                            if stop_loss_price_calc >= entry_price_calc:
                                # 检查止损价是否有效，即是否低于入场价。 (判断止损价是不是真的比买入价低，止损价必须比买入价低才行。)
                                entry_signal = False  # 止损价不低于入场价，取消信号
                                # 如果止损价无效，则取消入场信号。 (如果止损价有问题，那就取消买入信号。)
                                self.log(
                                    f"Range signal {data_name} skipped: Stop loss {stop_loss_price_calc:.2f} not below entry {entry_price_calc:.2f}", data=d)
                                # 记录日志，提示因止损价不低于入场价而跳过震荡信号。 (记录日记：震荡信号跳过，因为止损价不在入场价下方。)

                    except IndexError:
                        # 捕获索引错误
                        # Catch index error
                        # self.log(f'Skipping {data_name} range check: Not enough data.', data=d)
                        continue

                # 如果有入场信号并且计算出的止损价有效
                # If there is an entry signal and the calculated stop-loss price is valid
                if entry_signal and stop_loss_price_calc is not None and entry_price_calc > stop_loss_price_calc:
                    # 如果有入场信号，且止损价已计算且有效（低于入场价）。 (如果决定要买这只ETF，而且算好了有效的止损价。)
                    size = self._calculate_trade_size(
                        self.closes[i][0], entry_price_calc, stop_loss_price_calc, risk_per_trade_percent, data=d)
                    # 调用_calculate_trade_size方法计算仓位大小。 (让小工具帮忙算算买多少股。)

                    if size > 0:
                        # 检查计算出的仓位大小是否大于0。 (如果算了一圈下来，确实还能买 > 0 股这只ETF。)
                        self.log(
                            f'BUY SIGNAL (Bracket): {data_name}, Size: {size}, Entry: ~{entry_price_calc:.2f}, SL: {stop_loss_price_calc:.2f}, TP: {take_profit_price_calc if take_profit_price_calc else "N/A"}, Type: {potential_position_type}', data=d)
                        # 记录创建买入订单的日志。 (记录日记：准备买入！买多少股，预估入场价，止损价，止盈价，策略类型。)

                        # 使用市价单或次日开盘价限价单入场可能更实际
                        # Using market order or next day's open limit order might be more practical
                        # 这里简单使用市价单简化入场
                        # Here, simulate using a market order for simplified entry
                        bracket_orders = self.buy_bracket(
                            data=d,
                            size=size,
                            price=entry_price_calc,  # Limit price for the entry order
                            stopprice=stop_loss_price_calc,  # Price for the stop loss order
                            limitprice=take_profit_price_calc  # Price for the take profit order
                            # exectype, stopargs, limitargs can be added if defaults need changing
                        )

                        # Check if main order was created
                        if bracket_orders and bracket_orders[0]:
                            # Bracket orders handle SL/TP automatically, no need to store/track manually here
                            # self.orders[d] = bracket_orders[0] # Optional: track main order if needed
                            # self.stop_loss_prices[d] = stop_loss_price_calc # No longer needed
                            # self.take_profit_prices[d] = take_profit_price_calc # No longer needed
                            # Still record the type
                            self.position_types[d] = potential_position_type
                        else:
                            self.log(
                                f'Failed to create buy_bracket order for {data_name}', data=d)


# ===================================================================================
# Cerebro 设置函数 (Cerebro Setup Function)
# ===================================================================================
def setup_cerebro(config):
    """
    根据配置创建并返回Cerebro引擎实例。
    Creates and returns a Cerebro engine instance based on the configuration.

    Args:
        config (dict): 配置字典。

    Returns:
        bt.Cerebro: 配置好的Cerebro实例。
    """
    # 优化时设置 stdstats=False 避免 Windows 多进程 pickling 观察器时出错
    # Set stdstats=False during optimization to prevent observer pickling errors with multiprocessing on Windows
    cerebro = bt.Cerebro(optreturn=False, stdstats=not config['optimize'])
    # 创建Cerebro引擎实例，设置optreturn=False以便在优化时访问完整的策略实例和分析器。
    # 同时根据 optimize 标志设置 stdstats，优化时不添加标准观察器。
    # Create a Cerebro engine instance, setting optreturn=False to access full strategy instances and analyzers during optimization.
    # Also set stdstats based on the optimize flag, not adding standard observers during optimization.
    return cerebro

# ===================================================================================
# Broker 设置函数 (Broker Setup Function)
# ===================================================================================
# (后续会创建 setup_broker 函数)

# ===================================================================================
# 优化流程函数 (Optimization Process Function)
# ===================================================================================
# (后续会创建 run_optimization 函数)

# ===================================================================================
# 单次回测流程函数 (Single Backtest Process Function)
# ===================================================================================
# (后续会创建 run_single_backtest 函数)

# ===================================================================================
# 主回测运行函数 (Main Backtest Runner Function)
# ===================================================================================
def run_backtest():
    # Python主程序入口，当直接运行此脚本时，以下代码会被执行。 (This is the program's entry point; the code below runs only when this script is executed directly.)

    # --- 获取配置 (Get Configuration) ---
    config = get_backtest_config()
    # 调用函数获取配置字典。 (Call the function to get the configuration dictionary.)

    # --- 配置区 (Configuration Area) ---
    # 这些变量现在从 config 字典中获取 (但为了清晰，保留部分直接引用)
    # These variables are now retrieved from the config dictionary (but some direct references are kept for clarity)
    optimize = config['optimize']
    initial_cash = config['initial_cash']
    commission_rate = config['commission_rate']
    data_files = config['data_files']
    column_mapping = config['column_mapping']
    openinterest_col = config['openinterest_col']
    fromdate = config['fromdate']
    todate = config['todate']

    # 优化参数范围 (Optimization Parameter Ranges)
    ema_medium_range = config['ema_medium_range']
    ema_long_range = config['ema_long_range']
    bbands_period_range = config['bbands_period_range']
    bbands_dev_range = config['bbands_dev_range']
    # ------------------------------------

    # --- 创建Cerebro引擎实例 (Create Cerebro Engine Instance) ---
    cerebro = setup_cerebro(config)
    # 调用函数创建Cerebro实例。 (Call the function to create the Cerebro instance.)

    # --- 数据加载 (Data Loading) ---
    print("--- 开始加载数据 ---")
    # 打印数据加载开始的提示。 (Print a message indicating the start of data loading.)
    loaded_data_count = load_data_to_cerebro(cerebro, data_files, column_mapping,
                                           openinterest_col, fromdate, todate)
    # 调用函数加载数据到Cerebro。 (Call the function to load data into Cerebro.)

    # 检查是否有数据成功加载
    if loaded_data_count == 0:
        print("\n错误：没有成功加载任何数据，无法继续执行回测。")
        return # 如果没有数据，则退出函数

    print("--- 数据加载完成 --- ({loaded_data_count} 个数据源)".format(loaded_data_count=loaded_data_count))
    # 打印数据加载完成的提示。 (Print a message indicating the completion of data loading.)

    # 设置初始资金和佣金
    # Set initial cash and commission
    cerebro.broker.setcash(initial_cash)
    # 设置经纪商的初始现金。 (Set the broker's initial cash.)
    cerebro.broker.setcommission(commission=commission_rate)
    # 设置经纪商的交易佣金率。 (Set the broker's commission rate.)

    # --- 策略和分析器添加 (Strategy and Analyzer Addition) ---
    if optimize:
        # 如果是优化模式。 (If in optimization mode.)
        print("--- 开始参数优化 ---")
        # 打印参数优化开始的提示。 (Print a message indicating the start of parameter optimization.)
        # 添加优化策略
        # Add the optimization strategy
        cerebro.optstrategy(
            AShareETFStrategy,
            ema_medium_period=ema_medium_range,
            ema_long_period=ema_long_range,
            bbands_period=bbands_period_range,
            bbands_devfactor=bbands_dev_range
        )
        # 添加用于优化的策略，并传入参数范围。 (Add the strategy for optimization with parameter ranges.)

        # 添加优化所需的分析器
        # Add analyzers required for optimization
        cerebro.addanalyzer(bt.analyzers.SharpeRatio,
                            _name='sharpe_ratio', riskfreerate=0.0)  # 年化，假设无风险利率为0
        # 添加夏普比率分析器，假设无风险利率为0。 (Add SharpeRatio analyzer, assuming risk-free rate is 0.)
        cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
        # 添加收益率分析器。 (Add Returns analyzer.)
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        # 添加最大回撤分析器。 (Add DrawDown analyzer.)

        # 运行优化
        # Run the optimization
        start_time = time.time()
        # 记录开始时间。 (Record the start time.)
        results = cerebro.run(maxcpus=10)  # 使用多核进行优化
        # 运行优化过程，使用多核。 (Run the optimization process using multiple cores.)
        end_time = time.time()
        # 记录结束时间。 (Record the end time.)
        print("--- 参数优化完成 ---")
        # 打印参数优化完成的提示。 (Print a message indicating the completion of parameter optimization.)

        # --- 计算统计信息 ---
        # --- Calculate Statistics ---
        total_time = end_time - start_time
        # 计算总耗时。 (Calculate the total time taken.)
        actual_combinations = len(results) if results else 0
        # 获取实际运行组合数。 (Get the actual number of combinations run.)
        avg_time = total_time / actual_combinations if actual_combinations else 0
        # 计算平均耗时。 (Calculate the average time per combination.)

        # --- 优化结果分析 (Optimization Result Analysis) ---
        print("\n--- 开始分析优化结果 ---")
        # 打印开始分析优化结果的提示。 (Print a message indicating the start of optimization result analysis.)
        best_result, all_scored_results = analyze_optimization_results(results)
        # 调用函数分析优化结果，获取最佳结果和所有带得分的结果。 (Call the function to analyze optimization results, getting the best result and all scored results.)

        # 使用辅助函数打印优化结果 (传入统计信息)
        # Use helper function to print optimization results (passing statistics)
        print_optimization_summary(best_result, all_scored_results, ema_medium_range,
                                   ema_long_range, bbands_period_range, bbands_dev_range, total_time, actual_combinations, avg_time)

        print("\n--- 优化结果分析完成 ---")
        # 打印优化结果分析完成的提示。 (Print a message indicating the completion of optimization result analysis.)

    else:
        # 如果是单次回测模式。 (If in single backtest mode.)
        print("--- 开始单次回测 ---")
        # 打印单次回测开始的提示。 (Print a message indicating the start of the single backtest.)
        # 添加策略
        # Add the strategy
        cerebro.addstrategy(AShareETFStrategy,
                            # 使用 config 中的固定参数
                            # Use fixed parameters from config
                            ema_medium_period=config['ema_medium_period_fixed'],
                            ema_long_period=config['ema_long_period_fixed'],
                            bbands_period=config['bbands_period_fixed'],
                            bbands_devfactor=config['bbands_devfactor_fixed']
                            # risk_per_trade_percent 和 allow_short 可以继续使用策略默认值
                            # risk_per_trade_percent and allow_short can continue using strategy defaults
                            )
        # 添加策略，并使用固定的或之前优化得到的最佳参数。 (Add the strategy using fixed or previously optimized best parameters.)

        # 添加分析器
        # Add analyzers
        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
        # 添加夏普比率分析器。 (Add SharpeRatio analyzer.)
        cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
        # 添加收益率分析器。 (Add Returns analyzer.)
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        # 添加最大回撤分析器。 (Add DrawDown analyzer.)
        cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
        # 添加交易分析器。 (Add TradeAnalyzer.)
        cerebro.addanalyzer(bt.analyzers.SQN, _name='sqn')
        # 添加系统质量数（SQN）分析器。 (Add System Quality Number (SQN) analyzer.)
        cerebro.addanalyzer(bt.analyzers.PyFolio,
                            _name='pyfolio')  # 用于PyFolio集成
        # 添加用于PyFolio集成的分析器。 (Add analyzer for PyFolio integration.)

        # 添加观察器
        # Add observers
        cerebro.addobserver(bt.observers.Broker)
        # 添加经纪商观察器，显示现金和投资组合价值。 (Add Broker observer to display cash and portfolio value.)
        cerebro.addobserver(bt.observers.Trades)
        # 添加交易观察器，显示交易标记。 (Add Trades observer to display trade markers.)
        cerebro.addobserver(bt.observers.BuySell)
        # 添加买卖信号观察器。 (Add BuySell observer.)
        cerebro.addobserver(bt.observers.DrawDown)
        # 添加回撤观察器。 (Add DrawDown observer.)

        # 运行回测
        # Run the backtest
        print("Running single backtest...")
        # 打印开始运行单次回测的提示。 (Print a message indicating the start of the single backtest run.)
        results = cerebro.run()
        # 运行单次回测。 (Run the single backtest.)
        strat = results[0]  # 获取策略实例
        # 获取策略实例。 (Get the strategy instance.)
        print("--- 单次回测完成 ---")
        # 打印单次回测完成的提示。 (Print a message indicating the completion of the single backtest.)

        # --- 结果打印与分析 (Result Printing and Analysis) ---
        # 使用辅助函数打印回测结果
        # Use helper function to print backtest results
        final_value = cerebro.broker.getvalue()
        print_backtest_summary(initial_cash, final_value, strat)

        # --- 绘图 (Plotting) ---
        # 绘图部分 (Plotting Section)
        print("\n--- 生成回测图表 ---")
        # 打印生成图表的提示。 (Print a message indicating the start of chart generation.)
        try:
            # 尝试生成图表。 (Try to generate the chart.)
            figs = cerebro.plot(style='candlestick', barup='red', bardown='green',
                                numfigs=1, volume=True, iplot=False)  # 设置 iplot=False 可以在非交互环境保存图片
            # 调用Cerebro的plot方法生成图表，设置样式、颜色、数量、成交量显示和非交互模式。 (Call Cerebro's plot method to generate charts with specified style, colors, number, volume display, and non-interactive mode.)
            # 注意: 在某些环境中，即使设置iplot=False，也可能需要手动保存。
            # Note: In some environments, manual saving might be needed even with iplot=False.
            # 如果需要保存图片：
            # If saving the image is needed:
            # fig = figs[0][0] # 获取第一个图表对象
            # fig.savefig('backtest_results.png')
            # print("图表已保存为 backtest_results.png")
            print("--- 图表生成完成 --- (可能需要手动在窗口中查看或已保存)")
            # 打印图表生成完成的提示。 (Print a message indicating chart generation completion.)
        except Exception as e:
            # 捕获绘图过程中可能发生的异常。 (Catch potential exceptions during plotting.)
            print(f"错误：绘图失败 - {e}")
            # 打印绘图失败的错误信息。 (Print an error message about plotting failure.)


if __name__ == '__main__':
    # 调用封装好的回测函数。 (Call the encapsulated backtesting function.)
    run_backtest()
