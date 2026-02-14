import os
import wave
import audioop
import ffmpeg

def adjust_wav_speed(input_wav_path, target_duration_sec, overwrite_path=None):
    """
    Adjusts the speed of a WAV file to match a target duration.
    """
    if overwrite_path is None:
        overwrite_path = input_wav_path

    if not os.path.exists(input_wav_path):
        print(f"Error: File {input_wav_path} not found.")
        return

    try:
        with wave.open(input_wav_path, 'rb') as wf:
            n_channels = wf.getnchannels()
            sampwidth = wf.getsampwidth()
            framerate = wf.getframerate()
            n_frames = wf.getnframes()
            raw_data = wf.readframes(n_frames)

        if len(raw_data) == 0:
            return

        current_duration = n_frames / framerate
        if target_duration_sec <= 0:
            return 
            
        speed_factor = current_duration / target_duration_sec

        # Limit speed factor to avoid extreme distortion (e.g., 0.5x to 2.0x)
        # speed_factor = max(0.5, min(speed_factor, 2.0))

        if speed_factor != 1.0:
            # audioop.ratecv is a simple way to change speed (resampling)
            # state is None
            new_raw = audioop.ratecv(raw_data, sampwidth, n_channels, framerate,
                                     int(framerate * speed_factor), None)[0]
        else:
            new_raw = raw_data

        with wave.open(overwrite_path, 'wb') as wf:
            wf.setnchannels(n_channels)
            wf.setsampwidth(sampwidth)
            wf.setframerate(framerate)
            wf.writeframes(new_raw)
            
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
