import backtrader as bt
# 导入backtrader库，用于量化交易策略的回测和开发。 (Import the backtrader library for quantitative trading strategy backtesting and development.)
import backtrader.indicators as btind
# 导入backtrader的指标模块，方便使用内置的技术指标。 (Import the indicators module from backtrader for easy use of built-in technical indicators.)
import pandas as pd
# 导入pandas库，用于数据处理和分析，特别是在处理优化结果时。 (Import the pandas library for data processing and analysis, especially when handling optimization results.)
import numpy as np
# 导入numpy库，提供高效的数值计算功能。 (Import the numpy library for efficient numerical computation.)
import time
# 导入time库，用于计算代码执行时间。 (Import the time library to calculate code execution time.)
import itertools
# 导入itertools库，提供用于创建迭代器的工具，在优化参数组合时使用。 (Import the itertools library for tools to create iterators, used for combining optimization parameters.)
from collections import OrderedDict
# 从collections模块导入OrderedDict，用于保持字典中元素的插入顺序，方便结果展示。 (Import OrderedDict from the collections module to maintain the insertion order of elements in a dictionary, useful for presenting results.)
from concurrent.futures import ProcessPoolExecutor, as_completed
# 从concurrent.futures模块导入ProcessPoolExecutor和as_completed，用于并行执行优化任务，提高效率。 (Import ProcessPoolExecutor and as_completed from the concurrent.futures module for parallel execution of optimization tasks, improving efficiency.)
# ================= 日志系统所需导入 START =================
import logging
# 导入logging库，用于实现日志记录功能。 (Import the logging library for implementing logging functionality.)
import logging.handlers
# 导入logging.handlers模块，提供高级日志处理方式，如队列处理。 (Import the logging.handlers module for advanced logging handlers like queue handling.)
import json
# 导入json库，用于处理JSON数据格式，日志将以此格式存储。 (Import the json library for handling JSON data format, as logs will be stored in this format.)
import datetime
# 导入datetime库，用于处理日期和时间，日志时间戳需要用到。 (Import the datetime library for handling dates and times, needed for log timestamps.)
import uuid
# 导入uuid库，用于生成唯一的标识符，如交易周期ID。 (Import the uuid library for generating unique identifiers, such as trade cycle IDs.)
import os
# 导入os库，用于与操作系统交互，如创建日志目录。 (Import the os library for interacting with the operating system, like creating log directories.)
import threading
# 导入threading库，虽然此处可能未使用，但异步日志有时会涉及。 (Import the threading library; although possibly unused here, async logging sometimes involves it.)
import queue
# 导入queue库，用于创建队列，是异步日志处理的核心组件。 (Import the queue library for creating queues, a core component of asynchronous logging.)
import pytz  # 用于处理时区
# 导入pytz库，用于处理时区信息，确保日志时间戳的一致性。 (Import the pytz library for handling timezone information, ensuring consistency in log timestamps.)
# ================= 日志系统所需导入 END ===================


# ================= 自定义 JSON Formatter START =================
class JsonFormatter(logging.Formatter):
    # 定义一个名为 JsonFormatter 的类，继承自 logging.Formatter，用于将日志记录格式化为 JSON 字符串。 (创建一个日志格式化工具，专门把日志信息变成 JSON 格式。)
    def format(self, record):
        # 定义 format 方法，负责将单个日志记录（record）转换为字符串。 (定义如何转换一条日志记录。)
        log_entry = {}
        # 创建一个空字典，用于存放最终的日志条目。 (准备一个空的盒子，放日志信息。)
        if isinstance(record.msg, dict):
            # 检查日志消息主体（record.msg）是否已经是字典格式。 (看看传进来的日志信息是不是已经是整理好的盒子了。)
            log_entry.update(record.msg)
            # 如果是字典，直接将其内容更新到 log_entry 中。 (如果是，直接把里面的东西倒进我们的最终盒子。)
        else:
            # 如果不是字典，将其作为 'message' 字段的值。 (如果不是，就把这条原始信息当作一个叫 'message' 的标签放进盒子里。)
            log_entry['message'] = record.getMessage()
            # 将原始日志消息作为 'message' 字段的值。 (Store the original log message under the 'message' key.)

        # 添加一些标准的日志记录信息，如果它们不在消息主体中。 (补充一些标准信息，比如时间、日志级别等，如果最终盒子里还没有的话。)
        if 'timestamp' not in log_entry:
            # 如果 'timestamp' 不在，添加 ISO 8601 格式的 UTC 时间戳。 (如果没记时间，就记下现在的 UTC 标准时间。)
            log_entry['timestamp'] = datetime.datetime.now(pytz.utc).isoformat() + 'Z'
            # 如果日志条目中没有 'timestamp' 键，则添加当前 UTC 时间的 ISO 格式字符串。 (If 'timestamp' key is not in the log entry, add the current UTC time in ISO format.)
        if 'level' not in log_entry:
            # 如果 'level' 不在，添加日志级别名称（例如 'INFO', 'ERROR'）。 (如果没记重要程度，就记一下。)
            log_entry['level'] = record.levelname
            # 如果日志条目中没有 'level' 键，则添加日志级别名称。 (If 'level' key is not in the log entry, add the log level name.)
        if hasattr(record, 'strategy_id') and 'strategy_id' not in log_entry:
             # 如果记录对象有 strategy_id 属性且最终日志条目没有，添加它。 (如果记录里有策略 ID 但最终盒子里没有，加上。)
            log_entry['strategy_id'] = record.strategy_id
            # 如果日志记录对象有 strategy_id 属性且日志条目中没有，则添加它。 (If the log record object has a strategy_id attribute and it's not in the log entry, add it.)
        if hasattr(record, 'data_id') and 'data_id' not in log_entry:
            # 如果记录对象有 data_id 属性且最终日志条目没有，添加它。 (如果记录里有数据 ID 但最终盒子里没有，加上。)
            log_entry['data_id'] = record.data_id
            # 如果日志记录对象有 data_id 属性且日志条目中没有，则添加它。 (If the log record object has a data_id attribute and it's not in the log entry, add it.)

        # 处理日志记录中的异常信息。 (如果记录中有错误信息，也加到盒子里。)
        if record.exc_info:
            # 如果存在异常信息。
            if not record.exc_text:
                # 如果异常文本不存在，则格式化异常信息。
                record.exc_text = self.formatException(record.exc_info)
                # 如果记录中有异常信息但没有格式化文本，则格式化它。 (If the record has exception info but no formatted text, format it.)
        if record.exc_text:
            # 如果异常文本存在，将其添加到日志条目中。
            log_entry['exception'] = record.exc_text
            # 如果格式化后的异常文本存在，将其添加到日志条目中。 (If the formatted exception text exists, add it to the log entry.)
        if record.stack_info:
             # 如果存在堆栈信息，格式化并添加到日志条目中。
            log_entry['stack_trace'] = self.formatStack(record.stack_info)
            # 如果记录中有堆栈信息，格式化并添加到日志条目中。 (If the record has stack info, format it and add it to the log entry.)

        # 将字典转换为 JSON 字符串，确保使用 ASCII 编码并按键排序。 (把整理好的盒子里的所有东西变成一行 JSON 文本。)
        return json.dumps(log_entry, sort_keys=True, ensure_ascii=False)

# ================= 自定义 JSON Formatter END ===================


# ================== 日志队列处理线程 START ==================
# (这个部分是异步写入日志的核心，确保日志写入不阻塞策略运行)
log_queue = queue.Queue(-1)  # 使用无限大小的队列 (创建一个队列，用来临时存放日志)
log_listener = None  # 初始化日志监听器变量 (准备一个监听器，后面会用到)


def setup_log_listener(handler):
    # 定义一个函数来设置和启动日志监听器。 (定义一个启动监听器的函数。)
    global log_listener
    # 声明 log_listener 是全局变量。 (告诉程序我们要用全局的那个监听器。)
    log_listener = logging.handlers.QueueListener(
        log_queue, handler, respect_handler_level=True)
    # 创建 QueueListener 实例，连接队列和处理器。 (创建监听器，让它看着队列，并告诉它日志要交给哪个处理器处理。)
    log_listener.start()
    # 启动监听器线程。 (让监听器开始工作。)


def stop_log_listener():
    # 定义一个函数来停止日志监听器。 (定义一个停止监听器的函数。)
    global log_listener
    # 声明 log_listener 是全局变量。 (告诉程序我们要用全局的那个监听器。)
    if log_listener:
        # 如果监听器存在。 (如果监听器在工作。)
        log_listener.stop()
        # 停止监听器线程。 (让监听器停止工作。)
