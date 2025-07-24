import sounddevice as sd
import numpy as np
import wave
import webrtcvad
from vosk import Model, KaldiRecognizer
import json
import collections

model = Model("models/de/vosk-model-small-de-0.15")

class VADAudio:
    def __init__(self, aggressiveness=3, samplerate=16000, frame_duration=30):
        self.vad = webrtcvad.Vad(aggressiveness)
        self.samplerate = samplerate
        self.frame_duration = frame_duration  # ms
        self.frame_size = int(samplerate * frame_duration / 1000)  # samples per frame
        self.buffer = collections.deque(maxlen=10)
        self.recording = False
        self.frames = []

    def frame_generator(self, indata):
        # indata is float32 numpy array, convert to int16 bytes for VAD
        pcm_data = (indata * 32767).astype(np.int16).tobytes()
        return pcm_data

    def process_audio(self, indata, frames, time, status):
        pcm = self.frame_generator(indata[:, 0])
        is_speech = self.vad.is_speech(pcm, self.samplerate)
        self.buffer.append(is_speech)

        if not self.recording and any(self.buffer):
            self.recording = True
            print("Start recording...")
        
        if self.recording:
            self.frames.append(pcm)
            # Stop recording if silence detected for ~300ms (10 frames * 30ms)
            if not any(self.buffer):
                print("Silence detected, stop recording.")
                raise sd.CallbackStop()

def recognize_from_mic(fn: str):
    vad_audio = VADAudio()

    with sd.InputStream(samplerate=vad_audio.samplerate, channels=1, dtype='float32',
                        blocksize=vad_audio.frame_size, callback=vad_audio.process_audio):
        print("Listening for speech...")
        try:
            sd.sleep(10000)  # max 10 sec recording
        except sd.CallbackStop:
            pass

    # Save recording to WAV
    audio_data = b''.join(vad_audio.frames)
    filepath = f"audio/{fn}.wav"
    with wave.open(filepath, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(vad_audio.samplerate)
        wf.writeframes(audio_data)

    return file_recognize(fn)

def file_recognize(fn: str):
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
    else:
        return (False, "")
