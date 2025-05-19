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
import backtrader.indicators as btind
from backtrader.analyzers import SharpeRatio, DrawDown, TradeAnalyzer, SQN
import uuid  # 导入 uuid 模块用于生成唯一 ID
import json  # 导入 json 用于序列化日志
import logging  # 导入 logging 模块
import logging.handlers  # 导入 logging handlers
import queue  # 导入 queue 模块
import threading  # 导入 threading 模块
from datetime import datetime  # 导入 datetime
import pytz  # 导入 pytz 处理时区
import decimal  # 导入 decimal 模块
from logging.handlers import QueueHandler, QueueListener, RotatingFileHandler

# --- 日志系统增强 ---
# 定义日志事件类型常量
EVENT_TYPES = {
    "STRATEGY_INIT": "STRATEGY_INIT",
    "MARKET_STATE_ASSESSED": "MARKET_STATE_ASSESSED",
    "SIGNAL_TRIGGERED": "SIGNAL_TRIGGERED",
    "ORDER_CALCULATION": "ORDER_CALCULATION",
    "ORDER_SUBMITTED": "ORDER_SUBMITTED",
    "ORDER_STATUS_UPDATE": "ORDER_STATUS_UPDATE",
    "SL_TP_TRIGGERED": "SL_TP_TRIGGERED",  # 需要在策略中具体实现触发逻辑才能记录
    "TRADE_CLOSED": "TRADE_CLOSED",
    "RISK_EVENT": "RISK_EVENT",  # 需要在策略中具体实现风险事件逻辑才能记录
    "TRADE_SKIPPED": "TRADE_SKIPPED",
    "CASH_VALUE_UPDATE": "CASH_VALUE_UPDATE",  # 新增，记录现金和价值更新
    "INFO_MESSAGE": "INFO_MESSAGE"  # 用于记录通用信息
}

# 自定义 JSON Formatter


class JsonFormatter(logging.Formatter):
    """将日志记录格式化为单行JSON字符串的格式化器"""

    def format(self, record):
        # 定义format方法，将日志记录对象record转换为JSON字符串。 (把日志记录（record）变成JSON字符串。)
        import json
        import datetime
        import decimal

        # 自定义JSON序列化函数，处理常见的非JSON类型
        def json_serializer(obj):
            if isinstance(obj, (datetime.datetime, datetime.date)):
                return obj.isoformat()
            if isinstance(obj, decimal.Decimal):
                return float(obj)
            if hasattr(obj, '__dict__'):  # 处理自定义对象
                return obj.__dict__
            # 对于其他不可序列化的类型，转为字符串
            return str(obj)

        # 提取日志记录的消息部分，若为字典则直接使用，否则创建包含message的字典
        if isinstance(record.msg, dict):
            log_data = record.msg
        else:
            log_data = {"message": record.msg}

        # 添加标准日志字段
        log_data.update({
            "level": record.levelname,
            "logger": record.name,
        })

        # 序列化为JSON，处理特殊类型
        try:
            return json.dumps(log_data, default=json_serializer)
        except Exception as e:
            # 如果序列化失败，返回包含错误信息的简单JSON
            return json.dumps({
                "error": f"JSON serialization failed: {str(e)}",
                "message": str(log_data)
            })

        # ... existing code ...

# 日志系统设置函数


