import os
import shutil
import asyncio
from pydub import AudioSegment
from .audio_utils import extract_audio_from_video, adjust_wav_speed, merge_audio_video, create_silent_wav, get_video_duration
from .transcriber import Transcriber
from .idiom_replacer import IdiomReplacer
from .translator import TextTranslator
from .tts import TTSGenerator
try:
    from utils.utils import female_to_male, get_gender_from_audio
except ImportError:
    # Fallback or handle if utils not found (e.g. if structure changes)
    import sys
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from utils.utils import female_to_male, get_gender_from_audio


class DubbingEngine:
    def __init__(self, output_dir="output"):
        self.output_dir = output_dir
        self.temp_dir = os.path.join(output_dir, "temp")
        os.makedirs(self.temp_dir, exist_ok=True)
        
        self.transcriber = Transcriber()
        self.idiom_replacer = IdiomReplacer()
        self.translator = TextTranslator()
        self.tts = TTSGenerator()

    async def process_video(self, video_path, target_lang, output_video_path):
        print(f"Processing video: {video_path}")
        
        # 1. Extract Audio
        original_audio_path = os.path.join(self.temp_dir, "original.wav")
        if not extract_audio_from_video(video_path, original_audio_path):
            print("Failed to extract audio.")
            return False
            
        # Load original audio for segment extraction
        original_audio_full = AudioSegment.from_file(original_audio_path)

        # 2. Transcribe
        segments = self.transcriber.transcribe(original_audio_path)
        if not segments:
            print("No speech detected.")
            return False
            
        print(f"Detected {len(segments)} segments.")

        # 3. Process Segments (Idiom Replacement + Translation)
        processed_segments = []
        
        # Prepare batch translation if possible, but for now let's do it sequentially or gather
        # to ensure we keep track of segment indices.
        
        for i, seg in enumerate(segments):
            original_text = seg["text"]
            start_time = seg["start"]
            end_time = seg["end"]
            duration = end_time - start_time
            
            # a. Idiom Replacement
            literal_text = self.idiom_replacer.replace(original_text)
            
            # b. Translation
            # Note: We are calling async method synchronously here for simplicity in this loop, 
            # or we can gather them. Let's gather them for efficiency.
            processed_segments.append({
                "index": i,
                "start": start_time,
                "end": end_time,
                "duration": duration,
                "original_text": original_text,
                "literal_text": literal_text,
                "translated_text": "" # To be filled
            })

        # Batch translate
        texts_to_translate = [s["literal_text"] for s in processed_segments]
        translated_texts = await self.translator.translate_batch(texts_to_translate, dest_lang=target_lang)
        
        for i, text in enumerate(translated_texts):
            processed_segments[i]["translated_text"] = text

        # 4. Generate TTS and Adjust Speed
        final_audio = AudioSegment.silent(duration=0)
        current_time_ms = 0
        
        # We need to construct the timeline.
        # Gaps between segments should be filled with silence (or original background noise if we split tracks,
        # but for now let's just silence/duck).
        
        # Actually, a better approach is to create a base silent track of the total duration 
        # (we need total duration of video) and overlay segments.
        # But we don't know total duration easily unless we probe video.
        # Let's just build it chronologically.

        # First segment starts at processed_segments[0]['start']
        # We need to handle the gap before the first segment.
        
        for i, seg in enumerate(processed_segments):
            start_ms = int(seg['start'] * 1000)
            target_duration_ms = int(seg['duration'] * 1000)
            
            # Gap handling
            if start_ms > current_time_ms:
                silence_duration = start_ms - current_time_ms
                final_audio += AudioSegment.silent(duration=silence_duration)
                current_time_ms += silence_duration
            
            # Generate TTS
            tts_filename = os.path.join(self.temp_dir, f"seg_{i}.mp3") # gTTS saves as mp3 usually, but our wrapper is flexible.
            # Our TTS wrapper saves to path.
            
            # Translation might return empty if silent?
            text = seg['translated_text']
            if not text.strip():
                # If translation is empty, just add silence for the duration
                final_audio += AudioSegment.silent(duration=target_duration_ms)
                current_time_ms += target_duration_ms
                continue

            if self.tts.generate_audio(text, target_lang, tts_filename):
                # Now we have the TTS file. We need to check its duration.
                tts_audio = AudioSegment.from_file(tts_filename)
                tts_duration_ms = len(tts_audio)
                
                # Speed adjustment
                # We want the TTS to fit into target_duration_ms.
                # However, if it's too fast, it sounds bad. 
                # If TTS is shorter than target, we can pad with silence.
                # If TTS is longer, we must speed it up.
                
                # Let's use our audio_utils adjust_wav_speed (which uses wave/audioop) 
                # So we need to convert to wav first if it is mp3.
                tts_wav_path = os.path.join(self.temp_dir, f"seg_{i}.wav")
                tts_audio.export(tts_wav_path, format="wav")
                
                # Gender Check & Voice Conversion
                # Extract original segment audio to check gender
                # seg['start'] is in seconds
                orig_start_ms = int(seg['start'] * 1000)
                orig_end_ms = int(seg['end'] * 1000)
                
                # Ensure bounds
                if orig_end_ms > len(original_audio_full):
                    orig_end_ms = len(original_audio_full)
                    
                if orig_start_ms < orig_end_ms:
                    seg_audio_chunk = original_audio_full[orig_start_ms:orig_end_ms]
                    seg_chunk_path = os.path.join(self.temp_dir, f"seg_orig_{i}.wav")
                    seg_audio_chunk.export(seg_chunk_path, format="wav")
                    
                    try:
                        detected_gender = get_gender_from_audio(seg_chunk_path)                        
                        if detected_gender == 'male':

                            female_to_male(tts_wav_path, tts_wav_path)
                            tts_audio = AudioSegment.from_wav(tts_wav_path)
                            tts_duration_ms = len(tts_audio) # Update duration if it changed (usually similar)
                    except Exception as e:
                        print(f"Gender detection/conversion failed for segment {i}: {e}")

                # Adjust speed
                # Check ratio
                ratio = tts_duration_ms / target_duration_ms
                
                if ratio > 1.0: 
                    # TTS is longer, needs to speed up
                    # Pass target duration in seconds
                    adjust_wav_speed(tts_wav_path, seg['duration'], overwrite_path=tts_wav_path)
                    # Reload adjusted
                    adjusted_seg = AudioSegment.from_wav(tts_wav_path)
                else:
                    # TTS is shorter, we kept it as is, but we will center it or just append silence?
                    # Let's just use the original TTS and pad the remaining time after adding it to timeline
                    adjusted_seg = AudioSegment.from_wav(tts_wav_path)
                
                # Now append to final_audio
                final_audio += adjusted_seg
                current_time_ms += len(adjusted_seg)
                
                # If we sped it up, it should adhere to target_duration.
                # If we didn't (because it was shorter), we need to fill the rest of the slot.
                remaining_ms = target_duration_ms - len(adjusted_seg)
                if remaining_ms > 0:
                    final_audio += AudioSegment.silent(duration=remaining_ms)
                    current_time_ms += remaining_ms
                    
            else:
                 # TTS failed? Silent.
                final_audio += AudioSegment.silent(duration=target_duration_ms)
                current_time_ms += target_duration_ms
        
        # 5. Merge
        print(f"Merging into {output_video_path}...")
        
        # Check total duration and adjust if necessary
        video_duration_sec = get_video_duration(video_path)
        if video_duration_sec:
            final_audio_duration_ms = len(final_audio)
            video_duration_ms = video_duration_sec * 1000
            
            print(f"Video Duration: {video_duration_sec}s, Audio Duration: {final_audio_duration_ms/1000}s")
            
            # Tolerance of 100ms? 
            if final_audio_duration_ms > video_duration_ms:
                print("Audio is longer than video. Squeezing...")
                # Export temp for adjustment
                temp_dub_path = os.path.join(self.temp_dir, "temp_dub.wav")
                final_audio.export(temp_dub_path, format="wav")
                
                adjust_wav_speed(temp_dub_path, video_duration_sec, overwrite_path=temp_dub_path)
                final_audio = AudioSegment.from_wav(temp_dub_path)
            elif final_audio_duration_ms < video_duration_ms:
                print("Audio is shorter than video. Padding with silence...")
                silence_duration = video_duration_ms - final_audio_duration_ms
                final_audio += AudioSegment.silent(duration=silence_duration)
        
        # Export full audio
        dubbed_audio_path = os.path.join(self.temp_dir, "dubbed.wav")
        final_audio.export(dubbed_audio_path, format="wav")

        merge_audio_video(video_path, dubbed_audio_path, output_video_path)
        
        # Cleanup
        # shutil.rmtree(self.temp_dir) # Keep for debugging if needed, or delete.
        print("Done.")
        return True
