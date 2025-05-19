# module_2_pandas_script.py
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
import backtrader as bt
import pandas as pd
import datetime
import os

# --- 策略定义 ---


class LoggingStrategy(bt.Strategy):
    def log(self, txt, dt=None):
        # 日志记录函数
        dt = dt or self.datas[0].datetime.date(0)  # 使用数据馈送的日期
        print(f'{dt.isoformat()}, {txt}')

    def __init__(self):
        # 在初始化时保存对数据线的引用，方便后续访问
        self.dt = self.datas[0].datetime
        self.open = self.datas[0].open
        self.high = self.datas[0].high
        self.low = self.datas[0].low
        self.close = self.datas[0].close
        self.volume = self.datas[0].volume
        print("--- Strategy Initialized ---")
        # 打印数据源信息 (如果dataname在PandasData中被传递)
        if hasattr(self.datas[0].p, 'dataname') and isinstance(self.datas[0].p.dataname, pd.DataFrame):
            # 对于PandasData, dataname是DataFrame本身, 可能没有简单的名称属性
            # 可以考虑在加载数据时给数据馈送命名: cerebro.adddata(data_feed, name='MyStock')
            # 然后通过 self.data.p.name 访问
            print(
                f"Data Source: Pandas DataFrame (Index: {self.datas[0].p.dataname.index.name})")
        elif hasattr(self.datas[0].p, 'dataname'):
            print(f"Data Source: {self.datas[0].p.dataname}")

    def start(self):
        # 回测开始时调用
        print("--- Backtest Starting ---")
        print(f"Initial Portfolio Value: {self.broker.getvalue():.2f} RMB")

    def next(self):
        # 每个数据点调用一次
        # 记录当前Bar的OHLCV数据
        log_msg = (
            f"Open: {self.open[0]:.2f}, High: {self.high[0]:.2f}, "
            f"Low: {self.low[0]:.2f}, Close: {self.close[0]:.2f}, "
            f"Volume: {self.volume[0]:.0f}"
        )
        self.log(log_msg)

    def stop(self):
        # 回测结束时调用
        print("--- Backtest Finished ---")
        print(f"Final Portfolio Value: {self.broker.getvalue():.2f} RMB")


if __name__ == '__main__':
    cerebro = bt.Cerebro()
    cerebro.broker.setcash(500000.0)

    # --- 加载数据 (使用 PandasData) ---
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(script_dir, 'sample_data_a_share.csv')
    df = pd.read_csv(data_path, parse_dates=True, index_col='Date')
    data_feed = bt.feeds.PandasData(
        dataname=df,
        fromdate=datetime.datetime(2023, 1, 1),
        todate=datetime.datetime(2023, 1, 10)  # 使用较短周期以便观察日志
    )
    cerebro.adddata(data_feed, name='SampleStock')  # 给数据馈送命名

    # --- 添加策略 ---
    cerebro.addstrategy(LoggingStrategy)

    # 不再在这里打印初始值，策略的 start() 方法会打印
    # print(f'Starting Portfolio Value: {cerebro.broker.getvalue():.2f} RMB')
    cerebro.run()
    # 最终值由策略的 stop() 方法打印
