#!/usr/bin/env python3
"""
Test script for OpenAI API integration in the mission generator.

This script helps debug and fix issues with the OpenAI API calls and database constraints.
"""

import os
import sys
import logging
from dotenv import load_dotenv
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables from multiple potential locations
load_dotenv()  # Default .env file
load_dotenv("tasj.env")  # Project-specific env file
load_dotenv("config/.env")  # Config directory env file

# Check if OpenAI API key is available
api_key = os.getenv("OPENAI_API_KEY")
if api_key:
    logger.info(f"OpenAI API key found. First 10 chars: {api_key[:10]}...")
else:
    logger.error("No OpenAI API key found. Please check your environment variables.")
    sys.exit(1)

# Try to import OpenAI
try:
    from openai import OpenAI
    logger.info("OpenAI package is installed.")
except ImportError as e:
    logger.error(f"Failed to import OpenAI: {e}")
    logger.error("Please install the OpenAI package: pip install openai")
    sys.exit(1)

def test_openai_connection():
    """Test the connection to the OpenAI API."""
    try:
        # Create OpenAI client
        client = OpenAI(api_key=api_key)
        
        # Test with a simple completion
        logger.info("Testing OpenAI API connection with a simple completion...")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello, are you working?"}
            ]
        )
        
        logger.info(f"Response received: {response.choices[0].message.content}")
        logger.info("OpenAI API connection test successful!")
        return True
    except Exception as e:
        logger.error(f"Error testing OpenAI API connection: {e}")
        return False

def test_image_generation():
    """Test the image generation API."""
    try:
        # Create OpenAI client
        client = OpenAI(api_key=api_key)
        
        # Test with a simple image generation
        logger.info("Testing OpenAI image generation API...")
        response = client.images.generate(
            model="dall-e-3",
            prompt="A simple test image of a spaceship in orbit around a planet",
            n=1,
            size="1024x1024"
        )
        
        logger.info(f"Image URL: {response.data[0].url}")
        logger.info("OpenAI image generation test successful!")
        return True
    except Exception as e:
        logger.error(f"Error testing OpenAI image generation: {e}")
        return False

def main():
    """Main function to run all tests."""
    logger.info("Starting OpenAI API tests...")
    
    # Test OpenAI connection
    if not test_openai_connection():
        logger.error("OpenAI API connection test failed.")
        return
    
    # Test image generation
    if not test_image_generation():
        logger.error("OpenAI image generation test failed.")
        return
    
    logger.info("All tests completed successfully!")

if __name__ == "__main__":
    main()
