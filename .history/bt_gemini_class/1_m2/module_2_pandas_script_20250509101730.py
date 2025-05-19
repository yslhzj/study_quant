# module_2_pandas_script.py
from __future__ import (absolute_import, division, print_function, unicode_literals)
import backtrader as bt
import pandas as pd
import datetime,os

# --- 最小策略：用于打印数据验证 ---
class PrintDataStrategy(bt.Strategy):
     def log(self, txt, dt=None):
         dt = dt or self.datas[0].datetime.date(0)
         print(f'{dt.isoformat()} {txt}')
     def next(self):
         self.log(f'Date: {self.datas[0].datetime.date(0)}, Close: {self.datas[0].close[0]:.2f}')

if __name__ == '__main__':
    cerebro = bt.Cerebro()
    cerebro.broker.setcash(500000.0)

    # --- 使用 Pandas 加载 CSV 数据 ---
    # --- 增强数据文件路径的适应性，使其不受执行位置影响 ---
    # **__file__**: Python内置变量，表示当前脚本的文件路径。 人话翻译：“我这个脚本文件自己在哪儿”。
    # **os.path.abspath()**: 获取指定路径的绝对路径。 人话翻译：“把相对地址（比如‘我家门口那条路’）变成完整的家庭住址（比如‘XX市XX区XX街道XX号’）”。
    # **os.path.dirname()**: 获取路径中的目录部分。 人话翻译：“从完整的家庭住址里，只看在哪条街哪个小区（即文件夹）”。
    script_dir = os.path.dirname(os.path.abspath(__file__)) # 获取当前脚本文件所在的绝对目录路径，确保定位准确，就像导航找到了你脚本所在的“小区”
    # **os.path.join()**: 智能拼接路径，自动处理不同操作系统的路径分隔符（Windows用'\'，Linux/macOS用'/'）。 人话翻译：“用标准方式把‘小区地址’和‘文件名’（门牌号）安全地连起来，不会出错”。
    # 这样做的好处是，无论你从哪个文件夹位置运行这个Python脚本，它总能正确地找到与脚本文件放在同一个“小区”里的数据文件。
    data_path = os.path.join(script_dir, 'sample_data_a_share.csv') # 构建数据文件的完整、自适应路径，确保总能找到它
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