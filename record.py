import speech_recognition as sr
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import time
import os

r = sr.Recognizer()

if not os.path.exists("audio"):
    os.makedirs("audio")

def file_recognize(fn):
    filename = f"audio/{fn}.wav"
    
    try:
        with sr.AudioFile(filename) as source:
            audio = r.record(source)
            text = r.recognize_google(audio, language="de-DE")
            return text
    except sr.UnknownValueError:
        return "Google Speech Recognition didn't understand."
    except sr.RequestError as e:
        return f"Error with Google Speech Recognition: {e}"

def recognize_from_mic(fn):
    samplerate = 44100
    min_duration = 2
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
    
    wav.write(f"audio/{fn}.wav", samplerate, audio_recording)
    sd.wait()