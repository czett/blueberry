import speech_recognition as sr
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import time
import os, wave
import sounddevice as sd
import numpy as np
import threading
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

def file_recognize(fn):
    filename = f"audio/{fn}.wav"
    
    try:
        with sr.AudioFile(filename) as source:
            audio = r.record(source)
            text = r.recognize_google(audio, language="de-DE")
            return (True, text)
    except sr.UnknownValueError:
        return (False, "Google Speech Recognition didn't understand.")
    except sr.RequestError as e:
        return (False, f"Error with Google Speech Recognition: {e}")

def recognize_from_mic(fn):
    samplerate = 16000
    min_duration = 1.5
    silence_threshold = 0.02
    silence_count = 0
    duration = 0
    
    audio_recording = []
    
    start_time = time.time()
    
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
    
    # wav.write(f"audio/{fn}.wav", samplerate, audio_recording)

    output_path = f"audio/{fn}.wav"
    with wave.open(output_path, "wb") as wf:
        wf.setnchannels(1)  # Mono
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(samplerate)
        wf.writeframes(audio_recording.tobytes())

    sd.wait()

def record_fixed_duration(filename: str, duration: int, samplerate: int = 44100):
    audio_recording = sd.rec(int(samplerate * duration), samplerate=samplerate, channels=1, dtype="float32")
    sd.wait()
    audio_recording = np.array(audio_recording).flatten()
    audio_recording = np.int16(audio_recording / np.max(np.abs(audio_recording)) * 32767)  # Normierung
    wav.write(f"audio/{filename}.wav", samplerate, audio_recording)

def vosk_transcribe(fn):
    # Load the model
    model = Model("stt/vosk-model-small-de-0.15")
    filename = f"audio/{fn}.wav"

    # Open the audio file
    with wave.open(filename, "rb") as wf:
        # Validate audio format
        if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getframerate() not in [8000, 16000]:
            raise ValueError("Audio file must be WAV format, mono, 16-bit, with 8kHz or 16kHz sample rate.")

        # Initialize recognizer
        recognizer = KaldiRecognizer(model, wf.getframerate())

        # Process the audio file
        transcription = []
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                transcription.append(result.get("text", ""))

        # Add the final result
        final_result = json.loads(recognizer.FinalResult())
        transcription.append(final_result.get("text", ""))

    return " ".join(transcription)
