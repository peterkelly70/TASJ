from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton, QWidget
from PyQt6.QtCore import Qt, pyqtSignal, QEvent
from typing import Optional

class ConsoleView(QDialog):
    """A dialog window that displays logging output"""
    
    # Signal for when text is appended
    text_appended = pyqtSignal(str)
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("Console")
        self.setModal(False)  # Allow interaction with main window
        
        # Set up the layout
        self._layout = QVBoxLayout()
        self.setLayout(self._layout)
        
        # Create the text area
        self.text_area = QTextEdit(self)
        self.text_area.setReadOnly(True)
        self.text_area.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        
        # Use a monospace font for better log readability
        font = self.text_area.font()
        font.setFamily("Monospace")
        self.text_area.setFont(font)
        
        self._layout.addWidget(self.text_area)
        
        # Add clear button
        self.clear_button = QPushButton("Clear", self)
        self.clear_button.clicked.connect(self.clear_console)
        self._layout.addWidget(self.clear_button)
        
        # Set a reasonable default size
        self.resize(600, 400)
        
        # Install event filter to handle cleanup
        self.installEventFilter(self)
    
    def append_text(self, text: str):
        """Add text to the console and scroll to bottom"""
        if not hasattr(self, 'text_area') or self.text_area is None:
            return
            
        try:
            self.text_area.append(text)
            # Ensure newest text is visible
            cursor = self.text_area.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            self.text_area.setTextCursor(cursor)
            
            # Emit signal for testing
            self.text_appended.emit(text)
        except RuntimeError:
            # If the widget has been deleted, just return
            return
    
    def clear_console(self):
        """Clear all text from the console"""
        if not hasattr(self, 'text_area') or self.text_area is None:
            return
            
        try:
            self.text_area.clear()
        except RuntimeError:
            # If the widget has been deleted, just return
            return
    
    def eventFilter(self, obj, event):
        """Handle events to ensure proper cleanup"""
        if event.type() == QEvent.Type.Close:
            # When the dialog is closed, ensure we don't have any dangling references
            self.text_area = None
            self.clear_button = None
            self._layout = None
            return True
        return super().eventFilter(obj, event)
