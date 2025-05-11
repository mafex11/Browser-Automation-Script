import time
import re
import os
import platform
import random
import argparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

class AISearchAssistant:
    def __init__(self, use_profile=False):
        # Set up Chrome options
        self.chrome_options = Options()
        # Uncomment the line below if you want to run in headless mode
        # self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--start-maximized')
        
        # Create a profile directory if requested
        if use_profile:
            profile_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chrome-profile")
            if not os.path.exists(profile_dir):
                os.makedirs(profile_dir)
            print(f"Using Chrome profile directory: {profile_dir}")
            self.chrome_options.add_argument(f'--user-data-dir={profile_dir}')
        
        # Add anti-detection options
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
            raise FileNotFoundError(f"ChromeDriver not found at {chromedriver_path}. Please run download_chromedriver136.py first.")
        
        print(f"Using ChromeDriver at: {chromedriver_path}")
        self.service = Service(executable_path=chromedriver_path)
        
        # Initialize WebDriver
        self.driver = webdriver.Chrome(service=self.service, options=self.chrome_options)
        
        # Execute CDP commands to prevent detection
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
        
        self.wait = WebDriverWait(self.driver, 20)
        self.current_search_results = []
    
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
            
            # Check if CAPTCHA is present
            if "recaptcha" in self.driver.page_source.lower() or "captcha" in self.driver.page_source.lower():
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
        
        # Look for textarea to input the message
        try:
            input_box = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "textarea.resize-none")))
            
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
            
            # Send the message
            input_box.send_keys(Keys.CONTROL + Keys.ENTER)
            
            # Wait for response with a longer time
            print("Waiting for DeepSeek to respond...")
            time.sleep(random.uniform(8, 12))  # Wait for response to begin
            
            # Check for response
            response_elements = self.wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.markdown-body")))
            
            # Get the last response
            if response_elements:
                response_text = response_elements[-1].text
                print("\nDeepSeek Response:")
                print(response_text)
                return response_text
            else:
                print("No response found from DeepSeek")
                return "No response found"
        
        except Exception as e:
            print(f"Error sending to DeepSeek: {str(e)}")
            return f"Error: {str(e)}"
    
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
        """Close the browser"""
        self.driver.quit()

def parse_args():
    parser = argparse.ArgumentParser(description='AI Search Assistant')
    parser.add_argument('--profile', action='store_true', 
                        help='Use a persistent Chrome profile (helps with CAPTCHAs)')
    return parser.parse_args()

def main():
    # Parse command line arguments
    args = parse_args()
    
    try:
        # Initialize with profile if requested
        assistant = AISearchAssistant(use_profile=args.profile)
        
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
        print(f"An error occurred: {str(e)}")
    finally:
        # Ask if the user wants to keep the browser open
        keep_open = input("\nDo you want to keep the browser open? (yes/no): ")
        if keep_open.lower() != 'yes':
            assistant.close()
            print("Browser closed. Goodbye!")
        else:
            print("Browser remains open. You can continue browsing manually.")
            print("Run the script again to start a new search.")

if __name__ == "__main__":
    main() 