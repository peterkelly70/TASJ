from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPlainTextEdit, QPushButton, QHBoxLayout, QProgressBar, QSizePolicy
from PyQt6.QtGui import QFont, QTextCursor, QColor
from PyQt6.QtCore import QTimer, Qt, pyqtSignal

class ConsoleView(QWidget):
    """View for the console window."""
    
    textAppended = pyqtSignal(str)
    textCleared = pyqtSignal()
    progressUpdated = pyqtSignal(int)
    progressBarShown = pyqtSignal(bool)
    cancelButtonEnabled = pyqtSignal(bool)

    def __init__(self, parent=None):
        try:
            print("ConsoleView: Starting initialization")
            super().__init__(parent)
            print("ConsoleView: Super init complete")
            self.setWindowTitle("Console")
            print("ConsoleView: Window title set")
            
            # Set up the layout
            try:
                print("ConsoleView: Creating layout")
                self._layout = QVBoxLayout()
                print("ConsoleView: Layout created")
                self.setLayout(self._layout)
                print("ConsoleView: Layout set")
            except Exception as e:
                print(f"ConsoleView: Error creating layout: {str(e)}")
                import traceback
                traceback.print_exc()
                raise
            
            # Create the text area - using QPlainTextEdit which is better for console-like output
            try:
                print("ConsoleView: Creating text area")
                self.text_area = QPlainTextEdit(self)
                print("ConsoleView: Text area created")
                self.text_area.setReadOnly(True)
                self.text_area.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
                self.text_area.setMaximumBlockCount(5000)  # Limit to prevent memory issues
                print("ConsoleView: Text area properties set")
                
                # Set a dark background with green text for console-like appearance
                self.text_area.setStyleSheet("""
                    QPlainTextEdit {
                        background-color: #000000;
                        color: #00FF00;
                        border: 1px solid #333333;
                    }
                """)
                print("ConsoleView: Text area stylesheet set")
                
                # Use a standard font
                font = QFont()
                font.setPointSize(10)  # Smaller font size
                self.text_area.setFont(font)
                print("ConsoleView: Text area font set")
            except Exception as e:
                print(f"ConsoleView: Error creating text area: {str(e)}")
                import traceback
                traceback.print_exc()
                raise
            
            try:
                # Create progress bar
                print("ConsoleView: Creating progress bar")
                self.progress_bar = QProgressBar()
                self.progress_bar.setFixedHeight(20)
                self.progress_bar.setValue(0)
                self.progress_bar.hide()  # Hidden by default
                print("ConsoleView: Progress bar created and configured")
                
                # Create cancel button
                print("ConsoleView: Creating cancel button")
                self.cancel_button = QPushButton("Cancel")
                self.cancel_button.setEnabled(False)
                self.cancel_button.hide()  # Hidden by default
                print("ConsoleView: Cancel button created and configured")
            except Exception as e:
                print(f"ConsoleView: Error creating progress bar or cancel button: {str(e)}")
                import traceback
                traceback.print_exc()
                # Continue without progress bar or cancel button
                self.progress_bar = None
                self.cancel_button = None
            
            try:
                # Create button layout
                print("ConsoleView: Creating button layout")
                button_layout = QHBoxLayout()
                button_layout.addStretch()
                if self.cancel_button:
                    button_layout.addWidget(self.cancel_button)
                print("ConsoleView: Button layout created")
                
                # Add widgets to layout
                self._layout.addWidget(self.text_area)
                if self.progress_bar:
                    self._layout.addWidget(self.progress_bar)
                self._layout.addLayout(button_layout)
                print("ConsoleView: Widgets added to layout")
            except Exception as e:
                print(f"ConsoleView: Error setting up layout: {str(e)}")
                import traceback
                traceback.print_exc()
                # Continue with partial layout
            
            try:
                # Set size policy
                print("ConsoleView: Setting size policy")
                self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
                print("ConsoleView: Size policy set")
                
                # Set a reasonable default size
                print("ConsoleView: Setting default size")
                self.resize(600, 400)
                print("ConsoleView: Default size set")
            except Exception as e:
                print(f"ConsoleView: Error setting size properties: {str(e)}")
                import traceback
                traceback.print_exc()
                # Continue without size settings
                
            print("ConsoleView: Initialization complete")
        except Exception as e:
            print(f"ConsoleView: CRITICAL ERROR in initialization: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
        
    def append_text(self, text: str):
        """Append text to the console."""
        # Directly append the text - this is the most reliable method
        self.text_area.appendPlainText(text.rstrip())

        # Ensure we're at the bottom
        self.text_area.moveCursor(QTextCursor.MoveOperation.End)

        # Process events to ensure UI updates immediately
        QTimer.singleShot(1, self.text_area.repaint)
        
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
