"""Console output redirection for capturing stdout/stderr."""

import sys
from typing import Optional, TextIO


class ConsoleOutput:
    """Redirects stdout/stderr to a console view while maintaining original output."""
    
    def __init__(self, console_view=None, original_stream: Optional[TextIO] = None):
        """Initialize the console output redirector.
        
        Args:
            console_view: The console view to write to.
            original_stream: The original stream to also write to (defaults to stdout).
        """
        self.console_view = console_view
        self.original_stream = original_stream or sys.stdout
        
    def set_console_view(self, console_view):
        """Set the console view for this output redirector.
        
        Args:
            console_view: The console view to write to.
        """
        self.console_view = console_view
        
    def write(self, text: str):
        """Write text to both the console view and original stream.
        
        Args:
            text: The text to write.
        """
        try:
            if self.console_view:
                self.console_view.append_text(text)
        except Exception:
            # Continue even if console view fails
            pass
            
        # Always write to original stream
        self.original_stream.write(text)
        
    def flush(self):
        """Flush the original stream."""
        self.original_stream.flush()
        
    def __getattr__(self, attr):
        """Delegate any other attributes to the original stream."""
        return getattr(self.original_stream, attr)