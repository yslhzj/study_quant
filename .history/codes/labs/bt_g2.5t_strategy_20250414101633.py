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
                 return None
        except Exception as e:
            # self.log(f"下单时发生错误: {e}", data=data)
            # Log the error appropriately
            error_log_data = {
                 "reason": f"Exception during order placement: {e}",
                 "order_type": order_type, "size": size, "price": price,
                 "trade_cycle_id": trade_cycle_id
            }
            self.log_event(TRADE_SKIPPED, data_feed=data, **error_log_data)
            return None


    def next(self):
        # 定义next函数，在每个数据点（通常是每个交易日）都会被调用一次，用于执行策略的主要逻辑。 (定义next函数，这是策略的核心，每天开盘后都要运行一遍，决定今天该干啥。)
        # 检查是否暂停交易
        # Check if trading is halted
        if self.trading_halted_until_bar > len(self):
            # self.log(f'交易暂停中，剩余 {self.trading_halted_until_bar - len(self)} 根K线', dt=self.datas[0].datetime.date(0))
            return

        # 检查是否有持仓。
        # Check if there is an open position.
        position_size = self.getposition(self.datas[0]).size

        # 获取当前ATR值用于止损止盈。
        # Get current ATR value for stop loss and take profit.
        current_atr = self.atr[0]
        stop_loss_price = 0
        take_profit_price = 0

        # --- Log Market State Assessment ---
        # Example: Determine trend based on EMAs
        market_trend = 'NEUTRAL'
        if self.ema_short[0] > self.ema_medium[0] > self.ema_long[0]:
             market_trend = 'STRONG_UPTREND'
        elif self.ema_short[0] < self.ema_medium[0] < self.ema_long[0]:
             market_trend = 'STRONG_DOWNTREND'
        elif self.ema_short[0] > self.ema_long[0]:
             market_trend = 'UPTREND'
        elif self.ema_short[0] < self.ema_long[0]:
             market_trend = 'DOWNTREND'

        market_log_data = {
            "market_state": market_trend,
            "indicators": {
                "ema_short": self.ema_short[0],
                "ema_medium": self.ema_medium[0],
                "ema_long": self.ema_long[0],
                "rsi": self.rsi[0],
                "macd": self.macd.macd[0],
                "signal": self.macd.signal[0],
                "bb_mid": self.bbands.mid[0],
                "bb_top": self.bbands.top[0],
                "bb_bot": self.bbands.bot[0],
                "atr": current_atr,
                "close": self.data_close[0]
            }
        }
        self.log_event(MARKET_STATE_ASSESSED, data_feed=self.datas[0], **market_log_data)
        # -----------------------------------

        # 如果有持仓，则检查止损或止盈条件。
        # (If there is an open position, check for stop loss or take profit conditions.)
        if position_size != 0:
            entry_price = self.getposition(self.datas[0]).price
            if position_size > 0:  # Long position
                stop_loss_price = entry_price - current_atr * self.p.stop_loss_atr_multiplier
                take_profit_price = entry_price + current_atr * self.p.take_profit_atr_multiplier

                # Check for SL/TP Trigger (Simplified Example - assumes market order close)
                # Real implementation might involve checking stop/limit orders in notify_order
                if self.data_low[0] <= stop_loss_price:
                     sl_tp_log_data = {
                         "trigger_type": "STOP_LOSS",
                         "current_price": self.data_low[0], # Price that triggered it
                         "trigger_level": stop_loss_price,
                         "position_size": position_size,
                         "order_ref": None # Need to associate with the closing order ref if possible
                     }
                     # Retrieve trade_cycle_id from map based on how position was opened
                     # This requires knowing which order(s) opened the current position.
                     # For simplicity, log_event will use self.current_trade_id if still set,
                     # otherwise, requires lookup based on position details (more complex).
                     self.log_event(SL_TP_TRIGGERED, data_feed=self.datas[0], **sl_tp_log_data)
                     # self.log(f'多头止损触发: 价格 {self.data_low[0]:.2f} <= 止损位 {stop_loss_price:.2f}', data=self.datas[0])
                     self.close(data=self.datas[0]) # Close position
                elif self.data_high[0] >= take_profit_price:
                     sl_tp_log_data = {
                         "trigger_type": "TAKE_PROFIT",
                         "current_price": self.data_high[0],
                         "trigger_level": take_profit_price,
                         "position_size": position_size,
                         "order_ref": None
                     }
                     self.log_event(SL_TP_TRIGGERED, data_feed=self.datas[0], **sl_tp_log_data)
                     # self.log(f'多头止盈触发: 价格 {self.data_high[0]:.2f} >= 止盈位 {take_profit_price:.2f}', data=self.datas[0])
                     self.close(data=self.datas[0]) # Close position

            else:  # Short position
                stop_loss_price = entry_price + current_atr * self.p.stop_loss_atr_multiplier
                take_profit_price = entry_price - current_atr * self.p.take_profit_atr_multiplier

                if self.data_high[0] >= stop_loss_price:
                     sl_tp_log_data = {
                         "trigger_type": "STOP_LOSS",
                         "current_price": self.data_high[0],
                         "trigger_level": stop_loss_price,
                         "position_size": position_size,
                         "order_ref": None
                     }
                     self.log_event(SL_TP_TRIGGERED, data_feed=self.datas[0], **sl_tp_log_data)
                     # self.log(f'空头止损触发: 价格 {self.data_high[0]:.2f} >= 止损位 {stop_loss_price:.2f}', data=self.datas[0])
                     self.close(data=self.datas[0]) # Close position
                elif self.data_low[0] <= take_profit_price:
                     sl_tp_log_data = {
                         "trigger_type": "TAKE_PROFIT",
                         "current_price": self.data_low[0],
                         "trigger_level": take_profit_price,
                         "position_size": position_size,
                         "order_ref": None
                     }
                     self.log_event(SL_TP_TRIGGERED, data_feed=self.datas[0], **sl_tp_log_data)
                     # self.log(f'空头止盈触发: 价格 {self.data_low[0]:.2f} <= 止盈位 {take_profit_price:.2f}', data=self.datas[0])
                     self.close(data=self.datas[0]) # Close position

        # 如果没有持仓，则检查入场信号。
        # (If there is no open position, check for entry signals.)
        else:
            # 定义多头入场条件。
            # (Define long entry conditions.)
            long_condition_ema = self.ema_short[0] > self.ema_medium[0] > self.ema_long[0]
            long_condition_rsi = self.rsi[0] > 50 # Example: RSI above 50 indicates potential strength
            long_condition_macd = self.macd.macd[0] > self.macd.signal[0] and self.macd.macd[-1] <= self.macd.signal[-1] # MACD crossover
            long_condition_bbands = self.data_close[0] > self.bbands.mid[0] # Price above middle band

            is_long_signal = long_condition_ema and long_condition_rsi and long_condition_macd and long_condition_bbands

            # 定义空头入场条件。
            # (Define short entry conditions.)
            short_condition_ema = self.ema_short[0] < self.ema_medium[0] < self.ema_long[0]
            short_condition_rsi = self.rsi[0] < 50 # Example: RSI below 50 indicates potential weakness
            short_condition_macd = self.macd.macd[0] < self.macd.signal[0] and self.macd.macd[-1] >= self.macd.signal[-1] # MACD crossover
            short_condition_bbands = self.data_close[0] < self.bbands.mid[0] # Price below middle band

            is_short_signal = short_condition_ema and short_condition_rsi and short_condition_macd and short_condition_bbands

            if is_long_signal:
                # self.log('多头入场信号触发', data=self.datas[0])
                # (Log long entry signal triggered)

                # --- Generate Trade Cycle ID --- FR-ID-001
                self.current_trade_id = uuid.uuid4().hex
                # -------------------------------

                # --- Log Signal Triggered ---
                signal_log_data = {
                    "trade_cycle_id": self.current_trade_id, # Newly generated ID
                    "signal_type": "LONG_ENTRY",
                    "triggering_data": { # Capture state at signal time
                        "close": self.data_close[0],
                        "ema_short": self.ema_short[0], "ema_medium": self.ema_medium[0], "ema_long": self.ema_long[0],
                        "rsi": self.rsi[0],
                        "macd": self.macd.macd[0], "macd_signal": self.macd.signal[0],
                        "bb_mid": self.bbands.mid[0],
                        "conditions": { # Optionally log specific conditions met
                            "ema": long_condition_ema,
                            "rsi": long_condition_rsi,
                            "macd": long_condition_macd,
                            "bbands": long_condition_bbands
                        }
                    }
                }
                # Pass the trade_cycle_id directly as it's just generated
                self.log_event(SIGNAL_TRIGGERED, data_feed=self.datas[0], **signal_log_data)
                # ----------------------------


                entry_price = self.data_close[0]  # Use closing price for calculation/entry
                stop_loss_price = entry_price - current_atr * self.p.stop_loss_atr_multiplier

                # Calculate trade size *before* placing order
                # Pass signal type to calculation log
                size = self._calculate_trade_size(self.data_close[0], entry_price, stop_loss_price, self.p.risk_per_trade_percent, data=self.datas[0])
                # ORDER_CALCULATION log is done inside _calculate_trade_size

                if size > 0:
                    # Place the order
                    self._place_order(data=self.datas[0], order_type='buy', size=size, exectype=bt.Order.Market)
                    # ORDER_SUBMITTED log is done inside _place_order
                else:
                     # Log skip reason (already logged in _calculate_trade_size or _place_order)
                     # self.log(f"计算出的多头仓位大小为零或负数 ({size}), 跳过下单", data=self.datas[0])
                     self.current_trade_id = None # Reset ID if trade is skipped immediately after signal

            elif is_short_signal:
                # self.log('空头入场信号触发', data=self.datas[0])
                # (Log short entry signal triggered)

                 # --- Generate Trade Cycle ID --- FR-ID-001
                self.current_trade_id = uuid.uuid4().hex
                # -------------------------------

                # --- Log Signal Triggered ---
                signal_log_data = {
                    "trade_cycle_id": self.current_trade_id,
                    "signal_type": "SHORT_ENTRY",
                    "triggering_data": {
                        "close": self.data_close[0],
                        "ema_short": self.ema_short[0], "ema_medium": self.ema_medium[0], "ema_long": self.ema_long[0],
                        "rsi": self.rsi[0],
                        "macd": self.macd.macd[0], "macd_signal": self.macd.signal[0],
                        "bb_mid": self.bbands.mid[0],
                         "conditions": {
                            "ema": short_condition_ema,
                            "rsi": short_condition_rsi,
                            "macd": short_condition_macd,
                            "bbands": short_condition_bbands
                        }
                    }
                }
                self.log_event(SIGNAL_TRIGGERED, data_feed=self.datas[0], **signal_log_data)
                # ----------------------------


                entry_price = self.data_close[0]
                stop_loss_price = entry_price + current_atr * self.p.stop_loss_atr_multiplier
                size = self._calculate_trade_size(self.data_close[0], entry_price, stop_loss_price, self.p.risk_per_trade_percent, data=self.datas[0])
                # ORDER_CALCULATION log done inside

                if size > 0:
                    self._place_order(data=self.datas[0], order_type='sell', size=size, exectype=bt.Order.Market)
                    # ORDER_SUBMITTED log done inside
                else:
                    # self.log(f"计算出的空头仓位大小为零或负数 ({size}), 跳过下单", data=self.datas[0])
                    self.current_trade_id = None # Reset ID if trade is skipped

    def stop(self):
        # 定义stop函数，在策略结束时调用，用于执行清理工作或最终计算。 (Define the stop function, called at the end of the strategy for cleanup or final calculations.)
        # self.log(f"(EMA 短期: {self.p.ema_short_period}, 中期: {self.p.ema_medium_period}, 长期: {self.p.ema_long_period}), "
        #          f"(布林带 周期: {self.p.bbands_period}, 因子: {self.p.bbands_devfactor:.1f}), "
        #          f"(RSI 周期: {self.p.rsi_period}, 超买: {self.p.rsi_overbought}, 超卖: {self.p.rsi_oversold}), "
        #          f"(MACD 快: {self.p.macd_fast_period}, 慢: {self.p.macd_slow_period}, 信号: {self.p.macd_signal_period}), "
        #          f"(ATR 周期: {self.p.atr_period}, 止损倍数: {self.p.stop_loss_atr_multiplier:.1f}, 止盈倍数: {self.p.take_profit_atr_multiplier:.1f}), "
        #          f"(风险 每笔: {self.p.risk_per_trade_percent:.2%}, 总计: {self.p.max_total_risk_percent:.2%}, 动态调整: {self.p.enable_dynamic_risk_adjustment}), "
        #          f"(最大回撤: {self.p.max_drawdown_limit_percent:.2%}, 连续亏损: {self.p.consecutive_losses_limit}, 风险降低: {self.p.risk_reduction_factor:.1f}), "
        #          f"最终资产价值: {self.broker.getvalue():.2f}", dt=self.datas[0].datetime.date(0))

        # --- Log Strategy Stop ---
        stop_log_data = {
             "final_value": self.broker.getvalue(),
             "initial_cash": self.broker.startingcash,
             "final_cash": self.broker.getcash(),
             "high_water_mark": self.high_water_mark,
             # Include final parameter values if they could have changed (unlikely here)
             "params_at_stop": self.p._getkwargs()
        }
        self.log_event(STRATEGY_STOP, **stop_log_data)
        # --------------------------

        # --- Safely close logger --- FR-LOG-016
        if self.p.enable_logging and hasattr(self, 'logger'):
             if hasattr(self, '_log_queue_listener'): # Async
                 self._log_queue_listener.stop()
             if hasattr(self, '_log_handler_to_close'): # Sync or Async's actual handler
                 self._log_handler_to_close.close()
                 self.logger.removeHandler(self._log_handler_to_close)
        # --------------------------