# ================== 日志队列处理线程 END ==================


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
        # ================= 日志系统参数 START =================
        ('log_path', 'logs'),  # 日志文件存放目录 (日志文件放哪里)
        # 日志文件名格式模板 (日志文件叫什么名字的规则)
        ('log_filename_pattern',
         '{strategy_name}_{data_name}_{timestamp:%Y%m%d_%H%M%S}.log.jsonl'),
        ('log_level', logging.INFO),  # 日志记录级别 (记录多详细的信息，INFO级别比较常用)
        # ================= 日志系统参数 END ===================
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
        # (Define the order notification function notify_order, called when order status changes, parameter order is the order object.)

        # --- 日志记录：订单状态更新 ---
        # (Logging: Order Status Update)
        trade_id = self.order_ref_to_trade_id_map.get(
            order.ref, 'ORPHANED_ORDER')  # 尝试获取交易周期ID (Try to get trade cycle ID)
        # 查找这个订单对应的交易追踪号，找不到就标记为"孤儿订单"。 (查一下这个订单是哪个交易的，查不到就标为"孤儿"。)
        exec_details = {}
        # 初始化一个空字典，用于存放订单执行详情。 (准备一个空盒子，放订单执行细节。)
        if order.executed.price:
            # 如果订单有执行价格。 (如果订单成交了。)
            exec_details['price'] = order.executed.price
            # 记录执行价格。 (记下成交价。)
            exec_details['value'] = order.executed.value
            # 记录执行价值。 (记下成交金额。)
            exec_details['commission'] = order.executed.comm
            # 记录执行佣金。 (记下佣金。)
            exec_details['size'] = order.executed.size  # 已执行数量 (Executed size)
            # 记录已执行数量。 (记下成交了多少。)
        self.log_event('ORDER_STATUS_UPDATE',
                       data_feed=order.data,  # 关联数据源 (Associate data feed)
                       order_ref=order.ref,  # 订单引用 (Order reference)
                       # 使用查找到的交易ID (Use the retrieved trade ID)
                       trade_cycle_id=trade_id,
                       status=order.getstatusname(),  # 订单状态名称 (Order status name)
                       # 执行详情（如果存在） (Execution details (if any))
                       exec_details=exec_details if exec_details else None,
                       # 剩余未执行数量 (Remaining size)
                       remaining_size=order.executed.remsize,
                       order_type=order.ordtypename(),  # 订单类型 (Order type)
                       order_details={  # 订单创建时的细节 (Details from order creation)
                           # 创建时价格 (Creation price)
                           'created_price': order.created.price,
                           # 创建时大小 (Creation size)
                           'created_size': order.created.size,
                           'isbuy': order.isbuy(),  # 是否是买单 (Is it a buy order?)
                           'issell': order.issell()  # 是否是卖单 (Is it a sell order?)
                       })
        # 记录订单状态更新事件，包含各种详细信息。 (记录订单状态变化的日志，包括追踪号、状态、成交细节等。)

        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            # 如果订单是已提交或已接受状态，无需操作。 (如果订单只是刚提交或者被接受了，暂时不用做什么。)
            # self.log(f'Order {order.ref} Submitted/Accepted', data=order.data) # 旧日志 (Old log)
            return

        # Check if an order has been completed
        # 检查订单是否已完成 (Check if an order has been completed)
        # Attention: broker could reject order if not enough cash
        # 注意：如果现金不足，经纪商可能会拒绝订单 (Attention: broker could reject order if not enough cash)
        if order.status in [order.Completed]:
            # 如果订单状态是已完成。 (如果订单完成了。)
            if order.isbuy():
                # 如果是买单。 (如果是买单。)
                # self.log(
                #     f'BUY EXECUTED, Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f}, Comm {order.executed.comm:.2f}',
                #     data=order.data
                # ) # 旧日志 (Old log)
                self.buyprice = order.executed.price
                # 记录买入价格。 (记下买入价。)
                self.buycomm = order.executed.comm
                # 记录买入佣金。 (记下买入佣金。)
                self.open_trades += 1  # 增加持仓交易计数 (Increment open trades count)
                # 当前持仓交易数量加 1。 (手上的单子数量加 1。)
                # risk_per_trade = self.params.risk_per_trade_percent * self.broker.getvalue() / 100.0
                # self.cumulative_risk_units += risk_per_trade # 累加风险 (Accumulate risk) - 移动到下单处更准确 (Moved to order placement for accuracy)
                # self.log_event('RISK_UPDATE_ON_BUY', current_risk_units=self.cumulative_risk_units, added_risk=risk_per_trade, data_feed=order.data)

            elif order.issell():
                # 如果是卖单。 (如果是卖单。)
                # self.log(f'SELL EXECUTED, Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f}, Comm {order.executed.comm:.2f}', data=order.data) # 旧日志 (Old log)
                self.open_trades -= 1  # 减少持仓交易计数 (Decrement open trades count)
                # 当前持仓交易数量减 1。 (手上的单子数量减 1。)
                # --- 风险在 notify_trade 中根据 PNL 释放或调整更合理 ---
                # --- Risk adjustment based on PNL in notify_trade is more appropriate ---
                # closed_trade_risk = ??? # 难以直接在此处确定关闭交易的初始风险 (Difficult to determine initial risk here)
                # self.cumulative_risk_units -= closed_trade_risk # 释放风险 (Release risk)
                # self.log_event('RISK_UPDATE_ON_SELL', current_risk_units=self.cumulative_risk_units, released_risk=closed_trade_risk, data_feed=order.data)

            # 记录执行时的 K 线索引 (Record bar index when executed)
            self.bar_executed = len(self)
            # 记下这笔交易完成时是第几根 K 线。 (记下完成时是第几根 K 线。)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            # 如果订单被取消、因保证金不足或被拒绝。 (如果订单被取消、钱不够或者被拒了。)
            # self.log(f'Order {order.ref} Canceled/Margin/Rejected', data=order.data) # 旧日志 (Old log)
            # --- 如果是开仓订单失败，需要考虑回滚风险累加 ---
            # --- If an opening order fails, need to consider rolling back risk accumulation ---
            trade_id_for_failed_order = self.order_ref_to_trade_id_map.get(
                order.ref)
            # 获取失败订单对应的交易 ID。 (拿到这个失败订单的交易追踪号。)
            if trade_id_for_failed_order and trade_id_for_failed_order == self.current_trade_id:
                # 如果找到了交易 ID 且它就是当前正在尝试的交易。 (如果找到了追踪号，而且就是我们当前正在操作的这个。)
                # 这是一个尝试开新仓但失败的订单 (This was an attempt to open a new position that failed)
                # 重置 current_trade_id，因为这个交易周期并未成功开启
                # (Reset current_trade_id as this trade cycle didn't successfully start)
                self.current_trade_id = None
                # 把当前交易追踪号清空，因为这个交易没开始成功。)
                # 注意：风险计算的逻辑需要根据具体实现来调整 (Note: Risk calculation logic needs adjustment based on specific implementation)
                # self.log_event('TRADE_CYCLE_ABORTED', reason=order.getstatusname(), order_ref=order.ref, data_feed=order.data)
                # 记录交易周期中止事件。 (记一笔日志，说这个交易周期被中止了。)

            # 清理映射 (Clean up mapping)
            if order.ref in self.order_ref_to_trade_id_map:
                # 如果订单引用在映射表中。 (如果订单号在我们的对应表里。)
                del self.order_ref_to_trade_id_map[order.ref]
                # 从映射表中删除该订单引用。 (把它从对应表里删掉。)
                # self.log_event('ORDER_REF_MAP_CLEANUP', reason='Order Failed/Cancelled', order_ref=order.ref, data_feed=order.data) # 可选日志 (Optional log)

        # Write down: no pending order
        # 标记：没有待处理订单 (Write down: no pending order)
        self.order = None
        # 将 self.order 设置为 None，表示当前没有待处理订单。 (把 self.order 清空，表示现在没有订单在等结果了。)

    def notify_trade(self, trade):
        # 定义交易通知函数notify_trade，当交易（一买一卖）完成时被调用，参数trade是交易对象。 (定义交易完成通知函数，当一次完整的买卖结束了，程序会跑这个函数来通知你。)
        # (Define the trade notification function notify_trade, called when a trade (buy and sell) is completed, parameter trade is the trade object.)

        # --- 日志记录：交易关闭/更新 ---
        # (Logging: Trade Closed/Update)
        trade_id = 'UNKNOWN_TRADE'  # 默认交易 ID (Default trade ID)
        # 设置一个默认的交易追踪号。 (先假设不知道是哪个交易。)
        # 存储交易涉及的订单引用 (Store order references involved in the trade)
        order_refs_in_trade = []
        # 准备一个列表，放这个交易涉及到的所有订单号。 (准备一个空列表，放这次交易用到的所有订单号。)

        # 新版 backtrader (Newer backtrader version)
        if hasattr(trade, 'orders') and trade.orders:
            # 如果 trade 对象有 orders 属性且不为空 (新版 backtrader)。 (如果 trade 对象里有 orders 列表并且不是空的（新版 backtrader）。)
            # 直接获取订单引用列表 (Get the list of order references directly)
            order_refs_in_trade = [o.ref for o in trade.orders]
            # 直接拿到所有相关订单的引用号。 (直接拿到所有订单的引用号。)
            # 尝试从第一个订单引用获取交易ID (Try to get trade ID from the first order reference)
            if order_refs_in_trade:
                # 如果订单引用列表不为空。 (如果拿到了订单号。)
                trade_id = self.order_ref_to_trade_id_map.get(
                    order_refs_in_trade[0], 'ORPHANED_TRADE_BY_ORDER')
                # 尝试用第一个订单号去查交易追踪号，找不到就标记为"孤儿交易"。 (用第一个订单号去查追踪号，查不到就标为"孤儿"。)
        # 兼容旧版或特定情况 (Compatibility for older versions or specific cases)
        elif hasattr(trade, 'ref') and trade.ref in self.order_ref_to_trade_id_map:
            # 如果 trade 对象有 ref 属性（可能是订单引用）并且在映射表中。 (如果 trade 对象只有一个 ref 属性并且在我们的对应表里。)
            # 将单个引用放入列表 (Put the single reference into a list)
            order_refs_in_trade = [trade.ref]
            # 把这个单独的引用号放到列表里。)
            trade_id = self.order_ref_to_trade_id_map.get(
                trade.ref, 'ORPHANED_TRADE_BY_REF')
            # 查找交易追踪号，找不到标记为"孤儿"。 (用这个引用号去查追踪号，查不到标为"孤儿"。)

        if not trade.isclosed:
            # 如果交易尚未关闭（例如部分平仓更新）。 (如果这笔交易还没完全结束（比如只平了一部分仓）。)
            # 记录交易更新事件 (Log trade update event)
            self.log_event('TRADE_UPDATE',
                           data_feed=trade.data,  # 关联数据源 (Associate data feed)
                           trade_cycle_id=trade_id,  # 交易周期ID (Trade cycle ID)
                           trade_ref=trade.ref,  # 交易引用 (Trade reference)
                           # 交易状态 (Trade status)
                           status=trade.status_names[trade.status],
                           size=trade.size,  # 当前大小 (Current size)
                           price=trade.price,  # 当前价格 (Current price)
                           value=trade.value,  # 当前价值 (Current value)
                           pnl=trade.pnl,  # 当前 PNL (Current PNL)
                           pnlcomm=trade.pnlcomm,  # 当前净 PNL (Current net PNL)
                           # 累积佣金 (Accumulated commission)
                           commission=trade.commission
                           )
            # 记录交易更新的日志。 (记录交易更新的日志。)
            return  # 返回，因为交易还未结束 (Return as the trade is not yet finished)
            # 交易还没结束，先不往下走了。 (交易还没完，先停在这里。)

        # --- 交易已关闭 ---
        # (Trade is closed)
        # self.log(f'OPERATION PROFIT, GROSS {trade.pnl:.2f}, NET {trade.pnlcomm:.2f}', data=trade.data) # 旧日志 (Old log)

        self.log_event('TRADE_CLOSED',
                       data_feed=trade.data,  # 关联数据源 (Associate data feed)
                       trade_cycle_id=trade_id,  # 交易周期ID (Trade cycle ID)
                       trade_ref=trade.ref,  # 交易引用 (Trade reference)
                       pnl=trade.pnl,  # 毛利润/亏损 (Gross profit/loss)
                       pnlcomm=trade.pnlcomm,  # 净利润/亏损 (Net profit/loss)
                       commission=trade.commission,  # 总佣金 (Total commission)
                       # 持仓 K 线数 (Duration in bars)
                       duration_bars=trade.barlen,
                       open_datetime=trade.open_datetime().isoformat(
                       ) if trade.dtopen else None,  # 开仓时间 (Open datetime)
                       close_datetime=trade.close_datetime().isoformat(
                       ) if trade.dtclose else None,  # 平仓时间 (Close datetime)
                       size=trade.size,  # 最终大小（应为0） (Final size (should be 0))
                       # 初始开仓大小 (Initial open size)
                       initial_size=trade.history[0].event.size if trade.history else None,
                       # 交易方向 (Position type)
                       position_type='Long' if trade.long else 'Short'
                       )
        # 记录交易关闭事件，包含盈亏、时长等信息。 (记录交易关闭的日志，包括赚了多少钱、持了多久等。)

        # --- 清理 trade_cycle_id 映射 ---
        # (Clean up trade_cycle_id mapping)
        cleaned_refs = []  # 记录已清理的引用 (Record cleaned references)
        # 准备一个列表，记录删掉了哪些订单号。 (准备一个列表，记下删了哪些订单号。)
        if trade_id != 'ORPHANED_TRADE_BY_ORDER' and trade_id != 'ORPHANED_TRADE_BY_REF' and trade_id != 'UNKNOWN_TRADE':
            # 如果交易不是孤儿或未知。 (如果这个交易不是孤儿或者未知的。)
            refs_to_remove = [
                ref for ref, t_id in self.order_ref_to_trade_id_map.items() if t_id == trade_id]
            # 找到所有与此交易周期ID关联的订单引用。 (找出对应表里所有属于这个交易追踪号的订单号。)
            for ref in refs_to_remove:
                # 遍历找到的订单引用。 (检查每一个找到的订单号。)
                del self.order_ref_to_trade_id_map[ref]
                # 从映射表中删除。 (从对应表里删掉。)
                cleaned_refs.append(ref)
                # 添加到已清理列表。 (记一下这个订单号被删了。)

            # 如果这个关闭的交易是当前活跃的交易，则重置 current_trade_id
            # (If this closed trade was the currently active one, reset current_trade_id)
            if self.current_trade_id == trade_id:
                # 如果关闭的这个正好是当前正在进行的交易。 (如果关掉的正好是当前进行的这个。)
                self.current_trade_id = None
                # 将当前交易追踪号设为 None。 (把当前交易追踪号清空。)
                # self.log_event('CURRENT_TRADE_CYCLE_CLOSED', closed_trade_id=trade_id, data_feed=trade.data) # 可选日志 (Optional log)
        # else:
            # 对于孤儿交易，尝试使用 trade.orders 中的引用进行清理 (For orphaned trades, try cleaning using refs from trade.orders)
            # for ref in order_refs_in_trade:
            #     if ref in self.order_ref_to_trade_id_map:
            #         del self.order_ref_to_trade_id_map[ref]
            #         cleaned_refs.append(ref)
            # pass # 孤儿交易无需特殊处理映射清理，因为它们本就不在映射中或 ID 未知 (Orphaned trades don't need special map cleanup as they weren't mapped or ID was unknown)

        # self.log_event('ORDER_REF_MAP_CLEANUP', reason='Trade Closed', cleaned_refs=cleaned_refs, trade_id=trade_id, data_feed=trade.data) # 可选日志 (Optional log)

        # --- 更新风险状态 ---
        # (Update risk status)
        # 交易关闭，风险单位清零或根据策略调整 (Trade closed, risk units reset or adjusted based on strategy)
        # 这里假设每个关闭的交易完全释放其风险，简化处理 (Assuming each closed trade fully releases its risk for simplicity)
        # 更复杂的逻辑可能需要跟踪每个交易的初始风险 (More complex logic might need to track initial risk per trade)
        # self.cumulative_risk_units = max(0.0, self.cumulative_risk_units - ???) # 需要确定释放多少风险 (Need to determine how much risk to release)
        # self.log_event('RISK_UPDATE_ON_TRADE_CLOSE', current_risk_units=self.cumulative_risk_units, pnlcomm=trade.pnlcomm, data_feed=trade.data)

        # 更新最高水位线 (Update high water mark)
        current_value = self.broker.getvalue()
        # 获取当前总资产。 (拿到现在的总资产。)
        if current_value > self.high_water_mark:
            # 如果当前总资产超过了历史最高。 (如果现在的钱比以前最多的时候还多。)
            # self.log_event('HIGH_WATER_MARK_UPDATE', old_hwm=self.high_water_mark, new_hwm=current_value, data_feed=trade.data) # 可选日志 (Optional log)
            self.high_water_mark = current_value
            # 更新最高水位线。 (更新历史最高纪录。)

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
        # (Define the next function, called once per data point (usually each trading day), for executing the main strategy logic.)

        # --- 检查是否暂停交易 ---
        # (Check if trading is halted)
        current_dt = self.datas[0].datetime.datetime(
            0)  # 获取当前时间 (Get current time)
        # 拿到当前的回测时间。 (拿到现在的模拟时间。)
        if self.halt_trading_until and current_dt < self.halt_trading_until:
            # 如果设置了暂停交易时间点，并且当前时间还没到那个点。 (如果之前设置了暂停交易，并且还没到恢复时间。)
            # self.log(f'Trading halted until {self.halt_trading_until}. Skipping bar.', dt=current_dt) # 旧日志 (Old log)
            self.log_event('TRADING_HALTED_SKIP', halt_until=self.halt_trading_until.isoformat(
            ), current_time=current_dt.isoformat())
            # 记录交易暂停跳过事件。 (记一笔日志，说因为暂停交易，这根K线跳过了。)
            return  # 跳过当前 K 线 (Skip current bar)
            # 直接返回，不做任何操作。 (这根K线啥也不干。)
        elif self.halt_trading_until and current_dt >= self.halt_trading_until:
            # 如果到了或超过了暂停交易的恢复时间点。 (如果到了或者超过了恢复时间。)
            # self.log(f'Trading resumed at {current_dt}.', dt=current_dt) # 旧日志 (Old log)
            self.log_event('TRADING_RESUMED', resume_time=current_dt.isoformat(
            ), previous_halt_until=self.halt_trading_until.isoformat())
            # 记录交易恢复事件。 (记一笔日志，说交易恢复了。)
            self.halt_trading_until = None  # 清除暂停标记 (Clear halt flag)
            # 清除暂停交易的标记。 (把暂停标记去掉。)

        # --- 遍历所有数据源执行策略逻辑 ---
        # (Iterate through all data feeds to execute strategy logic)
        for d in self.datas:
            # 遍历每一个数据源。 (检查每一个我们关心的数据（比如不同的股票ETF）。)
            # Iterate through each data feed.
            data_name = d._name  # 获取数据源名称 (Get data feed name)
            # # 拿到当前数据源的名字。 (拿到当前这个数据的名字。)
            # close = self.d_close[data_name][0] # 获取当前收盘价 (Get current close price)
            # # 拿到当前这个数据的收盘价。 (拿到它的收盘价。)
            # # open_ = self.d_open[data_name][0] # 获取当前开盘价 (Get current open price)
            # # high = self.d_high[data_name][0] # 获取当前最高价 (Get current high price)
            # # low = self.d_low[data_name][0] # 获取当前最低价 (Get current low price)
            # inds = self.inds[data_name] # 获取当前数据源的指标 (Get indicators for the current data feed)
            # # 拿到当前这个数据对应的所有指标工具。 (拿到跟它相关的指标工具。)

            # # --- 记录市场状态评估 ---
            # # (Log Market State Assessment)
            # market_state_indicators = { # 收集用于市场判断的指标值 (Collect indicator values used for market judgment)
            #     'ema_short': inds['ema_short'][0], # 短期 EMA (Short-term EMA)
            #     'ema_medium': inds['ema_medium'][0], # 中期 EMA (Medium-term EMA)
            #     'ema_long': inds['ema_long'][0], # 长期 EMA (Long-term EMA)
            #     'bb_mid': inds['bbands'].lines.mid[0], # 布林带中轨 (Bollinger Bands Midline)
            #     'bb_top': inds['bbands'].lines.top[0], # 布林带上轨 (Bollinger Bands Top)
            #     'bb_bot': inds['bbands'].lines.bot[0], # 布林带下轨 (Bollinger Bands Bottom)
            #     'atr': inds['atr'][0] # ATR
            # }
            # # 把当前几个关键指标的值收集起来。 (把几个关键指标现在的值收在一起。)
            # self.log_event('MARKET_STATE_ASSESSED', data_feed=d, indicators=market_state_indicators)
            # # 记录市场状态评估事件。 (记一笔日志，说我们评估了市场状态，并附上指标值。)

            # Check if an order is pending ... if yes, we cannot send a 2nd one
            # 检查是否有待处理订单...如果是，则不能发送第二个订单 (Check if an order is pending ... if yes, we cannot send a 2nd one)
            if self.order:
                # 如果 self.order 不是 None（即有待处理订单）。 (如果 self.order 里面有东西（说明有个订单还没完成）。)
                # If self.order is not None (i.e., there is a pending order).
                # self.log_event('PENDING_ORDER_SKIP', data_feed=d, order_ref=self.order.ref) # 可选日志 (Optional log)
                continue  # 跳过当前数据源的处理 (Skip processing for this data feed)
                # 跳过这个数据，处理下一个。 (这个数据先不处理了，去看下一个。)

            # Check if we are in the market
            # 检查我们是否在市场中（即是否持仓） (Check if we are in the market (i.e., holding a position))
            position_size = self.getposition(d).size
            # 获取当前数据源的持仓大小。 (看看当前这个数据我们手里有多少。)

            # --- 定义入场和出场条件 ---
            # (Define entry and exit conditions)
            # is_bullish = inds['ema_short'][0] > inds['ema_medium'][0] and inds['ema_medium'][0] > inds['ema_long'][0] # 牛市条件 (Bullish condition)
            # # 判断是不是牛市：短期线在中期线之上，中期线在长期线之上。 (判断是不是牛市：短期均线上穿中期，中期上穿长期。)
            # is_bearish = inds['ema_short'][0] < inds['ema_medium'][0] and inds['ema_medium'][0] < inds['ema_long'][0] # 熊市条件 (Bearish condition)
            # # 判断是不是熊市：短期线在中期线之下，中期线在长期线之下。 (判断是不是熊市：短期均线下穿中期，中期下穿长期。)
            # cross_up_medium = bt.indicators.CrossOver(inds['ema_short'], inds['ema_medium'])[0] > 0 # 短期上穿中期 (Short crosses over medium)
            # # 判断短期线是否刚刚上穿中期线。 (判断短期 EMA 是不是刚上穿中期 EMA。)
            # cross_down_medium = bt.indicators.CrossDown(inds['ema_short'], inds['ema_medium'])[0] > 0 # 短期下穿中期 (Short crosses down medium)
            # # 判断短期线是否刚刚下穿中期线。 (判断短期 EMA 是不是刚下穿中期 EMA。)
            # # close_over_long = close > inds['ema_long'][0] # 收盘价在长期均线之上 (Close price is above long-term average)
            # # close_under_long = close < inds['ema_long'][0] # 收盘价在长期均线之下 (Close price is below long-term average)
            # close_over_bb_mid = close > inds['bbands'].lines.mid[0] # 收盘价在布林中轨之上 (Close price is above Bollinger midline)
            # # 判断收盘价是否在布林带中轨之上。 (判断收盘价是不是在中轨上面。)
            # close_under_bb_mid = close < inds['bbands'].lines.mid[0] # 收盘价在布林中轨之下 (Close price is below Bollinger midline)
            # # 判断收盘价是否在布林带中轨之下。 (判断收盘价是不是在中轨下面。)

            # --- 计算止损位和潜在入场价 ---
            # (Calculate stop loss level and potential entry price)
            atr_val = inds['atr'][0]  # 获取 ATR 值 (Get ATR value)
            # 拿到当前的 ATR 值。 (拿到现在的 ATR。)
            stop_loss_long = close - self.p.atr_multiplier * \
                atr_val  # 多头止损位 (Long stop loss level)
            # 计算做多的止损价位。 (算一下做多的止损价。)
            stop_loss_short = close + self.p.atr_multiplier * \
                atr_val  # 空头止损位 (Short stop loss level)
            # 计算做空的止损价位。 (算一下做空的止损价。)
            entry_price = close  # 假设以收盘价入场 (Assume entry at close price)
            # 假设用收盘价进场。 (假设按收盘价买入/卖出。)

            # --- 风险检查 ---
            # (Risk Check)
            can_trade = True  # 默认可以交易 (Default can trade)
            # 先假设可以交易。 (先假设能交易。)
            risk_check_details = {}  # 存储风险检查细节 (Store risk check details)
            # 准备一个盒子放风险检查的细节。 (准备一个空盒子放风险检查的细节。)

            # 1. 检查最大累积风险 (Check maximum cumulative risk)
            #    (需要先计算本次交易的潜在风险)
            #    (Need to calculate potential risk for this trade first)
            # 获取当前投资组合价值 (Get current portfolio value)
            portfolio_value = self.broker.getvalue()
            # 拿到当前的总资产。 (拿到现在的总资产。)
            # potential_risk_percent = self.p.risk_per_trade_percent # 本次交易风险百分比 (Risk percentage for this trade)
            # # 这次交易打算承担多少风险（百分比）。 (这次交易计划承担的风险比例。)
            # potential_risk_value = portfolio_value * potential_risk_percent / 100.0 # 本次交易风险金额 (Risk amount for this trade)
            # # 这次交易打算承担多少风险（金额）。 (这次交易计划承担的风险金额。)

            # # 检查是否超过最大总风险 (Check if maximum total risk is exceeded)
            # if self.cumulative_risk_units + potential_risk_value > portfolio_value * self.p.max_total_risk_percent / 100.0:
            #     # 如果当前累积风险加上这次潜在风险，超过了设定的最大总风险比例。 (如果目前总风险加上这次的，超过了我们设定的总风险上限。)
            #     can_trade = False # 不可交易 (Cannot trade)
            #     # 不能交易。 (那就不能交易。)
            #     risk_check_details['reason'] = 'MAX_TOTAL_RISK_EXCEEDED' # 原因：超过最大总风险 (Reason: Maximum total risk exceeded)
            #     # 记下原因：总风险超标。 (记下原因：总风险超了。)
            #     risk_check_details['cumulative'] = self.cumulative_risk_units # 当前累积风险 (Current cumulative risk)
            #     # 记下当前的累积风险。 (记下现在的总风险。)
            #     risk_check_details['potential'] = potential_risk_value # 本次潜在风险 (Potential risk for this trade)
            #     # 记下这次交易的潜在风险。 (记下这次的潜在风险。)
            #     risk_check_details['limit'] = portfolio_value * self.p.max_total_risk_percent / 100.0 # 总风险限额 (Total risk limit)
            #     # 记下总风险的上限。 (记下总风险的上限。)

            # 2. 检查最大持仓数量 (Check maximum number of open trades)
            if can_trade and not position_size and self.open_trades >= self.p.max_open_trades:
                # 如果前面检查通过，并且当前没有持仓，但是已开仓数量达到了最大限制。 (如果前面检查没问题，现在手里没这个数据，但总共开的单子数量已经到顶了。)
                can_trade = False  # 不可交易 (Cannot trade)
                # 不能交易。 (不能再开新单了。)
                # 原因：达到最大持仓数量 (Reason: Maximum open trades reached)
                risk_check_details['reason'] = 'MAX_OPEN_TRADES_REACHED'
                # 记下原因：开单数量到顶了。 (记下原因：开单数量满了。)
                # 当前持仓数量 (Current open trades)
                risk_check_details['open_trades'] = self.open_trades
                # 记下当前开了多少单。 (记下现在开了几单。)
                # 最大持仓限额 (Maximum open trades limit)
                risk_check_details['limit'] = self.p.max_open_trades
                # 记下最大能开几单。 (记下最多能开几单。)

            # 3. 检查最大回撤 (Check maximum drawdown) - 这个更适合在 notify_cashvalue 中处理，因为需要每个 bar 更新 HWM (More suitable in notify_cashvalue as HWM needs updating per bar)
            # current_drawdown = (self.high_water_mark - portfolio_value) / self.high_water_mark if self.high_water_mark > 0 else 0.0
            # if can_trade and current_drawdown > self.p.max_drawdown_percent / 100.0:
            #     can_trade = False
            #     risk_check_details['reason'] = 'MAX_DRAWDOWN_EXCEEDED'
            #     risk_check_details['current_drawdown'] = current_drawdown * 100
            #     risk_check_details['limit'] = self.p.max_drawdown_percent
            #     # 触发风控暂停交易 (Trigger risk control trading halt)
            #     halt_duration = datetime.timedelta(days=self.p.halt_duration_days)
            #     self.halt_trading_until = current_dt + halt_duration
            #     self.log_event('RISK_EVENT_HALT_TRIGGERED',
            #                    event_subtype='MAX_DRAWDOWN',
            #                    account_value=portfolio_value,
            #                    high_water_mark=self.high_water_mark,
            #                    drawdown_pct=current_drawdown * 100,
            #                    limit_pct=self.p.max_drawdown_percent,
            #                    halt_until=self.halt_trading_until.isoformat(),
            #                    data_feed=d)

            # --- 主要交易逻辑 ---
            # (Main Trading Logic)
            if not position_size:  # 没有持仓 (No position)
                # 如果当前没有持有这个数据。 (如果手里没这个货。)

                # --- 潜在入场信号 ---
                # (Potential Entry Signals)
                # 初始化入场信号类型 (Initialize entry signal type)
                entry_signal_type = None
                # 先假设没有入场信号。 (先假设没信号。)
                # 存储触发信号的数据 (Store data that triggered the signal)
                triggering_data = {}
                # 准备一个盒子放触发信号的具体数据。 (准备一个盒子放触发信号的数据。)

                # 多头入场信号 (Long entry signal)
                if is_bullish and cross_up_medium and close_over_bb_mid:
                    # 如果是牛市、短期线上穿中期线、且收盘价在中轨之上。 (如果是牛市，短期均线刚上穿中期，并且收盘价在中轨之上。)
                    # 信号类型 (Signal type)
                    entry_signal_type = 'EMA_Cross_BB_Confirm_Long'
                    # 信号类型：EMA金叉+BB确认做多。 (信号是：EMA金叉+BB确认做多。)
                    triggering_data = {
                        'close': close, 'ema_short': inds['ema_short'][0], 'ema_medium': inds['ema_medium'][0], 'bb_mid': inds['bbands'].lines.mid[0]}
                    # 记录触发时的价格和指标值。 (记下触发时的价格和指标值。)
                    # 使用多头止损 (Use long stop loss)
                    stop_loss_price = stop_loss_long
                    # 用做多的止损价。 (用多头止损。)
                    is_buy = True  # 标记为买入 (Mark as buy)
                    # 标记是买入操作。 (标记这是买入。)

                # elif is_bearish and cross_down_medium and close_under_bb_mid: # 空头入场信号（如果允许做空） (Short entry signal (if shorting allowed))
                #     # 如果是熊市、短期线下穿中期线、且收盘价在中轨之下。 (如果是熊市，短期均线刚下穿中期，并且收盘价在中轨之下。)
                #     # 注意：示例策略可能不包含做空逻辑 (Note: Example strategy might not include shorting logic)
                #     # entry_signal_type = 'EMA_Cross_BB_Confirm_Short'
                #     # triggering_data = {'close': close, 'ema_short': inds['ema_short'][0], 'ema_medium': inds['ema_medium'][0], 'bb_mid': inds['bbands'].lines.mid[0]}
                #     # stop_loss_price = stop_loss_short
                #     # is_buy = False
                #     pass # 暂不处理做空 (Do not handle shorting for now)
                #     # 暂时不做空。 (暂时不做空。)

                # --- 如果有入场信号并且风控检查通过 ---
                # (If there is an entry signal and risk checks passed)
                if entry_signal_type and can_trade:
                    # 如果探测到了入场信号，并且风险检查也通过了。 (如果有进场信号，而且风险检查也过了。)

                    # == 生成新的交易周期 ID ==
                    # (Generate new trade cycle ID)
                    self.current_trade_id = self._generate_trade_cycle_id()
                    # 生成一个新的交易追踪号，并存起来。 (生成一个新的交易追踪号，记下来。)

                    # 记录信号触发事件 (Log signal triggered event)
                    self.log_event('SIGNAL_TRIGGERED',
                                   data_feed=d,  # 关联数据源 (Associate data feed)
                                   # 信号类型 (Signal type)
                                   signal_type=entry_signal_type,
                                   # 触发数据 (Triggering data)
                                   triggering_data=triggering_data,
                                   # 必须包含新生成的ID (Must include the newly generated ID)
                                   trade_cycle_id=self.current_trade_id
                                   )
                    # 记录信号触发日志，带上新的追踪号。 (记录信号触发的日志，带上新的追踪号。)

                    # == 计算订单大小 ==
                    # (Calculate order size)
                    calculated_size_info = self._calculate_trade_size(
                        data_close_price=close,
                        entry_price=entry_price,
                        stop_loss_price=stop_loss_price,
                        risk_per_trade_percent=self.p.risk_per_trade_percent,
                        data=d  # 传递数据对象 (Pass the data object)
                    )
                    # 调用内部工具计算订单大小。 (调用咱们自己写的工具算一下该买多少。)
                    # 获取计算出的大小 (Get the calculated size)
                    size = calculated_size_info['size']
                    # 拿到计算结果：买多少。 (拿到算出来的数量。)
                    # 获取计算详情 (Get calculation details)
                    size_calc_details = calculated_size_info['details']
                    # 拿到计算过程的细节。 (拿到计算过程的细节。)

                    # 记录订单计算事件 (Log order calculation event)
                    self.log_event('ORDER_CALCULATION',
                                   data_feed=d,  # 关联数据源 (Associate data feed)
                                   # 关联的信号类型 (Associated signal type)
                                   signal_type=entry_signal_type,
                                   # 大致入场价 (Approximate entry price)
                                   entry_price_approx=entry_price,
                                   # 计算出的止损价 (Calculated stop loss price)
                                   stop_loss_calc=stop_loss_price,
                                   # 未计算止盈价 (Take profit price not calculated)
                                   take_profit_calc=None,
                                   # 风险计算输入 (Risk calculation inputs)
                                   risk_inputs=size_calc_details['risk_inputs'],
                                   # 原始计算大小 (Raw calculated size)
                                   size_raw=size_calc_details['raw_size'],
                                   # 最终调整后大小 (Final adjusted size)
                                   size_final=size,
                                   # 调整原因 (Adjustment reasons)
                                   adjustment_reasons=size_calc_details['adjustment_reasons'],
                                   # 必须包含交易ID (Must include trade ID)
                                   trade_cycle_id=self.current_trade_id
                                   )
                    # 记录订单计算日志，包含计算细节和交易追踪号。 (记录算单日志，包括怎么算的、结果多少、带上交易追踪号。)

                    if size > 0:
                        # 如果计算出的下单量大于0。 (如果算出来确实要买。)
                        # self.log(f'BUY CREATE, {close:.2f}, Size: {size}', dt=current_dt, data=d) # 旧日志 (Old log)
                        order_to_place = self.buy(data=d, size=size) if is_buy else self.sell(
                            data=d, size=size)  # 发出买入或卖出指令 (Issue buy or sell command)
                        # 发出买入（或卖出）指令。 (那就下单买入（或卖出）。)
                        self.order = order_to_place  # 跟踪订单 (Track the order)
                        # 把这个订单记到 self.order 里，表示有个订单发出去了。 (把这个订单记到 self.order，表示有个单子在外面跑。)

                        # == 映射订单引用和交易 ID ==
                        # (Map order reference and trade ID)
                        # 调用辅助方法进行映射 (Call helper method for mapping)
                        self._map_order_ref_to_trade_id(self.order)
                        # 把这个新订单的号和当前的交易追踪号关联起来。 (把这个订单号和当前的交易追踪号对上。)

                        # 记录订单提交事件 (Log order submitted event)
                        if self.order:
                            # 如果订单成功创建。 (如果订单创建成功了。)
                            self.log_event('ORDER_SUBMITTED',
                                           # 关联数据源 (Associate data feed)
                                           data_feed=d,
                                           # 订单引用 (Order reference)
                                           order_ref=self.order.ref,
                                           # 交易周期ID (Trade cycle ID)
                                           trade_cycle_id=self.current_trade_id,
                                           order_details={  # 订单详情 (Order details)
                                               'type': self.order.getordername(),  # 类型 (Type)
                                               # 大小 (Size)
                                               'size': self.order.created.size,
                                               # 价格 (Price)
                                               'price': self.order.created.price,
                                               # 限价 (Price limit)
                                               'pricelimit': self.order.created.pricelimit,
                                               # 有效期 (Validity)
                                               'valid': self.order.valid,
                                               'isbuy': self.order.isbuy(),  # 是否买单 (Is buy?)
                                               'issell': self.order.issell()  # 是否卖单 (Is sell?)
                                           })
                            # 记录订单提交日志，包含订单细节和交易追踪号。 (记录下单日志，包括订单细节和交易追踪号。)
                        # 如果 self.buy/sell 返回 None (比如 size 为 0 或其他内部原因) (If self.buy/sell returns None (e.g., size is 0 or other internal reasons))
                        else:
                            self.log_event('ORDER_SUBMISSION_FAILED', reason='Order object not returned by buy/sell',
                                           trade_cycle_id=self.current_trade_id, data_feed=d)
                            # 记录订单提交失败事件，因为 buy/sell 未返回订单对象。 (Log order submission failure because buy/sell didn't return an order object.)
                            # print(f"DEBUG: Resetting current_trade_id from {self.current_trade_id} due to submission failure.") # 调试
                            # 重置交易ID，因为订单未成功创建 (Reset trade ID as order wasn't successfully created)
                            self.current_trade_id = None
                            # 重置交易追踪号，因为订单未能成功创建。 (Reset trade ID as the order failed to be created.)
                    else:
                        # 如果计算出的尺寸无效 (If calculated size is not valid (<= 0))
                        # self.log_event('TRADE_SKIPPED', reason='Calculated size is zero or negative', details=size_calc_details, trade_cycle_id=self.current_trade_id, data_feed=d)
                        self.log_event('TRADE_SKIPPED',
                                       data_feed=d,
                                       # 关联数据源。 (Associate data feed.)
                                       reason='Calculated size is zero or negative',
                                       # 原因：计算出的大小为零或负数。 (Reason: Calculated size is zero or negative.)
                                       details=size_calc_details,
                                       # 计算细节。 (Calculation details.)
                                       # 关联的（失败的）交易周期ID (Associated (failed) trade cycle ID)
                                       trade_cycle_id=self.current_trade_id,
                                       # Associated (failed) trade cycle ID.
                                       signal_type=entry_signal_type)  # 触发的信号 (Triggering signal)
                        # Triggering signal type.
                        # 记录交易跳过事件，因为计算出的数量无效。 (记一笔日志，说这次交易跳过了，因为算出来的数量不对。)
                        # Log the TRADE_SKIPPED event because the calculated size was invalid.
                        # print(f"DEBUG: Resetting current_trade_id from {self.current_trade_id} due to zero size.") # 调试
                        # 重置交易ID，因为交易未启动 (Reset trade ID as trade wasn't initiated)
                        self.current_trade_id = None
                        # 把交易追踪号清掉。 (把交易追踪号清了。)

                # 有信号但风控阻止 (Signal exists but risk control prevents)
                elif entry_signal_type and not can_trade:
                    # 如果有入场信号，但是风险检查没通过。 (如果有信号，但风险检查不让交易。)
                    self.log_event('TRADE_SKIPPED',
                                   data_feed=d,  # 关联数据源 (Associate data feed)
                                   # Associate data feed.
                                   # 原因：风险控制 (Reason: Risk Control)
                                   reason='Risk Control',
                                   # Reason: Risk Control.
                                   # 风险检查细节 (Risk check details)
                                   details=risk_check_details,
                                   # Risk check details.
                                   # 触发的信号 (Triggered signal)
                                   signal_type=entry_signal_type,
                                   # Triggered signal type.
                                   # 信号数据 (Signal data)
                                   triggering_data=triggering_data
                                   # Signal triggering data.
                                   # trade_cycle_id 不适用，因为交易未启动 (trade_cycle_id not applicable as trade wasn't initiated)
                                   # trade_cycle_id is not applicable here as the trade was not initiated.
                                   )
                    # 记录交易跳过事件，因为风险控制。 (记一笔日志，说这次交易跳过了，因为风险控制不让。)
                    # Log the TRADE_SKIPPED event due to risk control.

            else:  # 持有仓位 (Holding a position)
                # 如果当前持有这个数据。 (如果手里有这个货。)

                # --- 潜在出场信号 ---
                # (Potential Exit Signals)
                # 初始化出场信号类型 (Initialize exit signal type)
                exit_signal_type = None
                # 先假设没有出场信号。 (先假设没信号。)
                # 存储触发信号的数据 (Store data that triggered the signal)
                triggering_data = {}
                # 准备一个盒子放触发信号的具体数据。 (准备一个盒子放触发信号的数据。)

                # 多头持仓，短期下穿中期 (Long position, short crosses down medium)
                if position_size > 0 and cross_down_medium:
                    # 如果是多头持仓，并且短期线下穿了中期线。 (如果是多单，并且短期均线下穿了中期均线。)
                    # 信号类型：EMA 死叉平多 (Signal type: EMA Death Cross Exit Long)
                    exit_signal_type = 'EMA_Cross_Exit_Long'
                    # 信号是：EMA死叉平多仓。 (信号是：EMA 死叉平多。)
                    triggering_data = {
                        'close': close, 'ema_short': inds['ema_short'][0], 'ema_medium': inds['ema_medium'][0]}
                    # 记录触发时的价格和指标值。 (记下触发时的价格和指标值。)
                    is_close = True  # 标记为平仓 (Mark as close)
                    # 标记是平仓操作。 (标记这是平仓。)

                # elif position_size < 0 and cross_up_medium: # 空头持仓，短期上穿中期 (Short position, short crosses up medium)
                #     # 如果是空头持仓，并且短期线上穿了中期线。 (如果是空单，并且短期均线上穿了中期均线。)
                #     exit_signal_type = 'EMA_Cross_Exit_Short'
                #     triggering_data = {'close': close, 'ema_short': inds['ema_short'][0], 'ema_medium': inds['ema_medium'][0]}
                #     is_close = True

                # --- 如果有出场信号 ---
                # (If there is an exit signal)
                if exit_signal_type:
                    # 如果探测到了出场信号。 (如果有平仓信号。)

                    # 尝试获取与当前持仓关联的 trade_cycle_id
                    # (Attempt to get the trade_cycle_id associated with the current position)
                    # 注意：简单的策略可能只有一个活跃的 trade_cycle_id
                    # (Note: Simple strategies might only have one active trade_cycle_id)
                    # 如果有多个并发交易，需要更复杂的逻辑来确定哪个交易被关闭
                    # (More complex logic is needed to determine which trade is being closed if multiple concurrent trades exist)
                    # 假设是当前活跃的交易 (Assume it's the currently active trade)
                    exit_trade_id = self.current_trade_id
                    # 先假设要平的是当前正在进行的这个交易。 (先假设要平的是当前这个。)
                    # 实际应用中，可能需要通过 self.getposition(d).tradeid 或其他方式确认
                    # (In practice, might need confirmation via self.getposition(d).tradeid or other means)

                    # 记录信号触发事件 (Log signal triggered event)
                    self.log_event('SIGNAL_TRIGGERED',
                                   data_feed=d,  # 关联数据源 (Associate data feed)
                                   # Associate data feed.
                                   # 信号类型 (Signal type)
                                   signal_type=exit_signal_type,
                                   # Signal type.
                                   # 触发数据 (Triggering data)
                                   triggering_data=triggering_data,
                                   # Triggering data.
                                   # 关联的交易ID或未知 (Associated trade ID or unknown)
                                   trade_cycle_id=exit_trade_id if exit_trade_id else 'UNKNOWN_EXIT'
                                   # Associated trade ID (or unknown).
                                   )
                    # 记录信号触发日志，带上关联的交易追踪号（如果知道的话）。 (记录信号触发日志，带上关联的交易追踪号（如果知道）。)

                    # self.log(f'CLOSE CREATE, {close:.2f}, Size: {position_size}', dt=current_dt, data=d) # 旧日志 (Old log)
                    # 发出平仓指令 (Issue close command)
                    order_to_place = self.close(data=d)
                    # 发出平仓指令。 (下单平仓。)
                    self.order = order_to_place  # 跟踪订单 (Track the order)
                    # 把这个订单记到 self.order 里。 (把这个订单记到 self.order。)

                    # == 映射订单引用和交易 ID ==
                    # (Map order reference and trade ID)
                    # 即使 exit_trade_id 不确定，也尝试映射，以便后续在 notify_trade 中查找
                    # (Even if exit_trade_id is uncertain, try mapping for later lookup in notify_trade)
                    # 使用平仓订单关联 (Associate using the closing order)
                    self._map_order_ref_to_trade_id(self.order)
                    # 把这个平仓订单的号和对应的交易追踪号关联起来。 (把这个平仓单号和对应的追踪号对上。)

                    # 记录订单提交事件 (Log order submitted event)
                    if self.order:
                        # 如果订单成功创建。 (如果订单创建成功了。)
                        self.log_event('ORDER_SUBMITTED',
                                       # 关联数据源 (Associate data feed)
                                       data_feed=d,
                                       # 订单引用 (Order reference)
                                       order_ref=self.order.ref,
                                       # 交易周期ID (Trade cycle ID)
                                       trade_cycle_id=exit_trade_id if exit_trade_id else 'UNKNOWN_EXIT',
                                       order_details={  # 订单详情 (Order details)
                                           'type': self.order.getordername(),  # 类型 (Type)
                                           # 大小 (Size)
                                           'size': self.order.created.size,
                                           # 价格 (Price)
                                           'price': self.order.created.price,
                                           # 标记为平仓单 (Mark as closing order)
                                           'isclose': True
                                       })
                        # 记录订单提交日志。 (记录下单日志。)
                    # else:
                        # self.log_event('ORDER_SUBMISSION_FAILED', reason='Close order failed', trade_cycle_id=exit_trade_id, data_feed=d)
                        # 记录平仓失败日志。 (记录平仓失败日志。)

    def stop(self):
        # 定义 stop 方法，在回测结束时调用。 (定义策略结束时要做的事情。)
        """Strategy stop method."""
        # """策略停止方法。"""
        self.log_event('STRATEGY_STOP', final_value=self.broker.getvalue(
        ), final_cash=self.broker.getcash())
        # 记录策略停止事件，包含最终资产和现金。 (记录策略停止的日志，附上最后的总资产和现金。)
        # --- 停止日志监听器 ---
        # (Stop the log listener)
        # stop_log_listener() # 在 Cerebro 运行结束后停止更合适 (More appropriate to stop after Cerebro run finishes)
        # print("Strategy stop method called.") # 用于调试 (For debugging)

    # ==================== 交易周期ID管理辅助方法 START ====================
    def _generate_trade_cycle_id(self):
        # 定义一个私有方法，用于生成新的交易周期ID。 (定义一个内部工具，用来生成新的交易追踪号。)
        """Generates a new unique trade cycle ID."""
        # """生成一个新的唯一交易周期ID。"""
        return uuid.uuid4().hex
        # 返回一个基于 UUID4 的十六进制字符串作为唯一ID。 (生成并返回一个独一无二的字符串ID。)
        # Return a hexadecimal string based on UUID4 as the unique ID.

    def _map_order_ref_to_trade_id(self, order):
        # 定义一个私有方法，将订单引用映射到当前的交易周期ID。 (定义一个内部工具，把订单号和当前的交易追踪号关联起来。)
        """Maps the order reference to the current trade cycle ID."""
        # """将订单引用映射到当前交易周期ID。"""
        if order and order.ref is not None and self.current_trade_id:
            # 如果订单对象有效，订单引用不为空，且当前交易周期ID存在。 (如果订单有效、订单号存在、并且当前有交易追踪号。)
            self.order_ref_to_trade_id_map[order.ref] = self.current_trade_id
            # 在映射字典中创建或更新条目。 (在对应表里记下：这个订单号 -> 这个交易追踪号。)
            # Create or update the entry in the mapping dictionary.
            # print(f"DEBUG: Mapped order_ref {order.ref} to trade_id {self.current_trade_id}") # 调试
            # self.log_event('ORDER_REF_MAPPED', order_ref=order.ref, trade_cycle_id=self.current_trade_id, data_feed=order.data) # 可选日志 (Optional log)
            # Optional: Log the mapping event.

    # ==================== 交易周期ID管理辅助方法 END ======================


