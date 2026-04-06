import asyncio
import threading
import os
import time
import edge_tts
import pygame
import ssl

VOICE = "hi-IN-SwaraNeural"
BUFFER_SIZE = 1024

def remove_file(file_path):
    max_attempts = 3
    attempts = 0
    while attempts < max_attempts:
        try:
            with open(file_path, "rb") as f:
                pass
            os.remove(file_path)
            break
        except Exception as e:
            print(f"Error: {e}. Retrying... ({attempts + 1}/{max_attempts})")
            attempts += 1
            
async def generate_speech(text, file_path) -> None:
    try:
        # Skip SSL verification for edge-tts
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        communicate = edge_tts.Communicate(text, VOICE)
        await communicate.save(file_path)
        
        audio_thread = threading.Thread(target=play_audio, args=(file_path,))
        audio_thread.start()
        audio_thread.join()
    except Exception as e:
        print(f"Error generating speech: {e}")
    finally:   
        remove_file(file_path)
        

def play_audio(file_path):
    try:
        pygame.init()
        pygame.mixer.init()
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.get_ticks(10)
            pygame.quit()
    except Exception as e:
        print(f"Error playing audio: {e}")
    
def speak(text, file_path=None):
    if file_path is None:
        file_path = f"{os.getcwd()}/speak.mp3"
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(generate_speech(text, file_path))
    
speak("Hii, how are you?")