"""
Web application for the text-to-video tool.

This module provides a Flask web interface for the text-to-video tool,
allowing users to create videos from text through a browser.
"""

import os
import json
import uuid
import time
import logging
import tempfile
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify, session, flash
from src import TextToVideoGenerator

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev_key_for_testing_only')

# Configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
RESULT_FOLDER = os.path.join(os.path.dirname(__file__), 'results')
TEMP_FOLDER = os.path.join(os.path.dirname(__file__), 'temp')
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv'}
ALLOWED_API_KEY_EXTENSIONS = {'json'}

# Create necessary directories
for folder in [UPLOAD_FOLDER, RESULT_FOLDER, TEMP_FOLDER]:
    os.makedirs(folder, exist_ok=True)

# Import the text-to-video generator
try:
    from src import TextToVideoGenerator
    logger.info("Successfully imported TextToVideoGenerator")
except ImportError as e:
    logger.error(f"Failed to import TextToVideoGenerator: {str(e)}")
    logger.error("Make sure the src package is in your Python path")
    TextToVideoGenerator = None


def allowed_file(filename, allowed_extensions):
    """Check if a file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')


@app.route('/generate', methods=['POST'])
def generate():
    """Handle the video generation request."""
    # Check if TextToVideoGenerator is available
    if TextToVideoGenerator is None:
        return render_template('index.html', error="Text-to-video generator module not available")
    
    # Get form data
    text = request.form.get('text', '')
    if not text:
        return render_template('index.html', error="No text provided")
    
    # Check if a video file was uploaded
    if 'background_video' not in request.files:
        return render_template('index.html', error="No background video uploaded", text=text)
    
    video_file = request.files['background_video']
    if video_file.filename == '':
        return render_template('index.html', error="No background video selected", text=text)
    
    if not allowed_file(video_file.filename, ALLOWED_VIDEO_EXTENSIONS):
        return render_template(
            'index.html', 
            error=f"Invalid video format. Allowed formats: {', '.join(ALLOWED_VIDEO_EXTENSIONS)}", 
            text=text
        )
    
    # Create a unique ID for this generation
    generation_id = str(uuid.uuid4())
    
    # Save the uploaded video
    video_filename = f"{generation_id}_{video_file.filename}"
    video_path = os.path.join(UPLOAD_FOLDER, video_filename)
    video_file.save(video_path)
    logger.info(f"Saved background video to {video_path}")
    
    # Get TTS engine settings
    tts_engine = request.form.get('tts_engine', 'gtts')
    language = request.form.get('language', 'en')
    voice = request.form.get('voice', None)
    
    # Handle API key file for Google Cloud TTS
    api_key_path = None
    if tts_engine == 'google_cloud' and 'api_key' in request.files:
        api_key_file = request.files['api_key']
        if api_key_file.filename != '' and allowed_file(api_key_file.filename, ALLOWED_API_KEY_EXTENSIONS):
            api_key_filename = f"{generation_id}_{api_key_file.filename}"
            api_key_path = os.path.join(UPLOAD_FOLDER, api_key_filename)
            api_key_file.save(api_key_path)
            logger.info(f"Saved API key file to {api_key_path}")
    
    # Get caption settings
    caption_approach = request.form.get('caption_approach', 'sentence')
    
    # Parse subtitle style
    subtitle_style = {
        'FontName': request.form.get('font_name', 'Arial'),
        'FontSize': int(request.form.get('font_size', 24)),
        'PrimaryColour': _parse_color(request.form.get('font_color', 'white')),
        'OutlineColour': _parse_color(request.form.get('outline_color', 'black')),
    }
    
    bg_color = request.form.get('bg_color')
    if bg_color:
        subtitle_style['BackColour'] = _parse_color(bg_color)
    
    # Set alignment based on position
    position = request.form.get('position', 'bottom')
    if position == 'top':
        subtitle_style['Alignment'] = 8  # Top-center
    elif position == 'middle':
        subtitle_style['Alignment'] = 5  # Mid-center
    else:  # bottom
        subtitle_style['Alignment'] = 2  # Bottom-center
    
    # Get video options
    loop_background = 'no_loop' not in request.form
    trim_background = 'no_trim' not in request.form
    optimize_for_story = 'no_story_opt' not in request.form
    
    # Prepare output path
    output_filename = f"{generation_id}_output.mp4"
    output_path = os.path.join(RESULT_FOLDER, output_filename)
    
    # Create temporary directory for this generation
    temp_dir = os.path.join(TEMP_FOLDER, generation_id)
    os.makedirs(temp_dir, exist_ok=True)
    
    try:
        # Store generation info in session
        session['generation_id'] = generation_id
        session['output_filename'] = output_filename
        
        # Initialize the generator
        logger.info("Initializing TextToVideoGenerator")
        generator = TextToVideoGenerator(
            tts_engine=tts_engine,
            caption_approach=caption_approach,
            use_ffmpeg_for_subtitles=True,
            api_key_path=api_key_path,
            temp_dir=temp_dir
        )
        
        # Generate the video
        logger.info("Starting video generation")
        start_time = time.time()
        
        # This is the main processing step
        output_video = generator.generate(
            text=text,
            background_video_path=video_path,
            output_path=output_path,
            voice=voice,
            language=language,
            subtitle_style=subtitle_style,
            optimize_for_story=optimize_for_story,
            loop_background=loop_background,
            trim_background=trim_background
        )
        
        # Calculate processing time
        end_time = time.time()
        processing_time = end_time - start_time
        logger.info(f"Video generation completed in {processing_time:.2f} seconds")
        logger.info(f"Video saved to {output_video}")
        
        # Create a preview frame
        preview_path = os.path.join(RESULT_FOLDER, f"{generation_id}_preview.jpg")
        generator.video_processor.extract_frame(output_path, preview_path, time=1.0)
        
        # Clean up
        generator.cleanup()
        
        # Redirect to the download page
        return redirect(url_for('download', generation_id=generation_id))
        
    except Exception as e:
        logger.error(f"Error generating video: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return render_template('index.html', error=f"Error generating video: {str(e)}", text=text)


@app.route('/download/<generation_id>')
def download(generation_id):
    """Show the download page for a generated video."""
    output_filename = session.get('output_filename')
    if not output_filename or generation_id != session.get('generation_id'):
        return redirect(url_for('index'))
    
    output_path = os.path.join(RESULT_FOLDER, output_filename)
    preview_path = os.path.join(RESULT_FOLDER, f"{generation_id}_preview.jpg")
    
    if not os.path.exists(output_path):
        return redirect(url_for('index'))
    
    # Get video information
    video_info = {}
    try:
        # Use FFprobe to get video info
        import subprocess
        import json
        
        result = subprocess.run([
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration,size : stream=width,height',
            '-of', 'json',
            output_path
        ], capture_output=True, text=True, check=True)
        
        info = json.loads(result.stdout)
        
        # Extract format information
        if 'format' in info:
            format_info = info['format']
            if 'duration' in format_info:
                video_info['duration'] = f"{float(format_info['duration']):.2f} seconds"
            if 'size' in format_info:
                size_mb = int(format_info['size']) / (1024 * 1024)
                video_info['size'] = f"{size_mb:.2f} MB"
        
        # Get stream information (use the first video stream)
        if 'streams' in info:
            for stream in info['streams']:
                if stream.get('codec_type') == 'video':
                    if 'width' in stream and 'height' in stream:
                        video_info['resolution'] = f"{stream['width']}x{stream['height']}"
                    break
    
    except Exception as e:
        logger.warning(f"Could not get video info: {str(e)}")
    
    # Check if preview exists
    preview_url = url_for('static', filename='img/placeholder.jpg')
    if os.path.exists(preview_path):
        # Copy preview to static folder
        static_preview_path = os.path.join(app.static_folder, 'previews', f"{generation_id}.jpg")
        os.makedirs(os.path.dirname(static_preview_path), exist_ok=True)
        
        try:
            import shutil
            shutil.copy(preview_path, static_preview_path)
            preview_url = url_for('static', filename=f'previews/{generation_id}.jpg')
        except Exception as e:
            logger.warning(f"Could not copy preview: {str(e)}")
    
    return render_template(
        'download.html',
        generation_id=generation_id,
        preview_url=preview_url,
        video_info=video_info
    )


@app.route('/get_video/<generation_id>')
def get_video(generation_id):
    """Download the generated video."""
    output_filename = session.get('output_filename')
    if not output_filename or generation_id != session.get('generation_id'):
        return redirect(url_for('index'))
    
    output_path = os.path.join(RESULT_FOLDER, output_filename)
    
    if not os.path.exists(output_path):
        return redirect(url_for('index'))
    
    # Extract original filename from output_filename
    original_name = "_".join(output_filename.split('_')[1:])
    
    return send_file(output_path, as_attachment=True, download_name=original_name)


@app.route('/list_voices', methods=['POST'])
def list_voices():
    """List available voices for a given TTS engine."""
    # Check if TextToVideoGenerator is available
    if TextToVideoGenerator is None:
        return jsonify({"error": "Text-to-video generator module not available"})
    
    # Get the requested TTS engine
    tts_engine = request.form.get('tts_engine', 'gtts')
    language = request.form.get('language', 'en')
    
    # Get API key path for Google Cloud TTS
    api_key_path = None
    if tts_engine == 'google_cloud' and 'api_key' in request.files:
        api_key_file = request.files['api_key']
        if api_key_file.filename != '' and allowed_file(api_key_file.filename, ALLOWED_API_KEY_EXTENSIONS):
            # Save API key to a temporary file
            temp_api_key_path = os.path.join(TEMP_FOLDER, f"temp_api_key_{uuid.uuid4()}.json")
            api_key_file.save(temp_api_key_path)
            api_key_path = temp_api_key_path
    
    try:
        # Create a generator just to list voices
        generator = TextToVideoGenerator(
            tts_engine=tts_engine,
            api_key_path=api_key_path,
            temp_dir=TEMP_FOLDER
        )
        
        # Get available voices
        voices = generator.get_available_voices()
        
        # Clean up
        generator.cleanup()
        
        # Filter voices by language if applicable
        if voices and language and isinstance(voices[0], dict):
            filtered_voices = [v for v in voices if language in str(v.get('languages', ''))]
            voices = filtered_voices if filtered_voices else voices
        
        return jsonify({"voices": voices})
        
    except Exception as e:
        logger.error(f"Error listing voices: {str(e)}")
        return jsonify({"error": str(e)})
    
    finally:
        # Clean up temporary API key file
        if api_key_path and api_key_path.startswith(TEMP_FOLDER):
            try:
                os.remove(api_key_path)
            except Exception:
                pass


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
    if color_str and color_str.lower() in color_map:
        return color_map[color_str.lower()]
    
    # Check for hex color
    if color_str and color_str.startswith('#'):
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


@app.route('/cleanup', methods=['POST'])
def cleanup():
    """Clean up temporary files older than a day."""
    try:
        # Get the current time
        current_time = time.time()
        
        # Clean up old files in UPLOAD_FOLDER
        for filename in os.listdir(UPLOAD_FOLDER):
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            if os.path.isfile(file_path):
                # If file is older than 1 day, delete it
                if current_time - os.path.getmtime(file_path) > 86400:  # 24 hours in seconds
                    os.remove(file_path)
                    logger.info(f"Deleted old file: {file_path}")
        
        # Clean up old files in RESULT_FOLDER
        for filename in os.listdir(RESULT_FOLDER):
            file_path = os.path.join(RESULT_FOLDER, filename)
            if os.path.isfile(file_path):
                # If file is older than 1 day, delete it
                if current_time - os.path.getmtime(file_path) > 86400:  # 24 hours in seconds
                    os.remove(file_path)
                    logger.info(f"Deleted old file: {file_path}")
        
        # Clean up old directories in TEMP_FOLDER
        for dirname in os.listdir(TEMP_FOLDER):
            dir_path = os.path.join(TEMP_FOLDER, dirname)
            if os.path.isdir(dir_path):
                # If directory is older than 1 day, delete it
                if current_time - os.path.getmtime(dir_path) > 86400:  # 24 hours in seconds
                    import shutil
                    shutil.rmtree(dir_path)
                    logger.info(f"Deleted old directory: {dir_path}")
        
        return jsonify({"status": "success"})
        
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")
        return jsonify({"status": "error", "message": str(e)})


if __name__ == '__main__':
    # Run the app
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))