def setup_logging(strategy_name, log_path='logs', log_level='INFO', async_write=True):
    # 定义setup_logging函数，用于配置和初始化日志系统。 (设置并启动我们的高级记录本。)
    # 确保日志目录存在
    # Ensure the log directory exists
    # 如果logs文件夹不存在，就创建一个。 (如果放记录本的文件夹（logs）不存在，就建一个。)
    import logging
    import os
    import time
    import uuid
    import queue
    from logging.handlers import QueueHandler, QueueListener, RotatingFileHandler

    try:
        # 创建日志目录
        if not os.path.exists(log_path):
            os.makedirs(log_path)

        # 生成唯一日志文件名
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        log_filename = f"{log_path}/{strategy_name}_{timestamp}_{unique_id}.jsonl"

        # 设置根日志记录器级别
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, log_level))

        # 创建策略特定的日志记录器
        logger = logging.getLogger(f"strategy.{strategy_name}")
        logger.setLevel(getattr(logging, log_level))
        logger.propagate = False  # 防止日志传递到根记录器

        # 配置文件处理器
        file_handler = RotatingFileHandler(
            log_filename,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(JsonFormatter())

        if async_write:
            # 异步日志写入设置
            log_queue = queue.Queue(-1)  # 无限队列
            queue_handler = QueueHandler(log_queue)
            logger.addHandler(queue_handler)

            # 创建监听器
            listener = QueueListener(
                log_queue, file_handler, respect_handler_level=True)
            listener.start()

            return logger, listener, log_filename
        else:
            # 同步日志写入
            logger.addHandler(file_handler)
            return logger, None, log_filename
    except Exception as e:
        # 确保日志系统错误不影响策略执行
        print(f"Error setting up logging system: {e}")
        import traceback
        traceback.print_exc()

        # 创建一个基本的控制台记录器作为备份
        fallback_logger = logging.getLogger(f"fallback.{strategy_name}")
        fallback_logger.setLevel(logging.INFO)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        fallback_logger.addHandler(console_handler)

        return fallback_logger, None, None
# --- 日志系统增强结束 ---


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
        ('log_level', 'INFO'),  # 添加日志级别参数。 (Add log level parameter.)
        # 添加异步写入配置参数。 (Add async write configuration parameter.)
        ('log_async_write', True),
        ('log_path', 'logs'),  # 添加日志路径参数。 (Add log path parameter.)
    )

    def log(self, txt, level='INFO', event_type=None, data=None, extra_data=None):
        """
        记录日志信息到控制台和日志文件。
        Log information to console and logfile.

        Args:
            txt (str): 日志文本内容
            level (str): 日志级别，默认为'INFO'
            event_type (str): 事件类型
            data: 关联的数据源
            extra_data: 额外数据
        """
        # 获取当前日期时间
        dt = self.datas[0].datetime.date(0) if len(self.datas) > 0 and len(
            self.datas[0]) > 0 else datetime.now().date()

        # 打印到控制台
        print(f'{dt.isoformat()} {level}: {txt}')

        # 如果初始化了日志记录器，也记录到文件
        if hasattr(self, 'logger') and self.logger:
            # 创建日志记录的额外数据
            log_extra = {'custom_extra': {}}
            if event_type:
                log_extra['custom_extra']['event_type'] = event_type
            if data and hasattr(data, '_name'):
                log_extra['custom_extra']['data_name'] = data._name
            if extra_data:
                log_extra['custom_extra'].update(extra_data)

            # 根据级别记录日志
            log_method = getattr(self.logger, level.lower(), self.logger.info)
            log_method(txt, extra=log_extra)

    def log_event(self, event_type, message=None, level='INFO', data_feed=None, **kwargs):
        """
        记录结构化事件日志

        Args:
            event_type: 事件类型常量
            message: 可选的消息描述
            level: 日志级别 ('INFO', 'DEBUG', 'WARNING', 'ERROR')
            data_feed: 数据源对象
            **kwargs: 事件相关的其他数据
        """
        try:
            # 准备标准字段
            from datetime import datetime
            import pytz

            log_data = {
                'timestamp': datetime.now(pytz.UTC).isoformat(),
                'event_type': event_type,
                'strategy_id': self.strategy_id
            }

            # 添加data_id
            if data_feed is not None:
                log_data['data_id'] = data_feed._name if hasattr(
                    data_feed, '_name') else str(data_feed)

            # 添加message
            if message:
                log_data['message'] = message

            # 合并其他事件特定数据
            log_data.update(kwargs)

            # 调用logger记录事件
            if hasattr(self, 'logger') and self.logger:
                getattr(self.logger, level.lower())(log_data)
            else:
                import logging
                logging.getLogger('backtrader').warning(
                    f"Logger not initialized for event: {event_type}")
        except Exception as e:
            # 确保日志系统错误不影响策略执行
            import sys
            import traceback
            error_msg = f"Error in log_event: {e}\n{traceback.format_exc()}"
            sys.stderr.write(error_msg + "\n")
            try:
                # 尝试记录到错误日志文件
                import logging
                error_logger = logging.getLogger('bt_log_system_errors')
                if not error_logger.handlers:
                    error_handler = logging.FileHandler(
                        'logs/bt_log_system_errors.log')
                    error_logger.addHandler(error_handler)
                    error_logger.setLevel(logging.ERROR)
                error_logger.error(error_msg)
            except:
                pass  # 防止二次异常

        # 默认消息
        if message is None:
            message = f"Event: {event_type}"

        # 调用log方法
        self.log(message, level=level, event_type=event_type,
                 data=data_feed, extra_data=kwargs)

    def __init__(self, **kwargs):  # 接受 **kwargs 以兼容 addstrategy 传递的参数
        # 定义策略的初始化函数__init__，在策略对象创建时自动执行。
        # (Define the initialization function __init__, executed automatically when the strategy object is created.)
        # (Accept **kwargs to be compatible with parameters passed by addstrategy)

        # --- 日志系统初始化 ---
        # 生成策略实例的唯一ID。 (Generate a unique ID for the strategy instance.)

        # --- 添加交易周期ID管理 ---
        import uuid
        self.strategy_id = uuid.uuid4().hex  # 策略实例唯一ID
        self.current_trade_id = None  # 当前交易周期ID
        self.order_ref_to_trade_id_map = {}  # 订单引用号到交易周期ID的映射

        self.logger, self.log_listener, self.log_filename = setup_logging(
            # 使用策略ID作为日志文件名的一部分。 (Use strategy ID as part of the log filename.)
            self.strategy_id,
            # 从参数获取日志路径。 (Get log path from parameters.)
            log_path=self.p.log_path,
            # 从参数获取日志级别。 (Get log level from parameters.)
            log_level=self.p.log_level,
            # 从参数获取是否异步写入。 (Get async write setting from parameters.)
            async_write=self.p.log_async_write
        )
        # 使用旧的log方法记录日志文件路径，稍后替换。 (Log the log file path using the old log method, will be replaced later.)
        self.log(f"日志文件初始化完成: {self.log_filename}",
                 level='INFO', event_type=EVENT_TYPES["STRATEGY_INIT"])
        # --- 日志系统初始化结束 ---

        # 创建数据源字典，以便通过名称访问
        # Create a data dictionary for accessing by name
        self.datas_dict = {
            d._name: d for d in self.datas if hasattr(d, '_name')}

        # --- trade_cycle_id 管理初始化 ---
        # 初始化订单引用到交易周期ID的映射字典。 (Initialize the mapping dictionary from order reference to trade cycle ID.)
        self.order_ref_to_trade_id_map = {}
        # 初始化当前交易周期ID为None。 (Initialize the current trade cycle ID to None.)
        self.current_trade_id = None
        # --- trade_cycle_id 管理初始化结束 ---

        # 引用数据源。
        # Reference the data feeds.
        # 获取所有数据源的收盘价序列。 (Get the close price series for all data feeds.)
        self.data_close = {alias: data.close for alias,
                           data in self.datas_dict.items()}
        # 获取所有数据源的成交量序列。 (Get the volume series for all data feeds.)
        self.data_volume = {alias: data.volume for alias,
                            data in self.datas_dict.items()}
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

        # 记录策略初始化完成事件
        # Log strategy initialization completion event
        init_data = {
            # 策略类名。 (Strategy class name.)
            "strategy_name": self.__class__.__name__,
            "params": self.p._getkwargs(),  # 策略参数字典。 (Strategy parameters dictionary.)
            # 所有数据源的别名列表。 (List of aliases for all data feeds.)
            "data_ids": list(self.datas_dict.keys())
        }
        # 注意：这里暂时无法直接调用 log_event，因为旧的 log 方法还存在
        # Note: Cannot call log_event directly here yet as the old log method still exists
        # 我们将在后面统一替换 self.log 为 self.log_event 调用
        # We will replace self.log with self.log_event calls later
        # 使用旧log记录初始化信息。 (Log initialization info using the old log method.)
        self.log(f"策略初始化完成: {init_data}", level='INFO',
                 event_type=EVENT_TYPES["STRATEGY_INIT"], extra_data=init_data)

    def notify_order(self, order):
        # 定义订单状态通知函数notify_order，当订单状态发生变化时被调用，参数order是订单对象。 (定义订单通知函数，当订单状态变化的时候，程序会跑这个函数来通知你。)
        dt = self.data.datetime.datetime()
        data_name = order.data._name

        # 从映射中查找trade_cycle_id
        trade_cycle_id = self.order_ref_to_trade_id_map.get(
            order.ref, 'ORPHANED_ORDER')

        # 获取订单详情
        order_details = {
            'type': order.ordtypename(),
            'size': order.size,
            'price': order.price if order.price else 'market',
            'ref': order.ref,
            'status': 'Unknown'
        }

        # 安全地获取订单创建信息
        created_attr = getattr(order, 'created', None)
        if created_attr is not None:
            if hasattr(created_attr, 'dst'):
                order_details['created_dst'] = created_attr.dst
            if hasattr(created_attr, 'dtformat'):
                order_details['created_dtformat'] = created_attr.dtformat

        # 根据订单状态进行相应处理和日志记录
        if order.status in [order.Submitted, order.Accepted]:
            # 订单已提交或已接受，记录状态更新
            order_details['status'] = 'Accepted' if order.status == order.Accepted else 'Submitted'
            self.log_event(
                'ORDER_STATUS_UPDATE',
                f"Order {order.ref} {'accepted' if order.status == order.Accepted else 'submitted'}",
                data_feed=order.data,
                order_ref=order.ref,
                trade_cycle_id=trade_cycle_id,
                status=order_details['status']
            )
            return

        # 订单完成 - 无论成功还是失败
        if order.status in [order.Completed]:
            # 订单已完成，记录执行详情
            order_details['status'] = 'Completed'
            exec_details = {
                'price': order.executed.price,
                'size': order.executed.size,
                'value': order.executed.value,
                'comm': order.executed.comm,
            }
            self.log_event(
                'ORDER_STATUS_UPDATE',
                f"Order {order.ref} completed at price {order.executed.price}",
                data_feed=order.data,
                order_ref=order.ref,
                trade_cycle_id=trade_cycle_id,
                status='Completed',
                exec_details=exec_details
            )

        # 订单取消/拒绝/过期 - 错误情况处理
        elif order.status in [order.Canceled, order.Margin, order.Rejected, order.Expired]:
            status_dict = {
                order.Canceled: 'Canceled',
                order.Margin: 'Margin',
                order.Rejected: 'Rejected',
                order.Expired: 'Expired'
            }
            status_name = status_dict.get(order.status, 'Unknown')
            order_details['status'] = status_name

            self.log_event(
                'ORDER_STATUS_UPDATE',
                f"Order {order.ref} {status_name.lower()}",
                data_feed=order.data,
                order_ref=order.ref,
                trade_cycle_id=trade_cycle_id,
                status=status_name,
                reason=getattr(order, 'reject_reason', 'Unknown')
            )

            # 如果不是bracket订单的一部分，可以移除映射
            if not getattr(order, 'parent', None) and not getattr(order, 'transmit', True):
                if order.ref in self.order_ref_to_trade_id_map:
                    del self.order_ref_to_trade_id_map[order.ref]

        # ... existing code ...

    def notify_trade(self, trade):
        # 定义交易通知函数notify_trade，当交易（一买一卖）完成时被调用，参数trade是交易对象。 (定义交易完成通知函数，当一次完整的买卖结束了，程序会跑这个函数来通知你。)
        
        # 查找trade关联的trade_cycle_id
        trade_cycle_id = 'ORPHANED_TRADE'
        # 在Backtrader中，trade对象本身不包含orders属性，但有一个ref属性
        if hasattr(trade, 'ref') and trade.ref in self.order_ref_to_trade_id_map:
            trade_cycle_id = self.order_ref_to_trade_id_map[trade.ref]
        
        if trade.isclosed:
            # 安全地获取开仓和平仓时间
            open_datetime = getattr(trade, 'open_datetime', None)
            close_datetime = getattr(trade, 'close_datetime', None)
            
            # 转换为字符串格式（如果方法存在）
            if callable(open_datetime) and hasattr(trade, 'dtopen') and trade.dtopen:
                open_datetime = open_datetime().isoformat()
            else:
                open_datetime = str(open_datetime) if open_datetime is not None else 'Unknown'
                
            if callable(close_datetime) and hasattr(trade, 'dtclose') and trade.dtclose:
                close_datetime = close_datetime().isoformat()
            else:
                close_datetime = str(
                    close_datetime) if close_datetime is not None else 'Unknown'

            # 交易已平仓，记录交易结果事件
            trade_data = {
                'trade_cycle_id': trade_cycle_id,
                'pnl': trade.pnl,
                'pnlcomm': trade.pnlcomm,
                'commission': trade.commission,
                'size': trade.size,
                'price': trade.price,
                'value': trade.value,
                'tradeid': trade.tradeid,
                'open_datetime': open_datetime,
                'close_datetime': close_datetime,
                'duration_bars': getattr(trade, 'barlen', 0),
                'position_type': 'LONG' if trade.size > 0 else 'SHORT'
            }

            self.log_event(
                'TRADE_CLOSED',
                f"Trade closed: PnL={trade.pnlcomm:.2f}",
                data_feed=trade.data,
                **trade_data
            )

            # 交易结束，清理映射关系
            for order_ref in trade.orders:
                if order_ref in self.order_ref_to_trade_id_map:
                    del self.order_ref_to_trade_id_map[order_ref]

            # 如果当前trade_cycle_id与已结束的交易相同，则重置
            if self.current_trade_id == trade_cycle_id:
                self.current_trade_id = None

    def notify_cashvalue(self, cash, value):
        # 定义现金和总价值通知函数notify_cashvalue，在账户现金或总价值更新时被调用，参数cash是当前现金，value是当前总价值。 (定义现金和总资产值通知函数，当账户里的钱或者总资产变化的时候，程序会跑这个函数来通知你。)
        # --- 日志记录: CASH_VALUE_UPDATE ---
        log_kwargs = {
            "cash": cash,  # 当前现金。 (Current cash.)
            # 当前总价值（现金+持仓市值）。 (Current total value (cash + portfolio value).)
            "value": value,
            # 粗略计算持仓市值。 (Roughly calculate portfolio value.)
            "portfolio_value": value - cash
        }
        # 注意：这里无法直接关联 trade_cycle_id，因为现金/价值更新是全局的
        # Note: Cannot directly associate trade_cycle_id here as cash/value updates are global
        # 记录现金价值更新事件。 (Log cash/value update event.)
        self.log_event(EVENT_TYPES["CASH_VALUE_UPDATE"], **log_kwargs)
        # --- 日志记录结束 ---

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

        # 生成交易周期ID
        trade_id = self.generate_trade_id()

        # 获取当前最新的投资组合价值（现金+仓位）。 (拿到当前账户总价值，包括现金和持有的股票/ETF。)
        portfolio_value = self.broker.getvalue()

        # 计算愿意为这笔交易承担的最大风险金额 (账户价值 * 单笔交易风险比例)
        # Calculate the maximum risk amount willing to take for this trade (Portfolio value * risk per trade percentage)
        risk_amount = portfolio_value * risk_per_trade_percent

        # 计算止损点到入场点的价格差异（风险幅度）
        # Calculate the price difference from stop loss to entry (risk amplitude)
        price_risk = abs(entry_price - stop_loss_price)

        if price_risk == 0:
            # 避免除以零。如果止损价与入场价相同，则无法计算合理的头寸大小，返回0。
            # Avoid division by zero. If stop loss price is the same as entry price, return 0.
            self.log(f"Stop loss price equals entry price. Cannot calculate position size.",
                     level="ERROR", event_type="RISK_ERROR", data=data)

            # 记录交易跳过事件
            self.log_event(
                'TRADE_SKIPPED',
                'Stop loss equals entry price',
                data_feed=data,
                trade_cycle_id=trade_id,
                reason='INVALID_STOP_LOSS',
                details={
                    'entry_price': entry_price,
                    'stop_loss_price': stop_loss_price
                }
            )
            return 0

        # 计算原始头寸大小：愿意承担的风险金额 / 每股价格风险
        # Calculate raw position size: Risk amount / Price risk per share
        position_size_raw = risk_amount / price_risk

        # 将头寸大小转换为股数（向下取整，确保不超风险）
        # Convert position size to number of shares (round down to ensure not exceeding risk)
        position_size_shares = int(position_size_raw / data_close_price)

        # 检查是否有足够的资金
        # Check if there is enough cash
        required_cash = position_size_shares * data_close_price
        available_cash = self.broker.getcash()

        # 如果需要的资金大于可用资金，减少头寸大小
        # If required cash is greater than available cash, reduce position size
        if required_cash > available_cash:
            position_size_shares = int(available_cash / data_close_price)

            if position_size_shares == 0:
                # 记录资金不足事件
                self.log_event(
                    'TRADE_SKIPPED',
                    'Insufficient funds',
                    data_feed=data,
                    trade_cycle_id=trade_id,
                    reason='INSUFFICIENT_FUNDS',
                    details={
                        'available_cash': available_cash,
                        'required_cash': required_cash,
                        'entry_price': entry_price
                    }
                )

        # 记录订单计算事件
        self.log_event(
            'ORDER_CALCULATION',
            f"Position size calculation",
            data_feed=data,
            trade_cycle_id=trade_id,
            entry_price_approx=entry_price,
            stop_loss_calc=stop_loss_price,
            risk_inputs={
                'portfolio_value': portfolio_value,
                'risk_percent': risk_per_trade_percent,
                'risk_amount': risk_amount,
                'price_risk': price_risk
            },
            size_raw=position_size_raw,
            size_final=position_size_shares,
            adjustment_reasons=[] if required_cash <= available_cash else ['INSUFFICIENT_FUNDS']
        )

        return position_size_shares

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

    def generate_trade_id(self):
        """生成新的交易周期ID并保存在实例变量中"""
        import uuid
        self.current_trade_id = uuid.uuid4().hex
        return self.current_trade_id

    def _record_order_trade_id_mapping(self, order):
        """记录订单引用号与交易周期ID的映射关系"""
        if order is None or not hasattr(order, 'ref'):
            return

        if self.current_trade_id is not None:
            self.order_ref_to_trade_id_map[order.ref] = self.current_trade_id
            # 记录订单提交事件
            self.log_event(
                'ORDER_SUBMITTED',
                f"Order submitted: {order.ref}",
                data_feed=self.data,
                order_ref=order.ref,
                trade_cycle_id=self.current_trade_id,
                order_details={
                    'type': order.ordtypename(),
                    'size': order.size,
                    'price': order.price if order.price else 'market',
                    'status': 'Created'
                }
            )

    def log_signal_triggered(self, signal_type, data, indicators=None, **kwargs):
        """
        记录信号触发事件

        Args:
            signal_type: 信号类型 (e.g., 'BREAKOUT_BUY', 'TREND_SELL')
            data: 数据源对象
            indicators: 触发信号的指标值字典
            **kwargs: 其他相关信息
        """
        # 生成新的交易周期ID
        trade_id = self.generate_trade_id()

        # 准备触发数据
        triggering_data = {
            'close': data.close[0],
            'open': data.open[0],
            'high': data.high[0],
            'low': data.low[0],
            'volume': data.volume[0]
        }

        # 添加指标数据
        if indicators:
            triggering_data.update(indicators)

        # 记录事件
        self.log_event(
            'SIGNAL_TRIGGERED',
            f"{signal_type} signal triggered",
            data_feed=data,
            trade_cycle_id=trade_id,
            signal_type=signal_type,
            triggering_data=triggering_data,
            **kwargs
        )

        return trade_id

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
        'fromdate': datetime(2023, 1, 1),
        'todate': datetime(2024, 4, 30),
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
    results = cerebro.run(maxcpus=1)  # 设置为1以禁用多处理，避免pickle错误
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
