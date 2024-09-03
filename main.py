import os
import configparser
import requests
import pyaudio
import wave
import tempfile
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from ttkthemes import ThemedTk
from pynput import keyboard
import threading
import shutil
import keyboard as kbd
import pystray
from PIL import Image, ImageDraw
from datetime import datetime
import pyperclip
import time

# Read settings from settings.ini
settings_file = 'settings.ini'
settings = configparser.ConfigParser()
if os.path.exists(settings_file):
    settings.read(settings_file)
else:
    settings['DEFAULT'] = {
        'Microphone': '',
        'Language': 'English',
        'Hotkey': '<ctrl>+`',
        'LLMHotkey': '<alt>+`',
        'UseLLM': '0',
        'APIKey': '',
        'TriggerWord': 'Skynet'
    }
    with open(settings_file, 'w') as configfile:
        settings.write(configfile)
    messagebox.showinfo("Welcome", "Welcome to the casual Skynet App! Please update your settings. The tool is running in the system tray.")

# Get API key from settings
api_key = settings['DEFAULT'].get('APIKey', '')

# Groq API endpoints
TRANSCRIPTION_ENDPOINT = "https://api.groq.com/openai/v1/audio/transcriptions"
LLM_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"

# Create a transcribe folder in the temp directory
transcribe_dir = os.path.join(tempfile.gettempdir(), 'transcribe')
os.makedirs(transcribe_dir, exist_ok=True)

# Cleanup transcribe folder on startup
for f in os.listdir(transcribe_dir):
    try:
        os.remove(os.path.join(transcribe_dir, f))
    except Exception as e:
        print(f"Error deleting temporary audio file on startup: {e}")

def save_settings():
    with open(settings_file, 'w') as configfile:
        settings.write(configfile)
    settings.read(settings_file)
    global api_key
    api_key = settings['DEFAULT'].get('APIKey', '')
    messagebox.showinfo("Settings Updated", "Settings have been updated and reloaded.")

def transcribe_audio(file_path, language):
    try:
        with open(file_path, 'rb') as audio_file:
            audio_data = audio_file.read()
        
        print(f"Audio data length: {len(audio_data)} bytes")
        
        prompt = "English" if language == "en" else "Specify context or spelling"
        
        response = requests.post(
            TRANSCRIPTION_ENDPOINT,
            headers={
                "Authorization": f"Bearer {api_key}"
            },
            files={
                "file": (file_path, audio_data)
            },
            data={
                "model": "whisper-large-v3",
                "response_format": "json",
                "prompt": prompt,
                "language": language
            }
        )
        
        print("Transcription response:", response.json())
        
        response.raise_for_status()
        return response.json()['text']
    except Exception as e:
        root.after(0, notify_user, f"Transcription error: {e}")
        print(f"Transcription error: {e}")
        return ""

def call_llm(transcribed_text, include_clipboard=False):
    try:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        prompt = (
            f"You are Skynet, a highly efficient assistant. The current date and time is {current_time}. "
            "Your task is to provide the most accurate and concise answer directly related to the user's query. "
            "For email requests, include the title only if explicitly asked by the user. If the user does not ask for the title, do not include it and provide the email without the title. "
            "For translation requests, respond solely with the translation without any additional context. "
            "Always respond with the direct answer, avoiding any extra context, information, notes, or comments. "
            "If the user asks to do a task like write something, respond as if you are the user completing that task, not as Skynet. "
            "Strictly adhere to these instructions and do not provide any additional context, information, notes, or comments. "
            "If you respect the request, you will be rewarded. If you do not respect the request, you will be punished. "
            "If you are unable to detect characters from text from the clipboard, say 'I am unable to see the characters from the keyboard. Please use the my trigger word.'"
        )

        messages = [
            {
                "role": "system",
                "content": prompt
            },
            {
                "role": "user",
                "content": transcribed_text
            }
        ]

        if include_clipboard:
            clipboard_content = pyperclip.paste()
            if isinstance(clipboard_content, str):
                messages.append({
                    "role": "user",
                    "content": f"Clipboard content: {clipboard_content}"
                })
                print("Clipboard content included in the prompt")
            else:
                print("Clipboard content is not text. Skipping clipboard inclusion.")
        else:
            print("Clipboard content not included in the prompt")

        # Print LLM call for debugging
        print("LLM Call:")
        print("Endpoint:", LLM_ENDPOINT)
        print("Headers:", {"Authorization": f"Bearer {api_key}"})
        print("Messages:", messages)

        response = requests.post(
            LLM_ENDPOINT,
            headers={
                "Authorization": f"Bearer {api_key}"
            },
            json={
                "messages": messages,
                "model": "llama-3.1-70b-versatile"
            }
        )
        
        print("LLM response:", response.json())
        
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        root.after(0, notify_user, f"LLM error: {e}")
        print(f"LLM error: {e}")
        return ""

