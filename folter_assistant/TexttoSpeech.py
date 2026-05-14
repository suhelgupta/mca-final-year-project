import pyttsx3
import pyautogui as pag
import os
import tkinter as tk
from tkinter import filedialog
import PyPDF2

def read_pdf(file):
    text = ""
    try:
        with open(file, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text() + "\n"
    except Exception as e:
        print(f"Error reading PDF: {e}")
    return text

    

# voc = pag.prompt("Enter the Rate of the Speech bewwten 0 to 300","Speech RATE")

# r = int(L[0])
def Speak(text,r,v):
    # global r,voc
    engine = pyttsx3.init() # object creation
    # try:
    # except Exception as e:
    #     print("Python Module pyttsx3 problem")
        # input("Press Enter Key")
        # exit()
    """ RATE"""
    rate = engine.getProperty('rate')   # getting details of current speaking rate
    engine.setProperty('rate', int(r))     # setting up new voice rate


    """VOLUME"""
    volume = engine.getProperty('volume')   #getting to know current volume level (min=0 and max=1)
    engine.setProperty('volume',1.0)    # setting up volume level  between 0 and 1

    """VOICE"""
    voices = engine.getProperty('voices')       #getting details of current voice
    engine.setProperty('voice', voices[int(v)].id)   #changing index, changes voices. 1 for female

    engine.say(text)
    engine.runAndWait()
    engine.stop()

def writefile(L):
    for i in range(len(L)):
        L[i] = L[i] + "\n" 
    with open("set.txt","w") as f:
        f.writelines(L)

def readfile():
    if not os.path.exists("set.txt"):
        with open("set.txt", "w") as f:
            f.write("150\n1")  # Default rate and voice index
    with open("set.txt", "r") as f:
        return f.read().splitlines()

def start():
    while 1:
        with open("set.txt") as f:
            L = f.readlines()
        for i in range(len(L)):
            L[i] = L[i].replace("\n","")
        print(L)
        r , v = L[0] , L[1]
        while 1:
            Choose  = pag.confirm(text='Please Select Any One', title='Text to Speech Conveter', buttons=['Set Speak Rate', 'Change Voice' ,"Convert Text to speech","Exit"])
            if  Choose == 'Set Speak Rate':
                while 1:
                    r = pag.prompt("Enter the Rate of the Speech bewwten 0 to 300","Speech RATE")
                    if r.isdigit():
                        L[0] = r
                        break
                    else:
                        pag.alert(text = "Entered wrong input try again", title = "Wrong input")
                        continue
                break

            
            if Choose == 'Change Voice':
                voc = pag.confirm(text="Select the Voice.", title="Voice", buttons = ['MALE','FEMALE'])
                if voc == 'MALE':
                    L[1] = "0"
                    print(L)
                if voc == 'FEMALE':
                    L[1] = "1"
                    print(L)
                break

            if Choose == "Convert Text to speech":
                ConvtText(r,v)
                break

            if Choose == "Exit":
                exit()
        writefile(L)
        continue
    # for i in range(len(L)):
    #     L[i] = L[i] + "\n" 
    # with open("set.txt","w") as f:
    #     f.writelines(L)
    # main()
    
def ConvtText(r, v):
    select = pag.confirm(text="Select any One", title="Select", buttons=["Type Text", "Select Txt/PDF file"])
    if select == "Type Text":
        get = pag.prompt(text="Type Your Text", title="TYPE")
        Speak(get, r, v)
    if select == "Select Txt/PDF file":
        root = tk.Tk()
        root.withdraw()
        file = filedialog.askopenfilename()
        try:
            if file.endswith(".pdf"):
                read = read_pdf(file)
            else:
                with open(file, "r", encoding="utf-8") as f:
                    read = f.read()
            Speak(read, r, v)
        except Exception as e:
            print(f"\n\nUnable to open file: {e}")
            input("\n\nPress Enter key to Try Again")
            ConvtText(r, v)

            
            
def main():
    start()
    

if __name__ == "__main__":
    try:
        if not os.path.exists("set.txt"):
            with open("set.txt","w") as f:
                f.write("200\n1")
    except:
        pass
    main()
# a = pag.prompt("Enter the Rate of the Speech bewwten 0 to 300","Speech RATE")
# voc = "1"
# s = f""" {a} Gupta """
# Speak(s, 200, voc)

