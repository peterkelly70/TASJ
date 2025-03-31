import logging
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout, QFileDialog, QMessageBox
from PyQt6.QtCore import pyqtSignal, QObject
from view.console_view import ConsoleView
import sys

class ConsoleController(QObject):
    """Controller for managing the console view and logging."""
    
    # Signal for when the console is shown
    console_shown = pyqtSignal()
    
    def __init__(self, main_window):
        """Initialize the console controller."""
        super().__init__()
        self.main_window = main_window
        self.console_view = ConsoleView(self.main_window)
        self.console_view.hide()
        self.setup_logging()
        self.setup_console_output()
        
        # Log initial message
        logging.info("Console initialized and ready")

    def setup_logging(self):
        """Set up logging to redirect to the console view."""
        # Create a custom handler that will write to the console view
        class ConsoleHandler(logging.Handler):
            def __init__(self, console_view):
                super().__init__()
                self.console_view = console_view
                
            def emit(self, record):
                msg = self.format(record)
                if self.console_view:
                    self.console_view.append_text(msg + '\n')  # Append newline character

        # Create and configure the handler
        handler = ConsoleHandler(self.console_view)
        handler.setLevel(logging.INFO)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        
        # Add handler to the root logger
        logging.getLogger().addHandler(handler)

    def setup_console_output(self):
        """Set up console output redirection."""
        class ConsoleOutput:
            def __init__(self, console_view):
                self.console_view = console_view
                self.stdout = sys.stdout
                self.stderr = sys.stderr

            def write(self, text):
                if self.console_view:
                    self.console_view.append_text(text)
                self.stdout.write(text)

            def flush(self):
                self.stdout.flush()

            def __getattr__(self, attr):
                return getattr(self.stdout, attr)

        # Redirect stdout and stderr
        sys.stdout = ConsoleOutput(self.console_view)
        sys.stderr = ConsoleOutput(self.console_view)

    def show_console(self):
        """Show the console view."""
        if not self.console_view.isVisible():
            self.console_view.show()
            self.console_view.raise_()  # Bring to front
            self.console_shown.emit()
            self.main_window.activateWindow()

    def log_cancel_operation(self, operation_name: str):
        """Log a cancelled operation and show a dialog"""
        message = f"Operation '{operation_name}' has been cancelled"
        
        # Log the cancellation
        logging.info(message)
        
        # Show dialog
        QMessageBox.information(
            self.main_window,
            "Operation Cancelled",
            message
        )

    def is_console_visible(self) -> bool:
        """Check if the console is currently visible."""
        return self.console_view.isVisible()
    
    def get_console_text(self) -> str:
        """Get the current text in the console."""
        return self.console_view.text_area.toPlainText()
    
    def hide_console(self):
        """Hide the console window."""
        self.console_view.close()