# ===================================================================================
# 数据加载函数 (Data Loading Function)
# ===================================================================================
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
                    f"错误: 在 {file_path} 中找不到映射后的 'datetime' 列。请确保Excel文件中有'日期'列，或正确修改脚本中的column_mapping。")
                # 打印错误信息，提示找不到'datetime'列。 (Print an error message indicating the 'datetime' column is missing.)
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

            processed_results.append({
                'instance': strategy_instance,
                'params': params,
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
# 结果打印辅助函数 (Result Printing Helper Functions)
# ===================================================================================

def print_optimization_summary(best_result, all_scored_results, ema_medium_range, ema_long_range, bbands_period_range, bbands_dev_range, total_time, actual_combinations, avg_time):
    # 打印优化结果的汇总信息，恢复原有格式，并增加序号列。
    # Print summary information for optimization results, restoring original format and adding a serial number column.
    if best_result:
        # 如果找到了最佳结果。 (If a best result was found.)

        # 先打印排序后的所有结果表格
        # First, print the table of all sorted results
        print('\n{:=^105}'.format(' 参数优化结果 (按得分排序) '))  # 增加宽度以容纳序号列
        # 打印排序后结果标题。 (Print the sorted results title.)
        print('{:<6} {:<12} {:<12} {:<12} {:<10} {:<12} {:<12} {:<12} {:<12}'.format(
            '序号', 'EMA中期', 'EMA长期', '布林周期', '布林标差', '夏普比率', '收益率(%)', '最大回撤(%)', '得分'
        ))
        # 打印结果表头。 (Print the results table header.)
        print('-' * 105)  # 增加宽度
        # 打印分割线。 (Print a separator line.)

        # 按得分降序排序
        # Sort by score descending
        all_scored_results.sort(key=lambda x: x['score'], reverse=True)
        # 按得分对所有结果进行降序排序。 (Sort all results by score in descending order.)

        for i, res_data in enumerate(all_scored_results, 1):
            # 遍历排序后的结果，从1开始编号。 (Iterate through the sorted results, starting enumeration from 1.)
            p = res_data['params']
            # 获取参数。 (Get the parameters.)
            print('{:<6} {:<12} {:<12} {:<12} {:<10.1f} {:<12.4f} {:<12.2f} {:<12.2f} {:<12.4f}'.format(
                i,  # 添加序号
                p.ema_medium_period, p.ema_long_period, p.bbands_period, p.bbands_devfactor,
                res_data['sharpe'], res_data['return'] * 100,  # 乘以100得到百分比
                res_data['drawdown'] * 100,  # 乘以100得到百分比
                res_data['score']
            ))
            # 打印格式化的结果行。 (Print the formatted result row.)

        # 再打印最优参数组合
        # Then, print the best parameter combination
        print('\n{:=^50}'.format(' 最优参数组合 '))
        # 打印最优参数组合标题。 (Print the best parameter combination title.)
        best_params = best_result['params']
        # 获取最佳参数。 (Get the best parameters.)
        print('{:<20}: {}'.format('EMA中期', best_params.ema_medium_period))
        # 打印最佳中期EMA。 (Print the best medium EMA.)
        print('{:<20}: {}'.format('EMA长期', best_params.ema_long_period))
        # 打印最佳长期EMA。 (Print the best long EMA.)
        print('{:<20}: {}'.format('布林带周期', best_params.bbands_period))
        # 打印最佳布林带周期。 (Print the best Bollinger Bands period.)
        print('{:<20}: {:.1f}'.format('布林带标准差', best_params.bbands_devfactor))
        # 打印最佳布林带标准差。 (Print the best Bollinger Bands deviation factor.)
        print('{:<20}: {:.4f}'.format('夏普比率', best_result['sharpe']))
        # 打印最佳夏普比率。 (Print the best Sharpe Ratio.)
        print('{:<20}: {:.2f}%'.format('总收益率', best_result['return'] * 100))
        # 打印最佳总收益率。 (Print the best total return.)
        print('{:<20}: {:.2f}%'.format('最大回撤', best_result['drawdown'] * 100))
        # 打印最佳最大回撤。 (Print the best max drawdown.)
        print('{:<20}: {:.4f}'.format('得分', best_result['score']))
        # 打印最佳得分。 (Print the best score.)
        print('=' * 50)
        # 打印分割线。 (Print a separator line.)

    else:
        # 如果没有找到最佳结果。 (If no best result was found.)
        print("\n错误：未能从优化结果中找到最佳参数组合。")
        # 打印错误信息。 (Print an error message.)

    # 先打印"参数优化设置"
    # First, print "Optimization Settings"
    print("\n{:-^50}".format(' 参数优化设置 '))
    # 打印参数优化设置的标题。 (Print the parameter optimization settings title.)
    print('{:<20}: {}'.format("优化开关", '开启'))  # 因为此函数只在优化时调用
    # 打印优化开关状态。 (Print the optimization switch status.)
    print('{:<20}: {}'.format("Observer 图表", '关闭'))  # 因为优化时 stdstats 为 False
    # 打印Observer图表状态。 (Print the Observer chart status.)
    print("优化参数范围:")
    # 打印优化参数范围标题。 (Print the optimization parameter ranges title.)
    print(f"  ema_medium_period: {list(ema_medium_range)}")
    # 打印中期EMA优化范围。 (Print the medium EMA optimization range.)
    print(f"  ema_long_period: {list(ema_long_range)}")
    # 打印长期EMA优化范围。 (Print the long EMA optimization range.)
    print(f"  bbands_period: {list(bbands_period_range)}")
    # 打印布林带周期优化范围。 (Print the Bollinger Bands period optimization range.)
    print(f"  bbands_devfactor: {list(bbands_dev_range)}")
    # 打印布林带标准差优化范围。 (Print the Bollinger Bands deviation factor optimization range.)
    print('-' * 50)
    # 打印分割线。 (Print a separator line.)

    # 再打印"优化完成统计"
    # Then, print "Optimization Completion Statistics"
    print('\n{:=^50}'.format(' 优化完成统计 '))
    # 打印优化完成统计标题。 (Print the optimization completion statistics title.)
    print('{:<20}: {:.2f}秒 ({:.2f}分钟)'.format(
        '总用时', total_time, total_time/60))
    # 打印总耗时。 (Print the total time taken.)
    print('{:<20}: {}'.format('实际参数组数', actual_combinations))
    # 打印实际组合数。 (Print the actual number of combinations run.)
    print('{:<20}: {:.2f}秒'.format('每组平均用时', avg_time))
    # 打印平均耗时。 (Print the average time per combination.)
    print('=' * 50)
    # 打印分割线。 (Print a separator line.)


def print_backtest_summary(initial_cash, final_value, strat):
    # 打印单次回测结果的汇总信息，格式与优化结果对齐。
    # Print summary information for single backtest results, aligning format with optimization results.
    print('\n{:=^50}'.format(' 单次回测结果分析 '))
    # 打印回测结果分析的标题。 (Print the title for backtest result analysis.)
    print('{:<30}: {:>18.2f}'.format(
        '初始组合价值 (Initial Value)', initial_cash))
    # 打印初始投资组合价值。 (Print the initial portfolio value.)
    print('{:<30}: {:>18.2f}'.format(
        '最终组合价值 (Final Value)', final_value))
    # 打印最终投资组合价值。 (Print the final portfolio value.)
    pnl = final_value - initial_cash
    # 计算净利润/亏损。 (Calculate the net profit/loss.)
    print('{:<30}: {:>18.2f}'.format('净利润/亏损 (Net P/L)', pnl))
    # 打印净利润/亏损。 (Print the net profit/loss.)
    print('-' * 50)
    # 打印分割线。

    # 打印分析器结果
    # Print analyzer results
    print('{:<30}: {}'.format('分析器', '结果'))
    # 打印分析器结果的标题。 (Print the title for analyzer results.)
    print('-' * 50)
    # 打印分割线。

    # ... (analysis extraction remains the same)
    sharpe_analysis = strat.analyzers.sharpe_ratio.get_analysis() if hasattr(
        strat.analyzers, 'sharpe_ratio') else None  # 使用正确的名字 'sharpe_ratio'
    returns_analysis = strat.analyzers.returns.get_analysis() if hasattr(
        strat.analyzers, 'returns') else None
    drawdown_analysis = strat.analyzers.drawdown.get_analysis() if hasattr(
        strat.analyzers, 'drawdown') else None
    trade_analysis = strat.analyzers.trade_analyzer.get_analysis() if hasattr(
        strat.analyzers, 'trade_analyzer') else None  # 使用正确的名字 'trade_analyzer'
    # SQN 分析器未添加，保留获取逻辑（会得到None）
    sqn_analysis = strat.analyzers.sqn.get_analysis() if hasattr(
        strat.analyzers, 'sqn') else None

    # Sharpe Ratio
    if sharpe_analysis and 'sharperatio' in sharpe_analysis:
        print('{:<30}: {:>18.3f}'.format(
            '年化夏普比率 (Annual Sharpe)', sharpe_analysis["sharperatio"]))
    else:
        print('{:<30}: {:>18}'.format(
            '年化夏普比率 (Annual Sharpe)', 'N/A'))

    # Returns
    if returns_analysis:
        if 'rtot' in returns_analysis:
            print('{:<30}: {:>17.2f}%'.format(
                '总收益率 (Total Return)', returns_analysis["rtot"]*100))
        else:
            print('{:<30}: {:>18}'.format('总收益率 (Total Return)', 'N/A'))

        annualized_return = returns_analysis.get("rnorm100", None)
        if annualized_return is not None:
            print('{:<30}: {:>17.2f}%'.format(
                '年化收益率 (Annual Return)', annualized_return))
        elif 'ravg' in returns_analysis:
            annualized_return_est = (
                (1 + returns_analysis['ravg']) ** 252 - 1) * 100
            print('{:<30}: {:>17.2f}% (est.)'.format(
                '年化收益率 (Annual Return)', annualized_return_est))
        else:
            print('{:<30}: {:>18}'.format('年化收益率 (Annual Return)', 'N/A'))
    else:
        print('{:<30}: {:>18}'.format('总收益率 (Total Return)', 'N/A'))
        print('{:<30}: {:>18}'.format('年化收益率 (Annual Return)', 'N/A'))

    # Drawdown
    if drawdown_analysis and 'max' in drawdown_analysis and 'drawdown' in drawdown_analysis.max:
        print('{:<30}: {:>17.2f}%'.format(
            '最大回撤 (Max Drawdown %)', drawdown_analysis.max.drawdown))
        print('{:<30}: {:>18.2f}'.format(
            '最大回撤金额 (Max DD Money)', drawdown_analysis.max.moneydown))
    else:
        print('{:<30}: {:>18}'.format('最大回撤 (Max Drawdown %)', 'N/A'))
        print('{:<30}: {:>18}'.format('最大回撤金额 (Max DD Money)', 'N/A'))

    # Trade Analysis
    if trade_analysis and 'total' in trade_analysis and 'total' in trade_analysis.total:
        total_trades = trade_analysis.total.total
        print('{:<30}: {:>18}'.format('总交易次数 (Total Trades)', total_trades))
        if total_trades > 0:
            win_rate = (trade_analysis.won.total / total_trades) * 100
            print('{:<30}: {:>17.2f}%'.format('胜率 (Winning Rate)', win_rate))

            avg_win = trade_analysis.won.pnl.average if trade_analysis.won.total > 0 else 0
            print('{:<30}: {:>18.2f}'.format('平均盈利 (Average Win)', avg_win))

            avg_loss = trade_analysis.lost.pnl.average if trade_analysis.lost.total > 0 else 0
            print('{:<30}: {:>18.2f}'.format('平均亏损 (Average Loss)', avg_loss))

            profit_factor = abs(trade_analysis.won.pnl.total /
                                trade_analysis.lost.pnl.total) if trade_analysis.lost.pnl.total != 0 else float('inf')
            print('{:<30}: {:>18.2f}'.format(
                '盈利因子 (Profit Factor)', profit_factor))
        else:
            print('{:<30}: {:>18}'.format('胜率 (Winning Rate)', 'N/A'))
            print('{:<30}: {:>18}'.format('平均盈利 (Average Win)', 'N/A'))
            print('{:<30}: {:>18}'.format('平均亏损 (Average Loss)', 'N/A'))
            print('{:<30}: {:>18}'.format('盈利因子 (Profit Factor)', 'N/A'))
    else:
        print('{:<30}: {:>18}'.format('总交易次数 (Total Trades)', 'N/A'))
        print('{:<30}: {:>18}'.format('胜率 (Winning Rate)', 'N/A'))
        print('{:<30}: {:>18}'.format('平均盈利 (Average Win)', 'N/A'))
        print('{:<30}: {:>18}'.format('平均亏损 (Average Loss)', 'N/A'))
        print('{:<30}: {:>18}'.format('盈利因子 (Profit Factor)', 'N/A'))

    # SQN
    if sqn_analysis and 'sqn' in sqn_analysis:
        print('{:<30}: {:>18.2f}'.format('系统质量数 (SQN)', sqn_analysis.sqn))
    else:
        print('{:<30}: {:>18}'.format('系统质量数 (SQN)', 'N/A'))

    print('=' * 50)
    # 打印结束分割线

# ===================================================================================
# 辅助函数定义 (Helper Function Definitions)
# ===================================================================================


def get_backtest_config():
    """
    集中管理和返回回测配置。
    (Manages and returns the backtest configuration.)
    """
    config = {
        'optimize': True,  # 设置为True进行参数优化，False进行单次回测
        'initial_cash': 500000.0,
        'commission_rate': 0.0003,
        'data_files': [
            r'D:\BT2025\datas\510050_d.xlsx',
            r'D:\BT2025\datas\510300_d.xlsx',
            # r'D:\BT2025\datas\159949_d.xlsx'
        ],
        'column_mapping': {
            'date': 'datetime', 'open': 'open', 'high': 'high', 'low': 'low',
            'close': 'close', 'volume': 'volume'
        },
        'openinterest_col': -1,
        'fromdate': datetime.datetime(2015, 1, 1),
        'todate': datetime.datetime(2024, 4, 30),
        # --- 优化参数范围 (Optimization Parameter Ranges) ---
        'optimization_ranges': {
            'ema_medium_period': range(40, 81, 10),
            'ema_long_period': range(100, 141, 10),
            'bbands_period': range(15, 26, 5),
            'bbands_devfactor': [1.8, 2.0, 2.2]
        },
        # --- 单次回测固定参数 (Fixed Parameters for Single Backtest) ---
        'single_run_params': {
            'ema_medium_period': 60,
            'ema_long_period': 120,
            'bbands_period': 20,
            'bbands_devfactor': 2.0,
            'risk_per_trade_percent': 0.01,
            'allow_short': False
        },
        # --- 其他配置 ---
        'risk_free_rate': 0.0  # 无风险利率，用于计算夏普比率等指标。
    }
    return config


def setup_cerebro_and_broker(config):
    """
    创建并配置Cerebro引擎和Broker。
    (Creates and configures the Cerebro engine and Broker.)
    """
    cerebro = bt.Cerebro(optreturn=True,
                         stdstats=not config['optimize'])
    cerebro.broker.setcash(config['initial_cash'])
    cerebro.broker.setcommission(commission=config['commission_rate'])
    return cerebro


def add_strategy_components(cerebro, config):
    """
    向Cerebro实例添加策略、分析器和观察器。
    (Adds strategy, analyzers, and observers to the Cerebro instance.)
    """
    if config['optimize']:
        print("--- 开始参数优化 ---")
        opt_ranges = config['optimization_ranges']
        cerebro.optstrategy(
            AShareETFStrategy,
            ema_medium_period=opt_ranges['ema_medium_period'],
            ema_long_period=opt_ranges['ema_long_period'],
            bbands_period=opt_ranges['bbands_period'],
            bbands_devfactor=opt_ranges['bbands_devfactor']
        )
        # 添加优化所需的分析器
        cerebro.addanalyzer(bt.analyzers.SharpeRatio,
                            _name='sharpe_ratio', riskfreerate=config['risk_free_rate'])
        cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    else:
        print("--- 开始单次回测 ---")
        # 添加单次回测策略
        cerebro.addstrategy(AShareETFStrategy, **config['single_run_params'])
        # 添加单次回测分析器
        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe_ratio',
                            timeframe=bt.TimeFrame.Days, riskfreerate=config['risk_free_rate'])
        cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trade_analyzer')
        cerebro.addanalyzer(bt.analyzers.PyFolio, _name='pyfolio')
        cerebro.addanalyzer(bt.analyzers.SQN, _name='sqn')  # 添加 SQN 分析器
        # 添加观察器 (仅在非优化模式下)
        cerebro.addobserver(bt.observers.Broker)
        cerebro.addobserver(bt.observers.Trades)
        cerebro.addobserver(bt.observers.BuySell)
        cerebro.addobserver(bt.observers.DrawDown)


def process_and_report_results(results, cerebro, config, start_time=None):
    """
    处理回测或优化结果并进行报告。
    (Processes backtest or optimization results and reports them.)
    Args:
        start_time (float, optional): 优化开始时间，用于计算总耗时。Defaults to None.
    """
    if config['optimize']:
        end_time = time.time()  # 需要在 run_backtest 中记录 start_time
        # print("--- 参数优化完成 --- ") # 这句可以移到 run_backtest 的结尾
        # --- 计算统计信息 ---
        total_time = end_time - start_time if start_time is not None else 0  # 计算总耗时
        actual_combinations = len(results) if results else 0
        avg_time = total_time / \
            actual_combinations if actual_combinations and total_time > 0 else 0  # 计算平均耗时
        print(f"优化总耗时: {total_time:.2f} 秒")
        print(f"实际组合数: {actual_combinations}")
        print(f"平均组合耗时: {avg_time:.4f} 秒")

        print("\n--- 开始分析优化结果 ---")
        best_result, all_scored_results = analyze_optimization_results(results)
        # 传递计算好的统计信息
        print_optimization_summary(best_result, all_scored_results,
                                   config['optimization_ranges']['ema_medium_period'],
                                   config['optimization_ranges']['ema_long_period'],
                                   config['optimization_ranges']['bbands_period'],
                                   config['optimization_ranges']['bbands_devfactor'],
                                   total_time, actual_combinations, avg_time)
        print("\n--- 优化结果分析完成 ---")
    else:
        if not results:
            print("\n错误：单次回测未能生成结果。请检查策略或数据。")
            return
        strat = results[0]
        final_value = cerebro.broker.getvalue()
        print_backtest_summary(config['initial_cash'], final_value, strat)

        # --- 绘图 (Plotting) ---
        print("\n--- 开始生成图表 ---")
        try:
            figs = cerebro.plot(style='candlestick', barup='red', bardown='green',
                                numfigs=1, volume=True, iplot=False)
            # 如果需要保存图片：
            # fig = figs[0][0]
            # fig.savefig('backtest_results.png')
            # print("图表已保存为 backtest_results.png")
            print("--- 图表生成完成 --- (可能需要手动在窗口中查看或已保存)")
        except Exception as e:
            print(f"\n错误：生成图表时出错: {e}")

# ===================================================================================
# 主回测运行函数 (Main Backtest Runner Function)
# ===================================================================================


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
