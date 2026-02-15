import whisper
import warnings

# Suppress warnings from whisper/torch
warnings.filterwarnings("ignore")

class Transcriber:
    def __init__(self, model_size="medium"):
        print(f"Loading Whisper model ({model_size})...")
        self.model = whisper.load_model(model_size)

    def transcribe(self, audio_path, language="en"):
        """
        Transcribes audio file and returns segments.
        """
        print(f"Transcribing {audio_path}...")
        result = self.model.transcribe(audio_path, language=language)
        return result.get("segments", [])

