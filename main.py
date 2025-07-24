import pvporcupine, re, io, wave, record_old, random, string, os, time, ollama, tools
from pvrecorder import PvRecorder
from deep_translator import GoogleTranslator
#from gtts import gTTS
#from espeakng import ESpeakNG
#import pyttsx3
#import scipy.io.wavfile as wav
from pytimeparse import parse
from pydub import AudioSegment
import sounddevice as sd
import soundfile as sf
import numpy as np
import asyncio
import edge_tts
import pygame
import json
import sys

pygame.mixer.init()
chat_history = []

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

with open("credentials.yml", "r") as c:
    lines = c.readlines()
    access_key = lines[0].strip()

def play_sound(fn:str, wait=True):
    file_path = f"assets/{fn}.mp3"
    data, samplerate = sf.read(file_path)
    sd.play(data, samplerate)
    if wait:
        sd.wait()

def listen_for_command():
    name = audio_name(16)
    record_old.recognize_from_mic(name)
    # play_sound("done")
    return name
    
def save_audio(filename, audio_data, samplerate):
    audio_data = (audio_data * 32767).astype(np.int16)  # Scale float32 data to int16
    with wave.open(filename, 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 2 bytes for 16-bit samples
        wav_file.setframerate(samplerate)
        wav_file.writeframes(audio_data.tobytes())

# def translate(text: str, flang: str, tlang: str) -> str:
#     return GoogleTranslator(source=flang, target=tlang).translate(text)

from translate import Translator

def translate(text: str, flang: str, tlang: str) -> str:
    translator = Translator(from_lang=flang, to_lang=tlang)
    return translator.translate(text)

def check_timers():
    if len(tools.check_timers()) > 0:
        for i in range(4):
            play_sound("timer")

def play_mp3_with_pygame(mp3_file):
    mp3_file = f"audio/{mp3_file}.mp3"
    pygame.mixer.init()
    pygame.mixer.music.load(mp3_file)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)
    pygame.mixer.music.stop()

# async def tts(text) -> None:
#     text = translate(text.strip(), flang="en", tlang="de")
#     VOICES = ["de-DE-ConradNeural"]
#     for voice in VOICES:
#         communicator = edge_tts.Communicate(text, voice)
#         name = audio_name(16)
#         await communicator.save(f"audio/{name}.mp3")
#     time.sleep(0.5)
#     play_mp3_with_pygame(name)

async def tts(text, rate='+0%', volume='+0%') -> None:
    text = translate(text.strip(), flang="en", tlang="de")
    VOICES = ["de-DE-KillianNeural"]
    for voice in VOICES:
        communicator = edge_tts.Communicate(
            text, 
            voice, 
            rate=rate,    # Geschwindigkeit anpassen
            volume=volume # Lautstärke anpassen
        )
        name = audio_name(16)
        await communicator.save(f"audio/{name}.mp3")
    time.sleep(0.5)
    play_mp3_with_pygame(name)

