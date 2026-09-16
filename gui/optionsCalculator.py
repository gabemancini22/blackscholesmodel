import sys
import os
from finance.cleaner import Truths, Cleaner
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QSlider, QCheckBox
from PySide6.QtWidgets import QGraphicsSceneMouseEvent, QMainWindow, QLayout, QLineEdit, QFrame
from PySide6.QtWidgets import QPushButton, QVBoxLayout, QHBoxLayout, QGridLayout, QComboBox
from PySide6.QtGui import QPainter, QFont, QPen, QColor, QBrush, QFontDatabase, QPalette
from PySide6.QtCore import QPoint, QPointF, Slot, QSize, QEventLoop, QTimer
from PySide6.QtCore import Qt
import numpy as np
import scipy
import statistics
import matplotlib
import yfinance as yf
from .sidebar import Terminal

class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.showMP = False
        self.showSpread = False
        self.showVolume = False
        self.showImpVol = True
        self.showITM = False
        self.showContrSize = False
        self.showCurrency = False
        self.showLastTrd = False
        self.showGreeks = True
        self.put = False

        self.setWindowTitle("Options Terminal: Home")
        self.resize(250, 400)
        self.setStyleSheet("background-color: #010417")

        container = QWidget()
        self.gridLayout = QGridLayout()
        container.setLayout(self.gridLayout)
        self.setCentralWidget(container)
        self.gridLayout.setContentsMargins(50,20,50,40)
        self.gridLayout.setHorizontalSpacing(50)

        title = QLabel("Options Terminal: Home")
        title.setStyleSheet("font-size: 24px; font-weight: bold")
        self.gridLayout.addWidget(title, 0, 0, 2, 2, alignment = Qt.AlignmentFlag.AlignLeft)
        self.gridLayout.setSpacing(10)
        title.setMaximumHeight(50)

        ticker = QLabel("Stock Ticker:")
        self.tickerInput = QLineEdit()
        ticker.setStyleSheet("font-size: 24px; font-weight: bold")
        self.gridLayout.addWidget(ticker, 2, 0)
        self.gridLayout.addWidget(self.tickerInput, 2, 1)
        self.tickerInput.setMaximumWidth(100)

        self.button1 = QPushButton("Get Expiration Dates")
        self.gridLayout.addWidget(self.button1, 2, 2)
        self.button1.clicked.connect(self.handle_press1)

        self.button2 = QPushButton("Show Chain")
        self.gridLayout.addWidget(self.button2, 0, 2)
        self.button2.clicked.connect(self.handleOptions)
        self.errorLabel = QLabel()
        self.gridLayout.addWidget(self.errorLabel, 8, 1, 1, 2)
        self.errorLabel.hide()
        self.tickerInput.setMaximumWidth(100)

        type = QLabel("Option Type:")
        self.typeDrop = QComboBox()
        self.typeDrop.addItems(["Call", "Put"])
        self.gridLayout.addWidget(type, 3, 0)
        self.gridLayout.addWidget(self.typeDrop, 3, 1)
        self.typeDrop.currentIndexChanged.connect(self.optionType)

        expDate = QLabel("Expiration Date:")
        self.dates = QComboBox()
        self.gridLayout.addWidget(expDate, 4, 0)
        self.gridLayout.addWidget(self.dates, 4, 1)

        self.status = QLabel("Click Button to Load Dates")
        self.gridLayout.addWidget(self.status, 4, 2)

        self.tickerInput.returnPressed.connect(self.handle_press1)

        h_line1 = QFrame()
        h_line1.setFrameShape(QFrame.Shape.HLine)
        h_line1.setStyleSheet("background-color: #343941")
        self.gridLayout.addWidget(h_line1, 1, 0, 1, 3)

        # ------------------ FILTER CHECKBOXES ----------------------
        self.spread = QCheckBox("Show Spread")
        self.maxSpread = QLabel("Maximum Bid-Ask Spread")
        self.maxSpread_inline = QLineEdit()
        self.spread.toggled.connect(self.maxSpread_METHOD)
        self.gridLayout.addWidget(self.maxSpread_inline, 6, 2)
        self.gridLayout.addWidget(self.maxSpread, 6, 1)
        self.gridLayout.addWidget(self.spread, 6, 0)
        self.maxSpread.hide()
        self.maxSpread_inline.hide()

        self.mp = QCheckBox("Show Market Price")
        self.gridLayout.addWidget(self.mp, 5, 0)
        self.mp.toggled.connect(self.minMP_METHOD)
        self.minMP = QLabel("Minimun Market Price")
        self.minMP_inline = QLineEdit()
        self.gridLayout.addWidget(self.minMP_inline, 5, 2)
        self.gridLayout.addWidget(self.minMP, 5, 1)
        self.minMP_inline.hide()
        self.minMP.hide()

        self.volume = QCheckBox("Show Volume")
        self.minVolume = QLabel("Minimum Volume")
        self.minVolume_inline = QLineEdit()
        self.volume.toggled.connect(self.showVolume_METHOD)
        self.gridLayout.addWidget(self.minVolume_inline, 7, 2)
        self.gridLayout.addWidget(self.minVolume, 7, 1)
        self.minVolume.hide()
        self.minVolume_inline.hide()

        self.money = QCheckBox("Show In the Money")
        self.money.toggled.connect(self.showMoney_METHOD)

        self.contract = QCheckBox("Show Contract Size")
        self.contract.toggled.connect(self.showContract_METHOD)

        self.currency = QCheckBox("Show Currency")
        self.currency.toggled.connect(self.showCurrency_METHOD)
        
        self.tradeDate = QCheckBox("Show Last Trade Date")
        self.tradeDate.toggled.connect(self.showtrDate_METHOD)

        self.gridLayout.addWidget(self.volume, 7, 0)
        self.gridLayout.addWidget(self.money, 9, 0)
        self.gridLayout.addWidget(self.contract, 10, 0)
        self.gridLayout.addWidget(self.currency, 11, 0)
        self.gridLayout.addWidget(self.tradeDate, 12, 0)
        
    # ----------------------- METHODS -------------------------------
    def handle_press1(self):
        ticker_symbol = self.tickerInput.text().strip().upper()
        stock = yf.Ticker(ticker_symbol)
        exp_dates = stock.options

        self.dates.clear()
        if exp_dates:
            self.dates.addItems(exp_dates)
            self.status.setText(f"Loaded {len(exp_dates)} Expiration Dates for {ticker_symbol}.")

        else:
            self.status.setText("No Options Found")

    def minMP_METHOD(self, isChecked):
        if isChecked:
            self.showMP = True
            self.minMP.show()
            self.minMP_inline.show()
        else:
            self.showMP = False
            self.minMP_inline.hide()
            self.minMP.hide()

    def maxSpread_METHOD(self, isChecked):
        if isChecked:
            self.showSpread = True
            self.maxSpread.show()
            self.maxSpread_inline.show()
        else:
            self.showSpread = False
            self.maxSpread.hide()
            self.maxSpread_inline.hide()

    # --------------- TRUTH STATEMENTS FOR CHECK BOXES -------------------

    def showVolume_METHOD(self, isChecked):
        if isChecked: 
            self.showVolume = True
            self.minVolume_inline.show()
            self.minVolume.show()
        else: 
            self.showVolume = False
            self.minVolume_inline.hide()
            self.minVolume.hide()

    def showMoney_METHOD(self, isChecked):
        if isChecked:
            self.showITM = True
        else:
            self.showITM = False

    def showContract_METHOD(self, isChecked):
        if isChecked:
            self.showContrSize = True
        else:
            self.showContrSize = False

    def showCurrency_METHOD(self, isChecked):
        if isChecked:
            self.showCurrency = True
        else:
            self.showCurrency = False

    def showtrDate_METHOD(self, isChecked):
        if isChecked:
            self.showLastTrd = True
        else:
            self.showLastTrd = False

    def optionType(self, index):
        if index == 0:
            self.put = False
        else:
            self.put = True

