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
        # 定义一个名为log的函数，用于记录日志信息，参数txt是日志文本，dt是日期时间，data是数据对象。 (定义一个日志记录函数，叫log，用来在程序运行的时候写日记。)
        # return # 注释掉return以启用日志记录
        _data = data if data is not None else (self.datas[0] if self.datas else None)
        # 如果传入了data参数，则使用data，否则尝试使用self.datas[0]（第一个数据源），再否则设为None。 (判断有没有提供数据，有就用提供的数据，没有就用第一个数据，再没有就啥也不用。)
        if _data:
            # 检查_data是否为真（即是否成功获取了数据对象）。 (判断有没有拿到数据。)
            dt = dt or _data.datetime.date(0)
            # 如果传入了dt参数，则使用dt，否则从_data中获取日期。 (判断有没有提供日期，有就用提供的日期，没有就从数据里取日期。)
            prefix = f"[{_data._name}] " if hasattr(_data, '_name') and _data._name else "" # 确保_data._name存在且不为空
            # 如果_data对象有_name属性，则创建带数据名称的前缀，否则前缀为空。 (判断数据有没有名字，有名字就加上名字前缀，没名字就啥也不加。)
            print(f"{dt.isoformat()} {prefix}{txt}")
            # 打印格式化的日志信息，包括日期、前缀和日志文本。 (把日期、前缀、日志内容拼起来，然后打印出来，就像写日记一样。)
        else:
            # 如果没有数据对象。 (如果啥数据都没拿到。)
            print(txt)
            # 直接打印日志文本，不包含日期和数据名称前缀。 (那就只打印日志内容，日期和数据名字就没了。)

    def __init__(self):
        # 定义策略的初始化函数__init__，在策略对象创建时自动执行。 (定义策略的初始化函数，策略一开始运行就会先跑这个函数。)
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
            self.emas_medium.append(bt.indicators.EMA(self.closes[i], period=self.params.ema_medium_period))
            # 为当前数据源计算中期EMA，并添加到self.emas_medium列表。 (计算当前ETF的中期EMA，然后放到列表中。)
            self.emas_long.append(bt.indicators.EMA(self.closes[i], period=self.params.ema_long_period))
            # 为当前数据源计算长期EMA，并添加到self.emas_long列表。 (计算当前ETF的长期EMA，然后放到列表中。)
            self.adxs.append(bt.indicators.ADX(d, period=self.params.adx_period))
            # 为当前数据源计算ADX指标，并添加到self.adxs列表。 (计算当前ETF的ADX指标，然后放到列表中。)
            self.atrs.append(bt.indicators.ATR(d, period=self.params.atr_period))
            # 为当前数据源计算ATR指标，并添加到self.atrs列表。 (计算当前ETF的ATR指标，然后放到列表中。)
            self.bbands.append(bt.indicators.BollingerBands(self.closes[i], period=self.params.bbands_period, devfactor=self.params.bbands_devfactor))
            # 为当前数据源计算布林带指标，并添加到self.bbands列表。 (计算当前ETF的布林带指标，然后放到列表中。)
            self.rsis.append(bt.indicators.RSI(self.closes[i], period=self.params.rsi_period))
            # 为当前数据源计算RSI指标，并添加到self.rsis列表。 (计算当前ETF的RSI指标，然后放到列表中。)
            self.highest_highs.append(bt.indicators.Highest(self.highs[i], period=self.params.trend_breakout_lookback))
            # 为当前数据源计算近期最高价指标，并添加到self.highest_highs列表。 (计算当前ETF的近期最高价指标，然后放到列表中。)
            self.sma_volumes.append(bt.indicators.SMA(self.volumes[i], period=self.params.trend_volume_avg_period))
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
        data_name = order_data._name if hasattr(order_data, '_name') else 'Unknown Data'
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
                self.log(f'BUY EXECUTED @ {order.executed.price:.2f}, Size: {order.executed.size}, Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}', data=order_data)
                # 记录买入成交的日志，包括成交价格、数量、总成本和佣金。 (记录买入成功的日志，包括成交价格、买了多少股、花了多少钱、手续费多少。)
                self.buy_prices[order_data] = order.executed.price
                # 更新当前数据源的买入价格为成交价。 (把当前ETF的买入价格更新为成交价。)
                self.buy_comms[order_data] = order.executed.comm
                # 更新当前数据源的买入佣金为成交佣金。 (把当前ETF的买入手续费更新为实际手续费。)
                # 查找关联的括号订单，并记录止损止盈价
                # Find associated bracket orders and record stop-loss/take-profit prices
                if hasattr(order, 'parent') and order.parent: # 检查是否有父订单
                    pass # 主订单成交不直接处理括号订单，等broker处理
                elif hasattr(order, 'transmit') and order.transmit is False: # 主买单可能是未transmit的
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
                self.log(f'SELL EXECUTED @ {order.executed.price:.2f}, Size: {order.executed.size}, Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}', data=order_data)
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
            self.log(f'Order {order.ref} Canceled/Margin/Rejected/Expired: Status {order.getstatusname()}', data=order_data)
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
        data_name = trade.data._name if hasattr(trade.data, '_name') else 'Unknown Data'
        # 获取数据名称。 (获取这个ETF的名字。)
        self.log(f'OPERATION PROFIT, GROSS {trade.pnl:.2f}, NET {trade.pnlcomm:.2f}, Position Type: {self.position_types.get(trade.data, "N/A")}', data=trade.data)
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
    def notify_cashvalue(self, cash, value):
        # 定义现金和总价值通知函数notify_cashvalue，在账户现金或总价值更新时被调用，参数cash是当前现金，value是当前总价值。 (定义现金和总资产值通知函数，当账户里的钱或者总资产变化的时候，程序会跑这个函数来通知你。)
        self.high_water_mark = max(self.high_water_mark, value)
        # 更新账户净值历史最高点，取当前总价值和历史最高点的较大值。 (更新账户净值的最高纪录，看看现在是不是比以前赚得更多了。)
        drawdown = (self.high_water_mark - value) / self.high_water_mark if self.high_water_mark > 0 else 0
        # 计算当前的回撤比例，即从历史最高点下跌的百分比。 (计算当前亏损的比例，就是看看现在比历史最高点亏了多少百分比。)

        if drawdown > self.params.drawdown_level2_threshold:
            # 检查当前回撤是否超过二级回撤阈值。 (判断当前亏损比例是不是超过了二级警戒线，比如10%。)
            if not self.halt_trading:
                # 检查当前是否未暂停交易。 (判断现在是不是还没暂停交易。)
                self.log(f'!!! RED ALERT: Drawdown {drawdown*100:.2f}% > {self.params.drawdown_level2_threshold*100:.0f}%. HALTING TRADING !!!')
                # 记录二级回撤警报日志，并宣布暂停交易。 (记录红色警报日志，提示亏损太多了，要暂停交易了。)
                self.halt_trading = True
                # 设置交易暂停状态为True。 (把暂停交易的开关打开，后面就不能再买卖了。)
        elif drawdown > self.params.drawdown_level1_threshold:
            # 检查当前回撤是否超过一级回撤阈值，但未超过二级阈值。 (判断当前亏损比例是不是超过了一级警戒线，比如5%，但还没到二级警戒线。)
            if not self.drawdown_level1_triggered:
                # 检查一级回撤警报是否尚未触发。 (判断是不是还没触发过黄色警报。)
                self.log(f'-- YELLOW ALERT: Drawdown {drawdown*100:.2f}% > {self.params.drawdown_level1_threshold*100:.0f}%. Reducing risk.--')
                # 记录一级回撤警报日志，提示降低风险。 (记录黄色警报日志，提示亏损有点多了，要降低风险了。)
                self.drawdown_level1_triggered = True
                # 设置一级回撤警报触发状态为True。 (把触发黄色警报的标记设为真，下次再亏损就不用重复报警了。)
                self.current_risk_multiplier = 0.5
                # 将风险乘数降低为0.5，降低后续交易的仓位大小。 (把风险系数降低一半，下次买的时候少买点，控制风险。)
        else:
            # 如果回撤未超过一级阈值，表示回撤已恢复或未达到警报级别。 (如果亏损没那么多了，低于黄色警戒线了。)
            if self.halt_trading:
                # 检查之前是否处于暂停交易状态。 (判断之前是不是暂停了交易。)
                self.log('--- Trading Resumed ---')
                # 记录交易恢复日志。 (记录交易恢复的日志，提示又可以开始交易了。)
                self.halt_trading = False
                # 重置交易暂停状态为False。 (把暂停交易的开关关掉，恢复正常交易。)
            if self.drawdown_level1_triggered:
                # 检查之前是否触发过一级回撤警报。 (判断之前是不是触发过黄色警报。)
                self.log('--- Risk Level Restored ---')
                # 记录风险水平恢复日志。 (记录风险水平恢复正常的日志，提示风险又回到正常水平了。)
                self.drawdown_level1_triggered = False
                # 重置一级回撤警报触发状态为False。 (把触发黄色警报的标记设为假，表示现在风险正常了。)
                self.current_risk_multiplier = 1.0
                # 将风险乘数恢复为1.0。 (把风险系数恢复到正常的1，下次交易又可以按正常仓位买了。)

    def _calculate_trade_size(self, data_close_price, entry_price, stop_loss_price, risk_per_trade_percent):
        # 定义一个私有方法_calculate_trade_size，用于计算交易仓位大小，根据风险管理规则。 (定义一个计算交易仓位大小的小工具，根据风险控制规则来算。)
        if stop_loss_price >= entry_price:
            # 检查止损价是否大于等于入场价。 (判断止损价是不是比买入价还高，止损价应该比买入价低才对。)
            self.log(f"Stop loss price {stop_loss_price:.2f} is not below entry price {entry_price:.2f}. Cannot calculate size.", data=None)
            # 记录错误日志，提示止损价不低于入场价，无法计算仓位。 (记录错误日志，说止损价有问题，没法算买多少股。)
            return 0
            # 如果止损价不低于入场价，则返回0，表示无法交易。 (如果止损价有问题，那就返回0，表示这次不买了。)

        risk_per_share = entry_price - stop_loss_price
        # 计算每股的风险金额，即入场价减去止损价。 (计算每股会亏多少钱，就是买入价减去止损价。)
        if risk_per_share <= 0:
            # 防止除以零或负数风险，检查每股风险是否小于等于0。 (防止计算出错，判断每股风险是不是小于等于0，正常情况下应该是大于0的。)
            self.log(f"Calculated risk per share is zero or negative ({risk_per_share:.2f}). Cannot calculate size.", data=None)
            # 记录错误日志，提示每股风险为零或负数，无法计算仓位。 (记录错误日志，说每股风险有问题，没法算买多少股。)
            return 0
            # 如果每股风险小于等于0，则返回0，表示无法交易。 (如果每股风险有问题，那就返回0，表示这次不买了。)

        effective_risk_percent = risk_per_trade_percent * self.current_risk_multiplier
        # 计算有效的单笔交易风险比例，考虑当前的风险乘数。 (计算实际承担的风险比例，要考虑当前的风险系数。)
        cash = self.broker.get_cash()
        # 获取当前账户的可用现金。 (看看现在账户里有多少现金可以用。)
        equity = self.broker.get_value()
        # 获取当前账户的总净值（现金+持仓市值）。 (看看现在账户里总共有多少钱，包括现金和股票。)
        risk_amount = equity * effective_risk_percent
        # 计算本次交易允许承担的最大风险金额，总净值乘以有效风险比例。 (计算这次交易最多能亏多少钱，用总资产乘以风险比例。)

        size_raw = risk_amount / risk_per_share
        # 计算理论上的仓位大小（股数），最大风险金额除以每股风险。 (计算理论上可以买多少股，用最大亏损金额除以每股亏损。)
        size = int(size_raw / 100) * 100
        # 将计算出的仓位大小向下取整到100的整数倍，因为A股交易单位是100股。 (因为A股买股票最少要买100股，所以把算出来的股数向下取整到100的倍数。)

        if size <= 0:
            # 检查计算出的仓位大小是否小于等于0。 (判断算出来的股数是不是小于等于0，小于等于0就说明买不了。)
            self.log(f"Calculated size is zero or negative ({size}). Cannot place order.", data=None)
            # 记录日志，提示计算出的仓位大小为零或负数，无法下单。 (记录日志，说算出来买不了，不买了。)
            return 0
            # 如果仓位大小小于等于0，则返回0，表示无法交易。 (如果算出来买不了，那就返回0，表示这次不买了。)

        max_pos_value = equity * self.params.max_position_per_etf_percent
        # 计算单个ETF允许的最大持仓市值，总净值乘以最大持仓比例。 (计算单个ETF最多能买多少钱的，用总资产乘以单个ETF最大仓位比例。)
        current_price_for_calc = data_close_price
        # 使用当前收盘价作为计算市值时的价格。 (用最新的收盘价来算算钱。)

        potential_trade_value = size * current_price_for_calc
        # 计算潜在交易的总市值，仓位大小乘以当前价格。 (算算如果按计划买这么多股，总共值多少钱。)

        if potential_trade_value > max_pos_value:
            # 检查潜在交易市值是否超过单个ETF最大持仓市值限制。 (判断算出来的要买的金额是不是超过了单个ETF的上限。)
            size = int(max_pos_value / current_price_for_calc / 100) * 100
            # 如果超过限制，则将仓位大小调整为不超过最大持仓市值的最大100股整数倍。 (如果超过了，那就减少买入股数，只买到上限允许的金额。)
            self.log(f"Size adjusted due to max position limit. New size: {size}", data=None)
            # 记录日志，提示仓位大小因最大持仓限制而调整。 (记录日志，说买太多超标了，减少到多少股。)

        potential_trade_value = size * current_price_for_calc
        # 重新计算调整后的潜在交易市值。 (重新算算调整后值多少钱。)
        if potential_trade_value > cash:
            # 检查调整后的潜在交易市值是否超过可用现金。 (看看算出来要买的金额是不是比现在手里的现金还多。)
            size = int(cash / current_price_for_calc / 100) * 100
            # 如果超过可用现金，则将仓位大小调整为不超过可用现金的最大100股整数倍。 (如果现金不够，那就再减少买入股数，只买现金够买的部分。)
            self.log(f"Size adjusted due to cash limit. New size: {size}", data=None)
            # 记录日志，提示仓位大小因现金限制而调整。 (记录日志，说现金不够买那么多了，减少到多少股。)

        return size
        # 返回最终计算出的、经过风险和资金限制调整的仓位大小。 (最终决定买多少股，返回这个股数。)

    def next(self):
        # 定义next函数，在每个数据点（通常是每个交易日）都会被调用一次，用于执行策略的主要逻辑。 (定义next函数，这是策略的核心，每天开盘后都要运行一遍，决定今天该干啥。)
        for i, d in enumerate(self.datas):
            # 遍历每个数据源，i是索引，d是数据对象。 (轮流检查每一只ETF。)
            position = self.getposition(d)
            # 获取当前数据源的持仓信息。 (看看现在手里有没有这只ETF的股票。)
            order = self.orders[d]
            # 获取当前数据源的订单状态。 (看看这只ETF有没有挂单。)

            if order:
                # 检查当前数据源是否有未完成的订单。 (判断这只ETF昨天下的指令还没成交。)
                continue
                # 如果有未完成的订单，则跳过当前数据源，处理下一个数据源。 (如果有挂单，那就先等着它的指令结果，去看下一只ETF。)

            if self.halt_trading:
                # 检查全局交易暂停状态。 (看看是不是因为之前亏太多暂停交易了。)
                continue
                # 如果全局交易暂停，则跳过当前数据源，处理下一个数据源。 (如果是暂停交易状态，那今天这只ETF啥也别干，去看下一只。)

            if not position:
                # 检查当前数据源是否没有持仓。 (如果现在这只ETF手里没货。)
                market_state = 'UNCERTAIN_DO_NOT_TRADE'
                # 初始化市场状态为'UNCERTAIN_DO_NOT_TRADE'（不确定，不交易）。 (先假设今天这只ETF市场情况不明朗，最好别交易。)
                is_trend_up = (self.closes[i][0] > self.emas_medium[i][0] > self.emas_long[i][0] and self.emas_medium[i][0] > self.emas_medium[i][-1] and self.emas_long[i][0] > self.emas_long[i][-1])
                # 判断是否为上升趋势：收盘价>中期EMA>长期EMA，且中期EMA和长期EMA均向上。 (判断这只ETF是不是牛市：短期均线在长期均线上方，而且两条线都在往上走。)
                is_range_confirmed = (not is_trend_up and abs(self.emas_medium[i][0] / self.emas_medium[i][-1] - 1) < 0.003 and abs(self.emas_long[i][0] / self.emas_long[i][-1] - 1) < 0.003 and self.adxs[i].adx[0] < 20 and (self.bbands[i].top[0] - self.bbands[i].bot[0]) / self.closes[i][0] < 0.07)
                # 判断是否为震荡市：非上升趋势，中期EMA和长期EMA近似走平，ADX值低，布林带宽度窄。 (判断这只ETF是不是震荡市：不是牛市，均线稍微有点动静没事，趋势强度弱，而且最近价格波动范围不大。)

                if is_trend_up:
                    # 如果判断为上升趋势。 (如果是牛市。)
                    market_state = 'TREND_UP'
                    # 将市场状态设置为'TREND_UP'（上升趋势）。 (那就标记一下，现在是上升趋势。)
                elif is_range_confirmed and self.p.etf_type == 'range':
                    # 如果判断为震荡市，并且该ETF类型设置为'range'（震荡型）。 (如果是震荡市，而且这个ETF适合"高抛低吸"。)
                    market_state = 'RANGE_CONFIRMED'
                    # 将市场状态设置为'RANGE_CONFIRMED'（确认震荡）。 (那就标记一下，现在是震荡市。)

                entry_signal = False
                # 初始化入场信号为False。 (先假设今天这只ETF没有买入信号。)
                potential_position_type = None
                # 初始化潜在持仓类型为None。 (先假设不知道要按哪种策略买这只ETF。)
                entry_price_calc = self.closes[i][0]
                # 假设以当前收盘价作为入场价进行计算。 (假设以收盘价买入，先用收盘价来算算。)

                if market_state == 'TREND_UP' and self.p.etf_type == 'trend':
                    # 如果市场状态为上升趋势，并且该ETF类型设置为'trend'（趋势型）。 (如果是上升趋势，而且这个ETF适合"追涨杀跌"。)
                    is_breakout = (self.closes[i][0] > self.highest_highs[i][-1] and self.volumes[i][0] > self.sma_volumes[i][0] * self.params.trend_volume_ratio_min)
                    # 判断是否为突破信号：当前收盘价创近期新高，且成交量放大。 (判断这只ETF是不是突破了：价格创了最近60天新高，而且交易量比平时大。)
                    is_pullback = (min(abs(self.lows[i][0]/self.emas_medium[i][0]-1), abs(self.lows[i][0]/self.emas_long[i][0]-1)) < 0.01 and self.closes[i][0] > self.opens[i][0])
                    # 判断是否为回调企稳信号：当日最低价接近均线，且当日收阳线。 (判断这只ETF是不是回调站稳了：价格跌到均线附近，但当天又涨回来了。)

                    if is_breakout or is_pullback:
                        # 如果出现突破信号或回调企稳信号。 (如果突破了或者回调站稳了。)
                        entry_signal = True
                        # 设置入场信号为True。 (标记：可以买这只ETF了！)
                        potential_position_type = 'trend'
                        # 设置潜在持仓类型为'trend'（趋势）。 (标记：这是按趋势策略买的。)
                        risk_per_trade_percent = self.params.max_risk_per_trade_trend
                        # 设置单笔交易风险比例为趋势策略的设定值。 (标记：这次交易最多亏总资金的1%。)
                        stop_loss_price_calc = entry_price_calc - self.params.trend_stop_loss_atr_mult * self.atrs[i][0]
                        # 使用ATR计算止损价，入场价减去ATR的倍数。 (根据这只ETF最近的平均波动幅度，算出止损价应该设在假定入场价下方多少。)

                        if stop_loss_price_calc < entry_price_calc:
                            # 检查止损价是否有效，即是否低于入场价。 (判断止损价是不是真的比买入价低，止损价必须比买入价低才行。)
                            risk_per_share = entry_price_calc - stop_loss_price_calc
                            # 计算每股风险金额。 (算一下如果买在这只ETF当前价，跌到止损价，每股会亏多少钱。)
                            if risk_per_share > 0:
                                # 检查每股风险是否大于0。 (判断每股风险是不是大于0，大于0才能算止盈。)
                                take_profit_price_calc = entry_price_calc + self.params.trend_take_profit_rratio * risk_per_share
                                # 根据盈亏比计算止盈价，入场价加上风险金额的倍数。 (根据设定的盈亏比（比如2倍），算出止盈价应该设在假定入场价上方多少。)
                            else:
                                entry_signal = False
                                # 如果每股风险不大于0，则取消入场信号。 (如果每股风险有问题，那就取消买入信号。)
                                self.log(f"Trend signal skipped: Stop loss {stop_loss_price_calc:.2f} not below entry {entry_price_calc:.2f}", data=d)
                                # 记录日志，提示因止损价不低于入场价而跳过趋势信号。 (记录日记：趋势信号跳过，因为止损价不在入场价下方。)

                elif market_state == 'RANGE_CONFIRMED' and self.p.etf_type == 'range':
                    # 如果市场状态为震荡市，并且该ETF类型设置为'range'（震荡型）。 (如果是震荡市，而且这个ETF适合"高抛低吸"。)
                    is_range_buy = (self.lows[i][0] <= self.bbands[i].bot[0] and self.closes[i][0] > self.bbands[i].bot[0] and self.rsis[i][0] < self.params.rsi_oversold)
                    # 判断是否为震荡买入信号：最低价触及或下穿布林带下轨，收盘价回到下轨之上，且RSI超卖。 (判断这只ETF是不是到底了：价格碰到或跌破布林带下轨，但当天收盘又涨回来了，并且RSI显示超卖。)

                    if is_range_buy:
                        # 如果出现震荡买入信号。 (如果满足上面的条件。)
                        entry_signal = True
                        # 设置入场信号为True。 (标记：可以买这只ETF了！)
                        potential_position_type = 'range'
                        # 设置潜在持仓类型为'range'（震荡）。 (标记：这是按震荡策略买的。)
                        risk_per_trade_percent = self.params.max_risk_per_trade_range
                        # 设置单笔交易风险比例为震荡策略的设定值。 (标记：这次交易最多亏总资金的0.5%。)
                        stop_loss_price_calc = self.lows[i][0] * (1 - self.params.range_stop_loss_buffer)
                        # 计算止损价，为信号K线最低价下方一定比例。 (把止损价设在触发信号那天最低价再低一点点的位置。)
                        take_profit_price_calc = self.bbands[i].mid[0]
                        # 计算止盈价，为布林带中轨价格。 (把止盈目标设在布林带的中线位置。)

                        if stop_loss_price_calc >= entry_price_calc:
                            # 检查止损价是否有效，即是否低于入场价。 (判断止损价是不是真的比买入价低，止损价必须比买入价低才行。)
                            entry_signal = False
                            # 如果止损价无效，则取消入场信号。 (如果止损价有问题，那就取消买入信号。)
                            self.log(f"Range signal skipped: Stop loss {stop_loss_price_calc:.2f} not below entry {entry_price_calc:.2f}", data=d)
                            # 记录日志，提示因止损价不低于入场价而跳过震荡信号。 (记录日记：震荡信号跳过，因为止损价不在入场价下方。)

                if entry_signal and stop_loss_price_calc is not None and entry_price_calc > stop_loss_price_calc:
                    # 如果有入场信号，且止损价已计算且有效（低于入场价）。 (如果决定要买这只ETF，而且算好了有效的止损价。)
                    size = self._calculate_trade_size(self.closes[i][0], entry_price_calc, stop_loss_price_calc, risk_per_trade_percent)
                    # 调用_calculate_trade_size方法计算仓位大小。 (让小工具帮忙算算买多少股。)

                    if size > 0:
                        # 检查计算出的仓位大小是否大于0。 (如果算了一圈下来，确实还能买 > 0 股这只ETF。)
                        self.log(f'CREATE BRACKET BUY ORDER, Size: {size}, StopPrice: {stop_loss_price_calc:.2f}, LimitPrice: {take_profit_price_calc if take_profit_price_calc else "N/A"}, Market State: {market_state}, Signal Type: {potential_position_type}', data=d)
                        # 记录创建买入括号订单的日志，包括仓位大小、止损价、止盈价（若有）、市场状态和信号类型。 (记录日记：准备买入（括号单）！买多少股，止损价，止盈价，当前市场状态，是按哪种策略买的。)

                        limit_exec_type = bt.Order.Limit if take_profit_price_calc is not None else None
                        # 如果止盈价已计算，则止盈单类型为限价单，否则为None。 (如果有止盈价，止盈单就用限价单，没有止盈价就不用止盈单。)

                        bracket_orders = self.buy_bracket(data=d, size=size, price=entry_price_calc, exectype=bt.Order.Limit, stopprice=stop_loss_price_calc, stopexec=bt.Order.Stop, limitprice=take_profit_price_calc, limitexec=limit_exec_type)
                        # 创建买入括号订单，包括主订单（限价买入）、止损单（市价卖出）和止盈单（限价卖出，若有）。 (下达买入括号单指令，包括买入单、止损单和止盈单。)
                        if bracket_orders and bracket_orders[0]:
                            # 检查括号订单是否成功创建且主订单存在。 (判断括号单是不是成功下单了，并且主订单存在。)
                            self.orders[d] = bracket_orders[0]
                            # 将当前数据源的订单状态更新为主订单。 (把当前ETF的订单状态更新为主订单，表示已经下单了。)
