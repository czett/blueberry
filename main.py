import pvporcupine, re, io, pyttsx3, record, random, string, os, time, ollama
from pvrecorder import PvRecorder
from gtts import gTTS
from espeakng import ESpeakNG
import translators as ts
import sounddevice as sd
import soundfile as sf

def play_sound(fn:str):
    file_path = f"assets/{fn}.mp3"
    data, samplerate = sf.read(file_path)
    sd.play(data, samplerate)
    sd.wait()

def listen_for_command():
    name = audio_name(16)
    record.recognize_from_mic(name)
    return name
    
def translate(text:str, flang:str, tlang:str):
    return ts.translate_text(text, to_language=tlang, from_language=flang)

def ask_and_speak(prompt: str):
    try:
        stream = ollama.chat(model="llama3.2:1b", messages=[{"role": "user", "content": prompt}], stream=True)
        buffer = ""
        combined_text = ""

        for chunk in stream:
            chunk_text = chunk["message"]["content"]
            chunk_text = chunk_text.replace("*", "")  # Entferne alle * aus der Ausgabe
            combined_text += chunk_text
            buffer += chunk_text

            print(chunk_text, end="", flush=True)

            # Split at proper sentence endings including ":"
            sentences = re.split(r'(?<!\d)(?<!\d[.])(?<!\w[.])([.!?:])(?=\s|\n|$)', buffer)

            # Reconstruct and process sentences
            temp_buffer = ""
            for i in range(0, len(sentences) - 1, 2):
                temp_buffer = sentences[i] + sentences[i + 1]

                # Übersetze den Text ins Deutsche und sprich ihn aus
                translated_sentence = translate(temp_buffer.strip(), flang="en", tlang="de")
                text_to_speech(translated_sentence)

                buffer = buffer[len(temp_buffer):]

        # Process any remaining buffer
        if buffer.strip():
            translated_buffer = translate(buffer.strip(), flang="en", tlang="de")
            text_to_speech(translated_buffer)

        return combined_text
    except Exception as e:
        print(f"Error in ask_and_speak: {e}")

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
        if keyword_index >= 0:
            play_sound("startup")
            command_file = listen_for_command()
            text = record.file_recognize(command_file)[1]
            play_sound("done")
            print("Verstandener Text: " + text)
            en_text = translate(text=text, flang="de", tlang="en")
            ask_and_speak(en_text)
            check_files()

            lfu = listen_for_follow_up(duration=10)

            while lfu[0]:
                print("\n\n")
                play_sound("done")
                ask_and_speak(translate(text=lfu[1], flang="de", tlang="en"))
                lfu = listen_for_follow_up(duration=10)

            print("Kein weiteres Gespräch erkannt.")

except KeyboardInterrupt:
    recoder.stop()
finally:
    porcupine.delete()
    recoder.delete()
