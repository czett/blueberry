import pvporcupine
from pvrecorder import PvRecorder
import record
import random
import string
import os
import time

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

try:
    recoder.start()

    while True:
        keyword_index = porcupine.process(recoder.read())
        if keyword_index >= 0:
            check_files()
            print(f"{keywords[keyword_index]} hört zu!")

            name = audio_name(16)
            record.recognize_from_mic(name)
            
            text = record.file_recognize(name)
            print(text)

except KeyboardInterrupt:
    recoder.stop()
finally:
    porcupine.delete()
    recoder.delete()