if __name__ == '__main__':
    # Python主程序入口，当直接运行此脚本时，以下代码会被执行。 (这是程序的入口，只有直接运行这个文件的时候，下面的代码才会跑。)
    cerebro = bt.Cerebro(stdstats=False)
    # 创建Cerebro引擎实例，stdstats=False表示禁用标准统计输出。 (创建一个交易回测的大脑，stdstats=False表示不显示默认的统计信息。)
    data_files = [r'D:\\BT2025\\datas\\510050_d.xlsx', r'D:\\BT2025\\datas\\510300_d.xlsx', r'D:\\BT2025\\datas\\159949_d.xlsx']
    # 定义包含Excel数据文件路径的列表。 (定义一个列表，里面放着三个Excel数据文件的路径，这三个文件就是我们要分析的ETF数据。)
    column_mapping = {'date': 'datetime', 'open': 'open', 'high': 'high', 'low': 'low', 'close': 'close', 'volume': 'volume'}
    # 定义Excel列名到Backtrader标准列名的映射字典。 (定义一个字典，用来告诉程序Excel文件里的列名分别对应Backtrader需要的标准名称。)
    openinterest_col = -1
    # 指定持仓量列索引为-1，表示数据中没有持仓量列。 (设置持仓量列的索引为-1，表示我们的数据里没有持仓量这一列。)
    fromdate = datetime.datetime(2015, 1, 1)
    # 设置回测的起始日期为2015年1月1日。 (设置回测开始的时间，从2015年1月1日开始。)
    todate = datetime.datetime(2024, 4, 30)
    # 设置回测的结束日期为2024年4月30日。 (设置回测结束的时间，到2024年4月30日结束。)

    print("开始加载数据...")
    # 打印提示信息，表示开始加载数据。 (打印一句话，提示用户：开始加载数据了。)
    for file_path in data_files:
        # 遍历数据文件路径列表。 (循环处理每个数据文件。)
        try:
            # 尝试执行以下代码，捕获可能发生的异常。 (尝试做下面的事情，如果出错了就跳到except那里。)
            dataframe = pd.read_excel(file_path)
            # 使用pandas读取Excel文件到DataFrame。 (用pandas读取Excel文件，把数据放到一个表格里。)
            dataframe.rename(columns=column_mapping, inplace=True)
            # 重命名DataFrame的列名，使其符合Backtrader标准。 (按照我们定义的字典，把表格的列名改成Backtrader认识的名字。)
            if 'datetime' in dataframe.columns:
                # 检查DataFrame中是否存在'datetime'列。 (判断表格里有没有日期时间这一列。)
                try:
                    # 尝试将'datetime'列转换为datetime对象。 (尝试把日期时间这一列的数据变成标准的日期时间格式。)
                    dataframe['datetime'] = pd.to_datetime(dataframe['datetime'])
                except Exception as e:
                    # 捕获日期时间转换异常。 (如果日期时间转换出错了。)
                    print(f"警告: 无法解析 {file_path} 中的日期时间列，请检查格式。错误: {e}")
                    # 打印警告信息，提示日期时间列解析失败，并显示错误信息。 (打印警告信息，告诉用户日期时间格式有问题，请检查。)
                    continue
                    # 跳过当前文件，继续处理下一个文件。 (跳过这个文件，不处理了，继续处理下一个。)
            else:
                # 如果DataFrame中不存在'datetime'列。 (如果表格里没有日期时间这一列。)
                print(f"错误: 在 {file_path} 中找不到映射后的 'datetime' 列。请确保Excel文件中有'日期'列，或正确修改脚本中的column_mapping。")
                # 打印错误信息，提示找不到'datetime'列。 (打印错误信息，告诉用户找不到日期时间列，请检查Excel文件或者列名映射。)
                continue
                # 跳过当前文件，继续处理下一个文件。 (跳过这个文件，不处理了，继续处理下一个。)
            dataframe.set_index('datetime', inplace=True)
            # 将'datetime'列设置为DataFrame的索引。 (把日期时间这一列变成表格的索引，方便按日期查找数据。)
            required_cols = ['open', 'high', 'low', 'close', 'volume']
            # 定义必需的OHLCV列名列表。 (定义一个列表，里面放着开盘价、最高价、最低价、收盘价、成交量这些必须有的列名。)
            if not all(col in dataframe.columns for col in required_cols):
                # 检查DataFrame是否缺少必需的OHLCV列。 (判断表格里是不是缺少了上面说的那些必须有的列。)
                print(f"错误: {file_path} 映射后缺少必需的列。")
                # 打印错误信息，提示缺少必需的列。 (打印错误信息，告诉用户缺少了必要的列。)
                print(f"可用的列: {dataframe.columns.tolist()}")
                # 打印可用的列名，帮助用户检查。 (打印现在表格里都有哪些列，方便用户检查是不是列名写错了。)
                continue
                # 跳过当前文件，继续处理下一个文件。 (跳过这个文件，不处理了，继续处理下一个。)
            dataframe = dataframe.loc[fromdate:todate]
            # 筛选DataFrame，只保留指定日期范围内的数据。 (只保留我们设定的回测时间段内的数据。)
            data = bt.feeds.PandasData(dataname=dataframe, fromdate=fromdate, todate=todate, datetime=None, open='open', high='high', low='low', close='close', volume='volume', openinterest=openinterest_col)
            # 创建PandasData数据源，使用处理后的DataFrame。 (用Backtrader的PandasData工具，把我们处理好的表格数据变成Backtrader能用的数据源。)
            data_name = os.path.basename(file_path).split('.')[0]
            # 从文件路径中提取数据名称。 (从文件路径里提取出文件名，作为这个数据源的名字。)
            cerebro.adddata(data, name=data_name)
            # 将数据源添加到Cerebro引擎中。 (把数据源添加到我们的大脑Cerebro里，让它可以用来做回测。)
            print(f"数据加载成功: {data_name}")
            # 打印数据加载成功的提示信息。 (打印一句话，告诉用户这个数据加载成功了。)

        except FileNotFoundError:
            # 捕获文件未找到异常。 (如果找不到文件。)
            print(f"错误: 文件未找到 {file_path}")
            # 打印文件未找到的错误信息。 (打印错误信息，告诉用户找不到文件。)
        except Exception as e:
            # 捕获其他所有异常。 (如果读取或者处理数据的时候出错了。)
            print(f"加载数据 {file_path} 时出错: {e}")
            # 打印加载数据出错的错误信息，并显示具体的错误原因。 (打印错误信息，告诉用户加载数据出错了，并显示具体的错误原因。)

    print("所有数据加载完成。")
    # 打印提示信息，表示所有数据加载完成。 (打印一句话，告诉用户所有数据都加载完了。)
    cerebro.optstrategy(AShareETFStrategy, etf_type='trend', ema_medium_period=range(40, 81, 10), ema_long_period=range(100, 141, 10), bbands_period=range(15, 26, 5), bbands_devfactor=[1.8, 2.0, 2.2])
    # 使用optstrategy进行策略参数优化，指定策略类和需要优化的参数范围。 (使用optstrategy进行参数优化，就是让程序自己尝试不同的参数组合，找到最好的。)
    cerebro.broker.setcash(500000.0)
    # 设置初始资金为500000.0。 (设置初始资金，回测一开始账户里有50万。)
    cerebro.broker.setcommission(commission=0.0003, stocklike=True)
    # 设置交易佣金为0.0003，stocklike=True表示按股票方式计算佣金。 (设置交易手续费，每次买卖都要交手续费，这里设置的是万分之三。)
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe_ratio', timeframe=bt.TimeFrame.Days, compression=252)
    # 添加夏普比率分析器，用于评估策略的风险调整后收益。 (添加夏普比率分析器，用来评价策略的好坏，夏普比率越高越好。)
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    # 添加最大回撤分析器，用于评估策略的最大亏损幅度。 (添加最大回撤分析器，用来看看策略最大亏损了多少。)
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
    # 添加收益率分析器，用于计算策略的总收益率。 (添加收益率分析器，用来计算策略一共赚了多少钱。)
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trade_analyzer')
    # 添加交易分析器，用于详细分析交易的各项指标。 (添加交易分析器，用来详细分析每次交易的情况，比如成功率、平均盈利等等。)

    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
    # 打印回测开始时的账户总价值。 (打印一句话，告诉用户回测开始的时候账户里有多少钱。)
    ema_medium_range = range(40, 81, 10)
    # 定义中期EMA周期参数的优化范围。 (定义中期EMA周期的优化范围，从40到80，每隔10取一个值。)
    ema_long_range = range(100, 141, 10)
    # 定义长期EMA周期参数的优化范围。 (定义长期EMA周期的优化范围，从100到140，每隔10取一个值。)
    bbands_period_range = range(15, 26, 5)
    # 定义布林带周期参数的优化范围。 (定义布林带周期的优化范围，从15到25，每隔5取一个值。)
    bbands_dev_range = [1.8, 2.0, 2.2]
    # 定义布林带标准差倍数参数的优化范围。 (定义布林带标准差倍数的优化范围，取1.8、2.0、2.2这三个值。)

    total_combinations = (len(list(ema_medium_range)) * len(list(ema_long_range)) * len(list(bbands_period_range)) * len(bbands_dev_range))
    # 计算参数优化的总组合数。 (计算总共有多少种参数组合，就是把上面定义的几个范围里的值都乘起来。)
    start_time = time.time()
    # 记录参数优化开始的时间。 (记录一下参数优化开始的时间，用来算算总共花了多久。)

    print('\n{:-^50}'.format(' 参数优化开始 '))
    # 打印参数优化开始的分割线和标题。 (打印一句话，提示用户参数优化开始了。)
    print('{:<20}: {}'.format('优化目标', '最大收益/最大回撤比'))
    # 打印优化目标。 (打印一句话，告诉用户优化的目标是啥，这里是最大收益回撤比。)
    print('\n{:-^50}'.format(' 参数范围 '))
    # 打印参数范围的分割线和标题。 (打印一句话，提示用户下面是参数的范围。)
    print('{:<20}: {} - {}, 步长 {}'.format('EMA中期', min(ema_medium_range), max(ema_medium_range), ema_medium_range.step))
    # 打印中期EMA周期参数的优化范围。 (打印中期EMA周期的优化范围，包括最小值、最大值和步长。)
    print('{:<20}: {} - {}, 步长 {}'.format('EMA长期', min(ema_long_range), max(ema_long_range), ema_long_range.step))
    # 打印长期EMA周期参数的优化范围。 (打印长期EMA周期的优化范围，包括最小值、最大值和步长。)
    print('{:<20}: {} - {}, 步长 {}'.format('布林带周期', min(bbands_period_range), max(bbands_period_range), bbands_period_range.step))
    # 打印布林带周期参数的优化范围。 (打印布林带周期的优化范围，包括最小值、最大值和步长。)
    print('{:<20}: {}'.format('布林带标准差', ', '.join(map(str, bbands_dev_range))))
    # 打印布林带标准差倍数参数的优化范围。 (打印布林带标准差倍数的优化范围，就是那三个值。)
    print('{:<20}: {}'.format('预计参数组数', total_combinations))
    # 打印预计的参数组合总数。 (打印一句话，告诉用户总共有多少种参数组合要测试。)
    print('-' * 50)
    # 打印分割线。 (打印一条分割线，好看一点。)

    results = cerebro.run(maxcpus=10)
    # 运行参数优化回测，maxcpus=10表示使用最多10个CPU核心并行计算。 (开始跑参数优化回测，用最多10个CPU核心同时计算，加快速度。)
    end_time = time.time()
    # 记录参数优化结束的时间。 (记录一下参数优化结束的时间，用来算算总共花了多久。)
    total_time = end_time - start_time
    # 计算参数优化总共耗时。 (计算参数优化总共花了多少时间。)
    actual_combinations = len(results) if results else 0
    # 获取实际运行的参数组合数。 (获取实际跑了多少组参数，有可能因为某些原因没跑完所有组合。)
    avg_time = total_time / actual_combinations if actual_combinations else 0
    # 计算每组参数的平均耗时。 (计算平均每组参数跑了多久。)

    print('\n{:=^50}'.format(' 优化完成统计 '))
    # 打印参数优化完成统计的分割线和标题。 (打印一句话，提示用户参数优化跑完了。)
    print('{:<20}: {:.2f}秒 ({:.2f}分钟)'.format('总用时', total_time, total_time/60))
    # 打印参数优化总共耗时，分别以秒和分钟显示。 (打印总共花了多少时间，包括秒和分钟。)
    print('{:<20}: {}'.format('实际参数组数', actual_combinations))
    # 打印实际运行的参数组合数。 (打印实际跑了多少组参数。)
    print('{:<20}: {:.2f}秒'.format('每组平均用时', avg_time))
    # 打印每组参数的平均耗时。 (打印平均每组参数花了多少时间。)
    print('=' * 50)
    # 打印分割线。 (打印一条分割线，好看一点。)

    if not results:
        # 检查回测结果是否为空。 (判断回测结果是不是空的，如果是空的说明出错了。)
        print("\n{:!^50}".format(' 错误 '))
        # 打印错误提示的分割线和标题。 (打印一句话，提示用户出错了。)
        print("没有策略成功运行。请检查数据加载是否有误。")
        # 打印错误信息，提示没有策略成功运行，建议检查数据加载。 (打印错误信息，告诉用户策略没跑起来，可能是数据加载有问题。)
        print('!' * 50)
        # 打印分割线。 (打印一条分割线，好看一点。)
    else:
        # 如果回测结果不为空，则继续处理结果。 (如果回测结果不是空的，说明跑成功了，继续处理结果。)
        best_ratio = float('-inf')
        # 初始化最佳收益回撤比为负无穷。 (初始化最佳收益回撤比为一个很小的负数，用来比较。)
        best_strat = None
        # 初始化最佳策略为None。 (初始化最佳策略为None，表示还没找到最佳策略。)

        print('\n{:=^50}'.format(' 参数优化结果 '))
        # 打印参数优化结果的分割线和标题。 (打印一句话，提示用户下面是参数优化的结果。)
        print('{:<12} {:<12} {:<12} {:<10} {:<10} {:<10} {:<10}'.format('EMA中期', 'EMA长期', '布林周期', '布林标差', '收益率%', '最大回撤%', '收益回撤比'))
        # 打印结果表格的表头。 (打印表格的表头，包括EMA中期、EMA长期、布林带周期、布林带标准差、收益率、最大回撤、收益回撤比。)
        print('-' * 80)
        # 打印表头下方的分割线。 (打印一条分割线，好看一点。)

        for strat in results:
            # 遍历每个策略回测结果。 (循环处理每个参数组合的回测结果。)
            params = strat[0].params
            # 获取当前策略的参数。 (拿到当前参数组合。)
            analyzers = strat[0].analyzers
            # 获取当前策略的分析器结果。 (拿到当前参数组合的分析结果。)
            returns = analyzers.returns.get_analysis()['rtot']
            # 从收益率分析器中获取总收益率。 (从收益率分析器里拿到总收益率。)
            max_drawdown = analyzers.drawdown.get_analysis().max.drawdown
            # 从最大回撤分析器中获取最大回撤。 (从最大回撤分析器里拿到最大回撤。)
            ratio = returns / max_drawdown if max_drawdown != 0 else float('inf')
            # 计算收益回撤比，如果最大回撤为0，则设为无穷大。 (计算收益回撤比，就是收益率除以最大回撤，如果最大回撤是0，就设为无穷大，表示非常好。)

            if ratio > best_ratio:
                # 如果当前收益回撤比大于最佳收益回撤比。 (判断当前的收益回撤比是不是比之前找到的最好的还要好。)
                best_ratio = ratio
                # 更新最佳收益回撤比。 (如果是更好的，那就更新最佳收益回撤比。)
                best_strat = strat[0]
                # 更新最佳策略。 (同时更新最佳策略，记录下这个参数组合。)

            print('{:<12} {:<12} {:<12} {:<10} {:<10.2f} {:<10.2f} {:<10.2f}'.format(params.ema_medium_period, params.ema_long_period, params.bbands_period, params.bbands_devfactor, returns * 100, max_drawdown, ratio))
            # 打印当前参数组合及其回测结果。 (打印当前参数组合的回测结果，包括参数值、收益率、最大回撤、收益回撤比。)

        if best_strat is not None:
            # 如果找到了最佳策略。 (如果找到了最佳策略，说明参数优化成功了。)
            print('\n{:=^50}'.format(' 最优参数组合 '))
            # 打印最优参数组合的分割线和标题。 (打印一句话，提示用户下面是最优的参数组合。)
            print('{:<20}: {}'.format('EMA中期', best_strat.params.ema_medium_period))
            # 打印最佳中期EMA周期参数。 (打印最佳的中期EMA周期参数。)
            print('{:<20}: {}'.format('EMA长期', best_strat.params.ema_long_period))
            # 打印最佳长期EMA周期参数。 (打印最佳的长期EMA周期参数。)
            print('{:<20}: {}'.format('布林带周期', best_strat.params.bbands_period))
            # 打印最佳布林带周期参数。 (打印最佳的布林带周期参数。)
            print('{:<20}: {}'.format('布林带标准差', best_strat.params.bbands_devfactor))
            # 打印最佳布林带标准差倍数参数。 (打印最佳的布林带标准差倍数参数。)
            returns = best_strat.analyzers.returns.get_analysis()['rtot']
            # 获取最佳策略的总收益率。 (拿到最佳策略的总收益率。)
            max_drawdown = best_strat.analyzers.drawdown.get_analysis().max.drawdown
            # 获取最佳策略的最大回撤。 (拿到最佳策略的最大回撤。)
            print('{:<20}: {:.2f}%'.format('总收益率', returns * 100))
            # 打印最佳策略的总收益率。 (打印最佳策略的总收益率，百分比显示。)
            print('{:<20}: {:.2f}%'.format('最大回撤', max_drawdown))
            # 打印最佳策略的最大回撤。 (打印最佳策略的最大回撤，百分比显示。)
            print('{:<20}: {:.2f}'.format('收益回撤比', best_ratio))
            # 打印最佳策略的收益回撤比。 (打印最佳策略的收益回撤比。)
            print('=' * 50)
            # 打印分割线。 (打印一条分割线，好看一点。)

        try:
            # 尝试执行以下绘图代码，捕获可能发生的异常。 (尝试画图，如果出错了就跳到except那里。)
            print("\n开始绘制图表...")
            # 打印提示信息，表示开始绘制图表。 (打印一句话，提示用户开始画图了。)
            # cerebro.plot(style='candlestick', barup='red', bardown='green', iplot=True, volume=True)
            # 调用Cerebro引擎的plot方法绘制回测结果图表，风格为k线图，上涨红色，下跌绿色，交互式显示，包含成交量。 (调用Cerebro的plot方法画图，画k线图，红色涨绿色跌，显示在网页上，带成交量。)
            print("图表绘制完成。")
            # 打印图表绘制完成的提示信息。 (打印一句话，告诉用户图画完了。)
        except Exception as e:
            # 捕获绘图过程中可能发生的异常。 (如果画图出错了。)
            print(f"\n绘制图表时出错: {e}")
            # 打印绘图出错的错误信息，并显示具体的错误原因。 (打印错误信息，告诉用户画图出错了，并显示具体的错误原因。)
            print("请尝试调整绘图参数或检查数据。")
            # 打印建议，提示用户调整绘图参数或检查数据。 (打印一句话，建议用户调整画图参数或者检查数据。)
