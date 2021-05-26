from datetime import datetime
from typing import List, Tuple, Dict

import numpy as np
import pyqtgraph as pg
import talib

from vnpy.trader.ui import create_qapp, QtCore, QtGui, QtWidgets
from vnpy.trader.database import database_manager
from vnpy.trader.constant import Exchange, Interval
from vnpy.trader.object import BarData

from vnpy.chart import ChartWidget, VolumeItem, CandleItem
from vnpy.chart.item import ChartItem
from vnpy.chart.manager import BarManager
from vnpy.chart.base import NORMAL_FONT


class LineItem(CandleItem):
    """"""

    def __init__(self, manager: BarManager):
        """"""
        super().__init__(manager)

        self.white_pen: QtGui.QPen = pg.mkPen(color=(255, 255, 255), width=1)

    def _draw_bar_picture(self, ix: int, bar: BarData) -> QtGui.QPicture:
        """"""
        last_bar = self._manager.get_bar(ix - 1)

        # Create objects
        picture = QtGui.QPicture()
        painter = QtGui.QPainter(picture)

        # Set painter color
        painter.setPen(self.white_pen)

        # Draw Line
        end_point = QtCore.QPointF(ix, bar.close_price)

        if last_bar:
            start_point = QtCore.QPointF(ix - 1, last_bar.close_price)
        else:
            start_point = end_point

        painter.drawLine(start_point, end_point)

        # Finish
        painter.end()
        return picture


class SmaItem(CandleItem):
    """"""

    def __init__(self, manager: BarManager):
        """"""
        super().__init__(manager)

        self.blue_pen: QtGui.QPen = pg.mkPen(color=(100, 100, 255), width=2)

        self.sma_window = 10
        self.sma_data: Dict[int, float] = {}

    def get_sma_value(self, ix: int) -> float:
        """"""
        if ix < 0:
            return 0

        # When initialize, calculate all rsi value
        if not self.sma_data:
            bars = self._manager.get_all_bars()
            close_data = [bar.close_price for bar in bars]
            sma_array = talib.SMA(np.array(close_data), self.sma_window)

            for n, value in enumerate(sma_array):
                self.sma_data[n] = value

        # Return if already calcualted
        if ix in self.sma_data:
            return self.sma_data[ix]

        # Else calculate new value
        close_data = []
        for n in range(ix - self.sma_window, ix + 1):
            bar = self._manager.get_bar(n)
            close_data.append(bar.close_price)

        sma_array = talib.SMA(np.array(close_data), self.sma_window)
        sma_value = sma_array[-1]
        self.sma_data[ix] = sma_value

        return sma_value

    def _draw_bar_picture(self, ix: int, bar: BarData) -> QtGui.QPicture:
        """"""
        sma_value = self.get_sma_value(ix)
        last_sma_value = self.get_sma_value(ix - 1)

        # Create objects
        picture = QtGui.QPicture()
        painter = QtGui.QPainter(picture)

        # Set painter color
        painter.setPen(self.blue_pen)

        # Draw Line
        start_point = QtCore.QPointF(ix-1, last_sma_value)
        end_point = QtCore.QPointF(ix, sma_value)
        painter.drawLine(start_point, end_point)

        # Finish
        painter.end()
        return picture

    def get_info_text(self, ix: int) -> str:
        """"""
        if ix in self.sma_data:
            sma_value = self.sma_data[ix]
            text = f"SMA {sma_value:.1f}"
        else:
            text = "SMA -"

        return text


