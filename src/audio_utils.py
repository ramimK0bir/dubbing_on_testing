import os
import wave
import ffmpeg

def adjust_wav_speed(input_wav_path, target_duration_sec, overwrite_path=None):
    """
    Adjusts the speed of a WAV file to match a target duration using FFmpeg.
    """
    if overwrite_path is None:
        overwrite_path = input_wav_path

    if not os.path.exists(input_wav_path):
        print(f"Error: File {input_wav_path} not found.")
        return

    try:
        probe = ffmpeg.probe(input_wav_path)
        current_duration = float(probe['format']['duration'])
        
        if target_duration_sec <= 0:
            return 
            
        speed_factor = current_duration / target_duration_sec
        
        # Audioop is deprecated/removed in newer python, so we use ffmpeg atempo filter.
        # atempo filter is limited to [0.5, 2.0]. We chain if needed.
        
        stream = ffmpeg.input(input_wav_path)
        
        remaining_factor = speed_factor
        
        # Chain filters if outside range
        while remaining_factor > 2.0:
            stream = stream.filter('atempo', 2.0)
            remaining_factor /= 2.0
            
        while remaining_factor < 0.5:
            stream = stream.filter('atempo', 0.5)
            remaining_factor /= 0.5
            
        stream = stream.filter('atempo', remaining_factor)
        
        # Write to temp file then move if overwrite
        temp_output = input_wav_path + ".temp.wav"
        
        # We need to preserve original format if possible, or just standard pcm_s16le
        stream = stream.output(temp_output, acodec='pcm_s16le')
        stream.run(overwrite_output=True, quiet=True)
        
        if os.path.exists(temp_output):
            if os.path.exists(overwrite_path):
                os.remove(overwrite_path)
            os.rename(temp_output, overwrite_path)
            
    except ffmpeg.Error as e:
        print(f"FFmpeg Error adjusting speed: {e.stderr.decode('utf8') if e.stderr else str(e)}")
    except Exception as e:
        print(f"Error adjusting WAV speed: {e}")

def extract_audio_from_video(input_video, output_audio, sample_rate=16000):
    """
    Extracts audio from video using ffmpeg-python.
    """
    try:
        (
            ffmpeg
            .input(input_video)
            .output(output_audio, acodec='pcm_s16le', ar=sample_rate, ac=1)
            .run(cmd='ffmpeg', capture_stdout=True, capture_stderr=True, overwrite_output=True)
        )
        return True
    except ffmpeg.Error as e:
        print(f"FFmpeg Error: {e.stderr.decode('utf8')}")
        return False

def merge_audio_video(video_path, audio_path, output_path):
    """
    Merges audio and video, replacing the original audio.
    """
    try:
        video = ffmpeg.input(video_path)
        audio = ffmpeg.input(audio_path)
        
        (
            ffmpeg
            .output(video.video, audio, output_path, vcodec='copy', acodec='aac')
            .run(cmd='ffmpeg', capture_stdout=True, capture_stderr=True, overwrite_output=True)
        )
        return True
    except ffmpeg.Error as e:
        print(f"FFmpeg Merge Error: {e.stderr.decode('utf8')}")
        return False

def create_silent_wav(output_path, duration_sec, sample_rate=16000):
    with wave.open(output_path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        # 2 bytes per sample * sample_rate * duration
        num_frames = int(sample_rate * duration_sec)
        data = b'\x00\x00' * num_frames
        wf.writeframes(data)

def get_video_duration(video_path):
    """
    Returns the duration of the video in seconds using ffmpeg probe.
    """
    try:
        probe = ffmpeg.probe(video_path)
        video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
        if video_stream:
            return float(video_stream['duration'])
        else:
            # Fallback if no video stream found or duration missing?
            # Try format duration
            return float(probe['format']['duration'])
    except ffmpeg.Error as e:
        print(f"FFmpeg Probe Error: {e.stderr.decode('utf8')}")
        return None
    except Exception as e:
        print(f"Error getting video duration: {e}")
        return None
