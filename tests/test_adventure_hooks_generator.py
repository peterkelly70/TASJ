import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import random
import logging

# Suppress warnings during tests
logging.basicConfig(level=logging.ERROR)

# Add the project root to the path so we can import modules properly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from controller.adventure_hooks_generator import AdventureHooksGenerator


class TestAdventureHooksGenerator(unittest.TestCase):
    """Test cases for the AdventureHooksGenerator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock the OpenAI API key check
        with patch('os.getenv', return_value=None):
            self.generator = AdventureHooksGenerator()
        
        # Provide test data
        self.generator.worlds = [
            {
                "name": "TestWorld",
                "UWP": "A553A85-D",
                "remarks": "Hi In Cp",
                "zone": "",
                "bases": "NS",
                "stellar": "M2 V",
                "trade_codes": ["High Pop", "Industrial", "Capital"]
            }
        ]
    
    def test_uwp_summary(self):
        """Test the UWP summary function."""
        summary = self.generator.uwp_summary("A553A85-D")
        # The population code 'A' corresponds to 'teeming megacities' in the generator
        self.assertIn("teeming megacities", summary)
        self.assertIn("class A starport", summary)
        self.assertIn("TL-D", summary)
    
    def test_template_hook_generation(self):
        """Test that template-based hook generation works."""
        # Set a fixed seed for reproducibility
        random.seed(42)
        
        hook = self.generator.generate_template_hook()
        
        # Verify the hook contains expected elements
        self.assertIsInstance(hook, str)
        self.assertGreater(len(hook), 0)
        self.assertIn("TestWorld", hook)  # Should contain the world name
    
    def test_multiple_hooks_generation(self):
        """Test generating multiple hooks."""
        hooks = self.generator.generate_multiple_hooks(count=3, use_gpt=False)
        
        # Verify we get the right number of hooks
        self.assertEqual(len(hooks), 3)
        
        # Verify each hook is a non-empty string
        for hook in hooks:
            self.assertIsInstance(hook, str)
            self.assertGreater(len(hook), 0)
    
    def test_gpt_hook_generation(self):
        """Test GPT-enhanced hook generation with OpenAI unavailable."""
        # Make sure gpt_available is False for testing
        self.generator.gpt_available = False
        
        # When OpenAI is not available, generate_gpt_hook should return None
        hook = self.generator.generate_gpt_hook()
        self.assertIsNone(hook)
        
        # Test that generate_adventure_hook falls back to template-based generation
        hook = self.generator.generate_adventure_hook(use_gpt=True)
        self.assertIsNotNone(hook)
        self.assertIsInstance(hook, str)
        self.assertGreater(len(hook), 0)


if __name__ == '__main__':
    unittest.main()
