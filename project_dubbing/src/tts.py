from gtts import gTTS
import os

class TTSGenerator:
    def __init__(self):
        pass

    def generate_audio(self, text, language, output_path):
        """
        Generates audio from text using gTTS and saves it to output_path.
        Returns True if successful, False otherwise.
        """
        if not text or not text.strip():
            return False

        try:
            tts = gTTS(text=text, lang=language)
            tts.save(output_path)
            return True
        except Exception as e:
            print(f"TTS Error for '{text}': {e}")
            return False
