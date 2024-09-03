import os
import sys
import subprocess
import platform

def check_requirements():
    print("[ SKYNET ] Initializing system components...")
    with open('requirements.txt', 'r') as f:
        requirements = f.read().splitlines()
    
    for package in requirements:
        try:
            __import__(package)
        except ImportError:
            print(f"[ SKYNET ] Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    print("[ SKYNET ] All components initialized successfully.")

def create_startup_script():
    print("[ SKYNET ] Configuring system integration...")
    system = platform.system()
    if system == "Windows":
        create_windows_startup()
    elif system == "Linux":
        create_linux_startup()
    elif system == "Darwin":  # macOS
        create_macos_startup()
    else:
        print(f"[ SKYNET ] Error: Unsupported operating system: {system}")

def create_windows_startup():
    startup_path = os.path.join(os.getenv('APPDATA'), 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')
    bat_path = os.path.join(startup_path, 'skynet_assistant.bat')
    python_path = sys.executable
    script_path = os.path.abspath('main.py')
    
    with open(bat_path, 'w') as f:
        f.write(f'@echo off\nstart /min "{python_path}" "{script_path}"')
    
    print(f"[ SKYNET ] Windows integration complete. Startup script created at: {bat_path}")

def create_linux_startup():
    home = os.path.expanduser('~')
    autostart_path = os.path.join(home, '.config', 'autostart')
    desktop_file = os.path.join(autostart_path, 'skynet_assistant.desktop')
    
    if not os.path.exists(autostart_path):
        os.makedirs(autostart_path)
    
    script_path = os.path.abspath('main.py')
    
    with open(desktop_file, 'w') as f:
        f.write(f"""[Desktop Entry]
Type=Application
Exec={sys.executable} {script_path}
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Name=SkynetAssistant
Comment=Activate Skynet AI Voice Assistant on login
""")
    
    print(f"[ SKYNET ] Linux integration complete. Startup script created at: {desktop_file}")

def create_macos_startup():
    home = os.path.expanduser('~')
    launch_agents_path = os.path.join(home, 'Library', 'LaunchAgents')
    plist_file = os.path.join(launch_agents_path, 'com.skynet.assistant.plist')
    
    if not os.path.exists(launch_agents_path):
        os.makedirs(launch_agents_path)
    
    script_path = os.path.abspath('main.py')
    
    with open(plist_file, 'w') as f:
        f.write(f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.skynet.assistant</string>
    <key>ProgramArguments</key>
    <array>
        <string>{sys.executable}</string>
        <string>{script_path}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
""")
    
    print(f"[ SKYNET ] macOS integration complete. Startup script created at: {plist_file}")

if __name__ == "__main__":
    print("[ SKYNET ] Welcome to Casual Skynet!")
    print("[ SKYNET ] Initializing Casual Skynet AI Voice Assistant...")
    check_requirements()
    create_startup_script()
    print("[ SKYNET ] System ready. Launching main program.")
    subprocess.run([sys.executable, 'main.py'])