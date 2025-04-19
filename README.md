# Text-to-Video Tool

A powerful tool for creating videos from text input with text-to-speech narration and synchronized captions. Perfect for storytelling, educational content, or automated video creation.

## Features

- **Text-to-Speech Conversion**: Convert your text to natural-sounding speech using multiple TTS engines
- **Sentence-by-Sentence Processing**: Process your stories sentence by sentence for natural pacing
- **Synchronized Captions**: Automatically generate captions that are perfectly timed with the narration
- **Background Video Integration**: Combine your narration with any background video
- **Customizable Styling**: Adjust fonts, colors, sizes, and positions of captions
- **Command-Line Interface**: Easy-to-use CLI that requires no coding knowledge
- **Multiple TTS Options**: Choose from Google Cloud TTS (high quality), gTTS (free), or pyttsx3 (offline)

## Installation

### From Source

```bash
git clone https://github.com/aalmaweri12/Create_Reel_Video.git
cd Create_Reel_Video
pip install -e requirements.txt
```

## Requirements

- Python 3.7 or higher
- FFmpeg (must be installed and available in your PATH)

## Quick Start

### Basic Usage

```bash
# Create a video from a text file
text2video --text story.txt --bg-video background.mp4 --output story_video.mp4
```

### Using Direct Text Input

```bash
text2video --text-input "Once upon a time, there was a small village nestled in a valley." --bg-video background.mp4 --output story_video.mp4
```

### Customizing Captions

```bash
text2video --text story.txt --bg-video background.mp4 --output story_video.mp4 --font-size 28 --font-color yellow --position top
```

### Using Google Cloud TTS

```bash
text2video --text story.txt --bg-video background.mp4 --output story_video.mp4 --tts google_cloud --api-key path/to/google-credentials.json --voice en-US-Neural2-F
```

## Command-Line Options

### Input/Output Options

- `--text FILE`: Path to text file containing the story
- `--text-input TEXT`: Direct text input
- `--bg-video FILE`: Path to background video
- `--output FILE`: Path to output video

### Text-to-Speech Options

- `--tts ENGINE`: TTS engine to use (google_cloud, gtts, or pyttsx3)
- `--voice VOICE`: Voice name/ID to use for speech
- `--language LANG`: Language code (default: en)
- `--api-key FILE`: Path to Google Cloud API key file
- `--list-voices`: List available voices and exit

### Caption Options

- `--caption-approach APPROACH`: Caption generation approach (sentence, paragraph, word, or simple)
- `--font-name NAME`: Font name for captions
- `--font-size SIZE`: Font size for captions
- `--font-color COLOR`: Font color for captions
- `--outline-color COLOR`: Outline color for captions
- `--bg-color COLOR`: Background color for captions
- `--position POS`: Vertical position of captions (top, middle, or bottom)

### Video Options

- `--no-loop`: Do not loop the background video if too short
- `--no-trim`: Do not trim the background video if too long
- `--ffmpeg-path PATH`: Path to FFmpeg executable

### General Options

- `--no-story-opt`: Disable story-specific optimizations
- `--temp-dir DIR`: Directory to use for temporary files
- `--verbose`: Enable verbose output
- `--version`: Show version information and exit

## Python API

You can also use the tool programmatically:

```python
from src import TextToVideoGenerator

generator = TextToVideoGenerator(
    tts_engine="gtts",
    caption_approach="sentence"
)

generator.generate(
    text="Your story text here...",
    background_video_path="background.mp4",
    output_path="output.mp4",
    optimize_for_story=True
)
```

## License

MIT License

## Credits

- [MoviePy](https://zulko.github.io/moviepy/) - Video editing library
- [gTTS](https://github.com/pndurette/gTTS) - Google Text-to-Speech API
- [FFmpeg](https://ffmpeg.org/) - Video processing backend