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
from collections import OrderedDict
from backtrader.utils.py3 import iteritems
from backtrader.order import Order

# --- Enhanced Logging System ---


class JsonFormatter(logging.Formatter):
    """自定义 Formatter，用于输出 JSON Lines 格式"""
    # (自定义 Formatter，把日志消息变成一行行的 JSON。)

    def format(self, record):
        # 创建基础日志记录字典 (创建一个基本的日志字典)
        log_record = {
            "timestamp": datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
            "level": record.levelname,
            "logger_name": record.name,
        }
        # 如果 record.msg 是字典，则合并 (如果日志消息本身是个字典，就把它合并进来)
        if isinstance(record.msg, dict):
            log_record.update(record.msg)
        else:
            # 否则，将消息放在 message 字段中 (如果不是字典，就把消息放在 'message' 字段里)
            log_record["message"] = record.getMessage()

        # 添加异常信息（如果存在）(如果程序出错了，把错误信息也加进去)
        if record.exc_info:
            log_record['exc_info'] = self.formatException(record.exc_info)

        # 将字典序列化为 JSON 字符串 (把字典变成 JSON 字符串)
        # 使用 default=str 处理无法序列化的类型
        return json.dumps(log_record, ensure_ascii=False, default=str)


# --- Global variable for the background logging thread ---
# (全局变量，用来放后台写日志的那个线程。)
_log_listener = None
_log_queue = None


def setup_logging(log_path, filename_pattern, strategy_name, data_name, pid, log_level='INFO', log_async_write=True):
    """设置日志系统"""
    # (这个函数用来设置日志怎么记录。)
    global _log_listener, _log_queue

    # 确保日志目录存在 (确保放日志的文件夹存在)
    os.makedirs(log_path, exist_ok=True)

    # 格式化文件名 (把文件名弄得好看点，加上策略名、数据名、时间啥的)
    timestamp_str = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    log_filename = filename_pattern.format(
        strategy_name=strategy_name,
        data_name=data_name,
        timestamp=timestamp_str,
        pid=pid
    )
    log_file_path = os.path.join(log_path, log_filename)

    # 获取根 logger (拿到日志系统的老大)
    logger = logging.getLogger(strategy_name)  # 使用策略名作为 logger 名称
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    # 移除所有现有的 handlers，避免重复添加 (先把以前可能加过的处理器都删掉，免得日志记好几遍)
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    # 避免日志传播到父 logger (不让日志消息传给上级 logger)
    logger.propagate = False

    # 创建 JSON Formatter (创建一个能输出 JSON 的格式化器)
    formatter = JsonFormatter()

    if log_async_write:
        # --- 异步写入设置 ---
        # (设置异步写日志，这样写日志就不会卡住策略运行了。)
        if _log_queue is None:
            # 创建一个队列，用于在线程间传递日志记录 (创建一个队列，用来放日志消息)
            _log_queue = queue.Queue(-1)  # 无限队列大小

        # 创建文件处理器，用于将日志写入文件 (创建一个处理器，负责把日志写到文件里)
        file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
        # 设置文件处理器的格式化器 (告诉文件处理器怎么格式化日志)
        file_handler.setFormatter(formatter)

        if _log_listener is None or not _log_listener.is_alive():
            # 创建并启动队列监听器，它会在后台线程中处理日志队列中的记录 (创建并启动一个监听器，它在后台偷偷地把队列里的日志写到文件里)
            _log_listener = logging.handlers.QueueListener(
                _log_queue, file_handler, respect_handler_level=True)
            _log_listener.start()

        # 创建队列处理器，将日志记录放入队列 (创建一个处理器，负责把日志消息扔到队列里)
        queue_handler = logging.handlers.QueueHandler(_log_queue)
        # 添加队列处理器到 logger (把这个队列处理器加给日志系统的老大)
        logger.addHandler(queue_handler)
    else:
        # --- 同步写入设置 ---
        # (设置同步写日志，日志会立刻写到文件里，但可能会稍微卡一下策略。)
        # 创建文件处理器 (直接创建文件处理器)
        file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
        # 设置格式化器 (设置格式化器)
        file_handler.setFormatter(formatter)
        # 添加处理器到 logger (直接把文件处理器加给日志系统的老大)
        logger.addHandler(file_handler)

    # 添加一个 StreamHandler 将日志输出到控制台，方便调试 (加一个处理器，把日志也打到屏幕上，方便看)
    # stream_handler = logging.StreamHandler()
    # stream_handler.setFormatter(formatter)
    # logger.addHandler(stream_handler)

    return logger  # 返回设置好的 logger


