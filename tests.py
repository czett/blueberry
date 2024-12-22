import asyncio
import edge_tts
import pygame

# All German voices
VOICES = ["de-DE-ConradNeural"]

def play_mp3_with_pygame(mp3_file):
    mp3_file = f"tests/{mp3_file}.mp3"
    pygame.mixer.init()
    pygame.mixer.music.load(mp3_file)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)

async def tts(text) -> None:
    OUTPUT_FILE = "german_tts.mp3"
    for voice in VOICES:
        print(f"Using voice: {voice}")
        communicator = edge_tts.Communicate(text, voice)
        await communicator.save(f"tests/{voice}.mp3")
    play_mp3_with_pygame(voice)

asyncio.run(tts("hewwo"))
