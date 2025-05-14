import os
import sys
import platform
import webbrowser
import urllib.parse
import time
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

def extract_search_results_and_send_to_deepseek():
    """Open a Google search, extract the results, and send to DeepSeek"""
    # Get user input for search
    search_query = input("Enter your search query: ")
    
    # Encode the query for URL
    encoded_query = urllib.parse.quote(search_query)
    
    # Create the Google search URL
    google_url = f"https://www.google.com/search?q={encoded_query}"
    
    print(f"Opening Google search for: {search_query}")
    
    # Set up Chrome options for selenium
    chrome_options = Options()
    
    # Use the default browser profile to maintain logins
    if platform.system() == "Windows":
        # Try to detect Chrome user data directory
        default_profile_path = os.path.join(os.path.expanduser('~'), 
            'AppData', 'Local', 'Google', 'Chrome', 'User Data')
        if os.path.exists(default_profile_path):
            chrome_options.add_argument(f'--user-data-dir={default_profile_path}')
            chrome_options.add_argument('--profile-directory=Default')
    
    # Initialize Chrome driver
    try:
        # Find chromedriver.exe in the current directory or backup
        current_dir = os.path.dirname(os.path.abspath(__file__))
        chromedriver_name = "chromedriver.exe" if platform.system() == "Windows" else "chromedriver"
        chromedriver_path = os.path.join(current_dir, chromedriver_name)
        
        # Check if chromedriver is in the backup directory
        if not os.path.exists(chromedriver_path):
            backup_path = os.path.join(current_dir, "backup", chromedriver_name)
            if os.path.exists(backup_path):
                chromedriver_path = backup_path
        
        # If chromedriver is still not found, use default behavior with webbrowser
        if not os.path.exists(chromedriver_path):
            print("ChromeDriver not found. Using default browser instead.")
            # Open the URL in the default browser
            webbrowser.open(google_url)
            print("Search opened in default browser. Script can't extract data without ChromeDriver.")
            return
            
        # Initialize the Chrome driver with the options
        service = Service(executable_path=chromedriver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Navigate to Google
        driver.get(google_url)
        
        # Wait for the search results to load
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "search")))
        
        print("Search results loaded. Scrolling to extract all results...")
        
        # Scroll down to the bottom of the page to load all results
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            # Scroll down to bottom
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            # Wait to load page
            time.sleep(2)
            
            # Calculate new scroll height and compare with last scroll height
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
            
            print("Scrolling... found more results.")
        
        # Extract all search results
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Extract title, links and snippets
        search_results = []
        
        # Look for result containers
        results = soup.select("div.g")
        if not results:  # Try alternative selectors if the first one doesn't work
            results = soup.select("div.tF2Cxc")
        if not results:
            results = soup.select("div.yuRUbf")
        
        for result in results:
            title_elem = result.select_one("h3")
            link_elem = result.select_one("a")
            snippet_elem = result.select_one("div.VwiC3b") or result.select_one("span.aCOpRe")
            
            title = title_elem.text if title_elem else "No title found"
            link = link_elem['href'] if link_elem and 'href' in link_elem.attrs else "No link found"
            snippet = snippet_elem.text if snippet_elem else "No snippet found"
            
            search_results.append({
                "title": title,
                "link": link,
                "snippet": snippet
            })
        
        print(f"Extracted {len(search_results)} search results.")
        
        # Format the extracted data
        formatted_data = f"Google Search Results for: {search_query}\n\n"
        
        for i, result in enumerate(search_results, 1):
            formatted_data += f"Result {i}:\n"
            formatted_data += f"Title: {result['title']}\n"
            formatted_data += f"Link: {result['link']}\n"
            formatted_data += f"Snippet: {result['snippet']}\n\n"
        
        print("Opening DeepSeek chat...")
        
        # Open DeepSeek in a new tab
        driver.execute_script("window.open('https://chat.deepseek.com/', '_blank');")
        
        # Switch to the new tab
        driver.switch_to.window(driver.window_handles[-1])
        
        # Wait for DeepSeek to load
        time.sleep(5)
        
        try:
            # Wait for the text area to appear
            textarea = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "textarea.resize-none"))
            )
            
            # Check if we need to login
            if "Sign in" in driver.page_source or "Log in" in driver.page_source:
                print("\nDeepSeek requires login. Please log in manually.")
                print("After logging in, the script will paste the search results.")
                input("Press Enter after logging in to continue...")
                
                # Refresh the page after login
                driver.refresh()
                time.sleep(3)
                
                # Find the textarea again
                textarea = WebDriverWait(driver, 20).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "textarea.resize-none"))
                )
            
            # Click the textarea and paste the data
            textarea.click()
            
            # Type the formatted data in chunks to avoid issues with large text
            chunk_size = 1000
            for i in range(0, len(formatted_data), chunk_size):
                chunk = formatted_data[i:i+chunk_size]
                textarea.send_keys(chunk)
                time.sleep(0.5)  # Small delay between chunks
            
            print("Search results pasted into DeepSeek. You can now send the message manually.")
            
            # Keep the browser window open
            input("Press Enter to close the browser and exit...")
            
        except Exception as e:
            print(f"Error interacting with DeepSeek: {e}")
            print("The browser window will stay open so you can manually interact with it.")
            input("Press Enter to close the browser and exit...")
        
        # Close the browser when done
        driver.quit()
        
    except Exception as e:
        print(f"Error opening browser with selenium: {e}")
        print("Falling back to default browser...")
        webbrowser.open(google_url)
        print("Search opened in default browser.")

if __name__ == "__main__":
    print("Enhanced Chrome Search")
    print("=====================")
    print("This script will:")
    print("1. Open Google search with your query")
    print("2. Scroll down to extract all results")
    print("3. Open DeepSeek and paste the results")
    print("")
    
    extract_search_results_and_send_to_deepseek() 