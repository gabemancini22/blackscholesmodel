import sys
import os
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QSlider, QCheckBox
from PySide6.QtWidgets import QGraphicsSceneMouseEvent, QMainWindow, QLayout, QLineEdit, QFrame
from PySide6.QtWidgets import QPushButton, QVBoxLayout, QHBoxLayout, QGridLayout, QComboBox
from PySide6.QtWidgets import QStackedWidget, QGraphicsView, QGraphicsScene, QSizePolicy
from pathlib import Path
from PySide6.QtGui import QPainter, QFont, QPen, QColor, QBrush, QFontDatabase, QPalette
from PySide6.QtCore import QPoint, QPointF, Slot, QSize, QEventLoop, QTimer
from PySide6.QtCore import Qt
from .optionsChain import ChainSpace, Chain
from .smileWidget import SmileSpace, Display, Graphs, Settings
from .surfaceWidget import SurfaceSpace, SurfaceGraph
from .monteCarloWidget import MonteCarloSpace
import numpy as np
import scipy
import statistics
import matplotlib

class SideBar(QWidget):
    def __init__(self):
        super().__init__()

        self.setObjectName("sidebar")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        title = QLabel("Navigator")
        title.setObjectName("sidebarTitle")

        layout.addWidget(title)

        self.options = QPushButton("Options Chain")
        self.smile = QPushButton("Volatility Smile")
        self.surface = QPushButton("Volatility Surface")
        self.monteCarlo = QPushButton("Monte Carlo Simulation")

        layout.addWidget(self.options)
        layout.addWidget(self.smile)
        layout.addWidget(self.surface)
        layout.addWidget(self.monteCarlo)

        layout.addStretch()

        self.setStyleSheet("""
            QWidget#sidebar {
                background-color: #2cd1d1;
            }

            QLabel#sidebarTitle {
                color: white;
                font-size: 30px;
                font-weight: bold;
                padding: 20px;
            }

            QPushButton {
                color: white;
                background-color: #050816;
                border: 1px solid #20263d;
                border-bottom: 1px solid #20263d;
                padding: 18px;
                text-align: left;
                border-radius: 0px;
                font-size: 20px;
            }

            QPushButton:hover {
                background-color: #0c1226;
            }
        """)

        self.setFixedWidth(300)

class Terminal(QMainWindow):
    def __init__(self, 
                 chain, 
                 ticker, 
                 minVol, 
                 minMP,        
                 maxSpread,
                 isPut,
                 stock,
                 exp_date):
        super().__init__()
        self.chain = chain
        self.ticker = ticker
        self.minVol = minVol
        self.minMP = minMP
        self.maxSpread = maxSpread
        self.isPut = isPut
        self.stock = stock
        self.exp_date = exp_date

        self.setWindowTitle("Terminal")

        container = QWidget()
        self.setCentralWidget(container)

        mainLayout = QHBoxLayout(container)
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.setSpacing(0)

        # Sidebar
        self.sidebar = SideBar()
        self.sidebar.setObjectName("sidebar")

        self.sidebar.setStyleSheet("""
    QPushButton {
        color: white;
        background-color: #050816;
        border: 1px solid #20263d;
        padding: 18px;
        text-align: left;
        font-size: 20px;
    }

    QPushButton:hover {
        background-color: #0c1226;
    }

    QPushButton:pressed{
    background-color: #0c1226;
    }
""")

        # Divider
        divider = QFrame()
        divider.setFixedWidth(4)
        divider.setStyleSheet("background-color: #9c9c9c;")

        # Main area
        main_area = QWidget()
        main_area.setSizePolicy(
        QSizePolicy.Policy.Expanding,
        QSizePolicy.Policy.Expanding
        )

        main_area.setStyleSheet("background-color: #02080d;")
        main_area_layout = QVBoxLayout(main_area)

        # Add everything horizontally
        mainLayout.addWidget(self.sidebar)
        mainLayout.addWidget(divider)
        mainLayout.addWidget(main_area)

        self.pages = QStackedWidget()
        self.optionsChainWidget = ChainSpace(self)
        self.volatilitySmileWidget = SmileSpace(self)
        self.volatilitySurfaceWidget = SurfaceSpace(self)
        self.pages.addWidget(self.optionsChainWidget)
        self.pages.addWidget(self.volatilitySmileWidget)
        self.pages.addWidget(self.volatilitySurfaceWidget)

        main_area_layout.addWidget(self.pages, 1)

        self.sidebar.options.clicked.connect(
            lambda: self.pages.setCurrentWidget(self.optionsChainWidget)
        )

        self.sidebar.smile.clicked.connect(
            lambda: self.pages.setCurrentWidget(self.volatilitySmileWidget)
        )

        self.sidebar.surface.clicked.connect(
            lambda: self.pages.setCurrentWidget(self.volatilitySurfaceWidget)
        )

    def inspectOption(self, selectedRow):
        if hasattr(self, "monteCarloWidget"):
            self.pages.removeWidget(self.monteCarloWidget)
            self.monteCarloWidget.deleteLater()

        self.monteCarloWidget = MonteCarloSpace(self, selectedRow)
        self.pages.addWidget(self.monteCarloWidget)
        self.pages.setCurrentWidget(self.monteCarloWidget)
        self.monteCarloWidget.run_simulator()

        self.sidebar.monteCarlo.clicked.connect(
            lambda: self.pages.setCurrentWidget(self.monteCarloWidget)
        )
        