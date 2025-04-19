"""
Text-to-Speech engines for the text-to-video tool.

This module provides several TTS engines for converting text to speech,
with specific optimizations for storytelling.
"""

import os
import re
import logging
from abc import ABC, abstractmethod

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TTSEngine(ABC):
    """
    Abstract base class for all TTS engines.
    """
    
    def __init__(self):
        """Initialize the TTS engine."""
        pass
    
    @abstractmethod
    def generate_speech(self, text, output_path, voice=None, language=None):
        """
        Generate speech from text and save to output_path.
        
        Args:
            text (str): The text to convert to speech
            output_path (str): Path to save the audio file
            voice (str, optional): Voice identifier to use
            language (str, optional): Language code
            
        Returns:
            str: Path to the generated audio file
        """
        pass
    
    def generate_speech_for_story(self, text, output_path, voice=None, language=None):
        """
        Generate speech optimized for storytelling with appropriate pacing.
        
        Args:
            text (str): The story text to convert to speech
            output_path (str): Path to save the audio file
            voice (str, optional): Voice identifier to use
            language (str, optional): Language code
            
        Returns:
            str: Path to the generated audio file
        """
        # Default implementation just calls the standard generate_speech
        # But specialized engines can override this with story-specific enhancements
        return self.generate_speech(text, output_path, voice, language)
    
    def prepare_text(self, text):
        """
        Prepare text for TTS processing (common preprocessing).
        
        Args:
            text (str): The text to prepare
            
        Returns:
            str: Processed text
        """
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Handle common abbreviations
        text = re.sub(r'Mr\.', 'Mister ', text)
        text = re.sub(r'Mrs\.', 'Misses ', text)
        text = re.sub(r'Dr\.', 'Doctor ', text)
        text = re.sub(r'Prof\.', 'Professor ', text)
        text = re.sub(r'vs\.', 'versus ', text)
        text = re.sub(r'e\.g\.', 'for example', text)
        text = re.sub(r'i\.e\.', 'that is', text)
        
        # Handle numbers for better pronunciation
        text = re.sub(r'(\d+)%', r'\1 percent', text)
        
        return text


class GoogleTTS(TTSEngine):
    """
    TTS engine using Google Cloud Text-to-Speech API.
    
    Requires a Google Cloud account and API key.
    Offers high-quality voices with SSML support.
    """
    
    def __init__(self, api_key_path=None):
        """
        Initialize the Google Cloud TTS engine.
        
        Args:
            api_key_path (str, optional): Path to Google Cloud API key file
        """
        super().__init__()
        
        # Try to load google.cloud.texttospeech
        try:
            from google.cloud import texttospeech
            self.texttospeech = texttospeech
        except ImportError:
            logger.error("Failed to import google.cloud.texttospeech. Install with: pip install google-cloud-texttospeech")
            raise ImportError("google-cloud-texttospeech library not found")
        
        # Set API key path if provided
        if api_key_path:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = api_key_path
        
        # Check if credentials are set
        if "GOOGLE_APPLICATION_CREDENTIALS" not in os.environ:
            logger.warning("GOOGLE_APPLICATION_CREDENTIALS environment variable not set. "
                          "Authentication may fail.")
    
    def generate_speech(self, text, output_path, voice="en-US-Neural2-F", language="en-US"):
        """
        Generate speech using Google Cloud TTS.
        
        Args:
            text (str): The text to convert to speech
            output_path (str): Path to save the audio file
            voice (str, optional): Voice name to use
            language (str, optional): Language code
            
        Returns:
            str: Path to the generated audio file
        """
        # Preprocess text
        text = self.prepare_text(text)
        
        # Create Google Cloud TTS client
        client = self.texttospeech.TextToSpeechClient()
        
        # Build the synthesis input
        synthesis_input = self.texttospeech.SynthesisInput(text=text)
        
        # Build the voice request
        voice_params = self.texttospeech.VoiceSelectionParams(
            language_code=language,
            name=voice
        )
        
        # Select the audio file type
        audio_config = self.texttospeech.AudioConfig(
            audio_encoding=self.texttospeech.AudioEncoding.MP3
        )
        
        # Perform the text-to-speech request
        try:
            response = client.synthesize_speech(
                input=synthesis_input,
                voice=voice_params,
                audio_config=audio_config
            )
            
            # Write the response to the output file
            with open(output_path, "wb") as out:
                out.write(response.audio_content)
                
            logger.info(f"Generated speech saved to {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating speech with Google Cloud TTS: {str(e)}")
            raise
    
    def generate_speech_for_story(self, text, output_path, voice="en-US-Neural2-F", language="en-US"):
        """
        Generate speech optimized for storytelling using Google Cloud TTS.
        
        Uses SSML for better pacing and expression in stories.
        
        Args:
            text (str): The story text to convert to speech
            output_path (str): Path to save the audio file
            voice (str, optional): Voice name to use
            language (str, optional): Language code
            
        Returns:
            str: Path to the generated audio file
        """
        # Preprocess text
        text = self.prepare_text(text)
        
        # Split into sentences for better SSML control
        sentences = []
        pattern = r'(?<=[.!?…])\s+(?=[A-Z0-9"])'
        parts = re.split(pattern, text)
        
        current_sentence = ""
        for part in parts:
            current_sentence += part
            if re.search(r'[.!?…]$', part.strip()):
                sentences.append(current_sentence.strip())
                current_sentence = ""
        
        if current_sentence.strip():
            sentences.append(current_sentence.strip())
        
        # Create SSML with appropriate breaks and prosody
        ssml_text = "<speak>"
        
        for i, sentence in enumerate(sentences):
            # Add prosody based on sentence type
            if sentence.endswith('?'):
                ssml_text += f'<prosody rate="95%" pitch="+0.5st">{sentence}</prosody>'
            elif sentence.endswith('!'):
                ssml_text += f'<prosody rate="100%" pitch="+1st">{sentence}</prosody>'
            else:
                ssml_text += f'<prosody rate="90%">{sentence}</prosody>'
            
            # Add appropriate pause after each sentence
            if i < len(sentences) - 1:
                ssml_text += '<break time="750ms"/>'
        
        ssml_text += "</speak>"
        
        # Create Google Cloud TTS client
        client = self.texttospeech.TextToSpeechClient()
        
        # Build the synthesis input with SSML
        synthesis_input = self.texttospeech.SynthesisInput(ssml=ssml_text)
        
        # Build the voice request
        voice_params = self.texttospeech.VoiceSelectionParams(
            language_code=language,
            name=voice
        )
        
        # Select the audio file type
        audio_config = self.texttospeech.AudioConfig(
            audio_encoding=self.texttospeech.AudioEncoding.MP3,
            speaking_rate=0.95  # Slightly slower for storytelling
        )
        
        # Perform the text-to-speech request
        try:
            response = client.synthesize_speech(
                input=synthesis_input,
                voice=voice_params,
                audio_config=audio_config
            )
            
            # Write the response to the output file
            with open(output_path, "wb") as out:
                out.write(response.audio_content)
                
            logger.info(f"Generated story speech saved to {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating story speech with Google Cloud TTS: {str(e)}")
            raise


