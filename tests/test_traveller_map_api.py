import unittest
import sys
import os
from unittest.mock import MagicMock, patch
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt

# Create a QApplication instance for all tests
app = QApplication.instance() or QApplication(sys.argv)

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from view.traveller_map_api import TravellerMapAPI
from view.sector_view import SectorMapWidget


class TestTravellerMapAPI(unittest.TestCase):
    """Test cases for the Traveller Map API integration."""
    
    def setUp(self):
        """Set up the test environment."""
        # QApplication is already created at module level
        pass
        
    def tearDown(self):
        """Clean up after tests."""
        pass
    
    @patch('view.traveller_map_api.urllib.request.urlopen')
    def test_get_sector_map(self, mock_urlopen):
        """Test fetching a sector map from the API."""
        # Mock the response from urlopen
        mock_response = MagicMock()
        # Create a small test image as bytes
        with open('tests/test_data/test_image.png', 'rb') as f:
            mock_response.read.return_value = f.read()
        mock_urlopen.return_value = mock_response
        
        # Call the method under test
        result = TravellerMapAPI.get_sector_map("Test Sector")
        
        # Verify the result
        self.assertIsNotNone(result)
        self.assertIsInstance(result, QPixmap)
        self.assertFalse(result.isNull())
        
        # Verify the URL was constructed correctly
        mock_urlopen.assert_called_once()
        args, _ = mock_urlopen.call_args
        self.assertIn("travellermap.com/api/poster?sector=Test%20Sector", args[0])
    
    @patch('view.traveller_map_api.urllib.request.urlopen')
    def test_get_sector_map_with_options(self, mock_urlopen):
        """Test fetching a sector map with options."""
        # Mock the response
        mock_response = MagicMock()
        with open('tests/test_data/test_image.png', 'rb') as f:
            mock_response.read.return_value = f.read()
        mock_urlopen.return_value = mock_response
        
        # Call with options
        options = {
            "style": "print",
            "scale": 64,
            "border": 1
        }
        result = TravellerMapAPI.get_sector_map("Test Sector", options)
        
        # Verify result is valid
        self.assertIsNotNone(result)
        self.assertFalse(result.isNull())
        
        # Verify URL contains options
        mock_urlopen.assert_called_once()
        args, _ = mock_urlopen.call_args
        url = args[0]
        self.assertIn("sector=Test%20Sector", url)
        self.assertIn("style=print", url)
        self.assertIn("scale=64", url)
        self.assertIn("border=1", url)
    
    @patch('view.traveller_map_api.urllib.request.urlopen')
    def test_get_sector_map_error(self, mock_urlopen):
        """Test handling errors when fetching a sector map."""
        # Mock an exception
        mock_urlopen.side_effect = Exception("Network error")
        
        # Call the method
        result = TravellerMapAPI.get_sector_map("Test Sector")
        
        # Verify error handling
        self.assertIsNone(result)
    
    @patch('view.traveller_map_api.urllib.request.urlopen')
    def test_get_system_map(self, mock_urlopen):
        """Test fetching a system map from the API."""
        # Mock the response
        mock_response = MagicMock()
        with open('tests/test_data/test_image.png', 'rb') as f:
            mock_response.read.return_value = f.read()
        mock_urlopen.return_value = mock_response
        
        # Call the method
        result = TravellerMapAPI.get_system_map("Test Sector", "1010")
        
        # Verify the result
        self.assertIsNotNone(result)
        self.assertIsInstance(result, QPixmap)
        self.assertFalse(result.isNull())  # Ensure we're using the result variable
        
        # Verify URL
        mock_urlopen.assert_called_once()
        args, _ = mock_urlopen.call_args
        self.assertIn("travellermap.com/api/jumpmap?sector=Test%20Sector&hex=1010", args[0])


class TestSectorMapWidget(unittest.TestCase):
    """Test cases for the SectorMapWidget."""
    
    def setUp(self):
        """Set up the test environment."""
        # QApplication is already created at module level
        self.widget = SectorMapWidget()
        
    def tearDown(self):
        """Clean up after tests."""
        self.widget.deleteLater()
    
    @patch('view.traveller_map_api.TravellerMapAPI')
    def test_set_sector(self, mock_api):
        """Test setting a sector in the widget."""
        # Mock the API response
        mock_pixmap = QPixmap(100, 100)
        mock_api.get_sector_map.return_value = mock_pixmap
        
        # Create test sector data
        sector = {"name": "Test Sector", "id": "test-sector"}
        
        # Call the method
        self.widget.api = mock_api  # Replace the real API with our mock
        self.widget.set_sector(sector)
        
        # Verify sector name was set
        self.assertEqual(self.widget.sector_name, "Test Sector")
        
        # Since loading is asynchronous, we can't easily test the final state
        # but we can verify the initial state
        self.assertFalse(self.widget.loading_error)
        self.assertIsNone(self.widget.map_pixmap)


if __name__ == '__main__':
    # Create test data directory if it doesn't exist
    os.makedirs('tests/test_data', exist_ok=True)
    
    # Create a test image if it doesn't exist
    if not os.path.exists('tests/test_data/test_image.png'):
        test_pixmap = QPixmap(100, 100)
        test_pixmap.fill()  # Fill with default color
        test_pixmap.save('tests/test_data/test_image.png')
    
    unittest.main()
