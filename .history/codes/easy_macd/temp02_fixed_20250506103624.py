# -*- coding: utf-8 -*-
# @Author : huanglei
# @File : 课程第十二阶段：自定义 Observer 进阶 - 事件驱动的可视化.py

import datetime
import os.path
import sys
import backtrader as bt
from backtrader.indicators import EMA
import pprint
from collections import OrderedDict, deque  # 导入 deque 用于存储交易信息
import math

# --- 自定义 Observer ---
# 响应交易关闭事件，在图上标记开仓和平仓点


class TradeEventObserver(bt.Observer):
    lines = ('trade_entry', 'trade_exit_win',
             'trade_exit_loss',)  # 标记开仓点、盈利平仓点、亏损平仓点
    plotinfo = dict(
        plot=True, subplot=False,  # 绘制在主图上
        plotlinelabels=True,  # 显示线的标签
    )

    # 分别设置标记样式
    plotlines = dict(
        trade_entry=dict(marker='^', markersize=8.0, color='blue',
                         fillstyle='full', ls=''),  # 开仓用蓝色向上三角
        trade_exit_win=dict(marker='o', markersize=8.0,
                            color='green', fillstyle='full', ls=''),  # 盈利平仓用绿色圆点
        trade_exit_loss=dict(marker='v', markersize=8.0,
                             color='red', fillstyle='full', ls=''),  # 亏损平仓用红色向下三角
    )

    def __init__(self):
        super().__init__()
        # 初始化时将所有线的值设为 NaN
        # 注意：不应该在__init__中设置值，因为此时数组还未初始化
        # 这些设置应该移到next方法中
        # self.lines.trade_entry[0] = math.nan
        # self.lines.trade_exit_win[0] = math.nan
        # self.lines.trade_exit_loss[0] = math.nan

    # 核心：响应交易通知
    def notify_trade(self, trade):
        if trade.isclosed:
            # 从策略中获取该交易的开平仓信息
            # (需要策略配合记录这些信息)
            entry_bar = self._owner.trade_entry_info.get(
                trade.ref, {}).get('bar')
            entry_price = self._owner.trade_entry_info.get(
                trade.ref, ).get('price')
            exit_bar = self._owner.trade_exit_info.get(
                trade.ref, {}).get('bar')
            exit_price = self._owner.trade_exit_info.get(
                trade.ref, {}).get('price')
            pnl = trade.pnlcomm  # 使用净利润判断

            if entry_bar is not None and entry_price is not None:
                # 在开仓 bar 索引处标记开仓价格
                # 注意：这里需要延迟标记，因为 Observer 的 next 可能已经执行完
                # 更好的方法是 Observer 自己维护一个待标记列表，在 next 中处理
                # 简化处理：直接在当前 bar (平仓bar) 的历史位置标记 (效果可能不精确)
                # idx_offset = len(self) - 1 - entry_bar # 计算索引偏移 (近似)
                # if idx_offset >= 0:
                #     self.lines.trade_entry[-idx_offset] = entry_price # 在历史位置标记

                # 简化：在当前 bar (平仓 bar) 标记开仓价格 (作为演示)
                # 注意：这会在平仓 K 线上标记开仓价，不是理想效果，仅为演示事件触发
                # self.lines.trade_entry[0] = entry_price # 取消这种不精确的标记

                pass  # 暂时不在 Observer 中标记开仓

            if exit_bar is not None and exit_price is not None:
                # 在平仓 bar 索引处标记平仓价格，根据盈亏选择不同的 line
                if pnl >= 0:
                    self.lines.trade_exit_win[0] = exit_price
                    self.lines.trade_exit_loss[0] = math.nan  # 清除另一个标记
                else:
                    self.lines.trade_exit_loss[0] = exit_price
                    self.lines.trade_exit_win[0] = math.nan  # 清除另一个标记

    # 在每个 K 线周期，需要将当前周期的标记重置为 NaN，否则标记会一直存在
    def next(self):
        self.lines.trade_entry[0] = math.nan
        self.lines.trade_exit_win[0] = math.nan
        self.lines.trade_exit_loss[0] = math.nan


