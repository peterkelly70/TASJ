#!/usr/bin/env python3
import sys
import os

# Add the site-packages directory to Python's path
site_packages_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.venv', 'lib', 'python3.12', 'site-packages')
if os.path.exists(site_packages_path):
    sys.path.insert(0, site_packages_path)
    print(f"Added {site_packages_path} to Python path")
else:
    print(f"Warning: {site_packages_path} does not exist")

# Print the current Python path
print("Python path:")
for path in sys.path:
    print(f"  - {path}")

# Try to import mysql.connector
try:
    import mysql.connector
    print("Successfully imported mysql.connector")
except ImportError as e:
    print(f"Failed to import mysql.connector: {e}")

# List all available packages in site-packages
print("\nAvailable packages in site-packages:")
if os.path.exists(site_packages_path):
    packages = [d for d in os.listdir(site_packages_path) if os.path.isdir(os.path.join(site_packages_path, d))]
    mysql_packages = [p for p in packages if 'mysql' in p.lower()]
    print(f"MySQL-related packages: {mysql_packages}")
