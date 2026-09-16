import sys
import os
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QSlider, QCheckBox
from PySide6.QtWidgets import QGraphicsSceneMouseEvent, QMainWindow, QLayout, QLineEdit, QFrame, QMenu
from PySide6.QtWidgets import QPushButton, QVBoxLayout, QHBoxLayout, QGridLayout, QComboBox
from PySide6.QtWidgets import QStackedWidget, QGraphicsView, QGraphicsScene, QScrollArea, QSizePolicy
from pathlib import Path
from PySide6.QtGui import QPainter, QFont, QPen, QColor, QBrush, QFontDatabase, QPalette, QFontMetrics, QCursor
from PySide6.QtCore import QPoint, QPointF, Slot, QSize, QEventLoop, QTimer
from PySide6.QtCore import Qt, Signal
from .components import Title, SubTitle
import numpy as np
import scipy
import statistics
import matplotlib
import yfinance as yf

class ChainSpace(QWidget):
    def __init__(self, terminal):
        super().__init__()
        self.terminal = terminal

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 20, 15, 10)
        layout.setSpacing(10)
        
        chainTitle = Title(self.terminal)
        layout.addWidget(chainTitle, alignment = Qt.AlignmentFlag.AlignTop)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        container = QWidget()
        container.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Minimum
            )
        chainLayout = QVBoxLayout(container)
        chainLayout.setContentsMargins(10, 10, 10, 10)
        chainLayout.setAlignment(Qt.AlignmentFlag.AlignTop)

        optionsChain = Chain(self.terminal)
        optionsChain.setSizePolicy(
    QSizePolicy.Policy.Expanding,
    QSizePolicy.Policy.Fixed
)

        chainLayout.addWidget(optionsChain)

        scroll.setWidget(container)
        layout.addWidget(scroll)

class clickableLabel(QLabel):
    clicked = Signal()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()

        super().mousePressEvent(event)

