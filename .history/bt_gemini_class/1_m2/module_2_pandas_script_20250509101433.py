# module_2_pandas_script.py
from __future__ import (absolute_import, division, print_function, unicode_literals)
import backtrader as bt
import pandas as pd
import datetime

# --- 最小策略：用于打印数据验证 ---
class PrintDataStrategy(bt.Strategy):
     def log(self, txt, dt=None):
         dt = dt or self.datas.datetime.date(0)
         print(f'{dt.isoformat()} {txt}')
     def next(self):
         self.log(f'Date: {self.datas.datetime.date(0)}, Close: {self.datas.close:.2f}')

if __name__ == '__main__':
    cerebro = bt.Cerebro()
    cerebro.broker.setcash(500000.0)

    # --- 使用 Pandas 加载 CSV 数据 ---
    data_path = 'sample_data_a_share.csv'
    df = pd.read_csv(
        data_path,
        parse_dates=True,  # 自动尝试解析日期列
        index_col='Date'   # 将 'Date' 列设为索引
    )

    # --- 从 DataFrame 创建 Backtrader 数据馈送 ---
    data_feed = bt.feeds.PandasData(
        dataname=df, # 直接传递 DataFrame
        fromdate=datetime.datetime(2023, 1, 1),
        todate=datetime.datetime(2023, 1, 10),
        # Backtrader 会自动映射索引为 datetime
        # 并尝试自动映射 'Open', 'High', 'Low', 'Close', 'Volume' 列名
        # 如果列名不同，需要手动指定，例如: open='PriceOpen', high='PriceHigh', etc.
        openinterest=-1 # 显式指定没有持仓量
    )

    cerebro.adddata(data_feed)
    cerebro.addstrategy(PrintDataStrategy)

    print(f'Starting Portfolio Value: {cerebro.broker.getvalue():.2f} RMB')
    print("Running Cerebro with Pandas data...")
    cerebro.run()
    print("Cerebro run complete.")
    print(f'Final Portfolio Value: {cerebro.broker.getvalue():.2f} RMB')