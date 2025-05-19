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
        # 将最终的日志字典转换为 JSON 字符串，按键排序且不强制 ASCII 编码。 (Convert the final log dictionary to a JSON string, with sorted keys and without ensuring ASCII.)

# ================= 自定义 JSON Formatter END ===================

# ================== 日志队列处理线程 START ==================
# (这个部分是异步写入日志的核心，确保日志写入不阻塞策略运行)
log_queue = queue.Queue(-1)  # 使用无限大小的队列 (创建一个队列，用来临时存放日志)
# 创建一个无限大小的队列用于存储待处理的日志记录。 (Create an infinitely sized queue to store pending log records.)
log_listener = None # 初始化日志监听器变量 (准备一个监听器，后面会用到)
# 初始化全局变量 log_listener 为 None。 (Initialize the global variable log_listener to None.)

def setup_log_listener(handler):
    # 定义一个函数来设置和启动日志监听器。 (定义一个启动监听器的函数。)
    """Sets up and starts the log listener thread."""
    # """设置并启动日志监听器线程。"""
    global log_listener
    # 声明 log_listener 是全局变量。 (告诉程序我们要用全局的那个监听器。)
    log_listener = logging.handlers.QueueListener(log_queue, handler, respect_handler_level=True)
    # 创建 QueueListener 实例，连接队列和处理器。 (创建监听器，让它看着队列，并告诉它日志要交给哪个处理器处理。)
    # 创建 QueueListener 实例，它会监听 log_queue 并将记录传递给指定的 handler。 (Create a QueueListener instance that listens to log_queue and passes records to the specified handler.)
    log_listener.start()
    # 启动监听器线程。 (让监听器开始工作。)
    # 启动监听器线程，开始处理队列中的日志记录。 (Start the listener thread to begin processing log records from the queue.)

def stop_log_listener():
    # 定义一个函数来停止日志监听器。 (定义一个停止监听器的函数。)
    """Stops the log listener thread."""
    # """停止日志监听器线程。"""
    global log_listener
    # 声明 log_listener 是全局变量。 (告诉程序我们要用全局的那个监听器。)
    if log_listener:
        # 如果监听器存在。 (如果监听器在工作。)
        # print("Attempting to stop log listener...") # 调试信息 (Debug message)
        log_listener.stop()
        # 停止监听器线程。 (让监听器停止工作。)
        # print("Log listener stopped.") # 调试信息 (Debug message)
        log_listener = None # 重置变量 (Reset variable)
        # 将 log_listener 重置为 None。 (Reset log_listener to None.)
# ================== 日志队列处理线程 END ==================


