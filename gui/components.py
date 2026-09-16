from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout, QFrame
from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QStackedWidget, QSizePolicy

class Title(QWidget):
    def __init__(self, terminal):
        super().__init__()
        self.terminal = terminal

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(20)
        if self.terminal.isPut: mainTit = QLabel(f"{self.terminal.ticker}: Put")
        else: mainTit = QLabel(f"{self.terminal.ticker}: Call")
        layout.addWidget(mainTit)

        pricing = QLabel(f"Stock Price: ${round(self.terminal.stock, 2)}")
        layout.addWidget(pricing)

        expiration = QLabel(f"Expiration Date: "+terminal.exp_date)
        layout.addWidget(expiration)

        self.setStyleSheet("""
        QLabel{
        color: white;
        font-size: 30px;
        }
        """)
    
class SubTitle(QWidget):
    def __init__(self, terminal, row):
        super().__init__()

        self.terminal = terminal
        self.row = row

        self.SLayout = QHBoxLayout(self)
        self.SLayout.setSpacing(30)
        self.SLayout.setContentsMargins(5, 5, 5, 5)

        self.optionInfo = self.terminal.chain.iloc[self.row]

        self.contractName = self.optionInfo["contractSymbol"]
        self.strike = self.optionInfo["strike"]
        self.bid = self.optionInfo["bid"]
        self.ask = self.optionInfo["ask"]
        self.impliedVolatility = self.optionInfo["impliedVolatility"]

        self.contractLabel = QLabel(f"Contract: {self.contractName}")
        self.strikeLabel = QLabel(f"Strike: ${self.strike:.2f}")
        self.bidLabel = QLabel(f"Bid: ${self.bid:.2f}")
        self.askLabel = QLabel(f"Ask: ${self.ask:.2f}")
        self.ivLabel = QLabel(f"Implied Volatility: {self.impliedVolatility:.2%}")

        self.SLayout.addWidget(self.contractLabel)
        self.SLayout.addWidget(self.strikeLabel)
        self.SLayout.addWidget(self.bidLabel)
        self.SLayout.addWidget(self.askLabel)
        self.SLayout.addWidget(self.ivLabel)

        self.SLayout.addStretch()

        self.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 22px;
            }
        """)