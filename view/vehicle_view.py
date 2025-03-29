from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel

class VehicleView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Vehicle View Content"))
        self.setLayout(layout)
