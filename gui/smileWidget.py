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
from .components import Title
import numpy as np
import scipy
import statistics
import matplotlib
import yfinance as yf
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

class SmileSpace(QWidget):
    def __init__(self, terminal):
        super().__init__()
        self.terminal = terminal
        self.volumeBool = False
        self.openBool = False

        self.volumeButton = QPushButton("Display Volume")
        self.volumeButton.setStyleSheet("""
                            QPushButton:hover {
                                background-color: #0c1226;
                                        }
                                """)
        
        self.openIntButton = QPushButton("Display Open Interest")
        self.openIntButton.setStyleSheet("""
                            QPushButton:hover {
                                background-color: #0c1226;
                                        }
                                """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 20, 15, 10)
        layout.setSpacing(0)

        smileTitle = Title(self.terminal)
        layout.addWidget(smileTitle, alignment = Qt.AlignmentFlag.AlignTop)

        fullDisplay = UnderSpace(self)
        fullDisplay.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Maximum
        )
        layout.addWidget(fullDisplay)

        layout.addStretch()

class UnderSpace(QWidget):
    def __init__(self, smileSpace):
        super().__init__()
        self.smileSpace = smileSpace

        layout = QHBoxLayout(self)

        layout.setSpacing(10)

        graphs_display = Display(self.smileSpace)
        layout.addWidget(graphs_display, stretch = 1)

        vline = QFrame()
        vline.setFrameShape(QFrame.Shape.VLine)
        vline.setFrameShadow(QFrame.Shadow.Sunken)

        vline.setStyleSheet("border: 1px solid white;")

        layout.addWidget(vline)

        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        stats_table = Stats(self.smileSpace)
        layout.addWidget(stats_table)

        self.setStyleSheet("""
            QPushButton {
                color: white;
                background-color: #050816;
                border: 1px solid #20263d;
                border-bottom: 1px solid #20263d;
                padding: 18px;
                text-align: left;
                font-size: 20px;
            }

            QPushButton:hover {
                background-color: #0c1226;
            }

            QLabel{
            background-color: #050816;
            border: 1px solid #20263d;
            padding: 5px;
            font-size: 20px;
            }

            QLabel: hover{
                background-color: #0c1226;
            }
        """)


class Display(QWidget):
    def __init__(self, smileSpace):
        super().__init__()
        self.smileSpace = smileSpace

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5) 

        # Store graph reference so Editors can instruct it to update
        self.graph = Graphs(self.smileSpace)
        layout.addWidget(self.graph)

        setting_labels = Settings(self.smileSpace, self.graph)
        layout.addWidget(setting_labels, alignment=Qt.AlignmentFlag.AlignTop)


class Graphs(QWidget):
    def __init__(self, smileSpace):
        super().__init__()
        self.smileSpace = smileSpace
        self.ax2 = None  # Reference to hold secondary axis

        layout = QVBoxLayout(self)
        layout.setSpacing(20) 

        self.figure = Figure(facecolor="#02080d")
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        self.ax = self.figure.add_subplot(111)
        
        # Perform initial plot
        self.update_graph()

    def update_graph(self):
        # 1. Clear main axis and safely remove secondary axis if present
        self.ax.clear()
        if self.ax2 is not None:
            self.ax2.remove()
            self.ax2 = None

        # 2. Re-apply dark styling after clearing
        self.ax.set_facecolor("#02080d")
        self.ax.tick_params(axis="both", colors="white")
        self.ax.xaxis.label.set_color("white")
        self.ax.yaxis.label.set_color("white")
        self.ax.title.set_color("white")

        for spine in self.ax.spines.values():
            spine.set_color("white")   
            
        x = []
        x2 = []
        y = []
        
        for index, row in self.smileSpace.terminal.chain.iterrows():
            x2.append(row["strike"])

            if row['impliedVolatility'] >= 1e-4:
                x.append(row['strike'])
                y.append(row['impliedVolatility'])

        self.ax.scatter(x, y, color="#C0D8C2", marker="o", s = 15)
        self.ax.axvline(x=self.smileSpace.terminal.stock, color = "#8ca18a", linestyle='--')

        if len(x) > 2:
            coefficients = np.polyfit(x, y, deg=2)
            quadratic = np.poly1d(coefficients)
            
            x_curve = np.linspace(min(x), max(x), 100)
            y_curve = quadratic(x_curve)

            if coefficients[0] < 1e-4:
                coefficients[0] = 0.0001
                equation = f"Fitted Equation: V = {coefficients[0]:.4f}K² + {coefficients[1]:.4f}K + {coefficients[2]:.4f}"

            else:
                equation = f"Fitted Equation: V = {coefficients[0]:.4f}K² + {coefficients[1]:.4f}K + {coefficients[2]:.4f}"

            self.ax.plot(x_curve, y_curve, color="#4FAF65", linewidth=1, label="Regression of Implied Volatility")

            self.ax.text(
                0.05, 0.95,
                equation,
                transform=self.ax.transAxes,
                color="white",
                verticalalignment="top"
            )

        self.ax.set_xlabel("Strike")
        self.ax.set_ylabel("Implied Volatility")
        self.ax.set_title("Volatility Smile")

        if self.smileSpace.volumeBool:
            self.ax2 = self.ax.twinx()
            self.ax2.tick_params(axis="both", colors="white")
            self.ax2.yaxis.label.set_color("white")
            
            y2 = [row['volume'] for _, row in self.smileSpace.terminal.chain.iterrows()]
            self.ax2.bar(x2, y2, width=1, alpha=0.5, color="#07a809", edgecolor="white", label="Volume")
            self.ax2.set_ylabel("Volume")

        elif self.smileSpace.openBool:
            self.ax2 = self.ax.twinx()
            self.ax2.tick_params(axis="both", colors="white")
            self.ax2.yaxis.label.set_color("white")

            y2 = [row['openInterest'] for _, row in self.smileSpace.terminal.chain.iterrows()]
            self.ax2.bar(x2, y2, width = 1, alpha=0.5, color="#07a809", edgecolor="white", label="Open Interest")
            self.ax2.set_ylabel("Open Interest")

        else:
            self.smileSpace.volumeButton.setStyleSheet("background-color: #050816;")
            self.smileSpace.openIntButton.setStyleSheet("background-color: #050816;")

        # 4. Draw canvas update
        self.canvas.draw()

