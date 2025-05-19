# -*- coding: utf-8 -*-
# @Author : huanglei
# @File : 课程第八阶段：创建简单自定义 Observer - 特定指标可视化.py

import datetime
import os.path
import sys
import backtrader as bt
from backtrader.indicators import EMA
import pprint

# --- 自定义 Observer ---
# 创建一个 Observer 来单独绘制 MACD Histogram


class MACDHistoObserver(bt.Observer):
    # 定义要观察的线，这里增加了两条线分别表示正值和负值
    lines = ('histo_plus', 'histo_minus',)

    # 设置绘图信息
    plotinfo = dict(
        plot=True,      # 绘制此 Observer
        subplot=True,   # 在单独的副图中绘制
        plotname='MACD Histogram',  # 图例名称
        plotlinelabels=True,  # 显示线的标签
    )

    # 设置线的属性
    plotlines = dict(
        histo_plus=dict(
            _name='Positive',  # 名称
            _method='bar',     # 使用柱状图
            width=0.5,         # 宽度
            color='green',     # 正值用绿色
            _skipnan=True,
        ),
        histo_minus=dict(
            _name='Negative',  # 名称
            _method='bar',     # 使用柱状图
            width=0.5,         # 宽度
            color='red',       # 负值用红色
            _skipnan=True,
        ),
    )

    # Observer 的初始化方法
    def __init__(self):
        # 调用父类的初始化方法
        super().__init__()
        # 将 Observer 的 histo 线 与 策略中的 MACD Histogram 指标的 histo 线关联
        # self._owner 指向的是包含此 Observer 的策略实例
        # 我们需要在策略的 __init__ 中计算 MACD Histogram 并保存引用
        self.src_histo = self._owner.macd_histo.histo

    # Observer 的 next 方法，每个 K 线调用一次
    # 根据 histogram 的正负值分别填充两条线
    def next(self):
        # 定义 next 方法，每个 K 线数据点都会调用一次这个方法。
        # (这个函数就像一个检查员，每来一根新的蜡烛图，它都要检查一下。)
        if self.src_histo[0] > 0:
            # 检查当前的 MACD Histogram 值 (self.src_histo[0]) 是否大于 0。
            # (看看当前的 MACD 柱子是不是正的，也就是在零轴上方。)
            self.lines.histo_plus[0] = self.src_histo[0]
            # 如果大于 0，将 'histo_plus' 这条线当前的值设置为 Histogram 的值。
            # (如果是正的，就在代表“正数”的柱子那边画上同样高度的柱子。)
            self.lines.histo_minus[0] = 0
            # 同时将 'histo_minus' 这条线当前的值设置为 0。
            # (同时，在代表“负数”的柱子那边就不画东西，高度是 0。)
        else:
            # 如果 Histogram 的值不大于 0 (即小于或等于 0)。
            # (如果 MACD 柱子不是正的，那就是负的或者刚好是零。)
            self.lines.histo_plus[0] = 0
            # 将 'histo_plus' 这条线当前的值设置为 0。
            # (那么，在代表“正数”的柱子那边就不画东西，高度是 0。)
            self.lines.histo_minus[0] = self.src_histo[0]
            # 将 'histo_minus' 这条线当前的值设置为 Histogram 的值 (这个值是负数或零)。
            # (在代表“负数”的柱子那边画上同样高度的柱子（向下画）。)

# --- 策略定义 ---


class TestStrategy(bt.Strategy):
    params = (('maperiod', 15),)

    def log(self, txt, dt=None): dt = dt or self.datas[0].datetime.date(
        0)  # ; print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.order = None
        me1 = EMA(self.data, period=12)
        me2 = EMA(self.data, period=26)
        self.macd = me1 - me2
        self.signal = EMA(self.macd, period=9)

        # --- 计算 MACD Histogram 并保存引用 ---
        # 同时禁用其默认绘图，避免重复
        self.macd_histo = bt.indicators.MACDHisto(self.data)
        self.macd_histo.plotinfo.plot = False  # 禁用默认绘制
        # ------------------------------------

        self.bar_executed_close = 0

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        if order.status in [order.Completed]:
            if order.isbuy():
                self.bar_executed_close = self.dataclose[0]
        self.order = None

    def notify_trade(self, trade): pass

    def next(self):
        if self.order:
            return
        if not self.position:
            condition1 = self.macd[-1] - self.signal[-1]
            condition2 = self.macd[0] - self.signal[0]
            if condition1 < 0 and condition2 > 0:
                self.order = self.buy()
        else:
            condition = (
                self.dataclose[0] - self.bar_executed_close) / self.dataclose[0]
            if condition > 0.1 or condition < -0.1:
                self.order = self.sell()


# --- 主程序入口 ---
if __name__ == '__main__':
    cerebro = bt.Cerebro(stdstats=False)  # 禁用默认 observers
    cerebro.addstrategy(TestStrategy)

    # --- 添加 Observers ---
    cerebro.addobserver(bt.observers.Broker)
    cerebro.addobserver(bt.observers.Trades)
    cerebro.addobserver(bt.observers.BuySell, barplot=True)
    # --- 添加自定义 Observer ---
    cerebro.addobserver(MACDHistoObserver)
    # -----------------------

    # --- 添加 Analyzers (保持不变) ---
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='tradeanalyzer')
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.SQN, _name='sqn')
    cerebro.addanalyzer(bt.analyzers.TimeReturn,
                        timeframe=bt.TimeFrame.Years, _name='timereturn_yearly')
    cerebro.addanalyzer(bt.analyzers.PyFolio,
                        timeframe=bt.TimeFrame.Days, _name='pyfolio')

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

    # --- 打印 Analyzer 结果 (保持不变，简化打印) ---
    # ... (省略) ...

    print("-" * 30 + " Final Portfolio Value " + "-" * 30)
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # --- 绘制图表 ---
    cerebro.plot(style='candlestick')
