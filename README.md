# AI Search Assistant

A Python automation tool that enhances search by integrating with DeepSeek AI.

## Features

- Search Google with user queries
- Extract search results and page content
- Send data to DeepSeek for processing through their chat interface
- Get AI-enhanced responses
- Perform follow-up searches based on AI insights

## Requirements

- Python 3.9+
- Chrome browser (version 136.x recommended)
- Required Python packages:
  - selenium
  - beautifulsoup4
  - requests

## Setup

1. Make sure you have Chrome browser installed

2. Install required Python packages:
   ```
   python -m pip install selenium beautifulsoup4 requests
   ```

3. Download the compatible ChromeDriver for your Chrome version:
   ```
   python download_chromedriver136.py
   ```
   This script automatically finds and downloads the correct ChromeDriver version for Chrome 136.

## Usage

1. Run the search assistant:
   ```
   # Basic usage
   python ai_search_assistant.py
   
   # Using persistent Chrome profile (recommended to avoid CAPTCHAs)
   python ai_search_assistant.py --profile
   ```

2. Enter your search query when prompted.

3. The script will:
   - Open Chrome browser
   - Search Google for your query
   - Extract the search results
   - Visit the first result to get detailed content
   - Send the content to DeepSeek
   - Return DeepSeek's response
   - Generate a follow-up search query

4. You can choose to perform a follow-up search based on the AI's analysis.

5. At the end, you'll have the option to keep the browser open or close it.

## Using Persistent Profile

The `--profile` option creates and uses a persistent Chrome profile stored in the `chrome-profile` directory. This has several benefits:

- Greatly reduces likelihood of encountering CAPTCHAs
- Maintains cookies between sessions
- Allows you to log in to Google (and DeepSeek) once and stay logged in
- Provides a more consistent browsing experience

If you're experiencing CAPTCHA issues, always use this option:
```
python ai_search_assistant.py --profile
```

## Handling CAPTCHAs

Google sometimes shows CAPTCHAs when it detects automated activity. The script includes several anti-detection measures, but you might still encounter CAPTCHAs occasionally. If a CAPTCHA appears:

1. The script will detect it and pause execution
2. You'll see a message prompting you to solve the CAPTCHA manually
3. Solve the CAPTCHA in the browser window that appears
4. Press Enter in the terminal to continue the script

Tips to reduce CAPTCHA frequency:
- Always use the `--profile` option
- Don't run too many searches in a short time period
- Use the script while logged into your Google account (this may help Google establish trust)
- Run the script with a VPN turned off
- Let the browser window remain visible (don't minimize it)

## Troubleshooting

- **ChromeDriver Error**: If you encounter ChromeDriver compatibility issues, run the `download_chromedriver136.py` script again to download the latest compatible driver.

- **Browser Not Starting**: Make sure no other instances of ChromeDriver are running in the background.

- **DeepSeek Not Loading**: Check your internet connection. The script may need adjustments if DeepSeek's interface changes.

- **Constant CAPTCHAs**: If you frequently encounter CAPTCHAs, try the following:
  - Use the `--profile` option and log in to your Google account in the profile 
  - Wait 10-15 minutes before running the script again
  - Clear your browser cookies and cache
  - Try using a different network connection

## How It Works

1. **Search Automation**: The script automates Google searches and extracts relevant information from websites.

2. **Content Analysis**: It sends the extracted content to DeepSeek AI for comprehensive analysis.

3. **Intelligent Follow-up**: Based on DeepSeek's response, it can perform follow-up searches to dig deeper into topics.

## Files

- `ai_search_assistant.py` - The main script
- `download_chromedriver136.py` - Helper script to download the correct ChromeDriver version
- `README.md` - This documentation file
- `chrome-profile/` - Directory created when using the `--profile` option (contains Chrome user data)

## License

This project is for educational purposes. Use responsibly and in accordance with the terms of service of Google and DeepSeek.

## Notes

- The script may need adjustments based on DeepSeek's UI changes
- Selectors and timing might require updates for different websites
- You must manually log in to DeepSeek if authentication is required

## Customization

You can modify the script to:
- Use different search engines
- Extract content from specific websites
- Change the AI service (from DeepSeek to another)
- Add more advanced content processing 