class Chain(QWidget):
    def __init__(self, terminal):
        super().__init__()
        self.terminal = terminal

        layout = QGridLayout(self)
        layout.setSpacing(0)

        headers_readable = {
            "contractSymbol": "Contract",
            "inTheMoney": "In the money",
            "impliedVolatility": "Implied Volatility",
            "lastTradeDate": "Last Traded",
            "contractSize": "Size",
            "marketPrice": "Market Price",
            "openInterest": "Open Interest",
            "percentChange": "Percent Change",
            "lastPrice": "Last Price",
            "strike": "Strike",
            "currency": "Currency",
            "spread": "Spread",
            "volume": "Volume",
            "bid": "Bid",
            "ask": "Ask",
            "change":"Change",
            "delta": "Delta",
            "gamma": "Gamma",
            "vega": "Vega",
            "theta": 'Theta',
            "rho": "Rho"
        }

        headers = self.terminal.chain.columns.tolist()

        for column,header in enumerate(headers):
            headerLabel = QLabel(str(headers_readable[header]))
            headerLabel.setStyleSheet("""
                            QLabel{
                            font-size: 16px;
                            text-align: left;
                            border: 1px solid #20263d;
                            background-color: #050816;
                            padding: 5px;}

                            QLabel:hover {
                            background-color: #0c1226;
                            }
                            """)

            headerLabel.setSizePolicy(
                QSizePolicy.Policy.Preferred,
                QSizePolicy.Policy.Fixed
                )
            
            font = QFont("arial", 16)
            metrics = QFontMetrics(font)
            width = metrics.horizontalAdvance(headers_readable[header])

            headerLabel.setFixedWidth(width + 20)
            layout.addWidget(headerLabel, 0, column, 1, 1)
            layout.setColumnMinimumWidth(column, width+20)

            layout.setColumnMinimumWidth(0, 100)

        for row, (_, option) in enumerate(
            self.terminal.chain.iterrows(), start=1
        ):
            for column, header in enumerate(headers):
                value = option[header]

                gridSpace = clickableLabel(str(value))
                gridSpace.clicked.connect(
                    lambda row=row-1: self.optionClicked(row))

                if header == "volume":
                    if value <= 5:
                        gridSpace.setStyleSheet("""
                                        QLabel {
                                            background-color: #050816;
                                            border: 1px solid #20263d;
                                            text-align: left;
                                            color: #b83a35;
                                            font-size: 12px;
                                            padding: 3px;
                                        }
                                        QLabel:hover{
                                                        background-color: #0c1226;
                                                        }""")

                    elif value <= 20:
                         gridSpace.setStyleSheet(
                            """QLabel {
                            background-color: #050816;
                            border: 1px solid #20263d;
                            color: #c9703c;
                            text-align: left;
                            font-size: 12px;
                            padding: 3px;
                        }
                        QLabel:hover{
                                        background-color: #0c1226;
                                        }""")

                    else:
                        gridSpace.setStyleSheet(
                            """QLabel {
                            background-color: #050816;
                            border: 1px solid #20263d;
                            text-align: left;
                            font-size: 12px;
                            padding: 3px;}
                            QLabel:hover{
                                            background-color: #0c1226;
                                            }
                        """)

                elif header == "vega":
                    if value >= 150:
                        gridSpace.setStyleSheet("""
                                    QLabel {
                                        background-color: #050816;
                                        border: 1px solid #20263d;
                                        text-align: left;
                                        color: #b83a35;
                                        font-size: 12px;
                                        padding: 3px;
                                    }
                                    QLabel:hover{
                                                    background-color: #0c1226;
                                                    }""")     

                    elif value >= 100:  
                        gridSpace.setStyleSheet(
                                    """QLabel {
                                        background-color: #050816;
                                        border: 1px solid #20263d;
                                        color: #c9703c;
                                        text-align: left;
                                        font-size: 12px;
                                        padding: 3px;
                                        }
                                        QLabel:hover{
                                                        background-color: #0c1226;
                                                        }""")  

                    elif value >= 80:
                        gridSpace.setStyleSheet(
                                    """QLabel {
                                        background-color: #050816;
                                        border: 1px solid #20263d;
                                        color: #c7b248;
                                        text-align: left;
                                        font-size: 12px;
                                        padding: 3px;
                                        }
                                        QLabel:hover{
                                                        background-color: #0c1226;
                                                        }""") 
                    else:
                        gridSpace.setStyleSheet(
                            """QLabel {
                            background-color: #050816;
                            border: 1px solid #20263d;
                            text-align: left;
                            font-size: 12px;
                            padding: 3px;}
                            QLabel:hover{
                                            background-color: #0c1226;
                                            }
                        """)

                elif header ==  "marketPrice":
                    if value <= 10:
                        gridSpace.setStyleSheet("""
                                    QLabel {
                                        background-color: #050816;
                                        border: 1px solid #20263d;
                                        text-align: left;
                                        color: #b83a35;
                                        font-size: 12px;
                                        padding: 3px;}
                                        QLabel:hover{
                                                        background-color: #0c1226;
                                                        }

                                    """) 

                    elif value <= 15: 
                        gridSpace.setStyleSheet(
                                    """QLabel {
                                        background-color: #050816;
                                        border: 1px solid #20263d;
                                        color: #c9703c;
                                        text-align: left;
                                        font-size: 12px;
                                        padding: 3px;}
                                        QLabel:hover{
                                                        background-color: #0c1226;
                                                        }
                                        """)    

                    else:
                        gridSpace.setStyleSheet(
                            """QLabel {
                            background-color: #050816;
                            border: 1px solid #20263d;
                            text-align: left;
                            font-size: 12px;
                            padding: 3px;}
                            QLabel:hover{
                                            background-color: #0c1226;
                                            }
                        """)

                elif header == "bid":
                    if value <= 5:
                        gridSpace.setStyleSheet("""
                                    QLabel {
                                        background-color: #050816;
                                        border: 1px solid #20263d;
                                        text-align: left;
                                        color: #b83a35;
                                        font-size: 12px;
                                        padding: 3px;}
                                        QLabel:hover{
                                                        background-color: #0c1226;
                                                        }

                                    """) 

                    elif value <= 10:
                        gridSpace.setStyleSheet(
                                    """QLabel {
                                        background-color: #050816;
                                        border: 1px solid #20263d;
                                        color: #c9703c;
                                        text-align: left;
                                        font-size: 12px;
                                        padding: 3px;}
                                        QLabel:hover{
                                                        background-color: #0c1226;
                                                        }
                                        """)      

                    elif value <= 20:
                        gridSpace.setStyleSheet(
                                    """QLabel {
                                        background-color: #050816;
                                        border: 1px solid #20263d;
                                        color: #c9703c;
                                        text-align: left;
                                        font-size: 12px;
                                        padding: 3px;}
                                        QLabel:hover{
                                                        background-color: #0c1226;
                                                        }
                                        """)    

                    else:
                        gridSpace.setStyleSheet(
                                        """QLabel {
                                        background-color: #050816;
                                        border: 1px solid #20263d;
                                        text-align: left;
                                        font-size: 12px;
                                        padding: 3px;}
                                        QLabel:hover{
                                                        background-color: #0c1226;
                                                        }
                                    """)

                elif header == "theta":
                    if self.terminal.isPut:
                        if value <= 5:
                            gridSpace.setStyleSheet("""
                            QLabel {
                                background-color: #050816;
                                border: 1px solid #20263d;
                                text-align: left;
                                color: #b83a35;
                                font-size: 12px;
                                padding: 3px;}
                                QLabel:hover{
                                                background-color: #0c1226;
                                                }
                                """) 

                        else:
                            gridSpace.setStyleSheet("""
                    QLabel {
                        background-color: #050816;
                        border: 1px solid #20263d;
                        text-align: left;
                        font-size: 12px;
                        padding: 3px;
                    }
                    QLabel:hover{
                                    background-color: #0c1226;
                                    }
                 """)

                    else:
                        if value <= -30:
                            gridSpace.setStyleSheet("""
                                    QLabel {
                                    background-color: #050816;
                                    border: 1px solid #20263d;
                                    text-align: left;
                                    color: #b83a35;
                                    font-size: 12px;
                                    padding: 3px;}
                                    QLabel:hover{
                                                    background-color: #0c1226;
                                                    }

                                    """) 

                        else:
                            gridSpace.setStyleSheet("""
                    QLabel {
                        background-color: #050816;
                        border: 1px solid #20263d;
                        text-align: left;
                        font-size: 12px;
                        padding: 3px;
                    }
                    QLabel:hover{
                                    background-color: #0c1226;
                                    }
                 """)

                else:
                    gridSpace.setStyleSheet("""
                    QLabel {
                        background-color: #050816;
                        border: 1px solid #20263d;
                        text-align: left;
                        font-size: 12px;
                        padding: 3px;
            
                    }
                    QLabel:hover{
                                    background-color: #0c1226;
                                    }
                 """)

                gridSpace.setSizePolicy(
                    QSizePolicy.Policy.Preferred,
                    QSizePolicy.Policy.Fixed
                )
                layout.addWidget(gridSpace, row, column)
        
        # Don't allow the grid rows to absorb extra space
        for row in range(layout.rowCount()):
            layout.setRowStretch(row, 0)

        layout.setVerticalSpacing(0)

        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed
            )

        self.adjustSize()

    def optionClicked(self, row):
        self.selectedRow = row
        menu = QMenu(self)
        inspectionAction = menu.addAction("Inspect Option")

        action = menu.exec(QCursor.pos())

        if action == inspectionAction:
            self.terminal.inspectOption(self.selectedRow)

        

        