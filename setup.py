#!/usr/bin/env python

from setuptools import setup, find_packages

# Utility function to read files
def read_file(file):
    with open(file, 'r', encoding='utf-8') as f:
        return f.read()

# Read the contents of the README file
long_description = read_file("README.md")

# Read the contents of the LICENSE file
license_text = read_file("LICENSE")

# Read the requirements from the requirements.txt file
def read_requirements(file):
    with open(file, 'r', encoding='utf-8') as f:
        return f.read().splitlines()

setup(
    name="TASJ",
    version="0.1.0",
    author="Peter Kelly",
    author_email="peter@computer-wizard.com.au",
    description="A Python project for TASJ.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license=license_text,  # This includes the full text of the license
    url="https://github.com/peterkelly70/TASJ",
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",  # GPL-3.0 License Classifier
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=read_requirements('requirements.txt'),
    entry_points={
        'console_scripts': [
            'tasj=tasj.cli:main',
        ],
    },
)
