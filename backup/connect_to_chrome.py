import os
import sys
import time
import platform
import random
import psutil
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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

def human_like_typing(element, text):
    """Type text with random delays like a human would"""
    for char in text:
        element.send_keys(char)
        # Random delay between keystrokes (50-150ms)
        time.sleep(random.uniform(0.05, 0.15))

def connect_to_chrome_and_search():
    # Set up ChromeDriver service
    current_dir = os.path.dirname(os.path.abspath(__file__))
    chromedriver_name = "chromedriver.exe" if platform.system() == "Windows" else "chromedriver"
    chromedriver_path = os.path.join(current_dir, chromedriver_name)
    
    if not os.path.exists(chromedriver_path):
        print(f"ChromeDriver not found at {chromedriver_path}. Please run download_chromedriver.py first.")
        return False
    
    # Check if Chrome is running with debugging
    debugging_port = find_existing_chrome_debugging_port()
    
    # If Chrome is not running with debugging, show instructions
    if not debugging_port:
        print("\nERROR: Chrome is not running with remote debugging enabled.")
        print("\nTo use this script, you must first:")
        print("1. Close all Chrome windows")
        print("2. Start Chrome with the remote debugging flag:")
        print("   chrome.exe --remote-debugging-port=9222")
        print("\nThen run this script again.")
        return False
    
    print(f"\nConnecting to Chrome on debugging port: {debugging_port}")
    
    # Set up the WebDriver options to connect to the existing Chrome
    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", f"127.0.0.1:{debugging_port}")
    
    # Initialize the WebDriver
    service = Service(executable_path=chromedriver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        # Get the current tabs
        current_tabs = driver.window_handles
        
        # Create a new tab
        driver.execute_script("window.open('about:blank', '_blank');")
        
        # Wait for the new tab to open
        time.sleep(1)
        
        # Get updated tabs
        new_tabs = driver.window_handles
        
        # Find the new tab (the tab that's in new_tabs but not in current_tabs)
        new_tab = list(set(new_tabs) - set(current_tabs))
        if new_tab:
            # Switch to the new tab
            driver.switch_to.window(new_tab[0])
            print("Created a new tab in your existing Chrome browser.")
        else:
            print("Created a new tab but couldn't identify it. Using the last tab.")
            driver.switch_to.window(driver.window_handles[-1])
        
        # Get search query from user
        search_query = input("\nEnter your search query: ")
        
        # Navigate to Google
        driver.get("https://www.google.com")
        time.sleep(1.5)
        
        # Find and interact with the search box
        try:
            wait = WebDriverWait(driver, 10)
            search_box = wait.until(EC.element_to_be_clickable((By.NAME, "q")))
            
            # Type the query with human-like typing
            human_like_typing(search_box, search_query)
            
            # Submit the search
            time.sleep(0.5)
            search_box.send_keys(Keys.RETURN)
            
            print(f"Searched for: {search_query}")
            
            # Wait for results to load
            wait.until(EC.presence_of_element_located((By.ID, "search")))
            
            # Keep the browser open
            print("\nSearch completed! The browser tab will remain open.")
            print("You can continue using it manually.")
            
            # Don't close the WebDriver so the tab stays open
            input("\nPress Enter to close the WebDriver connection (this will NOT close your Chrome browser)...")
            
            return True
            
        except Exception as e:
            print(f"Error during search: {e}")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        # Close the WebDriver but keep Chrome running
        driver.quit()
        return False
    finally:
        # This doesn't close Chrome, just the WebDriver connection
        driver.quit()
        print("WebDriver connection closed. Your Chrome browser remains open.")

if __name__ == "__main__":
    print("Chrome Tab Connector - Creates a new tab in your existing Chrome browser")
    print("=======================================================================")
    
    if connect_to_chrome_and_search():
        print("\nSuccessfully connected to Chrome and performed search.")
    else:
        print("\nFailed to connect to Chrome or perform search.") 