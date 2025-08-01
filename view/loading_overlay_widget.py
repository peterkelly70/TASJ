import logging
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush

logger = logging.getLogger(__name__)

class LoadingOverlayWidget(QWidget):
    """
    A semi-transparent overlay widget that displays a loading spinner and message.
    This can be placed on top of any widget to indicate loading/processing.
    """
    
    def __init__(self, parent=None, message="Loading..."):
        super().__init__(parent)
        
        # Set up the widget to be transparent and on top
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Store the loading message
        self.message = message
        
        # Set up layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Animation variables
        self.angle = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.rotate_spinner)
        self.timer.start(50)  # Update every 50ms for smooth animation
        
        # Make sure this widget is on top
        self.raise_()
        self.setVisible(False)  # Initially hidden
        
    def set_message(self, message):
        """Set the loading message."""
        self.message = message
        self.update()
        
    def show_loading(self, message=None):
        """Show the loading overlay with an optional custom message."""
        if message:
            self.message = message
        self.setVisible(True)
        self.raise_()
        
    def hide_loading(self):
        """Hide the loading overlay."""
        self.setVisible(False)
        
    def rotate_spinner(self):
        """Rotate the spinner animation."""
        self.angle = (self.angle + 10) % 360
        self.update()
        
    def resizeEvent(self, event):
        """Handle resize events to ensure the overlay covers the parent widget."""
        if self.parentWidget():
            self.setGeometry(0, 0, self.parentWidget().width(), self.parentWidget().height())
        super().resizeEvent(event)
        
    def paintEvent(self, event):
        """Paint the loading overlay with spinner and message."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Semi-transparent background
        background_color = QColor(0, 0, 0, 180)  # RGBA with alpha for transparency
        painter.fillRect(self.rect(), background_color)
        
        # Draw spinner
        center_x = self.width() / 2
        center_y = self.height() / 2 - 20  # Offset to make room for text
        outer_radius = 30
        inner_radius = 15
        
        # Draw spinner segments
        for i in range(8):
            segment_angle = self.angle + i * 45
            alpha = 255 - (i * 32)  # Fade out segments
            
            painter.save()
            painter.translate(center_x, center_y)
            painter.rotate(segment_angle)
            
            # Draw segment
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(255, 255, 255, alpha)))
            
            # Draw a rounded rectangle as a segment
            painter.drawRoundedRect(-4, -outer_radius, 8, outer_radius - inner_radius, 4, 4)
            
            painter.restore()
        
        # Draw message text
        painter.setPen(QPen(Qt.GlobalColor.white))
        text_rect = self.rect().adjusted(0, center_y + outer_radius, 0, 0)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, self.message)
