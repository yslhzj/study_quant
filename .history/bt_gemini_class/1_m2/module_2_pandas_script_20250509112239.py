# module_3_script.py
from __future__ import (absolute_import, division, print_function, unicode_literals)
import backtrader as bt
import pandas as pd
import datetime , os

# --- 策略定义 ---
class LoggingStrategy(bt.Strategy):
    def log(self, txt, dt=None):
        # 日志记录函数
        dt = dt or self.data.datetime.date(0) # 使用数据馈送的日期
        print(f'{dt.isoformat()}, {txt}')

    def __init__(self):
        # 在初始化时保存对数据线的引用，方便后续访问
        self.dt = self.data.datetime
        self.open = self.data.open
        self.high = self.data.high
        self.low = self.data.low
        self.close = self.data.close
        self.volume = self.data.volume
        print("--- Strategy Initialized ---")
        # 打印数据源信息 (如果dataname在PandasData中被传递)
        if hasattr(self.data.p, 'dataname') and isinstance(self.data.p.dataname, pd.DataFrame):
             # 对于PandasData, dataname是DataFrame本身, 可能没有简单的名称属性
             # 可以考虑在加载数据时给数据馈送命名: cerebro.adddata(data_feed, name='MyStock')
             # 然后通过 self.data.p.name 访问
             print(f"Data Source: Pandas DataFrame (Index: {self.data.p.dataname.index.name})")
        elif hasattr(self.data.p, 'dataname'):
             print(f"Data Source: {self.data.p.dataname}")


    def start(self):
        # 回测开始时调用
        print("--- Backtest Starting ---")
        print(f"Initial Portfolio Value: {self.broker.getvalue():.2f} RMB")

    def next(self):
        # 每个数据点调用一次
        # 记录当前Bar的OHLCV数据
        log_msg = (
            f"Open: {self.open:.2f}, High: {self.high:.2f}, "
            f"Low: {self.low:.2f}, Close: {self.close:.2f}, "
            f"Volume: {self.volume:.0f}"
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
    script_dir = os.path.dirname(os.path.abspath(__file__)); data_path = os.path.join(script_dir, 'sample_data_a_share.csv')
    df = pd.read_csv(data_path, parse_dates=True, index_col='Date')
    data_feed = bt.feeds.PandasData(
        dataname=df,
        fromdate=datetime.datetime(2023, 1, 1),
        todate=datetime.datetime(2023, 1, 10) # 使用较短周期以便观察日志
    )
    cerebro.adddata(data_feed, name='SampleStock') # 给数据馈送命名

    # --- 添加策略 ---
    cerebro.addstrategy(LoggingStrategy)

    # 不再在这里打印初始值，策略的 start() 方法会打印
    # print(f'Starting Portfolio Value: {cerebro.broker.getvalue():.2f} RMB')
    cerebro.run()
    # 最终值由策略的 stop() 方法打印