def stop_logging():
    """安全停止日志系统"""
    # (这个函数用来安全地停止日志系统。)
    global _log_listener
    if _log_listener:
        try:
            # 停止监听器线程 (停止后台写日志的那个线程)
            _log_listener.stop()
            _log_listener = None  # 重置全局变量
            _log_queue = None  # 重置全局变量
        except Exception as e:
            # 打印停止日志监听器时发生的任何错误 (如果停止时出错了，打印出来)
            print(f"Error stopping logging listener: {e}")
# --- End Enhanced Logging System ---


class AShareETFStrategy(bt.Strategy):
    # 定义一个名为AShareETFStrategy的类，它继承自bt.Strategy，表示这是一个Backtrader交易策略类。 (创建一个叫做AShareETFStrategy的策略类，它继承了bt.Strategy，说明这是个交易策略。)
    params = (
        ('ema_short_period', 12),
        ('ema_medium_period', 26),
        ('ema_long_period', 52),
        ('rsi_period', 14),
        ('bbands_period', 20),
        ('bbands_devfactor', 2.0),
        ('atr_period', 14),
        ('risk_per_trade_percent', 0.02),
        ('max_total_risk_percent', 0.1),
        ('stop_loss_atr_multiplier', 2.0),
        ('take_profit_atr_multiplier', 3.0),
        ('trailing_stop_atr_multiplier', 1.5),
        ('use_trailing_stop', True),
        ('partial_exit_atr_multiplier', 1.5),
        ('use_partial_exit', True),
        ('partial_exit_fraction', 0.5),
        ('trade_halt_drawdown_percent', 0.2),
        ('trade_resume_threshold', 0.1),
        ('trading_enabled', True),
        ('printlog', True),  # 控制是否打印普通日志 (Control whether to print regular logs)
        # --- Logging Parameters ---
        # (日志系统参数)
        ('log_path', './logs'),  # 日志文件存储路径 (Log file storage path)
        # 日志文件名模板 (Log filename template)
        ('log_filename_pattern',
         '{strategy_name}_{data_name}_{timestamp}_{pid}.log'),
        ('log_level', 'INFO'),  # 日志级别 (Log level)
        # 是否异步写入日志 (Whether to write logs asynchronously)
        ('log_async_write', True),
        # ------------------------
    )

    # 记录传入的kwargs到策略的参数中，以便在日志中记录。
    # (Record the incoming kwargs into the strategy's parameters for logging purposes.)
    # ... (保持传入的 kwargs)

    def log(self, txt, dt=None, data=None):
        # 定义日志记录函数log，用于输出策略运行过程中的信息，可选参数dt指定日期，printlog控制是否打印。
        # (Define the logging function log to output information during strategy execution, optional parameter dt specifies the date, printlog controls printing.)
        # ''' Logging function for this strategy'''
        # (这个策略的日志记录函数)
        # 如果params中的printlog为False，则不执行任何操作。
        # (If printlog in params is False, do nothing.)
        if self.p.printlog:
            # 获取当前日期，如果未提供dt，则使用当前数据的日期时间。
            # (Get the current date, use the current data's datetime if dt is not provided.)
            dt = dt or (data.datetime.date(
                0) if data else self.datas[0].datetime.date(0))
            # 打印带有日期和文本的日志信息。
            # (Print the log message with date and text.)
            print(f'{dt.isoformat()}, {txt}')

    def __init__(self, **kwargs):  # 接受 **kwargs 以兼容 addstrategy 传递的参数
        # 定义策略的初始化函数__init__，在策略对象创建时自动执行。
        # (Define the initialization function __init__, executed automatically when the strategy object is created.)
        # (Accept **kwargs to be compatible with parameters passed by addstrategy)

        # --- Initialize Logging System ---
        # (初始化日志系统)
        # 创建唯一的策略实例 ID (Create a unique strategy instance ID)
        self.strategy_id = f"{self.__class__.__name__}_{uuid.uuid4().hex[:8]}"
        self.logger = None  # 初始化 logger 为 None (Initialize logger to None)
        # 尝试设置日志，捕获任何可能的错误 (Try to set up logging, catching any potential errors)
        try:
            # 为每个数据源设置单独的 logger (Set up a separate logger for each data feed)
            # 注意：通常策略日志应该聚合，但如果需要区分数据源日志，可以这样做
            # (Note: Usually strategy logs should be aggregated, but this can be done if distinguishing data source logs is needed)
            # 这里我们使用第一个数据源的名称来命名日志文件
            # (Here we use the name of the first data source to name the log file)
            first_data_name = self.datas[0]._name if self.datas else 'default_data'
            self.logger = setup_logging(
                log_path=self.p.log_path,
                filename_pattern=self.p.log_filename_pattern,
                strategy_name=self.__class__.__name__,
                data_name=first_data_name,
                pid=os.getpid(),
                log_level=self.p.log_level,
                log_async_write=self.p.log_async_write
            )
            # 注册退出处理函数，确保日志监听器被停止 (Register exit handler to ensure the log listener is stopped)
            import atexit
            atexit.register(stop_logging)

        except Exception as e:
            # 如果日志设置失败，打印错误信息 (If logging setup fails, print the error message)
            print(
                f"Error setting up logger for strategy {self.strategy_id}: {e}", file=sys.stderr)
            # 提供一个备用 logger (Provide a fallback logger)
            self.logger = logging.getLogger('fallback_logger')
            # 避免 "No handler found" 警告 (Avoid "No handler found" warnings)
            self.logger.addHandler(logging.NullHandler())

        # 初始化交易周期 ID 和订单映射 (Initialize trade cycle ID and order mapping)
        # 当前活跃的交易周期 ID (Current active trade cycle ID)
        self.current_trade_id = None
        # 订单引用到交易周期 ID 的映射 (Mapping from order reference to trade cycle ID)
        self.order_ref_to_trade_id_map = {}

        # --- Log Strategy Initialization ---
        # (记录策略初始化事件)
        self.log_event(
            event_type='STRATEGY_INIT',
            # 使用第一个数据源作为参考 (Use the first data feed as reference)
            data_feed=self.datas[0],
            strategy_name=self.__class__.__name__,
            params=self.p._getkwargs(),  # 获取所有参数 (Get all parameters)
            # 获取所有数据源的名称 (Get names of all data feeds)
            data_ids=[d._name for d in self.datas]
        )
        # --- End Logging System Init ---

        # 引用数据源。
        # (Reference the data feeds.)
        self.closes = [d.close for d in self.datas]
        # 创建一个列表self.closes，存储每个数据源的收盘价序列。 (创建一个列表，用来放每个ETF的收盘价数据，收盘价是最重要的价格数据。)
        self.volumes = [d.volume for d in self.datas]
        # 创建一个列表self.volumes，存储每个数据源的成交量序列。 (创建一个列表，用来放每个ETF的成交量数据，成交量也很重要，可以看出市场活跃度。)

        # 指标计算
        # (Indicator Calculation)
        # 为每个数据源计算所需的指标
        # (Calculate required indicators for each data feed)
        self.ema_shorts = [bt.indicators.ExponentialMovingAverage(
            d, period=self.p.ema_short_period) for d in self.datas]
        # 计算短期EMA (Calculate short-term EMA)
        self.ema_mediums = [bt.indicators.ExponentialMovingAverage(
            d, period=self.p.ema_medium_period) for d in self.datas]
        # 计算中期EMA (Calculate medium-term EMA)
        self.ema_longs = [bt.indicators.ExponentialMovingAverage(
            d, period=self.p.ema_long_period) for d in self.datas]
        # 计算长期EMA (Calculate long-term EMA)
        self.rsis = [bt.indicators.RelativeStrengthIndex(
            d, period=self.p.rsi_period) for d in self.datas]
        # 计算RSI (Calculate RSI)
        self.bbands = [bt.indicators.BollingerBands(
            d, period=self.p.bbands_period, devfactor=self.p.bbands_devfactor) for d in self.datas]
        # 计算布林带 (Calculate Bollinger Bands)
        self.atrs = [bt.indicators.AverageTrueRange(
            d, period=self.p.atr_period) for d in self.datas]
        # 计算ATR (Calculate ATR)

        # 状态变量
        # (State Variables)
        # 用于跟踪当前活动的订单 (Used to track the currently active order)
        self.order = None
        self.trade_count = 0  # 交易计数 (Trade count)
        self.trailing_stop_price = None  # 跟踪止损价格 (Trailing stop price)
        # 账户最高价值，用于计算回撤 (Highest account value for drawdown calculation)
        self.high_water_mark = self.broker.getvalue()
        self.drawdown = 0.0  # 当前回撤百分比 (Current drawdown percentage)
        self.in_trade_halt = False  # 是否处于交易暂停状态 (Whether in trade halt status)
        # 存储活动订单引用及其类型 {order_ref: type} (Stores active order references and their types)
        self.active_orders = {}
        # 标记部分退出是否已执行 (Flag if partial exit has been executed)
        self.partial_exit_executed = False

    def log_event(self, event_type: str, data_feed: bt.DataBase, **kwargs):
        """统一的日志记录接口"""
        # (The unified logging interface)
        # 如果 logger 未初始化，则不记录 (If logger is not initialized, do not log)
        if not self.logger:
            return

        # 尝试记录日志，捕获并打印任何错误，防止中断策略 (Try to log, catch and print any errors to prevent interrupting the strategy)
        try:
            # 构建基础日志记录 (Build the base log record)
            log_entry = {
                "event_type": event_type,
                "strategy_id": self.strategy_id,
                # 获取数据源名称 (Get data feed name)
                "data_id": data_feed._name if data_feed else 'N/A',
            }

            # 尝试添加 trade_cycle_id (Try to add trade_cycle_id)
            if hasattr(self, 'current_trade_id') and self.current_trade_id:
                log_entry['trade_cycle_id'] = self.current_trade_id
            # 如果是订单状态更新或交易关闭事件，尝试从映射中查找 trade_cycle_id (If it's an order status update or trade closed event, try to find trade_cycle_id from the map)
            elif event_type in ['ORDER_STATUS_UPDATE', 'TRADE_CLOSED'] and 'order_ref' in kwargs:
                order_ref = kwargs['order_ref']
                if isinstance(order_ref, bt.Order):
                    # 如果传入的是 Order 对象，获取其 ref (If an Order object is passed, get its ref)
                    order_ref = order_ref.ref
                log_entry['trade_cycle_id'] = self.order_ref_to_trade_id_map.get(
                    order_ref, 'ORPHANED_EVENT')  # 从映射获取，记录孤立事件 (Get from map, log orphaned events)
            elif event_type == 'TRADE_CLOSED' and 'trade' in kwargs:
                trade = kwargs['trade']
                # 默认是孤立交易 (Default to orphaned trade)
                found_trade_id = 'ORPHANED_TRADE'
                if hasattr(trade, 'orders') and trade.orders:
                    for order_ref in trade.orders:
                        mapped_id = self.order_ref_to_trade_id_map.get(
                            order_ref)
                        if mapped_id:
                            found_trade_id = mapped_id
                            # 找到第一个匹配的即可 (Break once the first match is found)
                            break
                log_entry['trade_cycle_id'] = found_trade_id

            # 合并事件特定数据 (Merge event-specific data)
            log_entry.update(kwargs)

            # 使用 logger 记录日志 (Log using the logger)
            # 使用 .info() 并传入字典 (Use .info() and pass the dictionary)
            self.logger.info(log_entry)

        except Exception as e:
            # 打印日志记录期间发生的任何错误 (Print any errors that occur during logging)
            print(
                f"Error during logging event {event_type}: {e}", file=sys.stderr)

    # --- Lifecycle Methods ---
    # (生命周期方法)
    def start(self):
        """策略启动时调用"""
        # (Called when the strategy starts)
        self.high_water_mark = self.broker.getvalue()
        self.log_event(event_type="STRATEGY_START",
                       data_feed=self.datas[0], initial_value=self.broker.getvalue())

    def notify_order(self, order):
        # 定义订单状态通知函数notify_order，当订单状态发生变化时被调用，参数order是订单对象。 (定义订单通知函数，当订单状态变化的时候，程序会跑这个函数来通知你。)
        order_ref = order.ref  # 获取订单引用 (Get order reference)
        # 获取订单关联的数据源 (Get data feed associated with the order)
        data = order.data
        status_name = order.getstatusname()  # 获取订单状态名称 (Get order status name)

        # --- Log Order Status Update ---
        # (记录订单状态更新事件)
        # 初始化执行详情为 None (Initialize execution details to None)
        exec_details = None
        # 初始化剩余大小为 None (Initialize remaining size to None)
        remaining_size = None
        if order.executed:
            # 如果订单有执行部分 (If the order has an execution part)
            exec_details = {
                "price": order.executed.price,
                "size": order.executed.size,
                "value": order.executed.value,
                "commission": order.executed.comm
            }
            # 获取剩余未执行的大小 (Get the remaining unexecuted size)
            remaining_size = order.executed.remsize

        self.log_event(
            event_type='ORDER_STATUS_UPDATE',
            data_feed=data,
            order_ref=order_ref,
            status=status_name,
            order_type=order.ordtypename(),
            order_size=order.size,
            order_price=order.price,
            exec_type=order.getordername(),
            exec_details=exec_details,
            remaining_size=remaining_size,
            # 记录父订单引用 (Log parent order reference)
            parent_ref=order.parent.ref if order.parent else None,
            # 记录 OCO 订单引用 (Log OCO order reference)
            oco_ref=order.oco.ref if order.oco else None
        )
        # --- End Log ---

        # 打印订单日志
        # (Print order log)
        self.log(f'{data._name} Order {order.getstatusname()}: Ref:{order.ref}, Size:{order.size}, Price:{order.price:.2f}, ExecType:{order.getordername()}, Comm:{order.executed.comm:.2f}, Pnl:{order.executed.pnl:.2f}', data=data)

        if order.status in [order.Submitted, order.Accepted]:
            # 如果订单已提交或已接受，则不执行任何操作，等待后续通知。
            # (If the order is submitted or accepted, do nothing and wait for further notifications.)
            # 记录活动订单 (Record active order)
            self.active_orders[order_ref] = order.ordtypename()
            return

        if order.status in [order.Completed]:
            # 如果订单已完成 (If the order is completed)
            if order_ref in self.active_orders:
                # 从活动订单中移除 (Remove from active orders)
                del self.active_orders[order_ref]
            if order.isbuy():
                # 如果是买入订单完成。
                # (If it is a buy order completed.)
                self.log(
                    f'{data._name} BUY EXECUTED, Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f}, Comm {order.executed.comm:.2f}', data=data)
                # 记录买入执行信息，包括价格、成本和佣金。 (Log buy execution details including price, cost, and commission.)
                # 重置部分退出标记 (Reset partial exit flag)
                self.partial_exit_executed = False
            elif order.issell():
                # 如果是卖出订单完成。
                # (If it is a sell order completed.)
                self.log(
                    f'{data._name} SELL EXECUTED, Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f}, Comm {order.executed.comm:.2f}', data=data)
                # 记录卖出执行信息，包括价格、成本和佣金。 (Log sell execution details including price, cost, and commission.)

        elif order.status in [order.Canceled, order.Margin, order.Rejected, order.Expired]:
            # 如果订单被取消、因保证金不足、被拒绝或已过期。
            # (If the order was canceled, met margin, rejected, or expired.)
            self.log(
                f'{data._name} Order {order.getstatusname()}: Ref:{order.ref}', data=data)
            # 记录订单状态。
            # (Log the order status.)
            if order_ref in self.active_orders:
                # 从活动订单中移除 (Remove from active orders)
                del self.active_orders[order_ref]

            # --- 清理映射 (非 Bracket 订单) ---
            # (Clean up mapping (non-Bracket orders))
            # 注意：这里仅作为辅助清理，主要清理逻辑在 notify_trade 中
            # (Note: This is only auxiliary cleanup; main cleanup logic is in notify_trade)
            # 检查是否是 Bracket 订单的一部分 (Check if part of a Bracket order)
            is_bracket = order.parent or order.oco
            if not is_bracket and order_ref in self.order_ref_to_trade_id_map:
                # 如果不是 Bracket 订单且引用在映射中 (If not a Bracket order and ref is in the map)
                try:
                    del self.order_ref_to_trade_id_map[order_ref]
                    # 记录映射清理事件 (Log map cleanup event)
                    self.log_event(event_type="MAP_CLEANUP", data_feed=data,
                                   reason="Order Final State (Non-Bracket)", order_ref=order_ref)
                except KeyError:
                    # 可能已被 notify_trade 清理 (May have already been cleaned by notify_trade)
                    pass
            # --- End Cleanup ---

        # 重置 self.order 跟踪变量 (Reset self.order tracking variable)
        self.order = None
        # 重置订单跟踪变量。 (Reset the order tracking variable.)
        self.trailing_stop_price = None  # 重置跟踪止损价 (Reset trailing stop price)

    def notify_trade(self, trade):
        # 定义交易通知函数notify_trade，当交易（一买一卖）完成时被调用，参数trade是交易对象。 (定义交易完成通知函数，当一次完整的买卖结束了，程序会跑这个函数来通知你。)
        # 获取交易关联的数据源 (Get data feed associated with the trade)
        data = trade.data

        if not trade.isclosed:
            # 如果交易尚未关闭（例如，只是部分成交开仓），则直接返回，不处理。
            # (If the trade is not closed yet (e.g., only partially filled on entry), return directly.)
            # --- Log Partial Trade Update (Optional) ---
            # 可以选择性地在这里记录部分成交的更新信息
            # (Optionally log partial fill update information here)
            # self.log_event(event_type='TRADE_PARTIAL_UPDATE', data_feed=data, trade=trade, ...)
            return

        # --- Log Trade Closed ---
        # (记录交易关闭事件)
        self.log_event(
            event_type='TRADE_CLOSED',
            data_feed=data,
            # 传递 trade 对象以便 log_event 提取 trade_id (Pass trade object for log_event to extract trade_id)
            trade=trade,
            pnl=trade.pnl,
            pnlcomm=trade.pnlcomm,
            duration_bars=trade.barlen,
            open_datetime=trade.open_datetime().isoformat() if trade.dtopen else None,
            close_datetime=trade.close_datetime().isoformat() if trade.dtclose else None,
            size=trade.size,  # 最终成交大小 (Final executed size)
            price=trade.price,  # 平均成交价格 (Average executed price)
            value=trade.value,  # 最终价值 (Final value)
            commission=trade.commission,  # 总佣金 (Total commission)
            # 尝试获取 position_type (Try to get position_type)
            # position_type=self.position_types.get(data, 'Unknown') # 需要正确设置 self.position_types
        )
        # --- End Log ---

        # 打印交易日志
        # (Print trade log)
        self.log(f'{data._name} TRADE CLOSED, Pnl Gross:{trade.pnl:.2f}, Pnl Net:{trade.pnlcomm:.2f}, Duration:{trade.barlen} bars', data=data)

        # --- Cleanup trade_cycle_id mapping and reset current_trade_id ---
        # (清理 trade_cycle_id 映射并重置 current_trade_id)
        cleaned_refs = []  # 记录被清理的引用 (Record cleaned references)
        # 记录要清除的 trade_id (Record the trade_id to clear)
        trade_id_to_clear = None
        if hasattr(trade, 'orders') and trade.orders:
            # 如果 trade 对象包含订单引用列表 (If the trade object contains a list of order references)
            for order_ref in trade.orders:
                # 遍历交易中的所有订单引用 (Iterate through all order references in the trade)
                if order_ref in self.order_ref_to_trade_id_map:
                    # 如果引用在映射中 (If the reference is in the map)
                    if trade_id_to_clear is None:
                        trade_id_to_clear = self.order_ref_to_trade_id_map[order_ref]
                    # 尝试删除映射条目，使用 try-except 处理可能的 KeyError (Try to delete the map entry, handle potential KeyError)
                    try:
                        del self.order_ref_to_trade_id_map[order_ref]
                        cleaned_refs.append(order_ref)
                    except KeyError:
                        # 可能已被 notify_order 清理 (Might have been cleaned by notify_order already)
                        pass

        # 记录清理日志 (Log cleanup event)
        if cleaned_refs:
            self.log_event(event_type="MAP_CLEANUP", data_feed=data, reason="Trade Closed",
                           cleaned_order_refs=cleaned_refs, associated_trade_id=trade_id_to_clear)

        # 重置当前交易 ID (如果它与刚关闭的交易匹配) (Reset current trade ID if it matches the closed trade)
        if trade_id_to_clear and self.current_trade_id == trade_id_to_clear:
            self.log_event(event_type="TRADE_CYCLE_END",
                           data_feed=data, trade_cycle_id=self.current_trade_id)
            self.current_trade_id = None
        # --- End Cleanup ---

        # 更新交易计数器 (Update trade counter)
        self.trade_count += 1
        # 清理与该数据源相关的状态（如果适用）(Clean up state related to this data feed if applicable)
        # 例如: (For example:)
        # self.stop_loss_prices[data] = None
        # self.take_profit_prices[data] = None
        # self.position_types[data] = None

    def notify_cashvalue(self, cash, value):
        # 定义现金和总价值通知函数notify_cashvalue，在账户现金或总价值更新时被调用，参数cash是当前现金，value是当前总价值。 (定义现金和总资产值通知函数，当账户里的钱或者总资产变化的时候，程序会跑这个函数来通知你。)
        current_dt = self.datas[0].datetime.datetime(0) # 获取当前时间 (Get current time)
        self.log(f'Cash {cash:.2f}, Value {value:.2f} at {current_dt}')
        # 记录当前的现金和总账户价值。
        # (Log the current cash and total account value.)

        # 更新最高水位线和计算回撤 (Update high water mark and calculate drawdown)
        if value > self.high_water_mark:
            self.high_water_mark = value
            self.drawdown = 0.0
        else:
            self.drawdown = (self.high_water_mark - value) / self.high_water_mark if self.high_water_mark > 0 else 0.0

        # --- Log Risk Event if Drawdown Threshold Exceeded ---
        # (如果超过回撤阈值，则记录风险事件)
        if not self.in_trade_halt and self.drawdown >= self.p.trade_halt_drawdown_percent:
            self.in_trade_halt = True
            self.log_event(
                event_type='RISK_EVENT',
                data_feed=self.datas[0], # 使用第一个数据源作为参考 (Use the first data feed as reference)
                event_subtype='TRADE_HALT_TRIGGERED',
                account_value=value,
                cash=cash,
                drawdown_pct=self.drawdown,
                high_water_mark=self.high_water_mark,
                threshold=self.p.trade_halt_drawdown_percent
            )
            self.log(f"*** TRADE HALT TRIGGERED at {current_dt} due to drawdown {self.drawdown:.2%} exceeding {self.p.trade_halt_drawdown_percent:.1%} ***")
        elif self.in_trade_halt and self.drawdown < self.p.trade_resume_threshold:
            self.in_trade_halt = False
            self.log_event(
                event_type='RISK_EVENT',
                data_feed=self.datas[0],
                event_subtype='TRADE_RESUMED',
                account_value=value,
                cash=cash,
                drawdown_pct=self.drawdown,
                high_water_mark=self.high_water_mark,
                threshold=self.p.trade_resume_threshold
            )
            self.log(f"*** TRADING RESUMED at {current_dt} as drawdown {self.drawdown:.2%} is below {self.p.trade_resume_threshold:.1%} ***")
        # --- End Log ---

    # --- Risk Management Section ---
    # (风险管理部分)
    def _update_risk_params(self):
        """根据当前回撤更新风险参数"""
        # (Update risk parameters based on current drawdown)
        # 此函数可以根据需要扩展更复杂的风险调整逻辑
        # (This function can be extended with more complex risk adjustment logic as needed)
        if self.in_trade_halt:
            # 如果处于交易暂停状态，则不更新 (If in trade halt, do not update)
            return

        # 示例：如果需要基于回撤调整风险乘数等，可以在这里添加逻辑
        # (Example: Add logic here if risk multiplier adjustment based on drawdown is needed)
        # if self.drawdown > some_threshold:
        #     self.current_risk_multiplier = adjusted_value
        # else:
        #     self.current_risk_multiplier = default_value
        pass # 当前无动态风险调整逻辑 (Currently no dynamic risk adjustment logic)

    def get_total_risk_exposure(self):
        """计算当前所有未平仓头寸的总风险敞口"""
        # (Calculate the total risk exposure for all currently open positions)
        total_risk = 0.0
        for data in self.datas:
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