class RsiItem(ChartItem):
    """"""

    def __init__(self, manager: BarManager):
        """"""
        super().__init__(manager)

        self.white_pen: QtGui.QPen = pg.mkPen(color=(255, 255, 255), width=1)
        self.yellow_pen: QtGui.QPen = pg.mkPen(color=(255, 255, 0), width=2)

        self.rsi_window = 14
        self.rsi_data: Dict[int, float] = {}

    def get_rsi_value(self, ix: int) -> float:
        """"""
        if ix < 0:
            return 50

        # When initialize, calculate all rsi value
        if not self.rsi_data:
            bars = self._manager.get_all_bars()
            close_data = [bar.close_price for bar in bars]
            rsi_array = talib.RSI(np.array(close_data), self.rsi_window)

            for n, value in enumerate(rsi_array):
                self.rsi_data[n] = value

        # Return if already calcualted
        if ix in self.rsi_data:
            return self.rsi_data[ix]

        # Else calculate new value
        close_data = []
        for n in range(ix - self.rsi_window, ix + 1):
            bar = self._manager.get_bar(n)
            close_data.append(bar.close_price)

        rsi_array = talib.RSI(np.array(close_data), self.rsi_window)
        rsi_value = rsi_array[-1]
        self.rsi_data[ix] = rsi_value

        return rsi_value

    def _draw_bar_picture(self, ix: int, bar: BarData) -> QtGui.QPicture:
        """"""
        rsi_value = self.get_rsi_value(ix)
        last_rsi_value = self.get_rsi_value(ix - 1)

        # Create objects
        picture = QtGui.QPicture()
        painter = QtGui.QPainter(picture)

        # Draw RSI line
        painter.setPen(self.yellow_pen)

        end_point = QtCore.QPointF(ix, rsi_value)
        start_point = QtCore.QPointF(ix - 1, last_rsi_value)
        painter.drawLine(start_point, end_point)

        # Draw oversold/overbought line
        painter.setPen(self.white_pen)

        painter.drawLine(
            QtCore.QPointF(ix, 70),
            QtCore.QPointF(ix - 1, 70),
        )

        painter.drawLine(
            QtCore.QPointF(ix, 30),
            QtCore.QPointF(ix - 1, 30),
        )

        # Finish
        painter.end()
        return picture

    def boundingRect(self) -> QtCore.QRectF:
        """"""
        min_price, max_price = self._manager.get_price_range()
        rect = QtCore.QRectF(
            0,
            0,
            len(self._bar_picutures),
            100
        )
        return rect

    def get_y_range(
        self, min_ix: int = None, max_ix: int = None
    ) -> Tuple[float, float]:
        """"""
        return 0, 100

    def get_info_text(self, ix: int) -> str:
        """"""
        if ix in self.rsi_data:
            rsi_value = self.rsi_data[ix]
            text = f"RSI {rsi_value:.1f}"
        else:
            text = "RSI -"

        return text


class NewChartWidget(ChartWidget):
    """"""
    MIN_BAR_COUNT = 100

    def __init__(self, parent: QtWidgets.QWidget = None):
        """"""
        super().__init__(parent)

        self.last_price_line: pg.InfiniteLine = None

    def add_last_price_line(self):
        """"""
        plot = list(self._plots.values())[0]
        color = (255, 255, 255)

        self.last_price_line = pg.InfiniteLine(
            angle=0,
            movable=False,
            label="{value:.1f}",
            pen=pg.mkPen(color, width=1),
            labelOpts={
                "color": color,
                "position": 1,
                "anchors": [(1, 1), (1, 1)]
            }
        )
        self.last_price_line.label.setFont(NORMAL_FONT)
        plot.addItem(self.last_price_line)

    def update_history(self, history: List[BarData]) -> None:
        """
        Update a list of bar data.
        """
        self._manager.update_history(history)

        for item in self._items.values():
            item.update_history(history)

        self._update_plot_limits()

        self.move_to_right()

        self.update_last_price_line(history[-1])

    def update_bar(self, bar: BarData) -> None:
        """
        Update single bar data.
        """
        self._manager.update_bar(bar)

        for item in self._items.values():
            item.update_bar(bar)

        self._update_plot_limits()

        if self._right_ix >= (self._manager.get_count() - self._bar_count / 2):
            self.move_to_right()

        self.update_last_price_line(bar)

    def update_last_price_line(self, bar: BarData) -> None:
        """"""
        if self.last_price_line:
            self.last_price_line.setValue(bar.close_price)


if __name__ == "__main__":
    app = create_qapp()

    bars = database_manager.load_bar_data(
        "IF888",
        Exchange.CFFEX,
        interval=Interval.MINUTE,
        start=datetime(2019, 7, 1),
        end=datetime(2019, 7, 17)
    )

    widget = NewChartWidget()
    widget.add_plot("candle", hide_x_axis=True)
    widget.add_plot("volume", maximum_height=200)
    widget.add_plot("rsi", maximum_height=200)
    widget.add_item(CandleItem, "candle", "candle")
    widget.add_item(VolumeItem, "volume", "volume")

    # widget.add_item(LineItem, "line", "candle")
    widget.add_item(SmaItem, "sma", "candle")
    widget.add_item(RsiItem, "rsi", "rsi")
    widget.add_last_price_line()
    widget.add_cursor()

    n = 1000
    history = bars[:n]
    new_data = bars[n:]

    widget.update_history(history)

    def update_bar():
        bar = new_data.pop(0)
        widget.update_bar(bar)

    timer = QtCore.QTimer()
    timer.timeout.connect(update_bar)
    timer.start(100)

    widget.show()
    app.exec_()