# --- 策略定义 (修改以记录交易信息) ---
class TestStrategy(bt.Strategy):
    params = (('maperiod', 15), ('fast_ema', 12),
              ('slow_ema', 26), ('signal_ema', 9),)

    def log(self, txt, dt=None): dt = dt or self.datas[0].datetime.date(0)

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.order = None
        me1 = EMA(self.data, period=self.p.fast_ema)
        me2 = EMA(self.data, period=self.p.slow_ema)
        self.macd = me1 - me2
        self.signal = EMA(self.macd, period=self.p.signal_ema)

        # 使用bt.indicators.MACDHisto替代手动计算直方图
        # 这样可以避免"LinesOperation对象没有plotinfo属性"的错误
        self.macd_histo = bt.indicators.MACDHisto(
            self.data,
            period_me1=self.p.fast_ema,
            period_me2=self.p.slow_ema,
            period_signal=self.p.signal_ema
        )
        self.macd_histo.plotinfo.plot = False
        self.bar_executed_close = 0

        # --- 新增：用于存储交易开平仓信息的字典 ---
        # 键是 trade.ref，值是包含 bar 和 price 的字典
        self.trade_entry_info = {}
        self.trade_exit_info = {}
        # --------------------------------------

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        # --- 在订单完成时记录开仓信息 ---
        if order.status == order.Completed:
            # 如果是开仓订单 (买入且之前无仓位，或卖出且之前无仓位 - 简化：假设此策略只做多)
            # 这里用 tradeid 可能更可靠来判断是否是开仓，但简化处理
            # 或者通过 position size 变化判断
            is_entry = False
            current_pos = self.getposition(self.data).size
            executed_size = order.executed.size * (1 if order.isbuy() else -1)

            # 简单判断：如果执行后仓位从0变为非0，认为是开仓
            if current_pos - executed_size == 0 and current_pos != 0:
                is_entry = True

            if is_entry and order.isbuy():  # 只处理多头开仓
                # tradeid 可能还未完全关联，使用 order.ref 作为临时键或等待 notify_trade
                # 这里简化，假设 notify_order 时 tradeid 已可用 (不一定可靠)
                # 更可靠是在 notify_trade 首次进入时记录
                # pass # 移动到 notify_trade 中记录

                # 记录执行价格和 bar 索引
                self.bar_executed_close = self.dataclose[0]  # 这个变量原本就有

            # --- 在订单完成时记录平仓信息 (如果它是平仓单) ---
            is_exit = False
            # 简单判断：如果执行后仓位变为0，认为是平仓
            if current_pos == 0 and current_pos - executed_size != 0:
                is_exit = True

            if is_exit:
                # 找到对应的 trade ref
                trade_ref = order.tradeid  # 假设 tradeid 能唯一标识这次平仓对应的交易
                # 注意：如果 tradeid 复用，这里会有问题
                # 查找关联的 trade (这在 strategy 里不容易直接做)
                # 更好的方式是在 notify_trade 中处理

                # 简化：假设 order 完成时可以记录平仓信息给对应的 tradeid
                # self.trade_exit_info[trade_ref] = {
                #     'bar': len(self) -1, # 当前 bar 索引
                #     'price': order.executed.price
                # }
                pass  # 移动到 notify_trade 中记录

        self.order = None

    def notify_trade(self, trade):
        # --- 在交易首次打开时记录开仓信息 ---
        if trade.justopened:
            entry_order = trade.history[0].event.order  # 获取开仓订单
            self.trade_entry_info[trade.ref] = {
                'bar': trade.baropen,
                'price': entry_order.executed.price  # 使用订单执行价格
            }

        # --- 在交易关闭时记录平仓信息 ---
        if trade.isclosed:
            exit_order = trade.history[-1].event.order  # 获取平仓订单
            self.trade_exit_info[trade.ref] = {
                'bar': trade.barclose,
                'price': exit_order.executed.price  # 使用订单执行价格
            }
            # 清理可能过时的 entry_info (可选)
            # if trade.ref in self.trade_entry_info:
            #     pass # 保留用于 Observer 读取，或在 Observer 读取后清理

# --- 自定义 Analyzer (保持不变) ---


class GrossProfitFactorAnalyzer(bt.Analyzer):
    def __init__(self): super().__init__(
    ); self.tpnl = 0.0; self.tlnl = 0.0; self.wc = 0; self.lc = 0

    def notify_trade(self, t):
        if t.isclosed:
            p = t.pnl
            (self.tpnl, self.wc) = (self.tpnl+p,
                                    self.wc+1) if p > 0 else (self.tpnl, self.wc)
            (self.tlnl, self.lc) = (self.tlnl+p,
                                    self.lc+1) if p < 0 else (self.tlnl, self.lc)

    def stop(self): aw = self.tpnl/self.wc if self.wc else 0.0; al = self.tlnl/self.lc if self.lc else 0.0; f = abs(aw /
                                                                                                                    al) if al else float('inf') if aw else 0.0; self.rets = OrderedDict([('aw', aw), ('al', al), ('gpf', f)])


# --- 主程序入口 ---
if __name__ == '__main__':
    cerebro = bt.Cerebro(stdstats=False)
    cerebro.addstrategy(TestStrategy)

    # --- 添加 Observers ---
    cerebro.addobserver(bt.observers.Broker)
    cerebro.addobserver(bt.observers.Trades)
    cerebro.addobserver(bt.observers.BuySell, barplot=True)
    # --- 添加新的自定义事件驱动 Observer ---
    cerebro.addobserver(TradeEventObserver)
    # ---------------------------------

    # --- 添加 Analyzers (保持不变) ---
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='tradeanalyzer')
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, timeframe=bt.TimeFrame.Days,
                        compression=1, factor=252, annualize=True, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.SQN, _name='sqn')
    cerebro.addanalyzer(GrossProfitFactorAnalyzer, _name='grossprofitfactor')

    # --- 数据加载 (保持不变) ---
    modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
    datapath = os.path.join(modpath, '603186.csv')
    data = bt.feeds.GenericCSVData(
        dataname=datapath, fromdate=datetime.datetime(2010, 1, 1),
        todate=datetime.datetime(2020, 4, 12), dtformat='%Y%m%d',
        datetime=2, open=3, high=4, low=5, close=6, volume=10,
        timeframe=bt.TimeFrame.Days, reverse=True)
    cerebro.adddata(data)

    # --- 设置 (保持不变) ---
    cerebro.broker.setcash(10000.0)
    cerebro.addsizer(bt.sizers.FixedSize, stake=100)
    cerebro.broker.setcommission(commission=0.005)

    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
    results = cerebro.run()
    first_strategy = results[0]

    # --- 打印 Analyzer 结果 (保持不变) ---
    # ... (省略) ...

    print("-" * 30 + " Final Portfolio Value " + "-" * 30)
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # --- 绘制图表 ---
    cerebro.plot(style='candlestick')
