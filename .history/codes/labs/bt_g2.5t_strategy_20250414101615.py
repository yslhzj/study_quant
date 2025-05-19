import logging
import json
from datetime import datetime, timezone
import uuid
import os
import pytz
import queue
import threading
from logging.handlers import QueueHandler, QueueListener, RotatingFileHandler

# Define event type constants for clarity and consistency
STRATEGY_INIT = 'STRATEGY_INIT'
MARKET_STATE_ASSESSED = 'MARKET_STATE_ASSESSED'
SIGNAL_TRIGGERED = 'SIGNAL_TRIGGERED'
ORDER_CALCULATION = 'ORDER_CALCULATION'
ORDER_SUBMITTED = 'ORDER_SUBMITTED'
ORDER_STATUS_UPDATE = 'ORDER_STATUS_UPDATE'
SL_TP_TRIGGERED = 'SL_TP_TRIGGERED' # Note: Specific logic for SL/TP trigger detection might need refinement based on how they are implemented (e.g., separate orders, price monitoring)
TRADE_CLOSED = 'TRADE_CLOSED'
RISK_EVENT = 'RISK_EVENT'
TRADE_SKIPPED = 'TRADE_SKIPPED'
STRATEGY_STOP = 'STRATEGY_STOP' # Added for completeness

# Custom JSON Formatter
class JSONFormatter(logging.Formatter):
    """
    Formats log records as JSON Lines.
    """
    def format(self, record):
        # Create a dictionary from the log record's attributes
        log_object = record.msg # Assume record.msg is already a dictionary prepared by log_event
        if not isinstance(log_object, dict):
             # Fallback if msg is not a dict (e.g., internal logging errors)
             log_object = {
                 "timestamp": self.formatTime(record, self.datefmt),
                 "level": record.levelname,
                 "message": record.getMessage()
             }
        try:
            # Convert the dictionary to a JSON string
            return json.dumps(log_object, default=str) # Use default=str for non-serializable types like datetime
        except TypeError as e:
            # Handle potential serialization errors gracefully
            error_log = {
                "timestamp": datetime.now(timezone.utc).isoformat(timespec='microseconds') + 'Z',
                "level": "ERROR",
                "message": f"Failed to serialize log record: {e}",
                "original_record": str(log_object) # Log the problematic record as string
            }
            return json.dumps(error_log)

# --- Existing Backtrader Code ---
import backtrader as bt
import pandas as pd
import numpy as np
import math
import time
from scipy.stats import linregress
from collections import deque, defaultdict

# Ensure UTC timezone object is available
UTC = pytz.utc

