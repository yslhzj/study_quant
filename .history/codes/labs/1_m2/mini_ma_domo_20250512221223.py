# module_6_script.py
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
import backtrader as bt
import pandas as pd
import datetime
import os

# --- 策略定义 20250512---


class SmaCrossADXFilter(bt.Strategy):
    # 定义参数，包括均线周期、ADX周期和ADX阈值
    params = (
        ('fast_ma_period', 10),
        ('slow_ma_period', 30),
        ('adx_period', 14),      # ADX的标准周期
        ('adx_threshold', 25.0),  # ADX趋势强度阈值
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
            self.sma_fast, self.sma_slow, plot=False
        )

        # 实例化 ADX 指标
        self.adx = bt.indicators.AverageDirectionalMovementIndex(
            # 添加plot=False参数不在observer图中显示
            self.datas[0], period=self.p.adx_period, plot=False
        )
        print("--- SMA Crossover ADX Filter Strategy Initialized ---")
        print(f"Fast MA: {self.p.fast_ma_period}, Slow MA: {self.p.slow_ma_period}, ADX Period: {self.p.adx_period}, ADX Threshold: {self.p.adx_threshold}")

    def notify_order(self, order):
        # (与模块五相同)
        if order.status in [bt.Order.Submitted, bt.Order.Accepted]:
            return
        if order.status in [bt.Order.Completed]:
            if order.isbuy():
                self.log(
                    f'BUY EXECUTED, Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}, Size: {order.executed.size:.0f}')
            elif order.issell():
                self.log(
                    f'SELL EXECUTED, Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}, Size: {order.executed.size:.0f}')
        elif order.status in [bt.Order.Canceled, bt.Order.Margin, bt.Order.Rejected]:
            self.log(
                f'Order Canceled/Margin/Rejected: Status {order.getstatusname()}')
        self.order = None

    def notify_trade(self, trade):
        # (与模块五相同)
        if not trade.isclosed:
            return
        self.log(
            f'OPERATION PROFIT, GROSS {trade.pnl:.2f}, NET {trade.pnlcomm:.2f}')

    def next(self):
        # 检查是否有待处理订单
        if self.order:
            return

        # 获取当前ADX值
        current_adx = self.adx[0]

        # 检查是否持有仓位
        if not self.position:
            # 买入信号：快线上穿慢线 且 ADX高于阈值
            if self.sma_crossover > 0 and current_adx > self.p.adx_threshold:
                self.log(
                    f'BUY CREATE, Close: {self.dataclose[0]:.2f}, ADX: {current_adx:.2f}, Size: {self.getsizing(self.datas[0]):.0f} shares')
                self.order = self.buy(size=5000)
        else:  # 持有仓位
            # 卖出（平仓）信号：快线下穿慢线 (此处未加ADX过滤)
            if self.sma_crossover < 0:
                self.log(
                    f'SELL CREATE (Close Position), Close: {self.dataclose[0]:.2f}, Size: {self.position.size}')
                self.order = self.close()


# 优化回调函数
def opt_callback(result):
    # 提取参数和分析结果
    params = result[0].params
    sharpe = result[0].analyzers.sharpe.get_analysis().get('sharperatio', 0.0)
    drawdown = result[0].analyzers.drawdown.get_analysis()
    max_dd = drawdown.get('max', {}).get('drawdown', 0.0)
    total_return = result[0].analyzers.returns.get_analysis().get(
        'rtot', 0.0) * 100

    # 只打印高收益率和低回撤的策略参数
    if sharpe > 1.0 and max_dd < 0.20 and total_return > 10.0:
        print('-' * 80)
        print(f'Fast MA: {params.fast_ma_period}, Slow MA: {params.slow_ma_period}, '
              f'ADX Period: {params.adx_period}, ADX Threshold: {params.adx_threshold}')
        print(f'Sharpe Ratio: {sharpe:.4f}')
        print(f'Max. Drawdown: {max_dd:.2%}')
        print(f'Total Return: {total_return:.2f}%')


if __name__ == '__main__':
    cerebro = bt.Cerebro()
    cerebro.broker.setcash(500000.0)
    cerebro.broker.setcommission(commission=0.001)  # 设置0.1%的佣金

    # --- 加载数据 ---
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(script_dir, 'sample_data_a_share.csv')
    df = pd.read_csv(data_path, parse_dates=True, index_col='Date')
    data_feed = bt.feeds.PandasData(
        dataname=df,
        fromdate=datetime.datetime(2023, 1, 1),
        todate=datetime.datetime(2023, 12, 31)
    )
    cerebro.adddata(data_feed, name='SampleStock')

    # 添加分析器
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')

    # 设置优化回调
    cerebro.optcallback(opt_callback)

    # 参数优化设置
    cerebro.optstrategy(
        SmaCrossADXFilter,
        fast_ma_period=range(5, 21, 3),      # 5-20，步长3
        slow_ma_period=range(20, 41, 5),     # 20-40，步长5
        adx_period=range(10, 21, 2),         # 10-20，步长2
        adx_threshold=[20.0, 25.0, 30.0]     # 测试三个阈值
    )

    print(f'Initial Portfolio Value: {cerebro.broker.getvalue():.2f} RMB')
    results = cerebro.run()
    print(f'Final Portfolio Value: {cerebro.broker.getvalue():.2f} RMB')

    # 找出最佳参数组合
    best_sharpe = 0.0
    best_params = None
    best_result = None

    for result in results:
        sharpe = result[0].analyzers.sharpe.get_analysis().get(
            'sharperatio', 0.0)
        if sharpe > best_sharpe:
            best_sharpe = sharpe
            best_params = result[0].params
            best_result = result[0]

    if best_params:
        print("\n最佳参数组合:")
        print(f'Fast MA: {best_params.fast_ma_period}, Slow MA: {best_params.slow_ma_period}, '
              f'ADX Period: {best_params.adx_period}, ADX Threshold: {best_params.adx_threshold}')
        print(f'Sharpe Ratio: {best_sharpe:.4f}')
        drawdown = best_result.analyzers.drawdown.get_analysis()
        max_dd = drawdown.get('max', {}).get('drawdown', 0.0)
        print(f'Max. Drawdown: {max_dd:.2%}')
        total_return = best_result.analyzers.returns.get_analysis().get('rtot', 0.0) * 100
        print(f'Total Return: {total_return:.2f}%')

    # 使用最佳参数运行一次并绘制图表
    if best_params:
        print("\n使用最佳参数运行策略并绘制图表...")
        cerebro_plot = bt.Cerebro()
        cerebro_plot.broker.setcash(500000.0)
        cerebro_plot.broker.setcommission(commission=0.001)
        cerebro_plot.adddata(data_feed)
        cerebro_plot.addstrategy(
            SmaCrossADXFilter,
            fast_ma_period=best_params.fast_ma_period,
            slow_ma_period=best_params.slow_ma_period,
            adx_period=best_params.adx_period,
            adx_threshold=best_params.adx_threshold
        )
        cerebro_plot.run()
        cerebro_plot.plot(style='candlestick')
