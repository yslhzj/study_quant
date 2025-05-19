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
import logging
import logging.handlers
import json
import uuid
import threading
import queue
import atexit
import collections


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
        ('log_level', logging.INFO),
        # 定义日志级别参数log_level，默认值为logging.INFO，表示记录INFO级别及以上的日志。 (设置日志级别，默认是INFO，就是记录INFO级别及以上的日志。)
        ('log_file', 'bt_g2.5t_strategy0414.log'),
        # 定义日志文件名参数log_file，默认值为'bt_g2.5t_strategy0414.log'，表示日志文件名为bt_g2.5t_strategy0414.log。 (设置日志文件名，默认是bt_g2.5t_strategy0414.log。)
        ('log_format', '%(asctime)s [%(levelname)s] %(message)s'),
        # 定义日志格式参数log_format，默认值为'%(asctime)s [%(levelname)s] %(message)s'，表示日志格式为时间戳、日志级别和日志信息。 (设置日志格式，默认是时间戳、日志级别和日志信息。)
        ('log_datefmt', '%Y-%m-%d %H:%M:%S'),
        # 定义日志时间格式参数log_datefmt，默认值为'%Y-%m-%d %H:%M:%S'，表示日志时间格式为年-月-日 时:分:秒。 (设置日志时间格式，默认是年-月-日 时:分:秒。)
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
        """计算交易仓位大小，返回包含大小和调整原因的字典"""
        # (Calculate trade size, returning a dictionary with size and adjustment reasons)
        reasons = []  # 存储调整原因的列表 (List to store adjustment reasons)
        data_name = data._name if hasattr(data, '_name') else 'Unknown Data'

        if stop_loss_price >= entry_price:
            reason = f"Stop loss price {stop_loss_price:.2f} not below entry price {entry_price:.2f}"
            reasons.append(reason)
            self.log(
                f"{data_name}: {reason}. Cannot calculate size.", data=data)
            return {'size': 0, 'raw_size': 0, 'reasons': reasons}

        risk_per_share = entry_price - stop_loss_price
        if risk_per_share <= 0:
            reason = f"Calculated risk per share is zero or negative ({risk_per_share:.2f})"
            reasons.append(reason)
            self.log(
                f"{data_name}: {reason}. Cannot calculate size.", data=data)
            return {'size': 0, 'raw_size': 0, 'reasons': reasons}

        # 暂不考虑风险乘数 current_risk_multiplier，保持为 1.0
        # (Temporarily ignore risk multiplier, keep it at 1.0)
        effective_risk_percent = risk_per_trade_percent  # * self.current_risk_multiplier

        cash = self.broker.get_cash()
        equity = self.broker.get_value()

        # 检查账户总风险 (Check total account risk)
        # total_current_risk = self.get_total_risk_exposure() # 需要实现 get_total_risk_exposure
        # potential_new_risk = (equity * effective_risk_percent)
        # if total_current_risk + potential_new_risk > self.p.max_total_risk_percent:
        #     reason = f"Exceeds max total account risk. Current: {total_current_risk:.2%}, New: {effective_risk_percent:.2%}, Limit: {self.p.max_total_risk_percent:.2%}"
        #     reasons.append(reason)
        #     self.log(f"{data_name}: Trade skipped. {reason}", data=data)
        #     return {'size': 0, 'raw_size': 0, 'reasons': reasons}

        risk_amount = equity * effective_risk_percent
        size_raw = risk_amount / risk_per_share
        # A股向下取整100股 (Round down to nearest 100 for A-shares)
        size = int(size_raw / 100) * 100
        # 记录风险计算后的原始大小 (Record raw size after risk calculation)
        raw_size_calculated = size

        if size <= 0:
            reason = f"Size calculated based on risk is zero or negative ({size})"
            reasons.append(reason)
            self.log(f"{data_name}: {reason}. Cannot place order.", data=data)
            return {'size': 0, 'raw_size': raw_size_calculated, 'reasons': reasons}

        # 检查最大持仓限制 (Check max position limit)
        max_pos_value = equity * self.p.max_position_per_etf_percent
        current_price_for_calc = data_close_price if data_close_price > 0 else entry_price
        if current_price_for_calc <= 0:
            reason = f"Invalid price ({current_price_for_calc:.2f}) for max position check"
            reasons.append(reason)
            self.log(
                f"{data_name}: {reason}. Cannot calculate size.", data=data)
            return {'size': 0, 'raw_size': raw_size_calculated, 'reasons': reasons}

        potential_trade_value = size * current_price_for_calc
        if potential_trade_value > max_pos_value:
            original_size = size
            size = int(max_pos_value / current_price_for_calc / 100) * 100
            reason = f"Size reduced from {original_size} to {size} due to max position limit ({self.p.max_position_per_etf_percent:.1%})"
            reasons.append(reason)
            self.log(f"{data_name}: {reason}", data=data)

        # 检查现金限制 (Check cash limit)
        # 使用调整后的 size (Use adjusted size)
        potential_trade_value = size * current_price_for_calc
        if potential_trade_value > cash:
            original_size = size
            size = int(cash / current_price_for_calc / 100) * 100
            # 仅当现金限制导致实际减少时记录 (Only log if cash limit caused actual reduction)
            if size < original_size:
                reason = f"Size reduced from {original_size} to {size} due to cash limit (Available: {cash:.2f}, Required: {potential_trade_value:.2f})"
                reasons.append(reason)
                self.log(f"{data_name}: {reason}", data=data)

        if size <= 0:
            reason = f"Final calculated size is zero or negative ({size}) after limits"
            reasons.append(reason)
            self.log(f"{data_name}: {reason}. Cannot place order.", data=data)
            return {'size': 0, 'raw_size': raw_size_calculated, 'reasons': reasons}

        return {'size': size, 'raw_size': raw_size_calculated, 'reasons': reasons}

    def next(self):
        # 定义next函数，在每个数据点（通常是每个交易日）都会被调用一次，用于执行策略的主要逻辑。 (定义next函数，这是策略的核心，每天开盘后都要运行一遍，决定今天该干啥。)

        # ===================================================================================
        # 主回测运行函数 (Main Backtest Runner Function)
        # ===================================================================================

        # --- Calculate Order Details ---
        # (计算订单详情)
        # 使用收盘价作为近似入场价 (Use close price as approximate entry price)
        entry_price = self.closes[0]
        stop_loss_price = entry_price - \
            self.params.trend_stop_loss_atr_mult * self.atrs[0]
        take_profit_price = entry_price + \
            self.params.trend_take_profit_rratio * self.atrs[0]
        risk_per_trade_percent = self.params.max_risk_per_trade_trend

        # --- Log Order Calculation ---
        # (记录订单计算事件)
        # 调用修改后的函数，获取包含详细信息的字典
        # (Call the modified function to get a dictionary with detailed info)
        size_calc_result = self._calculate_trade_size(
            self.closes[0], entry_price, stop_loss_price, risk_per_trade_percent, data=self.datas[0])
        size = size_calc_result.get('size', 0)
        raw_size = size_calc_result.get('raw_size', 0)
        adjustment_reasons = size_calc_result.get('reasons', [])

        self.log_event(
            event_type='ORDER_CALCULATION',
            data_feed=self.datas[0],
            signal_type='TREND',
            entry_price_approx=entry_price,
            stop_loss_calc=stop_loss_price,
            take_profit_calc=take_profit_price,
            risk_inputs={
                'risk_per_trade_percent': risk_per_trade_percent,
                'stop_loss_atr_multiplier': self.params.trend_stop_loss_atr_mult,
                'atr': self.atrs[0]
            },
            size_raw=raw_size,  # 记录计算得出的原始大小 (Log the calculated raw size)
            size_final=size,  # 记录最终调整后的大小 (Log the final adjusted size)
            # 记录调整原因列表 (Log the list of adjustment reasons)
            adjustment_reasons=adjustment_reasons
        )
        # --- End Log ---

        # --- Place Order if Size > 0 ---
        # (如果大小 > 0，则下单)
        if size > 0:
            # --- Generate Trade Cycle ID ---
            # (生成交易周期 ID)
            # 检查是否已有活跃交易周期 (Check if there is already an active trade cycle)
            if self.current_trade_id is not None:
                # 如果已有，记录跳过信息并返回 (If yes, log skip info and return)
                self.log(
                    f"Warning: Attempting to start a new trade cycle for {self.datas[0]._name} while {self.current_trade_id} is active. Skipping new signal TREND.")
                self.log_event(
                    event_type='TRADE_SKIPPED',
                    data_feed=self.datas[0],
                    reason='Existing trade cycle active',
                    details={'active_trade_id': self.current_trade_id,
                             'new_signal': 'TREND'}
                )
                return  # 跳过此数据源 (Skip this data feed)

            # 生成新的交易周期 ID 并记录开始事件 (Generate new trade cycle ID and log start event)
            self.current_trade_id = f"TRADE_{uuid.uuid4().hex[:12]}"
            self.log_event(event_type="TRADE_CYCLE_START",
                           data_feed=self.datas[0], trade_cycle_id=self.current_trade_id)
            self.log(f"{self.datas[0]._name} TREND Signal. Trade Cycle {self.current_trade_id} Started. Calculated Size: {size}, Entry: {entry_price:.2f}, SL: {stop_loss_price:.2f}, TP: {take_profit_price:.2f}")
            # --- End Generate ---

            if self.position_types[self.datas[0]] is None:
                # 使用 buy_bracket 下单，包含止损和止盈 (Use buy_bracket to place order with stop loss and take profit)
                orders = self.buy_bracket(
                    data=self.datas[0],
                    size=size,
                    price=entry_price,  # 市价单或限价单 (Market or Limit order)
                    exectype=bt.Order.Market,
                    stopprice=stop_loss_price,
                    stopexec=bt.Order.Stop,
                    limitprice=take_profit_price,
                    limitexec=bt.Order.Limit
                )
                # 检查主订单是否成功创建 (Check if main order was created successfully)
                if orders and orders[0]:
                    self.order = orders[0]  # 跟踪主订单 (Track the main order)
                    # --- Log Order Submitted & Update Map for All Bracket Orders ---
                    # (记录订单提交事件并为所有括号订单更新映射)
                    for o in orders:
                        if o:
                            # 填充映射 (Populate map)
                            self.order_ref_to_trade_id_map[o.ref] = self.current_trade_id
                            # 记录提交日志 (Log submission)
                            self.log_event(
                                event_type='ORDER_SUBMITTED',
                                data_feed=self.datas[0],
                                order_ref=o.ref,
                                # trade_cycle_id 会被 log_event 自动添加 (trade_cycle_id will be added by log_event)
                                order_details={
                                    'type': o.ordtypename(),
                                    'size': o.size,
                                    'price': o.price,
                                    'plimit': o.plimit,
                                    'exectype': o.getordername(),
                                    'valid': o.valid,
                                    'tradeid': o.tradeid,
                                    'parent': o.parent.ref if o.parent else None,
                                    'oco': o.oco.ref if o.oco else None,
                                    'is_bracket_component': True
                                }
                            )
                    # --- End Log & Map Update ---
                else:
                    # 如果下单失败 (If order submission failed)
                    self.log(
                        f"{self.datas[0]._name} Failed to submit TREND bracket order for trade {self.current_trade_id}.")
                    # --- Log Trade Skipped ---
                    self.log_event(
                        event_type='TRADE_SKIPPED',
                        data_feed=self.datas[0],
                        reason='Failed to submit TREND bracket order',
                        # 包含失败的 trade_id (Include the failing trade_id)
                        trade_cycle_id=self.current_trade_id,
                        details={'intended_size': size, 'signal': 'TREND'}
                    )
                    # --- End Log ---
                    # 重置 trade_id，因为交易周期实际上未开始 (Reset trade_id as the cycle didn't actually start)
                    self.current_trade_id = None

            # Add SELL signal handling if shorting
            # (如果做空，添加 SELL 信号处理)

        else:
            # 如果计算出的 size 为 0 或负数 (If calculated size is 0 or negative)
            self.log(
                f"{self.datas[0]._name} TREND Signal. Calculated Size is {size}. Skipping trade. Reasons: {adjustment_reasons}")
            # --- Log Trade Skipped ---
            self.log_event(
                event_type='TRADE_SKIPPED',
                data_feed=self.datas[0],
                reason='Calculated size is zero or negative',
                details={
                    'calculated_size': size,
                    'signal': 'TREND',
                    'adjustment_reasons': adjustment_reasons
                }
            )
            # --- End Log ---


