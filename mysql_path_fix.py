#!/usr/bin/env python3
import sys
import os
import site

# Create a .pth file in the site-packages directory
site_packages_dir = site.getsitepackages()[0]
pth_file_path = os.path.join(site_packages_dir, 'mysql_path.pth')

with open(pth_file_path, 'w') as f:
    f.write('/mnt/Work/Projects/TASJ/.venv/lib/python3.12/site-packages\n')
    
print(f"Created {pth_file_path} to add MySQL connector path")
print("You should now be able to run main.py directly")
