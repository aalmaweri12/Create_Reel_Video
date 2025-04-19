"""
Main generator for the text-to-video tool.

This module provides the TextToVideoGenerator class that integrates
all components of the system: TTS, captions, and video processing.
"""

import os
import tempfile
import logging
import time
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TextToVideoGenerator:
    """
    Main class for generating videos from text.
    
    This class integrates the TTS, captions, and video processing
    components to create a complete text-to-video pipeline.
    """
    
    def __init__(self, tts_engine="gtts", caption_approach="sentence", 
                use_ffmpeg_for_subtitles=True, api_key_path=None, 
                ffmpeg_path=None, temp_dir=None):
        """
        Initialize the TextToVideoGenerator.
        
        Args:
            tts_engine (str): Type of TTS engine to use ('google_cloud', 'gtts', or 'pyttsx3')
            caption_approach (str): Approach to use for caption generation
                                  ('sentence', 'paragraph', 'word', or 'simple')
            use_ffmpeg_for_subtitles (bool): Whether to use FFmpeg for subtitle rendering
            api_key_path (str, optional): Path to Google Cloud API key file
            ffmpeg_path (str, optional): Path to FFmpeg executable
            temp_dir (str, optional): Directory to use for temporary files
        """
        self.tts_engine_type = tts_engine
        self.caption_approach = caption_approach
        self.use_ffmpeg = use_ffmpeg_for_subtitles
        self.api_key_path = api_key_path
        self.ffmpeg_path = ffmpeg_path
        
        # Create temporary directory if not provided
        if temp_dir:
            self.temp_dir = temp_dir
            os.makedirs(self.temp_dir, exist_ok=True)
        else:
            self.temp_dir = tempfile.mkdtemp()
        
        # Import and initialize components
        self._init_components()
    
    def _init_components(self):
        """Initialize TTS, captions, and video processing components."""
        # Import TTS module
        try:
            from src.tts import TTSEngine, GoogleTTS, GTTS, PyttsxTTS
            
            # Create the appropriate TTS engine
            if self.tts_engine_type == "google_cloud":
                self.tts_engine = GoogleTTS(api_key_path=self.api_key_path)
            elif self.tts_engine_type == "gtts":
                self.tts_engine = GTTS()
            elif self.tts_engine_type == "pyttsx3":
                self.tts_engine = PyttsxTTS()
            else:
                raise ValueError(f"Unsupported TTS engine type: {self.tts_engine_type}")
                
        except ImportError as e:
            logger.error(f"Error importing TTS module: {str(e)}")
            raise
        
        # Import captions module
        try:
            from src.captions import CaptionGenerator
            self.caption_generator = CaptionGenerator(approach=self.caption_approach)
        except ImportError as e:
            logger.error(f"Error importing captions module: {str(e)}")
            raise
        
        # Import video module
        try:
            from src.video import VideoProcessor
            self.video_processor = VideoProcessor(
                use_ffmpeg_for_subtitles=self.use_ffmpeg,
                ffmpeg_path=self.ffmpeg_path
            )
        except ImportError as e:
            logger.error(f"Error importing video module: {str(e)}")
            raise
        
        logger.info("All components initialized successfully")
    
    def generate(self, text, background_video_path, output_path, 
                voice=None, language=None, subtitle_style=None, 
                optimize_for_story=True, loop_background=True, 
                trim_background=True):
        """
        Generate a video from text.
        
        Args:
            text (str): The text to convert to speech and captions
            background_video_path (str): Path to the background video
            output_path (str): Path to save the final video
            voice (str, optional): Voice identifier for TTS
            language (str, optional): Language code for TTS
            subtitle_style (dict, optional): Style options for subtitles
            optimize_for_story (bool): Whether to use story-specific optimizations
            loop_background (bool): Whether to loop the background video if too short
            trim_background (bool): Whether to trim the background video if too long
            
        Returns:
            str: Path to the generated video
        """
        start_time = time.time()
        logger.info(f"Starting video generation for text of length {len(text)}")
        
        # Create a unique ID for this generation
        import uuid
        generation_id = str(uuid.uuid4())[:8]
        
        # Step 1: Generate speech from text
        audio_path = os.path.join(self.temp_dir, f"{generation_id}_speech.mp3")
        logger.info(f"Generating speech to {audio_path}")
        
        if optimize_for_story:
            self.tts_engine.generate_speech_for_story(text, audio_path, voice, language)
        else:
            self.tts_engine.generate_speech(text, audio_path, voice, language)
        
        # Step 2: Get audio duration
        try:
            from moviepy.editor import AudioFileClip
            audio_duration = AudioFileClip(audio_path).duration
            logger.info(f"Audio duration: {audio_duration:.2f} seconds")
        except Exception as e:
            logger.error(f"Error getting audio duration: {str(e)}")
            raise
        
        # Step 3: Generate captions
        srt_path = os.path.join(self.temp_dir, f"{generation_id}_captions.srt")
        logger.info(f"Generating captions to {srt_path}")
        self.caption_generator.generate_srt(text, audio_duration, srt_path)
        
        # Step 4: Process video
        logger.info(f"Processing video with background: {background_video_path}")
        
        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        final_video = self.video_processor.create_video(
            background_video_path=background_video_path,
            audio_path=audio_path,
            srt_path=srt_path,
            output_path=output_path,
            subtitle_style=subtitle_style,
            loop_background=loop_background,
            trim_background=trim_background
        )
        
        # Calculate processing time
        end_time = time.time()
        processing_time = end_time - start_time
        logger.info(f"Video generation completed in {processing_time:.2f} seconds")
        logger.info(f"Final video saved to: {final_video}")
        
        return final_video
    
    def cleanup(self):
        """Clean up temporary files and resources."""
        logger.info(f"Cleaning up temporary directory: {self.temp_dir}")
        
        # First clean up any component-specific resources
        try:
            self.video_processor.cleanup()
        except Exception as e:
            logger.warning(f"Error during video processor cleanup: {str(e)}")
        
        # Then remove the main temporary directory
        import shutil
        try:
            shutil.rmtree(self.temp_dir)
            logger.info("Cleanup completed successfully")
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
    
    def get_available_voices(self):
        """
        Get a list of available voices for the current TTS engine.
        
        Returns:
            list: List of available voice identifiers, or None if not supported
        """
        try:
            # This is only implemented for some TTS engines
            if hasattr(self.tts_engine, 'list_available_voices'):
                return self.tts_engine.list_available_voices()
            else:
                logger.warning(f"Voice listing not supported for {self.tts_engine_type}")
                return None
        except Exception as e:
            logger.error(f"Error getting available voices: {str(e)}")
            return None
    
    def extract_preview_frame(self, output_path, frame_time=1.0):
        """
        Extract a preview frame from the generated video.
        
        Args:
            output_path (str): Path to save the preview frame
            frame_time (float): Time in seconds to extract the frame
            
        Returns:
            str: Path to the extracted frame
        """
        # Get the most recently generated video
        # This assumes generate() has been called at least once
        if not hasattr(self, 'final_video_path') or not self.final_video_path:
            logger.error("No video has been generated yet")
            return None
        
        return self.video_processor.extract_frame(
            self.final_video_path, 
            output_path, 
            time=frame_time
        )


# Usage example if this module is run directly
if __name__ == "__main__":
    # Example text and background video
    example_text = """Once upon a time, there was a small village nestled in a valley. 
    The people who lived there were kind and hardworking. Every morning, they would wake up at dawn.
    One day, a stranger arrived at the village. He carried a mysterious package.
    "What's in the package?" asked the curious villagers. The stranger smiled but said nothing."""
    
    background_video = "example_background.mp4"
    output_path = "example_output.mp4"
    
    # Check if background video exists
    if not os.path.exists(background_video):
        print(f"Error: Background video not found: {background_video}")
        print("This is just an example. Please provide a real background video path.")
        exit(1)
    
    # Create the generator
    generator = TextToVideoGenerator(
        tts_engine="gtts",  # Use the free gTTS engine for the example
        caption_approach="sentence",  # Process by sentences
        use_ffmpeg_for_subtitles=True
    )
    
    try:
        # Generate the video
        output_video = generator.generate(
            text=example_text,
            background_video_path=background_video,
            output_path=output_path,
            language="en",
            optimize_for_story=True
        )
        
        print(f"Video generated successfully: {output_video}")
        
    except Exception as e:
        print(f"Error generating video: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        generator.cleanup()