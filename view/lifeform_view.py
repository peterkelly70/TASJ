from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel

class LifeformView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Lifeform View Content"))
        self.setLayout(layout)
