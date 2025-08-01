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
        """Show the console view as a separate window."""
        if not self.console_view.isVisible():
            self.console_view.show()
            self.console_view.raise_()  # Bring to front
            self.console_shown.emit()
            self.main_window.activateWindow()
            
    def show_view(self, display_widget):
        """Show console content in the main view widget.
        
        This follows the pattern used by other controllers to display content
        in the main window rather than as a separate window.
        """
        # Get the current console text
        console_text = self.get_console_text()
        
        # Display it in the main view widget
        display_widget.setPlainText(console_text)
        
        # Set up a timer to periodically update the main view with console content
        # This ensures the main view stays in sync with console output
        if not hasattr(self, 'update_timer'):
            from PyQt6.QtCore import QTimer
            self.update_timer = QTimer()
            self.update_timer.timeout.connect(lambda: self._update_main_view(display_widget))
            self.update_timer.start(2000)  # Update every 2 seconds instead of 500ms
            
    def _update_main_view(self, display_widget):
        """Update the main view with the latest console content."""
        if display_widget:
            # Don't update if text is selected (user might be trying to copy)
            cursor = display_widget.textCursor()
            if cursor.hasSelection():
                return
                
            # Preserve cursor position
            position = cursor.position()
            
            # Store scroll position
            scrollbar = display_widget.verticalScrollBar()
            scroll_pos = scrollbar.value()
            
            # Update text
            display_widget.setPlainText(self.get_console_text())
            
            # Restore cursor position
            cursor = display_widget.textCursor()
            cursor.setPosition(position)
            display_widget.setTextCursor(cursor)
            
            # Restore scroll position
            scrollbar.setValue(scroll_pos)

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
