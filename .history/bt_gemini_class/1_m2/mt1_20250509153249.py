# module_5_script.py
from __future__ import (absolute_import, division, print_function, unicode_literals)
import backtrader as bt
import pandas as pd
import datetime , os

# --- 策略定义 ---
class SmaCrossStrategy(bt.Strategy):
    # 定义策略参数
    params = (
        ('fast_ma_period', 10), # 快线周期
        ('slow_ma_period', 30), # 慢线周期
    )

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()}, {txt}')

    def __init__(self):
        self.dataclose = self.datas[0].close # 收盘价线引用
        self.order = None # 订单跟踪
        self.buyprice = None
        self.buycomm = None

        # 实例化移动平均线指标
        self.sma_fast = bt.indicators.SimpleMovingAverage(
            self.datas, period=self.params.fast_ma_period
        )
        self.sma_slow = bt.indicators.SimpleMovingAverage(
            self.datas, period=self.params.slow_ma_period
        )

        # 实例化交叉指标
        # 当 sma_fast 上穿 sma_slow 时，sma_crossover > 0
        # 当 sma_fast 下穿 sma_slow 时，sma_crossover < 0
        self.sma_crossover = bt.indicators.CrossOver(
            self.sma_fast, self.sma_slow
        )
        print("--- SMA Crossover Strategy Initialized ---")
        print(f"Fast MA Period: {self.p.fast_ma_period}, Slow MA Period: {self.p.slow_ma_period}")

    def notify_order(self, order):
        if order.status in [bt.Order.Submitted, bt.Order.Accepted]:
            return
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'BUY EXECUTED, Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}')
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            elif order.issell(): # 平仓单完成
                self.log(f'SELL EXECUTED, Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}')
        elif order.status in [bt.Order.Canceled, bt.Order.Rejected]:
            self.log(f'Order Canceled/Margin/Rejected: Status {order.Status[order.status]}')
        self.order = None # 重置订单跟踪

    def notify_trade(self, trade):
         if not trade.isclosed:
             return
         self.log(f'OPERATION PROFIT, GROSS {trade.pnl:.2f}, NET {trade.pnlcomm:.2f}')

    def next(self):
        # 记录收盘价和均线值（可选，用于调试）
        # self.log(f'Close: {self.dataclose:.2f}, FastMA: {self.sma_fast:.2f}, SlowMA: {self.sma_slow:.2f}, CrossOver: {self.sma_crossover}')

        # 检查是否有待处理订单
        if self.order:
            return

        # 检查是否持有仓位
        if not self.position:
            # 买入信号：快线上穿慢线 (sma_crossover > 0)
            if self.sma_crossover > 0:
                self.log(f'BUY CREATE, Close: {self.dataclose:.2f}')
                self.order = self.buy() #必须保存到self.order​，否则无法管理订单状态。
        else: # 持有仓位
            # 卖出（平仓）信号：快线下穿慢线 (sma_crossover < 0)
            if self.sma_crossover < 0:
                self.log(f'SELL CREATE (Close Position), Close: {self.dataclose:.2f}')
                self.order = self.close()

if __name__ == '__main__':
    cerebro = bt.Cerebro()
    cerebro.broker.setcash(500000.0)
    cerebro.broker.setcommission(commission=0.001) # 设置0.1%的佣金

    # --- 加载数据 ---
    script_dir = os.path.dirname(os.path.abspath(__file__)); data_path = os.path.join(script_dir, 'sample_data_a_share.csv')
    df = pd.read_csv(data_path, parse_dates=True, index_col='Date')
    data_feed = bt.feeds.PandasData(
        dataname=df,
        fromdate=datetime.datetime(2023, 1, 1),
        todate=datetime.datetime(2023, 12, 31) # 使用全年数据
    )
    cerebro.adddata(data_feed, name='SampleStock')

    cerebro.addstrategy(SmaCrossStrategy)

    print(f'Starting Portfolio Value: {cerebro.broker.getvalue():.2f} RMB')
    cerebro.run()
    print(f'Final Portfolio Value: {cerebro.broker.getvalue():.2f} RMB')

    # 可选: 绘制结果图表 (需要安装 matplotlib: pip install matplotlib)
    # print("Plotting results...")
    # cerebro.plot(style='candlestick')