"""Console logging handler for redirecting log messages to the console view."""

import logging
from typing import Optional


class ConsoleHandler(logging.Handler):
    """Custom logging handler that writes to a console view."""
    
    def __init__(self, console_view=None):
        """Initialize the handler with an optional console view.
        
        Args:
            console_view: The console view to write to. Can be set later with set_console_view.
        """
        super().__init__()
        self.console_view = console_view
        
    def set_console_view(self, console_view):
        """Set the console view for this handler.
        
        Args:
            console_view: The console view to write to.
        """
        self.console_view = console_view
        
    def emit(self, record: logging.LogRecord):
        """Emit a log record to the console view.
        
        Args:
            record: The log record to emit.
        """
        try:
            if self.console_view:
                msg = self.format(record)
                self.console_view.append_text(msg + '\n')
        except Exception:
            # Avoid recursion if logging the error would cause another error
            self.handleError(record)