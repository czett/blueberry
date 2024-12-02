import pvporcupine
from pvrecorder import PvRecorder
import record
import random
import string
import os
import time
import ollama
from gtts import gTTS
import sounddevice as sd
import soundfile as sf
import re
import io
import pyttsx3
from espeakng import ESpeakNG

def play_startup_sound():
    file_path = "assets/startup.mp3"
    data, samplerate = sf.read(file_path)
    sd.play(data, samplerate)
    sd.wait()

def ask_and_speak(prompt: str):
    try:
        stream = ollama.chat(model="mistral", messages=[{"role": "user", "content": prompt}], stream=True)
        buffer = ""
        combined_text = ""

        for chunk in stream:
            chunk_text = chunk["message"]["content"]
            combined_text += chunk_text
            buffer += chunk_text

            print(chunk_text, end="", flush=True)

            sentences = re.split(r'([.!?])', buffer)

            for i in range(0, len(sentences) - 1, 2):
                sentence = sentences[i] + sentences[i + 1]
                text_to_speech(sentence.strip())
                buffer = buffer[len(sentence):]

        if buffer.strip():
            es_text_to_speech(buffer.strip())

        return combined_text
    except:
        pass

def text_to_speech(text):
    tts = gTTS(text=text, lang="de")
    audio_buffer = io.BytesIO()
    tts.write_to_fp(audio_buffer)
    audio_buffer.seek(0)

    data, samplerate = sf.read(audio_buffer, dtype="float32")
    sd.play(data, samplerate)
    sd.wait()

def pyttsx3_text_to_speech(text: str):
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')

    for voice in voices:
        print(f"Voice: {voice.name}, ID: {voice.id}, Languages: {voice.languages}")

    for voice in voices:
        if "de" in voice.languages:
            engine.setProperty('voice', voice.id)
            break

    engine.setProperty('rate', 300)
    engine.setProperty('volume', 1.0)

    engine.say(text)
    engine.runAndWait()

def es_text_to_speech(text: str):
    tts = ESpeakNG()
    tts.voice = "de"
    tts.speed = 150
    tts.volume = 100
    tts.say(text)

keywords = ["blueberry"]

with open("credentials.yml", "r") as creds:
    access_key = creds.read()

def audio_name(length: int) -> str:
    return "".join([random.choice(string.ascii_lowercase) for i in range(length)])

def check_files() -> None:
    for audio_file in os.listdir("audio"):
        file_path = os.path.join("audio", audio_file)
        
        if os.path.isfile(file_path):
            file_creation_time = os.path.getctime(file_path)
            current_time = time.time()
            age_in_seconds = current_time - file_creation_time

            if age_in_seconds > 30:
                os.remove(file_path)

porcupine = pvporcupine.create(access_key=access_key, keywords=keywords)
recoder = PvRecorder(device_index=-1, frame_length=porcupine.frame_length)

import time

def listen_for_follow_up(duration: int) -> bool:
    temp_filename = audio_name(16)
    record.record_fixed_duration(temp_filename, duration=duration)

    recognized_result = record.file_recognize(temp_filename)

    if recognized_result[0]: # if new text recognized
        return (True, recognized_result[1])
    
    return (False, "")

try:
    recoder.start()

    while True:
        keyword_index = porcupine.process(recoder.read())
        go_again = True
        if keyword_index >= 0:
            print(f"...")
            play_startup_sound()
            check_files()

            name = audio_name(16)
            record.recognize_from_mic(name)
            
            text = record.file_recognize(name)[1]
            print("verstandener Text: " + text)

            ask_and_speak(text)

            lfu = listen_for_follow_up(duration=10)

            while lfu[0] == True:
                ask_and_speak(lfu[1])
                lfu = listen_for_follow_up(duration=10)

            print("Kein weiteres Gespräch erkannt.")

except KeyboardInterrupt:
    recoder.stop()
finally:
    porcupine.delete()
    recoder.delete()