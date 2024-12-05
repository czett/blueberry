import pvporcupine, re, io, pyttsx3, wave, record, random, string, os, time, ollama, tools
from pvrecorder import PvRecorder
from deep_translator import GoogleTranslator
from gtts import gTTS
from espeakng import ESpeakNG
import scipy.io.wavfile as wav
from pytimeparse import parse
import sounddevice as sd
import soundfile as sf
import numpy as np

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
    record.recognize_from_mic(name)
    play_sound("done")
    return name
    
def save_audio(filename, audio_data, samplerate):
    """Save audio data as a WAV file."""
    # Convert to 16-bit PCM if not already
    audio_data = (audio_data * 32767).astype(np.int16)  # Scale float32 data to int16
    with wave.open(filename, 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 2 bytes for 16-bit samples
        wav_file.setframerate(samplerate)
        wav_file.writeframes(audio_data.tobytes())

def translate(text: str, flang: str, tlang: str) -> str:
    return GoogleTranslator(source=flang, target=tlang).translate(text)

def check_timers():
    if len(tools.check_timers()) > 0:
        for i in range(4):
            play_sound("timer")

def ask_and_speak(prompt: str):
    print(f"Prompt: {prompt}")
    try:
        with open("prompt_config.txt", "r") as pc:
            prompt_prefix = pc.read()

        if "weather" in prompt.lower():
            w = tools.weather()
            print(w)
            prompt = f"Formulate a short sentence with this exact information: currently the weather in Dortmund is {w[0]}°C and {w[1]}% probability of rain"
        if "timer" in prompt.lower():
            mod_prompt = prompt.lower() # for safety i guess :)
            mod_prompt = mod_prompt.replace("timer to", "timer for")
            mod_prompt = mod_prompt.split("timer for ")[1] # cut off instruction part (makes commands having to be precise)
            mod_prompt = mod_prompt.replace(" and ", " ") # make usable for library (ily dear mister who coded it!)

            tid = audio_name(16) # not an audio name but the timer id, who cares though
            tools.add_timer(tid, parse(mod_prompt))

            prompt = f"You just created a timer for me (I asked for it) for this duration: {mod_prompt}. Quickly tell me that you completed my request. E. g.: {mod_prompt}, lets go!' Or so..."

        stream = ollama.chat(model="llama3.2:1b", messages=[{"role": "user", "content": prompt_prefix + prompt}], stream=True)
        buffer = ""
        combined_text = ""
        temp_recorder = record.AudioRecorder()
        temp_recorder.start()
        print("rec started")

        ran_str = audio_name(16)

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
                text_to_speech(sentence)  # Sentence is spoken
                print("tts done")
                buffer = buffer[len(sentence):]

                # Move recording and stop recognition after TTS
                temp_audio = temp_recorder.get_audio()  # Get the recorded audio
                print("audio fetched")
                temp_audio_fn = f"audio/{ran_str}.wav"
                save_audio(temp_audio_fn, temp_audio, temp_recorder.samplerate)  # Save the audio
                print("audio saved")
                # Check for "stop" after the sentence is spoken
                temp_stt = record.file_recognize(ran_str)[1].lower()
                print("stt done")
                if "stop" in temp_stt:
                    temp_recorder.stop()
                    play_sound("done")
                    return  # End method, break out

        # Process remaining buffer
        if buffer.strip():
            translated_buffer = translate(buffer.strip(), flang="en", tlang="de")
            text_to_speech(translated_buffer)

        temp_recorder.stop()
        final_audio_fn = f"audio/{ran_str}_final.wav"
        save_audio(final_audio_fn, temp_recorder.get_audio(), temp_recorder.samplerate)

        return combined_text
    except Exception as e:
        print(f"Error in ask_and_speak: {e}")

def text_to_speech(text):
    text = translate(text.strip(), flang="en", tlang="de")

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

def listen_for_follow_up() -> bool:
    temp_filename = audio_name(16)
    record.recognize_from_mic(temp_filename)

    recognized_result = record.file_recognize(temp_filename)

    if recognized_result[0]: # if new text recognized
        return (True, recognized_result[1])
    
    return (False, "")

try:
    recoder.start()

    while True:
        keyword_index = porcupine.process(recoder.read())
        if keyword_index >= 0:
            play_sound("startup")
            command_file = listen_for_command()
            text = record.file_recognize(command_file)[1]
            play_sound("done")

            print("Verstandener Text: " + text)
            en_text = translate(text=text, flang="de", tlang="en")
            ask_and_speak(en_text)

            check_files()

            lfu = listen_for_follow_up()

            while lfu[0]:
                print("\n\n")
                play_sound("done")
                ask_and_speak(translate(text=lfu[1], flang="de", tlang="en"))
                lfu = listen_for_follow_up()

            print("\nKein weiteres Gespräch erkannt.")
            # play_sound("no_conv") # this sound is annoying ash

except KeyboardInterrupt:
    recoder.stop()
finally:
    porcupine.delete()
    recoder.delete()
