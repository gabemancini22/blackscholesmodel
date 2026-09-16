import sys
import os
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QSlider, QCheckBox
from PySide6.QtWidgets import QGraphicsSceneMouseEvent, QMainWindow, QLayout, QLineEdit, QFrame
from PySide6.QtWidgets import QPushButton, QVBoxLayout, QHBoxLayout, QGridLayout, QComboBox
from PySide6.QtWidgets import QStackedWidget, QGraphicsView, QGraphicsScene, QScrollArea, QSizePolicy
from pathlib import Path
from PySide6.QtGui import QPainter, QFont, QPen, QColor, QBrush, QFontDatabase, QPalette, QFontMetrics
from PySide6.QtCore import QPoint, QPointF, Slot, QSize, QEventLoop, QTimer
from PySide6.QtCore import Qt
import numpy as np
import scipy
import statistics
import matplotlib
import yfinance as yf
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from finance.monteCarlo import MonteCarlo
from .components import Title, SubTitle
import pandas as pd

class MonteCarloSpace(QWidget):
    def __init__(self, terminal, row):
        super().__init__()
        self.terminal = terminal
        self.row = row
        self.information = self.terminal.chain.iloc[self.row]
        self.marketPrice = self.information["marketPrice"]
        self.showProfit = False

        self.r = MonteCarlo.calculateRiskFreeRate(self.terminal.chain, 
                                                self.terminal.exp_date, 
                                                self.terminal.stock, 
                                                self.terminal.ticker,
                                                self.terminal.isPut)

        self.t = int((pd.to_datetime(self.terminal.exp_date) - pd.to_datetime(pd.Timestamp.now().date())).days)

        title = Title(self.terminal)

        self.MLayout = QVBoxLayout(self)
        self.MLayout.setSpacing(5)
        self.MLayout.addWidget(title)

    def run_simulator(self):
        subTitle = SubTitle(self.terminal, self.row)
        self.MLayout.addWidget(subTitle)

        self.MLayout.addSpacing(15)
        self.MLayout.setContentsMargins(15, 20, 15, 10)

        self.simulator = MonteCarlo(self.terminal.stock,
                                               self.r,
                                               self.information["impliedVolatility"],
                                               self.t,
                                               self.information["strike"],
                                               self.terminal.ticker,
                                               self.terminal.isPut,
                                               self.marketPrice)

        self.simulator.simulation(3000)

        graphSpace = GraphSpace(self.terminal.ticker, self.simulator)
        self.MLayout.addWidget(graphSpace)

        fullStatSpace = fullStats(self.simulator, self.terminal, self.row)
        self.MLayout.addWidget(fullStatSpace)

        self.MLayout.addStretch()

class GraphSpace(QWidget):
    def __init__(self, This_ticker, monteCarlo):
        super().__init__()
        self.This_ticker = This_ticker
        self.monteCarlo = monteCarlo
        self.graphLayout = QHBoxLayout(self)
        self.graph1 = Graph(self.This_ticker, self.monteCarlo)
        self.graphLayout.addWidget(self.graph1)
        
class Graph(QWidget):
    def __init__(self, this_ticker, monteCarlo):
        super().__init__()
        self.this_ticker = this_ticker
        self.monteCarlo = monteCarlo

        self.graphLayout = QVBoxLayout(self)
        self.graphLayout.setSpacing(5)

        self.graphLayout.addStretch()

        self.figure1 = Figure(facecolor="#02080d")
        self.canvas1 = FigureCanvas(self.figure1)

        self.graphLayout.addWidget(self.canvas1)

        self.update_graph1()

    def update_graph1(self):
        self.figure1.clear()
        self.monteCarlo.profitCalculator()
        self.ax1 = self.figure1.add_subplot(111)
        self.ax1.set_facecolor("#02080d")
        self.ax1.tick_params(axis='x', colors='white')
        self.ax1.tick_params(axis='y', colors='white')
        self.ax1.xaxis.label.set_color("white")
        self.ax1.yaxis.label.set_color("white")

        self.ax1.hist(self.monteCarlo.profit, bins=30, color="#08870a", edgecolor="white", alpha=0.4)
        self.ax1.set_xlabel("Profit")
        self.ax1.set_ylabel("Frequency")
        self.ax1.set_title(f"Distribution of Profit: {self.this_ticker}", color="white")

        for spine in self.ax1.spines.values():
            spine.set_color("white")

        self.canvas1.draw()


class SimStats(QWidget):
    def __init__(self, monteCarlo):
        super().__init__()
        self.monteCarlo = monteCarlo

        self.statsLayout = QVBoxLayout(self)
        self.statsLayout.setSpacing(5)

        self.propProfit = self.monteCarlo.propProfit()

        meanPayoffLabel = QLabel(f"Mean Payoff: {self.monteCarlo.meanPayoff:.2f}")
        meanPayoffLabel.setStyleSheet("color: white; font-size: 16px;")

        nowPayoffLabel = QLabel(f"Option Value: {self.monteCarlo.nowPayoff:.2f}")
        nowPayoffLabel.setStyleSheet("color: white; font-size: 16px;")

        stdevPayoffLabel = QLabel("Standard Deviation of Payoffs: {:.2f}".format(self.monteCarlo.stdevPayoff))
        stdevPayoffLabel.setStyleSheet("color: white; font-size: 16px;")

        medianPayoffLabel = QLabel(f"Median Payoff: {self.monteCarlo.medianPayoff}")
        medianPayoffLabel.setStyleSheet("color: white; font-size: 16px;")

        emptyLabel = QLabel("")

        self.statsLayout.addWidget(meanPayoffLabel)
        self.statsLayout.addWidget(nowPayoffLabel)
        self.statsLayout.addWidget(stdevPayoffLabel)
        self.statsLayout.addWidget(medianPayoffLabel)
        self.statsLayout.addWidget(emptyLabel)

