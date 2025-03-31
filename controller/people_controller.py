from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
from typing import Any

class PeopleController:
    def __init__(self, db_instance: Any) -> None:
        self.db = db_instance

    def show_view(self, display_widget: QWidget) -> None:
        display_widget.setText("Characters button has been pushed")
