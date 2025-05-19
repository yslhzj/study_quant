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

    # --- 添加分析器 ---
    # 将 SharpeRatio_A 替换为 SharpeRatio
    # cerebro.addanalyzer(bt.analyzers.SharpeRatio_A, _name='sharpe', timeframe=bt.TimeFrame.Years) # 年化夏普比率 (原代码)
    # 使用SharpeRatio, 默认会年化。假设无风险利率为0
    cerebro.addanalyzer(bt.analyzers.SharpeRatio,
                        _name='sharpe', riskfreerate=0.0)
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')  # 最大回撤
    cerebro.addanalyzer(bt.analyzers.AnnualReturn, _name='annreturn')  # 年化回报率
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')  # 交易分析

    print(f'Starting Portfolio Value: {cerebro.broker.getvalue():.2f} RMB')

    # --- 运行优化 ---
    opt_results = cerebro.run(maxcpus=1)  # 使用单核运行

    print("--- Optimization Finished ---")

    # --- 分析优化结果 ---
    parsed_results = []
    for run_result in opt_results:
        strategy_instance = run_result[0]
        params = strategy_instance.params.__dict__.copy()

        # 获取分析器结果
        # SharpeRatio 分析器
        sharpe_analysis = strategy_instance.analyzers.sharpe.get_analysis()
        sharpe_ratio = sharpe_analysis.get('sharperatio', float('-inf'))
        if sharpe_ratio is None:  # 防御性检查
            sharpe_ratio = float('-inf')

        # 最大回撤
        drawdown_analysis = strategy_instance.analyzers.drawdown.get_analysis()
        max_drawdown_money = drawdown_analysis.max.moneydown
        max_drawdown_percent = drawdown_analysis.max.drawdown

        # 年化回报率 (返回一个字典，键为年份，值为回报率)
        annual_return_analysis = strategy_instance.analyzers.annreturn.get_analysis()

        # 交易次数
        trades_analysis = strategy_instance.analyzers.trades.get_analysis()
        total_trades = trades_analysis.total.total

        # 最终组合价值
        final_value = strategy_instance.broker.getvalue()

        parsed_results.append({
            'params': params,
            'sharpe_ratio': sharpe_ratio,  # 现在这个值来自 SharpeRatio 而非 SharpeRatio_A
            'max_drawdown_money': max_drawdown_money,
            'max_drawdown_percent': max_drawdown_percent,
            'annual_return': annual_return_analysis,
            'total_trades': total_trades,
            'final_value': final_value
        })

    # 根据夏普比率降序排序结果
    sorted_results = sorted(
        parsed_results, key=lambda x: x['sharpe_ratio'], reverse=True)

    # --- 打印最佳结果 ---
    print("\n--- Top 5 Optimization Results (Sorted by Sharpe Ratio) ---")
    if not sorted_results:
        print("No results to display. Check optimization parameters or data.")
    else:
        for i, result in enumerate(sorted_results[:5]):  # 打印前5个结果
            print(f"Rank {i+1}:")
            p = result['params']
            print(
                f"  Parameters: fast_ma={p.get('fast_ma_period')}, slow_ma={p.get('slow_ma_period')}, adx_period={p.get('adx_period')}, adx_threshold={p.get('adx_threshold')}")
            # 注意这里的Sharpe Ratio解释变为基于日收益率（或其他基础频率）计算并年化的结果
            print(f"  Sharpe Ratio (Annualized): {result['sharpe_ratio']:.2f}")
            formatted_returns = {
                year: f"{ret*100:.2f}%" for year, ret in result['annual_return'].items()}
            print(f"  Annual Returns: {formatted_returns}")
            print(
                f"  Max Drawdown: {result['max_drawdown_money']:.2f} RMB ({result['max_drawdown_percent']:.2f}%)")
            print(f"  Total Trades: {result['total_trades']}")
            print(f"  Final Portfolio Value: {result['final_value']:.2f} RMB")
            if i < len(sorted_results[:5]) - 1:
                print("-" * 40)  # 分隔线

    # 更新警告信息（尽管现在应该能算出Sharpe了）
    if sorted_results and sorted_results[0]['sharpe_ratio'] == float('-inf'):
        print("\nWarning: Sharpe Ratio calculation resulted in negative infinity for the top strategies.")
        print("This might still indicate issues like zero standard deviation in returns for the period, or negative returns.")
        print("Please review the results carefully.")
    elif not sorted_results:
        print("\nNo results found after optimization.")

    # cerebro.plot()
