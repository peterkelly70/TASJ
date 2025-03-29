from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel

class PlanetView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Planet View Content"))
        self.setLayout(layout)
