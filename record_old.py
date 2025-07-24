import speech_recognition as sr
import sounddevice as sd
import numpy as np
import wave
import time
import os
from vosk import Model, KaldiRecognizer
import json

class AudioRecorder:
    def __init__(self, samplerate=16000, channels=1):
        self.samplerate = samplerate
        self.channels = channels
        self.recording = False
        self.frames = []

    def _callback(self, indata, frames, time, status):
        if self.recording:
            self.frames.append(indata.copy())

    def start(self):
        self.frames = []
        self.recording = True
        self.stream = sd.InputStream(samplerate=self.samplerate,
                                     channels=self.channels,
                                     callback=self._callback)
        self.stream.start()

    def stop(self):
        self.recording = False
        self.stream.stop()
        self.stream.close()

    def get_audio(self):
        if self.frames:
            return np.concatenate(self.frames)
        return np.array([])

r = sr.Recognizer()

if not os.path.exists("audio"):
    os.makedirs("audio")

# def file_recognize(fn):
#     filename = f"audio/{fn}.wav"
    
#     try:
#         with sr.AudioFile(filename) as source:
#             audio = r.record(source)
#             text = r.recognize_google(audio, language="de-DE")
#             return (True, text)
#     except sr.UnknownValueError:
#         return (False, "Google Speech Recognition didn't understand.")
#     except sr.RequestError as e:
#         return (False, f"Error with Google Speech Recognition: {e}")

model = Model("models/de/vosk-model-small-de-0.15")

def file_recognize(fn):
    filename = f"audio/{fn}.wav"
    wf = wave.open(filename, "rb")
    rec = KaldiRecognizer(model, wf.getframerate())

    result_text = ""
    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            result = json.loads(rec.Result())
            result_text += result.get("text", "") + " "
    result = json.loads(rec.FinalResult())
    result_text += result.get("text", "")

    if result_text.strip():
        return (True, result_text.strip())
    return (False, "")

def recognize_from_mic(fn):
    samplerate = 16000
    min_duration = 1.5
    silence_threshold = 0.02
    silence_count = 0
    duration = 0
    
    audio_recording = []
    
    while True:
        audio_chunk = sd.rec(int(samplerate), samplerate=samplerate, channels=1, dtype="float32")
        sd.wait()
        audio_chunk = audio_chunk.flatten()
        audio_recording.extend(audio_chunk)
        duration += 1
        if duration >= 2:
            break

    while True:
        audio_chunk = sd.rec(int(samplerate), samplerate=samplerate, channels=1, dtype="float32")
        sd.wait()
        audio_chunk = audio_chunk.flatten()
        amplitude = np.max(np.abs(audio_chunk))
        
        if amplitude < silence_threshold:
            silence_count += 1
        else:
            silence_count = 0
        
        if silence_count >= min_duration:
            break
        
        audio_recording.extend(audio_chunk)
        duration += 1

    audio_recording = np.array(audio_recording)
    audio_recording = np.int16(audio_recording / np.max(np.abs(audio_recording)) * 32767)

    output_path = f"audio/{fn}.wav"
    with wave.open(output_path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(samplerate)
        wf.writeframes(audio_recording.tobytes())

    sd.wait()

def record_fixed_duration(filename: str, duration: int, samplerate: int = 44100):
    audio_recording = sd.rec(int(samplerate * duration), samplerate=samplerate, channels=1, dtype="float32")
    sd.wait()
    audio_recording = np.array(audio_recording).flatten()
    audio_recording = np.int16(audio_recording / np.max(np.abs(audio_recording)) * 32767)
    
    with wave.open(f"audio/{filename}.wav", "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(samplerate)
        wf.writeframes(audio_recording.tobytes())
