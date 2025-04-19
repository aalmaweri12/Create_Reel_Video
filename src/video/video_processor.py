"""
Video processor for the text-to-video tool.

This module provides the VideoProcessor class which handles:
- Processing background videos
- Combining videos with audio
- Adding captions to videos
- Exporting the final video
"""

import os
import tempfile
import subprocess
import logging
import shutil
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VideoProcessor:
    """
    Video processor for combining background videos with audio and captions.
    """
    
    def __init__(self, use_ffmpeg_for_subtitles=True, ffmpeg_path=None):
        """
        Initialize the VideoProcessor.
        
        Args:
            use_ffmpeg_for_subtitles (bool): If True, use FFmpeg for subtitle rendering.
                                           If False, use MoviePy (has limitations).
            ffmpeg_path (str, optional): Path to ffmpeg executable if not in system PATH
        """
        self.use_ffmpeg = use_ffmpeg_for_subtitles
        self.ffmpeg_path = ffmpeg_path if ffmpeg_path else 'ffmpeg'
        self.temp_dir = tempfile.mkdtemp()
        
        # Check FFmpeg availability if using it
        if self.use_ffmpeg:
            self._check_ffmpeg()
        
        # Try to import MoviePy
        try:
            try:
                # Try importing from moviepy.editor (old structure)
                from moviepy.editor import VideoFileClip, AudioFileClip
            except ImportError:
                try:
                    # Try importing individually (new structure)
                    from moviepy.video.io.VideoFileClip import VideoFileClip
                    from moviepy.audio.io.AudioFileClip import AudioFileClip
                except ImportError:
                    try:
                        # For newest versions
                        from moviepy.video.VideoClip import VideoFileClip
                        from moviepy.audio.AudioClip import AudioFileClip
                    except ImportError:
                        raise ImportError("Cannot import required MoviePy classes. Check MoviePy installation and version.")
            self.VideoFileClip = VideoFileClip
            self.AudioFileClip = AudioFileClip
        except ImportError:
            logger.error("Failed to import moviepy. Install with: pip install moviepy")
            raise ImportError("moviepy library not found")
    
    def _check_ffmpeg(self):
        """Check if FFmpeg is available."""
        try:
            result = subprocess.run(
                [self.ffmpeg_path, "-version"], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True
            )
            logger.info(f"FFmpeg found: {result.stdout.split('\\n')[0]}")
        except Exception as e:
            logger.error(f"FFmpeg not found or not working: {str(e)}")
            logger.error("Either install FFmpeg or set use_ffmpeg_for_subtitles=False")
            raise RuntimeError("FFmpeg not available")
    
    def create_video(self, background_video_path, audio_path, srt_path, output_path, 
                 subtitle_style=None, loop_background=True, trim_background=True):
        """
        Create a video with background, audio, and subtitles.
        """
        # Ensure output directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Step 1: Load background video
        logger.info(f"Loading background video: {background_video_path}")
        background = self.VideoFileClip(background_video_path)

        # Step 2: Load audio
        logger.info(f"Loading audio: {audio_path}")
        audio = self.AudioFileClip(audio_path)

        # Step 3: Adjust video length
        if audio.duration > background.duration and loop_background:
            logger.info(f"Looping background video to match audio length ({audio.duration:.2f}s)")
            background = background.loop(duration=audio.duration)
        elif audio.duration < background.duration and trim_background:
            logger.info(f"Trimming background video to match audio length ({audio.duration:.2f}s)")
            background = background.subclip(0, audio.duration)

        # Step 4: Add audio to video
        logger.info("Adding audio to video")
        video_with_audio = background.set_audio(audio)

        # Step 5: Handle subtitle overlay
        if self.use_ffmpeg:
            temp_output = os.path.join(self.temp_dir, "temp_video_with_audio.mp4")
            logger.info(f"Saving temporary video with audio: {temp_output}")
            video_with_audio.write_videofile(
                temp_output,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile=os.path.join(self.temp_dir, "temp_audio.m4a"),
                remove_temp=True
            )

            subtitle_style_str = self._get_subtitle_style_string(subtitle_style)
            temp_srt = os.path.join(os.path.dirname(temp_output), "temp_subtitles.srt")
            shutil.copy(srt_path, temp_srt)

            ffmpeg_cmd = [
                self.ffmpeg_path, '-i', temp_output,
                '-vf', f'subtitles=temp_subtitles.srt{subtitle_style_str}',
                '-c:a', 'copy', output_path
            ]

            logger.debug(f"FFmpeg command: {' '.join(ffmpeg_cmd)}")
            original_dir = os.getcwd()

            try:
                os.chdir(os.path.dirname(temp_output))
                subprocess.run(ffmpeg_cmd, check=True)
                logger.info(f"Video with subtitles saved to: {output_path}")
            except subprocess.CalledProcessError as e:
                logger.error(f"FFmpeg error: {str(e)}")
                if os.getcwd() != original_dir:
                    os.chdir(original_dir)
                raise
            finally:
                os.chdir(original_dir)

        else:
            logger.warning("FFmpeg not used. Saving video with audio only (no subtitles).")
            video_with_audio.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile=os.path.join(self.temp_dir, "temp_audio.m4a"),
                remove_temp=True
            )

        return output_path

    
    def _get_subtitle_style_string(self, style=None):
        """
        Generate the FFmpeg subtitle style string.
        
        Args:
            style (dict, optional): Style options for subtitles
            
        Returns:
            str: FFmpeg subtitle style string
        """
        # Default style
        default_style = {
            'FontName': 'Arial',
            'FontSize': 24,
            'PrimaryColour': '&HFFFFFF',  # White
            'OutlineColour': '&H000000',  # Black outline
            'BackColour': '&H80000000',   # Semi-transparent background
            'Bold': 1,
            'BorderStyle': 4,             # Outline + background
            'Outline': 1,
            'Alignment': 2,               # Centered
            'MarginV': 30                 # Bottom margin
        }
        
        # Merge with provided style
        merged_style = default_style.copy()
        if style:
            merged_style.update(style)
        
        # Build style string
        style_str = ":force_style='"
        style_parts = []
        
        for key, value in merged_style.items():
            style_parts.append(f"{key}={value}")
        
        style_str += ",".join(style_parts)
        style_str += "'"
        
        return style_str
    
    def extract_frame(self, video_path, output_path, time=0):
        """
        Extract a frame from a video at the specified time.
        
        Args:
            video_path (str): Path to the video
            output_path (str): Path to save the extracted frame
            time (float): Time in seconds to extract the frame
            
        Returns:
            str: Path to the extracted frame
        """
        # Ensure output directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Use FFmpeg to extract the frame
        logger.info(f"Extracting frame at {time}s from {video_path}")
        
        try:
            subprocess.run([
                self.ffmpeg_path,
                '-ss', str(time),
                '-i', video_path,
                '-vframes', '1',
                '-q:v', '2',
                output_path
            ], check=True)
            
            logger.info(f"Frame extracted to: {output_path}")
            return output_path
            
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg error extracting frame: {str(e)}")
            raise
    
    def get_video_info(self, video_path):
        """
        Get information about a video file.
        
        Args:
            video_path (str): Path to the video
            
        Returns:
            dict: Video information (duration, dimensions, fps, etc.)
        """
        logger.info(f"Getting info for video: {video_path}")
        
        # Use FFprobe to get video info
        try:
            result = subprocess.run([
                self.ffmpeg_path.replace('ffmpeg', 'ffprobe'),
                '-v', 'error',
                '-show_entries', 'format=duration,size : stream=width,height,r_frame_rate',
                '-of', 'json',
                video_path
            ], capture_output=True, text=True, check=True)
            
            import json
            info = json.loads(result.stdout)
            
            # Extract and process the relevant information
            video_info = {}
            
            # Get format information
            if 'format' in info:
                format_info = info['format']
                if 'duration' in format_info:
                    video_info['duration'] = float(format_info['duration'])
                if 'size' in format_info:
                    video_info['size'] = int(format_info['size'])
            
            # Get stream information (use the first video stream)
            if 'streams' in info:
                for stream in info['streams']:
                    if stream.get('codec_type') == 'video':
                        if 'width' in stream:
                            video_info['width'] = stream['width']
                        if 'height' in stream:
                            video_info['height'] = stream['height']
                        if 'r_frame_rate' in stream:
                            # Parse frame rate (e.g., "30000/1001")
                            rate_parts = stream['r_frame_rate'].split('/')
                            if len(rate_parts) == 2:
                                video_info['fps'] = float(rate_parts[0]) / float(rate_parts[1])
                            else:
                                video_info['fps'] = float(stream['r_frame_rate'])
                        break
            
            logger.info(f"Video info: {video_info}")
            return video_info
            
        except subprocess.CalledProcessError as e:
            logger.error(f"FFprobe error: {str(e)}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing FFprobe output: {str(e)}")
            raise
    
    def create_preview(self, video_path, output_path, max_width=640, max_height=360):
        """
        Create a smaller preview version of a video.
        
        Args:
            video_path (str): Path to the video
            output_path (str): Path to save the preview video
            max_width (int): Maximum width of the preview
            max_height (int): Maximum height of the preview
            
        Returns:
            str: Path to the preview video
        """
        # Ensure output directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Use FFmpeg to create the preview
        logger.info(f"Creating preview for video: {video_path}")
        
        try:
            subprocess.run([
                self.ffmpeg_path,
                '-i', video_path,
                '-vf', f'scale=min({max_width},iw):min({max_height},ih):force_original_aspect_ratio=decrease',
                '-c:v', 'libx264',
                '-preset', 'fast',
                '-crf', '28',
                '-c:a', 'aac',
                '-b:a', '128k',
                '-movflags', '+faststart',
                output_path
            ], check=True)
            
            logger.info(f"Preview created: {output_path}")
            return output_path
            
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg error creating preview: {str(e)}")
            raise
    
    def cleanup(self):
        """Remove temporary files."""
        logger.info(f"Cleaning up temporary directory: {self.temp_dir}")
        shutil.rmtree(self.temp_dir)


# Usage example if this module is run directly
if __name__ == "__main__":
    # Example usage
    background_video = "example_background.mp4"
    audio_file = "example_speech.mp3"
    srt_file = "example_captions.srt"
    output_file = "example_output.mp4"
    
    # Check if files exist
    for file_path in [background_video, audio_file, srt_file]:
        if not os.path.exists(file_path):
            print(f"Error: File not found: {file_path}")
            print("This is just an example. Please provide real file paths.")
            exit(1)
    
    # Create video processor
    processor = VideoProcessor()
    
    # Create the video
    try:
        output_path = processor.create_video(
            background_video, 
            audio_file, 
            srt_file, 
            output_file,
            subtitle_style={
                'FontSize': 28,
                'Bold': 1,
                'BorderStyle': 4
            }
        )
        
        print(f"Video created successfully: {output_path}")
        
    except Exception as e:
        print(f"Error creating video: {str(e)}")
    
    finally:
        processor.cleanup()