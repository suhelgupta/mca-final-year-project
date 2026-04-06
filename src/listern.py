import speech_recognition as sr
import os
import threading
# from mtranslate import translate
from colorama import Fore, Style,init 

init(autoreset=True) #Automatically reset Style After Each print

def print_loop():
    while True:
        print(Fore.LIGHTGREEN_EX + "I am listening... (Press Ctrl+C to stop)", end="", flush=True)
        print(Style.RESET_ALL, end="", flush=True)
        
# def Trans_hindi_to_english(txt):
#     english_txt = translate(txt, to_language: "en-in")
#     return english_txt

def listen():
    recognizer = sr.Recognizer()
    # recognizer.dynamic_energy_threshold = False
    # recognizer.energy_threshold = 350
    # recognizer.dynamic_energy_adjustment_damping = 0.03
    # recognizer.dynamic_energy_adjustment_ratio = 1.9
    recognizer.pause_threshold = 0.4
    recognizer.operation_timeout = None
    recognizer.non_speaking_duration = 0.3
    with sr.Microphone() as source:
        print(Fore.LIGHTGREEN_EX + "I am listening... (Press Ctrl+C to stop)", end="", flush=True)
        while True:
            try:
                audio = recognizer.listen(source, timeout=None)
                print("\r"+ Fore.LIGHTGREEN_EX + "Processing...", end="", flush=True)
                text = recognizer.recognize_google(audio, language="en-IN").lower()
                if text:
                    print("\r" + Fore.LIGHTGREEN_EX + "You said: " + text, end="", flush=True)
                    
                    return text
                else:
                    return ""
            except sr.UnknownValueError:
                print("\r" + Fore.RED + "Sorry, I could not understand the audio. Please try again.", end="", flush=True)
            except sr.RequestError as e:
                print("\r" + Fore.RED + "Could not request results from the speech recognition service; {0}".format(e), end="", flush=True)
            except KeyboardInterrupt:
                print("\n" + Fore.YELLOW + "Listening stopped by user.")
                break
            finally:                
                print("\r", end="", flush=True)
            
            os.system('cls' if os.name == 'nt' else 'clear')
            #threading.Thread(target=print_loop).start()
            listen_thread = threading.Thread(target=listen)
            print_thread = threading.Thread(target=print_loop)
            listen_thread.start()
            print_thread.start()
            listen_thread.join()
            print_thread.join()
            

listen()