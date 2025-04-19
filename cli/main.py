"""
Main entry point for the text-to-video tool CLI.

This module provides the main command-line interface for
creating videos from text with text-to-speech narration
and synchronized captions.
"""

import os
import sys
import argparse
import logging
import textwrap
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """
    Main entry point for the text-to-video command-line tool.
    """
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="Convert text to video with speech and captions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
        Examples:
          # Basic usage with text from a file
          text2video --text story.txt --bg-video background.mp4 --output story_video.mp4
          
          # Using Google Cloud TTS with a specific voice
          text2video --text story.txt --bg-video background.mp4 --output story_video.mp4 --tts google_cloud --voice en-US-Neural2-F
          
          # Customizing subtitle style
          text2video --text story.txt --bg-video background.mp4 --output story_video.mp4 --font-size 28 --font-color white
        """)
    )
    
    # Input/output options
    input_group = parser.add_argument_group('Input/Output Options')
    text_group = input_group.add_mutually_exclusive_group(required=True)
    text_group.add_argument('--text', help='Path to text file containing the story')
    text_group.add_argument('--text-input', help='Direct text input')
    input_group.add_argument('--bg-video', required=True, help='Path to background video')
    input_group.add_argument('--output', required=True, help='Path to output video')
    
    # TTS options
    tts_group = parser.add_argument_group('Text-to-Speech Options')
    tts_group.add_argument('--tts', choices=['google_cloud', 'gtts', 'pyttsx3'], default='gtts',
                          help='Text-to-speech engine to use (default: gtts)')
    tts_group.add_argument('--voice', help='Voice name/ID to use for speech')
    tts_group.add_argument('--language', default='en', help='Language code (default: en)')
    tts_group.add_argument('--api-key', help='Path to Google Cloud API key file (for google_cloud TTS)')
    tts_group.add_argument('--list-voices', action='store_true', help='List available voices and exit')
    
    # Caption options
    caption_group = parser.add_argument_group('Caption Options')
    caption_group.add_argument('--caption-approach', choices=['sentence', 'paragraph', 'word', 'simple'],
                              default='sentence', help='Caption generation approach (default: sentence)')
    caption_group.add_argument('--font-name', default='Arial', help='Font name for captions (default: Arial)')
    caption_group.add_argument('--font-size', type=int, default=24, help='Font size for captions (default: 24)')
    caption_group.add_argument('--font-color', default='white', help='Font color for captions (default: white)')
    caption_group.add_argument('--outline-color', default='black', help='Outline color for captions (default: black)')
    caption_group.add_argument('--bg-color', help='Background color for captions (default: semi-transparent black)')
    caption_group.add_argument('--position', choices=['top', 'middle', 'bottom'], default='bottom',
                              help='Vertical position of captions (default: bottom)')
    
    # Video options
    video_group = parser.add_argument_group('Video Options')
    video_group.add_argument('--no-loop', action='store_true', help='Do not loop the background video if too short')
    video_group.add_argument('--no-trim', action='store_true', help='Do not trim the background video if too long')
    video_group.add_argument('--ffmpeg-path', help='Path to FFmpeg executable')
    
    # General options
    general_group = parser.add_argument_group('General Options')
    general_group.add_argument('--no-story-opt', action='store_true', 
                              help='Disable story-specific optimizations')
    general_group.add_argument('--temp-dir', help='Directory to use for temporary files')
    general_group.add_argument('--verbose', action='store_true', help='Enable verbose output')
    general_group.add_argument('--version', action='store_true', help='Show version information and exit')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Show version information and exit if requested
    if args.version:
        from src import __version__
        print(f"Text-to-Video Tool v{__version__}")
        return 0
    
    # Set up logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose output enabled")
    
    # Import the text-to-video generator
    try:
        from src import TextToVideoGenerator
    except ImportError as e:
        logger.error(f"Failed to import TextToVideoGenerator: {str(e)}")
        logger.error("Make sure the package is installed or the src directory is in your Python path")
        return 1
    
    # List available voices if requested
    if args.list_voices:
        try:
            # Create a generator with the specified TTS engine
            generator = TextToVideoGenerator(
                tts_engine=args.tts,
                api_key_path=args.api_key
            )
            
            # Get available voices
            voices = generator.get_available_voices()
            
            if voices:
                print("Available voices:")
                for voice in voices:
                    if isinstance(voice, dict):
                        print(f"  - ID: {voice.get('id')}")
                        print(f"    Name: {voice.get('name')}")
                        print(f"    Languages: {voice.get('languages')}")
                        print(f"    Gender: {voice.get('gender')}")
                        print()
                    else:
                        print(f"  - {voice}")
            else:
                print(f"No voice listing available for the {args.tts} engine")
            
            # Clean up
            generator.cleanup()
            return 0
            
        except Exception as e:
            logger.error(f"Error listing voices: {str(e)}")
            return 1
    
    # Get the input text
    if args.text:
        try:
            with open(args.text, 'r', encoding='utf-8') as f:
                text = f.read()
                logger.info(f"Read {len(text)} characters from {args.text}")
        except Exception as e:
            logger.error(f"Error reading text file: {str(e)}")
            return 1
    else:
        text = args.text_input
        logger.info(f"Using direct text input ({len(text)} characters)")
    
    # Check if the background video exists
    if not os.path.exists(args.bg_video):
        logger.error(f"Background video not found: {args.bg_video}")
        return 1
    
    # Prepare output directory
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
            logger.info(f"Created output directory: {output_dir}")
        except Exception as e:
            logger.error(f"Error creating output directory: {str(e)}")
            return 1
    
    # Prepare subtitle style options
    subtitle_style = {
        'FontName': args.font_name,
        'FontSize': args.font_size,
        'PrimaryColour': _parse_color(args.font_color),
        'OutlineColour': _parse_color(args.outline_color),
    }
    
    if args.bg_color:
        subtitle_style['BackColour'] = _parse_color(args.bg_color)
    
    # Set alignment based on position
    if args.position == 'top':
        subtitle_style['Alignment'] = 8  # Top-center
    elif args.position == 'middle':
        subtitle_style['Alignment'] = 5  # Mid-center
    else:  # bottom
        subtitle_style['Alignment'] = 2  # Bottom-center
    
    # Create the generator
    try:
        generator = TextToVideoGenerator(
            tts_engine=args.tts,
            caption_approach=args.caption_approach,
            use_ffmpeg_for_subtitles=True,
            api_key_path=args.api_key,
            ffmpeg_path=args.ffmpeg_path,
            temp_dir=args.temp_dir
        )
        
        # Generate the video
        logger.info("Starting video generation...")
        output_video = generator.generate(
            text=text,
            background_video_path=args.bg_video,
            output_path=args.output,
            voice=args.voice,
            language=args.language,
            subtitle_style=subtitle_style,
            optimize_for_story=not args.no_story_opt,
            loop_background=not args.no_loop,
            trim_background=not args.no_trim
        )
        
        logger.info(f"Video generated successfully: {output_video}")
        
        # Clean up
        generator.cleanup()
        return 0
        
    except Exception as e:
        logger.error(f"Error generating video: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

def _parse_color(color_str):
    """
    Parse a color string into the format expected by FFmpeg subtitles.
    
    Accepts:
    - Named colors (white, black, red, etc.)
    - Hex colors (#RRGGBB or #AARRGGBB)
    
    Returns:
    - FFmpeg subtitle color string (e.g., '&HFFFFFF')
    """
    # Named color mapping
    color_map = {
        'white': '&HFFFFFF',
        'black': '&H000000',
        'red': '&H0000FF',
        'green': '&H00FF00',
        'blue': '&HFF0000',
        'yellow': '&H00FFFF',
        'cyan': '&HFFFF00',
        'magenta': '&HFF00FF',
        'gray': '&H808080',
        'transparent': '&H00000000',
        'semitransparent': '&H80000000',
    }
    
    # Check for named color
    if color_str.lower() in color_map:
        return color_map[color_str.lower()]
    
    # Check for hex color
    if color_str.startswith('#'):
        # Remove the hash
        color_str = color_str[1:]
        
        # Handle RGB hex
        if len(color_str) == 6:
            # Convert RGB to BGR (FFmpeg subtitles use BGR)
            r, g, b = color_str[0:2], color_str[2:4], color_str[4:6]
            return f'&H{b}{g}{r}'
        
        # Handle ARGB hex
        elif len(color_str) == 8:
            # Convert ARGB to ABGR (FFmpeg subtitles use ABGR)
            a, r, g, b = color_str[0:2], color_str[2:4], color_str[4:6], color_str[6:8]
            return f'&H{b}{g}{r}{a}'
    
    # Default to white if color is not recognized
    logger.warning(f"Unrecognized color: {color_str}, using white instead")
    return '&HFFFFFF'


if __name__ == "__main__":
    sys.exit(main())