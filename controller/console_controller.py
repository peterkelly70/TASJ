import logging
import sys
from PyQt6.QtWidgets import QStackedWidget, QTextEdit, QMessageBox
from PyQt6.QtCore import pyqtSignal, QObject

from view.console_view import ConsoleView
from controller.console_handler import ConsoleHandler
from controller.console_output import ConsoleOutput
from controller.console_updater import ConsoleUpdater

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
        
        # Initialize components
        self.console_handler = None
        self.console_output = None
        self.console_updater = ConsoleUpdater()
        
        # Set up logging and output redirection
        self._setup_logging()
        self._setup_console_output()
        
        # Log initial message
        logging.info("Console initialized and ready")

    def _setup_logging(self):
        """Set up logging to redirect to the console view."""
        # Create and configure the handler
        self.console_handler = ConsoleHandler(self.console_view)
        self.console_handler.setLevel(logging.INFO)
        self.console_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        )
        
        # Add handler to the root logger
        logging.getLogger().addHandler(self.console_handler)

    def _setup_console_output(self):
        """Set up console output redirection."""
        # Redirect stdout and stderr
        self.console_output = ConsoleOutput(self.console_view, sys.stdout)
        sys.stdout = self.console_output
        sys.stderr = ConsoleOutput(self.console_view, sys.stderr)

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
        # Handle QStackedWidget by finding or creating a console widget
        if isinstance(display_widget, QStackedWidget):
            display_widget = self._get_or_create_console_widget(display_widget)
        
        # Display current console text
        if hasattr(display_widget, 'setPlainText'):
            display_widget.setPlainText(self.get_console_text())
        
        # Start periodic updates
        self.console_updater.start_updates(display_widget, self.get_console_text)
            
    def _get_or_create_console_widget(self, stacked_widget):
        """Get or create a console widget within a QStackedWidget.
        
        Args:
            stacked_widget: The QStackedWidget to search or add to.
            
        Returns:
            The console text widget.
        """
        # Check if we already have a console widget in the stack
        for i in range(stacked_widget.count()):
            widget = stacked_widget.widget(i)
            if hasattr(widget, '_is_console_widget'):
                stacked_widget.setCurrentWidget(widget)
                return widget
        
        # Create a new console widget
        console_widget = QTextEdit()
        console_widget.setReadOnly(True)
        console_widget._is_console_widget = True
        stacked_widget.addWidget(console_widget)
        stacked_widget.setCurrentWidget(console_widget)
        
        return console_widget

    def log_cancel_operation(self, operation_name: str):
        """Log a cancelled operation and show a dialog.
        
        Args:
            operation_name: The name of the operation that was cancelled.
        """
        if not operation_name or not isinstance(operation_name, str):
            operation_name = "Unknown operation"
            
        message = f"Operation '{operation_name}' has been cancelled"
        
        try:
            # Log the cancellation
            logging.info(message)
            
            # Show dialog if main window is available
            if self.main_window:
                QMessageBox.information(
                    self.main_window,
                    "Operation Cancelled",
                    message
                )
        except Exception as e:
            # Fallback logging in case of errors
            print(f"Error in log_cancel_operation: {e}")
            print(message)

    def is_console_visible(self) -> bool:
        """Check if the console is currently visible.
        
        Returns:
            True if the console is visible, False otherwise.
        """
        try:
            return self.console_view.isVisible() if self.console_view else False
        except Exception:
            return False
    
    def get_console_text(self) -> str:
        """Get the current text in the console.
        
        Returns:
            The current console text, or empty string if unavailable.
        """
        try:
            if self.console_view and self.console_view.text_area:
                return self.console_view.text_area.toPlainText()
        except Exception as e:
            logging.error(f"Error getting console text: {e}")
        return ""
    
    def hide_console(self):
        """Hide the console window."""
        try:
            if self.console_view:
                self.console_view.close()
                # Stop updates when console is hidden
                self.console_updater.stop_updates()
        except Exception as e:
            logging.error(f"Error hiding console: {e}")
            
    def cleanup(self):
        """Clean up resources when the controller is destroyed."""
        try:
            # Stop updates
            self.console_updater.stop_updates()
            
            # Remove logging handler
            if self.console_handler:
                logging.getLogger().removeHandler(self.console_handler)
                
            # Restore original stdout/stderr if needed
            # Note: This is basic cleanup - full restoration would require 
            # storing original streams
            
        except Exception as e:
            logging.error(f"Error during console controller cleanup: {e}")
