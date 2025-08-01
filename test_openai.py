#!/usr/bin/env python3
"""
Test script to check if the OpenAI package is accessible.
"""

import sys
import os

def main():
    print("Python version:", sys.version)
    print("Python executable:", sys.executable)
    print("Python path:", sys.path)
    
    print("\nChecking for OpenAI package:")
    try:
        import openai
        print("✅ OpenAI package is installed and accessible.")
        print("OpenAI version:", openai.__version__)
        print("OpenAI package location:", openai.__file__)
        
        # Check if API key is available
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            print("✅ OpenAI API key is available in environment.")
        else:
            print("❌ OpenAI API key is not available in environment.")
    except ImportError as e:
        print("❌ OpenAI package is not accessible.")
        print("Error:", e)
    
    # Check sys.modules to see if openai was previously imported
    if 'openai' in sys.modules:
        print("\nOpenAI is in sys.modules.")
    else:
        print("\nOpenAI is NOT in sys.modules.")

if __name__ == "__main__":
    main()
