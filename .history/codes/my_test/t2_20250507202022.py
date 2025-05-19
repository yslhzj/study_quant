import backtrader as bt
import matplotlib.pyplot as plt
import pandas as pd
# 生成测试数据
data = bt.feeds.PandasData(
    dataname=pd.DataFrame({
        'close': [i for i in range(1, 101)]  # 1~100的直线
    })
)


class TestIndicator(bt.Indicator):
    params = (('threshold', 60), )

    def _plotinit(self):
        # 在阈值处画红线
        self.plotinfo.plotyhlines = [self.p.threshold]
        self.plotinfo.plotyhlines_colors = ['red']

    def next(self):
        self.line[0] = self.data.close[0]  # 简单复制价格

# 新增策略类，最小化修改


class MyStrategy(bt.Strategy):
    def __init__(self):
        # 在策略中添加自定义指标
        self.testind = TestIndicator(self.data, threshold=70)  # 修改阈值


# 运行测试
cerebro = bt.Cerebro()
cerebro.adddata(data)
cerebro.addstrategy(MyStrategy)  # 添加策略
cerebro.run()
cerebro.plot(iplot=False)  # 禁用内联绘图
plt.show()  # 会显示一条从1到100的线，并在y=70处有红色水平线
