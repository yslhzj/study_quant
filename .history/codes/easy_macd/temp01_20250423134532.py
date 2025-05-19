# -*- coding: utf-8 -*-
# @Author : huanglei
# @File : 课程第七阶段：配置观察器参数 - 自定义可视化.py

import datetime
import os.path
import sys
import backtrader as bt
from backtrader.indicators import EMA
import pprint

# --- 策略定义 (与之前相同) ---
class TestStrategy(bt.Strategy):
    params = (('maperiod', 15),)
    def log(self, txt, dt=None): dt = dt or self.datas[0].datetime.date(0) # ; print('%s, %s' % (dt.isoformat(), txt))
    def __init__(self):
        self.dataclose = self.datas[0].close; self.order = None
        me1 = EMA(self.data, period=12); me2 = EMA(self.data, period=26)
        self.macd = me1 - me2; self.signal = EMA(self.macd, period=9)
        bt.indicators.MACDHisto(self.data)
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

    # --- 手动添加并配置 Observers ---
    # 添加 Broker observer
    # 尝试修改线条颜色和样式 (注意: Broker Observer 的 plotinfo 可能不易直接通过kwargs配置，
    # 更可靠的方式是获取实例后修改，但这里尝试kwargs)
    # 效果可能不明显，取决于 backtrader 内部处理 plotinfo 的方式
    cerebro.addobserver(bt.observers.Broker, plotinfo=dict(subplot=True, color=' ', ls='--'))

    # 添加 Trades observer
    cerebro.addobserver(bt.observers.Trades)

    # 添加 BuySell observer，并配置参数
    # barplot=True: 将标记绘制在价格条下方/上方，而不是直接在价格上
    # buyarrow=bt.Marker.TRIANGLE_UP : 设置买入标记为上三角 (需要导入 Marker) - Marker 可能不存在，需确认
    # sellarrow=bt.Marker.TRIANGLE_DOWN: 设置卖出标记为下三角
    # size=10: 尝试增大标记大小 (可能无效，取决于实现)
    # color = 'red' # 尝试统一设置颜色 (可能无效)
    # 注意：并非所有参数都有效，取决于 Observer 的具体实现
    # 查看 backtrader/observers/buysell.py 源码可知其 plotinfo 设置
    cerebro.addobserver(bt.observers.BuySell, barplot=True) # barplot 是常用且有效的参数

    # 如果想更精细控制 BuySell 的箭头颜色，通常需要修改其 plotinfo 属性
    # 可以在策略的 start 方法中获取 observer 实例并修改
    # 例如 (在策略的 start 方法里):
    # self.stats.buysell.plotinfo.buyarrow = '^' # matplotlib marker
    # self.stats.buysell.plotinfo.sellarrow = 'v'
    # self.stats.buysell.plotinfo.arrowsize = 10.0
    # self.stats.buysell.plotinfo.buycolor = 'green'
    # self.stats.buysell.plotinfo.sellcolor = 'red'

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
    print("-" * 30 + " TradeAnalyzer Summary " + "-" * 30)
    try:
        ta = first_strategy.analyzers.tradeanalyzer.get_analysis()
        if ta and hasattr(ta, 'total') and ta.total.closed > 0:
             print(f"Total Net Profit: {ta.pnl.net.total:.2f}")
             print(f"Win Rate: {ta.won.total / ta.total.closed * 100:.2f}%")
        else: print("No trades.")
    except Exception as e: print(f"Error: {e}")

    # ... 其他 Analyzer 打印 ...

    print("-" * 30 + " Final Portfolio Value " + "-" * 30)
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # --- 绘制图表 ---
    # 观察图表中的 Observer 样式是否有变化
    cerebro.plot(style='candlestick') # 尝试不同的绘图风格