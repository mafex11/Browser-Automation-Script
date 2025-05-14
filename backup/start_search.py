import os
import sys
import time
import platform
import subprocess
import random
import psutil

def find_existing_chrome_debugging_port():
    """Check if Chrome is already running with remote debugging enabled and get the port"""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info.get('cmdline', [])
            if cmdline and any('chrome' in cmd.lower() for cmd in cmdline):
                for cmd in cmdline:
                    if '--remote-debugging-port=' in cmd:
                        port = cmd.split('=')[1]
                        return int(port)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess, ValueError):
            pass
    return None

def start_chrome_with_debugging():
    """Start Chrome with remote debugging enabled"""
    chrome_path = None
    system = platform.system()
    
    # Find Chrome executable
    if system == "Windows":
        paths = [
            os.path.join(os.environ.get('PROGRAMFILES', 'C:\\Program Files'), 'Google\\Chrome\\Application\\chrome.exe'),
            os.path.join(os.environ.get('PROGRAMFILES(X86)', 'C:\\Program Files (x86)'), 'Google\\Chrome\\Application\\chrome.exe'),
            os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Google\\Chrome\\Application\\chrome.exe')
        ]
        for path in paths:
            if os.path.exists(path):
                chrome_path = path
                break
    elif system == "Darwin":  # macOS
        chrome_path = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
    elif system == "Linux":
        # Try common locations
        for path in ['/usr/bin/google-chrome', '/usr/bin/chrome', '/usr/bin/chromium-browser']:
            if os.path.exists(path):
                chrome_path = path
                break
    
    if not chrome_path or not os.path.exists(chrome_path):
        print("Could not find Chrome browser. Please ensure Chrome is installed.")
        return None
    
    # Use port 9222 for consistency
    debugging_port = 9222
    
    # Build command
    command = [chrome_path, f"--remote-debugging-port={debugging_port}", "--no-first-run"]
    
    # Start Chrome in background
    if system == "Windows":
        from subprocess import DEVNULL
        subprocess.Popen(command, stdout=DEVNULL, stderr=DEVNULL, shell=True)
    else:
        subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Give Chrome a moment to start
    time.sleep(3)
    
    return debugging_port

def main():
    print("Chrome Search Helper")
    print("===================")
    print("This script will help you connect to Chrome and perform a search.")
    
    # Check if Chrome with debugging is already running
    port = find_existing_chrome_debugging_port()
    
    if port:
        print(f"\nFound Chrome already running with debugging on port {port}.")
        choice = input("Do you want to connect to this Chrome instance? (y/n): ")
        if choice.lower() != 'y':
            print("\nPlease close all Chrome windows before continuing.")
            input("Press Enter when all Chrome windows are closed...")
            port = None
    
    # If Chrome with debugging is not running, start it
    if not port:
        print("\nStarting Chrome with remote debugging enabled...")
        port = start_chrome_with_debugging()
        if not port:
            print("Failed to start Chrome with debugging.")
            return
        print("Chrome started successfully with remote debugging.")
    
    # Now run the connect_to_chrome.py script
    print("\nConnecting to Chrome and preparing to search...")
    time.sleep(1)
    
    # Run the connect_to_chrome.py script
    if platform.system() == "Windows":
        os.system("python connect_to_chrome.py")
    else:
        os.system("python3 connect_to_chrome.py")
    
    print("\nThank you for using Chrome Search Helper!")

if __name__ == "__main__":
    main() 