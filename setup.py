"""
Setup script for the text-to-video tool.

This module handles the installation of the text-to-video tool
and its dependencies, and sets up the command-line entry point.
"""

from setuptools import setup, find_packages

# Get version from src/__init__.py
import re
with open('src/__init__.py', 'r', encoding='utf-8') as f:
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", f.read(), re.M)
    version = version_match.group(1) if version_match else '0.1.0'

# Read long description from README.md
try:
    with open('README.md', 'r', encoding='utf-8') as f:
        long_description = f.read()
except FileNotFoundError:
    long_description = "A tool for creating videos from text with text-to-speech narration and synchronized captions."

setup(
    name="text2video",
    version=version,
    author="Your Name",
    author_email="your.email@example.com",
    description="Convert text to video with speech and captions",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/text-to-video-tool",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Multimedia :: Video",
        "Topic :: Text Processing",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.7",
    install_requires=[
        "moviepy>=1.0.3",
        "gTTS>=2.2.4",
        "pydub>=0.25.1",
        # Optional dependencies
        # "google-cloud-texttospeech>=2.11.0",
        # "pyttsx3>=2.90",
    ],
    extras_require={
        "google": ["google-cloud-texttospeech>=2.11.0"],
        "offline": ["pyttsx3>=2.90"],
        "dev": [
            "pytest>=6.0.0",
            "black>=21.5b2",
            "flake8>=3.9.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "text2video=cli.main:main",
        ],
    },
)