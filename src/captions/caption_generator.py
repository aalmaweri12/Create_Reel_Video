import re
from datetime import timedelta

class CaptionGenerator:
    """
    A class for generating caption files (SRT) from text input.
    Specialized for processing stories sentence by sentence.
    """
    
    def __init__(self, approach="sentence"):
        """
        Initialize the CaptionGenerator.
        
        Args:
            approach (str): The approach to use for caption generation.
                            Options: "sentence", "paragraph", "word", "simple"
        """
        self.approach = approach
    
    def generate_srt(self, text, audio_duration, output_path):
        """
        Generate an SRT file with appropriate timing.
        
        Args:
            text (str): The text to convert to subtitles
            audio_duration (float): Duration of the audio in seconds
            output_path (str): The path to save the SRT file
            
        Returns:
            str: Path to the generated SRT file
        """
        if self.approach == "sentence":
            return self._sentence_based_srt(text, audio_duration, output_path)
        elif self.approach == "paragraph":
            return self._paragraph_based_srt(text, audio_duration, output_path)
        elif self.approach == "word":
            return self._word_based_srt(text, audio_duration, output_path)
        elif self.approach == "simple":
            return self._simple_srt(text, audio_duration, output_path)
        else:
            raise ValueError(f"Unsupported caption approach: {self.approach}")
    
    def _format_time(self, seconds):
        """
        Format time for SRT (HH:MM:SS,mmm).
        
        Args:
            seconds (float): Time in seconds
            
        Returns:
            str: Formatted time string
        """
        # Handle negative time (should never happen, but just in case)
        if seconds < 0:
            seconds = 0
            
        # Calculate hours, minutes, seconds, and milliseconds
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds_whole = int(seconds % 60)
        milliseconds = int((seconds % 1) * 1000)
        
        # Format as HH:MM:SS,mmm
        return f"{hours:02d}:{minutes:02d}:{seconds_whole:02d},{milliseconds:03d}"
    
    def _sentence_based_srt(self, text, audio_duration, output_path):
        """
        Generate SRT based on sentences - ideal for stories.
        
        Each sentence becomes a separate caption entry.
        Duration is proportional to sentence length.
        
        Args:
            text (str): The text to convert to subtitles
            audio_duration (float): Duration of the audio in seconds
            output_path (str): The path to save the SRT file
            
        Returns:
            str: Path to the generated SRT file
        """
        # Use a more comprehensive sentence detection regex
        # This handles various end punctuation marks and preserves them in the output
        sentences = []
        # Match sentences ending with period, exclamation mark, question mark
        # Also handle ellipses (...) and quotes
        pattern = r'(?<=[.!?…])\s+(?=[A-Z0-9"])'
        # Split the text using the pattern
        parts = re.split(pattern, text)
        
        # Clean up and combine any fragments that aren't complete sentences
        current_sentence = ""
        for part in parts:
            current_sentence += part
            if re.search(r'[.!?…]$', part.strip()):
                sentences.append(current_sentence.strip())
                current_sentence = ""
        
        # Add any remaining text as a sentence
        if current_sentence.strip():
            sentences.append(current_sentence.strip())
        
        # Calculate time per sentence based on length (character count)
        # This ensures longer sentences get proportionally more time
        total_chars = sum(len(s) for s in sentences)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            cumulative_time = 0
            
            for i, sentence in enumerate(sentences):
                # Calculate duration proportional to sentence length
                # with a minimum duration for very short sentences
                sentence_duration = max(1.5, (len(sentence) / total_chars) * audio_duration)
                
                start_time = cumulative_time
                end_time = cumulative_time + sentence_duration
                cumulative_time = end_time
                
                # Format times for SRT
                start_formatted = self._format_time(start_time)
                end_formatted = self._format_time(end_time)
                
                # Write SRT entry
                f.write(f"{i+1}\n")
                f.write(f"{start_formatted} --> {end_formatted}\n")
                f.write(f"{sentence}\n\n")
        
        return output_path
    
    def _paragraph_based_srt(self, text, audio_duration, output_path):
        """
        Generate SRT based on paragraphs.
        
        Each paragraph becomes a separate caption entry.
        Duration is proportional to paragraph length.
        
        Args:
            text (str): The text to convert to subtitles
            audio_duration (float): Duration of the audio in seconds
            output_path (str): The path to save the SRT file
            
        Returns:
            str: Path to the generated SRT file
        """
        # Split text into paragraphs (by double newlines)
        paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
        
        # Calculate time per paragraph (proportional to length)
        total_chars = sum(len(p) for p in paragraphs)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            cumulative_time = 0
            
            for i, paragraph in enumerate(paragraphs):
                # Calculate duration proportional to paragraph length
                paragraph_duration = (len(paragraph) / total_chars) * audio_duration
                
                start_time = cumulative_time
                end_time = cumulative_time + paragraph_duration
                cumulative_time = end_time
                
                # Format times for SRT
                start_formatted = self._format_time(start_time)
                end_formatted = self._format_time(end_time)
                
                # Write SRT entry
                f.write(f"{i+1}\n")
                f.write(f"{start_formatted} --> {end_formatted}\n")
                f.write(f"{paragraph}\n\n")
        
        return output_path
    
    def _word_based_srt(self, text, audio_duration, output_path):
        """
        Generate SRT with word-by-word timing.
        
        Creates caption entries with small groups of words.
        Useful for highly synchronized captioning.
        
        Args:
            text (str): The text to convert to subtitles
            audio_duration (float): Duration of the audio in seconds
            output_path (str): The path to save the SRT file
            
        Returns:
            str: Path to the generated SRT file
        """
        # Split text into words
        words = text.split()
        
        # Group words into small chunks (3-5 words per entry)
        words_per_group = 4
        word_groups = []
        
        for i in range(0, len(words), words_per_group):
            group = words[i:i+words_per_group]
            word_groups.append(' '.join(group))
        
        # Calculate time per word group
        time_per_group = audio_duration / len(word_groups)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for i, group in enumerate(word_groups):
                start_time = i * time_per_group
                end_time = (i + 1) * time_per_group
                
                # Format times for SRT
                start_formatted = self._format_time(start_time)
                end_formatted = self._format_time(end_time)
                
                # Write SRT entry
                f.write(f"{i+1}\n")
                f.write(f"{start_formatted} --> {end_formatted}\n")
                f.write(f"{group}\n\n")
        
        return output_path
    
    def _simple_srt(self, text, audio_duration, output_path):
        """
        Generate a simple SRT with fixed-size segments.
        
        Divides text into roughly equal segments without
        considering sentence boundaries.
        
        Args:
            text (str): The text to convert to subtitles
            audio_duration (float): Duration of the audio in seconds
            output_path (str): The path to save the SRT file
            
        Returns:
            str: Path to the generated SRT file
        """
        # Simple approach: approximately even segments
        # Target around 10-12 words per caption
        words = text.split()
        words_per_segment = 12
        segments = []
        
        for i in range(0, len(words), words_per_segment):
            segment = ' '.join(words[i:i+words_per_segment])
            segments.append(segment)
        
        # Calculate time per segment
        time_per_segment = audio_duration / len(segments)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for i, segment in enumerate(segments):
                start_time = i * time_per_segment
                end_time = (i + 1) * time_per_segment
                
                # Format times for SRT
                start_formatted = self._format_time(start_time)
                end_formatted = self._format_time(end_time)
                
                # Write SRT entry
                f.write(f"{i+1}\n")
                f.write(f"{start_formatted} --> {end_formatted}\n")
                f.write(f"{segment}\n\n")
        
        return output_path


# Usage example if this module is run directly
if __name__ == "__main__":
    # Example text and audio duration
    example_text = """Once upon a time, there was a small village nestled in a valley. 
    The people who lived there were kind and hardworking. Every morning, they would wake up at dawn.
    One day, a stranger arrived at the village. He carried a mysterious package.
    "What's in the package?" asked the curious villagers. The stranger smiled but said nothing."""
    
    # Create a caption generator using the sentence approach
    generator = CaptionGenerator(approach="sentence")
    
    # Generate SRT file with 30 seconds of audio duration
    srt_path = "example_captions.srt"
    generator.generate_srt(example_text, 30.0, srt_path)
    
    print(f"Generated SRT file: {srt_path}")