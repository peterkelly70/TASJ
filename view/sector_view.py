from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel

class SectorView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Sector View Content"))
        self.setLayout(layout)
