from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout,
                           QProgressBar, QSizePolicy)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QTextCursor, QFont

class ConsoleView(QWidget):
    """View for the console window."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Console")
        
        # Set up the layout
        self._layout = QVBoxLayout()
        self.setLayout(self._layout)
        
        # Create the text area
        self.text_area = QTextEdit(self)
        self.text_area.setReadOnly(True)
        self.text_area.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        
        # Use a standard font
        font = QFont()
        font.setPointSize(10)  # Smaller font size
        self.text_area.setFont(font)
        
        # Create progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(20)
        self.progress_bar.setValue(0)
        self.progress_bar.hide()  # Hidden by default
        
        # Create cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setEnabled(False)
        self.cancel_button.hide()  # Hidden by default
        
        # Create button layout
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        
        # Add widgets to layout
        self._layout.addWidget(self.text_area)
        self._layout.addWidget(self.progress_bar)
        self._layout.addLayout(button_layout)
        
        # Set size policy
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Set a reasonable default size
        self.resize(600, 400)
        
    def append_text(self, text: str):
        """Append text to the console."""
        self.text_area.moveCursor(QTextCursor.MoveOperation.End)
        self.text_area.insertPlainText(text)
        self.text_area.moveCursor(QTextCursor.MoveOperation.End)
        
    def clear_text(self):
        """Clear the console text."""
        self.text_area.clear()
        
    def update_progress_bar(self, progress: int):
        """Update the progress bar value."""
        self.progress_bar.setValue(progress)
        
    def show_progress_bar(self, enabled: bool):
        """Show/hide the progress bar and cancel button."""
        self.progress_bar.setVisible(enabled)
        self.cancel_button.setVisible(enabled)
        
    def enable_cancel_button(self, enabled: bool):
        """Enable/disable the cancel button."""
        self.cancel_button.setEnabled(enabled)
