#!/usr/bin/env python3
import sys
import os
import importlib.util

# Add the site-packages directory to Python's path
site_packages_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.venv', 'lib', 'python3.12', 'site-packages')
if os.path.exists(site_packages_path):
    sys.path.insert(0, site_packages_path)
    print(f"Added {site_packages_path} to Python path")

# Import and run the main module
main_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'main.py')
spec = importlib.util.spec_from_file_location("main", main_path)
main_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(main_module)