class Settings(QWidget):
    def __init__(self, smileSpace, graph):
        super().__init__()
        self.smileSpace = smileSpace
        self.graph = graph

        layout = QVBoxLayout(self)
        layout.setSpacing(20) 

        settingsTit = QLabel("Settings")
        settingsTit.setStyleSheet("font-size: 26px; text-align: left;")
        layout.addWidget(settingsTit, alignment=Qt.AlignmentFlag.AlignTop)

        editing_buttons = Editors(self.smileSpace, self.graph)
        layout.addWidget(editing_buttons)

class Editors(QWidget):
    def __init__(self, smileSpace, graph):
        super().__init__()
        self.smileSpace = smileSpace
        self.graph = graph

        layout = QHBoxLayout(self)
        layout.setSpacing(20)
        
        self.smileSpace.volumeButton.clicked.connect(self.handle_volume)
        self.smileSpace.openIntButton.clicked.connect(self.handle_open)

        layout.addWidget(self.smileSpace.volumeButton)
        layout.addWidget(self.smileSpace.openIntButton)

    def handle_volume(self):
        self.smileSpace.volumeBool = not self.smileSpace.volumeBool
        self.smileSpace.openBool = False

        self.smileSpace.openIntButton.setStyleSheet("background-color: #050816;")
        self.smileSpace.volumeButton.setStyleSheet("background-color: #0c1226;")
        
        self.graph.update_graph()

    def handle_open(self):
        self.smileSpace.openBool = not self.smileSpace.openBool
        self.smileSpace.volumeBool = False
        
        self.smileSpace.volumeButton.setStyleSheet("background-color: #050816;")
        self.smileSpace.openIntButton.setStyleSheet("background-color: #0c1226;")

        self.graph.update_graph()

class Stats(QWidget):
    def __init__(self, smileSpace):
        super().__init__()
        self.smileSpace = smileSpace

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5,5,5,5)

        self.setStyleSheet("""
                    QLabel: {
                    font-size: 16px; color: white;")
                    }
        """)

        layout.setSpacing(20)

        summary = QLabel("Volatility Data:")
        summary.setStyleSheet("font-weight: bold; font-size: 18px; color: white;")

        hline = QFrame()
        hline.setFrameShape(QFrame.Shape.HLine)
        hline.setFrameShadow(QFrame.Shadow.Sunken)
        hline.setStyleSheet("border: 1px solid white")

        layout.addWidget(hline)

        datas = self.smileSpace.terminal.chain['impliedVolatility'].to_numpy().tolist()

        avg_volt = QLabel(f"Average IV: {round(statistics.mean(datas), 3)}")

        avg_volt.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Maximum
        )
        stdev_volt = QLabel(f"Standard Dev IV: {round(statistics.stdev(datas), 3)}")
        stdev_volt.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Maximum
        )
        contracts = QLabel(f"Contracts: {len(datas)}")
        contracts.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Maximum
        )

        maxVol = max(datas)
        minVol = min(datas)
        skew = QLabel(f"IV Skew: {round(max(datas)-min(datas), 3)}")
        skew.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Maximum
        )

        layout.addWidget(avg_volt)
        layout.addWidget(stdev_volt)
        layout.addWidget(contracts)
        layout.addWidget(skew)

        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        






        

