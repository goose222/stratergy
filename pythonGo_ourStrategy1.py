# encoding: UTF-8

from __future__ import division
from ctaTemplate import *
import datetime


class ourstrategy(CtaTemplate):
    """our"""
    # 参数列表
    # 填写合约列表和交易所时，使用“;”分开，如
    # ag1812;a1809
    # SHFE;DCE
    paramList = ['vtSymbol',
                 'price_spread',]

    # 变量列表
    varList = ['trading',
               'time',
               'pos']

    # 参数映射表
    paramMap = {'vtSymbol': u'合约列表',
                'price_spread': u'价差',}

    # 变量映射表
    varMap = {'trading': u'交易中',
              'time': u'当前时间',
              'pos': u'当前持仓'}

    def __init__(self, ctaEngine=None, setting={}):
        """Constructor"""
        super(ourstrategy, self).__init__(ctaEngine, setting)
        self.price_spread = 5
        self.time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        self.tick_symbol_1 = VtTickData()
        self.tick_symbol_2 = VtTickData()
        # 标注上一个报单是否已被撤单
        self.has_canceled = False
        self.order1 = '00'
        self.order2 = '00'

    def onTick(self, tick):
        super(ourstrategy, self).onTick(tick)
        #self.output(u'ontick!!!')
        # 过滤涨跌停和集合竞价
        if tick.lastPrice == 0 or tick.askPrice1 == 0 or tick.bidPrice1 == 0:
            return

        # 更新时间，推送状态
        self.time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.putEvent()

        # 分别缓存不同合约的上一个tick
        if tick.vtSymbol == self.symbolList[0]:
            self.tick_symbol_1 = tick

        if tick.vtSymbol == self.symbolList[1]:
            self.tick_symbol_2 = tick

        # 计算交易信号
        self.get_signal(self.tick_symbol_1, self.tick_symbol_2)

        # 执行交易信号
        self.exec_signal(self.tick_symbol_1, self.tick_symbol_2)


    def get_signal(self, tick1, tick2):
        if tick2.lastPrice - tick1.lastPrice >= self.price_spread + 20:
            self.buySig = True

    def exec_signal(self, tick1, tick2):
        if self.buySig:
            # 第一个tick推过来肯定是龙一的tick，所以此时需要确保缓存的龙二的tick数据不为空
            if tick2.lastPrice > 0 and self.pos.get(self.symbolList[1])!=0 and self.order1 is not None:
                self.cover(tick2.lastPrice, -self.pos.get(self.symbolList[1]), symbol=self.symbolList[1])

            if tick1.lastPrice > 0 and self.pos.get(self.symbolList[0])!=0 and self.order2 is not None:
                self.sell(tick1.lastPrice, self.pos.get(self.symbolList[0]), symbol=self.symbolList[0])

            if self.pos.get(self.symbolList[0]) == 0 and self.pos.get(self.symbolList[1]) == 0:
                self.onStop()

            self.has_canceled = False

    def onTrade(self, trade, log=True):
        super(ourstrategy, self).onTrade(trade, log)

    def onOrder(self, order, log=False):
        super(ourstrategy, self).onOrder(order, log)
        if order is None:
            return None
        if (order.status == u'未成交') :
            if self.symbolList[1]==order.vtSymbol:
                self.order1=None
            if self.symbolList[0]==order.vtSymbol:
                self.order2 = None

    def onStart(self):
        super(ourstrategy, self).onStart()
        self.manage_position()

    def onStop(self):
        super(ourstrategy, self).onStop()