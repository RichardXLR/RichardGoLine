#!/usr/bin/env python3
"""
Setup script for RichardGoLine - YouTube Downloader Ultra-Fast
"""
from setuptools import setup, find_packages
from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

setup(
    name="RichardGoLine",
    version="1.0.0",
    description="YouTube Downloader Ultra-Rápido com Máxima Qualidade",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Richard",
    python_requires=">=3.8",
    install_requires=[
        "yt-dlp>=2024.1.1",
    ],
    entry_points={
        "console_scripts": [
            "RichardGoLine=RichardGoLine:main",
            "RichardGoLine_GUI=RichardGoLine_GUI:main",
        ],
    },
    py_modules=["RichardGoLine", "RichardGoLine_GUI"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "Topic :: Multimedia :: Video",
        "Topic :: Internet :: WWW/HTTP",
    ],
    keywords="youtube downloader yt-dlp video audio mp3 4k 8k",
    project_urls={
        "Source": "https://github.com/RichardGoLine",
        "Issues": "https://github.com/RichardGoLine/issues",
    },
)