# --- Remaining unchanged code (data loading, analysis, printing etc.) ---

def load_data_to_cerebro(cerebro, data_files, column_mapping, openinterest_col, fromdate, todate):
    # 加载数据到Cerebro引擎，处理多个数据文件和列映射。
    # Load data into Cerebro engine, handling multiple data files and column mapping.
    """Loads data from specified files into Cerebro, handling column mapping."""
    print("开始加载数据文件...")
    # (Start loading data files...)
    for i, file_path in enumerate(data_files):
        print(f"加载文件: {file_path}")
        # (Loading file: {file_path})
        try:
            # 创建Pandas数据加载器。
            # Create Pandas data feed loader.
            data = bt.feeds.PandasData(
                dataname=pd.read_csv(file_path, index_col='datetime', parse_dates=True),
                fromdate=fromdate,
                todate=todate,
                # 根据提供的映射动态设置列名。
                # Dynamically set column names based on the provided mapping.
                **{bt_col: csv_col for csv_col, bt_col in column_mapping.items()},
                # 将未平仓合约量列设置为-1，表示不使用该列。
                # Set openinterest column to -1, indicating not to use this column.
                openinterest=openinterest_col
            )
            # 为数据源添加名称，便于区分和日志记录。
            # Add a name to the data feed for easy identification and logging.
            data_name = os.path.splitext(os.path.basename(file_path))[0]
            cerebro.adddata(data, name=data_name)
            print(f"数据 '{data_name}' 加载成功。")
            # (Data '{data_name}' loaded successfully.)
        except Exception as e:
            print(f"加载文件 {file_path} 时出错: {e}")
            # (Error loading file {file_path}: {e})
            print("请检查文件路径、格式以及列名映射是否正确。")
            # (Please check the file path, format, and column name mapping.)
            raise  # 重新引发异常，以便上层调用者知道加载失败。 (Re-raise the exception so the caller knows loading failed.)
    print(f"数据加载完成，共加载 {len(cerebro.datas)} 个数据源。")
    # (Data loading complete, loaded {len(cerebro.datas)} data feeds.)


