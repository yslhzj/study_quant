#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2015-2023 Daniel Rodriguez
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)


import collections

import backtrader as bt
from backtrader.utils.py3 import items, iteritems

from . import TimeReturn, PositionsValue, Transactions, GrossLeverage


class PyFolio(bt.Analyzer):
    '''This analyzer uses 4 children analyzers to collect data and transforms it
    in to a data set compatible with ``pyfolio``

    Children Analyzer

      - ``TimeReturn``

        Used to calculate the returns of the global portfolio value

      - ``PositionsValue``

        Used to calculate the value of the positions per data. It sets the
        ``headers`` and ``cash`` parameters to ``True``

      - ``Transactions``

        Used to record each transaction on a data (size, price, value). Sets
        the ``headers`` parameter to ``True``

      - ``GrossLeverage``

        Keeps track of the gross leverage (how much the strategy is invested)

    Params:
      These are passed transparently to the children

      - timeframe (default: ``bt.TimeFrame.Days``)

        If ``None`` then the timeframe of the 1st data of the system will be
        used

      - compression (default: `1``)

        If ``None`` then the compression of the 1st data of the system will be
        used

    Both ``timeframe`` and ``compression`` are set following the default
    behavior of ``pyfolio`` which is working with *daily* data and upsample it
    to obtaine values like yearly returns.

    Methods:

      - get_analysis

        Returns a dictionary with returns as values and the datetime points for
        each return as keys
    '''
    params = (
        ('timeframe', bt.TimeFrame.Days),
        ('compression', 1)
    )

    def __init__(self):
        dtfcomp = dict(timeframe=self.p.timeframe,
                       compression=self.p.compression)

        self._returns = TimeReturn(**dtfcomp)
        self._positions = PositionsValue(headers=True, cash=True)
        self._transactions = Transactions(headers=True)
        self._gross_lev = GrossLeverage()

    def stop(self):
        super(PyFolio, self).stop()
        self.rets['returns'] = self._returns.get_analysis()
        self.rets['positions'] = self._positions.get_analysis()
        self.rets['transactions'] = self._transactions.get_analysis()
        self.rets['gross_lev'] = self._gross_lev.get_analysis()

    def get_pf_items(self):
        '''Returns a tuple of 4 elements which can be used for further processing with
          ``pyfolio``

          returns, positions, transactions, gross_leverage

        Because the objects are meant to be used as direct input to ``pyfolio``
        this method makes a local import of ``pandas`` to convert the internal
        *backtrader* results to *pandas DataFrames* which is the expected input
        by, for example, ``pyfolio.create_full_tear_sheet``

        The method will break if ``pandas`` is not installed
        '''
        # keep import local to avoid disturbing installations with no pandas
        import pandas
        from pandas import DataFrame as DF
        import numpy as np

        #
        # Returns
        cols = ['index', 'return']
        # 使用 items() 替代 iteritems() 来兼容新版 pandas
        try:
            returns = DF.from_records(self.rets['returns'].items() if hasattr(self.rets['returns'], 'items')
                                      else list(self.rets['returns'].items()),
                                      index=cols[0], columns=cols)
        except AttributeError:
            # 如果是字典类型，则使用字典的 items() 方法
            returns = DF.from_records(list(self.rets['returns'].items()),
                                      index=cols[0], columns=cols)

        # 确保日期索引正确处理
        returns.index = pandas.to_datetime(returns.index)
        try:
            # 尝试添加时区信息，但捕获可能的异常
            returns.index = returns.index.tz_localize('UTC')
        except:
            # 如果已经有时区信息，使用 tz_convert 而不是 tz_localize
            try:
                returns.index = returns.index.tz_convert('UTC')
            except:
                pass  # 如果无法转换，保持原样

        rets = returns['return']

        #
        # Positions
        pss = self.rets['positions']
        # 使用 items() 替代 iteritems()
        try:
            ps = [[k] + v[-2:]
                  for k, v in (pss.items() if hasattr(pss, 'items') else pss.items())]
        except AttributeError:
            ps = [[k] + v[-2:] for k, v in list(pss.items())]

        cols = ps.pop(0)  # headers are in the first entry
        positions = DF.from_records(ps, index=cols[0], columns=cols)

        # 确保日期索引正确处理
        positions.index = pandas.to_datetime(positions.index)
        try:
            positions.index = positions.index.tz_localize('UTC')
        except:
            try:
                positions.index = positions.index.tz_convert('UTC')
            except:
                pass

        #
        # Transactions
        txss = self.rets['transactions']
        txs = list()
        # The transactions have a common key (date) and can potentially happend
        # for several assets. The dictionary has a single key and a list of
        # lists. Each sublist contains the fields of a transaction
        # Hence the double loop to undo the list indirection
        # 使用 items() 替代 iteritems()
        try:
            for k, v in (txss.items() if hasattr(txss, 'items') else txss.items()):
                for v2 in v:
                    txs.append([k] + v2)
        except AttributeError:
            for k, v in list(txss.items()):
                for v2 in v:
                    txs.append([k] + v2)

        cols = txs.pop(0)  # headers are in the first entry
        transactions = DF.from_records(txs, index=cols[0], columns=cols)

        # 确保日期索引正确处理
        transactions.index = pandas.to_datetime(transactions.index)
        try:
            transactions.index = transactions.index.tz_localize('UTC')
        except:
            try:
                transactions.index = transactions.index.tz_convert('UTC')
            except:
                pass

        # Gross Leverage
        cols = ['index', 'gross_lev']
        # 使用 items() 替代 iteritems()
        try:
            gross_lev = DF.from_records(self.rets['gross_lev'].items() if hasattr(self.rets['gross_lev'], 'items')
                                        else list(self.rets['gross_lev'].items()),
                                        index=cols[0], columns=cols)
        except AttributeError:
            gross_lev = DF.from_records(list(self.rets['gross_lev'].items()),
                                        index=cols[0], columns=cols)

        # 确保日期索引正确处理
        gross_lev.index = pandas.to_datetime(gross_lev.index)
        try:
            gross_lev.index = gross_lev.index.tz_localize('UTC')
        except:
            try:
                gross_lev.index = gross_lev.index.tz_convert('UTC')
            except:
                pass

        glev = gross_lev['gross_lev']

        # Return all together
        return rets, positions, transactions, glev
