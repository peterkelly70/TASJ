from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QTabWidget, QTextEdit)

class ControlController:
    def __init__(self, main_window):
        self.main_window = main_window

    def show_control_view(self):
        # Create the main control widget
        control_widget = QWidget()
        control_layout = QVBoxLayout(control_widget)

        # Create the tab widget
        tab_widget = QTabWidget()

        # Create the console tab
        console_tab = QWidget()
        console_layout = QVBoxLayout(console_tab)
        self.console_text_edit = QTextEdit()
        self.console_text_edit.setReadOnly(True)
        console_layout.addWidget(self.console_text_edit)
        tab_widget.addTab(console_tab, "Console")

        # Create the data tab (currently empty)
        data_tab = QWidget()
        data_layout = QVBoxLayout(data_tab)
        tab_widget.addTab(data_tab, "Data")

        # Create the SQL tab (currently empty)
        sql_tab = QWidget()
        sql_layout = QVBoxLayout(sql_tab)
        tab_widget.addTab(sql_tab, "SQL")

        # Add the tab widget to the control layout
        control_layout.addWidget(tab_widget)

        # Set the control widget as the central widget
        self.main_window.setCentralWidget(control_widget)

    def append_to_console(self, message):
        self.console_text_edit.append(message)
