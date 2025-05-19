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


if __name__ == '__main__':
    cerebro = bt.Cerebro(optreturn=False)  # 设置optreturn=False以便后续分析策略详情

    # --- 优化参数范围设定 ---
    # 为每个需要优化的参数提供一个范围列表或range对象
    # 这里使用了range进行示例，你可以根据需要调整范围和步长
    fast_ma_range = range(5, 16, 5)      # 快线周期: 5, 10, 15
    slow_ma_range = range(20, 41, 10)    # 慢线周期: 20, 30, 40
    adx_period_range = range(10, 21, 5)   # ADX周期: 10, 15, 20
    adx_threshold_range = [20.0, 25.0, 30.0]  # ADX阈值: 20.0, 25.0, 30.0

    # --- 使用 optstrategy 添加策略进行优化 ---
    # 将 addstrategy 替换为 optstrategy
    # 注意：参数现在传入的是上面定义的范围
    cerebro.optstrategy(
        SmaCrossADXFilter,
        fast_ma_period=fast_ma_range,
        slow_ma_period=slow_ma_range,
        adx_period=adx_period_range,
        adx_threshold=adx_threshold_range
    )

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

    # 添加策略，使用默认参数
    # cerebro.addstrategy(SmaCrossADXFilter) # 注释掉原来的添加方式
    # 或者在添加时覆盖参数:
    # cerebro.addstrategy(SmaCrossADXFilter, adx_threshold=20.0, fast_ma_period=15)
    # cerebro.addsizer(bt.sizers.FixedSize, stake=5000) # 如果需要固定手数，取消注释
    print(f'Starting Portfolio Value: {cerebro.broker.getvalue():.2f} RMB')

    # --- 运行优化 ---
    # cerebro.run() 返回的是一个包含多组策略运行结果的列表
    opt_results = cerebro.run(maxcpus=1)  # 使用单核运行，如果需要多核加速，请确保代码可序列化并调整maxcpus

    print("--- Optimization Finished ---")

    # --- 分析优化结果 (可选) ---
    # 这里可以添加代码来分析 opt_results，找到最佳参数组合
    # 例如，可以遍历结果，根据最终组合价值或其他指标排序
    # final_results_list = []
    # for run in opt_results:
    #     for strategy in run:
    #         value = strategy.broker.get_value()
    #         params = strategy.params.__dict__ # 获取参数
    #         # 你可能还需要添加Analyzer来获取更详细的指标，如夏普比率、最大回撤等
    #         final_results_list.append({'params': params, 'value': value})

    # # 按最终价值降序排序
    # sorted_results = sorted(final_results_list, key=lambda x: x['value'], reverse=True)

    # print("--- Top 5 Optimization Results ---")
    # for i, result in enumerate(sorted_results[:5]):
    #      print(f"Rank {i+1}: Params: {result['params']}, Final Value: {result['value']:.2f}")

    # 注意：优化后，plot() 可能无法直接绘制所有结果，通常需要手动分析结果
    # cerebro.plot()
    # print(f'Final Portfolio Value: {cerebro.broker.getvalue():.2f} RMB') # 优化运行时，这个最终值意义不大，每个参数组合都有一个最终值

    # 可选: 绘制结果图表
    # 注意：ADX默认会绘制在单独的面板中
    # print("Plotting results...")
    # cerebro.plot(style='candlestick', volume=False)
