# Simple Chrome Search

A lightweight Python tool that opens a Google search in your default browser.

## Features

- Simple and straightforward interface
- No special configuration required
- Works with your existing Chrome browser
- No need for ChromeDriver or automation tools

## Requirements

- Python 3.6+
- A web browser (Chrome recommended)

## Usage

1. Run the search tool:
   ```
   python simple_chrome_search.py
   ```

2. Enter your search query when prompted.

3. The script will:
   - Open your default browser
   - Navigate to Google
   - Perform the search with your query

## How It Works

This script uses Python's built-in `webbrowser` module to open a search query in your default browser. There's no complex automation or browser control - it simply launches a Google search URL with your query parameters.

## Benefits

- **Simplicity**: No complex setup or configuration
- **Speed**: Opens searches instantly in your existing browser
- **Reliability**: No dependencies on ChromeDriver or Selenium
- **Compatibility**: Works on all platforms (Windows, macOS, Linux)

## Notes

If you want to always use Chrome for searches (even if it's not your default browser), you can modify the script to specify Chrome directly. 