
plotinfo = dict(
                # 一、绘图基本控制 (这部分是管图画不画，画在哪，叫啥名儿的基本设定)
                plot=True,
                # 控制是否绘制该指标或数据 (就是说，这个东西到底画不画出来)
                subplot=True,
                # 控制是否在独立的子图中绘制 (是不是给它单独开个小窗户，而不是跟K线挤一块儿)
                plotname='',
                # 设置图表的显示名称 (给这幅图起个名字，显示在图上)
                plotskip=False,
                # 控制是否跳过绘制该指标 (临时不想看这个指标了，可以暂时不画它，但指标还在)

                # 二、绘图元素与布局 (这部分是管图上具体显示哪些信息，以及这些信息怎么摆)
                plotabove=False,
                # 控制是否将绘图绘制在主数据之上 (是画在K线图的上面还是下面)
                plotlinelabels=False,
                # 控制是否为线条显示标签 (线条旁边要不要显示这条线是啥，比如"MA5")
                plotlinevalues=True,
                # 控制是否在图表上显示线条的数值 (要不要在线上直接标出当前的具体数值)
                plotvaluetags=True,
                # 控制是否为线条上的数值显示标签/标记 (数值旁边要不要加个小标记，让它更显眼)

                # 三、Y轴显示控制 (这部分是专门管Y轴怎么显示的)
                plotymargin=0.0,
                # 设置Y轴的边距 (Y轴上下两边留多少空白，0就是不留)
                plotyhlines=[],
                # 在Y轴上绘制水平线，值为列表中的数值 (在Y轴的某些刻度上画几条横线，比如在50、100的位置画线)
                plotyticks=[],
                # 自定义Y轴的刻度标记 (Y轴上具体显示哪些刻度值，比如只显示0, 50, 100)
                plotylimited=True,
                # 控制Y轴的范围是否仅限于当前绘图对象的值 (Y轴的显示范围是不是就根据当前画的这条线来定，不高不低正合适)

                # 四、高级绘图选项 (这部分是一些更细致或者特殊的绘图控制)
                plothlines=[],
                # 在图表上根据数据值绘制水平线 (在图表上画横线，但这个线是根据指标本身的数值来的，不是固定的Y轴刻度)
                plotforce=False,
                # 控制是否强制绘图，即使在某些情况下可能被跳过 (不管三七二十一，强制要画出来)
                plotmaster=None,
                # 指定一个主绘图对象，当前绘图将依附于主对象 (如果这个图是某个主图的附属，这里就指定老大是谁)
           )
import backtrader as bt

class DemoStrategy(bt.Strategy):
    def __init__(self):
        self.sma = bt.indicators.SMA(self.data, period=10)
        self.pct = bt.indicators.PctChange(self.data.close, period=1)
        
        # 1. 均线和主K线画在一起
        self.sma.plotinfo.subplot = False  # 不单独开小窗
        self.sma.plotinfo.plotmaster = self.data  # 跟随主K线画
        
        # 2. 涨跌幅单独开小窗，y轴只看自己
        self.pct.plotinfo.subplot = True  # 单独开小窗
        self.pct.plotinfo.plotylimited = True  # y轴只看自己

# 后面是标准回测流程
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