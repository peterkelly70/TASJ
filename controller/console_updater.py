"""Console updater for managing periodic updates of console content."""

from PyQt6.QtCore import QTimer, QObject, pyqtSignal
from typing import Optional, Callable


class ConsoleUpdater(QObject):
    """Manages periodic updates of console content in display widgets."""
    
    # Signal emitted when update fails
    update_failed = pyqtSignal(str)
    
    def __init__(self, update_interval: int = 2000):
        """Initialize the console updater.
        
        Args:
            update_interval: Update interval in milliseconds (default: 2000ms).
        """
        super().__init__()
        self.timer = QTimer()
        self.timer.setSingleShot(False)
        self.timer.timeout.connect(self._on_timeout)
        self.update_interval = update_interval
        self.display_widget = None
        self.get_console_text_func = None
        
    def start_updates(self, display_widget, get_console_text_func: Callable[[], str]):
        """Start periodic updates of the display widget.
        
        Args:
            display_widget: The widget to update with console content.
            get_console_text_func: Function that returns the current console text.
        """
        self.display_widget = display_widget
        self.get_console_text_func = get_console_text_func
        
        if not self.timer.isActive():
            self.timer.start(self.update_interval)
            
    def stop_updates(self):
        """Stop periodic updates."""
        self.timer.stop()
        self.display_widget = None
        self.get_console_text_func = None
        
    def set_update_interval(self, interval: int):
        """Set the update interval.
        
        Args:
            interval: Update interval in milliseconds.
        """
        self.update_interval = interval
        if self.timer.isActive():
            self.timer.setInterval(interval)
            
    def _on_timeout(self):
        """Handle timer timeout and update the display widget."""
        try:
            self._update_display_widget()
        except Exception as e:
            self.update_failed.emit(str(e))
            
    def _update_display_widget(self):
        """Update the display widget with the latest console content."""
        if not self.display_widget or not self.get_console_text_func:
            return
            
        # Don't update if text is selected (user might be trying to copy)
        if hasattr(self.display_widget, 'textCursor'):
            cursor = self.display_widget.textCursor()
            if cursor.hasSelection():
                return
                
            # Preserve cursor position
            position = cursor.position()
            
            # Store scroll position
            if hasattr(self.display_widget, 'verticalScrollBar'):
                scrollbar = self.display_widget.verticalScrollBar()
                scroll_pos = scrollbar.value()
            else:
                scroll_pos = None
                
            # Update text
            if hasattr(self.display_widget, 'setPlainText'):
                self.display_widget.setPlainText(self.get_console_text_func())
                
            # Restore cursor position
            cursor = self.display_widget.textCursor()
            cursor.setPosition(position)
            self.display_widget.setTextCursor(cursor)
            
            # Restore scroll position
            if scroll_pos is not None and hasattr(self.display_widget, 'verticalScrollBar'):
                scrollbar.setValue(scroll_pos)