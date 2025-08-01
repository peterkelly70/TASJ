from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
import pytest

from controller.console_controller import ConsoleController
from main import HitchhikersGuideToTheGalaxy

class TestConsole:
    """Test suite for the console functionality using pytest-qt"""
    
    @pytest.fixture
    def app(self, qtbot):
        """Create a QApplication instance for all tests"""
        app = QApplication([])
        yield app
        app.quit()
    
    @pytest.fixture
    def main_window(self, qtbot):
        """Create a test instance of the main window"""
        window = HitchhikersGuideToTheGalaxy()
        qtbot.addWidget(window)
        return window
    
    @pytest.fixture
    def controller(self, main_window):
        """Create a test instance of the console controller"""
        return ConsoleController(main_window)
    
    def test_console_view_creation(self, controller, qtbot):
        """Test that ConsoleView is created correctly"""
        console = controller.console_view
        
        # Verify console is created and hidden initially
        assert console is not None
        assert not console.isVisible()
        
        # Verify console properties
        assert hasattr(console, 'text_area')
        assert hasattr(console, 'clear_button')
        assert console.windowTitle() == "Console"
        assert console.size().width() == 600
        assert console.size().height() == 400
    
    def test_console_logging(self, controller, qtbot):
        """Test that logging messages appear in the console"""
        import logging
        test_message = "Test log message"
        
        # Show the console
        controller.show_console()
        qtbot.wait(100)  # Wait for the console to show
        
        # Log a message
        logging.info(test_message)
        
        # Wait for the logging to complete
        qtbot.wait(100)
        
        # Verify the message appears in the console
        text = controller.get_console_text()
        assert test_message in text
    
    def test_menu_integration(self, controller, qtbot):
        """Test that console menu item is properly integrated"""
        main_window = controller.main_window
        
        # Find the File menu
        file_menu = None
        for action in main_window.menuBar().actions():
            if action.text() == '&File':
                file_menu = action.menu()
                break
        
        assert file_menu is not None, "File menu should exist"
        
        # Find Console action
        console_action = None
        for action in file_menu.actions():
            if action.text() == '&Console':
                console_action = action
                break
        
        assert console_action is not None, "Console action should exist"
        assert console_action.shortcut().toString() == "Ctrl+L"
        
        # Hide the console
        controller.hide_console()
        assert not controller.is_console_visible()
        
        # Trigger the action to show it again
        qtbot.mouseClick(console_action, Qt.MouseButton.LeftButton)
        assert controller.is_console_visible()
    
    def test_cancel_operation(self, controller, qtbot):
        """Test that cancel operations are properly logged and show dialog"""
        operation_name = "Test Operation"
        
        # Show the console
        controller.show_console()
        qtbot.wait(100)
        
        # Log cancel operation
        controller.log_cancel_operation(operation_name)
        
        # Wait for the dialog to close
        qtbot.wait(100)
        
        # Verify message appears in console
        text = controller.get_console_text()
        assert operation_name in text
        assert "cancelled" in text.lower()
