import soundfile as sf
import librosa
import psola
import numpy as np
import scipy.signal
FRAME_LENGTH = 1024
FMIN = librosa.note_to_hz('C2')
FMAX = librosa.note_to_hz('C5')

def female_to_male(input_wav: str, output_wav: str, pitch_factor: float = None):
    audio, sr = sf.read(input_wav)
    if audio.ndim > 1:
        audio = audio[0, :]  # Use first channel if stereo
    f0, _, _ = librosa.pyin(audio, frame_length=FRAME_LENGTH, sr=sr, fmin=FMIN, fmax=FMAX)
    nans = np.isnan(f0)
    if np.any(~nans):
        f0[nans] = np.interp(np.flatnonzero(nans), np.flatnonzero(~nans), f0[~nans])
    else:
        f0[:] = FMIN  # fallback if pyin fails
    avg_f0 = np.mean(f0)
    # is_female = avg_f0 > 160  # typical female F0 > 160Hz
    # if not is_female:
    #    print(f"DEBUG: female_to_male - Skipped because avg_f0 {avg_f0} <= 160")
    #    sf.write(output_wav, audio, sr)
    #    return
    if pitch_factor is None:
        pitch_factor = 110 / avg_f0
    shifted_f0 = scipy.signal.medfilt(f0 * pitch_factor, kernel_size=11)
    male_audio = psola.vocode(audio, sample_rate=int(sr), target_pitch=shifted_f0, fmin=FMIN, fmax=FMAX)
    sf.write(output_wav, male_audio, sr)

import torch
from transformers import Wav2Vec2ForSequenceClassification, Wav2Vec2FeatureExtractor
model_name = "prithivMLmods/Common-Voice-Geneder-Detection"
model = Wav2Vec2ForSequenceClassification.from_pretrained(model_name)
processor = Wav2Vec2FeatureExtractor.from_pretrained(model_name)
id2label = {
"0": "female",
"1": "male"}
def get_gender_from_audio(audio_path):

    speech, sample_rate = librosa.load(audio_path, sr=16000)
    inputs = processor(
        speech,
        sampling_rate=sample_rate,
        return_tensors="pt",
        padding=True
    )
    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits
        probs = torch.nn.functional.softmax(logits, dim=1).squeeze().tolist()
    prediction = {id2label[str(i)]: round(probs[i], 3) for i in range(len(probs))}
    return max(prediction, key=prediction.get)