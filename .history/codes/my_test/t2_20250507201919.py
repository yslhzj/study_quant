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

# 运行测试
cerebro = bt.Cerebro()
cerebro.adddata(data)
cerebro.addindicator(TestIndicator(threshold=70))  # 修改阈值
cerebro.run()
cerebro.plot(iplot=False)  # 禁用内联绘图
plt.show()  # 会显示一条从1到100的线，并在y=70处有红色水平线