class ProfitStats(QWidget):
    def __init__(self, monteCarlo):
        super().__init__()
        self.monteCarlo = monteCarlo
        self.profitLayout = QVBoxLayout(self)
        self.profitProp = self.monteCarlo.profitability()

        avgProfitLabel = QLabel(f"Average Profit: {round(self.monteCarlo.meanProfit, 3)}")
        avgProfitLabel.setStyleSheet("color: white; font-size: 16px;")
        stDevLabel = QLabel(f"Standard Deviation Profit: {round(self.monteCarlo.stDevProfit, 3)}")
        stDevLabel.setStyleSheet("color: white; font-size: 16px;")
        profitabilityLabel = QLabel(f"Profitability: {round(self.profitProp, 3)}%")
        profitabilityLabel.setStyleSheet("color: white; font-size: 16px;")

        self.profitLayout.addWidget(avgProfitLabel)
        self.profitLayout.addWidget(stDevLabel)
        self.profitLayout.addWidget(profitabilityLabel)

        self.profitLayout.setSpacing(5)
        self.profitLayout.addStretch()
        

class Greeks(QWidget):
    def __init__(self, terminal, row):
        super().__init__()
        self.terminal = terminal
        self.row = row

        self.information = self.terminal.chain.iloc[self.row]

        self.gamma = self.information["gamma"]
        self.delt = self.information['delta']
        self.theta = self.information["theta"]
        self.vega = self.information["vega"]
        self.rho = self.information["rho"]

        self.greeksLayout = QVBoxLayout(self)
        self.greeksLayout.setSpacing(5)

        deltaLabel = QLabel(f"Delta: {self.delt:.4f}")
        deltaLabel.setStyleSheet("color: white; font-size: 16px;")

        gammaLabel = QLabel(f"Gamma: {self.gamma:.4f}")
        gammaLabel.setStyleSheet("color: white; font-size: 16px;")

        vegaLabel = QLabel(f"Vega: {self.vega:.4f}")
        vegaLabel.setStyleSheet("color: white; font-size: 16px;")

        thetaLabel = QLabel(f"Theta: {self.theta:.4f}")
        thetaLabel.setStyleSheet("color: white; font-size: 16px;")

        rhoLabel = QLabel(f"Rho: {self.rho:.4f}")
        rhoLabel.setStyleSheet("color: white; font-size: 16px;")

        self.greeksLayout.addWidget(deltaLabel)
        self.greeksLayout.addWidget(gammaLabel)
        self.greeksLayout.addWidget(vegaLabel)
        self.greeksLayout.addWidget(thetaLabel)
        self.greeksLayout.addWidget(rhoLabel)

class MoreStats(QWidget):
    def __init__(self, monteCarlo):
        super().__init__()
        self.monteCarlo = monteCarlo
        self.skewness = self.monteCarlo.skewness()
        self.kurtosis = self.monteCarlo.kurtosis()
        self.VaR, self.CVaR = self.monteCarlo.riskMeasurements()
        
        self.stats2Layout = QVBoxLayout(self)

        self.stats2Layout.setSpacing(5)

        skewnessLabel = QLabel(f"Skewness: {self.skewness:.4f}")
        skewnessLabel.setStyleSheet("color: white; font-size: 16px;")
        kurtosisLabel = QLabel(f"Kurtosis: {self.kurtosis:.4f}")
        kurtosisLabel.setStyleSheet("color: white; font-size: 16px;")
        VaRLabel = QLabel(f"VaR: {self.VaR:.4f}")
        VaRLabel.setStyleSheet("color: white; font-size: 16px;")
        CVaRLabel = QLabel(f"CVaR: {self.CVaR:.4f}")
        CVaRLabel.setStyleSheet("color: white; font-size: 16px;")
        emptyLabel = QLabel("")

        self.stats2Layout.addWidget(skewnessLabel)
        self.stats2Layout.addWidget(kurtosisLabel)
        self.stats2Layout.addWidget(VaRLabel)
        self.stats2Layout.addWidget(CVaRLabel)
        self.stats2Layout.addWidget(emptyLabel)
        

class fullStats(QWidget):
    def __init__(self, monteCarlo, terminal, row):
        super().__init__()
        self.monteCarlo = monteCarlo
        self.terminal = terminal
        self.row = row

        self.fullLayout = QHBoxLayout(self)
        self.fullLayout.setSpacing(5)

        self.simStats = SimStats(self.monteCarlo)
        self.greeks = Greeks(self.terminal, self.row)
        self.stats2 = MoreStats(self.monteCarlo)
        self.stats3 = ProfitStats(self.monteCarlo)

        self.fullLayout.addWidget(self.simStats)
        self.fullLayout.addWidget(self.greeks)
        self.fullLayout.addWidget(self.stats2)
        self.fullLayout.addWidget(self.stats3)

        self.fullLayout.setContentsMargins(20, 5, 20, 5)




