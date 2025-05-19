# module_6_script.py
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
import backtrader as bt
import pandas as pd
import datetime
import os
import numpy as np

# --- 策略定义 ---


class SmaCrossStrategy(bt.Strategy):
    # 定义参数
    params = (
        ('fast_ma_period', 10),
        ('slow_ma_period', 30),
    )

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()}, {txt}')

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.order = None

        # 实例化 SMA 指标
        self.sma_fast = bt.indicators.SimpleMovingAverage(
            self.datas[0], period=self.p.fast_ma_period
        )
        self.sma_slow = bt.indicators.SimpleMovingAverage(
            self.datas[0], period=self.p.slow_ma_period
        )
        # 实例化 Crossover 指标
        self.sma_crossover = bt.indicators.CrossOver(
            self.sma_fast, self.sma_slow
        )

        print("--- SMA Crossover Strategy Initialized ---")
        print(
            f"Fast MA: {self.p.fast_ma_period}, Slow MA: {self.p.slow_ma_period}")

    def notify_order(self, order):
        # 处理订单状态
        if order.status in [bt.Order.Submitted, bt.Order.Accepted]:
            return
        if order.status in [bt.Order.Completed]:
            if order.isbuy():
                self.log(
                    f'BUY EXECUTED, Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}')
            elif order.issell():
                self.log(
                    f'SELL EXECUTED, Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}')
        elif order.status in [bt.Order.Canceled, bt.Order.Margin, bt.Order.Rejected]:
            self.log(f'Order Canceled/Margin/Rejected')
        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self.log(
            f'OPERATION PROFIT, GROSS {trade.pnl:.2f}, NET {trade.pnlcomm:.2f}')

    def next(self):
        # 检查是否有待处理订单
        if self.order:
            return

        # 检查是否持有仓位
        if not self.position:
            # 买入信号：快线上穿慢线
            if self.sma_crossover > 0:
                self.log(f'BUY CREATE, Close: {self.dataclose[0]:.2f}')
                self.order = self.buy()
        else:  # 持有仓位
            # 卖出（平仓）信号：快线下穿慢线
            if self.sma_crossover < 0:
                self.log(
                    f'SELL CREATE (Close Position), Close: {self.dataclose[0]:.2f}')
                self.order = self.close()


if __name__ == '__main__':
    cerebro = bt.Cerebro()
    cerebro.broker.setcash(500000.0)
    cerebro.broker.setcommission(commission=0.001)  # 设置0.1%的佣金

    # --- 创建示例数据 ---
    # 手动创建示例数据
    print("创建示例数据...")

    # 创建日期范围
    start_date = datetime.datetime(2023, 1, 1)
    end_date = datetime.datetime(2023, 12, 31)
    dates = pd.date_range(start=start_date, end=end_date, freq='B')

    # 生成随机价格数据
    np.random.seed(42)  # 设置随机种子，保证可复现

    # 初始价格
    initial_price = 100.0
    # 价格变动范围
    daily_volatility = 0.02

    # 生成价格
    prices = [initial_price]
    for _ in range(1, len(dates)):
        # 随机价格变动，有一定趋势性
        change = np.random.normal(0, daily_volatility)
        # 添加一些趋势
        if _ < len(dates) // 3:
            change += 0.001  # 上升趋势
        elif _ < 2 * len(dates) // 3:
            change -= 0.001  # 下降趋势
        else:
            change += 0.0005  # 轻微上升

        new_price = prices[-1] * (1 + change)
        prices.append(new_price)

    # 创建数据框
    df = pd.DataFrame({
        'Open': prices,
        'High': [p * (1 + np.random.uniform(0, daily_volatility)) for p in prices],
        'Low': [p * (1 - np.random.uniform(0, daily_volatility)) for p in prices],
        'Close': [p * (1 + np.random.normal(0, daily_volatility/2)) for p in prices],
        'Volume': np.random.randint(1000, 100000, size=len(dates)),
    }, index=dates)

    # 加载数据
    data_feed = bt.feeds.PandasData(
        dataname=df,
        fromdate=datetime.datetime(2023, 1, 1),
        todate=datetime.datetime(2023, 12, 31)
    )
    cerebro.adddata(data_feed, name='SampleStock')

    # 添加策略
    cerebro.addstrategy(SmaCrossStrategy)

    print(f'Starting Portfolio Value: {cerebro.broker.getvalue():.2f} RMB')

    try:
        results = cerebro.run()
        print(f'Final Portfolio Value: {cerebro.broker.getvalue():.2f} RMB')

        # 绘制结果图表
        print("Plotting results...")
        cerebro.plot(style='candlestick', volume=False)
    except Exception as e:
        print(f"执行出错：{str(e)}")
        print("可能需要安装matplotlib：pip install matplotlib")
