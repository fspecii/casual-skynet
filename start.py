import os
import sys
import subprocess
import platform

def check_python_and_pip():
    python_commands = ['python3', 'python', 'py']
    pip_commands = ['pip3', 'pip']

    python_command = None
    for cmd in python_commands:
        try:
            subprocess.check_call([cmd, '--version'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            python_command = cmd
            break
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue

    pip_command = None
    for cmd in pip_commands:
        try:
            subprocess.check_call([python_command, '-m', cmd, '--version'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            pip_command = cmd
            break
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue

    if not python_command:
        print("[ SKYNET ] Error: Python not found. Please install Python and add it to your PATH.")
        sys.exit(1)

    if not pip_command:
        print("[ SKYNET ] Error: pip not found. Please install pip and add it to your PATH.")
        sys.exit(1)

    return python_command, pip_command

def check_requirements():
    print("[ SKYNET ] Initializing system components...")
    python_command, pip_command = check_python_and_pip()
    with open('requirements.txt', 'r') as f:
        requirements = f.read().splitlines()
    
    for package in requirements:
        try:
            __import__(package)
        except ImportError:
            print("[ SKYNET ] Installing {0}...".format(package))
            try:
                subprocess.check_call([python_command, "-m", pip_command, "install", package])
            except subprocess.CalledProcessError:
                print("[ SKYNET ] Error: Failed to install {0}. Please install it manually.".format(package))
                sys.exit(1)
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
        print("[ SKYNET ] Error: Unsupported operating system: {0}".format(system))

def create_windows_startup():
    startup_path = os.path.join(os.getenv('APPDATA'), 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')
    bat_path = os.path.join(startup_path, 'skynet_assistant.bat')
    python_command, _ = check_python_and_pip()
    
    # Get the directory of the Python executable
    python_dir = os.path.dirname(subprocess.check_output([python_command, "-c", "import sys; print(sys.executable)"]).decode().strip())
    
    # Construct the path to pythonw.exe
    pythonw_path = os.path.join(python_dir, 'pythonw.exe')
    
    script_path = os.path.abspath('main.py')
    
    with open(bat_path, 'w') as f:
        f.write('@echo off\nstart /min "{0}" "{1}"'.format(pythonw_path, script_path))
    
    print("[ SKYNET ] Windows integration complete. Startup script created at: {0}".format(bat_path))

def create_linux_startup():
    home = os.path.expanduser('~')
    autostart_path = os.path.join(home, '.config', 'autostart')
    desktop_file = os.path.join(autostart_path, 'skynet_assistant.desktop')
    
    if not os.path.exists(autostart_path):
        os.makedirs(autostart_path)
    
    python_command, _ = check_python_and_pip()
    script_path = os.path.abspath('main.py')
    
    with open(desktop_file, 'w') as f:
        f.write("""[Desktop Entry]
Type=Application
Exec={0} {1}
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Name=SkynetAssistant
Comment=Activate Skynet AI Voice Assistant on login
""".format(python_command, script_path))
    
    print("[ SKYNET ] Linux integration complete. Startup script created at: {0}".format(desktop_file))

def create_macos_startup():
    home = os.path.expanduser('~')
    launch_agents_path = os.path.join(home, 'Library', 'LaunchAgents')
    plist_file = os.path.join(launch_agents_path, 'com.skynet.assistant.plist')
    
    if not os.path.exists(launch_agents_path):
        os.makedirs(launch_agents_path)
    
    python_command, _ = check_python_and_pip()
    script_path = os.path.abspath('main.py')
    
    with open(plist_file, 'w') as f:
        f.write("""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.skynet.assistant</string>
    <key>ProgramArguments</key>
    <array>
        <string>{0}</string>
        <string>{1}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
""".format(python_command, script_path))
    
    print("[ SKYNET ] macOS integration complete. Startup script created at: {0}".format(plist_file))

if __name__ == "__main__":
    print("[ SKYNET ] Welcome to Casual Skynet!")
    print("[ SKYNET ] Initializing Casual Skynet AI Voice Assistant...")
    check_requirements()
    create_startup_script()
    print("[ SKYNET ] System ready. Launching main program.")
    python_command, _ = check_python_and_pip()
    subprocess.run([python_command, 'main.py'])