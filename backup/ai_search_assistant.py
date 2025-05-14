import time
import re
import os
import sys
import platform
import random
import argparse
import subprocess
import psutil
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import requests
import json

class AISearchAssistant:
    def __init__(self, use_profile=False, use_default_profile=False, reuse_chrome=True, force_new_chrome=False):
        # Ensure ChromeDriver is available and compatible
        self.check_and_setup_chromedriver()
        
        # Check if we can reuse a running Chrome instance
        self.debugging_port = None
        self.chrome_process_started = False
        
        # Set up Chrome options
        self.chrome_options = Options()
        # Uncomment the line below if you want to run in headless mode
        # self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--start-maximized')
        
        # Set flag to track if we're using default profile
        self.using_default_profile = False
        
        # Determine the user data directory to use
        user_data_dir = None
        
        # Handle profile options - with priority for default profile if both are specified
        if use_default_profile:
            # Use the default Chrome profile from the user's system
            system = platform.system()
            if system == "Windows":
                default_profile_path = os.path.join(os.path.expanduser('~'), 
                    'AppData', 'Local', 'Google', 'Chrome', 'User Data')
            elif system == "Darwin":  # macOS
                default_profile_path = os.path.join(os.path.expanduser('~'), 
                    'Library', 'Application Support', 'Google', 'Chrome')
            elif system == "Linux":
                default_profile_path = os.path.join(os.path.expanduser('~'), 
                    '.config', 'google-chrome')
            else:
                print(f"Unsupported platform: {system}. Using custom profile instead.")
                default_profile_path = None
                
            if default_profile_path and os.path.exists(default_profile_path):
                print(f"Using default Chrome profile at: {default_profile_path}")
                user_data_dir = default_profile_path
                self.using_default_profile = True
            else:
                print("Default Chrome profile not found. Using custom profile instead.")
                use_profile = True
        
        # Create a custom profile directory if requested and not using default profile
        if use_profile and not use_default_profile:
            profile_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chrome-profile")
            if not os.path.exists(profile_dir):
                os.makedirs(profile_dir)
            print(f"Using Chrome profile directory: {profile_dir}")
            user_data_dir = profile_dir
        
        # Check if we should try to reuse Chrome
        if reuse_chrome and not force_new_chrome:
            # First, try to connect to an existing Chrome instance with debugging enabled
            port, options = attach_to_existing_chrome()
            if port:
                print("Connecting to existing Chrome browser with remote debugging...")
                self.debugging_port = port
                self.chrome_options = options
            elif is_chrome_running():
                # Chrome is running but without debugging
                if user_data_dir and self.using_default_profile:
                    print("Chrome is already running. Using the profile directly.")
                    # Just use the profile directly, even if Chrome is running
                    self.chrome_options.add_argument(f'--user-data-dir={user_data_dir}')
                    if use_default_profile:
                        self.chrome_options.add_argument('--profile-directory=Default')
                    
                    print("\nNOTE: This may cause issues if Chrome is already using this profile.")
                    print("If you encounter errors, either:")
                    print("1. Close all Chrome windows and try again")
                    print("2. Start Chrome with --remote-debugging-port=9222")
                    print("3. Use the --force-new-chrome option to use a temporary profile")
                    
                    # Add a brief pause to let the user read the message
                    time.sleep(3)
                else:
                    # No specific profile requested, just open a new browser window
                    print("Chrome is already running. Opening a new browser window.")
            else:
                # Chrome is not running, start it normally
                print("Chrome is not running. Starting a new browser instance.")
                if user_data_dir:
                    self.chrome_options.add_argument(f'--user-data-dir={user_data_dir}')
                    if use_default_profile:
                        self.chrome_options.add_argument('--profile-directory=Default')
        elif force_new_chrome:
            # Force a new Chrome instance with a temporary profile
            print("Using a new Chrome instance with a temporary profile.")
            # Don't add any user_data_dir argument to use a temporary profile
        elif user_data_dir:
            # Not reusing Chrome, but still using a profile
            self.chrome_options.add_argument(f'--user-data-dir={user_data_dir}')
            if use_default_profile:
                self.chrome_options.add_argument('--profile-directory=Default')
        
        # Add anti-detection options (only if not connecting to existing Chrome)
        if not self.debugging_port:
            self.chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            self.chrome_options.add_argument('--disable-extensions')
            self.chrome_options.add_argument('--disable-infobars')
            self.chrome_options.add_argument('--no-sandbox')
            self.chrome_options.add_argument('--disable-gpu')
            
            # Add a user agent to appear more like a regular browser
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.7103.93 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.7103.93 Safari/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.7103.93 Safari/537.36'
            ]
            self.chrome_options.add_argument(f'--user-agent={random.choice(user_agents)}')
            
            # Add options to ignore certificate errors and version mismatches
            self.chrome_options.add_argument('--ignore-ssl-errors=yes')
            self.chrome_options.add_argument('--ignore-certificate-errors')
            self.chrome_options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])
            self.chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Additional preferences to avoid detection
            prefs = {
                "profile.default_content_setting_values.notifications": 2,
                "credentials_enable_service": False,
                "profile.password_manager_enabled": False,
                "profile.default_content_settings.popups": 0,
            }
            self.chrome_options.add_experimental_option("prefs", prefs)
        
        # Set up ChromeDriver service
        # Find the chromedriver executable in the current directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        chromedriver_name = "chromedriver.exe" if platform.system() == "Windows" else "chromedriver"
        chromedriver_path = os.path.join(current_dir, chromedriver_name)
        
        if not os.path.exists(chromedriver_path):
            raise FileNotFoundError(f"ChromeDriver not found at {chromedriver_path}. Please run download_chromedriver.py first.")
        
        print(f"Using ChromeDriver at: {chromedriver_path}")
        self.service = Service(executable_path=chromedriver_path)
        
        # Initialize WebDriver
        try:
            self.driver = webdriver.Chrome(service=self.service, options=self.chrome_options)
            
            # Create a new tab if we're connected to an existing Chrome
            if self.debugging_port:
                # Get current tabs
                current_tabs = self.driver.window_handles
                # Open a new tab
                self.driver.execute_script("window.open('about:blank', '_blank');")
                # Wait for the new tab to open
                time.sleep(1)
                # Get updated tabs
                new_tabs = self.driver.window_handles
                # Find the new tab (the tab that's in new_tabs but not in current_tabs)
                new_tab = list(set(new_tabs) - set(current_tabs))
                if new_tab:
                    # Switch to the new tab
                    self.driver.switch_to.window(new_tab[0])
                
                print("Created a new tab in existing Chrome browser.")
        except Exception as e:
            error_message = str(e)
            if "user data directory is already in use" in error_message.lower():
                print("\nERROR: Chrome user data directory is already in use.")
                print("This happens when Chrome is already running with the same profile.")
                print("\nOptions to fix this:")
                print("1. Close all Chrome windows and try again")
                print("2. Start Chrome with --remote-debugging-port=9222")
                print("3. Use --force-new-chrome to use a temporary profile instead")
                raise Exception(
                    "Chrome user data directory is already in use. See above for options."
                ) from e
            elif "chrome failed to start" in error_message.lower() or "cannot access chrome" in error_message.lower():
                print("\nERROR: Chrome failed to start properly.")
                print("This might be due to profile conflicts or Chrome processes still running.")
                print("\nOptions to fix this:")
                print("1. Close all Chrome windows and check Task Manager for any Chrome processes")
                print("2. Use --force-new-chrome to use a temporary profile instead")
                raise Exception(
                    "Chrome failed to start. See above for options."
                ) from e
            else:
                raise
        
        # Execute CDP commands to prevent detection (only if not connecting to existing Chrome)
        if not self.debugging_port:
            try:
                self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": random.choice(user_agents)})
                self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                    "source": """
                        Object.defineProperty(navigator, 'webdriver', {
                            get: () => undefined
                        });
                        Object.defineProperty(navigator, 'languages', {
                            get: () => ['en-US', 'en']
                        });
                        Object.defineProperty(navigator, 'plugins', {
                            get: () => [1, 2, 3, 4, 5]
                        });
                    """
                })
            except Exception as e:
                print(f"Warning: Could not execute CDP commands: {e}")
        
        self.wait = WebDriverWait(self.driver, 20)
        self.current_search_results = []
    
    def check_and_setup_chromedriver(self):
        """Check if ChromeDriver is available and compatible, download if needed"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        chromedriver_name = "chromedriver.exe" if platform.system() == "Windows" else "chromedriver"
        chromedriver_path = os.path.join(current_dir, chromedriver_name)
        
        # Check if downloader script exists
        downloader_path = os.path.join(current_dir, "download_chromedriver.py")
        if not os.path.exists(downloader_path):
            print("Warning: ChromeDriver downloader script not found.")
            
            # Check if we at least have the ChromeDriver executable
            if not os.path.exists(chromedriver_path):
                raise FileNotFoundError(
                    "ChromeDriver not found. Please download a compatible ChromeDriver manually, "
                    "or get the download_chromedriver.py script."
                )
            return
        
        # If ChromeDriver doesn't exist, download it
        if not os.path.exists(chromedriver_path):
            print("ChromeDriver not found. Downloading compatible version...")
            try:
                subprocess.check_call([sys.executable, downloader_path])
            except Exception as e:
                print(f"Error downloading ChromeDriver: {e}")
                raise
            return
        
        # Test if ChromeDriver is compatible with installed Chrome
        try:
            print("Testing ChromeDriver compatibility...")
            options = Options()
            options.add_argument('--headless')
            service = Service(executable_path=chromedriver_path)
            driver = webdriver.Chrome(service=service, options=options)
            driver.quit()
            print("ChromeDriver is compatible with installed Chrome.")
        except Exception as e:
            error_message = str(e)
            if "This version of ChromeDriver only supports Chrome version" in error_message:
                print("ChromeDriver is not compatible with installed Chrome version.")
                print("Downloading compatible ChromeDriver...")
                try:
                    subprocess.check_call([sys.executable, downloader_path])
                except Exception as download_error:
                    print(f"Error downloading ChromeDriver: {download_error}")
                    raise
            else:
                print(f"Error testing ChromeDriver: {e}")
                raise

    def human_like_typing(self, element, text):
        """Type text with random delays like a human would"""
        for char in text:
            element.send_keys(char)
            # Random delay between keystrokes (50-150ms)
            time.sleep(random.uniform(0.05, 0.15))
    
    def human_like_scroll(self, scroll_amount=None):
        """Scroll the page in a human-like manner"""
        if scroll_amount is None:
            # Random scroll amount
            scroll_amount = random.randint(300, 700)
        
        # Use JavaScript to scroll
        self.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
        # Random pause after scrolling
        time.sleep(random.uniform(0.5, 1.5))
    
    def search_google(self, query):
        """Search Google with the given query and extract results"""
        print(f"\nSearching Google for: {query}")
        
        # Navigate to Google with a random delay
        self.driver.get("https://www.google.com")
        time.sleep(random.uniform(1, 2))
        
        # Check for and handle cookies consent
        try:
            cookie_buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Accept') or contains(text(), 'Agree') or contains(text(), 'I agree') or contains(text(), 'Accept all')]")
            if cookie_buttons:
                cookie_buttons[0].click()
                time.sleep(random.uniform(0.5, 1))
        except:
            pass
        
        # Find search input and enter query with human-like typing
        try:
            search_box = self.wait.until(EC.element_to_be_clickable((By.NAME, "q")))
            search_box.clear()
            self.human_like_typing(search_box, query)
            
            # Random pause before hitting Enter
            time.sleep(random.uniform(0.5, 1.2))
            search_box.send_keys(Keys.RETURN)
            
            # Random pause after search
            time.sleep(random.uniform(2, 3))
        except Exception as e:
            print(f"Error during search: {str(e)}")
            
            # Enhanced CAPTCHA detection
            if self.is_captcha_present():
                print("\n*** CAPTCHA detected! ***")
                print("Please solve the CAPTCHA manually in the browser window.")
                input("Press Enter after solving the CAPTCHA to continue...")
                # Try the search again
                search_box = self.wait.until(EC.element_to_be_clickable((By.NAME, "q")))
                search_box.clear()
                self.human_like_typing(search_box, query)
                time.sleep(random.uniform(0.5, 1.2))
                search_box.send_keys(Keys.RETURN)
        
        # Wait for results to load
        self.wait.until(EC.presence_of_element_located((By.ID, "search")))
        
        # Human-like scrolling
        self.human_like_scroll()
        
        # Random pause before extraction
        time.sleep(random.uniform(1.5, 2.5))
        
        # Extract search results
        search_results = self.driver.find_elements(By.CSS_SELECTOR, "div.g")
        self.current_search_results = []
        
        for result in search_results[:5]:  # Limit to top 5 results
            try:
                title_element = result.find_element(By.CSS_SELECTOR, "h3")
                title = title_element.text
                link_element = result.find_element(By.CSS_SELECTOR, "a")
                link = link_element.get_attribute("href")
                
                self.current_search_results.append({
                    "title": title,
                    "link": link
                })
                
                print(f"Found: {title} - {link}")
            except:
                continue
        
        return self.current_search_results
    
    def is_captcha_present(self):
        """Enhanced method to detect various types of CAPTCHAs"""
        # Check for common CAPTCHA indicators in the page source
        page_source = self.driver.page_source.lower()
        if "recaptcha" in page_source or "captcha" in page_source:
            return True
            
        # Check for specific CAPTCHA elements
        try:
            # Check for reCAPTCHA iframe
            recaptcha_frames = self.driver.find_elements(By.CSS_SELECTOR, "iframe[src*='recaptcha'], iframe[src*='captcha']")
            if recaptcha_frames:
                return True
                
            # Check for common CAPTCHA images
            captcha_images = self.driver.find_elements(By.XPATH, "//img[contains(@src, 'captcha')]")
            if captcha_images:
                return True
                
            # Check for common CAPTCHA text
            captcha_text = self.driver.find_elements(By.XPATH, 
                "//*[contains(text(), 'captcha') or contains(text(), 'CAPTCHA') or contains(text(), 'robot') or contains(text(), 'unusual traffic') or contains(text(), 'suspicious activity')]")
            if captcha_text:
                return True
                
            # Check for Google's specific security challenges
            if "Our systems have detected unusual traffic" in self.driver.page_source:
                return True
        except:
            # If any error occurs during detection, better to assume it might be a CAPTCHA
            pass
            
        return False
    
    def get_page_content(self, url):
        """Extract content from a web page"""
        print(f"\nGetting content from: {url}")
        
        # Navigate to the page
        self.driver.get(url)
        
        # Wait for the page to load with random time
        time.sleep(random.uniform(3, 5))
        
        # Human-like scrolling to simulate reading
        for _ in range(random.randint(2, 4)):
            self.human_like_scroll()
        
        # Get the page content
        page_html = self.driver.page_source
        soup = BeautifulSoup(page_html, 'html.parser')
        
        # Get the title
        title = soup.title.string if soup.title else "No title found"
        
        # Try to extract main content (this is a simple approach and might need adjustment)
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.extract()
        
        # Get text
        text = soup.get_text(separator='\n')
        
        # Clean up text
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        # Trim the text to a reasonable length
        max_length = 5000
        if len(text) > max_length:
            text = text[:max_length] + "... [Text truncated due to length]"
        
        content = {
            "title": title,
            "text": text,
            "url": url
        }
        
        return content
    
    def send_to_deepseek(self, content):
        """Send the content to DeepSeek AI chat"""
        print("\nSending data to DeepSeek...")
        
        # Navigate to DeepSeek chat
        self.driver.get("https://chat.deepseek.com/")
        
        # Wait for DeepSeek to load with random time
        time.sleep(random.uniform(4, 6))
        
        # Check if login is required
        if "Sign in" in self.driver.page_source or "Log in" in self.driver.page_source:
            print("\nDeepSeek requires login. Please log in manually in the browser window.")
            print("If you're using a persistent profile (--profile), you should only need to do this once.")
            input("Press Enter after logging in to continue...")
            time.sleep(2)  # Allow time for post-login page to load
        
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # Look for textarea to input the message
                try:
                    # Try multiple possible selectors for the input box
                    selectors = [
                        "textarea.resize-none",
                        "textarea[placeholder*='Send a message']",
                        "div[contenteditable='true']",
                        "div.chat-input textarea"
                    ]
                    
                    input_box = None
                    for selector in selectors:
                        try:
                            input_box = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                            if input_box:
                                break
                        except:
                            continue
                    
                    if not input_box:
                        raise Exception("Could not find input area on DeepSeek interface")
                    
                    # Prepare the message
                    message = f"Analyze this content from {content['url']}:\n\nTitle: {content['title']}\n\nContent: {content['text']}\n\nProvide a comprehensive analysis and extract key information."
                    
                    # Type the message in chunks with human-like behavior
                    chunk_size = 500
                    for i in range(0, len(message), chunk_size):
                        chunk = message[i:i+chunk_size]
                        self.human_like_typing(input_box, chunk)
                        time.sleep(random.uniform(0.3, 0.7))
                    
                    # Random pause before sending
                    time.sleep(random.uniform(0.8, 1.5))
                    
                    # Try different methods to send the message
                    try:
                        # Method 1: Using keyboard shortcut
                        input_box.send_keys(Keys.CONTROL + Keys.ENTER)
                        
                        # Check if a send button is present and try clicking it if shortcut didn't work
                        time.sleep(1)
                        try:
                            send_buttons = self.driver.find_elements(By.XPATH, 
                                "//button[contains(@aria-label, 'send') or contains(@title, 'send') or contains(@class, 'send')]")
                            if send_buttons:
                                send_buttons[0].click()
                        except:
                            pass
                    except:
                        # Method 2: Try to find and click a send button
                        try:
                            send_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, 
                                "//button[contains(@aria-label, 'send') or contains(@title, 'send') or contains(@class, 'send')]")))
                            send_button.click()
                        except:
                            # Method 3: Enter key
                            input_box.send_keys(Keys.ENTER)
                    
                    # Wait for response with progressive timeouts
                    print("Waiting for DeepSeek to respond...")
                    
                    # Try to find different types of response elements
                    response_selectors = [
                        "div.markdown-body", 
                        "div.message-content", 
                        "div.assistant-message",
                        "div.response-content"
                    ]
                    
                    # Wait progressively longer for AI to generate a response
                    wait_times = [5, 10, 15, 20]
                    response_text = None
                    
                    for wait_time in wait_times:
                        time.sleep(wait_time)
                        
                        # Check all possible response selectors
                        for selector in response_selectors:
                            try:
                                response_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                                if response_elements and len(response_elements) > 0:
                                    # Get the last response element's text
                                    response_text = response_elements[-1].text
                                    if response_text and len(response_text) > 50:  # Ensure it's a substantial response
                                        print("\nDeepSeek Response:")
                                        print(response_text)
                                        return response_text
                            except:
                                continue
                    
                    # If we've checked all wait times and selectors but found nothing valid
                    if not response_text or len(response_text) < 50:
                        raise Exception("No substantial response found from DeepSeek")
                
                except Exception as e:
                    print(f"Error with DeepSeek interface: {str(e)}")
                    retry_count += 1
                    if retry_count < max_retries:
                        print(f"Retrying ({retry_count}/{max_retries})...")
                        # Refresh the page and try again
                        self.driver.refresh()
                        time.sleep(5)  # Wait for page to refresh
                    else:
                        return f"Error interacting with DeepSeek: {str(e)}"
            
            except Exception as e:
                print(f"Critical error sending to DeepSeek: {str(e)}")
                return f"Critical error with DeepSeek: {str(e)}"
        
        # If we've exhausted retries
        return "Could not get a proper response from DeepSeek after multiple attempts."
    
    def follow_up_search(self, deepseek_response):
        """Generate a follow-up search query based on DeepSeek's response"""
        # Simple approach: extract key terms from the response
        words = re.findall(r'\b\w+\b', deepseek_response.lower())
        common_words = ['the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'and', 'or', 'but', 'is', 'are', 'was', 'were']
        filtered_words = [word for word in words if word not in common_words and len(word) > 4]
        
        # Count word frequency
        from collections import Counter
        word_count = Counter(filtered_words)
        top_words = [word for word, count in word_count.most_common(5)]
        
        # Generate a new search query
        if top_words:
            query = ' '.join(top_words[:3])  # Take top 3 words
            print(f"\nGenerated follow-up search query: {query}")
            return query
        else:
            print("\nCouldn't generate a meaningful follow-up query")
            return None
    
    def close(self):
        """Close the browser, but only if we started it"""
        self.driver.quit()
        
        # If we started Chrome with debugging, we should also close that Chrome instance
        if self.chrome_process_started:
            try:
                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                    try:
                        cmdline = proc.info.get('cmdline', [])
                        if cmdline and any(f"--remote-debugging-port={self.debugging_port}" in cmd for cmd in cmdline):
                            print(f"Terminating Chrome process (PID: {proc.info['pid']})...")
                            proc.terminate()
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        pass
            except Exception as e:
                print(f"Error closing Chrome process: {e}")

def parse_args():
    parser = argparse.ArgumentParser(description='AI Search Assistant')
    parser.add_argument('--profile', action='store_true', 
                        help='Use a persistent Chrome profile (helps with CAPTCHAs)')
    parser.add_argument('--use-default-profile', action='store_true',
                        help='Use the default Chrome profile on your device (maintains all your logins)')
    parser.add_argument('--no-reuse-chrome', action='store_true',
                        help='Don\'t try to reuse running Chrome instances (starts a new session)')
    parser.add_argument('--force-new-chrome', action='store_true',
                        help='Force a new Chrome instance with a temporary profile (avoids profile conflicts)')
    return parser.parse_args()

def main():
    # Parse command line arguments
    args = parse_args()
    
    # If using default profile but not reusing Chrome, show warning
    if args.use_default_profile and args.no_reuse_chrome and not args.force_new_chrome:
        print("\n*** IMPORTANT: Using your default Chrome profile with a new browser instance ***")
        print("For this to work properly, please close all Chrome windows before continuing.")
        input("Press Enter when Chrome is closed to continue...")
    
    # Show information about connecting to existing Chrome
    if not args.no_reuse_chrome and not args.force_new_chrome:
        print("\n*** CHROME BROWSER MODE ***")
        print("The script will try to work with Chrome in one of these ways:")
        print("1. Connect to Chrome if it's already running with remote debugging")
        print("2. Use your profile directly if Chrome is running normally")
        print("3. Start a new Chrome instance if Chrome is not running")
        
        print("\nFor the best experience with an existing Chrome window, start Chrome with:")
        if platform.system() == "Windows":
            print("  chrome.exe --remote-debugging-port=9222")
        elif platform.system() == "Darwin":  # macOS
            print("  /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222")
        else:
            print("  google-chrome --remote-debugging-port=9222")
    elif args.force_new_chrome:
        print("\n*** USING TEMPORARY CHROME PROFILE ***")
        print("The script will start a new Chrome instance with a temporary profile.")
        print("This avoids conflicts with any running Chrome instances, but won't have your existing logins.")
    
    try:
        # Initialize with profile if requested
        assistant = AISearchAssistant(
            use_profile=args.profile, 
            use_default_profile=args.use_default_profile,
            reuse_chrome=not args.no_reuse_chrome,
            force_new_chrome=args.force_new_chrome
        )
        
        # Get the initial search query
        query = input("\nEnter your search query: ")
        
        # Search Google
        search_results = assistant.search_google(query)
        
        if search_results:
            # Get the first result
            first_result = search_results[0]
            
            # Get content from the page
            content = assistant.get_page_content(first_result["link"])
            
            # Send to DeepSeek
            deepseek_response = assistant.send_to_deepseek(content)
            
            # Generate follow-up search
            follow_up_query = assistant.follow_up_search(deepseek_response)
            
            if follow_up_query:
                print("\nWould you like to perform the follow-up search?")
                choice = input("Enter 'yes' to proceed or any other key to exit: ")
                
                if choice.lower() == 'yes':
                    # Perform follow-up search
                    follow_up_results = assistant.search_google(follow_up_query)
                    
                    if follow_up_results:
                        # Get content from the first follow-up result
                        follow_up_content = assistant.get_page_content(follow_up_results[0]["link"])
                        
                        # Send to DeepSeek
                        assistant.send_to_deepseek(follow_up_content)
        
        print("\nSearch assistant process completed.")
    except Exception as e:
        error_message = str(e)
        print(f"\nAn error occurred: {error_message}")
        
        # Provide specific guidance based on error type
        if "user data directory is already in use" in error_message.lower() or "chrome failed to start" in error_message.lower():
            print("\nTROUBLESHOOTING:")
            print("1. Make sure all Chrome windows are completely closed")
            print("2. Check Task Manager (Windows) or Activity Monitor (Mac) for any Chrome processes")
            print("3. Try again with a custom profile instead:")
            print("   python ai_search_assistant.py --profile")
        elif "chromedriver" in error_message.lower():
            print("\nTROUBLESHOOTING:")
            print("1. Try running the ChromeDriver downloader:")
            print("   python download_chromedriver.py")
            print("2. Make sure you have the latest Chrome browser installed")
        elif "no such file" in error_message.lower() or "not found" in error_message.lower():
            print("\nTROUBLESHOOTING:")
            print("1. Check if the required files exist in the directory")
            print("2. Try reinstalling the script and dependencies")
    finally:
        # Define assistant variable in case it wasn't defined due to an early error
        assistant_exists = 'assistant' in locals() or 'assistant' in globals()
        
        if assistant_exists:
            # Ask if the user wants to keep the browser open
            keep_open = input("\nDo you want to keep the browser open? (yes/no): ")
            if keep_open.lower() != 'yes':
                assistant.close()
                print("Browser closed. Goodbye!")
            else:
                print("Browser remains open. You can continue browsing manually.")
                print("Run the script again to start a new search.")
        else:
            print("\nScript terminated due to initialization error.")

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

def is_chrome_running_with_debugging():
    """Check if Chrome is already running with remote debugging enabled"""
    return find_existing_chrome_debugging_port() is not None

def get_running_chrome_info():
    """Try to connect to already running Chrome"""
    port = find_existing_chrome_debugging_port()
    if not port:
        return None
    
    try:
        response = requests.get(f'http://localhost:{port}/json/version')
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def attach_to_existing_chrome():
    """Try to attach to an already running Chrome instance"""
    port = find_existing_chrome_debugging_port()
    if port:
        print(f"Found Chrome running with debugging port: {port}")
        chrome_options = Options()
        chrome_options.add_experimental_option("debuggerAddress", f"127.0.0.1:{port}")
        return port, chrome_options
    return None, None

def is_chrome_running():
    """Check if Chrome is running on the system"""
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            process_name = proc.info['name'].lower()
            if 'chrome' in process_name and 'chromedriver' not in process_name:
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False

def start_chrome_with_debugging(user_data_dir=None):
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
    
    # Choose a random port between 9222 and 9299 to avoid conflicts
    debugging_port = random.randint(9222, 9299)
    
    # Build command
    command = [chrome_path, f"--remote-debugging-port={debugging_port}", "--no-first-run"]
    
    if user_data_dir:
        command.append(f"--user-data-dir={user_data_dir}")
    
    # Start Chrome in background
    if system == "Windows":
        from subprocess import DEVNULL
        subprocess.Popen(command, stdout=DEVNULL, stderr=DEVNULL, shell=True)
    else:
        subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Give Chrome a moment to start
    time.sleep(3)
    
    return debugging_port

if __name__ == "__main__":
    main() 