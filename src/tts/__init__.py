"""
Text-to-Speech module for the text-to-video tool.

This module provides functionality for converting text to speech
using various TTS engines, with specific optimizations for storytelling.
"""

from .tts_engine import TTSEngine, GoogleTTS, GTTS, PyttsxTTS

__all__ = ['TTSEngine', 'GoogleTTS', 'GTTS', 'PyttsxTTS']