# ---------------------------- OPENS OPTION TERMINAL ----------------------
    def handleOptions(self):
        if not self.tickerInput.text().strip() or self.typeDrop.currentIndex() == -1 or self.dates.currentIndex() == -1:
            self.errorLabel.setText("No Ticker or Option type chosen.")
            self.errorLabel.setStyleSheet("""
            color: #ed5353;
            """)
            self.errorLabel.show()

        else:
            self.errorLabel.hide()
            ticker_symbol = self.tickerInput.text().strip().upper()
            stock = yf.Ticker(ticker_symbol)
            price1 = stock.history(period = "1d")["Close"].iloc[-1]
            print(ticker_symbol)

            expiration = self.dates.currentText()

            hist1 = stock.history(period = "1y", auto_adjust = True)
            hist1["Return"] = hist1["Close"].pct_change()
            returns1 = hist1["Return"].dropna()
            stdev1 = statistics.stdev(returns1)

            if self.showVolume:
                volume = int(self.minVolume_inline.text().strip())
            else:
                volume = None

            if self.showMP:
                marketPrice = float(self.minMP_inline.text().strip())
            else:
                marketPrice = None

            if self.showSpread:
                spreadMax = float(self.maxSpread_inline.text().strip())
            else:
                spreadMax = None

            chain = stock.option_chain(expiration)

            if self.put: df = chain.puts
            else: df = chain.calls

            options = Cleaner(df, ticker_symbol, expiration)

            truths = Truths(self.showMP,
                            self.showSpread,
                            self.showVolume,
                            self.showImpVol,
                            self.showITM,
                            self.showContrSize,
                            self.showCurrency,
                            self.showLastTrd,
                            self.showGreeks,
                            self.put)

            cleanedChain = options.cleanChain(truths, 
                               minVolume = volume, 
                               minMP = marketPrice, 
                               maxSpread = spreadMax, 
            )

            self.terminal = Terminal(cleanedChain, 
                                              ticker_symbol,
                                              volume,
                                              marketPrice,
                                              spreadMax,
                                              self.put,
                                              price1, 
                                              expiration)

            self.setCentralWidget(self.terminal)
            self.terminal.show()
            

            
            
