import backtrader as bt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 1️⃣ 生成合成数据（含时间戳）


def create_test_data():
    # 生成时间范围（过去100天）
    start_date = datetime.now() - timedelta(days=100)
    dates = pd.date_range(start=start_date, periods=100)

    # 生成模拟价格数据（带波动）
    np.random.seed(42)  # 固定随机种子确保可重复性
    open_prices = np.linspace(100, 200, 100)
    close_prices = open_prices + np.random.normal(0, 5, 100)
    high_prices = close_prices + np.random.uniform(0, 3, 100)
    low_prices = close_prices - np.random.uniform(0, 3, 100)

    # 创建DataFrame（必须包含datetime索引）
    data = pd.DataFrame({
        'open': open_prices,
        'high': high_prices,
        'low': low_prices,
        'close': close_prices,
        'volume': np.random.randint(1000, 5000, 100)
    }, index=dates)
    return data

# 2️⃣ 定义策略


class FillDemoStrategy(bt.Strategy):
    def __init__(self):
        # 添加20日均线作为参考线
        self.sma20 = bt.indicators.SMA(period=20)

        # 配置填充规则
        self.plotlines = dict(
            close=dict(
                fill_gt=(self.sma20, 'green', 0.3),  # 收盘价大于均线时，填充绿色，透明度0.3
                fill_lt=(self.sma20, 'red', 0.3)     # 收盘价小于均线时，填充红色，透明度0.3
            ),
            sma20=dict(
                fill_gt=(150, 'blue', 0.2),          # 均线大于150时，填充蓝色，透明度0.2
                fill_lt=(150, 'orange', 0.2)         # 均线小于150时，填充橙色，透明度0.2
            )
        )


# 3️⃣ 初始化回测引擎
cerebro = bt.Cerebro()

# 4️⃣ 加载数据
data = bt.feeds.PandasData(dataname=create_test_data())
cerebro.adddata(data)

# 5️⃣ 添加策略
cerebro.addstrategy(FillDemoStrategy)

# 6️⃣ 设置初始资金和佣金
cerebro.broker.setcash(100000.0)
cerebro.broker.setcommission(commission=0.001)

# 7️⃣ 运行回测
cerebro.run()

# 8️⃣ 绘制结果（显示填充区域）
cerebro.plot(style='candle', volume=False,
             fill_between=True,  # 必须启用以显示填充
             title="Fill Demo: 收盘价与均线关系")
