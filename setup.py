#!/usr/bin/env python

from setuptools import setup, find_packages

# Utility function to read files
def read_file(file):
    with open(file, 'r', encoding='utf-8') as f:
        return f.read()

setup(
    name="tasj",
    version="0.1.0",
    author="Peter Kelly",
    author_email="your.email@example.com",
    description="AI-integrated database for Traveller Campaigns",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/TASJ",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "PyQt5>=5.15.0",
        "python-dotenv>=0.19.0",
        "mysql-connector-python>=8.0.26",
        "requests>=2.26.0",
    ],
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    entry_points={
        'console_scripts': [
            'tasj=tasj.cli:main',
        ],
    },
)
