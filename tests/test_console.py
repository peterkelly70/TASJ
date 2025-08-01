import unittest
from unittest.mock import Mock, patch, MagicMock
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QDialog
import sys

class TestConsole(unittest.TestCase):
    """Test suite for the console functionality"""
    
    @classmethod
    def setUpClass(cls):
        """Create QApplication instance for all tests"""
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
    
    def setUp(self):
        """Set up test fixtures"""
        # Create a real QMainWindow for testing
        self.main_window = QMainWindow()
        self.addCleanup(self.main_window.deleteLater)
    
    @patch('view.console_view.QTextEdit')
    @patch('view.console_view.QPushButton')
    def test_console_view_creation(self, mock_button, mock_text_edit):
        """Test that ConsoleView is created correctly"""
        from view.console_view import ConsoleView
        
        # Create console view
        console = ConsoleView(self.main_window)
        self.assertIsNotNone(console)
        self.assertTrue(hasattr(console, 'text_area'))
        mock_text_edit.assert_called_once()
        
        # Verify layout setup
        self.assertEqual(console.layout().count(), 2)  # Text area and button
        
        # Verify button setup
        mock_button.assert_called_once()
        self.assertEqual(console.clear_button.text(), "Clear")
        
        # Verify console view functionality
        self.assertTrue(console.isVisible())
        self.assertIsInstance(console.text_area, mock_text_edit.return_value.__class__)
        self.assertIsInstance(console.clear_button, mock_button.return_value.__class__)
    
    @patch('view.console_view.ConsoleView')
    def test_console_logging_handler(self, mock_console_view):
        """Test that logging is properly redirected to console"""
        from controller.console_controller import ConsoleController
        import logging
        
        # Create controller and store reference (needed for cleanup)
        controller = ConsoleController(self.main_window)
        mock_instance = mock_console_view.return_value
        
        # Simulate logging
        test_message = "Test log message"
        logging.getLogger().info(test_message)
        
        # Verify the message was sent to the console view
        mock_instance.append_text.assert_called_once()
        # Check that the logged message contains our test message
        log_text = mock_instance.append_text.call_args[0][0]
        self.assertIn(test_message, log_text)
    
    @patch('view.console_view.ConsoleView')
    def test_menu_integration(self, mock_console_view):
        """Test that console menu item is properly integrated"""
        from controller.console_controller import ConsoleController
        
        # Create controller and store reference (needed for cleanup)
        controller = ConsoleController(self.main_window)
        
        # Get the File menu
        file_menu = None
        for action in self.main_window.menuBar().actions():
            if action.text() == '&File':
                file_menu = action.menu()
                break
        
        self.assertIsNotNone(file_menu, "File menu should exist")
        
        # Find Console action
        console_action = None
        for action in file_menu.actions():
            if action.text() == '&Console':
                console_action = action
                break
        
        self.assertIsNotNone(console_action, "Console action should exist")
        self.assertEqual(console_action.shortcut().toString(), "Ctrl+L")
        
        # Simulate menu action trigger
        console_action.trigger()
        
        # Verify console is shown
        mock_console_view.return_value.show.assert_called_once()
        
        # Verify console is not shown again when menu item is triggered again
        console_action.trigger()
        self.assertEqual(mock_console_view.return_value.show.call_count, 1)
    
    @patch('view.console_view.ConsoleView')
    @patch('PyQt6.QtWidgets.QMessageBox')
    def test_cancel_operation_logging(self, mock_dialog, mock_console_view):
        """Test that cancel operations are properly logged and show dialog"""
        from controller.console_controller import ConsoleController
        
        # Setup mocks
        mock_instance = mock_console_view.return_value
        
        # Create controller and store reference (needed for cleanup)
        controller = ConsoleController(self.main_window)
        
        # Simulate cancel operation
        operation_name = "Test Operation"
        controller.log_cancel_operation(operation_name)
        
        # Verify dialog shown
        mock_dialog.information.assert_called_once()
        
        # Verify logged to console
        mock_instance.append_text.assert_called()
        
        # Verify log contains operation name and 'cancelled'
        log_text = mock_instance.append_text.call_args[0][0]
        self.assertIn(operation_name, log_text)
        self.assertIn("cancelled", log_text.lower())

if __name__ == '__main__':
    unittest.main()
