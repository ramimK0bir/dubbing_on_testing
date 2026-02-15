import os
import wave
import struct
import math
import ffmpeg
import sys

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

from audio_utils import get_video_duration, adjust_wav_speed, create_silent_wav

def create_dummy_video(filename, duration=5):
    """Creates a black video of specified duration."""
    try:
        (
            ffmpeg
            .input(f'color=c=black:s=640x480:d={duration}', f='lavfi')
            .output(filename)
            .run(overwrite_output=True, quiet=True)
        )
        return True
    except Exception as e:
        print(f"Failed to create dummy video: {e}")
        return False

def create_sine_wave_wav(filename, duration=6, sample_rate=44100):
    """Creates a sine wave wav file."""
    try:
        with wave.open(filename, 'w') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            
            data = []
            for i in range(int(duration * sample_rate)):
                value = int(32767.0 * math.sin(2 * math.pi * 440 * i / sample_rate))
                data.append(struct.pack('<h', value))
            
            wf.writeframes(b''.join(data))
        return True
    except Exception as e:
        print(f"Failed to create wav: {e}")
        return False

def test_duration_constraint():
    print("Testing Audio Duration Constraint...")
    
    # Setup paths
    video_path = "test_video.mp4"
    audio_path = "test_audio.wav"
    output_audio_path = "test_audio_adjusted.wav"
    
    # 1. Create Dummy Video (5s)
    print("Creating 5s dummy video...")
    if not create_dummy_video(video_path, duration=5):
        return
    
    # 2. Test get_video_duration
    duration = get_video_duration(video_path)
    print(f"Detected Video Duration: {duration}")
    if abs(duration - 5.0) > 0.1:
        print("FAIL: Video duration detection failed.")
    else:
        print("PASS: Video duration detection correct.")

    # 3. Create Dummy Audio (6s)
    print("Creating 6s dummy audio...")
    create_sine_wave_wav(audio_path, duration=6, sample_rate=16000)
    
    # 4. Squeeze Audio
    print("Squeezing audio to 5s...")
    adjust_wav_speed(audio_path, 5.0, overwrite_path=output_audio_path)
    
    # 5. Check Result
    with wave.open(output_audio_path, 'r') as wf:
        frames = wf.getnframes()
        rate = wf.getframerate()
        new_duration = frames / float(rate)
        
    print(f"New Audio Duration: {new_duration}")
    
    if abs(new_duration - 5.0) > 0.1:
        print("FAIL: Audio duration adjustment failed.")
    else:
        print("PASS: Audio duration adjustment correct.")

    # Cleanup
    if os.path.exists(video_path): os.remove(video_path)
    if os.path.exists(audio_path): os.remove(audio_path)
    if os.path.exists(output_audio_path): os.remove(output_audio_path)

if __name__ == "__main__":
    test_duration_constraint()
