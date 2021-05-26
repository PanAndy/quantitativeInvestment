from vnpy.app.cta_strategy import (
    CtaTemplate,
    StopOrder,
    TickData,
    BarData,
    TradeData,
    OrderData,
    BarGenerator,
    ArrayManager,
)
from vnpy.app.cta_strategy.base import StopOrderStatus


class DemoStrategy1(CtaTemplate):
    """"""

    author = "用Python的交易员"

    dc_length = 11
    trailing_percent = 0.8
    fixed_size = 1

    dc_up = 0
    dc_down = 0
    intra_trade_high = 0
    intra_trade_low = 0

    parameters = ["dc_length", "trailing_percent", "fixed_size"]
    variables = ["dc_up", "dc_down"]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.bg = BarGenerator(self.on_bar, 5, self.on_5min_bar)
        self.am = ArrayManager()

        self.buy_price = 0
        self.short_price = 0

        self.buy_orderids = []
        self.short_orderids = []

    def on_init(self):
        """
        Callback when strategy is inited.
        """
        self.write_log("策略初始化")
        self.load_bar(10)

    def on_start(self):
        """
        Callback when strategy is started.
        """
        self.write_log("策略启动")

    def on_stop(self):
        """
        Callback when strategy is stopped.
        """
        self.write_log("策略停止")

    def on_tick(self, tick: TickData):
        """
        Callback of new tick data update.
        """
        self.bg.update_tick(tick)

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        self.bg.update_bar(bar)

    def on_5min_bar(self, bar: BarData):
        """"""
        am = self.am
        am.update_bar(bar)
        if not am.inited:
            return

        # 计算指标
        self.dc_up, self.dc_down = am.donchian(self.dc_length)

        # 检查信号
        if not self.pos:
            self.intra_trade_high = bar.high_price
            self.intra_trade_low = bar.low_price

            # 如果没有挂过停止单，则立即发单
            if not self.buy_orderids:
                self.buy_price = self.dc_up
                self.buy_orderids = self.buy(self.dc_up, self.fixed_size, True)
            # 如果有，检查目标价格是否变化，若变了则撤单
            elif self.buy_price != self.dc_up:
                self.cancel_orders(self.buy_orderids)
            # 如果未变化，则不做操作

            if not self.short_orderids:
                self.short_price = self.dc_down
                self.short_orderids = self.short(self.dc_down, self.fixed_size, True)
            elif self.short_price != self.dc_down:
                self.cancel_orders(self.short_orderids)

        elif self.pos > 0:
            if self.buy_orderids:
                self.cancel_orders(self.buy_orderids)
            if self.short_orderids:
                self.cancel_orders(self.short_orderids)

            self.intra_trade_high = max(self.intra_trade_high, bar.high_price)
            self.intra_trade_low = bar.low_price

            long_stop = self.intra_trade_high * (1 - self.trailing_percent / 100)
            if bar.low_price <= long_stop:
                self.sell(bar.close_price - 10, abs(self.pos))

        elif self.pos < 0:
            if self.buy_orderids:
                self.cancel_orders(self.buy_orderids)
            if self.short_orderids:
                self.cancel_orders(self.short_orderids)

            self.intra_trade_high = bar.high_price
            self.intra_trade_low = min(self.intra_trade_low, bar.low_price)

            short_stop = self.intra_trade_low * (1 + self.trailing_percent / 100)
            if bar.high_price >= short_stop:
                self.cover(bar.close_price + 10, abs(self.pos))

        self.put_event()

    def on_order(self, order: OrderData):
        """
        Callback of new order data update.
        """
        pass

    def on_trade(self, trade: TradeData):
        """
        Callback of new trade data update.
        """
        self.put_event()

    def on_stop_order(self, stop_order: StopOrder):
        """
        Callback of stop order update.
        """
        # 只处理结束的停止单
        if stop_order.status == StopOrderStatus.WAITING:
            return

        # 买入停止单
        if stop_order.stop_orderid in self.buy_orderids:
            # 移除委托号
            self.buy_orderids.remove(stop_order.stop_orderid)

            # 清空停止委托价格
            if not self.buy_orderids:
                self.buy_price = 0

            # 若是撤单，且目前无仓位，则立即重发
            if stop_order.status == StopOrderStatus.CANCELLED and not self.pos:
                self.buy_price = self.dc_up
                self.buy_orderids = self.buy(self.dc_up, self.fixed_size, True)

        elif stop_order.stop_orderid in self.short_orderids:
            self.short_orderids.remove(stop_order.stop_orderid)

            if not self.short_orderids:
                self.short_price = 0

            if stop_order.status == StopOrderStatus.CANCELLED and not self.pos:
                self.short_price = self.dc_down
                self.short_orderids = self.short(self.dc_down, self.fixed_size, True)

    def cancel_orders(self, vt_orderids: list):
        """"""
        for vt_orderid in vt_orderids:
            self.cancel_order(vt_orderid)