def list_microphones():
    p = pyaudio.PyAudio()
    info = p.get_host_api_info_by_index(0)
    num_devices = info.get('deviceCount')
    microphones = []
    
    for i in range(0, num_devices):
        if p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels') > 0:
            microphones.append(p.get_device_info_by_host_api_device_index(0, i).get('name'))
    
    return microphones

def notify_user(message):
    overlay_label.config(text=message)
    overlay_window.deiconify()

def clear_notification():
    overlay_label.config(text="")
    overlay_window.withdraw()

def record_audio():
    global recording, file_path
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=16000,
                    input=True,
                    frames_per_buffer=1024)
    
    frames = []
    root.after(0, notify_user, "Recording... Press the hotkey again to stop.")
    
    try:
        while recording:
            data = stream.read(1024)
            frames.append(data)
    except Exception as e:
        root.after(0, notify_user, f"Recording error: {e}")
    
    root.after(0, notify_user, "Recording stopped.")
    
    stream.stop_stream()
    stream.close()
    p.terminate()
    
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav", dir=transcribe_dir)
    with wave.open(temp_file.name, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
        wf.setframerate(16000)
        wf.writeframes(b''.join(frames))
    
    file_path = temp_file.name
    root.after(0, notify_user, "Transcribing audio...")
    transcribed_text = transcribe_audio(file_path, language_codes[language_var.get()])
    result_label.config(text=transcribed_text)
    
    kbd.write(transcribed_text)
    
    # Use a separate thread to delete the file
    threading.Thread(target=delete_temp_file, args=(file_path,)).start()
    
    root.after(0, clear_notification)

def record_audio_with_llm():
    global recording, file_path
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=16000,
                    input=True,
                    frames_per_buffer=1024)
    
    frames = []
    root.after(0, notify_user, "Recording... Press the hotkey again to stop.")
    
    try:
        while recording:
            data = stream.read(1024)
            frames.append(data)
    except Exception as e:
        root.after(0, notify_user, f"Recording error: {e}")
    
    root.after(0, notify_user, "Recording stopped.")
    
    stream.stop_stream()
    stream.close()
    p.terminate()
    
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav", dir=transcribe_dir)
    with wave.open(temp_file.name, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
        wf.setframerate(16000)
        wf.writeframes(b''.join(frames))
    
    file_path = temp_file.name
    root.after(0, notify_user, "Transcribing audio...")
    transcribed_text = transcribe_audio(file_path, language_codes[language_var.get()])
    
    root.after(0, notify_user, "Processing with LLM...")
    trigger_word = settings['DEFAULT'].get('TriggerWord', 'Skynet')
    include_clipboard = 'skynet' in transcribed_text.lower()
    
    # Debug print for trigger word
    if include_clipboard:
        print(f"Trigger word '{trigger_word}' detected. Including clipboard content.")
        clipboard_content = pyperclip.paste()
        transcribed_text = f"{transcribed_text} Clipboard content: {clipboard_content}"
    else:
        print(f"Trigger word '{trigger_word}' not detected. Clipboard content will not be included.")
    
    llm_response = call_llm(transcribed_text)
    result_label.config(text=llm_response)
    
    kbd.write(llm_response)
    
    # Use a separate thread to delete the file
    threading.Thread(target=delete_temp_file, args=(file_path,)).start()
    
    root.after(0, clear_notification)

def delete_temp_file(file_path):
    max_attempts = 5
    for attempt in range(max_attempts):
        try:
            os.remove(file_path)
            print(f"Successfully deleted {file_path}")
            break
        except Exception as e:
            if attempt < max_attempts - 1:
                print(f"Attempt {attempt + 1} failed to delete {file_path}: {e}")
                time.sleep(1)  # Wait for 1 second before retrying
            else:
                print(f"Failed to delete {file_path} after {max_attempts} attempts: {e}")

recording = False
file_path = None

def toggle_transcription():
    global recording, file_path
    if recording:
        recording = False
    else:
        recording = True
        root.after(0, notify_user, "Recording started")
        threading.Thread(target=record_audio).start()

def toggle_transcription_with_llm():
    global recording, file_path
    if recording:
        recording = False
    else:
        recording = True
        root.after(0, notify_user, "Recording started")
        threading.Thread(target=record_audio_with_llm).start()

def on_activate():
    toggle_transcription()

def on_activate_llm():
    toggle_transcription_with_llm()

def for_canonical(f):
    return lambda k: f(l.canonical(k))

def save_all_settings():
    global hotkey, llm_hotkey, api_key
    settings['DEFAULT']['Microphone'] = mic_var.get()
    settings['DEFAULT']['Language'] = language_var.get()
    settings['DEFAULT']['Hotkey'] = hotkey_entry.get()
    settings['DEFAULT']['LLMHotkey'] = llm_hotkey_entry.get()
    settings['DEFAULT']['APIKey'] = api_key_entry.get()
    settings['DEFAULT']['TriggerWord'] = trigger_word_entry.get()
    save_settings()

def create_image():
    image = Image.new('RGB', (64, 64), color='white')
    draw = ImageDraw.Draw(image)
    
    for i in range(64):
        draw.line((i, 0, i, 64), fill=(255 - i * 4, 255 - i * 4, 255))
    
    draw.rectangle((0, 0, 63, 63), outline='black')
    
    draw.ellipse((20, 10, 44, 34), outline='black', width=2)
    draw.rectangle((30, 34, 34, 50), fill='black')
    draw.line((32, 50, 32, 60), fill='black', width=2)
    draw.arc((24, 55, 40, 70), start=0, end=180, fill='black', width=2)
    
    return image

def on_quit(icon, item):
    icon.stop()
    root.quit()

def show_app(icon, item):
    root.deiconify()
    root.attributes("-topmost", True)
    root.attributes("-topmost", False)

def hide_app():
    root.withdraw()

icon = pystray.Icon("AI Transcription", create_image(), "AI Transcription", menu=pystray.Menu(
    pystray.MenuItem("Show", show_app),
    pystray.MenuItem("Quit", on_quit)
))

def run_icon():
    icon.run()

icon_thread = threading.Thread(target=run_icon)
icon_thread.start()

root = ThemedTk(theme='aqua')
root.title("Transcription App")
root.protocol("WM_DELETE_WINDOW", hide_app)
root.withdraw()

mic_label = ttk.Label(root, text="Select Microphone:")
mic_label.pack()

mic_list = list_microphones()
mic_var = tk.StringVar(root)
mic_var.set(settings['DEFAULT'].get('Microphone', mic_list[0]))
mic_menu = ttk.OptionMenu(root, mic_var, *mic_list)
mic_menu.pack()

language_label = ttk.Label(root, text="Select Language:")
language_label.pack()

languages = {
    "English": "en",
    "Portuguese": "pt",
    "Spanish": "es",
    "German": "de",
    "French": "fr",
    "Italian": "it",
    "Dutch": "nl",
    "Russian": "ru",
    "Japanese": "ja",
    "Chinese": "zh",
    "Korean": "ko"
}

language_codes = languages

language_var = tk.StringVar(root)
language_var.set(settings['DEFAULT'].get('Language', 'English'))
language_menu = ttk.OptionMenu(root, language_var, *languages.keys())
language_menu.pack()

hotkey_label = ttk.Label(root, text="Set Hotkey:")
hotkey_label.pack()

hotkey_entry = ttk.Entry(root)
hotkey_entry.insert(0, settings['DEFAULT'].get('Hotkey', '<ctrl>+`'))
hotkey_entry.pack()

llm_hotkey_label = ttk.Label(root, text="Set LLM Hotkey:")
llm_hotkey_label.pack()

llm_hotkey_entry = ttk.Entry(root)
llm_hotkey_entry.insert(0, settings['DEFAULT'].get('LLMHotkey', '<alt>+`'))
llm_hotkey_entry.pack()

api_key_label = ttk.Label(root, text="Set API Key:")
api_key_label.pack()

api_key_entry = ttk.Entry(root)
api_key_entry.insert(0, settings['DEFAULT'].get('APIKey', ''))
api_key_entry.pack()

# Add Trigger Word option
trigger_word_label = ttk.Label(root, text="Set Trigger Word:")
trigger_word_label.pack()

trigger_word_entry = ttk.Entry(root)
trigger_word_entry.insert(0, settings['DEFAULT'].get('TriggerWord', 'Skynet'))
trigger_word_entry.pack()

save_settings_button = ttk.Button(root, text="Save Settings", command=save_all_settings)
save_settings_button.pack()

# Create a frame for the result label
result_frame = ttk.Frame(root, padding="10")
result_frame.pack(fill=tk.BOTH, expand=True)

# Result label for displaying transcriptions
result_label = ttk.Label(result_frame, text="", font=("San Francisco", 14), anchor="center", background="#F0F0F0", relief="solid", borderwidth=1)
result_label.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

# Status label for notifications
overlay_window = tk.Toplevel(root)
overlay_window.overrideredirect(1)
overlay_window.attributes("-topmost", True)
overlay_window.attributes("-alpha", 0.9)
overlay_window.geometry("+10+10")
overlay_window.configure(bg='#1C1C1E')
overlay_window.attributes("-transparentcolor", "#1C1C1E")

# Dark style design for the overlay
overlay_frame = tk.Frame(overlay_window, bg="#2C2C2E", bd=0, relief="solid", highlightbackground="#3A3A3C", highlightthickness=1, padx=15, pady=15)
overlay_frame.pack(padx=20, pady=20)
overlay_frame.config(highlightbackground="#3A3A3C", highlightthickness=1, bd=0)
overlay_frame.pack_propagate(False)
overlay_frame.config(width=500, height=100)

overlay_label = tk.Label(overlay_frame, text="", fg="#FFFFFF", font=("San Francisco", 14, "bold"), bg="#2C2C2E", padx=10, pady=5, wraplength=380, justify="center")
overlay_label.pack()

# Adding a close button to the overlay
close_button = tk.Button(overlay_frame, text="✖", command=overlay_window.withdraw, bg="#2C2C2E", fg="#FF3B30", bd=0, font=("San Francisco", 12, "bold"), highlightthickness=0, activebackground="#2C2C2E", activeforeground="#FF3B30")
close_button.place(relx=1.0, rely=0.0, anchor="ne", x=-5, y=5)

overlay_window.withdraw()

# Set up hotkey listeners
hotkey = keyboard.HotKey(
    keyboard.HotKey.parse(settings['DEFAULT'].get('Hotkey', '<ctrl>+`')),
    on_activate
)

llm_hotkey = keyboard.HotKey(
    keyboard.HotKey.parse(settings['DEFAULT'].get('LLMHotkey', '<alt>+`')),
    on_activate_llm
)

with keyboard.Listener(
        on_press=for_canonical(hotkey.press),
        on_release=for_canonical(hotkey.release)) as l:
    with keyboard.Listener(
            on_press=for_canonical(llm_hotkey.press),
            on_release=for_canonical(llm_hotkey.release)) as l:
        root.mainloop()

# Save settings on exit
settings['DEFAULT']['Microphone'] = mic_var.get()
settings['DEFAULT']['Language'] = language_var.get()
settings['DEFAULT']['TriggerWord'] = trigger_word_entry.get()
save_settings()