class GTTS(TTSEngine):
    """
    TTS engine using Google Translate's TTS API via the gTTS library.
    
    Free to use but with limited voice options and quality.
    Good for basic use cases without requiring API keys.
    """
    
    def __init__(self):
        """Initialize the gTTS engine."""
        super().__init__()
        
        # Try to load gtts
        try:
            from gtts import gTTS
            self.gTTS = gTTS
        except ImportError:
            logger.error("Failed to import gtts. Install with: pip install gtts")
            raise ImportError("gtts library not found")
    
    def generate_speech(self, text, output_path, voice=None, language="en"):
        """
        Generate speech using gTTS.
        
        Args:
            text (str): The text to convert to speech
            output_path (str): Path to save the audio file
            voice (str, optional): Not used for gTTS (only language matters)
            language (str, optional): Language code
            
        Returns:
            str: Path to the generated audio file
        """
        # Preprocess text
        text = self.prepare_text(text)
        
        try:
            # Create gTTS object
            tts = self.gTTS(text=text, lang=language, slow=False)
            
            # Save to file
            tts.save(output_path)
            
            logger.info(f"Generated speech saved to {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating speech with gTTS: {str(e)}")
            raise
    
    def generate_speech_for_story(self, text, output_path, voice=None, language="en"):
        """
        Generate speech optimized for storytelling using gTTS.
        
        Since gTTS doesn't support SSML, this implementation adds
        extra pauses between sentences by generating separate audio
        files and concatenating them.
        
        Args:
            text (str): The story text to convert to speech
            output_path (str): Path to save the audio file
            voice (str, optional): Not used for gTTS
            language (str, optional): Language code
            
        Returns:
            str: Path to the generated audio file
        """
        # Preprocess text
        text = self.prepare_text(text)
        
        # Split into sentences
        sentences = []
        pattern = r'(?<=[.!?…])\s+(?=[A-Z0-9"])'
        parts = re.split(pattern, text)
        
        current_sentence = ""
        for part in parts:
            current_sentence += part
            if re.search(r'[.!?…]$', part.strip()):
                sentences.append(current_sentence.strip())
                current_sentence = ""
        
        if current_sentence.strip():
            sentences.append(current_sentence.strip())
        
        try:
            # For concatenating audio files
            from pydub import AudioSegment
            
            # Create a temporary directory for sentence audio files
            import tempfile
            temp_dir = tempfile.mkdtemp()
            
            # Generate speech for each sentence
            audio_segments = []
            
            for i, sentence in enumerate(sentences):
                # Create gTTS object for this sentence
                sentence_path = os.path.join(temp_dir, f"sentence_{i}.mp3")
                tts = self.gTTS(text=sentence, lang=language, slow=False)
                tts.save(sentence_path)
                
                # Load the audio segment
                audio_segment = AudioSegment.from_mp3(sentence_path)
                
                # Add to the list
                audio_segments.append(audio_segment)
                
                # Add a pause after each sentence (except the last one)
                if i < len(sentences) - 1:
                    pause_duration = 750  # 750ms pause
                    pause = AudioSegment.silent(duration=pause_duration)
                    audio_segments.append(pause)
            
            # Concatenate all segments
            combined = sum(audio_segments)
            
            # Export the combined audio
            combined.export(output_path, format="mp3")
            
            # Clean up
            import shutil
            shutil.rmtree(temp_dir)
            
            logger.info(f"Generated story speech saved to {output_path}")
            return output_path
            
        except ImportError:
            logger.warning("pydub not installed, falling back to standard speech generation")
            return self.generate_speech(text, output_path, voice, language)
            
        except Exception as e:
            logger.error(f"Error generating story speech with gTTS: {str(e)}")
            raise


