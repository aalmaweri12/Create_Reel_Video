"""
Text-to-Video Tool

A tool for creating videos from text input with text-to-speech
narration and synchronized captions.

This package provides a complete pipeline for converting text
(particularly stories) into videos with the following features:
- Text-to-speech conversion using various engines
- Sentence-by-sentence caption generation
- Video processing and combining with background videos
- Customizable subtitle styles and voice options

Modules:
- tts: Text-to-speech conversion
- captions: Subtitle and caption generation
- video: Video processing and composition
- core: Main generator integrating all components
"""

# Import the main class for easy access
from .core import TextToVideoGenerator

# Version information
__version__ = '0.1.0'
__author__ = 'Your Name'
__email__ = 'your.email@example.com'

# Package exports
__all__ = ['TextToVideoGenerator']