class AShareETFStrategy(bt.Strategy):
    # 定义一个名为AShareETFStrategy的类，它继承自bt.Strategy，表示这是一个Backtrader交易策略类。 (创建一个叫做AShareETFStrategy的策略类，它继承了bt.Strategy，说明这是个交易策略。)
    params = (
        ('ema_short_period', 10),  # 短期EMA周期 (Short-term EMA period)
        # 定义短期指数移动平均线的周期参数，默认值为10。 (Define the period parameter for the short-term Exponential Moving Average, default value is 10.)
        ('ema_medium_period', 30), # 中期EMA周期 (Medium-term EMA period)
        # 定义中期指数移动平均线的周期参数，默认值为30。 (Define the period parameter for the medium-term Exponential Moving Average, default value is 30.)
        ('ema_long_period', 60),  # 长期EMA周期 (Long-term EMA period)
        # 定义长期指数移动平均线的周期参数，默认值为60。 (Define the period parameter for the long-term Exponential Moving Average, default value is 60.)
        ('bbands_period', 20),    # 布林带周期 (Bollinger Bands period)
        # 定义布林带计算周期参数，默认值为20。 (Define the period parameter for Bollinger Bands calculation, default value is 20.)
        ('bbands_devfactor', 2.0),# 布林带标准差因子 (Bollinger Bands standard deviation factor)
        # 定义布林带通道宽度（标准差倍数）参数，默认值为2.0。 (Define the parameter for Bollinger Bands channel width (standard deviation multiplier), default value is 2.0.)
        ('atr_period', 14),       # ATR周期 (ATR period)
        # 定义平均真实波幅（ATR）计算周期参数，默认值为14。 (Define the period parameter for Average True Range (ATR) calculation, default value is 14.)
        ('atr_multiplier', 3.0),  # ATR止损乘数 (ATR stop loss multiplier)
        # 定义ATR止损计算中使用的乘数因子，默认值为3.0。 (Define the multiplier factor used in ATR stop loss calculation, default value is 3.0.)
        ('risk_per_trade_percent', 1.0), # 单笔交易风险百分比 (Risk percentage per trade)
        # 定义单笔交易允许承担的最大风险占总资产的百分比，默认值为1.0%。 (Define the maximum risk percentage of total assets allowed per single trade, default value is 1.0%.)
        ('max_total_risk_percent', 10.0),# 最大总风险百分比 (Maximum total risk percentage)
        # 定义整个策略允许承担的最大累积风险占总资产的百分比，默认值为10.0%。 (Define the maximum cumulative risk percentage of total assets allowed for the entire strategy, default value is 10.0%.)
        ('max_open_trades', 5),       # 最大同时持仓数量 (Maximum number of simultaneous open trades)
        # 定义策略允许同时持有的最大未平仓交易数量，默认值为5。 (Define the maximum number of open trades the strategy is allowed to hold simultaneously, default value is 5.)
        ('max_drawdown_percent', 20.0), # 最大可接受回撤百分比 (Maximum acceptable drawdown percentage)
        # 定义策略可接受的最大资金回撤百分比，默认值为20.0%。 (Define the maximum acceptable portfolio drawdown percentage for the strategy, default value is 20.0%.)
        ('halt_duration_days', 5) ,   # 触发风控后的暂停交易天数 (Trading halt duration in days after risk trigger)
        # 定义触发风险控制（如最大回撤）后暂停交易的天数，默认值为5天。 (Define the number of days trading is halted after a risk control trigger (e.g., max drawdown), default value is 5 days.)
        # ================= 日志系统参数 START =================
        ('log_path', 'logs'), # 日志文件存放目录 (日志文件放哪里)
        # 定义日志文件的存储目录，默认为 'logs'。 (Define the directory where log files will be stored, default is 'logs'.)
        ('log_filename_pattern', '{strategy_name}_{data_name}_{timestamp:%Y%m%d_%H%M%S}.log.jsonl'), # 日志文件名格式模板 (日志文件叫什么名字的规则)
        # 定义日志文件名的格式模板，包含策略名、数据名和时间戳。 (Define the format template for log filenames, including strategy name, data name, and timestamp.)
        ('log_level', logging.INFO), # 日志记录级别 (记录多详细的信息，INFO级别比较常用)
        # 定义日志记录的最低级别，默认为 INFO。 (Define the minimum logging level, default is INFO.)
        # ================= 日志系统参数 END ===================
    )
    # 定义策略的参数，包括EMA周期、布林带设置、ATR设置、风险管理参数等。 (Define the strategy parameters, including EMA periods, Bollinger Bands settings, ATR settings, risk management parameters, etc.)


    # ==================== 日志系统核心方法 START ====================
    def _setup_logger(self):
        # 定义一个私有方法 _setup_logger，用于配置和初始化日志记录器。 (定义一个内部工具，用来设置好日志系统。)
        """Sets up the logging system for the strategy."""
        # """为策略设置日志系统。"""
        self.strategy_id = f"{self.__class__.__name__}_{uuid.uuid4().hex[:8]}"
        # 为当前策略实例生成一个唯一的标识符。 (给这个策略起个独一无二的名字，加一串随机码防重复。)
        # Generate a unique identifier for the current strategy instance.
        self.logger = logging.getLogger(self.strategy_id)
        # 获取一个特定于此策略实例的日志记录器。 (拿到这个策略专属的记事本。)
        # Get a logger instance specific to this strategy instance.
        self.logger.setLevel(self.p.log_level)
        # 设置日志记录器的级别。 (设定这个记事本记录信息的详细程度。)
        # Set the logging level for the logger.

        # 防止重复添加处理器，特别是在优化运行时。 (避免重复设置记事本的写入方式。)
        # Prevent adding handlers multiple times, especially during optimization runs.
        if self.logger.hasHandlers():
            # 如果记录器已经有关联的处理器。
            # In optimization, __init__ might be called multiple times for the same logger name.
            # 清理旧的处理器，以防万一。
            # (在优化模式下，同一个策略名可能会初始化多次，先把旧的设置清理掉。)
            # for h in self.logger.handlers[:]:
            #     self.logger.removeHandler(h)
            # 通常不需要清理，因为 getLogger 会返回同一个实例。主要问题是重复添加。
            # (通常不需要清理，因为getLogger会返回同一个记事本实例，主要是避免重复添加写入方式。)
            # 如果已经有 QueueHandler，则假设已经设置好了
            # (If a QueueHandler already exists, assume setup is done)
            if any(isinstance(h, logging.handlers.QueueHandler) for h in self.logger.handlers):
                 # 检查是否已有队列处理器。 (检查是否已经设置了异步写入方式。)
                 # Check if a QueueHandler already exists.
                 # print(f"Logger {self.strategy_id} already has QueueHandler. Skipping setup.") # 用于调试 (打印调试信息)
                 # Print debug message.
                 return # 如果有，则跳过后续设置。 (如果已经有了，就不用再设了。)
                 # If yes, skip the rest of the setup.


        # --- 文件处理器和格式化器 ---
        # --- File Handler and Formatter ---
        log_dir = self.p.log_path
        # 获取日志目录路径。 (拿到日志文件夹的名字。)
        # Get the log directory path from parameters.
        os.makedirs(log_dir, exist_ok=True)
        # 创建日志目录，如果目录已存在则忽略。 (确保这个文件夹存在，没有就创建一个。)
        # Create the log directory if it doesn't exist.

        # 构建日志文件名 (Construct the log filename)
        now_str = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        # 获取当前时间字符串。 (拿到现在的时间，格式化成年月日_时分秒。)
        # Get the current time string.
        data_name_part = "multi_data" if len(self.datas) > 1 else self.datas[0]._name if self.datas else "no_data"
        # 根据数据源数量确定文件名中的数据部分。 (看看有几个数据源，如果多于一个就叫 multi_data，只有一个就用它的名字，没有就叫 no_data。)
        # Determine the data name part based on the number of data feeds.
        log_filename = self.p.log_filename_pattern.format(
            strategy_name=self.__class__.__name__,
            # 格式化文件名模板中的策略名称部分。 (Format the strategy name part of the filename template.)
            data_name=data_name_part,
            # 格式化文件名模板中的数据名称部分。 (Format the data name part of the filename template.)
            timestamp=datetime.datetime.now() # 使用当前时间对象进行格式化 (用当前时间格式化文件名模板。)
            # 格式化文件名模板中的时间戳部分。 (Format the timestamp part of the filename template using the current datetime object.)
            # pid=os.getpid() # 可选：添加进程ID (Optional: Add process ID)
            # Optional: Add process ID to the filename.
        )
        # 格式化日志文件名模板。 (按照规则拼出完整的日志文件名。)
        # Format the log filename using the template and parameters.
        log_filepath = os.path.join(log_dir, log_filename)
        # 拼接日志目录和文件名得到完整路径。 (把文件夹名和文件名组合成完整路径。)
        # Join the directory and filename to get the full log file path.

        # --- 异步日志处理设置 ---
        # (Async logging setup)
        json_formatter = JsonFormatter()
        # 创建自定义的 JSON 格式化器实例。 (创建我们前面定义的 JSON 格式化工具。)
        # Create an instance of the custom JSON formatter.

        # 文件处理器 - 这是最终写入文件的处理器
        # (File handler - this is the handler that writes to the file)
        file_handler = logging.FileHandler(log_filepath, encoding='utf-8')
        # 创建一个文件处理器，指定文件路径和编码。 (创建一个写入文件的工具，告诉它写到哪个文件，用什么编码。)
        # Create a file handler, specifying the file path and encoding.
        file_handler.setFormatter(json_formatter)
        # 为文件处理器设置 JSON 格式化器。 (告诉这个写入工具，要用 JSON 格式写。)
        # Set the JSON formatter for the file handler.

        # 队列处理器 - 将日志发送到队列
        # (Queue handler - sends logs to the queue)
        queue_handler = logging.handlers.QueueHandler(log_queue)
        # 创建一个队列处理器，将日志记录放入全局队列 log_queue。 (创建一个队列处理器，它负责把日志先扔到队列里。)
        # Create a queue handler that puts log records into the global log_queue.

        # 将队列处理器添加到策略的 logger
        # (Add the queue handler to the strategy's logger)
        self.logger.addHandler(queue_handler)
        # 将队列处理器添加到策略的日志记录器中。 (把这个"扔队列"的工具装到策略的记事本上。)
        # Add the queue handler to the strategy's logger.

        # 设置并启动监听器（如果尚未启动）
        # (Setup and start the listener (if not already started))
        global log_listener
        # 声明 log_listener 是全局变量。 (告诉程序我们要用全局的那个监听器。)
        # Declare log_listener as a global variable.
        if log_listener is None or not log_listener.is_alive(): # 检查监听器是否已启动 (Check if listener is already running)
            # Check if the listener exists and is running.
            # print(f"Setting up log listener for handler: {file_handler}") # 用于调试 (打印调试信息)
            # Print debug message.
            setup_log_listener(file_handler) # 启动监听器，将文件处理器传给它 (Start the listener, passing the file handler to it)
            # Start the listener, passing the file handler to it.
            # print(f"Log listener started.") # 用于调试 (打印调试信息)
            # Print debug message.
        # else:
            # print(f"Log listener already running.") # 用于调试 (打印调试信息)
            # Print debug message.

        # 记录日志系统初始化完成
        # (Log that the logging system initialization is complete)
        self.log_event('LOGGER_INITIALIZED', details={'log_filepath': log_filepath})
        # 调用 log_event 记录一条初始化完成的日志。 (写一条日志，说日志系统已经准备好了。)
        # Log an event indicating that the logger is initialized, including the log file path.


    def log_event(self, event_type, data_feed=None, **kwargs):
        # 定义 log_event 方法，用于记录结构化的日志事件。 (定义一个专门用来记录各种事件的工具。)
        """Logs a structured event."""
        # """记录一个结构化事件。"""
        try:
            # 尝试执行日志记录逻辑。 (试试看能不能记日志。)
            # Try executing the logging logic.
            log_entry = {
                # 'timestamp': datetime.datetime.now(pytz.utc).isoformat() + 'Z', # 使用 UTC 时间 (Use UTC time)
                # Get the current UTC time in ISO format.
                 'timestamp': self.datas[0].datetime.datetime(0).isoformat() if self.datas and len(self.datas[0]) else datetime.datetime.now(pytz.utc).isoformat() + 'Z', # 优先使用回测时间 (Prefer backtest time)
                 # 优先使用第一个数据源的当前回测时间，如果不可用则使用当前UTC时间。 (Prefer the current backtest time from the first data feed; use current UTC time if unavailable.)
                'event_type': event_type, # 事件类型 (Event type)
                # Set the event type.
                'strategy_id': getattr(self, 'strategy_id', 'unknown'), # 策略实例 ID (Strategy instance ID)
                # Get the strategy ID, default to 'unknown' if not set.
                'data_id': data_feed._name if data_feed else getattr(self.data, '_name', 'default_data'), # 数据源名称 (Data feed name)
                # Get the data feed name, using the provided feed or the default one.
            }
            # 创建基础日志条目字典，包含标准字段。 (创建一个日志的基本信息盒子，放上时间、事件类型、策略ID、数据ID。)
            # Create the base log entry dictionary with standard fields.

            # 尝试添加交易周期ID (Try to add trade cycle ID)
            # Try to add the trade cycle ID.
            if hasattr(self, 'current_trade_id') and self.current_trade_id:
                # 如果当前策略实例有 'current_trade_id' 属性且不为空。 (如果现在有一个正在进行的交易追踪号。)
                # If the strategy instance has a non-empty 'current_trade_id' attribute.
                log_entry['trade_cycle_id'] = self.current_trade_id
                # 将其添加到日志条目中。 (把这个追踪号也放进盒子。)
                # Add it to the log entry.
            elif 'order_ref' in kwargs and hasattr(self, 'order_ref_to_trade_id_map'):
                 # 如果没有进行中的追踪号，但事件信息里有订单引用号 (order_ref)，并且策略有订单引用号到交易ID的映射表。 (如果没有进行中的追踪号，但是这次事件跟某个订单有关，并且我们有订单号到追踪号的对应表。)
                 # If no current trade ID, but kwargs contain 'order_ref' and the mapping exists.
                 trade_id = self.order_ref_to_trade_id_map.get(kwargs['order_ref'], None)
                 # 尝试从映射表中查找对应的交易周期ID。 (去对应表里查查这个订单号对应的追踪号。)
                 # Try to find the corresponding trade cycle ID from the map.
                 if trade_id:
                     # 如果找到了。 (如果查到了。)
                     # If found.
                     log_entry['trade_cycle_id'] = trade_id
                     # 将找到的交易周期ID添加到日志条目中。 (把找到的追踪号放进盒子。)
                     # Add the found trade cycle ID to the log entry.
                 # else:
                 #     log_entry['trade_cycle_id'] = 'ORPHANED_ORDER_EVENT' # 可选：标记孤儿订单事件 (Optional: Mark orphan order event)
                 #     # Optional: Mark as an orphan order event if not found.

            # 合并额外的关键字参数 (Merge additional keyword arguments)
            log_entry.update(kwargs)
            # 将调用时传入的其他信息（kwargs）也添加到日志条目中。 (把调用这个记录工具时附带的其他信息也放进盒子。)
            # Merge any additional keyword arguments passed to the function into the log entry.

            # 使用附加信息调用 logger，以便 formatter 可以访问它们
            # (Call logger with extra info so formatter can access them)
            # self.logger.info(log_entry, extra={'strategy_id': log_entry['strategy_id'], 'data_id': log_entry.get('data_id')})
            # 直接传递完整的字典给 info，让 JsonFormatter 处理
            # (Pass the complete dictionary directly to info, let JsonFormatter handle it)
            self.logger.info(log_entry)
            # 调用日志记录器的 info 方法记录日志。 (用记事本的"记录"功能把这个盒子里的信息记下来。)
            # Log the complete log entry dictionary using the logger's info method.

        except Exception as e:
            # 如果在记录日志时发生任何错误。 (如果在记日志的时候出错了。)
            # If any error occurs during logging.
            # Ensure logging errors don't crash the strategy
            # 确保日志错误不会导致策略崩溃
            import sys
            # 导入 sys 模块以访问标准错误流。 (导入 sys 工具包，用来往控制台打错误信息。)
            # Import the sys module to access standard error.
            print(f"CRITICAL: Logging failed! Event: {event_type}, Error: {e}", file=sys.stderr)
            # 在标准错误流中打印错误信息。 (在控制台打印严重的错误信息，说明记日志失败了。)
            # Print a critical error message to standard error.
            # Optionally, log to a fallback logger or handle differently
            # 可选地，记录到备用日志记录器或以其他方式处理
            # Optionally, log to a fallback logger or handle the error differently.

    # ==================== 日志系统核心方法 END ======================

    def log(self, txt, dt=None, data=None):
        # 定义 log 方法，用于简单的文本日志记录（保留原有方法，但建议使用 log_event）。 (定义一个简单的文本记录方法，兼容旧代码，但推荐用新的 log_event。)
        ''' Logging function for this strategy'''
        # '''此策略的日志记录功能'''
        # 使用 log_event 记录简单消息
        # (Log simple messages using log_event)
        log_dt = dt or self.datas[0].datetime.date(0)
        # 获取日志时间戳，优先使用传入的 dt，否则使用第一个数据源的当前日期。 (拿到日志时间，有传入的就用，没有就用第一个数据的日期。)
        # Get the log timestamp, preferring the passed dt, otherwise use the date from the first data feed.
        # print('%s, %s' % (log_dt.isoformat(), txt)) # 旧的打印方式 (Old print method)
        # Old print method.
        self.log_event('LEGACY_LOG', message=txt, log_timestamp=log_dt.isoformat())
        # 调用 log_event 记录，事件类型为 'LEGACY_LOG'。 (用新的 log_event 来记录，类型标记为旧日志。)
        # Call log_event to record the message with type 'LEGACY_LOG'.


    def __init__(self, **kwargs):  # 接受 **kwargs 以兼容 addstrategy 传递的参数 (Accept **kwargs to be compatible with parameters passed by addstrategy)
        # 定义策略的初始化函数__init__，在策略对象创建时自动执行。 (定义策略初始化要做的事情。)
        # Define the strategy initialization function __init__, executed automatically when the strategy object is created.

        # --- 初始化日志系统 ---
        # (Initialize logging system)
        self._setup_logger() # 调用内部方法设置日志记录器 (Call internal method to set up the logger)
        # Call the internal method to set up the logger.
        self.log_event('STRATEGY_INIT_START') # 记录初始化开始 (Log initialization start)
        # Log the start of the strategy initialization.


        # --- 初始化交易周期 ID 管理 ---
        # (Initialize trade cycle ID management)
        self.order_ref_to_trade_id_map = {} # 订单引用到交易周期ID的映射 (Mapping from order reference to trade cycle ID)
        # Initialize an empty dictionary to map order references to trade cycle IDs.
        self.current_trade_id = None # 当前活跃的交易周期ID (Currently active trade cycle ID)
        # Initialize the currently active trade cycle ID to None.


        # 引用数据源。 (Reference the data feeds.)
        # Keep a reference to the "close" line in the data[0] dataseries
        # self.dataclose = self.datas[0].close # 原有代码 (Original code)
        # Original code referencing only the first data's close line.
        # 引用所有数据源的收盘价、开盘价、最高价、最低价 (Reference close, open, high, low prices for all data feeds)
        self.d_close = {d._name: d.close for d in self.datas}
        # 创建一个字典，存储每个数据源名称到其收盘价序列的映射。 (创建一个字典，记录每个数据源名字和它的收盘价数据。)
        # Create a dictionary mapping each data feed name to its close price series.
        self.d_open = {d._name: d.open for d in self.datas}
        # 创建一个字典，存储每个数据源名称到其开盘价序列的映射。 (创建一个字典，记录每个数据源名字和它的开盘价数据。)
        # Create a dictionary mapping each data feed name to its open price series.
        self.d_high = {d._name: d.high for d in self.datas}
        # 创建一个字典，存储每个数据源名称到其最高价序列的映射。 (创建一个字典，记录每个数据源名字和它的最高价数据。)
        # Create a dictionary mapping each data feed name to its high price series.
        self.d_low = {d._name: d.low for d in self.datas}
        # 创建一个字典，存储每个数据源名称到其最低价序列的映射。 (创建一个字典，记录每个数据源名字和它的最低价数据。)
        # Create a dictionary mapping each data feed name to its low price series.

        # 引用主要数据源（第一个）以便快速访问，如果存在的话
        # (Reference the primary data feed (the first one) for quick access if it exists)
        self.data = self.datas[0] if self.datas else None
        # 将第一个数据源赋值给 self.data，如果数据源列表不为空。 (如果至少有一个数据源，把第一个存到 self.data 方便使用。)
        # Assign the first data feed to self.data if the data feeds list is not empty.
        self.dataclose = self.data.close if self.data else None # 保持原有 self.dataclose 的兼容性 (Maintain compatibility with original self.dataclose)
        # 如果 self.data 存在，将其收盘价序列赋值给 self.dataclose，保持旧代码兼容性。 (如果 self.data 有东西，把它的收盘价存到 self.dataclose，兼容旧代码。)
        # Assign the close series of self.data to self.dataclose if self.data exists, for backward compatibility.


        # To keep track of pending orders and buy price/commission
        # 跟踪待处理订单和买入价格/佣金 (To keep track of pending orders and buy price/commission)
        self.order = None
        # 初始化 self.order 为 None，用于跟踪最近的待处理订单。 (初始化一个变量 self.order，用来记住最近还没完成的订单。)
        # Initialize self.order to None, used to track the most recent pending order.
        self.buyprice = None
        # 初始化 self.buyprice 为 None，用于记录买入价格。 (初始化一个变量 self.buyprice，用来记买入价。)
        # Initialize self.buyprice to None, used to record the buy price.
        self.buycomm = None
        # 初始化 self.buycomm 为 None，用于记录买入佣金。 (初始化一个变量 self.buycomm，用来记买入佣金。)
        # Initialize self.buycomm to None, used to record the buy commission.

        # 实例化指标 (Instantiate Indicators)
        # self.sma_short = bt.indicators.SimpleMovingAverage(self.datas[0], period=self.params.ema_short_period) # 原有代码 (Original code)
        # self.sma_medium = bt.indicators.SimpleMovingAverage(self.datas[0], period=self.params.ema_medium_period) # 原有代码 (Original code)
        # self.sma_long = bt.indicators.SimpleMovingAverage(self.datas[0], period=self.params.ema_long_period) # 原有代码 (Original code)
        # self.bbands = bt.indicators.BollingerBands(self.datas[0], period=self.params.bbands_period, devfactor=self.params.bbands_devfactor) # 原有代码 (Original code)

        # 为每个数据源创建指标实例 (Create indicator instances for each data feed)
        self.inds = {}
        # 初始化一个空字典 self.inds，用于存储每个数据源的指标。 (准备一个空盒子 self.inds，用来放每个数据源对应的指标工具。)
        # Initialize an empty dictionary self.inds to store indicators for each data feed.
        for d in self.datas:
            # 遍历所有数据源。 (检查每一个数据源。)
            # Iterate through all data feeds.
            self.inds[d._name] = {} # 为每个数据源创建一个内部字典 (Create an inner dictionary for each data feed)
            # 在 self.inds 中为当前数据源 d 创建一个专属的小盒子。 (给当前数据源 d 在 self.inds 里创建一个专属小盒子。)
            # Create an inner dictionary for the current data feed d within self.inds.

            # 使用 self.p 访问参数 (Access parameters using self.p)
            self.inds[d._name]['ema_short'] = bt.indicators.ExponentialMovingAverage(d, period=self.p.ema_short_period)
            # 创建短期 EMA 指标实例，并存入对应数据源的小盒子。 (创建短期 EMA 指标，放到对应数据源的小盒子里。)
            # Create a short-term EMA indicator instance and store it in the dictionary for the corresponding data feed.
            self.inds[d._name]['ema_medium'] = bt.indicators.ExponentialMovingAverage(d, period=self.p.ema_medium_period)
            # 创建中期 EMA 指标实例，并存入对应数据源的小盒子。 (创建中期 EMA 指标，放到对应数据源的小盒子里。)
            # Create a medium-term EMA indicator instance and store it.
            self.inds[d._name]['ema_long'] = bt.indicators.ExponentialMovingAverage(d, period=self.p.ema_long_period)
            # 创建长期 EMA 指标实例，并存入对应数据源的小盒子。 (创建长期 EMA 指标，放到对应数据源的小盒子里。)
            # Create a long-term EMA indicator instance and store it.
            self.inds[d._name]['bbands'] = bt.indicators.BollingerBands(d, period=self.p.bbands_period, devfactor=self.p.bbands_devfactor)
            # 创建布林带指标实例，并存入对应数据源的小盒子。 (创建布林带指标，放到对应数据源的小盒子里。)
            # Create a Bollinger Bands indicator instance and store it.
            self.inds[d._name]['atr'] = bt.indicators.AverageTrueRange(d, period=self.p.atr_period)
            # 创建 ATR 指标实例，并存入对应数据源的小盒子。 (创建 ATR 指标，放到对应数据源的小盒子里。)
            # Create an Average True Range (ATR) indicator instance and store it.

        # 风险管理相关变量 (Risk management related variables)
        self.halt_trading_until = None # 暂停交易直到指定时间戳 (Halt trading until specified timestamp)
        # 初始化 self.halt_trading_until 为 None，标记当前是否处于暂停交易状态。 (初始化一个标记，表示现在没暂停交易。)
        # Initialize self.halt_trading_until to None, marking if trading is currently halted.
        self.cumulative_risk_units = 0.0 # 累积风险单位 (Cumulative risk units)
        # 初始化 self.cumulative_risk_units 为 0.0，记录当前累积的总风险。 (初始化一个计数器，记录总共承担了多少风险。)
        # Initialize self.cumulative_risk_units to 0.0, tracking the total accumulated risk.
        self.open_trades = 0 # 当前持仓交易数量 (Number of currently open trades)
        # 初始化 self.open_trades 为 0，记录当前有多少笔交易还在进行中。 (初始化一个计数器，记录当前有几单在手。)
        # Initialize self.open_trades to 0, tracking the number of currently open trades.
        self.initial_portfolio_value = self.broker.getvalue() # 记录初始投资组合价值 (Record initial portfolio value)
        # 记录策略开始时的总资产。 (记一下开始时有多少钱。)
        # Record the initial portfolio value at the start of the strategy.
        self.high_water_mark = self.initial_portfolio_value # 记录最高水位线 (Record high water mark)
        # 初始化最高水位线为初始总资产。 (记一下历史最高赚到过多少钱，初始就是本金。)
        # Initialize the high water mark to the initial portfolio value.

        # 使用 kwargs 更新参数，如果它们在 params 中定义了
        # (Update parameters using kwargs if they are defined in params)
        for key, value in kwargs.items():
            # 遍历从 addstrategy 传入的参数。 (检查通过 addstrategy 传进来的每个参数。)
            # Iterate through the parameters passed via addstrategy.
            if hasattr(self.params, key):
                # 如果这个参数是策略本身定义的参数之一。 (如果这个参数是咱们策略认识的。)
                # If this parameter is one defined by the strategy itself.
                setattr(self.params, key, value)
                # 更新策略参数的值。 (那就更新一下这个参数的值。)
                # Update the value of the strategy parameter.
                self.log_event('PARAM_OVERRIDE', param_key=key, param_value=value)
                # 记录参数被覆盖的事件。 (记一笔日志，说这个参数被传进来的值覆盖了。)
                # Log an event indicating that the parameter was overridden.
            # else:
                # self.log_event('UNKNOWN_PARAM_PASSED', param_key=key, param_value=value) # 可选：记录未知参数 (Optional: log unknown parameters)
                # Optional: Log an event if an unknown parameter was passed.

        # 记录策略初始化完成和参数
        # (Log strategy initialization completion and parameters)
        param_dict = {p: getattr(self.params, p) for p in dir(self.params) if not p.startswith('_')}
        # 获取所有策略参数及其值，过滤掉内部属性和方法。 (Get all strategy parameters and their values, filtering out internal attributes and methods.)
        # Get all strategy parameters and their values into a dictionary, filtering out internal attributes and methods.
        data_ids = [d._name for d in self.datas]
        # 获取所有数据源的名称列表。 (拿到所有数据源的名字。)
        # Get a list of names for all data feeds.
        self.log_event('STRATEGY_INIT_COMPLETE', params=param_dict, data_ids=data_ids)
        # 记录策略初始化完成事件，包含参数和数据源信息。 (记录一条日志，说策略初始化完成了，并附上所有参数和数据源名字。)
        # Log an event indicating strategy initialization is complete, including parameters and data feed names.

    def notify_order(self, order):
        # 定义订单状态通知函数notify_order，当订单状态发生变化时被调用，参数order是订单对象。 (定义订单通知函数，当订单状态变化的时候，程序会跑这个函数来通知你。)
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
