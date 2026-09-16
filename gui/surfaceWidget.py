import numpy as np
import yfinance as yf
from typing import Any
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QSlider, QCheckBox
from PySide6.QtWidgets import QGraphicsSceneMouseEvent, QMainWindow, QLayout, QLineEdit, QFrame
from PySide6.QtWidgets import QPushButton, QVBoxLayout, QHBoxLayout, QGridLayout, QComboBox
from PySide6.QtWidgets import QStackedWidget, QGraphicsView, QGraphicsScene, QScrollArea, QSizePolicy
from PySide6.QtGui import QPainter, QFont, QPen, QColor, QBrush, QFontDatabase, QPalette, QFontMetrics
from PySide6.QtCore import QPoint, QPointF, Slot, QSize, QEventLoop, QTimer
from PySide6.QtCore import Qt
from .components import Title
from scipy.interpolate import griddata
from finance.impliedVolatility import ImpliedVolatilitySolver

from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas


class SurfaceSpace(QWidget):

    def __init__(self, terminal):
        super().__init__()

        self.terminal = terminal

        self.SurfaceLayout = QVBoxLayout(self)
        self.SurfaceLayout.setContentsMargins(0, 0, 0, 0)
        self.SurfaceLayout.setSpacing(0)

        self.title = Title(self.terminal)
        self.graph = SurfaceGraph(self.terminal)

        self.SurfaceLayout.addWidget(self.title)
        self.SurfaceLayout.addWidget(self.graph, 1)


class SurfaceGraph(FigureCanvas):

    def __init__(self, terminal):
        self.terminal = terminal

        self.figure = Figure(
            facecolor="#02080d"
        )

        self.ax = self.figure.add_subplot(
            111,
            projection="3d"
        )

        super().__init__(self.figure)

        self.setup_graph()
        self.create_surface()

    def get_risk_free_rate(self):

        try:
            treasury = yf.Ticker("^IRX")

            data = treasury.history(
                period="5d"
            )

            if data.empty:
                return 0.04

            rate = data["Close"].dropna().iloc[-1]

            return float(rate) / 100

        except Exception:
            return 0.04

    def setup_graph(self):

        self.ax.set_facecolor("#02080d")

        self.ax.tick_params(
            axis="x",
            colors="white"
        )

        self.ax.tick_params(
            axis="y",
            colors="white"
        )

        self.ax.zaxis.set_tick_params(
            colors="white"
        )

        self.ax.xaxis.label.set_color("white")
        self.ax.yaxis.label.set_color("white")
        self.ax.zaxis.label.set_color("white")

        self.ax.title.set_color("white")

        self.ax.grid(
            True,
            color="white",
            alpha=0.15
        )

        axis_x: Any = self.ax.xaxis
        axis_y: Any = self.ax.yaxis
        axis_z: Any = self.ax.zaxis

        for axis in (axis_x, axis_y, axis_z):
            axis.pane.set_facecolor("#02080d")
            axis.pane.set_edgecolor("white")

    def create_surface(self):

        ticker = yf.Ticker(
            self.terminal.ticker
        )

        expirations = ticker.options

        if not expirations:
            return

        stock_price = self.terminal.stock

        risk_free_rate = self.get_risk_free_rate()

        strikes = []
        times = []
        volatilities = []

        for expiration in expirations:

            chain = ticker.option_chain(
                expiration
            )

            if self.terminal.isPut:
                options = chain.puts
            else:
                options = chain.calls

            expiration_date = np.datetime64(
                expiration
            )

            today = np.datetime64(
                "today"
            )

            days = (
                expiration_date - today
            ).astype("timedelta64[D]").astype(int)

            T = days / 365.0

            if T <= 0:
                continue

            for _, option in options.iterrows():

                strike = option["strike"]
                bid = option["bid"]
                ask = option["ask"]

                if (
                    bid <= 0
                    or ask <= 0
                    or strike <= 0
                ):
                    continue

                market_price = (
                    bid + ask
                ) / 2

                try:

                    solver = ImpliedVolatilitySolver(
                        stock_price,
                        strike,
                        T,
                        risk_free_rate,
                        0.3,
                        market_price,
                        self.terminal.isPut
                    )

                    volatility = (
                        solver.implied_volatility()
                    )

                except Exception:
                    continue

                if not np.isfinite(volatility):
                    continue

                if volatility <= 0:
                    continue

                if volatility > 5:
                    continue

                strikes.append(strike)
                times.append(T)
                volatilities.append(volatility)

        if len(strikes) < 3:
            return

        strikes = np.array(strikes)
        times = np.array(times)
        volatilities = np.array(volatilities)

        self.plot_surface(
            strikes,
            times,
            volatilities
        )


    def plot_surface(
        self,
        strikes,
        times,
        volatilities
    ):

        self.ax.clear()
        self.setup_graph()

        # Create regular grid
        strike_grid = np.linspace(
            np.min(strikes),
            np.max(strikes),
            100
        )

        time_grid = np.linspace(
        np.min(times),
        np.max(times),
        100
        )

        K, T = np.meshgrid(
        strike_grid,
        time_grid
        )

    # Interpolate actual IV points onto grid
        IV = griddata(
        (strikes, times),
        volatilities,
        (K, T),
        method="linear"
    )

    # Plot smooth surface
        self.ax.plot_surface(
        K,
        T,
        IV,
        cmap="viridis",
        edgecolor="none",
        antialiased=True
    )

        self.ax.set_xlabel(
        "Strike Price"
    )

        self.ax.set_ylabel(
        "Time to Expiration (Years)"
    )

        self.ax.set_zlabel(
        "Implied Volatility"
    )

        option_type = (
        "Put"
        if self.terminal.isPut
        else "Call"
        )

        self.ax.set_title(
        f"{option_type} Implied Volatility Surface"
    )

        self.ax.view_init(
        elev=25,
        azim=-120
    )

        self.figure.tight_layout()

        self.draw()