def ask_and_speak(prompt: str):
    print(f"Prompt: {prompt.lower()}")

    try:
        with open("prompt_config.json", "r") as pc:
            prefixes = json.load(pc)
            prompt_prefix = prefixes["standard"]

        if "weather" in prompt.lower():
            w = tools.weather()
            print(w)

            prompt = ""
            prompt_prefix = prefixes["weather"]
            prompt_data = {"_TEMP": w[0], "_RAIN": w[1]}
            
            print(prompt_prefix)
            for key, value in prompt_data.items():
                prompt_prefix = prompt_prefix.replace(key, str(value))
                print(key, value)

        if "timer" in prompt.lower():
            mod_prompt = prompt.lower() # for safety i guess :)
            mod_prompt = mod_prompt.replace("timer to", "timer for")
            mod_prompt = mod_prompt.split("timer for ")[1] # cut off instruction part (makes commands having to be precise)
            mod_prompt = mod_prompt.replace(" and ", " ") # make usable for library (ily dear mister who coded it!)

            tid = audio_name(16) # not an audio name but the timer id, who cares though
            tools.add_timer(tid, parse(mod_prompt))

            prompt = ""
            prompt_prefix = prefixes["timer"]
            prompt_data = {"_DUR": mod_prompt}

            for key, value in prompt_data.items():
                prompt_prefix = prompt_prefix.replace(key, str(value))

        # stream = ollama.chat(model="deepseek-r1:1.5b", messages=[{"role": "user", "content": prompt_prefix + prompt}], stream=True)
        # stream = ollama.chat(model="gemma3:4b-it-qat", messages=[{"role": "user", "content": prompt_prefix + prompt}], stream=True)
        
        if len(chat_history) == 0:
            chat_history.append({"role": "user", "content": prompt_prefix + prompt})
        
        stream = ollama.chat(model="gemma3:1b", messages={"role": "user", "content": prompt_prefix + prompt}, stream=True)
        # stream = ollama.chat(model="gemma3:1b", messages=chat_history, stream=True)
        buffer = ""
        combined_text = ""
        thinks = False

        # ran_str = audio_name(16)

        for chunk in stream:
            if chunk is None or "message" not in chunk or "content" not in chunk["message"]:
                print("Error: Invalid API response")
                continue

            chunk_text = chunk["message"]["content"].replace("*", "")  # Clean text
            combined_text += chunk_text
            buffer += chunk_text

            print(chunk_text, end="", flush=True)
            check_timers()

            sentences = re.split(r'(?<!\d)(?<!\d[.])(?<!\w[.])([.!?:])(?=\s|\n|$)', buffer)
            for i in range(0, len(sentences) - 1, 2):
                sentence = sentences[i] + sentences[i + 1]

                if not thinks:
                    #text_to_speech(sentence)
                    asyncio.run(tts(sentence))  # Sentence is spoken
                    #print("tts done")
                buffer = buffer[len(sentence):]
                
                if "</think>" in sentence:
                    thinks = False

        # Process remaining buffer
        if buffer.strip():
            translated_buffer = translate(buffer.strip(), flang="en", tlang="de")
            asyncio.run(tts(translated_buffer))

        chat_history.append({"role": "assistant", "content": combined_text})
        print(chat_history)
        return combined_text
    except Exception as e:
        print(f"Error in ask_and_speak: {e}")

#def text_to_speech(text):
#    text = translate(text.strip(), flang="en", tlang="de")

#    tts = gTTS(text=text, lang="de")
#    audio_buffer = io.BytesIO()
#    tts.write_to_fp(audio_buffer)
#    audio_buffer.seek(0)

#    data, samplerate = sf.read(audio_buffer, dtype="float32")
#    sd.play(data, samplerate)
#    sd.wait()

#def pyttsx3_text_to_speech(text: str):
#    engine = pyttsx3.init()
#    voices = engine.getProperty('voices')

#    for voice in voices:
#        if "de" in voice.languages:
#            engine.setProperty('voice', voice.id)
#            break

#    engine.setProperty('rate', 200)
#    engine.setProperty('volume', 1.0)

#    engine.say(text)
#    engine.runAndWait()

#def es_text_to_speech(text: str):
#    tts = ESpeakNG()
#    tts.voice = "de"
#    tts.speed = 150
#    tts.volume = 100
#    tts.say(text)

keywords = ["blueberry"]

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
                try:
                    pygame.mixer.music.stop()  # Stoppt ggf. laufende Wiedergabe
                    os.remove(file_path)
                except PermissionError:
                    print(f"Datei {file_path} wird noch verwendet, Löschen übersprungen")

porcupine = pvporcupine.create(access_key=access_key, keywords=keywords)
recoder = PvRecorder(device_index=-1, frame_length=porcupine.frame_length)

def listen_for_follow_up() -> bool:
    temp_filename = audio_name(16)
    record_old.recognize_from_mic(temp_filename)

    recognized_result = record_old.file_recognize(temp_filename)

    # return recognized_result

    if recognized_result[0]: # if new text recognized
        return (True, recognized_result[1])
    
    return (False, "")

try:
    recoder.start()

    while True:
        keyword_index = porcupine.process(recoder.read())
        check_timers()
        if keyword_index >= 0:
            play_sound("startup")
            command_file = listen_for_command()
            text = record_old.file_recognize(command_file)[1]
            play_sound("chime")

            print("Verstandener Text: " + text)
            
            en_text = translate(text=text, flang="de", tlang="en")
            ask_and_speak(en_text)

            check_files()

            lfu = listen_for_follow_up()

            while lfu[0]:
                print("\n\n")
                play_sound("chime")
                check_files()
                ask_and_speak(translate(text=lfu[1], flang="de", tlang="en"))
                lfu = listen_for_follow_up()

            print("\nKein weiteres Gespräch erkannt.")

except KeyboardInterrupt:
    recoder.stop()
finally:
    porcupine.delete()
    recoder.delete()
