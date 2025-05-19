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
    # 定义要观察的线，这里只有一条线 histo
    lines = ('histo',)

    # 设置绘图信息
    plotinfo = dict(
        plot=True,      # 绘制此 Observer
        subplot=True,   # 在单独的副图中绘制
        plotname='MACD Histogram', # 图例名称
        # plotlinelabels=True, # 是否显示线的标签 (比如 'histo')
        # 我们希望根据正负值显示不同颜色，基础 plotinfo 不易直接实现
        # 一种简单方法是用两条线，或在 next 中判断后赋值给特定线
        # 这里先用默认颜色绘制
    )

    # Observer 的初始化方法
    def __init__(self):
        # 调用父类的初始化方法
        super().__init__()
        # 将 Observer 的 histo 线 与 策略中的 MACD Histogram 指标的 histo 线关联
        # self._owner 指向的是包含此 Observer 的策略实例
        # 我们需要在策略的 __init__ 中计算 MACD Histogram 并保存引用
        self.lines.histo = self._owner.macd_histo.histo

    # Observer 的 next 方法，每个 K 线调用一次
    # 对于简单映射指标值的 Observer，next 通常可以为空
    # Backtrader 的绘图系统会自动从 self.lines.histo 获取数据
    def next(self):
        # 如果需要根据 histo 值做一些判断或计算，可以在这里进行
        # 例如，根据正负值更新不同的 lines (如果定义了多条线)
        pass

# --- 策略定义 ---
class TestStrategy(bt.Strategy):
    params = (('maperiod', 15),)
    def log(self, txt, dt=None): dt = dt or self.datas[0].datetime.date(0) # ; print('%s, %s' % (dt.isoformat(), txt))
    def __init__(self):
        self.dataclose = self.datas[0].close; self.order = None
        me1 = EMA(self.data, period=12); me2 = EMA(self.data, period=26)
        self.macd = me1 - me2; self.signal = EMA(self.macd, period=9)

        # --- 计算 MACD Histogram 并保存引用 ---
        # 同时禁用其默认绘图，避免重复
        self.macd_histo = bt.indicators.MACDHisto(self.data)
        # self.macd_histo.plotinfo.plot = False # 禁用默认绘制
        # ------------------------------------

        self.bar_executed_close = 0
    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]: return
        if order.status in [order.Completed]:
            if order.isbuy(): self.bar_executed_close = self.dataclose[0]
        self.order = None
    def notify_trade(self, trade): pass
    def next(self):
        if self.order: return
        if not self.position:
            condition1 = self.macd[-1] - self.signal[-1]; condition2 = self.macd[0] - self.signal[0]
            if condition1 < 0 and condition2 > 0: self.order = self.buy()
        else:
            condition = (self.dataclose[0] - self.bar_executed_close) / self.dataclose[0]
            if condition > 0.1 or condition < -0.1: self.order = self.sell()

# --- 主程序入口 ---
if __name__ == '__main__':
    cerebro = bt.Cerebro(stdstats=False) # 禁用默认 observers
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
    cerebro.addanalyzer(bt.analyzers.TimeReturn, timeframe=bt.TimeFrame.Years, _name='timereturn_yearly')
    cerebro.addanalyzer(bt.analyzers.PyFolio, timeframe=bt.TimeFrame.Days, _name='pyfolio')

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