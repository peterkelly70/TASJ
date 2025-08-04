#!/usr/bin/env python3
"""
Debug script for the Traveller Map API search functionality.
This script tests the search API and prints the raw response structure.
"""

import json
import logging
from model.traveller_map_api_fixed_v2 import TravellerMapAPI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def debug_search_api():
    """Debug the Traveller Map API search functionality."""
    print("=== DEBUGGING TRAVELLER MAP API SEARCH ===")
    
    # Create API client
    api = TravellerMapAPI()
    
    # Test search for 'Regina'
    search_term = "Regina"
    print(f"\n1. Testing search for '{search_term}'...")
    try:
        results = api.search(search_term)
        if results:
            print("✓ Successfully retrieved search results")
            print(f"Raw response structure:")
            print(json.dumps(results, indent=2))
            
            # Print items if available
            if 'Results' in results and 'Items' in results['Results']:
                items = results['Results']['Items']
                print(f"\nFound {len(items)} items")
                for i, item in enumerate(items):
                    print(f"\nItem {i+1}:")
                    print(json.dumps(item, indent=2))
            else:
                print("No items found in search results")
        else:
            print("✗ Failed to retrieve search results")
    except Exception as e:
        print(f"✗ Error retrieving search results: {e}")
    
    # Test search for 'Spinward Marches'
    search_term = "Spinward Marches"
    print(f"\n2. Testing search for '{search_term}'...")
    try:
        results = api.search(search_term)
        if results:
            print("✓ Successfully retrieved search results")
            print(f"Raw response structure:")
            print(json.dumps(results, indent=2))
            
            # Print items if available
            if 'Results' in results and 'Items' in results['Results']:
                items = results['Results']['Items']
                print(f"\nFound {len(items)} items")
                for i, item in enumerate(items):
                    print(f"\nItem {i+1}:")
                    print(json.dumps(item, indent=2))
            else:
                print("No items found in search results")
        else:
            print("✗ Failed to retrieve search results")
    except Exception as e:
        print(f"✗ Error retrieving search results: {e}")
    
    print("\n=== DEBUG COMPLETED ===")

if __name__ == "__main__":
    debug_search_api()
