# module_1_script.py
from __future__ import (absolute_import, division, print_function, unicode_literals)
import backtrader as bt
import datetime # 导入datetime模块，虽然暂时不用，但后续会用到

if __name__ == '__main__':
    # 1. 创建 Cerebro 引擎实例
    cerebro = bt.Cerebro()

    # 2. 设置初始资金
    start_cash = 500000.0 # 用户指定的初始资金 50万 RMB
    cerebro.broker.setcash(start_cash)

    # 3. 打印初始投资组合价值
    print(f'Starting Portfolio Value: {cerebro.broker.getvalue():.2f} RMB')

    # 4. 运行回测 (但目前没有数据和策略)
    print("Running Cerebro...")
    cerebro.run()
    print("Cerebro run complete.")

    # 5. 打印最终投资组合价值
    print(f'Final Portfolio Value: {cerebro.broker.getvalue():.2f} RMB')