class AShareETFStrategy(bt.Strategy):
    # 定义一个名为AShareETFStrategy的类，它继承自bt.Strategy，表示这是一个Backtrader交易策略类。 (创建一个叫做AShareETFStrategy的策略类，它继承了bt.Strategy，说明这是个交易策略。)
    params = (
        ('ema_short_period', 12),                     # 短期EMA周期 (Short-term EMA period)
        ('ema_medium_period', 26),                    # 中期EMA周期 (Medium-term EMA period)
        ('ema_long_period', 52),                      # 长期EMA周期 (Long-term EMA period)
        ('bbands_period', 20),                        # 布林带周期 (Bollinger Bands period)
        ('bbands_devfactor', 2.0),                    # 布林带标准差倍数 (Bollinger Bands deviation factor)
        ('rsi_period', 14),                           # RSI周期 (RSI period)
        ('rsi_overbought', 70),                       # RSI超买阈值 (RSI overbought threshold)
        ('rsi_oversold', 30),                         # RSI超卖阈值 (RSI oversold threshold)
        ('macd_fast_period', 12),                     # MACD快线周期 (MACD fast period)
        ('macd_slow_period', 26),                     # MACD慢线周期 (MACD slow period)
        ('macd_signal_period', 9),                    # MACD信号线周期 (MACD signal period)
        ('atr_period', 14),                           # ATR周期 (ATR period)
        ('stop_loss_atr_multiplier', 2.0),            # 基于ATR的止损倍数 (ATR-based stop loss multiplier)
        ('take_profit_atr_multiplier', 3.0),          # 基于ATR的止盈倍数 (ATR-based take profit multiplier)
        ('risk_per_trade_percent', 0.01),             # 每笔交易风险百分比 (Risk per trade percentage)
        ('max_total_risk_percent', 0.1),              # 最大总风险百分比 (Maximum total risk percentage)
        ('enable_dynamic_risk_adjustment', True),     # 是否启用动态风险调整 (Enable dynamic risk adjustment)
        ('max_drawdown_limit_percent', 0.15),         # 最大回撤限制百分比 (Maximum drawdown limit percentage)
        ('consecutive_losses_limit', 5),              # 连续亏损次数限制 (Consecutive losses limit)
        ('risk_reduction_factor', 0.5),               # 风险降低因子 (Risk reduction factor)
        ('trading_halt_duration_bars', 10),           # 交易暂停持续期（K线数） (Trading halt duration in bars)
        ('order_retry_attempts', 3),                  # 订单重试次数 (Order retry attempts)
        ('order_retry_delay_seconds', 5),             # 订单重试延迟（秒） (Order retry delay in seconds)
        ('enable_logging', True),                     # 是否启用日志记录 (Enable logging)
        ('log_path', 'logs'),                         # 日志文件路径 (Log file path) - FR-LOG-008
        ('log_filename_pattern', '{strategy_name}_{data_name}_{timestamp:%Y%m%d_%H%M%S}_{pid}.jsonl'), # 日志文件名模板 - FR-LOG-009
        ('log_level', 'INFO'),                        # 日志级别 ('INFO', 'DEBUG') - FR-LOG-010
        ('log_async_write', True),                    # 是否异步写入日志 - FR-LOG-011
        ('log_rotation_size_mb', 100),                # 日志轮转大小(MB) - FR-LOG-012 (optional)
        ('log_rotation_backup_count', 5),             # 日志轮转备份数量 - FR-LOG-012 (optional)
    )

    def log(self, txt, dt=None, data=None):
        # Deprecated: Use log_event instead. Kept for potential internal/legacy use if any.
        # Consider removing or refactoring its usages to log_event.
        if self.p.enable_logging:
            # Original logging logic (can be removed or adapted)
            dt = dt or self.datas[0].datetime.date(0)
            data_name = data._name if data else 'Global'
            print(f'{dt.isoformat()} [{data_name}]: {txt}')
            # --- New logging integration ---
            # We should ideally not call the old log AND the new log_event for the same message.
            # This might require refactoring where self.log was previously called.
            # Example adaptation (if needed, but prefer direct log_event calls):
            # log_data = {'message': txt}
            # self.log_event(event_type='LEGACY_LOG', data_feed=data or self.datas[0], **log_data)

    def _setup_logger(self):
        """Sets up the logging system based on strategy parameters."""
        # FR-LOG-013: Use Python logging module
        self.logger = logging.getLogger(f"Strategy_{self.strategy_id}")
        log_level = getattr(logging, self.p.log_level.upper(), logging.INFO)
        self.logger.setLevel(log_level)

        # Prevent adding multiple handlers if re-initialized (e.g., optimization)
        if self.logger.hasHandlers():
            self.logger.handlers.clear()
             # If using QueueListener, ensure it's also stopped/cleared if necessary
            if hasattr(self, '_log_queue_listener'):
                 self._log_queue_listener.stop()
                 delattr(self, '_log_queue')
                 delattr(self, '_log_queue_listener')


        # Ensure log directory exists - FR-LOG-008
        os.makedirs(self.p.log_path, exist_ok=True)

        # Create log filename - FR-LOG-009
        timestamp_str = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        data_name_safe = self.datas[0]._name.replace('*','_').replace(':','_') # Basic sanitization
        log_filename = self.p.log_filename_pattern.format(
            strategy_name=self.__class__.__name__,
            data_name=data_name_safe, # Use the primary data feed name for simplicity
            timestamp=datetime.now(timezone.utc), # Pass datetime object
            pid=os.getpid()
        )
        log_filepath = os.path.join(self.p.log_path, log_filename)

        # FR-LOG-015: Custom JSON Formatter
        formatter = JSONFormatter()

        # FR-LOG-014: Async vs Sync Writing
        if self.p.log_async_write:
            self._log_queue = queue.Queue(-1) # Infinite queue size
            # FR-LOG-012: Optional Rotation for the actual handler
            file_handler = RotatingFileHandler(
                log_filepath,
                maxBytes=self.p.log_rotation_size_mb * 1024 * 1024,
                backupCount=self.p.log_rotation_backup_count,
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            # QueueHandler forwards records to the queue
            queue_handler = QueueHandler(self._log_queue)
            # QueueListener takes records from the queue and sends them to the actual handler
            self._log_queue_listener = QueueListener(self._log_queue, file_handler, respect_handler_level=True)
            self.logger.addHandler(queue_handler)
            self._log_queue_listener.start()
            self._log_handler_to_close = file_handler # Keep ref for closing
        else:
            # Synchronous writing with optional rotation - FR-LOG-012
            handler = RotatingFileHandler(
                 log_filepath,
                 maxBytes=self.p.log_rotation_size_mb * 1024 * 1024,
                 backupCount=self.p.log_rotation_backup_count,
                 encoding='utf-8'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self._log_handler_to_close = handler # Keep ref for closing

    # FR-LOG-001: Unified logging interface
    def log_event(self, event_type: str, data_feed: bt.DataBase = None, **kwargs):
        """
        Logs a structured event to the JSONL file.

        Args:
            event_type (str): The type of the event (e.g., 'SIGNAL_TRIGGERED').
            data_feed (bt.DataBase, optional): The data feed associated with the event.
                                               Defaults to self.datas[0] if None.
            **kwargs: Event-specific key-value data.
        """
        if not self.p.enable_logging or not hasattr(self, 'logger'):
            return

        # FR-LOG-017, FR-LOG-018: Robust error handling
        try:
            data_feed = data_feed or self.datas[0] # Default to main data feed

            # FR-LOG-002: Standard Fields
            log_entry = {
                # Force UTC time, ISO 8601 format with microseconds and 'Z'
                "timestamp": datetime.now(timezone.utc).isoformat(timespec='microseconds') + 'Z',
                "event_type": event_type,
                "strategy_id": self.strategy_id,
                "data_id": data_feed._name if data_feed else 'N/A',
                # FR-ID-002: Include trade_cycle_id if available
                "trade_cycle_id": getattr(self, 'current_trade_id', None)
            }

            # FR-ID-003 / FR-ID-004: Special handling for order/trade events to ensure trade_cycle_id mapping
            if event_type in [ORDER_STATUS_UPDATE, SL_TP_TRIGGERED]: # SL/TP might be order updates
                order_ref = kwargs.get('order_ref') # Expect order_ref in kwargs
                if order_ref:
                     # Retrieve trade_id using the map, provide default if not found
                     trade_id = self.order_ref_to_trade_id_map.get(order_ref, 'ORPHANED_ORDER_EVENT')
                     log_entry['trade_cycle_id'] = trade_id
                     log_entry['order_ref'] = order_ref # Ensure order_ref is logged

            elif event_type == TRADE_CLOSED:
                trade_orders_refs = kwargs.get('trade_orders_refs') # Expect list of order refs in kwargs
                trade_id = 'ORPHANED_TRADE_EVENT' # Default
                if trade_orders_refs:
                     log_entry['trade_orders_refs'] = trade_orders_refs # Log refs for debugging
                     for ref in trade_orders_refs:
                         found_id = self.order_ref_to_trade_id_map.get(ref)
                         if found_id:
                             trade_id = found_id
                             break # Found the ID, stop searching
                log_entry['trade_cycle_id'] = trade_id


            # FR-LOG-003: Merge standard fields and specific event data
            log_entry.update(kwargs)

            # Log the structured dictionary directly
            self.logger.info(log_entry) # logger expects the message here

        except Exception as e:
            # FR-LOG-019: Log internal errors to stderr
            print(f"{datetime.now(timezone.utc).isoformat()} [LogSystemError]: Failed to log event - {e}")
            # Optionally log to a dedicated error file
            # with open("log_system_error.log", "a") as f_err:
            #     f_err.write(f"{datetime.now(timezone.utc).isoformat()} - {e}\n")


    def __init__(self, **kwargs):  # 接受 **kwargs 以兼容 addstrategy 传递的参数
        # 定义策略的初始化函数__init__，在策略对象创建时自动执行。
        # (Define the initialization function __init__, executed automatically when the strategy object is created.)
        # (Accept **kwargs to be compatible with parameters passed by addstrategy)
        # 引用数据源。
        # Reference the data feeds.
        self.data_close = self.datas[0].close   # 收盘价 (Closing price)
        self.data_open = self.datas[0].open     # 开盘价 (Opening price)
        self.data_high = self.datas[0].high     # 最高价 (Highest price)
        self.data_low = self.datas[0].low       # 最低价 (Lowest price)
        self.data_volume = self.datas[0].volume # 成交量 (Volume)

        # --- Logging System Setup ---
        self.strategy_id = f"{self.__class__.__name__}_{uuid.uuid4().hex[:8]}" # Unique ID for this strategy instance
        if self.p.enable_logging:
            self._setup_logger()
        # --------------------------

        # 初始化指标。
        # Initialize indicators.
        self.ema_short = bt.indicators.ExponentialMovingAverage(self.datas[0], period=self.p.ema_short_period)
        # 计算短期指数移动平均线（EMA）。 (Calculate the short-term Exponential Moving Average (EMA).)
        self.ema_medium = bt.indicators.ExponentialMovingAverage(self.datas[0], period=self.p.ema_medium_period)
        # 计算中期指数移动平均线（EMA）。 (Calculate the medium-term Exponential Moving Average (EMA).)
        self.ema_long = bt.indicators.ExponentialMovingAverage(self.datas[0], period=self.p.ema_long_period)
        # 计算长期指数移动平均线（EMA）。 (Calculate the long-term Exponential Moving Average (EMA).)
        self.bbands = bt.indicators.BollingerBands(self.datas[0], period=self.p.bbands_period, devfactor=self.p.bbands_devfactor)
        # 计算布林带指标，包括中轨、上轨和下轨。 (Calculate the Bollinger Bands indicator, including middle, upper, and lower bands.)
        self.rsi = bt.indicators.RelativeStrengthIndex(self.datas[0], period=self.p.rsi_period)
        # 计算相对强弱指数（RSI）。 (Calculate the Relative Strength Index (RSI).)
        self.macd = bt.indicators.MACD(self.datas[0], period_me1=self.p.macd_fast_period, period_me2=self.p.macd_slow_period, period_signal=self.p.macd_signal_period)
        # 计算移动平均收敛散度（MACD）指标，包括MACD线、信号线和柱状图。 (Calculate the Moving Average Convergence Divergence (MACD) indicator, including MACD line, signal line, and histogram.)
        self.atr = bt.indicators.AverageTrueRange(self.datas[0], period=self.p.atr_period)
        # 计算平均真实波幅（ATR）。 (Calculate the Average True Range (ATR).)

        # 初始化风险管理变量。
        # Initialize risk management variables.
        self.current_risk_multiplier = 1.0  # 当前风险乘数 (Current risk multiplier)
        self.high_water_mark = self.broker.getvalue()  # 最高水位线 (High water mark)
        self.consecutive_losses = 0  # 连续亏损次数 (Consecutive losses count)
        self.trading_halted_until_bar = 0  # 交易暂停至第几根K线 (Trading halted until bar number)
        self.order_retry_counts = defaultdict(int) # 订单重试计数器 (Order retry counter)

        # 用于跟踪订单和交易。
        # For tracking orders and trades.
        self.active_orders = {}  # 活跃订单字典 (Active orders dictionary)
        self.current_trade_id = None # 当前交易周期的唯一ID (Unique ID for the current trade cycle) - FR-ID-001
        self.order_ref_to_trade_id_map = {} # 订单引用到交易周期ID的映射 (Mapping from order reference to trade cycle ID) - FR-ID-003

        # --- Log Strategy Initialization ---
        # FR-LOG-002, event_type: STRATEGY_INIT
        init_log_data = {
             "strategy_name": self.__class__.__name__,
             "params": self.p._getkwargs(), # Get all parameters
             "data_ids": [d._name for d in self.datas]
        }
        self.log_event(event_type=STRATEGY_INIT, **init_log_data)
        # ---------------------------------


    def notify_order(self, order):
        # 定义订单状态通知函数notify_order，当订单状态发生变化时被调用，参数order是订单对象。 (定义订单通知函数，当订单状态变化的时候，程序会跑这个函数来通知你。)

        # --- Log Order Status Update ---
        # FR-LOG-002, FR-ID-004, event_type: ORDER_STATUS_UPDATE
        order_log_data = {
             "order_ref": order.ref, # FR-ID-004: Log order.ref
             "status": order.getstatusname(),
             "order_details": { # Include key details for context
                 "type": order.getordername(),
                 "ordtype": order.ordtypename(),
                 "size": order.size,
                 "price": order.price,
                 "created_price": order.created.price,
                 "executed_price": order.executed.price,
                 "executed_size": order.executed.size,
                 "executed_value": order.executed.value,
                 "executed_comm": order.executed.comm,
                 "remaining": order.executed.remsize,
             }
        }
        # exec_details can be added if needed based on specific broker implementations or properties
        if order.executed.remsize is not None:
             order_log_data["remaining_size"] = order.executed.remsize
        if order.executed.price:
             order_log_data["exec_details"] = {"avg_price": order.executed.price} # Example

        # FR-ID-003: Retrieve trade_cycle_id using the map (will be added by log_event)
        self.log_event(event_type=ORDER_STATUS_UPDATE, data_feed=order.data, **order_log_data)
        # ---------------------------------


        order_ref = order.ref
        # 如果订单状态是已提交或已接受，则记录订单信息并添加到活跃订单字典。
        # (If the order status is Submitted or Accepted, record the order info and add it to the active orders dictionary.)
        if order.status in [order.Submitted, order.Accepted]:
            # self.log(f'订单 {order.ref} 已提交/已接受', data=order.data)
            self.active_orders[order_ref] = order
            return

        # 如果订单状态是已完成，则记录订单完成信息。
        # (If the order status is Completed, record the order completion info.)
        if order.status == order.Completed:
            # self.log(f'订单 {order.ref} 已完成: 类型 {order.ordtypename()}, 执行类型 {order.getordername()}, 价格 {order.executed.price:.2f}, 数量 {order.executed.size}', data=order.data)
            pass # Logging handled by log_event above

        # 如果订单状态是已取消、保证金不足或被拒绝，则记录相应信息。
        # (If the order status is Canceled, Margin, or Rejected, record the corresponding info.)
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
             # self.log(f'订单 {order.ref} {order.getstatusname()}', data=order.data)
             # Handle rejected orders potentially for retry logic
             if order.status == order.Rejected and order_ref in self.order_retry_counts:
                 # self.log(f'订单 {order.ref} 被拒绝，尝试重试...', data=order.data)
                 # Implement retry logic here if needed, using self.order_retry_counts[order_ref]
                 pass
             pass # Logging handled by log_event above

         # 如果订单状态是已过期，则记录订单过期信息。
         # (If the order status is Expired, record the order expiration info.)
        elif order.status == order.Expired:
             # self.log(f'订单 {order.ref} 已过期', data=order.data)
             pass # Logging handled by log_event above

        # 从活跃订单字典中移除已处理的订单。
        # (Remove the processed order from the active orders dictionary.)
        if order_ref in self.active_orders:
            del self.active_orders[order_ref]
        if order_ref in self.order_retry_counts: # Clean retry count as well
             del self.order_retry_counts[order_ref]

        # FR-ID-003: Optional Secondary Cleanup Point (Use with caution, primary is notify_trade)
        # if order.status in [order.Completed, order.Canceled, order.Margin, order.Rejected, order.Expired]:
        #     # Avoid removing if part of a bracket that isn't fully closed yet.
        #     # This check is complex and might be better handled solely in notify_trade.
        #     is_bracket_component = False # Simplified check, needs proper implementation if used
        #     # Example check (might be insufficient):
        #     # if self.order_ref_to_trade_id_map.get(order_ref):
        #     #     trade_id = self.order_ref_to_trade_id_map[order_ref]
        #     #     # Check if other orders with the same trade_id are still active (complex)
        #
        #     if not is_bracket_component and order.ref in self.order_ref_to_trade_id_map:
        #          # self.log(f'DEBUG: Removing order ref {order.ref} from map in notify_order (Status: {order.getstatusname()})')
        #          # del self.order_ref_to_trade_id_map[order.ref]
        #          pass # Decided to primarily clean in notify_trade for simplicity and robustness

    def notify_trade(self, trade):
        # 定义交易通知函数notify_trade，当交易（一买一卖）完成时被调用，参数trade是交易对象。 (定义交易完成通知函数，当一次完整的买卖结束了，程序会跑这个函数来通知你。)

        # --- Log Trade Closed Event ---
        # FR-LOG-002, event_type: TRADE_CLOSED
        if trade.isclosed:
            trade_log_data = {
                 # FR-ID-003: Pass order refs for lookup in log_event
                 "trade_orders_refs": [o.ref for o in trade.orders],
                 "pnl": trade.pnl,
                 "pnlcomm": trade.pnlcomm,
                 "size": trade.size, # Size of the closed trade part
                 "price": trade.price, # Avg price of the trade
                 "value": trade.value, # Value of the trade
                 "commission": trade.commission, # Total commission
                 "duration_bars": trade.barlen,
                 "open_datetime": trade.open_datetime().isoformat() if trade.dtopen else None,
                 "close_datetime": trade.close_datetime().isoformat() if trade.dtclose else None,
                 "position_type": 'Long' if trade.long else 'Short' # Requires trade.long attribute if available
            }
            self.log_event(event_type=TRADE_CLOSED, data_feed=trade.data, **trade_log_data)

            # FR-ID-003: Primary Cleanup Point for order_ref_to_trade_id_map
            cleaned_refs = []
            for order in trade.orders:
                if order.ref in self.order_ref_to_trade_id_map:
                    del self.order_ref_to_trade_id_map[order.ref]
                    cleaned_refs.append(order.ref)
            # if cleaned_refs:
                # self.log(f'DEBUG: Cleaned refs {cleaned_refs} from map for closed trade {trade.ref} (Trade Cycle ID was likely {trade_log_data["trade_cycle_id"]})')

            # Reset current_trade_id if this closed the cycle managed by it.
            # Need robust check if multiple cycles are allowed. Assuming one main cycle for now.
            # Check if ANY order ref from the map still exists (belonging to *other* trades)
            # A simple check might be if the map is now empty or if the closed trade's ID is no longer referenced.
            # For simplicity: Reset if the map becomes empty or if the specific trade_id is gone.
            # This needs careful design for concurrent trades. Assuming simple case:
            # Let's reset self.current_trade_id ONLY IF the map becomes empty after cleaning.
            # A better approach might be needed for complex scenarios.
            # tentative_trade_id_closed = trade_log_data.get("trade_cycle_id", "UNKNOWN_ID")
            # if tentative_trade_id_closed == self.current_trade_id:
            #     # Check if any *other* order associated with this trade_id still exists in the map
            #     is_cycle_completely_closed = True
            #     for ref, tid in self.order_ref_to_trade_id_map.items():
            #          if tid == tentative_trade_id_closed:
            #              is_cycle_completely_closed = False
            #              break
            #     if is_cycle_completely_closed:
            #         # self.log(f"DEBUG: Resetting current_trade_id as trade cycle {self.current_trade_id} seems closed.")
            #         self.current_trade_id = None
            # Simplest approach: Reset if the ID associated with *this* closed trade is the current one.
            if trade_log_data.get("trade_cycle_id") == self.current_trade_id:
                 self.current_trade_id = None
        # --------------------------


        # 如果交易未完成，则返回。
        # (If the trade is not closed, return.)
        if not trade.isclosed:
            # Log partial close or opening if needed (e.g., TRADE_UPDATE event type)
            # self.log_event(event_type='TRADE_UPDATE', ...)
            return

        # self.log(f'交易 PNL: 毛利 {trade.pnl:.2f}, 净利 {trade.pnlcomm:.2f}', data=trade.data)
        # (Log trade PNL: Gross PNL {trade.pnl:.2f}, Net PNL {trade.pnlcomm:.2f})

        # 检查并更新回撤和连续亏损。
        # (Check and update drawdown and consecutive losses.)
        self._update_risk_metrics(trade.pnlcomm)


    def notify_cashvalue(self, cash, value):
        # 定义现金和总价值通知函数notify_cashvalue，在账户现金或总价值更新时被调用，参数cash是当前现金，value是当前总价值。 (定义现金和总资产值通知函数，当账户里的钱或者总资产变化的时候，程序会跑这个函数来通知你。)
        # self.log(f'现金: {cash:.2f}, 总价值: {value:.2f}', dt=self.datas[0].datetime.date(0))
        # (Log cash: {cash:.2f}, Total value: {value:.2f})

        # FR-LOG-002, event_type: RISK_EVENT (Drawdown Check Example)
        current_drawdown = (self.high_water_mark - value) / self.high_water_mark if self.high_water_mark > 0 else 0
        if self.p.enable_dynamic_risk_adjustment and current_drawdown > self.p.max_drawdown_limit_percent:
             if self.trading_halted_until_bar <= len(self): # Avoid logging every bar during halt
                 risk_log_data = {
                     "event_subtype": "DRAWDOWN_LIMIT_EXCEEDED",
                     "account_value": value,
                     "cash": cash,
                     "drawdown_pct": current_drawdown,
                     "high_water_mark": self.high_water_mark,
                     "limit_pct": self.p.max_drawdown_limit_percent,
                     "action_taken": "HALT_TRADING"
                 }
                 self.log_event(event_type=RISK_EVENT, **risk_log_data)
                 # self.log(f'触发最大回撤限制，暂停交易 {self.p.trading_halt_duration_bars} 根K线', dt=self.datas[0].datetime.date(0))
                 self.trading_halted_until_bar = len(self) + self.p.trading_halt_duration_bars
                 # Optionally cancel all open orders
                 # for order_ref in list(self.active_orders.keys()):
                 #     self.cancel(self.active_orders[order_ref])

        # 更新最高水位线。
        # (Update high water mark.)
        self.high_water_mark = max(self.high_water_mark, value)


    def _update_risk_metrics(self, pnlcomm):
        # 定义一个私有方法_update_risk_metrics，用于更新风险相关的指标，如连续亏损次数。 (Define a private method _update_risk_metrics to update risk-related metrics like consecutive losses.)
        """Updates consecutive losses and adjusts risk multiplier."""
        if pnlcomm < 0:
            self.consecutive_losses += 1
            # self.log(f'连续亏损次数: {self.consecutive_losses}', dt=self.datas[0].datetime.date(0))
        else:
             if self.consecutive_losses > 0:
                 # self.log(f'连续亏损结束，次数: {self.consecutive_losses}', dt=self.datas[0].datetime.date(0))
                 pass
             self.consecutive_losses = 0
             # Optionally reset risk multiplier if it was reduced
             # if self.current_risk_multiplier < 1.0:
                 # self.current_risk_multiplier = 1.0
                 # self.log(f'盈利，风险乘数恢复为 {self.current_risk_multiplier:.2f}')


        # 如果启用了动态风险调整且达到连续亏损限制，则调整风险乘数。
        # (If dynamic risk adjustment is enabled and consecutive loss limit is reached, adjust the risk multiplier.)
        if self.p.enable_dynamic_risk_adjustment and self.consecutive_losses >= self.p.consecutive_losses_limit:
             old_multiplier = self.current_risk_multiplier
             self.current_risk_multiplier *= self.p.risk_reduction_factor
             # FR-LOG-002, event_type: RISK_EVENT
             risk_log_data = {
                 "event_subtype": "CONSECUTIVE_LOSS_LIMIT",
                 "consecutive_losses": self.consecutive_losses,
                 "limit": self.p.consecutive_losses_limit,
                 "old_risk_multiplier": old_multiplier,
                 "new_risk_multiplier": self.current_risk_multiplier,
                 "reduction_factor": self.p.risk_reduction_factor,
                 "action_taken": "REDUCE_RISK"
             }
             self.log_event(event_type=RISK_EVENT, **risk_log_data)
             # self.log(f'达到连续亏损限制，风险乘数降至 {self.current_risk_multiplier:.2f}', dt=self.datas[0].datetime.date(0))


    def _calculate_trade_size(self, data_close_price, entry_price, stop_loss_price, risk_per_trade_percent, data=None):
        # 定义一个私有方法_calculate_trade_size，用于计算交易仓位大小，根据风险管理规则。 (Define a private method _calculate_trade_size to calculate trade position size based on risk management rules.)
        """
        Calculates the trade size based on risk parameters, ATR stop loss, and account value.
        Returns the calculated size (positive integer) or 0 if constraints are violated.
        """
        data = data or self.datas[0]
        account_value = self.broker.getvalue()
        risk_amount_per_trade = account_value * risk_per_trade_percent * self.current_risk_multiplier
        price_risk_per_share = abs(entry_price - stop_loss_price)

        # --- Log Order Calculation Inputs ---
        calc_log_data = {
            "signal_type": "Unknown", # This should be passed or determined based on context
            "entry_price_approx": entry_price,
            "stop_loss_calc": stop_loss_price,
            "take_profit_calc": None, # Calculate TP if applicable here or elsewhere
            "risk_inputs": {
                "account_value": account_value,
                "risk_per_trade_percent": risk_per_trade_percent,
                "current_risk_multiplier": self.current_risk_multiplier,
                "price_risk_per_share": price_risk_per_share,
                "risk_amount_per_trade": risk_amount_per_trade,
             },
             "adjustment_reasons": []
        }
        # ---------------------------------


        if price_risk_per_share <= 0:
            calc_log_data["size_raw"] = 0
            calc_log_data["size_final"] = 0
            calc_log_data["adjustment_reasons"].append("Zero or negative price risk per share")
            self.log_event(event_type=ORDER_CALCULATION, data_feed=data, **calc_log_data)
            return 0  # Avoid division by zero or invalid risk

        # Calculate raw size based on risk amount and price risk
        size_raw = math.floor(risk_amount_per_trade / price_risk_per_share)
        calc_log_data["size_raw"] = size_raw

        if size_raw <= 0:
            calc_log_data["size_final"] = 0
            calc_log_data["adjustment_reasons"].append("Calculated raw size is non-positive")
            self.log_event(event_type=ORDER_CALCULATION, data_feed=data, **calc_log_data)
            return 0

        # Get commission info for the data feed
        comminfo = self.broker.getcommissioninfo(data)

        # Check margin requirements (simplified example)
        required_margin = comminfo.getmargin(entry_price) * size_raw # Simplified margin calc
        available_cash = self.broker.getcash()

        # Check total portfolio risk constraint
        current_total_risk = 0
        # TODO: Calculate current total risk based on open positions and their stop losses
        # This requires iterating through open positions and their associated stop orders or calculated stops.
        # Example placeholder:
        # for pos_data, position in self.broker.positions.items():
        #     if position.size != 0:
        #         # Find corresponding stop loss price for this position (complex part)
        #         pos_stop_loss = ... # Get stop loss for this position
        #         pos_entry_price = position.price
        #         pos_size = position.size
        #         current_total_risk += abs(pos_entry_price - pos_stop_loss) * abs(pos_size)

        max_allowed_total_risk = account_value * self.p.max_total_risk_percent
        potential_new_total_risk = current_total_risk + risk_amount_per_trade

        size_final = size_raw
        # Apply constraints
        if potential_new_total_risk > max_allowed_total_risk:
             calc_log_data["adjustment_reasons"].append("Maximum total portfolio risk exceeded")
             size_final = 0 # Or adjust size downwards, more complex

        # Add more checks like available cash vs required value + commission if needed
        required_value = size_final * entry_price
        estimated_commission = comminfo.getcommission(size_final, entry_price)
        if available_cash < required_value + estimated_commission: # Simple check
            calc_log_data["adjustment_reasons"].append("Insufficient cash for calculated size + commission")
            size_final = 0 # Or adjust size based on cash


        # Apply any broker/exchange minimum size constraints if necessary
        # min_size = comminfo.getsize() ... # Check comminfo structure

        # Log the final calculation details
        calc_log_data["size_final"] = size_final
        # Retrieve the trade_cycle_id generated just before calling this function
        calc_log_data["trade_cycle_id"] = getattr(self, 'current_trade_id', None)
        self.log_event(event_type=ORDER_CALCULATION, data_feed=data, **calc_log_data)


        return size_final


    def _place_order(self, data, order_type, size, price=None, exectype=None, **kwargs):
        # 定义一个私有方法_place_order，用于根据计算出的仓位大小实际下单。 (Define a private method _place_order to actually place an order based on the calculated position size.)
        """Places the order and handles retries for rejections."""
        # FR-ID-001: Ensure trade_cycle_id is generated *before* calling this if it's a new trade.
        # It should be in self.current_trade_id when this is called for a new trade.
        trade_cycle_id = getattr(self, 'current_trade_id', None) # Get the current ID

        if size <= 0:
             # self.log(f"尝试下单大小为零或负数: {size}, 跳过下单。", data=data)
             skip_log_data = {
                  "reason": "Calculated size is zero or negative",
                  "calculated_size": size,
                  "trade_cycle_id": trade_cycle_id # Log the ID even if skipped
             }
             self.log_event(TRADE_SKIPPED, data_feed=data, **skip_log_data)
             return None

        # Determine order function (buy or sell)
        order_func = self.buy if order_type == 'buy' else self.sell

        # Prepare order arguments
        order_args = {
            'data': data,
            'size': size,
            'price': price,
            'exectype': exectype,
            'tradeid': 0 # Or manage tradeid if needed
            # Pass other relevant kwargs like valid, oco, parent etc. if used
        }
        order_args.update(kwargs) # Add any extra arguments like stop_loss etc. if needed by broker

        try:
            order = order_func(**order_args)
            if order:
                # self.log(f"订单 {order.ref} 已创建: 类型 {order.ordtypename()}, 执行类型 {order.getordername()}, 价格 {order.created.price if order.created.price else 'Market'}, 数量 {order.created.size}", data=data)
                self.active_orders[order.ref] = order
                self.order_retry_counts[order.ref] = 0 # Initialize retry count

                # FR-ID-003: Map order ref to trade cycle ID
                if trade_cycle_id:
                    self.order_ref_to_trade_id_map[order.ref] = trade_cycle_id
                    # Handle bracket orders - they return a list
                    if isinstance(order, list): # Check if buy_bracket/sell_bracket was used indirectly
                         for sub_order in order:
                             if sub_order and sub_order.ref:
                                 self.order_ref_to_trade_id_map[sub_order.ref] = trade_cycle_id
                    elif order.ref: # Standard order
                        self.order_ref_to_trade_id_map[order.ref] = trade_cycle_id

                # --- Log Order Submission ---
                # FR-LOG-002, FR-ID-004, event_type: ORDER_SUBMITTED
                submit_log_data = {
                     "order_ref": order.ref if not isinstance(order, list) else [o.ref for o in order if o], # FR-ID-004
                     "trade_cycle_id": trade_cycle_id, # FR-ID-002
                     "order_details": { # Capture creation details
                         "type": order.getordername() if not isinstance(order, list) else 'Bracket',
                         "ordtype": order.ordtypename() if not isinstance(order, list) else ('BuyBracket' if order_type=='buy' else 'SellBracket'),
                         "size": order.created.size if not isinstance(order, list) else order[0].created.size if order and order[0] else 0,
                         "price": order.created.price if not isinstance(order, list) else order[0].created.price if order and order[0] else None,
                         "pricelimit": order.created.pricelimit if not isinstance(order, list) else order[0].created.pricelimit if order and order[0] else None,
                         "exectype": order.getordername() if not isinstance(order, list) else order[0].getordername() if order and order[0] else None,
                         "valid": order.valid, # Log validity if set
                         "tradeid": order.tradeid,
                         # Add other relevant creation params from order_args if needed
                     }
                }
                self.log_event(event_type=ORDER_SUBMITTED, data_feed=data, **submit_log_data)
                # --------------------------

                return order
            else:
                 # self.log(f"创建订单失败: 类型 {order_type}, 数量 {size}, 价格 {price}", data=data)
                 skip_log_data = {
                     "reason": "Order creation function returned None",
                     "order_type": order_type, "size": size, "price": price,
                     "trade_cycle_id": trade_cycle_id
                 }
                 self.log_event(TRADE_SKIPPED, data_feed=data, **skip_log_data)
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
