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
        try:
            print("ConsoleController: Starting initialization")
            super().__init__()
            print("ConsoleController: Super init complete")
            self.main_window = main_window
            print("ConsoleController: Main window reference set")
            
            try:
                print("ConsoleController: Creating ConsoleView")
                self.console_view = ConsoleView(self.main_window)
                print("ConsoleController: ConsoleView created")
                self.console_view.hide()
                print("ConsoleController: ConsoleView hidden")
            except Exception as e:
                print(f"ConsoleController: Error creating ConsoleView: {str(e)}")
                import traceback
                traceback.print_exc()
                # Create a dummy console view to prevent further errors
                self.console_view = None
                raise
                
            try:
                print("ConsoleController: Setting up logging")
                self.setup_logging()
                print("ConsoleController: Logging setup complete")
            except Exception as e:
                print(f"ConsoleController: Error setting up logging: {str(e)}")
                import traceback
                traceback.print_exc()
                # Continue without custom logging
                
            try:
                print("ConsoleController: Setting up console output")
                self.setup_console_output()
                print("ConsoleController: Console output setup complete")
            except Exception as e:
                print(f"ConsoleController: Error setting up console output: {str(e)}")
                import traceback
                traceback.print_exc()
                # Continue without console output redirection
            
            # Log initial message
            print("ConsoleController: Initialization complete, logging success message")
            logging.info("Console initialized and ready")
            
        except Exception as e:
            print(f"ConsoleController: CRITICAL ERROR in initialization: {str(e)}")
            import traceback
            traceback.print_exc()

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
        try:
            print("ConsoleController: Creating ConsoleOutput class")
            class ConsoleOutput:
                def __init__(self, console_view):
                    print("ConsoleOutput: Initializing")
                    self.console_view = console_view
                    self.stdout = sys.stdout
                    self.stderr = sys.stderr
                    print("ConsoleOutput: Initialized")

                def write(self, text):
                    try:
                        if self.console_view:
                            # Only try to append text if it's not empty
                            if text.strip():
                                self.console_view.append_text(text)
                    except Exception:
                        # Don't use print here to avoid recursion
                        pass
                    # Always write to the original stdout
                    self.stdout.write(text)

                def flush(self):
                    try:
                        self.stdout.flush()
                    except Exception:
                        # Don't use print here to avoid recursion
                        pass

                def __getattr__(self, attr):
                    try:
                        return getattr(self.stdout, attr)
                    except Exception:
                        # Don't use print here to avoid recursion
                        return None

            print("ConsoleController: ConsoleOutput class created")
            
            # Create and apply stdout/stderr redirects
            print("ConsoleController: Creating and applying stdout/stderr redirects")
            self.stdout_redirect = ConsoleOutput(self.console_view)
            self.stderr_redirect = ConsoleOutput(self.console_view)
            
            # Apply the redirects
            print("ConsoleController: Applying redirects")
            sys.stdout = self.stdout_redirect
            sys.stderr = self.stderr_redirect
            print("ConsoleController: Redirects applied successfully")
        except Exception as e:
            print(f"ConsoleController: Error in setup_console_output: {str(e)}")
            import traceback
            traceback.print_exc()

    def show_console(self):
        """Show the console view in the main window's widget view."""
        try:
            # Clear the widget view layout
            while self.main_window.main_widget_layout.count():
                item = self.main_window.main_widget_layout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.setParent(None)
            
            # Add console view to the widget view
            self.main_window.main_widget_layout.addWidget(self.console_view)
            
            # Switch to the widget view in the stacked widget
            self.main_window.main_container.setCurrentIndex(1)  # Index 1 is the widget view
            
            # Make console view visible
            self.console_view.show()
            self.console_view.raise_()  # Bring to front
            
            # Emit signal and activate window
            self.console_shown.emit()
            self.main_window.activateWindow()
            
            # Log that console view is now displayed
            logging.info("Console view displayed in main view")
        except Exception as e:
            print(f"Error showing console: {str(e)}")
            import traceback
            traceback.print_exc()

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