def analyze_optimization_results(results):
    # 分析优化结果，找出最佳参数组合。
    # Analyze optimization results to find the best parameter combination.
    """Analyzes optimization results to find the best performing strategy."""
    best_result = None
    best_score = -float('inf') # 初始化为负无穷大，确保任何正收益都会被选中 (Initialize to negative infinity to ensure any positive return is selected)
    all_results = []
    all_scored_results = [] # 用于存储带评分的结果 (To store results with scores)

    print("\n--- 开始分析优化结果 ---")
    # (Start analyzing optimization results)
    if not results:
        print("警告：未收到任何优化结果。")
        # (Warning: No optimization results received.)
        return None, []

    for i, run in enumerate(results):
        # 确保 run 是列表或元组，并且至少有一个元素 (strategy instance)
        # Ensure run is a list or tuple and has at least one element (strategy instance)
        if not isinstance(run, (list, tuple)) or not run:
             print(f"警告：跳过无效的运行结果 #{i+1}，格式不符合预期。")
             # (Warning: Skipping invalid run result #{i+1}, format not as expected.)
             continue

        strategy = run[0] # 第一个元素是策略实例 (The first element is the strategy instance)
        params = strategy.params._getkwargs() # 获取当前运行的参数 (Get parameters for the current run)
        final_value = strategy.broker.getvalue()
        initial_cash = strategy.broker.startingcash
        pnl = final_value - initial_cash
        pnl_percent = (pnl / initial_cash) * 100 if initial_cash else 0

        # 提取分析器结果 (如果存在)
        # Extract analyzer results (if they exist)
        analyzers = strategy.analyzers.getitems()
        sharpe = None
        drawdown = None
        trade_analysis = None
        sqn = None

        for aname, analyzer in analyzers:
            analysis = analyzer.get_analysis()
            if isinstance(analyzer, bt.analyzers.SharpeRatio):
                 sharpe = analysis.get('sharperatio')
            elif isinstance(analyzer, bt.analyzers.DrawDown):
                 drawdown = analysis.get('max', {}).get('drawdown')
            elif isinstance(analyzer, bt.analyzers.TradeAnalyzer):
                 trade_analysis = analysis # 存储整个交易分析结果 (Store the entire trade analysis result)
            elif isinstance(analyzer, bt.analyzers.SQN):
                 sqn = analysis.get('sqn')


        # --- 评分机制 (Scoring Mechanism) ---
        # 目标：结合多个指标给出综合评分，高评分代表更好的策略表现
        # Goal: Combine multiple metrics for a composite score, higher score indicates better strategy performance
        # 1. 主要指标：夏普比率 (如果存在)
        # 1. Primary Metric: Sharpe Ratio (if available)
        score = sharpe if sharpe is not None else 0

        # 2. 辅助指标：总收益率 (加分项)
        # 2. Secondary Metric: Total PnL % (Bonus points)
        score += pnl_percent / 100 # 将百分比转换为小数加入评分 (Convert percentage to decimal and add to score)

        # 3. 风险调整：最大回撤 (扣分项，回撤越大扣分越多)
        # 3. Risk Adjustment: Max Drawdown (Penalty points, larger drawdown means more penalty)
        if drawdown is not None and drawdown > 0:
             score -= (drawdown / 100) * 0.5 # 示例：回撤惩罚权重为0.5 (Example: Drawdown penalty weight 0.5)

        # 4. 系统质量：SQN (加分项，越高越好)
        # 4. System Quality: SQN (Bonus points, higher is better)
        if sqn is not None:
             score += sqn / 10 # 示例：SQN 评分权重为 0.1 (Example: SQN score weight 0.1)

        # 5. 交易次数惩罚/奖励 (可选): 避免过拟合或交易不足
        # 5. Trade Count Penalty/Reward (Optional): Avoid overfitting or insufficient trading
        # if trade_analysis and 'total' in trade_analysis and 'closed' in trade_analysis['total']:
        #     total_trades = trade_analysis['total']['closed']
        #     if total_trades < 10: # 交易太少可能不可靠 (Too few trades might be unreliable)
        #         score *= 0.8 # 惩罚 (Penalty)
        #     elif total_trades > 500: # 交易过多可能过拟合或成本高 (Too many trades might overfit or have high costs)
        #         score *= 0.9 # 轻微惩罚 (Slight penalty)

        # ------------------------------------

        result_summary = {
            'params': params,
            'final_value': final_value,
            'pnl_percent': pnl_percent,
            'sharpe': sharpe,
            'max_drawdown': drawdown,
            'sqn': sqn,
            'trade_analysis': trade_analysis, # 包含详细交易统计 (Includes detailed trade statistics)
            'score': score # 添加综合评分 (Add composite score)
        }
        all_results.append(result_summary)
        all_scored_results.append(result_summary) # 也添加到带评分列表 (Add to scored list as well)

        # 更新最佳结果 (Update best result based on score)
        if score > best_score:
            best_score = score
            best_result = result_summary
            print(f"找到新的最佳结果 (Run #{i+1}): Score={score:.4f}, Sharpe={sharpe if sharpe is not None else 'N/A'}, PNL%={pnl_percent:.2f}%, Drawdown={drawdown if drawdown is not None else 'N/A'}%, Params={params}")
            # (Found new best result (Run #{i+1}): Score=..., Sharpe=..., PNL%=..., Drawdown=..., Params=...)

    if best_result:
        print("\n--- 优化分析完成 ---")
        # (Optimization analysis complete)
        print(f"最佳评分: {best_result['score']:.4f}")
        # (Best Score:)
        print(f"最佳参数组合: {best_result['params']}")
        # (Best Parameter Combination:)
        print(f"对应指标: 最终价值={best_result['final_value']:.2f}, 收益率={best_result['pnl_percent']:.2f}%, "
              f"夏普比率={best_result['sharpe'] if best_result['sharpe'] is not None else 'N/A'}, "
              f"最大回撤={best_result['max_drawdown'] if best_result['max_drawdown'] is not None else 'N/A'}%, "
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
