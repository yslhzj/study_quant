# module_2_script.py
from __future__ import (absolute_import, division, print_function, unicode_literals)
import backtrader as bt
import datetime

# --- 定义数据馈送类 ---
# 通过继承 GenericCSVData 来自定义CSV格式
class CSVDailyData(bt.feeds.GenericCSVData):
    params = (
        ('dtformat', '%Y-%m-%d'), # 日期格式 YYYY-MM-DD
        ('datetime', 0),         # 日期在第1列 (索引0)
        ('open', 1),             # 开盘价在第2列
        ('high', 2),             # 最高价在第3列
        ('low', 3),              # 最低价在第4列
        ('close', 4),            # 收盘价在第5列
        ('volume', 5),           # 成交量在第6列
        ('openinterest', -1),    # 无持仓量数据
        ('nullvalue', 0.0)       # 用0.0填充缺失值 (根据实际情况调整)
    )

# --- 最小策略：用于打印数据验证 ---
class PrintDataStrategy(bt.Strategy):
     def log(self, txt, dt=None):
         dt = dt or self.datas[0].datetime.date[0]
         print(f'{dt.isoformat()} {txt}')
     def next(self):
         # 打印当前bar的日期和收盘价
        self.log(f'Date: {self.datas[0].datetime.date(0)}, Close: {self.datas[0].close[0]:.2f}')

if __name__ == '__main__':
    cerebro = bt.Cerebro()
    cerebro.broker.setcash(500000.0)

    # --- 加载数据 ---
    data_path = r'bt_gemini_class\1_m2\sample_data_a_share.csv' # 确保这个文件存在且包含数据
    data_feed = CSVDailyData(
        dataname=data_path,
        fromdate=datetime.datetime(2023, 1, 1), # 加载数据的起始日期
        todate=datetime.datetime(2023, 1, 10)   # 加载数据的结束日期 (示例用较短周期)
    )

    # --- 将数据添加到 Cerebro ---
    cerebro.adddata(data_feed)

    # --- 添加打印策略 ---
    cerebro.addstrategy(PrintDataStrategy)

    print(f'Starting Portfolio Value: {cerebro.broker.getvalue():.2f} RMB')
    print("Running Cerebro with data...")
    cerebro.run()
    print("Cerebro run complete.")
    # 最终价值仍然不变，因为策略只打印数据，不交易
    print(f'Final Portfolio Value: {cerebro.broker.getvalue():.2f} RMB')