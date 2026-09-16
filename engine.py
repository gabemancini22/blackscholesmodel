import sys
from gui.optionsCalculator import Window
from PySide6.QtWidgets import QApplication

app = QApplication(sys.argv)
app.setStyleSheet("""
    QWidget {
        background-color: #15171A;
        color: #E6E8EB;
    }

    QPushButton {
        background-color: #050816;
        border: 1px solid #343941;
        border-radius: 6px;
        padding: 8px 14px;
    }

    QPushButton:hover {
        background-color:  #0c1226;
    }

    QLineEdit {
        background-color: #1D2024;
        border: 1px solid #343941;
        border-radius: 5px;
        padding: 6px;
    }

    QCheckBox{
    border: 1px solid #6b6969;
    }  
""")

engine = Window()
engine.show()
sys.exit(app.exec())