class PyttsxTTS(TTSEngine):
    """
    TTS engine using the pyttsx3 library for offline text-to-speech.
    
    Works without internet connection but with limited voice quality.
    Uses the system's installed TTS voices.
    """
    
    def __init__(self):
        """Initialize the pyttsx3 engine."""
        super().__init__()
        
        # Try to load pyttsx3
        try:
            import pyttsx3
            self.pyttsx3 = pyttsx3
        except ImportError:
            logger.error("Failed to import pyttsx3. Install with: pip install pyttsx3")
            raise ImportError("pyttsx3 library not found")
    
    def generate_speech(self, text, output_path, voice=None, language=None):
        """
        Generate speech using pyttsx3.
        
        Args:
            text (str): The text to convert to speech
            output_path (str): Path to save the audio file
            voice (str, optional): Voice ID to use (system-dependent)
            language (str, optional): Not directly used (voice determines language)
            
        Returns:
            str: Path to the generated audio file
        """
        # Preprocess text
        text = self.prepare_text(text)
        
        try:
            # Initialize the engine
            engine = self.pyttsx3.init()
            
            # Set voice if specified
            if voice is not None:
                engine.setProperty('voice', voice)
            
            # Set rate and volume
            engine.setProperty('rate', 150)  # Speed in words per minute
            engine.setProperty('volume', 1.0)  # Volume (0.0 to 1.0)
            
            # Save to file
            engine.save_to_file(text, output_path)
            
            # Wait for the file to be created
            engine.runAndWait()
            
            logger.info(f"Generated speech saved to {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating speech with pyttsx3: {str(e)}")
            raise
    
    def list_available_voices(self):
        """
        List all available voices for pyttsx3.
        
        Returns:
            list: List of available voice IDs
        """
        try:
            engine = self.pyttsx3.init()
            voices = engine.getProperty('voices')
            
            voice_list = []
            for voice in voices:
                voice_list.append({
                    'id': voice.id,
                    'name': voice.name,
                    'languages': voice.languages,
                    'gender': voice.gender,
                    'age': voice.age
                })
            
            return voice_list
            
        except Exception as e:
            logger.error(f"Error listing voices with pyttsx3: {str(e)}")
            raise


# Factory function to create the appropriate TTS engine
def create_tts_engine(engine_type="gtts", api_key_path=None):
    """
    Create a TTS engine of the specified type.
    
    Args:
        engine_type (str): Type of TTS engine to create
                          ('google_cloud', 'gtts', or 'pyttsx3')
        api_key_path (str, optional): Path to Google Cloud API key file
        
    Returns:
        TTSEngine: An instance of the specified TTS engine
    """
    if engine_type == "google_cloud":
        return GoogleTTS(api_key_path=api_key_path)
    elif engine_type == "gtts":
        return GTTS()
    elif engine_type == "pyttsx3":
        return PyttsxTTS()
    else:
        raise ValueError(f"Unsupported TTS engine type: {engine_type}")


# Usage example if this module is run directly
if __name__ == "__main__":
    # Example text
    example_text = """Once upon a time, there was a small village nestled in a valley. 
    The people who lived there were kind and hardworking. Every morning, they would wake up at dawn.
    One day, a stranger arrived at the village. He carried a mysterious package.
    "What's in the package?" asked the curious villagers. The stranger smiled but said nothing."""
    
    # Create a TTS engine (using gTTS by default)
    tts_engine = create_tts_engine(engine_type="gtts")
    
    # Generate speech for the example text
    output_path = "example_speech.mp3"
    tts_engine.generate_speech_for_story(example_text, output_path, language="en")
    
    print(f"Generated speech file: {output_path}")