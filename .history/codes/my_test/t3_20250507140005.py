
import backtrader as bt

class DemoStrategy(bt.Strategy):
    def __init__(self):
        # 定义一根简单均线
        self.sma = bt.indicators.SMA(
            self.data,
            period=30,
        )
        # 设置 plotinfo 的所有参数
        self.sma.plotinfo.plot = True  # 1. 是否画出来，True 表示要画
        self.sma.plotinfo.subplot = True  # 2. 是否单独开小窗，True 表示单独开个小窗口
        self.sma.plotinfo.plotname = 'demo_ma'  # 3. 线的名字，图例里显示
        self.sma.plotinfo.plotskip = False  # 4. 是否跳过绘图，False 表示不跳过
        self.sma.plotinfo.plotabove = True  # 5. 是否画在主图上方，False 表示不放主图上面
        self.sma.plotinfo.plotlinelabels = True  # 6. 是否显示线名，True 表示在图上标出线名
        self.sma.plotinfo.plotlinevalues = True  # 7. 是否显示数值，True 表示在图上显示数值
        self.sma.plotinfo.plotvaluetags = True  # 8. 是否显示标签，True 表示在图上加标签
        self.sma.plotinfo.plotymargin = 0.1  # 9. y轴边距，0.1 表示上下各留10%的空白
        self.sma.plotinfo.plotyhlines = [20, 50, 80]  # 10. y轴加三条横线
        self.sma.plotinfo.plotyticks = [0, 20, 40, 60, 80, 100]  # 11. y轴刻度自定义
        self.sma.plotinfo.plothlines = [30, 70]  # 12. 图上加两条水平线
        self.sma.plotinfo.plotforce = False  # 13. 是否强制画，False 表示不强制
        self.sma.plotinfo.plotmaster = None  # 14. 主图对象，None 表示不跟随其他主图
        self.sma.plotinfo.plotylimited = True  # 15. y轴只显示本线的范围

# 后面是标准的回测流程
cerebro = bt.Cerebro()
data = bt.feeds.GenericCSVData(
    dataname='test.csv',
    dtformat=('%Y-%m-%d'),
    datetime=0, open=1, high=2, low=3, close=4,
    volume=5, openinterest=6
)
cerebro.adddata(data)
cerebro.addstrategy(DemoStrategy)
cerebro.run()
cerebro.plot()