def run_backtest():
    """
    主函数，协调整个回测或优化流程。
    (Main function coordinating the entire backtest or optimization process.)
    """
    # --- 获取配置 ---
    config = get_backtest_config()

    # --- 创建Cerebro引擎并设置Broker ---
    cerebro = setup_cerebro_and_broker(config)

    # --- 数据加载 ---
    print("--- 开始加载数据 ---")
    # 注意: load_data_to_cerebro 需要定义在别处或此文件内
    load_data_to_cerebro(cerebro, config['data_files'], config['column_mapping'],
                         config['openinterest_col'], config['fromdate'], config['todate'])
    print("--- 数据加载完成 ---")

    # --- 添加策略、分析器和观察器 ---
    add_strategy_components(cerebro, config)

    # --- 运行回测或优化 ---
    print("--- 开始运行 Cerebro ---")
    start_time = time.time()  # 记录开始时间以供优化统计
    # maxcpus=10 在 setup_cerebro_and_broker 中处理，如果需要的话
    results = cerebro.run(maxcpus=10)
    print("--- Cerebro 运行结束 ---")

    # --- 处理和报告结果 ---
    # 传递 results, cerebro, config 和 start_time
    # 注意: process_and_report_results 需要 analyze_optimization_results, print_optimization_summary, print_backtest_summary 定义
    process_and_report_results(results, cerebro, config, start_time)

    print("\n--- 回测结束 ---")


# ===================================================================================
# 脚本执行入口 (Script Execution Entry Point)
# ===================================================================================
if __name__ == '__main__':
    run_backtest()
