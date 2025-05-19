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


# 修改后的性能分析器实现
class SharpeRatioWithDrawdown(bt.Analyzer):
    params = (
        ('timeframe', bt.TimeFrame.Years),
        ('compression', 1),
        ('riskfreerate', 0.01),
    )

    def start(self):
        # 不再尝试添加其他分析器
        pass

    def stop(self):
        pass

    def get_analysis(self):
        # 直接从策略中获取其他分析器的结果
        # 使用getattr避免属性不存在时出错
        ret_analyzer = getattr(self.strategy.analyzers, 'returns', None)
        sharpe_analyzer = getattr(self.strategy.analyzers, 'sharpe', None)
        dd_analyzer = getattr(self.strategy.analyzers, 'drawdown', None)

        # 增强的空值处理
        try:
            # 获取收益率，确保数值有效
            if ret_analyzer:
                ret_analysis = ret_analyzer.get_analysis()
                ret = ret_analysis.get('rtot', 0.0) if ret_analysis else 0.0
            else:
                ret = 0.0

            # 获取夏普比率，确保数值有效
            if sharpe_analyzer:
                sharpe_analysis = sharpe_analyzer.get_analysis()
                sharpe = sharpe_analysis.get(
                    'sharperatio', 0.0) if sharpe_analysis else 0.0
            else:
                sharpe = 0.0

            # 获取最大回撤，确保数值有效
            if dd_analyzer:
                dd_analysis = dd_analyzer.get_analysis()
                max_dd = dd_analysis.get('max', {}) if dd_analysis else {}
                dd = max_dd.get('drawdown', 0.0) if isinstance(
                    max_dd, dict) else 0.0
            else:
                dd = 0.0

            # 确保所有值都是数值类型
            ret = float(ret) if ret is not None else 0.0
            sharpe = float(sharpe) if sharpe is not None else 0.0
            dd = float(dd) if dd is not None else 0.0

            # 计算综合得分
            score = sharpe - dd * 0.5

        except Exception as e:
            # 出现任何异常都使用默认值
            ret = 0.0
            sharpe = 0.0
            dd = 0.0
            score = 0.0
            print(f"分析器计算出错: {str(e)}")

        return {
            'returns': ret,
            'sharpe': sharpe,
            'drawdown': dd,
            'score': score  # 综合评分
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

    # 减少参数空间，提高优化效率
    cerebro.optstrategy(
        SmaCrossADXFilter,
        fast_ma_period=[5, 10, 15],        # 减少搜索范围
        slow_ma_period=[20, 30, 40],       # 减少搜索范围
        adx_period=[10, 14, 18],           # 保持不变
        adx_threshold=[20, 25, 30]         # 减少搜索范围
    )

    # 添加所有必要的分析器
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
    cerebro.addanalyzer(bt.analyzers.SharpeRatio_A, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')

    # 添加我们的综合分析器
    cerebro.addanalyzer(SharpeRatioWithDrawdown, _name='sharpe_dd')

    try:
        # 运行优化
        print('开始参数优化...')
        results = cerebro.run(maxcpus=1)

        # 分析结果
        best_result = None
        best_score = -999
        best_params = None

        for r in results:
            try:
                analyzer = r[0].analyzers.sharpe_dd.get_analysis()
                score = analyzer.get('score', 0)

                # 添加调试信息，输出每组参数的得分
                params = r[0].params
                print(
                    f"参数组合: 快均线={params.fast_ma_period}, 慢均线={params.slow_ma_period}, ADX周期={params.adx_period}, ADX阈值={params.adx_threshold}, 得分={score:.4f}")

                if score > best_score:
                    best_score = score
                    best_result = r[0]
                    best_params = r[0].params
            except Exception as e:
                print(f"处理结果时出错: {str(e)}")
                continue

        if best_params:
            print('最优参数组合:')
            print(f'快速均线周期: {best_params.fast_ma_period}')
            print(f'慢速均线周期: {best_params.slow_ma_period}')
            print(f'ADX周期: {best_params.adx_period}')
            print(f'ADX阈值: {best_params.adx_threshold}')

            # 获取分析结果
            analysis = best_result.analyzers.sharpe_dd.get_analysis()
            print(f'收益率: {analysis["returns"]:.2%}')
            print(f'夏普比率: {analysis["sharpe"]:.2f}')
            print(f'最大回撤: {analysis["drawdown"]:.2%}')

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

            # 添加分析器来显示最终回测结果
            cerebro_best.addanalyzer(bt.analyzers.Returns, _name='returns')
            cerebro_best.addanalyzer(
                bt.analyzers.SharpeRatio_A, _name='sharpe')
            cerebro_best.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')

            print('使用最优参数运行回测...')
            print(f'初始资金: {cerebro_best.broker.getvalue():.2f} RMB')
            run_result = cerebro_best.run()
            strat = run_result[0]

            # 显示回测结果
            final_value = cerebro_best.broker.getvalue()
            print(f'最终资金: {final_value:.2f} RMB')
            print(f'总收益率: {(final_value/500000.0 - 1.0):.2%}')

            try:
                ret_analysis = strat.analyzers.returns.get_analysis()
                ret_value = ret_analysis.get("rtot", 0.0)
                if ret_value is not None:
                    print(f'回测收益率: {ret_value:.2%}')
                else:
                    print('回测收益率: 无法获取')

                sharpe_analysis = strat.analyzers.sharpe.get_analysis()
                sharpe_value = sharpe_analysis.get("sharperatio", 0.0)
                if sharpe_value is not None:
                    print(f'回测夏普比率: {sharpe_value:.2f}')
                else:
                    print('回测夏普比率: 无法获取')

                dd_analysis = strat.analyzers.drawdown.get_analysis()
                max_dd = dd_analysis.get('max', {})
                dd_value = max_dd.get("drawdown", 0.0)
                if dd_value is not None:
                    print(f'回测最大回撤: {dd_value:.2%}')
                else:
                    print('回测最大回撤: 无法获取')
            except Exception as e:
                print(f"获取回测分析结果时出错: {str(e)}")

            # 绘制图表
            cerebro_best.plot(style='candlestick')
        else:
            print("优化过程未找到有效的参数组合")
    except Exception as e:
        print(f"程序执行出错: {str(e)}")
