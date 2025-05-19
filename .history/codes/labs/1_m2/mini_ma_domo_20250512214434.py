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
        elif order.status in [bt.Order.Canceled, bt.Order.Rejected]:
            self.log(
                f'Order Canceled/Margin/Rejected: Status {order.Status[order.status]}')
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


# 添加一个性能分析器
class SharpeRatioWithDrawdown(bt.Analyzer):
    params = (
        ('timeframe', bt.TimeFrame.Years),
        ('compression', 1),
        ('riskfreerate', 0.01),
    )

    def start(self):
        self.returns = bt.analyzers.Returns(self.strategy)
        self.sharpe = bt.analyzers.SharpeRatio_A(self.strategy)
        self.drawdown = bt.analyzers.DrawDown(self.strategy)

    def stop(self):
        self.rets = self.returns.get_analysis()
        self.sharp = self.sharpe.get_analysis()
        self.dd = self.drawdown.get_analysis()

    def get_analysis(self):
        return {
            'returns': self.rets.get('rtot', 0.0),
            'sharpe': self.sharp.get('sharperatio', 0.0),
            'drawdown': self.dd.get('max', {}).get('drawdown', 0.0),
            'score': self.sharp.get('sharperatio', 0.0) - self.dd.get('max', {}).get('drawdown', 0.0) * 0.5
        }


if __name__ == '__main__':
    cerebro = bt.Cerebro(optreturn=False)  # 使用优化模式
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

    # 添加策略优化参数空间
    cerebro.optstrategy(
        SmaCrossADXFilter,
        fast_ma_period=range(5, 21, 5),       # 5,10,15,20
        slow_ma_period=range(20, 61, 10),     # 20,30,40,50,60
        adx_period=range(10, 21, 5),          # 10,15,20
        adx_threshold=range(15, 36, 5)        # 15,20,25,30,35
    )

    # 添加性能分析器
    cerebro.addanalyzer(SharpeRatioWithDrawdown, _name='sharpe_dd')

    # 运行优化
    print('开始参数优化...')
    results = cerebro.run()

    # 分析结果
    best_result = None
    best_score = -999

    for r in results:
        analyzer = r[0].analyzers.sharpe_dd.get_analysis()
        score = analyzer.get('score', 0)

        if score > best_score:
            best_score = score
            best_result = r[0]
            best_params = r[0].params

    print('最优参数组合:')
    print(f'快速均线周期: {best_params.fast_ma_period}')
    print(f'慢速均线周期: {best_params.slow_ma_period}')
    print(f'ADX周期: {best_params.adx_period}')
    print(f'ADX阈值: {best_params.adx_threshold}')
    print(
        f'收益率: {best_result.analyzers.sharpe_dd.get_analysis()["returns"]:.2%}')
    print(
        f'夏普比率: {best_result.analyzers.sharpe_dd.get_analysis()["sharpe"]:.2f}')
    print(
        f'最大回撤: {best_result.analyzers.sharpe_dd.get_analysis()["drawdown"]:.2%}')

    # 使用最优参数运行一次可视化回测
    cerebro_best = bt.Cerebro()
    cerebro_best.broker.setcash(500000.0)
    cerebro_best.broker.setcommission(commission=0.001)
    cerebro_best.adddata(data_feed, name='SampleStock')
    cerebro_best.addstrategy(
        SmaCrossADXFilter,
        fast_ma_period=best_params.fast_ma_period,
        slow_ma_period=best_params.slow_ma_period,
        adx_period=best_params.adx_period,
        adx_threshold=best_params.adx_threshold
    )

    print('使用最优参数运行回测...')
    print(f'初始资金: {cerebro_best.broker.getvalue():.2f} RMB')
    cerebro_best.run()
    print(f'最终资金: {cerebro_best.broker.getvalue():.2f} RMB')
    cerebro_best.plot(style='candlestick')
